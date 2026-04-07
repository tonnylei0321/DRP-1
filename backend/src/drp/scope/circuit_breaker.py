"""熔断开关：Redis 键值存储 + 二次密码验证 + 5 分钟冷却期。

核心接口：
- is_circuit_open(tenant_id) → bool：检查熔断状态
- set_circuit_breaker(...)：设置熔断状态（含密码验证、冷却期、审计日志）
- get_circuit_breaker_status(tenant_id) → dict：获取当前状态
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from drp.auth.password import verify_password as _verify_password
from drp.config import settings

logger = logging.getLogger(__name__)

# Redis 键前缀
CB_KEY_PREFIX = "ds:circuit_breaker"
CB_COOLDOWN_PREFIX = "ds:cb_cooldown"
CB_COOLDOWN_TTL = 300  # 5 分钟冷却期


async def _get_redis():
    """获取 Redis 异步客户端。"""
    import redis.asyncio as aioredis

    return aioredis.from_url(settings.redis_url)


async def is_circuit_open(tenant_id: str) -> bool:
    """检查熔断开关是否开启（数据过滤是否被旁路）。

    Returns:
        True 表示熔断开启（过滤被禁用/旁路），False 表示正常过滤。
    """
    try:
        r = await _get_redis()
        try:
            raw = await r.get(f"{CB_KEY_PREFIX}:{tenant_id}")
            if raw is not None:
                data = json.loads(raw)
                # enabled=False 表示过滤被禁用（熔断开启）
                return not data.get("enabled", True)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("熔断状态检查失败，默认不旁路", exc_info=True)
    return False


async def get_circuit_breaker_status(tenant_id: str) -> dict:
    """获取熔断开关当前状态。

    Returns:
        包含 enabled, operator_id, disabled_at, auto_recover_at, cooldown_remaining 的字典。
    """
    result: dict = {
        "enabled": True,
        "operator_id": None,
        "disabled_at": None,
        "auto_recover_at": None,
        "cooldown_remaining": 0,
    }
    try:
        r = await _get_redis()
        try:
            raw = await r.get(f"{CB_KEY_PREFIX}:{tenant_id}")
            if raw is not None:
                data = json.loads(raw)
                result.update(data)

            # 检查冷却期剩余时间
            cooldown_ttl = await r.ttl(f"{CB_COOLDOWN_PREFIX}:{tenant_id}")
            if cooldown_ttl and cooldown_ttl > 0:
                result["cooldown_remaining"] = cooldown_ttl
            else:
                result["cooldown_remaining"] = 0
        finally:
            await r.aclose()
    except Exception:
        logger.warning("获取熔断状态失败", exc_info=True)
    return result


async def set_circuit_breaker(
    tenant_id: str,
    enabled: bool,
    password: str,
    operator: "TokenPayload",
    auto_recover_minutes: int | None = None,
    *,
    session=None,
) -> None:
    """设置熔断开关状态。

    安全机制：
    1. 验证 operator 的密码是否正确
    2. 检查冷却期（5 分钟内不可重复操作）
    3. 执行状态变更
    4. 设置冷却键
    5. 写入审计日志

    Raises:
        ValueError: 密码验证失败
        RuntimeError: 冷却期内重复操作
    """
    # 1. 验证密码
    password_valid = await _verify_operator_password(operator.sub, password, session=session)
    if not password_valid:
        # 写入审计日志
        await _write_cb_audit(
            tenant_id=tenant_id,
            operator_id=operator.sub,
            action="circuit_breaker.password_failed",
            detail={"reason": "密码验证失败"},
            session=session,
        )
        raise ValueError("密码验证失败")

    # 2. 检查冷却期
    r = await _get_redis()
    try:
        cooldown_key = f"{CB_COOLDOWN_PREFIX}:{tenant_id}"
        cooldown_exists = await r.exists(cooldown_key)
        if cooldown_exists:
            ttl = await r.ttl(cooldown_key)
            remaining = ttl if ttl and ttl > 0 else CB_COOLDOWN_TTL
            raise RuntimeError(f"操作过于频繁，请 {remaining} 秒后重试")

        # 3. 设置熔断状态
        now = datetime.now(timezone.utc).isoformat()
        cb_data: dict = {
            "enabled": enabled,
            "operator_id": operator.sub,
            "last_toggle_at": now,
        }
        if not enabled:
            cb_data["disabled_at"] = now
        else:
            cb_data["disabled_at"] = None

        # 可选自动恢复
        cb_key = f"{CB_KEY_PREFIX}:{tenant_id}"
        if auto_recover_minutes and not enabled:
            ttl_seconds = auto_recover_minutes * 60
            cb_data["auto_recover_at"] = now  # 简化：记录设置时间
            await r.set(cb_key, json.dumps(cb_data), ex=ttl_seconds)
        else:
            cb_data["auto_recover_at"] = None
            await r.set(cb_key, json.dumps(cb_data))

        # 4. 设置冷却键
        await r.set(cooldown_key, "1", ex=CB_COOLDOWN_TTL)

    finally:
        await r.aclose()

    # 5. 写入审计日志
    action = "circuit_breaker.enabled" if enabled else "circuit_breaker.disabled"
    await _write_cb_audit(
        tenant_id=tenant_id,
        operator_id=operator.sub,
        action=action,
        detail={
            "enabled": enabled,
            "auto_recover_minutes": auto_recover_minutes,
        },
        session=session,
    )


async def _verify_operator_password(
    user_id: str, password: str, *, session=None
) -> bool:
    """验证操作者密码。"""
    if session is None:
        try:
            from drp.db.session import _session_factory

            async with _session_factory() as session:
                return await _do_verify_password(session, user_id, password)
        except Exception:
            logger.error("密码验证失败（无法获取数据库会话）", exc_info=True)
            return False
    return await _do_verify_password(session, user_id, password)


async def _do_verify_password(session, user_id: str, password: str) -> bool:
    """从数据库加载密码哈希并验证。"""
    from sqlalchemy import text

    result = await session.execute(
        text('SELECT password_hash FROM "user" WHERE id = :user_id'),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row or not row[0]:
        return False
    return _verify_password(password, row[0])


async def _write_cb_audit(
    *,
    tenant_id: str,
    operator_id: str,
    action: str,
    detail: dict | None = None,
    session=None,
) -> None:
    """写入熔断操作审计日志。"""
    try:
        if session is None:
            from drp.db.session import _session_factory

            async with _session_factory() as s:
                await _do_write_audit(s, tenant_id, operator_id, action, detail)
                await s.commit()
        else:
            await _do_write_audit(session, tenant_id, operator_id, action, detail)
            await session.commit()
    except Exception:
        logger.error("熔断审计日志写入失败", exc_info=True)


async def _do_write_audit(session, tenant_id, operator_id, action, detail):
    """执行审计日志写入。"""
    from sqlalchemy import text

    await session.execute(
        text(
            "INSERT INTO audit_log (id, tenant_id, user_id, action, detail, created_at) "
            "VALUES (gen_random_uuid(), :tenant_id, :operator_id, :action, :detail, NOW())"
        ),
        {
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "action": action,
            "detail": json.dumps(detail) if detail else None,
        },
    )
