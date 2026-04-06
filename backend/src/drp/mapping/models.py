"""映射规范 ORM 模型（映射 mapping_spec 表）和存取 Repository。"""
import hashlib
import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select, DateTime

from drp.db.base import Base


class MappingSpec(Base):
    """字段映射规范，映射 PostgreSQL `mapping_spec` 表。"""

    __tablename__ = "mapping_spec"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    ddl_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_table: Mapped[str] = mapped_column(String(255), nullable=False)
    source_field: Mapped[str] = mapped_column(String(255), nullable=False)
    target_property: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transform_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    auto_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("tenant_id", "ddl_hash", "source_table", "source_field"),)


def compute_ddl_hash(ddl: str) -> str:
    """计算 DDL 内容的 SHA-256 哈希（用于幂等存储）。"""
    return hashlib.sha256(ddl.encode()).hexdigest()


class MappingRepository:
    """映射规范 PostgreSQL CRUD。"""

    async def upsert_mappings(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        ddl_hash: str,
        suggestions: list[dict],
    ) -> list[MappingSpec]:
        """批量插入映射建议（已存在则跳过）。"""
        results = []
        for s in suggestions:
            existing = await session.execute(
                select(MappingSpec).where(
                    MappingSpec.tenant_id == tenant_id,
                    MappingSpec.ddl_hash == ddl_hash,
                    MappingSpec.source_table == s["source_table"],
                    MappingSpec.source_field == s["source_field"],
                )
            )
            obj = existing.scalar_one_or_none()
            if obj is None:
                obj = MappingSpec(
                    tenant_id=tenant_id,
                    ddl_hash=ddl_hash,
                    source_table=s["source_table"],
                    source_field=s["source_field"],
                    target_property=s.get("target_property"),
                    transform_rule=s.get("transform_rule"),
                    confidence=s.get("confidence"),
                    auto_approved=s.get("auto_approved", False),
                    status="approved" if s.get("auto_approved") else "pending",
                )
                session.add(obj)
            results.append(obj)

        await session.flush()
        return results

    async def get_by_id(
        self, session: AsyncSession, mapping_id: uuid.UUID
    ) -> MappingSpec | None:
        result = await session.execute(
            select(MappingSpec).where(MappingSpec.id == mapping_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status: str | None = None,
    ) -> list[MappingSpec]:
        q = select(MappingSpec).where(MappingSpec.tenant_id == tenant_id)
        if status:
            q = q.where(MappingSpec.status == status)
        result = await session.execute(q.order_by(MappingSpec.created_at))
        return list(result.scalars().all())

    async def get_approved_for_history(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> list[dict]:
        """返回已批准的映射记录（供置信度算法使用）。"""
        results = await self.list_by_tenant(session, tenant_id, status="approved")
        return [
            {
                "source_table": r.source_table,
                "source_field": r.source_field,
                "target_property": r.target_property,
            }
            for r in results
        ]
