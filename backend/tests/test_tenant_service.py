"""TenantService 单元测试（mock Repository + GraphDBClient）。"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drp.graphdb.client import GraphDBError
from drp.tenants.models import Tenant
from drp.tenants.schemas import TenantCreate, TenantResponse
from drp.tenants.service import TenantNotFoundError, TenantService


def _make_tenant(name="测试租户", slug="test-co") -> Tenant:
    tid = uuid.uuid4()
    t = Tenant()
    t.id = tid
    t.name = name
    t.slug = slug
    t.status = "active"
    t.graph_iri = f"urn:tenant:{tid}"
    t.created_at = datetime(2026, 4, 3, 0, 0, 0, tzinfo=timezone.utc)
    return t


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_graphdb():
    return AsyncMock()


@pytest.fixture
def service(mock_session, mock_repo, mock_graphdb):
    return TenantService(
        session=mock_session,
        repository=mock_repo,
        graphdb=mock_graphdb,
    )


# ─── create_tenant ────────────────────────────────────────────────────────────


async def test_create_tenant_正常流程(service, mock_repo, mock_graphdb, mock_session):
    """正常创建：写 PG → 创建 Named Graph → 返回 TenantResponse。"""
    data = TenantCreate(name="航天科工", slug="casic")
    tenant = _make_tenant("航天科工", "casic")
    mock_repo.create.return_value = tenant

    result = await service.create_tenant(data)

    mock_repo.create.assert_called_once()
    mock_session.commit.assert_called()
    mock_graphdb.create_named_graph.assert_called_once()
    # graph_iri 由 service 内部生成，验证格式即可
    called_iri = mock_graphdb.create_named_graph.call_args[0][0]
    assert called_iri.startswith("urn:tenant:")
    assert isinstance(result, TenantResponse)
    assert result.slug == "casic"


async def test_create_tenant_graphdb失败时回滚(service, mock_repo, mock_graphdb, mock_session):
    """GraphDB 创建失败时，应回滚 PG 记录并抛出 RuntimeError。"""
    data = TenantCreate(name="失败租户", slug="fail-co")
    tenant = _make_tenant("失败租户", "fail-co")
    mock_repo.create.return_value = tenant
    mock_graphdb.create_named_graph.side_effect = GraphDBError("连接拒绝")

    with pytest.raises(RuntimeError, match="GraphDB 不可用"):
        await service.create_tenant(data)

    # 应删除刚写入的记录
    mock_session.delete.assert_called_once_with(tenant)
    mock_session.commit.assert_called()


# ─── get_tenant ───────────────────────────────────────────────────────────────


async def test_get_tenant_存在(service, mock_repo):
    """租户存在时应返回 TenantResponse。"""
    tenant = _make_tenant()
    mock_repo.get_by_id.return_value = tenant

    result = await service.get_tenant(tenant.id)

    assert result.id == tenant.id
    assert isinstance(result, TenantResponse)


async def test_get_tenant_不存在(service, mock_repo):
    """租户不存在时应抛出 TenantNotFoundError。"""
    mock_repo.get_by_id.return_value = None

    with pytest.raises(TenantNotFoundError):
        await service.get_tenant(uuid.uuid4())


# ─── delete_tenant ────────────────────────────────────────────────────────────


async def test_delete_tenant_正常流程(service, mock_repo, mock_graphdb, mock_session):
    """正常删除：先删 Named Graph，再删 PG 记录。"""
    tenant = _make_tenant()
    mock_repo.get_by_id.return_value = tenant

    await service.delete_tenant(tenant.id)

    mock_graphdb.delete_named_graph.assert_called_once_with(tenant.graph_iri)
    mock_repo.delete.assert_called_once_with(mock_session, tenant.id)
    mock_session.commit.assert_called()


async def test_delete_tenant_不存在(service, mock_repo):
    """租户不存在时应抛出 TenantNotFoundError。"""
    mock_repo.get_by_id.return_value = None

    with pytest.raises(TenantNotFoundError):
        await service.delete_tenant(uuid.uuid4())


async def test_delete_tenant_graphdb失败时继续删pg(service, mock_repo, mock_graphdb, mock_session):
    """GraphDB 删除失败时应 warning 并继续删 PG（幂等容错）。"""
    tenant = _make_tenant()
    mock_repo.get_by_id.return_value = tenant
    mock_graphdb.delete_named_graph.side_effect = GraphDBError("连接失败")

    # 不应抛出异常
    await service.delete_tenant(tenant.id)

    mock_repo.delete.assert_called_once()
    mock_session.commit.assert_called()
