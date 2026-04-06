"""ETL 任务运行器：桥接 Celery（同步）与 asyncio（异步）。

将实际的异步 IO 操作封装在此，由 tasks.py 通过 asyncio.run() 调用。

13.4 幂等重放保证：
- 每次同步创建唯一 run_id（UUID）
- 同一 run_id 若已存在 success 记录，直接返回（防止 Celery 重试重复写入）
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drp.config import settings
from drp.etl.engine import EtlSyncEngine
from drp.etl.models import EtlJob, EtlJobRepository
from drp.graphdb.client import GraphDBClient
from drp.tenants.repository import TenantRepository

logger = logging.getLogger(__name__)

_engine = create_async_engine(settings.postgres_dsn, pool_size=3)
_session_factory = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def _make_engine(tenant_id: str, mapping_yaml: str) -> EtlSyncEngine:
    """构建 EtlSyncEngine（占位，实际使用时替换 source_fetcher）。"""
    # source_fetcher 在真实部署中从 mapping_spec 或配置获取源库连接
    # 此处提供一个无操作占位（测试时 mock 替换）
    async def _noop_fetcher(table, watermark=None):
        return []

    return EtlSyncEngine(
        source_fetcher=_noop_fetcher,
        graphdb_client=GraphDBClient(),
        mapping_yaml=mapping_yaml,
        tenant_id=tenant_id,
    )


async def _is_run_id_duplicate(session: AsyncSession, run_id: uuid.UUID) -> bool:
    """检查 run_id 是否已成功执行（幂等保证）。"""
    result = await session.execute(
        select(EtlJob.id).where(
            EtlJob.run_id == run_id,
            EtlJob.status == "success",
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def run_full_sync(tenant_id: str, table: str, mapping_yaml: str, run_id: str | None = None) -> dict:
    """执行全量同步并记录 ETL Job。

    Args:
        tenant_id: 租户 UUID
        table: 源表名
        mapping_yaml: 映射配置 YAML 字符串
        run_id: 可选，外部传入的 run_id（用于幂等重放）
    """
    repo = EtlJobRepository()
    resolved_run_id = uuid.UUID(run_id) if run_id else uuid.uuid4()

    async with _session_factory() as session:
        # 幂等检查：同一 run_id 若已成功，直接返回
        if await _is_run_id_duplicate(session, resolved_run_id):
            logger.info("[全量同步] run_id=%s 已成功执行，跳过重复执行", resolved_run_id)
            return {"status": "skipped", "reason": "duplicate_run_id", "run_id": str(resolved_run_id)}

        job = await repo.create(session, uuid.UUID(tenant_id), "full_sync")
        job.run_id = resolved_run_id
        await session.flush()
        await session.commit()

        try:
            engine = await _make_engine(tenant_id, mapping_yaml)
            triples = await engine.full_sync(table)
            await repo.mark_success(session, job, triples)
            await session.commit()

            # ETL 成功后自动触发指标计算
            try:
                from drp.indicators.tasks import calculate_indicators_for_tenant_task
                calculate_indicators_for_tenant_task.delay(tenant_id)
                logger.info("[全量同步] 已触发指标计算: tenant=%s", tenant_id)
            except Exception as exc:
                logger.warning("[全量同步] 触发指标计算失败: %s", exc)

            return {"status": "success", "triples": triples, "job_id": str(job.id), "run_id": str(resolved_run_id)}
        except Exception as exc:
            await repo.mark_failed(session, job, str(exc))
            await session.commit()
            raise


async def run_incremental_sync(tenant_id: str, table: str, mapping_yaml: str, run_id: str | None = None) -> dict:
    """执行增量同步并记录 ETL Job。

    Args:
        tenant_id: 租户 UUID
        table: ��表名
        mapping_yaml: 映射配置 YAML 字符串
        run_id: 可选，外部传入的 run_id（用于幂等重放）
    """
    repo = EtlJobRepository()
    resolved_run_id = uuid.UUID(run_id) if run_id else uuid.uuid4()

    async with _session_factory() as session:
        # 幂等检查：同一 run_id 若已成功，直接返回
        if await _is_run_id_duplicate(session, resolved_run_id):
            logger.info("[增量同步] run_id=%s 已成功执行，跳过重复执行", resolved_run_id)
            return {"status": "skipped", "reason": "duplicate_run_id", "run_id": str(resolved_run_id)}

        watermark = await repo.get_last_watermark(session, uuid.UUID(tenant_id), "incremental_sync")
        job = await repo.create(session, uuid.UUID(tenant_id), "incremental_sync")
        job.run_id = resolved_run_id
        await session.flush()
        await session.commit()

        try:
            engine = await _make_engine(tenant_id, mapping_yaml)
            triples, new_watermark = await engine.incremental_sync(table, watermark)
            await repo.mark_success(session, job, triples, watermark=new_watermark)
            await session.commit()

            # ETL 成功后自动触发指标计算
            try:
                from drp.indicators.tasks import calculate_indicators_for_tenant_task
                calculate_indicators_for_tenant_task.delay(tenant_id)
                logger.info("[增量同步] 已触发指标计算: tenant=%s", tenant_id)
            except Exception as exc:
                logger.warning("[增量同步] 触发指标计算失败: %s", exc)

            return {"status": "success", "triples": triples, "job_id": str(job.id), "run_id": str(resolved_run_id)}
        except Exception as exc:
            await repo.mark_failed(session, job, str(exc))
            await session.commit()
            raise


async def get_active_tenant_configs() -> list[dict]:
    """返回所有激活租户的同步配置（供 Beat 触发用）。"""
    from drp.tenants.repository import TenantRepository
    tenant_repo = TenantRepository()
    async with _session_factory() as session:
        tenants = await tenant_repo.list_active(session)
    # 实际配置从 mapping_spec 查询，此处返回空（无映射时跳过）
    return []
