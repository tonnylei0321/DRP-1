"""缓存服务：Redis Pipeline 原子失效缓存键。

核心接口：
- invalidate_scope_cache(redis, tenant_id, user_id) → bool
- invalidate_mask_cache(redis, tenant_id, role_id) → bool
- invalidate_dept_cache(redis, tenant_id) → bool
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# 缓存键前缀
SCOPE_CACHE_PREFIX = "ds:scope"
MASK_CACHE_PREFIX = "ds:mask"
DEPT_TREE_CACHE_PREFIX = "ds:dept_tree"


async def invalidate_scope_cache(redis, tenant_id: str, user_id: str) -> bool:
    """使用 Redis Pipeline（MULTI/EXEC）原子删除 scope 缓存。

    删除键模式：ds:scope:{tenant_id}:{user_id}:*

    Args:
        redis: Redis 异步客户端实例
        tenant_id: 租户 ID
        user_id: 用户 ID

    Returns:
        True 表示操作成功，False 表示失败
    """
    try:
        pattern = f"{SCOPE_CACHE_PREFIX}:{tenant_id}:{user_id}:*"
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.delete(*keys)
                await pipe.execute()

        logger.info(
            "scope 缓存失效成功: tenant=%s, user=%s, 删除 %d 个键",
            tenant_id, user_id, len(keys),
        )
        return True
    except Exception:
        logger.warning("scope 缓存失效操作失败", exc_info=True)
        return False


async def invalidate_mask_cache(redis, tenant_id: str, role_id: str) -> bool:
    """使用 Redis Pipeline（MULTI/EXEC）原子删除 mask 缓存。

    查询角色关联的所有用户，删除对应的 mask 缓存键。
    键模式：ds:mask:{tenant_id}:{user_id}:*

    Args:
        redis: Redis 异步客户端实例
        tenant_id: 租户 ID
        role_id: 角色 ID

    Returns:
        True 表示操作成功，False 表示失败
    """
    try:
        # 查询角色关联的所有用户
        user_ids = await _get_role_user_ids(role_id)

        keys = []
        for user_id in user_ids:
            pattern = f"{MASK_CACHE_PREFIX}:{tenant_id}:{user_id}:*"
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

        if keys:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.delete(*keys)
                await pipe.execute()

        logger.info(
            "mask 缓存失效成功: tenant=%s, role=%s, 关联用户 %d 个, 删除 %d 个键",
            tenant_id, role_id, len(user_ids), len(keys),
        )
        return True
    except Exception:
        logger.warning("mask 缓存失效操作失败", exc_info=True)
        return False


async def invalidate_dept_cache(redis, tenant_id: str) -> bool:
    """使用 Redis Pipeline（MULTI/EXEC）原子删除部门树缓存。

    删除键模式：ds:dept_tree:{tenant_id}:*

    Args:
        redis: Redis 异步客户端实例
        tenant_id: 租户 ID

    Returns:
        True 表示操作成功，False 表示失败
    """
    try:
        pattern = f"{DEPT_TREE_CACHE_PREFIX}:{tenant_id}:*"
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.delete(*keys)
                await pipe.execute()

        logger.info(
            "dept 缓存失效成功: tenant=%s, 删除 %d 个键",
            tenant_id, len(keys),
        )
        return True
    except Exception:
        logger.warning("dept 缓存失效操作失败", exc_info=True)
        return False


async def _get_role_user_ids(role_id: str) -> list[str]:
    """查询角色关联的所有用户 ID。"""
    try:
        from drp.db.session import _session_factory
        from sqlalchemy import text

        async with _session_factory() as session:
            result = await session.execute(
                text("SELECT user_id FROM user_role WHERE role_id = :role_id"),
                {"role_id": role_id},
            )
            return [str(row[0]) for row in result.fetchall()]
    except Exception:
        logger.error("查询角色关联用户失败", exc_info=True)
        return []
