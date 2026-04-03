"""多租户隔离集成测试。

需要真实 GraphDB + PostgreSQL。用 pytest 标记 `integration` 控制跳过。

运行方式：
    docker-compose -f docker-compose.dev.yml up -d
    cd backend && uv run pytest -m integration -v
"""
import os
import uuid

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drp.config import settings
from drp.graphdb.client import GraphDBClient
from drp.sparql.proxy import set_tenant_context, sparql_query, sparql_update
from drp.tenants.models import Base, Tenant
from drp.tenants.repository import TenantRepository
from drp.tenants.schemas import TenantCreate
from drp.tenants.service import TenantService


# ─── 基础设施：检测 PostgreSQL 是否可用 ──────────────────────────────────────


def _pg_available() -> bool:
    try:
        import socket
        s = socket.create_connection(
            (settings.postgres_host, settings.postgres_port), timeout=2
        )
        s.close()
        return True
    except OSError:
        return False


def _graphdb_available() -> bool:
    try:
        import socket
        host = settings.graphdb_url.split("://")[-1].split(":")[0]
        port_str = settings.graphdb_url.split(":")[-1].rstrip("/")
        port = int(port_str) if port_str.isdigit() else 7200
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        return True
    except OSError:
        return False


skip_if_no_pg = pytest.mark.skipif(
    not _pg_available(), reason="PostgreSQL 不可用，跳过集成测试"
)
skip_if_no_graphdb = pytest.mark.skipif(
    not _graphdb_available(), reason="GraphDB 不可用，跳过集成测试"
)


# ─── Fixture ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    """为测试库创建独立 AsyncEngine 并建表。"""
    engine = create_async_engine(settings.postgres_dsn, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine):
    """每个测试独立事务，测试结束后回滚。"""
    factory = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def graphdb_client():
    """GraphDB HTTP 客户端（不 mock）。"""
    async with httpx.AsyncClient(
        auth=(settings.graphdb_username, settings.graphdb_password), timeout=15.0
    ) as client:
        yield GraphDBClient(client=client)


# ─── Named Graph 生命周期测试 ─────────────────────────────────────────────────


@pytest.mark.integration
@skip_if_no_graphdb
async def test_named_graph_创建和删除(graphdb_client):
    """Named Graph 创建后应存在，删除后应不存在。"""
    iri = f"urn:tenant:test-{uuid.uuid4()}"

    await graphdb_client.create_named_graph(iri)
    assert await graphdb_client.named_graph_exists(iri) is True

    await graphdb_client.delete_named_graph(iri)
    assert await graphdb_client.named_graph_exists(iri) is False


@pytest.mark.integration
@skip_if_no_graphdb
async def test_named_graph_幂等创建(graphdb_client):
    """CREATE SILENT 对已存在的 Named Graph 应无错误。"""
    iri = f"urn:tenant:test-{uuid.uuid4()}"
    await graphdb_client.create_named_graph(iri)
    await graphdb_client.create_named_graph(iri)  # 第二次调用不应报错
    await graphdb_client.delete_named_graph(iri)


@pytest.mark.integration
@skip_if_no_graphdb
async def test_named_graph_幂等删除(graphdb_client):
    """DROP SILENT 对不存在的 Named Graph 应无错误。"""
    iri = f"urn:tenant:nonexistent-{uuid.uuid4()}"
    await graphdb_client.delete_named_graph(iri)  # 不应报错


# ─── 多租户隔离核心测试 ───────────────────────────────────────────────────────


@pytest.mark.integration
@skip_if_no_graphdb
async def test_租户数据隔离_租户A无法查询租户B数据():
    """
    场景：租户 A 和 B 分别写入不同三元组，
    以租户 A 上下文查询租户 B 的专有数据，应返回空结果。
    """
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    subject_a = f"<urn:test:entity-a-{tenant_a}>"
    subject_b = f"<urn:test:entity-b-{tenant_b}>"

    graph_a = f"urn:tenant:{tenant_a}"
    graph_b = f"urn:tenant:{tenant_b}"

    base_url = f"{settings.graphdb_url}/repositories/{settings.graphdb_repository}"
    async with httpx.AsyncClient(
        auth=(settings.graphdb_username, settings.graphdb_password), timeout=15.0
    ) as client:
        gc = GraphDBClient(client=client)

        # 步骤 1：创建两个 Named Graph
        await gc.create_named_graph(graph_a)
        await gc.create_named_graph(graph_b)

        # 步骤 2：向各自 Named Graph 写入专有三元组
        insert_a = f"INSERT DATA {{ GRAPH <{graph_a}> {{ {subject_a} a <urn:test:EntityA> }} }}"
        insert_b = f"INSERT DATA {{ GRAPH <{graph_b}> {{ {subject_b} a <urn:test:EntityB> }} }}"

        for stmt in [insert_a, insert_b]:
            resp = await client.post(
                f"{base_url}/statements",
                content=stmt,
                headers={"Content-Type": "application/sparql-update"},
            )
            assert resp.status_code in (200, 204), f"写入失败: {resp.text}"

        # 步骤 3：以租户 A 上下文查询租户 B 的专有三元组
        results = await sparql_query(
            f"SELECT ?s WHERE {{ ?s a <urn:test:EntityB> }}",
            tenant_id=tenant_a,
            client=client,
        )

        # 断言：租户 A 不应看到租户 B 的数据
        assert results == [], f"隔离失效！租户 A 查到了租户 B 的数据: {results}"

        # 步骤 4：用正确上下文查询，应能看到
        results_b = await sparql_query(
            f"SELECT ?s WHERE {{ ?s a <urn:test:EntityB> }}",
            tenant_id=tenant_b,
            client=client,
        )
        assert any(r.get("s") == f"urn:test:entity-b-{tenant_b}" for r in results_b), \
            f"租户 B 应能查到自己的数据: {results_b}"

        # 步骤 5：清理
        await gc.delete_named_graph(graph_a)
        await gc.delete_named_graph(graph_b)
