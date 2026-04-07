"""缓存服务单元测试。

覆盖核心场景：
- invalidate_scope_cache Pipeline 原子删除
- invalidate_mask_cache 查询角色关联用户后删除
- invalidate_dept_cache Pipeline 原子删除
- Redis 不可用时返回 False
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drp.scope.cache import (
    invalidate_dept_cache,
    invalidate_mask_cache,
    invalidate_scope_cache,
)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_redis_mock(scan_keys: list[str] | None = None):
    """创建 Redis mock 实例，支持 scan_iter 和 pipeline。"""
    mock = AsyncMock()

    # scan_iter mock
    keys = [k.encode() for k in (scan_keys or [])]

    async def scan_iter_mock(match=None):
        for key in keys:
            yield key

    mock.scan_iter = scan_iter_mock

    # pipeline mock
    pipe_mock = AsyncMock()
    pipe_mock.delete = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[])
    pipe_mock.__aenter__ = AsyncMock(return_value=pipe_mock)
    pipe_mock.__aexit__ = AsyncMock(return_value=False)
    mock.pipeline = MagicMock(return_value=pipe_mock)

    return mock, pipe_mock


# ---------------------------------------------------------------------------
# 测试：invalidate_scope_cache
# ---------------------------------------------------------------------------

class TestInvalidateScopeCache:
    """测试 invalidate_scope_cache 函数。"""

    @pytest.mark.asyncio
    async def test_deletes_matching_keys(self):
        """删除匹配的 scope 缓存键。"""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        keys = [
            f"ds:scope:{tenant_id}:{user_id}:item",
            f"ds:scope:{tenant_id}:{user_id}:order",
        ]
        mock_redis, pipe_mock = _make_redis_mock(keys)

        result = await invalidate_scope_cache(mock_redis, tenant_id, user_id)

        assert result is True
        pipe_mock.delete.assert_called_once()
        # 验证传入了正确数量的键
        call_args = pipe_mock.delete.call_args[0]
        assert len(call_args) == 2

    @pytest.mark.asyncio
    async def test_no_keys_still_succeeds(self):
        """无匹配键时仍返回成功。"""
        mock_redis, pipe_mock = _make_redis_mock([])

        result = await invalidate_scope_cache(mock_redis, "t1", "u1")

        assert result is True
        # pipeline 不应被调用（无键需要删除）
        pipe_mock.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_error_returns_false(self):
        """Redis 异常时返回 False。"""
        mock_redis = AsyncMock()

        async def failing_scan(*args, **kwargs):
            raise Exception("Redis error")
            yield  # noqa: unreachable - 使其成为异步生成器

        mock_redis.scan_iter = failing_scan

        result = await invalidate_scope_cache(mock_redis, "t1", "u1")
        assert result is False


# ---------------------------------------------------------------------------
# 测试：invalidate_mask_cache
# ---------------------------------------------------------------------------

class TestInvalidateMaskCache:
    """测试 invalidate_mask_cache 函数。"""

    @pytest.mark.asyncio
    async def test_deletes_keys_for_role_users(self):
        """查询角色关联用户后删除对应 mask 缓存。"""
        tenant_id = str(uuid.uuid4())
        role_id = str(uuid.uuid4())
        user_id_1 = str(uuid.uuid4())
        user_id_2 = str(uuid.uuid4())

        keys = [
            f"ds:mask:{tenant_id}:{user_id_1}:item",
            f"ds:mask:{tenant_id}:{user_id_2}:item",
        ]
        mock_redis, pipe_mock = _make_redis_mock(keys)

        with patch(
            "drp.scope.cache._get_role_user_ids",
            return_value=[user_id_1, user_id_2],
        ):
            result = await invalidate_mask_cache(mock_redis, tenant_id, role_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_no_users_still_succeeds(self):
        """角色无关联用户时仍返回成功。"""
        mock_redis, pipe_mock = _make_redis_mock([])

        with patch(
            "drp.scope.cache._get_role_user_ids",
            return_value=[],
        ):
            result = await invalidate_mask_cache(mock_redis, "t1", "r1")

        assert result is True

    @pytest.mark.asyncio
    async def test_redis_error_returns_false(self):
        """Redis 异常时返回 False。"""
        mock_redis = AsyncMock()

        async def failing_scan(*args, **kwargs):
            raise Exception("Redis error")
            yield  # noqa: unreachable

        mock_redis.scan_iter = failing_scan

        with patch(
            "drp.scope.cache._get_role_user_ids",
            return_value=["u1"],
        ):
            result = await invalidate_mask_cache(mock_redis, "t1", "r1")
        assert result is False


# ---------------------------------------------------------------------------
# 测试：invalidate_dept_cache
# ---------------------------------------------------------------------------

class TestInvalidateDeptCache:
    """测试 invalidate_dept_cache 函数。"""

    @pytest.mark.asyncio
    async def test_deletes_matching_keys(self):
        """删除匹配的 dept 缓存键。"""
        tenant_id = str(uuid.uuid4())
        keys = [
            f"ds:dept_tree:{tenant_id}:dept-1",
            f"ds:dept_tree:{tenant_id}:dept-2",
        ]
        mock_redis, pipe_mock = _make_redis_mock(keys)

        result = await invalidate_dept_cache(mock_redis, tenant_id)

        assert result is True
        pipe_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_keys_still_succeeds(self):
        """无匹配键时仍返回成功。"""
        mock_redis, pipe_mock = _make_redis_mock([])

        result = await invalidate_dept_cache(mock_redis, "t1")

        assert result is True
        pipe_mock.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_error_returns_false(self):
        """Redis 异常时返回 False。"""
        mock_redis = AsyncMock()

        async def failing_scan(*args, **kwargs):
            raise Exception("Redis error")
            yield  # noqa: unreachable

        mock_redis.scan_iter = failing_scan

        result = await invalidate_dept_cache(mock_redis, "t1")
        assert result is False


# ---------------------------------------------------------------------------
# 测试：Pipeline 原子性
# ---------------------------------------------------------------------------

class TestPipelineAtomicity:
    """验证缓存失效使用 Pipeline（MULTI/EXEC）。"""

    @pytest.mark.asyncio
    async def test_scope_uses_pipeline_transaction(self):
        """scope 缓存失效使用 transaction=True 的 Pipeline。"""
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        keys = [f"ds:scope:{tenant_id}:{user_id}:item"]
        mock_redis, pipe_mock = _make_redis_mock(keys)

        await invalidate_scope_cache(mock_redis, tenant_id, user_id)

        # 验证 pipeline 以 transaction=True 调用
        mock_redis.pipeline.assert_called_once_with(transaction=True)
        # 验证 execute 被调用（EXEC）
        pipe_mock.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_dept_uses_pipeline_transaction(self):
        """dept 缓存失效使用 transaction=True 的 Pipeline。"""
        tenant_id = str(uuid.uuid4())
        keys = [f"ds:dept_tree:{tenant_id}:dept-1"]
        mock_redis, pipe_mock = _make_redis_mock(keys)

        await invalidate_dept_cache(mock_redis, tenant_id)

        mock_redis.pipeline.assert_called_once_with(transaction=True)
        pipe_mock.execute.assert_called_once()
