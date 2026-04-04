"""
OpenAPI 规范测试。

这些测试确保 API 实现符合 OpenAPI 规范。
"""

import json
from pathlib import Path

import pytest
import schemathesis
from fastapi.testclient import TestClient

from drp.main import app

# 创建测试客户端
client = TestClient(app)

# 获取 OpenAPI 规范
openapi_schema = app.openapi()

# 创建 schemathesis 策略
schema = schemathesis.from_dict(openapi_schema)


def test_openapi_spec_exists():
    """测试 OpenAPI 规范是否存在。"""
    assert openapi_schema is not None
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert "paths" in openapi_schema


def test_openapi_version():
    """测试 OpenAPI 版本。"""
    assert openapi_schema["openapi"].startswith("3.")


def test_api_info():
    """测试 API 基本信息。"""
    info = openapi_schema["info"]
    assert "title" in info
    assert "version" in info
    assert info["title"] == "DRP — 穿透式资金监管平台"
    assert info["version"] == "0.1.0"


def test_paths_exist():
    """测试 API 路径是否存在。"""
    paths = openapi_schema["paths"]
    assert len(paths) > 0
    
    # 检查特定路径
    expected_paths = ["/health", "/tenants", "/tenants/{tenant_id}"]
    for path in expected_paths:
        assert path in paths or any(p.startswith(path.split("{")[0]) for p in paths)


def test_health_endpoint():
    """测试健康检查端点。"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data
    assert "env" in data


def test_tenants_endpoints():
    """测试租户管理端点。"""
    # 测试 GET /tenants/{tenant_id} (应该返回 404，因为没有租户)
    response = client.get("/tenants/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    
    # 测试 POST /tenants (需要有效的请求体)
    tenant_data = {
        "name": "测试租户",
        "description": "测试租户描述",
        "contact_email": "test@example.com"
    }
    response = client.post("/tenants", json=tenant_data)
    # 可能是 201 创建成功，或 502 如果 GraphDB 不可用
    assert response.status_code in [201, 502]


@pytest.mark.slow
@schema.parametrize()
def test_api_conformance(case):
    """使用 schemathesis 测试 API 符合性。"""
    # 跳过某些测试
    if case.path == "/tenants" and case.method == "POST":
        # POST /tenants 可能需要特殊处理
        pytest.skip("POST /tenants 需要 GraphDB 连接")
    
    response = case.call()
    case.validate_response(response)


def test_openapi_spec_validation():
    """测试 OpenAPI 规范验证。"""
    from openapi_spec_validator import validate_spec
    
    try:
        validate_spec(openapi_schema)
        assert True
    except Exception as e:
        pytest.fail(f"OpenAPI 规范验证失败: {e}")


def test_error_responses():
    """测试错误响应定义。"""
    paths = openapi_schema["paths"]
    
    for path, methods in paths.items():
        for method, spec in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # 检查是否有 responses
                assert "responses" in spec, f"{method.upper()} {path} 缺少 responses"
                
                responses = spec["responses"]
                
                # 检查是否有成功响应
                success_codes = ["200", "201", "202", "204"]
                has_success = any(code in responses for code in success_codes)
                assert has_success, f"{method.upper()} {path} 缺少成功响应"
                
                # 检查是否有错误响应
                error_codes = ["400", "401", "403", "404", "422", "500"]
                has_error = any(code in responses for code in error_codes)
                assert has_error, f"{method.upper()} {path} 缺少错误响应"


def test_save_openapi_spec(tmp_path):
    """测试保存 OpenAPI 规范到文件。"""
    spec_path = tmp_path / "openapi.json"
    
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    
    assert spec_path.exists()
    
    # 重新加载并验证
    with open(spec_path, "r", encoding="utf-8") as f:
        loaded_spec = json.load(f)
    
    assert loaded_spec["openapi"] == openapi_schema["openapi"]
    assert loaded_spec["info"]["title"] == openapi_schema["info"]["title"]