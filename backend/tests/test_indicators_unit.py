"""指标 API 单元测试 — GET /indicators/{entity_id}。

覆盖场景：
  1. 正常查询 — mock 返回指标数据，验证域名映射正确
  2. 空结果 — 返回空数组
  3. SPARQL 失败 — 返回 500
  4. 域名映射 — 验证后端7大业务域→前端领域 ID 映射
  5. entity_id 非法字符 — 返回 422

运行: cd backend && python -m pytest tests/test_indicators_unit.py -v
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FAKE_USER = TokenPayload(
    sub="test-user-001",
    tenant_id="tenant-unit",
    email="unit@test.com",
    permissions=[],
    exp=9999999999,
)


@pytest.fixture()
def authenticated_app():
    """覆盖 get_current_user 依赖，绕过真实 JWT 校验。"""
    app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
    yield app
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mock 数据
# ---------------------------------------------------------------------------

_INDICATOR_ROWS = [
    {
        "indicatorId": "f01",
        "name": "资金归集率",
        "domain": "银行账户",
        "unit": "%",
        "value": "87.5",
        "thresholdLow": "85",
        "thresholdHigh": "95",
        "direction": "up",
    },
    {
        "indicatorId": "d01",
        "name": "资产负债率",
        "domain": "债务融资",
        "unit": "%",
        "value": "65.3",
        "thresholdLow": None,
        "thresholdHigh": "70",
        "direction": "down",
    },
    {
        "indicatorId": "g01",
        "name": "风险决策评分",
        "domain": "决策风险",
        "unit": "分",
        "value": "88",
        "thresholdLow": "80",
        "thresholdHigh": "100",
        "direction": "mid",
    },
]


# ---------------------------------------------------------------------------
# 1. GET /indicators/{entity_id} 正常查询 — 验证域名映射正确
# ---------------------------------------------------------------------------

async def test_indicators_normal(authenticated_app):
    """正常查询：mock 返回指标数据，验证响应结构和域名映射。"""
    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        return_value=_INDICATOR_ROWS,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/indicators/test-entity-001")

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 3

    # 验证第一个指标
    ind0 = body[0]
    assert ind0["id"] == "f01"
    assert ind0["name"] == "资金归集率"
    assert ind0["domain"] == "fund"  # 银行账户 → fund
    assert ind0["unit"] == "%"
    assert ind0["value"] == 87.5
    assert ind0["threshold"] == [85.0, 95.0]
    assert ind0["direction"] == "up"

    # 验证域名映射
    assert body[1]["domain"] == "debt"       # 债务融资 → debt
    assert body[2]["domain"] == "guarantee"  # 决策风险 → guarantee


# ---------------------------------------------------------------------------
# 2. GET /indicators/{entity_id} 空结果 — 返回空数组
# ---------------------------------------------------------------------------

async def test_indicators_empty(authenticated_app):
    """空结果：mock SPARQL 返回空列表，验证返回空数组。"""
    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/indicators/test-entity-001")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# 3. GET /indicators/{entity_id} SPARQL 失败 — 返回 500
# ---------------------------------------------------------------------------

async def test_indicators_sparql_error(authenticated_app):
    """SPARQL 失败：mock 抛异常，验证返回 500。"""
    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        side_effect=Exception("GraphDB 连接超时"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/indicators/test-entity-001")

    assert resp.status_code == 500
    body = resp.json()
    assert "数据查询失败" in body["detail"]


# ---------------------------------------------------------------------------
# 4. GET /indicators/{entity_id} 域名映射 — 验证全部7种映射
# ---------------------------------------------------------------------------

async def test_indicators_domain_mapping(authenticated_app):
    """域名映射：验证后端7大业务域→前端领域 ID 映射正确。

    映射规则：
      银行账户 → fund
      资金集中 → fund
      债务融资 → debt
      决策风险 → guarantee
      票据     → derivative
      结算(编号<056) → finbiz
      结算(编号>=056) → invest
      国资委考核 → overseas
    """
    domain_rows = [
        {"indicatorId": "001", "name": "银行账户指标", "domain": "银行账户",
         "unit": "", "value": "1", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "033", "name": "资金集中指标", "domain": "资金集中",
         "unit": "", "value": "2", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "079", "name": "债务融资指标", "domain": "债务融资",
         "unit": "", "value": "3", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "086", "name": "决策风险指标", "domain": "决策风险",
         "unit": "", "value": "4", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "069", "name": "票据指标", "domain": "票据",
         "unit": "", "value": "5", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "042", "name": "结算指标(finbiz)", "domain": "结算",
         "unit": "", "value": "6", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "056", "name": "结算指标(invest)", "domain": "结算",
         "unit": "", "value": "7", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
        {"indicatorId": "098", "name": "国资委考核指标", "domain": "国资委考核",
         "unit": "", "value": "8", "thresholdLow": None, "thresholdHigh": None, "direction": "up"},
    ]

    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        return_value=domain_rows,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/indicators/test-entity-001")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 8

    # 按 indicatorId 建立映射方便断言
    by_id = {ind["id"]: ind["domain"] for ind in body}

    assert by_id["001"] == "fund"        # 银行账户 → fund
    assert by_id["033"] == "fund"        # 资金集中 → fund
    assert by_id["079"] == "debt"        # 债务融资 → debt
    assert by_id["086"] == "guarantee"   # 决策风险 → guarantee
    assert by_id["069"] == "derivative"  # 票据 → derivative
    assert by_id["042"] == "finbiz"      # 结算(编号<056) → finbiz
    assert by_id["056"] == "invest"      # 结算(编号>=056) → invest
    assert by_id["098"] == "overseas"    # 国资委考核 → overseas


# ---------------------------------------------------------------------------
# 5. GET /indicators/{entity_id} entity_id 非法字符 — 返回 422
# ---------------------------------------------------------------------------

async def test_indicators_invalid_entity_id(authenticated_app):
    """entity_id 非法字符：包含特殊字符时返回 422 校验错误。"""
    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            # 包含 SPARQL 注入字符
            resp = await client.get("/indicators/evil%3B%20DROP")

    assert resp.status_code == 422
