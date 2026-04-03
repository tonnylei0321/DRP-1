"""ETL 任务运行器：桥接 Celery（同步）与 asyncio（异步）。

将实际的异步 IO 操作封装在此，由 tasks.py 通过 asyncio.run() 调用。
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drp.config import settings
from drp.etl.engine import EtlSyncEngine
from drp.etl.models import EtlJobRepository
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


async def run_full_sync(tenant_id: str, table: str, mapping_yaml: str) -> dict:
    """执行全量同步并记录 ETL Job。"""
    repo = EtlJobRepository()
    async with _session_factory() as session:
        job = await repo.create(session, uuid.UUID(tenant_id), "full_sync")
        await session.commit()

        try:
            engine = await _make_engine(tenant_id, mapping_yaml)
            triples = await engine.full_sync(table)
            await repo.mark_success(session, job, triples)
            await session.commit()
            return {"status": "success", "triples": triples, "job_id": str(job.id)}
        except Exception as exc:
            await repo.mark_failed(session, job, str(exc))
            await session.commit()
            raise


async def run_incremental_sync(tenant_id: str, table: str, mapping_yaml: str) -> dict:
    """执行增量同步并记录 ETL Job。"""
    repo = EtlJobRepository()
    async with _session_factory() as session:
        watermark = await repo.get_last_watermark(session, uuid.UUID(tenant_id), "incremental_sync")
        job = await repo.create(session, uuid.UUID(tenant_id), "incremental_sync")
        await session.commit()

        try:
            engine = await _make_engine(tenant_id, mapping_yaml)
            triples, new_watermark = await engine.incremental_sync(table, watermark)
            await repo.mark_success(session, job, triples, watermark=new_watermark)
            await session.commit()
            return {"status": "success", "triples": triples, "job_id": str(job.id)}
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
