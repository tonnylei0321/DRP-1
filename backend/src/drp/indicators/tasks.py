"""指标计算 Celery 任务定义。"""
import asyncio
import logging

from drp.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="drp.indicators.tasks.calculate_indicators_for_tenant",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def calculate_indicators_for_tenant_task(self, tenant_id: str) -> dict:
    """对单个租户计算全部 106 条指标（按业务域分批执行）。"""
    try:
        return asyncio.run(_run_calculation(tenant_id))
    except Exception as exc:
        logger.error("[指标计算] 失败: tenant=%s err=%s", tenant_id, exc)
        raise self.retry(exc=exc)


async def _run_calculation(tenant_id: str) -> dict:
    """异步计算入口，供 Celery 任务通过 asyncio.run() 调用。"""
    from drp.indicators.calculator import calculate_all_domains

    all_results = await calculate_all_domains(tenant_id)

    total = sum(len(v) for v in all_results.values())
    compliant = sum(
        sum(1 for r in v if r.is_compliant) for v in all_results.values()
    )
    logger.info(
        "[指标计算] 完成: tenant=%s total=%d compliant=%d",
        tenant_id, total, compliant,
    )
    return {"tenant_id": tenant_id, "total": total, "compliant": compliant}


@celery_app.task(name="drp.indicators.tasks.trigger_indicator_calc_all_tenants")
def trigger_indicator_calc_all_tenants() -> None:
    """Beat 定时任务：对所有激活租户触发指标计算（每 60 分钟）。"""
    configs = asyncio.run(_get_active_tenants())
    for tenant_id in configs:
        calculate_indicators_for_tenant_task.delay(tenant_id)
    logger.info("[Beat] 已触发 %d 个租户的指标计算", len(configs))


async def _get_active_tenants() -> list[str]:
    """返回所有激活租户的 ID 列表。"""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from drp.config import settings
    from drp.tenants.repository import TenantRepository

    engine = create_async_engine(settings.postgres_dsn, pool_size=2)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    repo = TenantRepository()
    async with factory() as session:
        tenants = await repo.list_active(session)
    await engine.dispose()
    return [str(t.id) for t in tenants]
