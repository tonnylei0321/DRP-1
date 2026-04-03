"""
12.5 健康检查端点增强 — 含依赖组件状态
12.8 数据新鲜度告警 — 超过 90 分钟未完成增量同步则告警
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from drp.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["基础设施"])

_FRESHNESS_THRESHOLD_MINUTES = 90


@router.get("/health")
async def health_check() -> dict:
    """增强版健康���查端点，检测各依赖组件状态。"""
    checks: dict[str, str] = {}

    # GraphDB 检查
    checks["graphdb"] = await _check_graphdb()
    # Redis 检查
    checks["redis"] = await _check_redis()
    # PostgreSQL 检查
    checks["postgres"] = await _check_postgres()

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": "0.1.0",
        "env": settings.app_env,
        "components": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _check_graphdb() -> str:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as c:
            resp = await c.get(f"{settings.graphdb_url}/rest/repositories")
        return "ok" if resp.status_code == 200 else f"error:{resp.status_code}"
    except Exception as exc:
        return f"error:{exc}"


async def _check_redis() -> str:
    try:
        import redis.asyncio as aioredis
        async with aioredis.from_url(settings.redis_url) as r:
            await r.ping()
        return "ok"
    except Exception as exc:
        return f"error:{exc}"


async def _check_postgres() -> str:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.postgres_dsn, pool_size=1)
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        await engine.dispose()
        return "ok"
    except Exception as exc:
        return f"error:{exc}"


def check_data_freshness(last_synced_at: datetime | None) -> bool:
    """
    12.8 数据新鲜度检查：超过 90 分钟未同步则返回 False（触发告警）。

    Args:
        last_synced_at: 最后一次成功增量同步的时间戳

    Returns:
        True 表示数据新鲜，False 表示需要告警
    """
    if last_synced_at is None:
        logger.warning("数据新鲜度告警：从未完成增量同步")
        return False
    threshold = datetime.now(timezone.utc) - timedelta(minutes=_FRESHNESS_THRESHOLD_MINUTES)
    if last_synced_at < threshold:
        age_minutes = (datetime.now(timezone.utc) - last_synced_at).total_seconds() / 60
        logger.warning(
            "数据新鲜度告警：超过 %.0f 分钟未完成增量同步（上次: %s）",
            age_minutes, last_synced_at.isoformat(),
        )
        return False
    return True
