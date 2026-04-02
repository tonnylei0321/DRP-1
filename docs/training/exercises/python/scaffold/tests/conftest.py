"""
pytest fixtures

已完成：TestClient fixture，可直接在测试中使用。
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_services():
    """每个测试前重置服务状态，保证测试隔离"""
    from app.routers.logs import _alert_service, _log_service
    if _log_service:
        _log_service.reset()
    if _alert_service:
        _alert_service.reset()
    yield


@pytest.fixture(autouse=True)
def mock_httpx_post():
    """全局 mock httpx.post，避免真实网络调用"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.alert_service.httpx.post", return_value=mock_response):
        yield


@pytest.fixture
def sample_logs():
    """示例日志数据"""
    return {
        "logs": [
            {
                "timestamp": "2026-03-09 14:30:15",
                "level": "ERROR",
                "service": "UserService",
                "message": "用户认证失败: user_id=12345, reason=token_expired",
            },
            {
                "timestamp": "2026-03-09 14:30:16",
                "level": "INFO",
                "service": "OrderService",
                "message": "订单创建成功: order_id=67890",
            },
            {
                "timestamp": "2026-03-09 14:30:17",
                "level": "WARN",
                "service": "PaymentService",
                "message": "支付超时重试: payment_id=11111, retry=2",
            },
        ]
    }
