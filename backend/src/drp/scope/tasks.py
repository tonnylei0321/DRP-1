"""Celery beat 熔断审计定时任务。

每 5 分钟检查所有租户的熔断状态，禁用状态时写入审计日志提醒。

注意：如果项目中没有完整的 Celery 配置，此模块提供占位实现，
可通过 run_circuit_breaker_audit() 手动调用核心逻辑。
"""

from __future__ import annotations

import json
import logging

from drp.config import settings

logger = logging.getLogger(__name__)

# Redis 键前缀（与 circuit_breaker.py 保持一致）
CB_KEY_PREFIX = "ds:circuit_breaker"


async def run_circuit_breaker_audit() -> None:
    """检查所有租户的熔断状态，禁用时写入审计日志提醒。

    核心逻辑：
    1. 扫描 Redis 中所有 ds:circuit_breaker:* 键
    2. 对 enabled=False 的租户写入审计日志提醒
    """
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        try:
            # 扫描所有熔断键
            keys: list[bytes] = []
            async for key in r.scan_iter(match=f"{CB_KEY_PREFIX}:*"):
                keys.append(key)

            for key in keys:
                raw = await r.get(key)
                if raw is None:
                    continue

                data = json.loads(raw)
                if not data.get("enabled", True):
                    # 熔断处于禁用状态，提取 tenant_id
                    key_str = key.decode() if isinstance(key, bytes) else key
                    tenant_id = key_str.replace(f"{CB_KEY_PREFIX}:", "")
                    operator_id = data.get("operator_id", "unknown")

                    logger.warning(
                        "租户 %s 的数据权限熔断开关处于禁用状态（操作者: %s）",
                        tenant_id,
                        operator_id,
                    )

                    # 写入审计日志
                    await _write_audit_reminder(tenant_id, operator_id)
        finally:
            await r.aclose()
    except Exception:
        logger.error("熔断审计定时任务执行失败", exc_info=True)


async def _write_audit_reminder(tenant_id: str, operator_id: str) -> None:
    """写入熔断状态审计提醒日志。"""
    try:
        from drp.db.session import _session_factory
        from sqlalchemy import text

        async with _session_factory() as session:
            await session.execute(
                text(
                    "INSERT INTO audit_log (id, tenant_id, user_id, action, detail, created_at) "
                    "VALUES (gen_random_uuid(), :tenant_id, :operator_id, :action, :detail, NOW())"
                ),
                {
                    "tenant_id": tenant_id,
                    "operator_id": operator_id if operator_id != "unknown" else None,
                    "action": "circuit_breaker.audit_reminder",
                    "detail": json.dumps({
                        "message": "数据权限熔断开关仍处于禁用状态",
                        "operator_id": operator_id,
                    }),
                },
            )
            await session.commit()
    except Exception:
        logger.error("审计提醒日志写入失败", exc_info=True)


# ---------------------------------------------------------------------------
# Celery 集成（占位实现）
# ---------------------------------------------------------------------------

try:
    from celery import Celery

    celery_app = Celery("drp")
    celery_app.config_from_object(settings, namespace="CELERY")

    @celery_app.task(name="drp.scope.tasks.circuit_breaker_audit_task")
    def circuit_breaker_audit_task():
        """Celery 任务包装器：运行熔断审计检查。"""
        import asyncio

        asyncio.run(run_circuit_breaker_audit())

    # 注册到 celery beat schedule
    celery_app.conf.beat_schedule = {
        **getattr(celery_app.conf, "beat_schedule", {}),
        "circuit-breaker-audit": {
            "task": "drp.scope.tasks.circuit_breaker_audit_task",
            "schedule": 300.0,  # 每 5 分钟
        },
    }

except ImportError:
    # Celery 未安装，提供占位实现
    logger.info("Celery 未安装，熔断审计定时任务使用占位实现")
    celery_app = None

    def circuit_breaker_audit_task():
        """占位实现：Celery 未安装时不执行。"""
        logger.warning("Celery 未安装，请手动调用 run_circuit_breaker_audit()")
