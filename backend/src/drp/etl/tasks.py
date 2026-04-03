"""ETL Celery 任务定义。"""
import logging
import uuid
from datetime import timezone

from drp.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="drp.etl.tasks.full_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def full_sync_task(self, tenant_id: str, table: str, mapping_yaml: str) -> dict:
    """全量同步 Celery 任务。

    异步执行：同步创建 DB session、GraphDB client，调用 EtlSyncEngine。
    """
    import asyncio
    from drp.etl._task_runner import run_full_sync
    try:
        return asyncio.run(run_full_sync(tenant_id, table, mapping_yaml))
    except Exception as exc:
        logger.error("[全量同步] 失败: tenant=%s table=%s err=%s", tenant_id, table, exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="drp.etl.tasks.incremental_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def incremental_sync_task(self, tenant_id: str, table: str, mapping_yaml: str) -> dict:
    """增量同步 Celery 任务（每 60 分钟触发）。"""
    import asyncio
    from drp.etl._task_runner import run_incremental_sync
    try:
        return asyncio.run(run_incremental_sync(tenant_id, table, mapping_yaml))
    except Exception as exc:
        logger.error("[增量同步] 失败: tenant=%s table=%s err=%s", tenant_id, table, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="drp.etl.tasks.trigger_incremental_sync_all_tenants")
def trigger_incremental_sync_all_tenants() -> None:
    """Beat 定时任务：对所有激活租户触发增量同步。"""
    import asyncio
    from drp.etl._task_runner import get_active_tenant_configs

    configs = asyncio.run(get_active_tenant_configs())
    for cfg in configs:
        incremental_sync_task.delay(cfg["tenant_id"], cfg["table"], cfg["mapping_yaml"])
    logger.info("[Beat] 已触发 %d 个租户的增量同步", len(configs))
