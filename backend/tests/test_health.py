import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_returns_200():
    """健康检查端点应返回 200。"""
    from drp.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_schema():
    """健康检查响应体应包含 status、version、env 字段。

    增强版健康检查在外部服务不可用时返回 'degraded'，测试环境中此属正常行为。
    """
    from drp.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    body = response.json()
    assert body["status"] in ("ok", "degraded")  # 测试环境无外部服务，可能为 degraded
    assert "version" in body
    assert "env" in body
    assert "components" in body  # 增强版包含组件状态
