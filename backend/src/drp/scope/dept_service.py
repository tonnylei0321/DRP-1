"""部门服务：递归 CTE 查询部门子树、循环引用检测。

提供 get_dept_subtree() 和 check_circular_reference() 两个核心接口，
供 Data_Scope_Interceptor（dept 类型规则解析）和部门管理 API 使用。
"""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis 缓存配置
DEPT_TREE_CACHE_PREFIX = "ds:dept_tree"
DEPT_TREE_CACHE_TTL = 300  # 秒

# 最大递归深度
MAX_RECURSION_DEPTH = 10


async def get_dept_subtree(
    session: AsyncSession,
    dept_id: uuid.UUID,
    *,
    tenant_id: uuid.UUID | None = None,
    redis_client=None,
) -> list[uuid.UUID]:
    """获取指定部门及其所有下级部门的 ID 列表。

    使用 WITH RECURSIVE CTE 查询，最大递归深度 10 层。
    可选 Redis 缓存：先查缓存，未命中再查数据库。

    Args:
        session: SQLAlchemy 异步会话
        dept_id: 起始部门 ID
        tenant_id: 租户 ID（用于缓存键，可选）
        redis_client: Redis 客户端实例（可选，传入则启用缓存）

    Returns:
        包含起始部门自身的完整 ID 列表
    """
    # 尝试从 Redis 缓存读取
    if redis_client is not None and tenant_id is not None:
        try:
            cache_key = f"{DEPT_TREE_CACHE_PREFIX}:{tenant_id}:{dept_id}"
            cached = await redis_client.get(cache_key)
            if cached is not None:
                logger.debug("部门树缓存命中: %s", cache_key)
                return [uuid.UUID(uid) for uid in json.loads(cached)]
        except Exception:
            logger.warning("Redis 缓存读取失败，回退到数据库查询", exc_info=True)

    # 使用 WITH RECURSIVE CTE 查询部门子树
    sql = text("""
        WITH RECURSIVE dept_tree AS (
            SELECT id, parent_id, 1 AS depth
            FROM department
            WHERE id = :dept_id
            UNION ALL
            SELECT d.id, d.parent_id, dt.depth + 1
            FROM department d
            INNER JOIN dept_tree dt ON d.parent_id = dt.id
            WHERE dt.depth < :max_depth
        )
        SELECT id FROM dept_tree
    """)

    result = await session.execute(
        sql, {"dept_id": str(dept_id), "max_depth": MAX_RECURSION_DEPTH}
    )
    dept_ids = [uuid.UUID(str(row[0])) for row in result.fetchall()]

    # 写入 Redis 缓存
    if redis_client is not None and tenant_id is not None:
        try:
            cache_key = f"{DEPT_TREE_CACHE_PREFIX}:{tenant_id}:{dept_id}"
            await redis_client.set(
                cache_key,
                json.dumps([str(uid) for uid in dept_ids]),
                ex=DEPT_TREE_CACHE_TTL,
            )
        except Exception:
            logger.warning("Redis 缓存写入失败", exc_info=True)

    return dept_ids


async def check_circular_reference(
    session: AsyncSession,
    dept_id: uuid.UUID,
    new_parent_id: uuid.UUID,
) -> bool:
    """检查将 dept_id 的 parent_id 更新为 new_parent_id 是否会产生循环引用。

    从 new_parent_id 向上遍历 parent 链，如果遇到 dept_id 则存在循环。
    同时检查 dept_id == new_parent_id 的自引用情况。

    Args:
        session: SQLAlchemy 异步会话
        dept_id: 要更新的部门 ID
        new_parent_id: 新的父部门 ID

    Returns:
        True 表示存在循环引用（应拒绝操作），False 表示安全
    """
    # 自引用直接判定为循环
    if dept_id == new_parent_id:
        return True

    # 从 new_parent_id 向上遍历 parent 链，检查是否会遇到 dept_id
    sql = text("""
        WITH RECURSIVE ancestor_chain AS (
            SELECT id, parent_id, 1 AS depth
            FROM department
            WHERE id = :new_parent_id
            UNION ALL
            SELECT d.id, d.parent_id, ac.depth + 1
            FROM department d
            INNER JOIN ancestor_chain ac ON d.id = ac.parent_id
            WHERE ac.depth < :max_depth AND ac.parent_id IS NOT NULL
        )
        SELECT id FROM ancestor_chain WHERE id = :dept_id
    """)

    result = await session.execute(
        sql,
        {
            "new_parent_id": str(new_parent_id),
            "dept_id": str(dept_id),
            "max_depth": MAX_RECURSION_DEPTH,
        },
    )
    return result.fetchone() is not None
