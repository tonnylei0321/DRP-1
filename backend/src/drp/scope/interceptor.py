"""行级过滤拦截器：基于 SQLAlchemy do_orm_execute 事件 + ContextVar 实现。

核心思路：
- require_data_scope 依赖（async）中预加载规则、构建 WHERE 子句，存入 ScopeContext
- do_orm_execute 事件监听器（sync）从 ContextVar 读取预构建的 where_clause 注入 statement
- 避免在同步事件中做 async IO
"""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.config import settings
from drp.scope.dept_service import get_dept_subtree
from drp.scope.expr_parser import parse_condition
from drp.scope.registry import get_registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ContextVar 定义
# ---------------------------------------------------------------------------

_scope_ctx: ContextVar["ScopeContext | None"] = ContextVar("scope_ctx", default=None)
_current_table: ContextVar[str | None] = ContextVar("_current_table", default=None)

# ---------------------------------------------------------------------------
# 缓存配置
# ---------------------------------------------------------------------------

SCOPE_CACHE_PREFIX = "ds:scope"
SCOPE_CACHE_TTL = 300  # 秒


# ---------------------------------------------------------------------------
# ScopeContext 数据类
# ---------------------------------------------------------------------------

@dataclass
class ScopeContext:
    """当前请求的数据权限上下文。"""

    active: bool
    tenant_id: str
    user_id: str
    target_tables: set[str]
    # 预构建的 WHERE 子句片段和绑定参数（在依赖中异步构建）
    where_clause: str | None = None
    bind_params: dict[str, Any] = field(default_factory=dict)
    # 是否为 all 类型（不追加条件）
    is_all: bool = False
    # 熔断旁路标记
    bypassed: bool = False


# ---------------------------------------------------------------------------
# 辅助函数：加载规则（Redis 缓存 + DB 回退）
# ---------------------------------------------------------------------------

async def _load_rules_from_cache_or_db(
    tenant_id: str,
    user_id: str,
    table_name: str,
    session=None,
) -> list[dict]:
    """从 Redis 缓存加载规则，不可用时回退到数据库。

    返回规则字典列表，每个字典包含 scope_type 和 custom_condition。
    """
    cache_key = f"{SCOPE_CACHE_PREFIX}:{tenant_id}:{user_id}:{table_name}"

    # 尝试 Redis 缓存
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        try:
            cached = await r.get(cache_key)
            if cached is not None:
                logger.debug("scope 规则缓存命中: %s", cache_key)
                return json.loads(cached)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("Redis 缓存读取失败，回退到数据库查询", exc_info=True)

    # 回退到数据库
    if session is None:
        return []

    result = await session.execute(
        text(
            "SELECT scope_type, custom_condition FROM data_scope_rule "
            "WHERE tenant_id = :tenant_id AND user_id = :user_id AND table_name = :table_name"
        ),
        {"tenant_id": tenant_id, "user_id": user_id, "table_name": table_name},
    )
    rows = result.fetchall()
    rules = [{"scope_type": row[0], "custom_condition": row[1]} for row in rows]

    # 写入 Redis 缓存
    if rules:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url)
            try:
                await r.set(cache_key, json.dumps(rules), ex=SCOPE_CACHE_TTL)
            finally:
                await r.aclose()
        except Exception:
            logger.warning("Redis 缓存写入失败", exc_info=True)

    return rules


# ---------------------------------------------------------------------------
# 辅助函数：检查熔断状态
# ---------------------------------------------------------------------------

async def _is_circuit_bypassed(tenant_id: str) -> bool:
    """检查熔断开关是否开启（数据过滤被旁路）。"""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        try:
            raw = await r.get(f"ds:circuit_breaker:{tenant_id}")
            if raw is not None:
                data = json.loads(raw)
                # enabled=false 表示过滤被禁用（熔断开启）
                return not data.get("enabled", True)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("熔断状态检查失败，默认不旁路", exc_info=True)
    return False


# ---------------------------------------------------------------------------
# 辅助函数：构建 WHERE 子句
# ---------------------------------------------------------------------------

async def _build_where_clause(
    rules: list[dict],
    tenant_id: str,
    user_id: str,
    table_name: str,
    session=None,
) -> tuple[str | None, dict[str, Any], bool]:
    """根据规则列表构建 WHERE 子句。

    返回 (where_clause, bind_params, is_all)。
    - is_all=True 时 where_clause 为 None（不追加条件）
    """
    conditions: list[str] = []
    bind_params: dict[str, Any] = {}
    param_counter = 0

    registry = get_registry()
    table_meta = registry.get(table_name)
    allowed_columns = list(table_meta["columns"].keys()) if table_meta else []

    for rule in rules:
        scope_type = rule["scope_type"]

        if scope_type == "all":
            # all 类型不追加任何条件
            return None, {}, True

        if scope_type == "self":
            param_name = f"_scope_self_{param_counter}"
            conditions.append(f"created_by = :{param_name}")
            bind_params[param_name] = user_id
            param_counter += 1

        elif scope_type == "dept":
            # 获取用户的 dept_id
            user_dept_id = await _get_user_dept_id(user_id, session)
            if user_dept_id is None:
                logger.warning(
                    "用户 %s 未分配部门，dept 类型规则返回空结果", user_id
                )
                # dept_id 为 NULL 时返回空结果集（1=0）
                conditions.append("1=0")
                continue

            # 获取部门子树
            dept_ids = await get_dept_subtree(
                session,
                user_dept_id,
                tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
            )
            if not dept_ids:
                conditions.append("1=0")
                continue

            placeholders = []
            for did in dept_ids:
                param_name = f"_scope_dept_{param_counter}"
                placeholders.append(f":{param_name}")
                bind_params[param_name] = str(did)
                param_counter += 1
            conditions.append(f"dept_id IN ({', '.join(placeholders)})")

        elif scope_type == "custom":
            custom_condition = rule.get("custom_condition")
            if not custom_condition:
                continue
            try:
                result = parse_condition(custom_condition, allowed_columns)
                # 重命名绑定参数避免冲突
                renamed_sql = result.sql_fragment
                for old_name, value in result.bind_params.items():
                    new_name = f"_scope_custom_{param_counter}"
                    renamed_sql = renamed_sql.replace(f":{old_name}", f":{new_name}")
                    bind_params[new_name] = value
                    param_counter += 1
                conditions.append(f"({renamed_sql})")
            except ValueError as exc:
                logger.warning("custom_condition 解析失败: %s", exc)
                # 解析失败的规则跳过（不影响其他规则）
                continue

    if not conditions:
        return None, {}, False

    # 多规则 OR 合并
    if len(conditions) == 1:
        where_clause = conditions[0]
    else:
        where_clause = " OR ".join(f"({c})" for c in conditions)

    return where_clause, bind_params, False


async def _get_user_dept_id(user_id: str, session=None) -> uuid.UUID | None:
    """获取用户的 dept_id。"""
    if session is None:
        return None
    result = await session.execute(
        text('SELECT dept_id FROM "user" WHERE id = :user_id'),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if row and row[0]:
        return uuid.UUID(str(row[0]))
    return None


# ---------------------------------------------------------------------------
# FastAPI 依赖工厂：require_data_scope
# ---------------------------------------------------------------------------

def require_data_scope(table_name: str):
    """FastAPI 依赖工厂，标记该路由需要行级数据过滤。

    用法::

        @router.get("/items", dependencies=[Depends(require_data_scope("item"))])
        async def list_items(): ...

    流程：
    1. 从 get_current_user 获取 TokenPayload
    2. 检查熔断状态
    3. 异步加载规则 → 构建 WHERE 条件 → 存入 ScopeContext
    4. 设置 _current_table 和 _scope_ctx ContextVar
    5. yield TokenPayload
    6. finally 中清除 ContextVar
    """
    from drp.db.session import get_session

    async def _dependency(
        user: TokenPayload = Depends(get_current_user),
        session=Depends(get_session),
    ):
        # 设置 _current_table 供 Column_Mask_Serializer 读取
        table_token = _current_table.set(table_name)

        # 检查熔断状态
        bypassed = False
        if user.tenant_id:
            bypassed = await _is_circuit_bypassed(user.tenant_id)

        if bypassed:
            # 熔断旁路：不加载规则，不追加条件
            ctx = ScopeContext(
                active=False,
                tenant_id=user.tenant_id or "",
                user_id=user.sub,
                target_tables={table_name},
                bypassed=True,
            )
            scope_token = _scope_ctx.set(ctx)
            try:
                yield user
            finally:
                _scope_ctx.reset(scope_token)
                _current_table.reset(table_token)
            return

        # 正常模式：加载规则并构建 WHERE 子句
        rules = await _load_rules_from_cache_or_db(
            tenant_id=user.tenant_id or "",
            user_id=user.sub,
            table_name=table_name,
            session=session,
        )

        if not rules:
            # 无规则时抛出 403
            logger.warning(
                "用户 %s 对表 %s 未配置数据范围规则",
                user.sub,
                table_name,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="未配置数据范围规则，请联系管理员",
            )

        where_clause, bind_params, is_all = await _build_where_clause(
            rules=rules,
            tenant_id=user.tenant_id or "",
            user_id=user.sub,
            table_name=table_name,
            session=session,
        )

        ctx = ScopeContext(
            active=True,
            tenant_id=user.tenant_id or "",
            user_id=user.sub,
            target_tables={table_name},
            where_clause=where_clause,
            bind_params=bind_params,
            is_all=is_all,
        )
        scope_token = _scope_ctx.set(ctx)
        try:
            yield user
        finally:
            _scope_ctx.reset(scope_token)
            _current_table.reset(table_token)

    return _dependency


# ---------------------------------------------------------------------------
# SQLAlchemy do_orm_execute 事件监听器
# ---------------------------------------------------------------------------

@event.listens_for(Session, "do_orm_execute")
def _inject_scope_filter(orm_execute_state):
    """SQLAlchemy 2.x do_orm_execute 事件，兼容 AsyncSession。

    从 ContextVar 读取预构建的 where_clause 并注入到 SELECT 语句。
    所有 async IO（规则加载、部门查询）已在 require_data_scope 依赖中完成。
    """
    ctx = _scope_ctx.get()
    if ctx is None or not ctx.active:
        return

    # 仅处理 SELECT 语句
    if not orm_execute_state.is_select:
        return

    # is_all 类型不追加条件
    if ctx.is_all:
        return

    # 无 where_clause 时跳过（不应发生，因为无规则已在依赖中抛 403）
    if ctx.where_clause is None:
        return

    # 检查查询涉及的表是否在目标表集合中
    try:
        for mapper_entity in orm_execute_state.all_mappers:
            table_name = mapper_entity.local_table.name
            if table_name in ctx.target_tables:
                # 注入 WHERE 子句
                statement = orm_execute_state.statement
                where_text = text(ctx.where_clause)
                if ctx.bind_params:
                    where_text = where_text.bindparams(
                        **{k: v for k, v in ctx.bind_params.items()}
                    )
                orm_execute_state.statement = statement.where(where_text)
                return
    except Exception:
        logger.error("scope 过滤注入失败", exc_info=True)


# ---------------------------------------------------------------------------
# 公开接口（供其他模块使用）
# ---------------------------------------------------------------------------

def get_current_table() -> str | None:
    """获取当前请求的业务表名（供 Column_Mask_Serializer 使用）。"""
    return _current_table.get()


def get_scope_context() -> ScopeContext | None:
    """获取当前请求的 scope 上下文。"""
    return _scope_ctx.get()
