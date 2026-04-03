import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from drp.graphdb.client import GraphDBClient, GraphDBError
from drp.tenants.repository import TenantRepository
from drp.tenants.schemas import TenantCreate, TenantResponse

logger = logging.getLogger(__name__)


class TenantNotFoundError(Exception):
    """租户不存在。"""


class TenantService:
    """租户业务逻辑：协调 PostgreSQL 元数据与 GraphDB Named Graph。"""

    def __init__(
        self,
        session: AsyncSession,
        repository: TenantRepository | None = None,
        graphdb: GraphDBClient | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or TenantRepository()
        self._graphdb = graphdb or GraphDBClient()

    async def create_tenant(self, data: TenantCreate) -> TenantResponse:
        """创建租户：① 写 PG 元数据  ② 创建 GraphDB Named Graph。

        若 GraphDB 创建失败，回滚 PG 记录并抛出 RuntimeError。
        """
        tenant_id = uuid.uuid4()
        graph_iri = f"urn:tenant:{tenant_id}"

        # 步骤 1：写入 PostgreSQL
        tenant = await self._repo.create(self._session, data, graph_iri, tenant_id)
        await self._session.commit()

        # 步骤 2：创建 GraphDB Named Graph
        try:
            await self._graphdb.create_named_graph(graph_iri)
        except GraphDBError as exc:
            logger.error("创建 Named Graph 失败，回滚租户记录: %s", exc)
            await self._session.delete(tenant)
            await self._session.commit()
            raise RuntimeError("GraphDB 不可用，无法完成租户创建") from exc

        return TenantResponse.model_validate(tenant)

    async def get_tenant(self, tenant_id: uuid.UUID) -> TenantResponse:
        """查询租户详情，不存在抛出 TenantNotFoundError。"""
        tenant = await self._repo.get_by_id(self._session, tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"租户不存在: {tenant_id}")
        return TenantResponse.model_validate(tenant)

    async def delete_tenant(self, tenant_id: uuid.UUID) -> None:
        """删除租户：① 删除 GraphDB Named Graph  ② 删除 PG 记录。

        GraphDB 删除失败时记录 warning 并继续（幂等容错）。
        """
        tenant = await self._repo.get_by_id(self._session, tenant_id)
        if tenant is None:
            raise TenantNotFoundError(f"租户不存在: {tenant_id}")

        # 步骤 1：删除 Named Graph（幂等，不存在则 warning）
        try:
            await self._graphdb.delete_named_graph(tenant.graph_iri)
        except GraphDBError as exc:
            logger.warning("删除 Named Graph 失败，继续删除 PG 记录: %s", exc)

        # 步骤 2：删除 PG 记录
        await self._repo.delete(self._session, tenant_id)
        await self._session.commit()
