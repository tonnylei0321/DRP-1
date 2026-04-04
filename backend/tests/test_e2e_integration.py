"""端到端集成测试 — 前后端集成场景验证。

覆盖 4 个集成测试场景：
  场景1：登录 → 加载组织架构 → 选中实体 → 查看指标（完整用户流程）
  场景2：穿透钻取 → 面包屑回退（多层级导航）
  场景3：指标异常 → 穿透路径 → 报告下载（风险追溯流程）
  场景4：多租户隔离 — 不同 tenant_id 返回不同数据

技术方案：
  - pytest + httpx.AsyncClient（FastAPI TestClient）
  - mock SPARQL_Proxy 返回模拟数据（不依赖真实 GraphDB）
  - mock get_current_user 返回不同 tenant_id 的用户
  - 每个场景是一个独立的 async test 函数

运行方式：
    cd backend && python -m pytest tests/test_e2e_integration.py -v
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

def _make_user(tenant_id: str = "tenant-e2e", sub: str = "user-e2e") -> TokenPayload:
    """构造模拟用户 TokenPayload。"""
    return TokenPayload(
        sub=sub,
        tenant_id=tenant_id,
        email=f"{sub}@test.com",
        permissions=[],
        exp=9999999999,
    )


# 组织架构 mock 数据：集团 → 华东子集团 → 上海子公司
_ORG_TREE_ROWS = [
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
]

# 子树 mock 数据：华东子集团 → 上海子公司
_SUBTREE_ROWS = [
    {
        "entity": "urn:entity:east_group",
        "name": "华东子集团",
        "level": "0",
        "type": "二级子集团",
        "city": "上海",
        "parent": None,
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
        "level": "1",
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

# 指标 mock 数据
_INDICATOR_ROWS = [
    {
        "indicatorId": "f01",
        "name": "资金归集率",
        "domain": "资金集中",
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
        "value": "65.2",
        "thresholdLow": None,
        "thresholdHigh": "70",
        "direction": "down",
    },
]

# 穿透路径 mock 数据
_DRILL_PATH_ROWS = [
    {"step": "1", "node": "urn:ind:f01", "nodeType": "RegulatoryIndicator", "nodeLabel": "资金归集率"},
    {"step": "2", "node": "urn:entity:east_group", "nodeType": "LegalEntity", "nodeLabel": "华东子集团"},
    {"step": "3", "node": "urn:entity:acct-001", "nodeType": "Account", "nodeLabel": "ACC-001"},
]



# ---------------------------------------------------------------------------
# 场景1：登录 → 加载组织架构 → 选中实体 → 查看指标（完整用户流程）
# ---------------------------------------------------------------------------

async def test_scenario1_login_org_tree_select_entity_view_indicators():
    """场景1：完整用户流程。

    步骤：
      1. POST /auth/login（mock AuthService）获取 token
      2. GET /org/tree 加载组织架构树
      3. GET /indicators/{entity_id} 查看选中实体的指标数据

    验证：
      - 登录返回 access_token
      - 组织架构树包含根节点和子节点
      - 指标数据包含正确的领域和值
    """
    # --- Step 1: 登录 ---
    # 通过 dependency_overrides mock AuthService 依赖
    from drp.auth.router import _get_auth_service
    from drp.auth.schemas import TokenResponse

    mock_svc = AsyncMock()
    mock_svc.login.return_value = TokenResponse(
        access_token="fake-jwt-token",
        token_type="bearer",
        expires_in=3600,
    )
    app.dependency_overrides[_get_auth_service] = lambda: mock_svc
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_resp = await client.post(
                "/auth/login",
                json={"email": "admin@test.com", "password": "secret123"},
            )
    finally:
        app.dependency_overrides.pop(_get_auth_service, None)

    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    # --- Step 2 & 3: 使用认证用户访问 API ---
    fake_user = _make_user("tenant-e2e")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        # Step 2: 加载组织架构
        with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=_ORG_TREE_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                org_resp = await client.get("/org/tree")

        assert org_resp.status_code == 200
        org_tree = org_resp.json()
        assert org_tree["id"] == "group"
        assert org_tree["name"] == "中央企业集团"
        assert len(org_tree["children"]) == 1
        assert org_tree["children"][0]["id"] == "east_group"

        # Step 3: 选中实体 → 查看指标
        with patch("drp.indicators.router.sparql_query", new_callable=AsyncMock, return_value=_INDICATOR_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                ind_resp = await client.get("/indicators/east_group")

        assert ind_resp.status_code == 200
        indicators = ind_resp.json()
        assert len(indicators) == 2
        # 验证域名映射：资金集中 → fund
        domains = {ind["domain"] for ind in indicators}
        assert "fund" in domains
        assert "debt" in domains
        # 验证指标值
        fund_ind = next(i for i in indicators if i["id"] == "f01")
        assert fund_ind["value"] == 87.5
        assert fund_ind["direction"] == "up"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 场景2：穿透钻取 → 面包屑回退（多层级导航）
# ---------------------------------------------------------------------------

async def test_scenario2_drill_down_and_breadcrumb_back():
    """场景2：穿透钻取 → 面包屑回退。

    步骤：
      1. GET /org/tree?max_depth=2 加载初始组织架构（2层）
      2. GET /org/tree?root_id=east_group&max_depth=1 穿透到华东子集团
      3. 验证子树数据正确（模拟面包屑回退时使用已加载数据）

    验证：
      - 初始树包含2层节点
      - 穿透后返回以 east_group 为根的子树
      - 子树包含下级子公司
    """
    fake_user = _make_user("tenant-e2e")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        # Step 1: 初始加载 max_depth=2
        with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=_ORG_TREE_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp1 = await client.get("/org/tree", params={"max_depth": 2})

        assert resp1.status_code == 200
        tree = resp1.json()
        assert tree["id"] == "group"
        assert tree["level"] == 0
        assert len(tree["children"]) >= 1

        # Step 2: 穿透钻取 — 以 east_group 为根，max_depth=1
        with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=_SUBTREE_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp2 = await client.get(
                    "/org/tree",
                    params={"root_id": "east_group", "max_depth": 1},
                )

        assert resp2.status_code == 200
        subtree = resp2.json()
        assert subtree["id"] == "east_group"
        assert subtree["name"] == "华东子集团"
        assert len(subtree["children"]) == 1
        assert subtree["children"][0]["id"] == "sh_company"
        assert subtree["children"][0]["name"] == "上海子公司"

        # Step 3: 面包屑回退 — 重新请求根树（模拟前端使用缓存或重新请求）
        with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=_ORG_TREE_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp3 = await client.get("/org/tree", params={"max_depth": 2})

        assert resp3.status_code == 200
        root_tree = resp3.json()
        assert root_tree["id"] == "group"
        assert root_tree["name"] == "中央企业集团"
    finally:
        app.dependency_overrides.clear()



# ---------------------------------------------------------------------------
# 场景3：指标异常 → 穿透路径 → 报告下载（风险追溯流程）
# ---------------------------------------------------------------------------

async def test_scenario3_anomaly_drill_path_report_download():
    """场景3：风险追溯流程。

    步骤：
      1. GET /drill/path/{indicator_id} 查询穿透路径
      2. GET /drill/report/{indicator_id} 下载溯源报告

    验证：
      - 穿透路径包含3个步骤（指标→法人→账户）
      - 报告下载返回有效内容（JSON 或 PDF）
      - 报告 Content-Disposition 包含正确的文件名
    """
    fake_user = _make_user("tenant-e2e")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        indicator_id = "f01"

        # Step 1: 查询穿透路径
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=_DRILL_PATH_ROWS):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                path_resp = await client.get(f"/drill/path/{indicator_id}")

        assert path_resp.status_code == 200
        path_data = path_resp.json()
        assert len(path_data) == 3
        # 验证步骤顺序
        assert path_data[0]["step"] == 1
        assert path_data[0]["node_type"] == "RegulatoryIndicator"
        assert path_data[1]["step"] == 2
        assert path_data[1]["node_type"] == "LegalEntity"
        assert path_data[2]["step"] == 3
        assert path_data[2]["node_type"] == "Account"

        # Step 2: 下载溯源报告（mock sparql_query 使报告内含数据）
        # drill/report 内部调用 get_entities_by_indicator 和 get_drill_path
        mock_entities = [
            {"entity": "urn:entity:east_group", "entityName": "华东子集团", "value": "0.8"},
        ]
        with patch("drp.drill.router.sparql_query", new_callable=AsyncMock) as mock_sq:
            # 第一次调用：get_entities_by_indicator
            # 第二次调用：get_drill_path
            mock_sq.side_effect = [mock_entities, _DRILL_PATH_ROWS]
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                report_resp = await client.get(f"/drill/report/{indicator_id}")

        assert report_resp.status_code == 200
        content_type = report_resp.headers.get("content-type", "")
        assert "application/json" in content_type or "application/pdf" in content_type
        # 验证 Content-Disposition 包含文件名
        content_disp = report_resp.headers.get("content-disposition", "")
        assert f"drill_report_{indicator_id}" in content_disp

        # 如果是 JSON 报告，验证内容结构
        if "application/json" in content_type:
            import json
            report_data = json.loads(report_resp.content.decode("utf-8"))
            assert report_data["indicator_id"] == indicator_id
            assert "generated_at" in report_data
            assert "entities" in report_data
            assert "path" in report_data
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 场景4：多租户隔离 — 不同 tenant_id 返回不同数据
# ---------------------------------------------------------------------------

async def test_scenario4_multi_tenant_isolation():
    """场景4：多租户隔离验证。

    步骤：
      1. 租户A 请求 /org/tree，验证 sparql_query 被调用时传入 tenant_id='tenant-A'
      2. 租户B 请求 /org/tree，验证 sparql_query 被调用时传入 tenant_id='tenant-B'

    验证：
      - 两个租户的 sparql_query 调用分别传入了正确的 tenant_id
      - 返回的数据来自各自的 mock（不同租户看到不同数据）
    """
    # 租户A 的组织架构数据
    tenant_a_rows = [
        {
            "entity": "urn:entity:group_a",
            "name": "央企集团A",
            "level": "0",
            "type": "集团",
            "city": "北京",
            "parent": None,
            "cash": "5000000",
            "debt": "3000000",
            "asset": "20000000",
            "guarantee": "1000000",
            "compliance": "90.0",
            "risk": "lo",
            "hasChildren": "false",
        },
    ]

    # 租户B 的组织架构数据
    tenant_b_rows = [
        {
            "entity": "urn:entity:group_b",
            "name": "央企集团B",
            "level": "0",
            "type": "集团",
            "city": "深圳",
            "parent": None,
            "cash": "3000000",
            "debt": "2000000",
            "asset": "15000000",
            "guarantee": "800000",
            "compliance": "85.0",
            "risk": "md",
            "hasChildren": "false",
        },
    ]

    # --- 租户A 请求 ---
    user_a = _make_user(tenant_id="tenant-A", sub="user-a")
    app.dependency_overrides[get_current_user] = lambda: user_a

    with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=tenant_a_rows) as mock_sq_a:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp_a = await client.get("/org/tree")

    assert resp_a.status_code == 200
    tree_a = resp_a.json()
    assert tree_a["id"] == "group_a"
    assert tree_a["name"] == "央企集团A"

    # 验证 sparql_query 被调用时传入了 tenant_id='tenant-A'
    mock_sq_a.assert_called_once()
    call_kwargs_a = mock_sq_a.call_args
    assert call_kwargs_a.kwargs.get("tenant_id") == "tenant-A" or \
        (len(call_kwargs_a.args) > 1 and call_kwargs_a.args[1] == "tenant-A")

    # --- 租户B 请求 ---
    user_b = _make_user(tenant_id="tenant-B", sub="user-b")
    app.dependency_overrides[get_current_user] = lambda: user_b

    with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=tenant_b_rows) as mock_sq_b:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp_b = await client.get("/org/tree")

    assert resp_b.status_code == 200
    tree_b = resp_b.json()
    assert tree_b["id"] == "group_b"
    assert tree_b["name"] == "央企集团B"
    assert tree_b["city"] == "深圳"

    # 验证 sparql_query 被调用时传入了 tenant_id='tenant-B'
    mock_sq_b.assert_called_once()
    call_kwargs_b = mock_sq_b.call_args
    assert call_kwargs_b.kwargs.get("tenant_id") == "tenant-B" or \
        (len(call_kwargs_b.args) > 1 and call_kwargs_b.args[1] == "tenant-B")

    # 验证两个租户返回的数据不同
    assert tree_a["id"] != tree_b["id"]
    assert tree_a["name"] != tree_b["name"]

    app.dependency_overrides.clear()
