"""列级脱敏序列化器：基于 FastAPI APIRoute 子类 + ContextVar 实现。

核心思路：
- MaskedAPIRoute 在序列化阶段拦截 JSONResponse，执行脱敏
- 从 ContextVar _current_table 获取 table_name（由 require_data_scope 设置）
- 从 Redis 缓存加载脱敏规则，不可用时回退数据库
- 多角色取最宽松策略（优先级：none > mask > hide）
- 异常时 fallback 到 hide + 错误日志
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from drp.config import settings
from drp.scope.interceptor import _current_table

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 缓存配置
# ---------------------------------------------------------------------------

MASK_CACHE_PREFIX = "ds:mask"
MASK_CACHE_TTL = 300  # 秒

# ---------------------------------------------------------------------------
# 策略优先级（数值越大越宽松）
# ---------------------------------------------------------------------------

_STRATEGY_PRIORITY: dict[str, int] = {
    "hide": 0,
    "mask": 1,
    "none": 2,
}


# ---------------------------------------------------------------------------
# 内置脱敏函数
# ---------------------------------------------------------------------------

def mask_value(value: str, pattern: str, regex_expression: str | None = None) -> str:
    """按脱敏模式处理字段值。

    Args:
        value: 原始字段值
        pattern: 脱敏模式（phone / id_card / email / custom_regex）
        regex_expression: 自定义正则表达式（仅 custom_regex 时使用）

    Returns:
        脱敏后的字符串
    """
    if not value or not isinstance(value, str):
        return value  # type: ignore[return-value]

    if pattern == "phone":
        # 保留前3后4位，中间替换为 ****
        if len(value) >= 7:
            return value[:3] + "****" + value[-4:]
        return "****"

    if pattern == "id_card":
        # 保留前3后4位，中间替换为 *
        if len(value) >= 7:
            masked_len = len(value) - 7
            return value[:3] + "*" * masked_len + value[-4:]
        return "****"

    if pattern == "email":
        # 用户名部分遮蔽：保留首字符 + *** + @domain
        at_idx = value.find("@")
        if at_idx > 0:
            username = value[:at_idx]
            domain = value[at_idx:]
            if len(username) >= 1:
                return username[0] + "***" + domain
        return "***"

    if pattern == "custom_regex":
        # 按正则匹配部分替换为 *
        if regex_expression:
            try:
                return re.sub(regex_expression, lambda m: "*" * len(m.group()), value)
            except re.error:
                logger.error("自定义正则表达式无效: %s", regex_expression)
                return "****"
        return "****"

    # 未知模式，返回全遮蔽
    return "****"


# ---------------------------------------------------------------------------
# 辅助函数：合并多角色策略（取最宽松）
# ---------------------------------------------------------------------------

def _merge_strategies(rules: list[dict], column_name: str, user_role_ids: list[str]) -> dict | None:
    """合并多角色对同一列的脱敏策略，取最宽松。

    Args:
        rules: 脱敏规则列表
        column_name: 列名
        user_role_ids: 用户角色 ID 列表

    Returns:
        最宽松策略对应的规则 dict，或 None（无匹配规则）
    """
    matched: list[dict] = []
    role_id_set = set(user_role_ids)

    for rule in rules:
        if rule.get("column_name") == column_name and rule.get("role_id") in role_id_set:
            matched.append(rule)

    if not matched:
        return None

    # 按优先级排序，取最宽松（优先级最高）
    matched.sort(key=lambda r: _STRATEGY_PRIORITY.get(r.get("mask_strategy", "hide"), 0), reverse=True)
    return matched[0]


# ---------------------------------------------------------------------------
# 核心函数：对响应数据应用脱敏规则
# ---------------------------------------------------------------------------

def apply_mask_rules(
    data: dict | list[dict],
    rules: list[dict],
    user_role_ids: list[str],
) -> dict | list[dict]:
    """对响应数据应用脱敏规则。

    Args:
        data: 响应数据（dict 或 list[dict]）
        rules: 脱敏规则列表
        user_role_ids: 用户角色 ID 列表

    Returns:
        脱敏后的数据
    """
    if isinstance(data, list):
        return [_mask_single_dict(item, rules, user_role_ids) for item in data]
    if isinstance(data, dict):
        return _mask_single_dict(data, rules, user_role_ids)
    return data


def _mask_single_dict(
    data: dict,
    rules: list[dict],
    user_role_ids: list[str],
) -> dict:
    """对单个 dict 应用脱敏规则。"""
    if not isinstance(data, dict):
        return data

    # 收集所有涉及的列名
    affected_columns: set[str] = set()
    for rule in rules:
        role_id = rule.get("role_id", "")
        if role_id in set(user_role_ids):
            col = rule.get("column_name")
            if col:
                affected_columns.add(col)

    result = dict(data)
    keys_to_remove: list[str] = []

    for col in affected_columns:
        if col not in result:
            continue

        try:
            merged = _merge_strategies(rules, col, user_role_ids)
            if merged is None:
                continue

            strategy = merged.get("mask_strategy", "hide")

            if strategy == "none":
                # 不修改
                continue
            elif strategy == "hide":
                # 从 dict 中删除该键
                keys_to_remove.append(col)
            elif strategy == "mask":
                # 部分遮蔽
                original = result[col]
                if original is not None:
                    pattern = merged.get("mask_pattern", "")
                    regex_expr = merged.get("regex_expression")
                    result[col] = mask_value(str(original), pattern, regex_expr)
            else:
                # 未知策略，fallback 到 hide
                keys_to_remove.append(col)
        except Exception:
            # 异常时 fallback 到 hide + 错误日志
            logger.error("脱敏处理异常，fallback 到 hide 策略，列: %s", col, exc_info=True)
            keys_to_remove.append(col)

    for key in keys_to_remove:
        result.pop(key, None)

    return result


# ---------------------------------------------------------------------------
# 缓存加载：从 Redis 或数据库加载脱敏规则
# ---------------------------------------------------------------------------

async def load_mask_rules(
    tenant_id: str,
    user_id: str,
    table_name: str,
) -> list[dict]:
    """从 Redis 缓存加载脱敏规则，不可用时回退到数据库。

    缓存键：ds:mask:{tenant_id}:{user_id}:{table_name}
    TTL：300s

    Returns:
        规则字典列表，每个字典包含 role_id, column_name, mask_strategy, mask_pattern, regex_expression
    """
    cache_key = f"{MASK_CACHE_PREFIX}:{tenant_id}:{user_id}:{table_name}"

    # 尝试 Redis 缓存
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        try:
            cached = await r.get(cache_key)
            if cached is not None:
                logger.debug("mask 规则缓存命中: %s", cache_key)
                return json.loads(cached)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("Redis 缓存读取失败，回退到数据库查询", exc_info=True)

    # 回退到数据库
    rules = await _load_mask_rules_from_db(tenant_id, user_id, table_name)

    # 写入 Redis 缓存
    if rules:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url)
            try:
                await r.set(cache_key, json.dumps(rules), ex=MASK_CACHE_TTL)
            finally:
                await r.aclose()
        except Exception:
            logger.warning("Redis 缓存写入失败", exc_info=True)

    return rules


async def _load_mask_rules_from_db(
    tenant_id: str,
    user_id: str,
    table_name: str,
) -> list[dict]:
    """从数据库加载用户所有角色对应的脱敏规则。"""
    try:
        from drp.db.session import async_session_factory
        from sqlalchemy import text

        async with async_session_factory() as session:
            # 先查用户的角色
            result = await session.execute(
                text(
                    "SELECT role_id FROM user_role "
                    "WHERE user_id = :user_id"
                ),
                {"user_id": user_id},
            )
            role_rows = result.fetchall()
            if not role_rows:
                return []

            role_ids = [str(row[0]) for row in role_rows]

            # 查询脱敏规则
            placeholders = ", ".join(f":r{i}" for i in range(len(role_ids)))
            params: dict[str, Any] = {
                "tenant_id": tenant_id,
                "table_name": table_name,
            }
            for i, rid in enumerate(role_ids):
                params[f"r{i}"] = rid

            result = await session.execute(
                text(
                    f"SELECT role_id, column_name, mask_strategy, mask_pattern, regex_expression "
                    f"FROM column_mask_rule "
                    f"WHERE tenant_id = :tenant_id AND table_name = :table_name "
                    f"AND role_id IN ({placeholders})"
                ),
                params,
            )
            rows = result.fetchall()
            return [
                {
                    "role_id": str(row[0]),
                    "column_name": row[1],
                    "mask_strategy": row[2],
                    "mask_pattern": row[3],
                    "regex_expression": row[4],
                }
                for row in rows
            ]
    except Exception:
        logger.error("从数据库加载脱敏规则失败", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# 文件导出专用脱敏函数
# ---------------------------------------------------------------------------

async def export_mask(
    rows: list[dict],
    tenant_id: str,
    user_id: str,
    role_ids: list[str],
    table_name: str,
) -> list[dict]:
    """文件导出专用脱敏函数，在数据查询层执行。

    与 MaskedAPIRoute 共享 apply_mask_rules 逻辑，
    但独立于 HTTP 响应流程，适用于 CSV/Excel 导出场景。

    Args:
        rows: 原始数据行列表
        tenant_id: 租户 ID
        user_id: 用户 ID
        role_ids: 用户角色 ID 列表
        table_name: 业务表名

    Returns:
        脱敏后的数据行列表
    """
    rules = await load_mask_rules(tenant_id, user_id, table_name)
    if not rules:
        return rows
    return [apply_mask_rules(row, rules, role_ids) for row in rows]  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 辅助函数：检查熔断状态
# ---------------------------------------------------------------------------

async def _is_circuit_bypassed(tenant_id: str) -> bool:
    """检查熔断开关是否开启（脱敏被旁路）。"""
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
# MaskedAPIRoute：FastAPI APIRoute 子类
# ---------------------------------------------------------------------------

class MaskedAPIRoute(APIRoute):
    """自定义 APIRoute 子类，在序列化阶段执行列级脱敏。

    用法：在需要脱敏的 router 上设置 route_class::

        router = APIRouter(route_class=MaskedAPIRoute)
    """

    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def masked_handler(request: Request) -> Response:
            response = await original_handler(request)

            # 从 ContextVar 获取 table_name（由 require_data_scope 设置）
            table_name = _current_table.get()
            if not table_name or not isinstance(response, JSONResponse):
                return response

            # 获取租户和用户信息
            tenant_id: str | None = None
            user_id: str | None = None
            role_ids: list[str] = []

            # 从 request.state 获取用户信息（由 auth 中间件设置）
            user = getattr(request.state, "user", None)
            if user is not None:
                tenant_id = getattr(user, "tenant_id", None)
                user_id = getattr(user, "sub", None)
                role_ids = [str(rid) for rid in getattr(user, "role_ids", [])]

            if not tenant_id or not user_id:
                return response

            # 检查熔断状态
            if await _is_circuit_bypassed(tenant_id):
                return response

            # 加载脱敏规则
            rules = await load_mask_rules(tenant_id, user_id, table_name)
            if not rules:
                return response

            # 解析响应体并应用脱敏
            try:
                data = json.loads(response.body)
                masked = apply_mask_rules(data, rules, role_ids)
                return JSONResponse(
                    content=masked,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except Exception:
                logger.error("MaskedAPIRoute 脱敏处理失败", exc_info=True)
                return response

        return masked_handler
