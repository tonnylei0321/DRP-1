"""数据权限管理路由：Data_Scope_Rule / Column_Mask_Rule CRUD + 熔断开关 + 注册表查询。"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.models import AuditLog
from drp.auth.schemas import TokenPayload
from drp.db.session import get_session
from drp.scope.circuit_breaker import (
    get_circuit_breaker_status,
    set_circuit_breaker,
)
from drp.scope.conflict_detector import detect_conflict
from drp.scope.expr_parser import parse_condition
from drp.scope.models import ColumnMaskRule, DataScopeRule
from drp.scope.registry import get_registry, is_column_valid, is_table_registered

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-scope", tags=["数据权限管理"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────


class DataScopeRuleCreate(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    table_name: str
    scope_type: str = Field(..., pattern=r"^(all|dept|self|custom)$")
    custom_condition: str | None = None


class DataScopeRuleUpdate(BaseModel):
    scope_type: str | None = Field(None, pattern=r"^(all|dept|self|custom)$")
    custom_condition: str | None = None


class DataScopeRuleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    table_name: str
    scope_type: str
    custom_condition: str | None
    created_at: datetime
    updated_at: datetime
    warning: str | None = None
    requires_confirmation: bool | None = None

    model_config = {"from_attributes": True}


class ColumnMaskRuleCreate(BaseModel):
    tenant_id: uuid.UUID
    role_id: uuid.UUID
    table_name: str
    column_name: str
    mask_strategy: str = Field(..., pattern=r"^(mask|hide|none)$")
    mask_pattern: str | None = Field(None, pattern=r"^(phone|id_card|email|custom_regex)$")
    regex_expression: str | None = None


class ColumnMaskRuleUpdate(BaseModel):
    mask_strategy: str | None = Field(None, pattern=r"^(mask|hide|none)$")
    mask_pattern: str | None = Field(None, pattern=r"^(phone|id_card|email|custom_regex)$")
    regex_expression: str | None = None


class ColumnMaskRuleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    role_id: uuid.UUID
    table_name: str
    column_name: str
    mask_strategy: str
    mask_pattern: str | None
    regex_expression: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CircuitBreakerRequest(BaseModel):
    enabled: bool
    password: str
    auto_recover_minutes: int | None = None


class CircuitBreakerResponse(BaseModel):
    enabled: bool
    operator_id: str | None = None
    disabled_at: str | None = None
    auto_recover_at: str | None = None
    cooldown_remaining: int = 0


class DeleteRuleResponse(BaseModel):
    detail: str = "已删除"
    warning: str | None = None


# ─── 辅助函数 ─────────────────────────────────────────────────────────────────


def _validate_table(table_name: str) -> None:
    """校验表名是否在注册表中。"""
    if not is_table_registered(table_name):
        raise HTTPException(status_code=400, detail=f"业务表 {table_name} 未注册")


def _validate_column(table_name: str, column_name: str) -> None:
    """校验列名是否存在于指定表中。"""
    if not is_column_valid(table_name, column_name):
        raise HTTPException(
            status_code=400,
            detail=f"列 {column_name} 不存在于表 {table_name}",
        )


def _validate_custom_condition(table_name: str, condition: str) -> None:
    """校验 custom_condition 表达式合法性。"""
    registry = get_registry()
    table_meta = registry.get(table_name)
    allowed_columns = list(table_meta["columns"].keys()) if table_meta else []
    try:
        parse_condition(condition, allowed_columns)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _validate_regex(regex_expression: str) -> None:
    """校验正则表达式合法性。"""
    try:
        re.compile(regex_expression)
    except re.error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"正则表达式不合法：{exc}",
        ) from exc


def _validate_self_type(table_name: str) -> None:
    """校验 self 类型规则的表是否包含 created_by 列。"""
    registry = get_registry()
    table_meta = registry.get(table_name)
    if table_meta and not table_meta.get("supports_self", False):
        raise HTTPException(
            status_code=400,
            detail=f"表 {table_name} 不支持 self 类型规则（缺少 created_by 列）",
        )


async def _invalidate_scope_cache(tenant_id: str, user_id: str) -> None:
    """清除 scope 缓存（Redis 不可用时静默失败）。"""
    try:
        import redis.asyncio as aioredis
        from drp.config import settings
        from drp.scope.cache import invalidate_scope_cache

        r = aioredis.from_url(settings.redis_url)
        try:
            await invalidate_scope_cache(r, tenant_id, user_id)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("scope 缓存清除失败", exc_info=True)


async def _invalidate_mask_cache(tenant_id: str, role_id: str) -> None:
    """清除 mask 缓存（Redis 不可用时静默失败）。"""
    try:
        import redis.asyncio as aioredis
        from drp.config import settings
        from drp.scope.cache import invalidate_mask_cache

        r = aioredis.from_url(settings.redis_url)
        try:
            await invalidate_mask_cache(r, tenant_id, role_id)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("mask 缓存清除失败", exc_info=True)


# ─── 注册表查询 ───────────────────────────────────────────────────────────────


@router.get(
    "/tables",
    dependencies=[Depends(require_permission("data_scope:read"))],
)
async def list_tables() -> list[dict]:
    """返回已注册业务表元数据。"""
    registry = get_registry()
    return [
        {
            "table_name": meta["table_name"],
            "columns": meta["columns"],
            "supports_self": meta["supports_self"],
        }
        for meta in registry.values()
    ]


# ─── Data_Scope_Rule CRUD ────────────────────────────────────────────────────


@router.get(
    "/rules",
    response_model=list[DataScopeRuleResponse],
    dependencies=[Depends(require_permission("data_scope:read"))],
)
async def list_rules(
    user_id: uuid.UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[DataScopeRuleResponse]:
    """查询行级规则列表（可按 user_id 筛选）。"""
    q = select(DataScopeRule).order_by(DataScopeRule.created_at)
    if user_id is not None:
        q = q.where(DataScopeRule.user_id == user_id)
    result = await session.execute(q)
    return [DataScopeRuleResponse.model_validate(r) for r in result.scalars()]


@router.post(
    "/rules",
    response_model=DataScopeRuleResponse,
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def create_rule(
    data: DataScopeRuleCreate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DataScopeRuleResponse:
    """创建行级规则。"""
    _validate_table(data.table_name)

    # self 类型校验
    if data.scope_type == "self":
        _validate_self_type(data.table_name)

    # custom_condition 校验
    if data.scope_type == "custom":
        if not data.custom_condition:
            raise HTTPException(status_code=400, detail="custom 类型规则必须提供 custom_condition")
        _validate_custom_condition(data.table_name, data.custom_condition)

    # 冲突检测
    existing_result = await session.execute(
        select(DataScopeRule).where(
            DataScopeRule.tenant_id == data.tenant_id,
            DataScopeRule.user_id == data.user_id,
            DataScopeRule.table_name == data.table_name,
        )
    )
    existing_rules = [
        {"scope_type": r.scope_type} for r in existing_result.scalars()
    ]
    warning = detect_conflict(existing_rules, data.scope_type)

    rule = DataScopeRule(
        tenant_id=data.tenant_id,
        user_id=data.user_id,
        table_name=data.table_name,
        scope_type=data.scope_type,
        custom_condition=data.custom_condition,
    )
    session.add(rule)

    # 审计日志
    session.add(AuditLog(
        tenant_id=data.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="data_scope_rule.create",
        resource_type="data_scope_rule",
        detail={
            "table_name": data.table_name,
            "scope_type": data.scope_type,
            "target_user_id": str(data.user_id),
        },
    ))

    await session.commit()
    await session.refresh(rule)

    # 清除缓存
    await _invalidate_scope_cache(str(data.tenant_id), str(data.user_id))

    resp = DataScopeRuleResponse.model_validate(rule)
    if warning:
        resp.warning = warning
    if data.scope_type == "all":
        resp.requires_confirmation = True
    return resp


@router.put(
    "/rules/{rule_id}",
    response_model=DataScopeRuleResponse,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def update_rule(
    rule_id: uuid.UUID,
    data: DataScopeRuleUpdate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DataScopeRuleResponse:
    """更新行级规则。"""
    rule = await session.get(DataScopeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    effective_scope_type = data.scope_type or rule.scope_type
    effective_condition = data.custom_condition if data.custom_condition is not None else rule.custom_condition

    # self 类型校验
    if effective_scope_type == "self":
        _validate_self_type(rule.table_name)

    # custom_condition 校验
    if effective_scope_type == "custom":
        if not effective_condition:
            raise HTTPException(status_code=400, detail="custom 类型规则必须提供 custom_condition")
        _validate_custom_condition(rule.table_name, effective_condition)

    if data.scope_type is not None:
        rule.scope_type = data.scope_type
    if data.custom_condition is not None:
        rule.custom_condition = data.custom_condition

    # 审计日志
    session.add(AuditLog(
        tenant_id=rule.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="data_scope_rule.update",
        resource_type="data_scope_rule",
        resource_id=str(rule_id),
        detail=data.model_dump(exclude_none=True),
    ))

    await session.commit()
    await session.refresh(rule)

    # 清除缓存
    await _invalidate_scope_cache(str(rule.tenant_id), str(rule.user_id))

    return DataScopeRuleResponse.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    response_model=DeleteRuleResponse,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def delete_rule(
    rule_id: uuid.UUID,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DeleteRuleResponse:
    """删除行级规则（最后一条时返回 warning）。"""
    rule = await session.get(DataScopeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 检查是否为最后一条规则
    count_result = await session.execute(
        select(sa_func.count()).select_from(DataScopeRule).where(
            DataScopeRule.tenant_id == rule.tenant_id,
            DataScopeRule.user_id == rule.user_id,
            DataScopeRule.table_name == rule.table_name,
        )
    )
    rule_count = count_result.scalar() or 0
    warning = None
    if rule_count <= 1:
        warning = "删除后该用户将无法访问此表数据"

    tenant_id = rule.tenant_id
    user_id_target = rule.user_id

    # 审计日志
    session.add(AuditLog(
        tenant_id=tenant_id,
        user_id=uuid.UUID(user.sub),
        action="data_scope_rule.delete",
        resource_type="data_scope_rule",
        resource_id=str(rule_id),
        detail={
            "table_name": rule.table_name,
            "scope_type": rule.scope_type,
            "target_user_id": str(user_id_target),
        },
    ))

    await session.delete(rule)
    await session.commit()

    # 清除缓存
    await _invalidate_scope_cache(str(tenant_id), str(user_id_target))

    return DeleteRuleResponse(warning=warning)


# ─── Column_Mask_Rule CRUD ────────────────────────────────────────────────────


@router.get(
    "/mask-rules",
    response_model=list[ColumnMaskRuleResponse],
    dependencies=[Depends(require_permission("data_scope:read"))],
)
async def list_mask_rules(
    role_id: uuid.UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[ColumnMaskRuleResponse]:
    """查询列级脱敏规则列表（可按 role_id 筛选）。"""
    q = select(ColumnMaskRule).order_by(ColumnMaskRule.created_at)
    if role_id is not None:
        q = q.where(ColumnMaskRule.role_id == role_id)
    result = await session.execute(q)
    return [ColumnMaskRuleResponse.model_validate(r) for r in result.scalars()]


@router.post(
    "/mask-rules",
    response_model=ColumnMaskRuleResponse,
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def create_mask_rule(
    data: ColumnMaskRuleCreate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ColumnMaskRuleResponse:
    """创建列级脱敏规则。"""
    _validate_table(data.table_name)
    _validate_column(data.table_name, data.column_name)

    # mask 策略必须有 mask_pattern
    if data.mask_strategy == "mask" and not data.mask_pattern:
        raise HTTPException(status_code=400, detail="mask 策略必须指定 mask_pattern")

    # custom_regex 必须有 regex_expression
    if data.mask_pattern == "custom_regex":
        if not data.regex_expression:
            raise HTTPException(status_code=400, detail="custom_regex 模式必须提供 regex_expression")
        _validate_regex(data.regex_expression)

    rule = ColumnMaskRule(
        tenant_id=data.tenant_id,
        role_id=data.role_id,
        table_name=data.table_name,
        column_name=data.column_name,
        mask_strategy=data.mask_strategy,
        mask_pattern=data.mask_pattern,
        regex_expression=data.regex_expression,
    )
    session.add(rule)

    # 审计日志
    session.add(AuditLog(
        tenant_id=data.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="column_mask_rule.create",
        resource_type="column_mask_rule",
        detail={
            "table_name": data.table_name,
            "column_name": data.column_name,
            "mask_strategy": data.mask_strategy,
            "target_role_id": str(data.role_id),
        },
    ))

    await session.commit()
    await session.refresh(rule)

    # 清除缓存
    await _invalidate_mask_cache(str(data.tenant_id), str(data.role_id))

    return ColumnMaskRuleResponse.model_validate(rule)


@router.put(
    "/mask-rules/{rule_id}",
    response_model=ColumnMaskRuleResponse,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def update_mask_rule(
    rule_id: uuid.UUID,
    data: ColumnMaskRuleUpdate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ColumnMaskRuleResponse:
    """更新列级脱敏规则。"""
    rule = await session.get(ColumnMaskRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    effective_strategy = data.mask_strategy or rule.mask_strategy
    effective_pattern = data.mask_pattern if data.mask_pattern is not None else rule.mask_pattern
    effective_regex = data.regex_expression if data.regex_expression is not None else rule.regex_expression

    if effective_strategy == "mask" and not effective_pattern:
        raise HTTPException(status_code=400, detail="mask 策略必须指定 mask_pattern")

    if effective_pattern == "custom_regex":
        if not effective_regex:
            raise HTTPException(status_code=400, detail="custom_regex 模式必须提供 regex_expression")
        _validate_regex(effective_regex)

    if data.mask_strategy is not None:
        rule.mask_strategy = data.mask_strategy
    if data.mask_pattern is not None:
        rule.mask_pattern = data.mask_pattern
    if data.regex_expression is not None:
        rule.regex_expression = data.regex_expression

    # 审计日志
    session.add(AuditLog(
        tenant_id=rule.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="column_mask_rule.update",
        resource_type="column_mask_rule",
        resource_id=str(rule_id),
        detail=data.model_dump(exclude_none=True),
    ))

    await session.commit()
    await session.refresh(rule)

    # 清除缓存
    await _invalidate_mask_cache(str(rule.tenant_id), str(rule.role_id))

    return ColumnMaskRuleResponse.model_validate(rule)


@router.delete(
    "/mask-rules/{rule_id}",
    status_code=HTTPStatus.NO_CONTENT,
    dependencies=[Depends(require_permission("data_scope:write"))],
)
async def delete_mask_rule(
    rule_id: uuid.UUID,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """删除列级脱敏规则。"""
    rule = await session.get(ColumnMaskRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="规则不存在")

    tenant_id = rule.tenant_id
    role_id = rule.role_id

    # 审计日志
    session.add(AuditLog(
        tenant_id=tenant_id,
        user_id=uuid.UUID(user.sub),
        action="column_mask_rule.delete",
        resource_type="column_mask_rule",
        resource_id=str(rule_id),
        detail={
            "table_name": rule.table_name,
            "column_name": rule.column_name,
            "target_role_id": str(role_id),
        },
    ))

    await session.delete(rule)
    await session.commit()

    # 清除缓存
    await _invalidate_mask_cache(str(tenant_id), str(role_id))


# ─── 熔断开关 ─────────────────────────────────────────────────────────────────


@router.post(
    "/circuit-breaker",
    response_model=CircuitBreakerResponse,
    dependencies=[Depends(require_permission("data_scope:circuit_breaker"))],
)
async def toggle_circuit_breaker(
    data: CircuitBreakerRequest,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CircuitBreakerResponse:
    """设置熔断开关（需二次密码验证 + 5 分钟冷却期）。"""
    tenant_id = user.tenant_id or ""
    try:
        await set_circuit_breaker(
            tenant_id=tenant_id,
            enabled=data.enabled,
            password=data.password,
            operator=user,
            auto_recover_minutes=data.auto_recover_minutes,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    status = await get_circuit_breaker_status(tenant_id)
    return CircuitBreakerResponse(**status)


@router.get(
    "/circuit-breaker",
    response_model=CircuitBreakerResponse,
    dependencies=[Depends(require_permission("data_scope:read"))],
)
async def get_circuit_breaker(
    user: TokenPayload = Depends(get_current_user),
) -> CircuitBreakerResponse:
    """查询熔断开关状态。"""
    tenant_id = user.tenant_id or ""
    status = await get_circuit_breaker_status(tenant_id)
    return CircuitBreakerResponse(**status)
