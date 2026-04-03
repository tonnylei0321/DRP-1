"""指标计算引擎：按业务域批量执行 SPARQL，写回 GraphDB 并缓存到 Redis。"""
import json
import logging
from dataclasses import dataclass

import httpx
import redis.asyncio as aioredis

from drp.config import settings
from drp.indicators.registry import INDICATOR_BY_ID, INDICATORS
from drp.sparql.proxy import sparql_query, sparql_update

logger = logging.getLogger(__name__)

# 各业务域的指标 ID 范围（用于分批执行）
DOMAIN_BATCHES: list[tuple[str, list[str]]] = [
    ("银行账户", [ind["id"] for ind in INDICATORS if ind["domain"] == "银行账户"]),
    ("资金集中", [ind["id"] for ind in INDICATORS if ind["domain"] == "资金集中"]),
    ("结算",     [ind["id"] for ind in INDICATORS if ind["domain"] == "结算"]),
    ("票据",     [ind["id"] for ind in INDICATORS if ind["domain"] == "票据"]),
    ("债务融资", [ind["id"] for ind in INDICATORS if ind["domain"] == "债务融资"]),
    ("决策风险", [ind["id"] for ind in INDICATORS if ind["domain"] == "决策风险"]),
    ("国资委考核",[ind["id"] for ind in INDICATORS if ind["domain"] == "国资委考核"]),
]

# Redis 缓存 TTL（秒）
_CACHE_TTL = 3600

# Redis key 前缀
_KEY_PREFIX = "kpi"


@dataclass
class IndicatorResult:
    """单条指标计算结果。"""
    indicator_id: str
    tenant_id: str
    value: float | None
    is_compliant: bool


def _redis_key(tenant_id: str, indicator_id: str) -> str:
    return f"{_KEY_PREFIX}:{tenant_id}:{indicator_id}"


async def _execute_sparql(indicator: dict, tenant_id: str, client: httpx.AsyncClient | None = None) -> float | None:
    """执行单条 SPARQL，返回计算结果值（None 表示无数据）。"""
    sparql = indicator["sparql"]
    try:
        rows = await sparql_query(sparql, tenant_id=tenant_id, client=client)
        if not rows:
            return None
        # SELECT 第一列第一行的值
        first_row = rows[0]
        first_val = next(iter(first_row.values()), None)
        if first_val is None:
            return None
        return float(first_val)
    except Exception as exc:  # noqa: BLE001
        logger.warning("指标 %s 计算失败（tenant=%s）: %s", indicator["id"], tenant_id, exc)
        return None


def _check_compliance(indicator: dict, value: float | None) -> bool:
    """根据 target_value/threshold 判断是否达标。"""
    if value is None:
        return False
    target = indicator.get("target_value")
    threshold = indicator.get("threshold")
    if target is not None:
        if target == 0:
            # 目标为 0 的指标（如风险事件数），≤ threshold 即达标
            th = threshold if threshold is not None else 0
            return value <= th
        # 比率类指标：>= threshold 达标
        check_val = threshold if threshold is not None else target
        return value >= check_val
    return True  # 无目标要求，默认达标


async def _update_graphdb(
    result: IndicatorResult,
    tenant_id: str,
    client: httpx.AsyncClient | None = None,
) -> None:
    """将指标当前值写回 GraphDB 中的 RegulatoryIndicator 实例。"""
    value_str = str(result.value) if result.value is not None else "0.0"
    compliant_str = "true" if result.is_compliant else "false"
    sparql = f"""
PREFIX ctio: <urn:ctio:>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE {{
  ?ind ctio:currentValue ?oldVal ;
       ctio:isCompliant ?oldComp .
}}
INSERT {{
  ?ind ctio:currentValue "{value_str}"^^xsd:decimal ;
       ctio:isCompliant {compliant_str} .
}}
WHERE {{
  ?ind a ctio:RegulatoryIndicator ;
       ctio:indicatorId "{result.indicator_id}" .
  OPTIONAL {{ ?ind ctio:currentValue ?oldVal . }}
  OPTIONAL {{ ?ind ctio:isCompliant ?oldComp . }}
}}
"""
    try:
        await sparql_update(sparql, tenant_id=tenant_id, client=client)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "指标 %s 写回 GraphDB 失败（tenant=%s）: %s",
            result.indicator_id, tenant_id, exc,
        )


async def _write_redis_cache(
    result: IndicatorResult,
    redis_client: aioredis.Redis | None = None,
) -> None:
    """将指标结果写入 Redis 缓存，TTL=3600s。"""
    key = _redis_key(result.tenant_id, result.indicator_id)
    payload = json.dumps({
        "value": result.value,
        "is_compliant": result.is_compliant,
    })
    try:
        if redis_client is not None:
            await redis_client.setex(key, _CACHE_TTL, payload)
        else:
            async with aioredis.from_url(settings.redis_url) as r:
                await r.setex(key, _CACHE_TTL, payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("指标 %s 写入 Redis 失败（tenant=%s）: %s", result.indicator_id, result.tenant_id, exc)


async def _publish_risk_event(
    indicator: dict,
    result: IndicatorResult,
    redis_client: aioredis.Redis | None = None,
) -> None:
    """若指标不达标，向 Redis Pub/Sub ���道 `risk_events` 发布风险事件。"""
    if result.is_compliant:
        return

    event = json.dumps({
        "type": "risk_event",
        "tenant_id": result.tenant_id,
        "indicator_id": result.indicator_id,
        "indicator_name": indicator["name"],
        "domain": indicator["domain"],
        "value": result.value,
        "target_value": indicator.get("target_value"),
        "threshold": indicator.get("threshold"),
    })
    try:
        if redis_client is not None:
            await redis_client.publish("risk_events", event)
        else:
            async with aioredis.from_url(settings.redis_url) as r:
                await r.publish("risk_events", event)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "风险事件发布失败（tenant=%s, ind=%s）: %s",
            result.tenant_id, result.indicator_id, exc,
        )


async def calculate_domain(
    domain: str,
    indicator_ids: list[str],
    tenant_id: str,
    *,
    sparql_client: httpx.AsyncClient | None = None,
    redis_client: aioredis.Redis | None = None,
) -> list[IndicatorResult]:
    """计算单个业务域下所有指标，写回 GraphDB + Redis，发布风险事件。

    Args:
        domain: 业务域名称（仅用于日志）
        indicator_ids: 该域下的指标 ID 列表
        tenant_id: 租户 ID
        sparql_client: 可注入的 httpx 客户端（测试用）
        redis_client: 可注入的 Redis 客户端（测试用）

    Returns:
        该域所有指标的计算结果列表
    """
    results: list[IndicatorResult] = []
    logger.info("开始计算业务域 %s（%d 项指标，tenant=%s）", domain, len(indicator_ids), tenant_id)

    for ind_id in indicator_ids:
        indicator = INDICATOR_BY_ID.get(ind_id)
        if indicator is None:
            logger.error("指标 %s 不存在于注册表", ind_id)
            continue

        value = await _execute_sparql(indicator, tenant_id, client=sparql_client)
        is_compliant = _check_compliance(indicator, value)
        result = IndicatorResult(
            indicator_id=ind_id,
            tenant_id=tenant_id,
            value=value,
            is_compliant=is_compliant,
        )
        results.append(result)

        # 写回 GraphDB
        await _update_graphdb(result, tenant_id, client=sparql_client)
        # 写 Redis 缓存
        await _write_redis_cache(result, redis_client=redis_client)
        # 发布风险事件（不达标时）
        await _publish_risk_event(indicator, result, redis_client=redis_client)

    logger.info(
        "业务域 %s 计算完成：%d/%d 指标达标（tenant=%s）",
        domain,
        sum(1 for r in results if r.is_compliant),
        len(results),
        tenant_id,
    )
    return results


async def calculate_all_domains(
    tenant_id: str,
    *,
    sparql_client: httpx.AsyncClient | None = None,
    redis_client: aioredis.Redis | None = None,
) -> dict[str, list[IndicatorResult]]:
    """按业务域顺序计算全部 106 条指标。

    Returns:
        {domain: [IndicatorResult, ...]} 字典
    """
    all_results: dict[str, list[IndicatorResult]] = {}
    for domain, ids in DOMAIN_BATCHES:
        domain_results = await calculate_domain(
            domain, ids, tenant_id,
            sparql_client=sparql_client,
            redis_client=redis_client,
        )
        all_results[domain] = domain_results
    return all_results
