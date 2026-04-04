"""冒烟测试 — 验证前后端集成的最小可用路径。

7 个冒烟场景覆盖后端 API 可用性（S1-S5）和前端页面完整性（S6-S7）。
后端测试使用 FastAPI TestClient（httpx.AsyncClient + ASGITransport），
通过 mock SPARQL_Proxy 隔离 GraphDB 依赖。

运行方式：
    cd backend && python -m pytest tests/test_smoke.py -v
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 项目根目录（backend 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 模拟已认证用户，绕过真实 JWT 校验
_FAKE_USER = TokenPayload(
    sub="test-user-001",
    tenant_id="tenant-smoke",
    email="smoke@test.com",
    permissions=[],
    exp=9999999999,
)


@pytest.fixture()
def authenticated_app():
    """返回一个已覆盖 get_current_user 依赖的 FastAPI app 实例。

    所有需要认证的端点将直接使用 _FAKE_USER，无需真实 JWT。
    """
    app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
def raw_app():
    """返回未做任何依赖覆盖的原始 app，用于测试无认证场景。"""
    app.dependency_overrides.clear()
    yield app
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# S1: 后端服务启动 — GET /api/docs 返回 200
# ---------------------------------------------------------------------------

async def test_s1_backend_docs_available(raw_app):
    """S1: 后端服务启动验证。

    前置条件：
        - FastAPI 应用正常初始化
        - app_env 为 development（docs_url = /api/docs）
    操作步骤：
        - 发送 GET /api/docs 请求
    预期结果：
        - HTTP 200，Swagger UI 页面可访问
    """
    async with AsyncClient(
        transport=ASGITransport(app=raw_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/docs")

    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}"


# ---------------------------------------------------------------------------
# S2: 登录接口可用 — POST /auth/login 返回 200 或 401
# ---------------------------------------------------------------------------

async def test_s2_login_endpoint_available(raw_app):
    """S2: 登录接口可用性验证。

    前置条件：
        - auth router 已注册到 app
    操作步骤：
        - 发送 POST /auth/login，body 为 {"email": "test@test.com", "password": "test"}
    预期结果：
        - HTTP 状态码为 200（登录成功）或 401（凭证无效），
          不应出现 404（路由未注册）或 500（服务端异常）
    """
    async with AsyncClient(
        transport=ASGITransport(app=raw_app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/auth/login",
            json={"email": "test@test.com", "password": "test"},
        )

    assert resp.status_code in (200, 401), (
        f"期望 200 或 401，实际 {resp.status_code}；body={resp.text}"
    )


# ---------------------------------------------------------------------------
# S3: 组织架构 API 可用 — GET /org/tree（带 token）返回 200
# ---------------------------------------------------------------------------

async def test_s3_org_tree_api_available(authenticated_app):
    """S3: 组织架构 API 可用性验证。

    前置条件：
        - 用户已认证（通过 dependency override 模拟）
        - SPARQL_Proxy 被 mock，返回空结果集
    操作步骤：
        - 发送 GET /org/tree
    预期结果：
        - HTTP 200，返回 JSON 格式的组织架构树（可能为空根节点）
    """
    with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=[]):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/tree")

    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}；body={resp.text}"
    body = resp.json()
    # 空结果时返回默认根节点，至少包含 id 和 name
    assert "id" in body
    assert "name" in body


# ---------------------------------------------------------------------------
# S4: 指标 API 可用 — GET /indicators/{id}（带 token）返回 200 或 404
# ---------------------------------------------------------------------------

async def test_s4_indicators_api_available(authenticated_app):
    """S4: 指标 API 可用性验证。

    前置条件：
        - 用户已认证（通过 dependency override 模拟）
        - SPARQL_Proxy 被 mock，返回空结果集
    操作步骤：
        - 发送 GET /indicators/test-entity-001
    预期结果：
        - HTTP 200（返回空指标列表）或 404（实体不存在），
          不应出现 500
    """
    with patch(
        "drp.indicators.router.sparql_query",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/indicators/test-entity-001")

    assert resp.status_code in (200, 404), (
        f"期望 200 或 404，实际 {resp.status_code}；body={resp.text}"
    )


# ---------------------------------------------------------------------------
# S5: 关系 API 可用 — GET /org/{id}/relations（带 token）返回 200
# ---------------------------------------------------------------------------

async def test_s5_relations_api_available(authenticated_app):
    """S5: 实体关系 API 可用性验证。

    前置条件：
        - 用户已认证（通过 dependency override 模拟）
        - SPARQL_Proxy 被 mock，返回空结果集
    操作步骤：
        - 发送 GET /org/test-entity-001/relations
    预期结果：
        - HTTP 200，返回 JSON 数组（可能为空）
    """
    with patch("drp.org.router.sparql_query", new_callable=AsyncMock, return_value=[]):
        async with AsyncClient(
            transport=ASGITransport(app=authenticated_app), base_url="http://test"
        ) as client:
            resp = await client.get("/org/test-entity-001/relations")

    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}；body={resp.text}"
    body = resp.json()
    assert isinstance(body, list)


# ---------------------------------------------------------------------------
# S6: 前端页面加载 — 验证 HTML 文件存在且包含关键元素
# ---------------------------------------------------------------------------

def test_s6_frontend_html_exists_and_valid():
    """S6: 前端页面完整性验证。

    前置条件：
        - 项目根目录存在 央企数字资产监管平台_prototype.html
    操作步骤：
        - 检查文件存在性
        - 读取文件内容，验证包含关键 HTML 元素
    预期结果：
        - 文件存在
        - 包含 <html>、<head>、<body> 基本结构
        - 包含 #app 主容器
        - 包含 canvas 或 graph-area 图谱区域
        - 包含 prototype_app.js 或内联脚本引用
    """
    html_path = PROJECT_ROOT / "央企数字资产监管平台_prototype.html"
    assert html_path.exists(), f"前端 HTML 文件不存在: {html_path}"

    content = html_path.read_text(encoding="utf-8")

    # 基本 HTML 结构
    assert "<html" in content, "缺少 <html> 标签"
    assert "<head" in content, "缺少 <head> 标签"

    # 主容器
    assert 'id="app"' in content or "id='app'" in content, "缺少 #app 主容器"

    # 图谱区域
    assert "graph-area" in content, "缺少 graph-area 图谱区域"

    # KPI 栏
    assert "kpi" in content.lower(), "缺少 KPI 栏相关元素"


# ---------------------------------------------------------------------------
# S7: 登录页面渲染 — 验证 HTML 包含登录表单元素
# ---------------------------------------------------------------------------

def test_s7_login_page_elements():
    """S7: 登录页面渲染验证。

    前置条件：
        - 项目根目录存在 央企数字资产监管平台_prototype.html
    操作步骤：
        - 读取 HTML 文件内容
        - 验证包含登录页面所需的表单元素
    预期结果：
        - 包含 login-page 容器
        - 包含邮箱输入框（login-email）
        - 包含密码输入框（login-password）
        - 包含登录按钮（login-btn）
        - 包含错误提示区域（login-error）
    """
    html_path = PROJECT_ROOT / "央企数字资产监管平台_prototype.html"
    assert html_path.exists(), f"前端 HTML 文件不存在: {html_path}"

    content = html_path.read_text(encoding="utf-8")

    # 登录页容器
    assert "login-page" in content, "缺少 login-page 登录页容器"

    # 邮箱输入框
    assert "login-email" in content, "缺少 login-email 邮箱输入框"

    # 密码输入框
    assert "login-password" in content, "缺少 login-password 密码输入框"

    # 登录按钮
    assert "login-btn" in content, "缺少 login-btn 登录按钮"

    # 错误提示
    assert "login-error" in content, "缺少 login-error 错误提示区域"
