"""实体指标 API — 查询实体在7大监管领域下的指标数据。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.indicators.schemas import IndicatorResponse
from drp.sparql.proxy import sparql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indicators", tags=["监管指标"])

# 后端业务域 → 前端领域 ID 映射
_DOMAIN_MAP: dict[str, str] = {
    "银行账户": "fund",
    "资金集中": "fund",
    "结算": "finbiz",
    "票据": "finbiz",
    "债务融资": "debt",
    "决策风险": "finbiz",
    "国资委考核": "overseas",
}


def _safe_float(val: str | None) -> float | None:
    """安全地将字符串转换为 float。"""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@router.get(
    "/{entity_id}",
    summary="获取实体监管指标",
    description="返回指定实体在7大监管领域下所有指标的计算值。不返回 status 字段，由前端根据 threshold + direction 计算。",
    response_model=list[IndicatorResponse],
)
async def get_entity_indicators(
    entity_id: str = Path(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="实体唯一标识（仅允许字母数字下划线和连字符）",
    ),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[IndicatorResponse]:
    """返回指定实体在7大领域下所有指标的计算值。

    - entity_id: 实体唯一标识
    - 安全约束：entity_id 仅允许字母数字下划线和连字符，防止 SPARQL 注入
    - 性能约束：SPARQL 查询超时 30 秒，结果集上限 1000 条
    - 不返回 status 字段，由前端根据 threshold + direction 计算
    """
    sparql = f"""
PREFIX ctio: <urn:ctio:>
SELECT ?indicatorId ?name ?domain ?unit ?value ?thresholdLow ?thresholdHigh ?direction
WHERE {{
  ?ind a ctio:RegulatoryIndicator ;
       ctio:indicatorId ?indicatorId ;
       ctio:indicatorName ?name ;
       ctio:domain ?domain ;
       ctio:currentValue ?value .
  ?ind ctio:affectsEntity <urn:entity:{entity_id}> .
  OPTIONAL {{ ?ind ctio:unit ?unit . }}
  OPTIONAL {{ ?ind ctio:thresholdLow ?thresholdLow . }}
  OPTIONAL {{ ?ind ctio:thresholdHigh ?thresholdHigh . }}
  OPTIONAL {{ ?ind ctio:direction ?direction . }}
}}
LIMIT 1000
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error(
            "指标查询失败: entity_id=%s err=%s", entity_id, exc
        )
        raise HTTPException(
            status_code=500, detail="数据查询失败，请稍后重试"
        ) from exc

    results: list[IndicatorResponse] = []
    for row in rows:
        indicator_id = row.get("indicatorId", "")
        if not indicator_id:
            continue

        # 后端域名 → 前端领域 ID 映射
        backend_domain = row.get("domain", "")
        frontend_domain = _DOMAIN_MAP.get(backend_domain, backend_domain)

        threshold_low = _safe_float(row.get("thresholdLow"))
        threshold_high = _safe_float(row.get("thresholdHigh"))

        value_raw = row.get("value")
        value = _safe_float(value_raw)
        # 若无法转为数值，保留原始字符串
        if value is None and value_raw is not None:
            value = value_raw  # type: ignore[assignment]

        results.append(
            IndicatorResponse(
                id=indicator_id,
                name=row.get("name", ""),
                domain=frontend_domain,
                unit=row.get("unit", ""),
                value=value,
                threshold=[threshold_low, threshold_high],
                direction=row.get("direction", "up") or "up",
            )
        )

    return results
