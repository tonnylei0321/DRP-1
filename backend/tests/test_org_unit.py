"""组织架构 API 单元测试 — /org/tree 和 /org/{entity_id}/relations。

覆盖场景：
  1. GET /org/tree 正常查询（多层实体数据，验证树结构）
  2. GET /org/tree 空结果（返回默认空根节点）
  3. GET /org/tree max_depth 边界（max_depth=1 只返回1层）
  4. GET /org/tree SPARQL 失败（返回 500）
  5. GET /org/tree root_id 参数（指定子树查询）
  6. GET /org/{entity_id}/relations 正常查询
  7. GET /org/{entity_id}/relations 空结果
  8. GET /org/{entity_id}/relations SPARQL 失败
  9. GET /org/{entity_id}/relations entity_id 非法字符

运行: cd backend && python -m pytest tests/test_org_unit.py -v
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

# 多层实体 SPARQL 返回数据（集团 → 华东子集团 → 上海子公司）
_MULTI_LEVEL_ROWS = [
    {
        "entity": "urn:entity:group",
        "name": "中央企业集团",
        "level": "0",
        "type": "集团",
        "city": "北京",
        "parent": None,
        "cash": "4868000",
        "debt": "3421000",
        "asset": "18624000",
        "guarantee": "1286000",
        "compliance": "92.4",
        "risk": "lo",
        "hasChildren": "true",
    },
    {
        "entity": "urn:entity:east_group",
        "name": "华东子集团",
        "level": "1",
        "type": "二级子集团",
        "city": "上海",
        "parent": "urn:entity:group",
        "cash": "1200000",
        "debt": "800000",
        "asset": "5000000",
        "guarantee": "300000",
        "compliance": "88.5",
        "risk": "md",
        "hasChildren": "true",
    },
    {
        "entity": "urn:entity:sh_company",
        "name": "上海子公司",
        "level": "2",
        "type": "三级子公司",
        "city": "上海",
        "parent": "urn:entity:east_group",
        "cash": "500000",
        "debt": "200000",
        "asset": "1500000",
        "guarantee": "100000",
        "compliance": "95.0",
        "risk": "lo",
        "hasChildren": "false",
    },
]

# 关系数据
_RELATION_ROWS = [
    {
        "source": "urn:entity:east_group",
        "target": "urn:entity:group",
        "relType": "hasSubsidiary",
    },
    {
        "source": "urn:entity:east_group",
        "target": "urn:entity:group",
        "relType": "fundFlow",
    },
    {
        "source": "urn:entity:group",
        "target": "urn:entity:east_group",
        "relType": "guarantee",
    },
]


# ---------------------------------------------------------------------------
# 1. GET /org/tree 正常查询 — 多层实体数据，验证树结构正确
# ---------------------------------------------------------------------------

async def test_org_tree_normal(authenticated_app):
    """正常查询：mock SPARQL 返回多层实体数据，验证树结构正确。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=_MULTI_LEVEL_ROWS,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree")

    assert resp.status_code == 200
    body = resp.json()
    # 根节点是集团
    assert body["id"] == "group"
    assert body["name"] == "中央企业集团"
    assert body["level"] == 0
    # 根节点有子节点
    assert len(body["children"]) == 1
    child = body["children"][0]
    assert child["id"] == "east_group"
    assert child["name"] == "华东子集团"
    # 二级节点有子节点
    assert len(child["children"]) == 1
    assert child["children"][0]["id"] == "sh_company"


# ---------------------------------------------------------------------------
# 2. GET /org/tree 空结果 — 返回默认空根节点
# ---------------------------------------------------------------------------

async def test_org_tree_empty(authenticated_app):
    """空结果：mock SPARQL 返回空列表，验证返回默认空根节点。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "root"
    assert body["name"] == "未知"
    assert body["level"] == 0


# ---------------------------------------------------------------------------
# 3. GET /org/tree max_depth 边界 — max_depth=1 只返回1层
# ---------------------------------------------------------------------------

async def test_org_tree_max_depth_1(authenticated_app):
    """max_depth=1：只返回根节点和第1层，不包含第2层。"""
    # 只返回 level <= 1 的行（模拟 SPARQL FILTER）
    rows_depth1 = [r for r in _MULTI_LEVEL_ROWS if int(r["level"]) <= 1]
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=rows_depth1,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree", params={"max_depth": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "group"
    # 有1层子节点
    assert len(body["children"]) == 1
    child = body["children"][0]
    assert child["id"] == "east_group"
    # 第2层不应出现
    assert len(child["children"]) == 0


# ---------------------------------------------------------------------------
# 4. GET /org/tree SPARQL 失败 — 返回 500
# ---------------------------------------------------------------------------

async def test_org_tree_sparql_error(authenticated_app):
    """SPARQL 失败：mock 抛异常，验证返回 500。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        side_effect=Exception("GraphDB 连接超时"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree")

    assert resp.status_code == 500
    body = resp.json()
    assert "detail" in body
    assert "数据查询失败" in body["detail"]


# ---------------------------------------------------------------------------
# 5. GET /org/tree root_id 参数 — 指定 root_id 查询子树
# ---------------------------------------------------------------------------

async def test_org_tree_with_root_id(authenticated_app):
    """root_id 参数：指定子树根节点，验证返回以该节点为根的子树。"""
    # 模拟返回 east_group 及其子节点
    subtree_rows = [r for r in _MULTI_LEVEL_ROWS if r["entity"] != "urn:entity:group"]
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=subtree_rows,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree", params={"root_id": "east_group"})

    assert resp.status_code == 200
    body = resp.json()
    # 根节点应该是 east_group
    assert body["id"] == "east_group"
    assert body["name"] == "华东子集团"
    assert len(body["children"]) == 1
    assert body["children"][0]["id"] == "sh_company"


# ---------------------------------------------------------------------------
# 6. GET /org/{entity_id}/relations 正常查询
# ---------------------------------------------------------------------------

async def test_relations_normal(authenticated_app):
    """正常查询：mock 返回关系数据，验证结果正确。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=_RELATION_ROWS,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/east_group/relations")

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 3
    # 验证关系类型
    types = {r["type"] for r in body}
    assert types == {"hasSubsidiary", "fundFlow", "guarantee"}
    # 验证 source/target 已从 IRI 提取 ID
    for rel in body:
        assert rel["source"] in ("east_group", "group")
        assert rel["target"] in ("east_group", "group")


# ---------------------------------------------------------------------------
# 7. GET /org/{entity_id}/relations 空结果
# ---------------------------------------------------------------------------

async def test_relations_empty(authenticated_app):
    """空结果：mock SPARQL 返回空列表，验证返回空数组。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/some-entity/relations")

    assert resp.status_code == 200
    body = resp.json()
    assert body == []


# ---------------------------------------------------------------------------
# 8. GET /org/{entity_id}/relations SPARQL 失败
# ---------------------------------------------------------------------------

async def test_relations_sparql_error(authenticated_app):
    """SPARQL 失败：mock 抛异常，验证返回 500。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        side_effect=Exception("SPARQL 执行超时"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/east_group/relations")

    assert resp.status_code == 500
    body = resp.json()
    assert "数据查询失败" in body["detail"]


# ---------------------------------------------------------------------------
# 9. GET /org/{entity_id}/relations entity_id 非法字符 — 返回 422
# ---------------------------------------------------------------------------

async def test_relations_invalid_entity_id(authenticated_app):
    """entity_id 非法字符：包含特殊字符时返回 422 校验错误。"""
    with patch(
        "drp.org.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            # 包含 SPARQL 注入字符
            resp = await client.get("/org/evil%3B%20DROP/relations")

    assert resp.status_code == 422
