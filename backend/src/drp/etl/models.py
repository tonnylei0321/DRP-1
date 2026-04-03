"""ETL 任务 ORM 模型和状态管理 Repository。"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from drp.db.base import Base


class EtlJob(Base):
    """ETL 任务记录，映射 PostgreSQL `etl_job` 表。"""

    __tablename__ = "etl_job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triples_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EtlJobRepository:
    """ETL 任务状态 CRUD。"""

    async def create(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        job_type: str,
    ) -> EtlJob:
        job = EtlJob(tenant_id=tenant_id, job_type=job_type)
        session.add(job)
        await session.flush()
        await session.refresh(job)
        return job

    async def mark_success(
        self,
        session: AsyncSession,
        job: EtlJob,
        triples: int,
        watermark: datetime | None = None,
    ) -> None:
        from datetime import timezone
        job.status = "success"
        job.triples_written = triples
        job.finished_at = datetime.now(timezone.utc)
        if watermark:
            job.last_synced_at = watermark
        await session.flush()

    async def mark_failed(
        self,
        session: AsyncSession,
        job: EtlJob,
        error: str,
    ) -> None:
        from datetime import timezone
        job.status = "failed"
        job.error_message = error[:2000]
        job.finished_at = datetime.now(timezone.utc)
        await session.flush()

    async def mark_retrying(self, session: AsyncSession, job: EtlJob) -> None:
        job.status = "retrying"
        await session.flush()

    async def get_last_watermark(
        self, session: AsyncSession, tenant_id: uuid.UUID, job_type: str
    ) -> datetime | None:
        """返回上次成功同步的水位线时间戳。"""
        result = await session.execute(
            select(EtlJob.last_synced_at)
            .where(
                EtlJob.tenant_id == tenant_id,
                EtlJob.job_type == job_type,
                EtlJob.status == "success",
                EtlJob.last_synced_at.is_not(None),
            )
            .order_by(EtlJob.finished_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
