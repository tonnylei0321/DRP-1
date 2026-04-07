"""Celery beat 熔断审计定时任务单元测试。

覆盖核心场景：
- 扫描 Redis 中所有熔断键
- 禁用状态时写入审计日志提醒
- Redis 不可用时不崩溃
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from drp.scope.tasks import run_circuit_breaker_audit


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_redis_mock(keys_and_values: dict[str, dict] | None = None):
    """创建 Redis mock 实例。"""
    mock = AsyncMock()
    mock.aclose = AsyncMock()

    if keys_and_values is None:
        keys_and_values = {}

    # scan_iter mock：返回异步迭代器
    async def scan_iter_mock(match=None):
        for key in keys_and_values:
            yield key.encode()

    mock.scan_iter = scan_iter_mock

    # get mock：根据键返回对应值
    async def get_mock(key):
        key_str = key.decode() if isinstance(key, bytes) else key
        if key_str in keys_and_values:
            return json.dumps(keys_and_values[key_str]).encode()
        return None

    mock.get = get_mock

    return mock


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------

class TestRunCircuitBreakerAudit:
    """测试 run_circuit_breaker_audit 函数。"""

    @pytest.mark.asyncio
    async def test_no_keys_does_nothing(self):
        """无熔断键时不执行任何操作。"""
        mock_redis = _make_redis_mock({})
        with patch(
            "redis.asyncio.from_url",
            return_value=mock_redis,
        ):
            # 不应抛出异常
            await run_circuit_breaker_audit()

    @pytest.mark.asyncio
    async def test_enabled_key_no_audit(self):
        """enabled=True 的键不写入审计日志。"""
        mock_redis = _make_redis_mock({
            "ds:circuit_breaker:tenant-1": {"enabled": True, "operator_id": "op-1"},
        })
        with patch(
            "redis.asyncio.from_url",
            return_value=mock_redis,
        ), patch(
            "drp.scope.tasks._write_audit_reminder",
            new_callable=AsyncMock,
        ) as mock_write:
            await run_circuit_breaker_audit()
        mock_write.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_key_writes_audit(self):
        """enabled=False 的键写入审计日志提醒。"""
        mock_redis = _make_redis_mock({
            "ds:circuit_breaker:tenant-1": {"enabled": False, "operator_id": "op-1"},
        })
        with patch(
            "redis.asyncio.from_url",
            return_value=mock_redis,
        ), patch(
            "drp.scope.tasks._write_audit_reminder",
            new_callable=AsyncMock,
        ) as mock_write:
            await run_circuit_breaker_audit()
        mock_write.assert_called_once_with("tenant-1", "op-1")

    @pytest.mark.asyncio
    async def test_multiple_tenants(self):
        """多租户场景：仅对禁用的租户写入审计。"""
        mock_redis = _make_redis_mock({
            "ds:circuit_breaker:tenant-1": {"enabled": True, "operator_id": "op-1"},
            "ds:circuit_breaker:tenant-2": {"enabled": False, "operator_id": "op-2"},
            "ds:circuit_breaker:tenant-3": {"enabled": False, "operator_id": "op-3"},
        })
        with patch(
            "redis.asyncio.from_url",
            return_value=mock_redis,
        ), patch(
            "drp.scope.tasks._write_audit_reminder",
            new_callable=AsyncMock,
        ) as mock_write:
            await run_circuit_breaker_audit()
        assert mock_write.call_count == 2

    @pytest.mark.asyncio
    async def test_redis_unavailable_no_crash(self):
        """Redis 不可用时不崩溃。"""
        with patch(
            "redis.asyncio.from_url",
            side_effect=Exception("Redis down"),
        ):
            # 不应抛出异常
            await run_circuit_breaker_audit()
