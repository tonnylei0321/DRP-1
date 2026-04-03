"""第7章：指标计算引擎单元测试。"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drp.indicators.calculator import (
    IndicatorResult,
    _check_compliance,
    _publish_risk_event,
    _redis_key,
    _update_graphdb,
    _write_redis_cache,
    calculate_all_domains,
    calculate_domain,
)
from drp.indicators.registry import INDICATOR_BY_ID, INDICATORS


# ─── registry 基础校验 ──────────────────────────────────────────────────────────

def test_indicators_总数为106():
    assert len(INDICATORS) == 106


def test_indicators_id_唯一():
    ids = [ind["id"] for ind in INDICATORS]
    assert len(ids) == len(set(ids))


def test_indicators_包含关键指标():
    assert "009" in INDICATOR_BY_ID  # 直联率
    assert "033" in INDICATOR_BY_ID  # 资金集中率
    assert "043" in INDICATOR_BY_ID  # 结算率
    assert "086" in INDICATOR_BY_ID  # 风险事件数
    assert "098" in INDICATOR_BY_ID  # 监管指标达标率


def test_indicators_必要字段完整():
    for ind in INDICATORS:
        assert "id" in ind
        assert "domain" in ind
        assert "name" in ind
        assert "sparql" in ind
        assert "target_value" in ind
        assert "threshold" in ind


def test_indicators_覆盖7个业务域():
    domains = {ind["domain"] for ind in INDICATORS}
    expected = {"银行账户", "资金集中", "结算", "票据", "债务融资", "决策风险", "国资委考核"}
    assert domains == expected


# ─── 达标判断 ─────────────────────────────────────────────────────────────────

def test_check_compliance_无目标默认达标():
    ind = {"target_value": None, "threshold": None}
    assert _check_compliance(ind, 0.5) is True


def test_check_compliance_比率指标达标():
    ind = {"target_value": 1.0, "threshold": 0.95}
    assert _check_compliance(ind, 0.97) is True
    assert _check_compliance(ind, 0.94) is False


def test_check_compliance_目标为0的指标():
    # 风险事件数：目标 0，阈值 5，值 ≤ 5 为达标
    ind = {"target_value": 0, "threshold": 5}
    assert _check_compliance(ind, 3.0) is True
    assert _check_compliance(ind, 6.0) is False


def test_check_compliance_值为None返回不达标():
    ind = {"target_value": 1.0, "threshold": 0.9}
    assert _check_compliance(ind, None) is False


def test_redis_key_格式():
    key = _redis_key("tenant-abc", "009")
    assert key == "kpi:tenant-abc:009"


# ─── Redis 缓存写入 ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_write_redis_cache_调用setex():
    mock_redis = AsyncMock()
    result = IndicatorResult(
        indicator_id="009", tenant_id="t1", value=0.97, is_compliant=True
    )
    await _write_redis_cache(result, redis_client=mock_redis)

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    key = call_args[0][0]
    ttl = call_args[0][1]
    payload = json.loads(call_args[0][2])

    assert key == "kpi:t1:009"
    assert ttl == 3600
    assert payload["value"] == 0.97
    assert payload["is_compliant"] is True


@pytest.mark.asyncio
async def test_write_redis_cache_失败不抛异常():
    """Redis 写入失败时，不应向外抛出异常（仅日志）。"""
    mock_redis = AsyncMock()
    mock_redis.setex.side_effect = Exception("Redis 连接失败")
    result = IndicatorResult(
        indicator_id="001", tenant_id="t1", value=10.0, is_compliant=True
    )
    # 不应抛出
    await _write_redis_cache(result, redis_client=mock_redis)


# ─── GraphDB 写回 ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_graphdb_调用sparql_update():
    result = IndicatorResult(
        indicator_id="009", tenant_id="t1", value=0.97, is_compliant=True
    )
    mock_client = AsyncMock()

    with patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock) as mock_update:
        await _update_graphdb(result, "t1", client=mock_client)
        mock_update.assert_called_once()
        # 验证 SPARQL 包含指标 ID 和值
        call_sparql = mock_update.call_args[0][0]
        assert "009" in call_sparql
        assert "0.97" in call_sparql
        assert "true" in call_sparql


@pytest.mark.asyncio
async def test_update_graphdb_失败不抛异常():
    result = IndicatorResult(
        indicator_id="009", tenant_id="t1", value=0.97, is_compliant=True
    )
    with patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock) as mock_update:
        mock_update.side_effect = Exception("GraphDB 连接失败")
        # 不应抛出
        await _update_graphdb(result, "t1")


# ─── Pub/Sub 风险事件 ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_publish_risk_event_达标不发布():
    mock_redis = AsyncMock()
    indicator = INDICATOR_BY_ID["009"]
    result = IndicatorResult(
        indicator_id="009", tenant_id="t1", value=0.97, is_compliant=True
    )
    await _publish_risk_event(indicator, result, redis_client=mock_redis)
    mock_redis.publish.assert_not_called()


@pytest.mark.asyncio
async def test_publish_risk_event_不达标发布():
    mock_redis = AsyncMock()
    indicator = INDICATOR_BY_ID["009"]
    result = IndicatorResult(
        indicator_id="009", tenant_id="t1", value=0.5, is_compliant=False
    )
    await _publish_risk_event(indicator, result, redis_client=mock_redis)
    mock_redis.publish.assert_called_once()
    channel, payload = mock_redis.publish.call_args[0]
    assert channel == "risk_events"
    event = json.loads(payload)
    assert event["indicator_id"] == "009"
    assert event["tenant_id"] == "t1"
    assert event["type"] == "risk_event"


@pytest.mark.asyncio
async def test_publish_risk_event_失败不抛异常():
    mock_redis = AsyncMock()
    mock_redis.publish.side_effect = Exception("Redis 不可达")
    indicator = INDICATOR_BY_ID["086"]
    result = IndicatorResult(
        indicator_id="086", tenant_id="t1", value=10.0, is_compliant=False
    )
    # 不应抛出
    await _publish_risk_event(indicator, result, redis_client=mock_redis)


# ─── calculate_domain 集成 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_calculate_domain_全部调用完成():
    """模拟 SPARQL 返回结果，验证 calculate_domain 能正确处理所有指标。"""
    mock_redis = AsyncMock()

    # 只测 "决策风险" 域（12 条指标，含 086/087 有意义指标）
    domain_ids = [ind["id"] for ind in INDICATORS if ind["domain"] == "决策风险"]

    with patch("drp.indicators.calculator.sparql_query", new_callable=AsyncMock) as mock_q, \
         patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock):
        mock_q.return_value = [{"value": "3"}]  # 模拟所有指标返回值为 3

        results = await calculate_domain(
            "决策风险", domain_ids, "tenant-test",
            redis_client=mock_redis,
        )

    assert len(results) == len(domain_ids)
    # 086 目标为 0，阈值 5，值 3 ≤ 5，应达标
    ind086 = next(r for r in results if r.indicator_id == "086")
    assert ind086.is_compliant is True
    assert ind086.value == 3.0


@pytest.mark.asyncio
async def test_calculate_domain_sparql失败不中断():
    """单条指标 SPARQL 执行失败时，其他指标正常继续。"""
    domain_ids = ["086", "087"]

    call_count = 0

    async def _side_effect(sparql, tenant_id=None, client=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("超时")
        return [{"value": "0"}]

    with patch("drp.indicators.calculator.sparql_query", side_effect=_side_effect), \
         patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock), \
         patch("drp.indicators.calculator._write_redis_cache", new_callable=AsyncMock), \
         patch("drp.indicators.calculator._publish_risk_event", new_callable=AsyncMock):

        results = await calculate_domain(
            "决策风险", domain_ids, "tenant-test",
        )

    assert len(results) == 2
    assert results[0].value is None  # 第一条失败
    assert results[1].value == 0.0   # 第二条成功


@pytest.mark.asyncio
async def test_calculate_all_domains_返回全7域():
    with patch("drp.indicators.calculator.sparql_query", new_callable=AsyncMock) as mock_q, \
         patch("drp.indicators.calculator.sparql_update", new_callable=AsyncMock), \
         patch("drp.indicators.calculator._write_redis_cache", new_callable=AsyncMock), \
         patch("drp.indicators.calculator._publish_risk_event", new_callable=AsyncMock):
        mock_q.return_value = [{"value": "1"}]

        all_results = await calculate_all_domains("t1")

    assert len(all_results) == 7
    total = sum(len(v) for v in all_results.values())
    assert total == 106
