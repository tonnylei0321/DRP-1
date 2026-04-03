"""第8章：穿透溯源 API 单元测试。"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from drp.auth.schemas import TokenPayload
from drp.drill.router import _safe_float, _generate_pdf
from drp.main import app


def _make_user(tenant_id: str = "tenant-test") -> TokenPayload:
    return TokenPayload(
        sub="user-001",
        tenant_id=tenant_id,
        email="test@example.com",
        permissions=["drill:read"],
        exp=9999999999,
    )


def _mock_auth(user: TokenPayload | None = None):
    """覆盖 get_current_user 依赖。"""
    from drp.auth.middleware import get_current_user
    u = user or _make_user()
    app.dependency_overrides[get_current_user] = lambda: u
    return u


def _clear_auth():
    from drp.auth.middleware import get_current_user
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app, raise_server_exceptions=False)


# ─── _safe_float ──────────────────────────────────────────────────────────────

def test_safe_float_正常转换():
    assert _safe_float("0.97") == 0.97
    assert _safe_float("100") == 100.0


def test_safe_float_None返回None():
    assert _safe_float(None) is None


def test_safe_float_非数字返回None():
    assert _safe_float("invalid") is None


# ─── 一级穿透 ─────────────────────────────────────────────────────────────────

def test_get_entities_无认证返回401():
    _clear_auth()
    resp = client.get("/drill/009/entities")
    assert resp.status_code == 401


def test_get_entities_返回法人列表():
    _mock_auth()
    mock_rows = [
        {"entity": "urn:entity:corp1", "entityName": "集团A", "value": "0.8"},
        {"entity": "urn:entity:corp2", "entityName": None, "value": "0.6"},
    ]
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=mock_rows):
        resp = client.get("/drill/009/entities")
    _clear_auth()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["entity_iri"] == "urn:entity:corp1"
    assert data[0]["entity_name"] == "集团A"
    assert data[0]["contribution_value"] == 0.8
    # entityName=None 时从 entity IRI 取末段
    assert data[1]["entity_name"] == "corp2"


def test_get_entities_sparql失败返回500():
    _mock_auth()
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, side_effect=Exception("超时")):
        resp = client.get("/drill/009/entities")
    _clear_auth()
    assert resp.status_code == 500


# ─── 二级穿透 ─────────────────────────────────────────────────────────────────

def test_get_accounts_返回账户列表():
    _mock_auth()
    mock_rows = [
        {
            "acct": "urn:entity:acct1",
            "acctNo": "001-2024",
            "balance": "1000000.00",
            "status": "active",
            "isDirectLinked": "true",
        }
    ]
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=mock_rows):
        resp = client.get("/drill/corp1/accounts")
    _clear_auth()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["account_number"] == "001-2024"
    assert data[0]["balance"] == 1000000.0
    assert data[0]["is_direct_linked"] is True


# ─── 三级穿透 ─────────────────────────────────────────────────────────────────

def test_get_account_properties_返回属性字典():
    _mock_auth()
    mock_rows = [
        {"predicate": "urn:ctio:accountNumber", "object": "ACC-001"},
        {"predicate": "urn:ctio:balance", "object": "5000.0"},
        {"predicate": "urn:ctio:isRestricted", "object": "false"},
    ]
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=mock_rows):
        resp = client.get("/drill/acct001/properties")
    _clear_auth()

    assert resp.status_code == 200
    data = resp.json()
    assert data["accountNumber"] == "ACC-001"
    assert data["balance"] == "5000.0"


def test_get_account_properties_不存在返回404():
    _mock_auth()
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/drill/nonexistent/properties")
    _clear_auth()
    assert resp.status_code == 404


# ─── 路径查询 ─────────────────────────────────────────────────────────────────

def test_get_drill_path_返回路径节点():
    _mock_auth()
    mock_rows = [
        {"step": "1", "node": "urn:ind:009", "nodeType": "RegulatoryIndicator", "nodeLabel": "009"},
        {"step": "2", "node": "urn:entity:corp1", "nodeType": "LegalEntity", "nodeLabel": "集团A"},
        {"step": "3", "node": "urn:entity:acct1", "nodeType": "Account", "nodeLabel": "ACC-001"},
    ]
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=mock_rows):
        resp = client.get("/drill/path/009")
    _clear_auth()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["step"] == 1
    assert data[0]["node_type"] == "RegulatoryIndicator"
    assert data[2]["node_type"] == "Account"


# ─── PDF 报告 ─────────────────────────────────────────────────────────────────

def test_generate_pdf_reportlab未安装返回None():
    """当 reportlab 未安装时，_generate_pdf 应返回 None 而非抛出异常。"""
    import sys
    # 临时屏蔽 reportlab
    orig = sys.modules.get("reportlab")
    sys.modules["reportlab"] = None  # type: ignore
    try:
        result = _generate_pdf("009", {"entities": [], "path": [], "tenant_id": "t1", "generated_at": ""})
        assert result is None
    finally:
        if orig is None:
            del sys.modules["reportlab"]
        else:
            sys.modules["reportlab"] = orig


def test_download_report_返回JSON_fallback():
    _mock_auth()
    with patch("drp.drill.router.sparql_query", new_callable=AsyncMock, return_value=[]), \
         patch("drp.drill.router._generate_pdf", return_value=None):
        resp = client.get("/drill/report/009")
    _clear_auth()

    assert resp.status_code == 200
    # Content-Type 为 application/json
    assert "application/json" in resp.headers.get("content-type", "")
