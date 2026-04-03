import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drp.tenants.models import Tenant
from drp.tenants.schemas import TenantCreate


class TenantRepository:
    """租户 PostgreSQL CRUD，不含业务逻辑。"""

    async def create(
        self,
        session: AsyncSession,
        data: TenantCreate,
        graph_iri: str,
        tenant_id: uuid.UUID,
    ) -> Tenant:
        """插入新租户记录并刷新（不提交事务）。"""
        tenant = Tenant(
            id=tenant_id,
            name=data.name,
            slug=data.slug,
            graph_iri=graph_iri,
        )
        session.add(tenant)
        await session.flush()
        await session.refresh(tenant)
        return tenant

    async def get_by_id(
        self, session: AsyncSession, tenant_id: uuid.UUID
    ) -> Tenant | None:
        """按 UUID 查询租户，不存在返回 None。"""
        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(
        self, session: AsyncSession, slug: str
    ) -> Tenant | None:
        """按 slug 查询租户，不存在返回 None。"""
        result = await session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def delete(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        """删除租户记录（不提交事务）。不存在则静默跳过。"""
        tenant = await self.get_by_id(session, tenant_id)
        if tenant is not None:
            await session.delete(tenant)
            await session.flush()

    async def list_active(self, session: AsyncSession) -> list[Tenant]:
        """列出所有激活租户，按创建时间升序。"""
        result = await session.execute(
            select(Tenant)
            .where(Tenant.status == "active")
            .order_by(Tenant.created_at)
        )
        return list(result.scalars().all())
