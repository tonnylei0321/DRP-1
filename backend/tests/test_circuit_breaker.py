"""熔断开关单元测试。

覆盖核心场景：
- is_circuit_open 检查熔断状态
- set_circuit_breaker 密码验证、冷却期、状态变更
- get_circuit_breaker_status 获取当前状态
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drp.auth.schemas import TokenPayload
from drp.scope.circuit_breaker import (
    CB_COOLDOWN_PREFIX,
    CB_KEY_PREFIX,
    get_circuit_breaker_status,
    is_circuit_open,
    set_circuit_breaker,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tenant_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def operator() -> TokenPayload:
    return TokenPayload(
        sub=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        email="admin@example.com",
        permissions=["data_scope:circuit_breaker"],
        exp=9999999999,
    )


def _make_redis_mock(get_return=None, exists_return=0, ttl_return=-2):
    """创建 Redis mock 实例。"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=get_return)
    mock.set = AsyncMock()
    mock.exists = AsyncMock(return_value=exists_return)
    mock.ttl = AsyncMock(return_value=ttl_return)
    mock.aclose = AsyncMock()
    mock.pipeline = MagicMock()

    # Pipeline mock
    pipe_mock = AsyncMock()
    pipe_mock.delete = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[])
    pipe_mock.__aenter__ = AsyncMock(return_value=pipe_mock)
    pipe_mock.__aexit__ = AsyncMock(return_value=False)
    mock.pipeline.return_value = pipe_mock

    return mock


# ---------------------------------------------------------------------------
# 测试：is_circuit_open
# ---------------------------------------------------------------------------

class TestIsCircuitOpen:
    """测试 is_circuit_open 函数。"""

    @pytest.mark.asyncio
    async def test_open_when_disabled(self, tenant_id):
        """enabled=False 时返回 True（熔断开启/旁路）。"""
        mock_redis = _make_redis_mock(
            get_return=json.dumps({"enabled": False}).encode()
        )
        with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis):
            result = await is_circuit_open(tenant_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_closed_when_enabled(self, tenant_id):
        """enabled=True 时返回 False（正常过滤）。"""
        mock_redis = _make_redis_mock(
            get_return=json.dumps({"enabled": True}).encode()
        )
        with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis):
            result = await is_circuit_open(tenant_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_closed_when_no_key(self, tenant_id):
        """Redis 中无键时默认不旁路。"""
        mock_redis = _make_redis_mock(get_return=None)
        with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis):
            result = await is_circuit_open(tenant_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_closed_when_redis_unavailable(self, tenant_id):
        """Redis 不可用时默认不旁路。"""
        with patch(
            "drp.scope.circuit_breaker._get_redis",
            side_effect=Exception("Redis down"),
        ):
            result = await is_circuit_open(tenant_id)
        assert result is False


# ---------------------------------------------------------------------------
# 测试：get_circuit_breaker_status
# ---------------------------------------------------------------------------

class TestGetCircuitBreakerStatus:
    """测试 get_circuit_breaker_status 函数。"""

    @pytest.mark.asyncio
    async def test_returns_default_when_no_key(self, tenant_id):
        """无键时返回默认状态。"""
        mock_redis = _make_redis_mock(get_return=None, ttl_return=-2)
        with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis):
            status = await get_circuit_breaker_status(tenant_id)
        assert status["enabled"] is True
        assert status["cooldown_remaining"] == 0

    @pytest.mark.asyncio
    async def test_returns_stored_status(self, tenant_id):
        """返回 Redis 中存储的状态。"""
        stored = {
            "enabled": False,
            "operator_id": "op-123",
            "disabled_at": "2024-01-01T00:00:00+00:00",
        }
        mock_redis = _make_redis_mock(
            get_return=json.dumps(stored).encode(),
            ttl_return=120,
        )
        with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis):
            status = await get_circuit_breaker_status(tenant_id)
        assert status["enabled"] is False
        assert status["operator_id"] == "op-123"
        assert status["cooldown_remaining"] == 120

    @pytest.mark.asyncio
    async def test_returns_default_when_redis_unavailable(self, tenant_id):
        """Redis 不可用时返回默认状态。"""
        with patch(
            "drp.scope.circuit_breaker._get_redis",
            side_effect=Exception("Redis down"),
        ):
            status = await get_circuit_breaker_status(tenant_id)
        assert status["enabled"] is True


# ---------------------------------------------------------------------------
# 测试：set_circuit_breaker
# ---------------------------------------------------------------------------

class TestSetCircuitBreaker:
    """测试 set_circuit_breaker 函数。"""

    @pytest.mark.asyncio
    async def test_rejects_wrong_password(self, tenant_id, operator):
        """密码错误时拒绝操作。"""
        with patch(
            "drp.scope.circuit_breaker._verify_operator_password",
            return_value=False,
        ), patch(
            "drp.scope.circuit_breaker._write_cb_audit",
            new_callable=AsyncMock,
        ):
            with pytest.raises(ValueError, match="密码验证失败"):
                await set_circuit_breaker(
                    tenant_id, enabled=False, password="wrong", operator=operator
                )

    @pytest.mark.asyncio
    async def test_rejects_during_cooldown(self, tenant_id, operator):
        """冷却期内拒绝操作。"""
        mock_redis = _make_redis_mock(exists_return=1, ttl_return=200)
        with patch(
            "drp.scope.circuit_breaker._verify_operator_password",
            return_value=True,
        ), patch(
            "drp.scope.circuit_breaker._get_redis",
            return_value=mock_redis,
        ):
            with pytest.raises(RuntimeError, match="操作过于频繁"):
                await set_circuit_breaker(
                    tenant_id, enabled=False, password="correct", operator=operator
                )

    @pytest.mark.asyncio
    async def test_successful_disable(self, tenant_id, operator):
        """成功禁用熔断开关。"""
        mock_redis = _make_redis_mock(exists_return=0)
        with patch(
            "drp.scope.circuit_breaker._verify_operator_password",
            return_value=True,
        ), patch(
            "drp.scope.circuit_breaker._get_redis",
            return_value=mock_redis,
        ), patch(
            "drp.scope.circuit_breaker._write_cb_audit",
            new_callable=AsyncMock,
        ) as mock_audit:
            await set_circuit_breaker(
                tenant_id, enabled=False, password="correct", operator=operator
            )

        # 验证 Redis set 被调用
        mock_redis.set.assert_called()
        # 验证审计日志被写入
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs.kwargs["action"] == "circuit_breaker.disabled"

    @pytest.mark.asyncio
    async def test_successful_enable(self, tenant_id, operator):
        """成功启用熔断开关。"""
        mock_redis = _make_redis_mock(exists_return=0)
        with patch(
            "drp.scope.circuit_breaker._verify_operator_password",
            return_value=True,
        ), patch(
            "drp.scope.circuit_breaker._get_redis",
            return_value=mock_redis,
        ), patch(
            "drp.scope.circuit_breaker._write_cb_audit",
            new_callable=AsyncMock,
        ) as mock_audit:
            await set_circuit_breaker(
                tenant_id, enabled=True, password="correct", operator=operator
            )

        mock_redis.set.assert_called()
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs.kwargs["action"] == "circuit_breaker.enabled"

    @pytest.mark.asyncio
    async def test_auto_recover_sets_ttl(self, tenant_id, operator):
        """auto_recover_minutes 设置 TTL。"""
        mock_redis = _make_redis_mock(exists_return=0)
        with patch(
            "drp.scope.circuit_breaker._verify_operator_password",
            return_value=True,
        ), patch(
            "drp.scope.circuit_breaker._get_redis",
            return_value=mock_redis,
        ), patch(
            "drp.scope.circuit_breaker._write_cb_audit",
            new_callable=AsyncMock,
        ):
            await set_circuit_breaker(
                tenant_id,
                enabled=False,
                password="correct",
                operator=operator,
                auto_recover_minutes=30,
            )

        # 验证 Redis set 被调用时带有 ex 参数（30 * 60 = 1800）
        calls = mock_redis.set.call_args_list
        # 找到设置 circuit_breaker 键的调用（非 cooldown 键）
        cb_call = [c for c in calls if CB_KEY_PREFIX in str(c)]
        assert len(cb_call) >= 1
        # 检查 ex 参数
        cb_args = cb_call[0]
        assert cb_args.kwargs.get("ex") == 1800 or (len(cb_args.args) > 2 and cb_args.args[2] == 1800)
