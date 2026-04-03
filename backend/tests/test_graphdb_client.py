"""GraphDBClient 单元测试（respx mock httpx）。"""
import pytest
import respx
import httpx
from respx.patterns import M

from drp.graphdb.client import GraphDBClient, GraphDBError


BASE = "http://localhost:7200/repositories/drp"


@pytest.fixture
def client():
    """注入 httpx.AsyncClient（respx 会拦截所有请求）。"""
    return httpx.AsyncClient(auth=("admin", "root"), timeout=10.0)


@respx.mock
async def test_create_named_graph_成功(client):
    """CREATE SILENT GRAPH 返回 204 时应静默成功。"""
    respx.post(f"{BASE}/statements").mock(return_value=httpx.Response(204))
    gc = GraphDBClient(client=client)
    await gc.create_named_graph("urn:tenant:abc")
    assert respx.calls.call_count == 1
    body = respx.calls.last.request.content.decode()
    assert "CREATE SILENT GRAPH" in body
    assert "urn:tenant:abc" in body


@respx.mock
async def test_create_named_graph_失败时抛出异常(client):
    """GraphDB 返回 500 时应抛出 GraphDBError。"""
    respx.post(f"{BASE}/statements").mock(return_value=httpx.Response(500, text="服务器错误"))
    gc = GraphDBClient(client=client)
    with pytest.raises(GraphDBError, match="SPARQL Update 失败"):
        await gc.create_named_graph("urn:tenant:abc")


@respx.mock
async def test_delete_named_graph_成功(client):
    """DROP SILENT GRAPH 返回 204 时应静默成功。"""
    respx.post(f"{BASE}/statements").mock(return_value=httpx.Response(204))
    gc = GraphDBClient(client=client)
    await gc.delete_named_graph("urn:tenant:xyz")
    body = respx.calls.last.request.content.decode()
    assert "DROP SILENT GRAPH" in body
    assert "urn:tenant:xyz" in body


@respx.mock
async def test_named_graph_exists_返回true(client):
    """ASK 查询返回 true 时应返回 True。"""
    respx.post(BASE).mock(
        return_value=httpx.Response(
            200,
            json={"boolean": True},
            headers={"Content-Type": "application/sparql-results+json"},
        )
    )
    gc = GraphDBClient(client=client)
    result = await gc.named_graph_exists("urn:tenant:abc")
    assert result is True


@respx.mock
async def test_named_graph_exists_返回false(client):
    """ASK 查询返回 false 时应返回 False。"""
    respx.post(BASE).mock(
        return_value=httpx.Response(
            200,
            json={"boolean": False},
            headers={"Content-Type": "application/sparql-results+json"},
        )
    )
    gc = GraphDBClient(client=client)
    result = await gc.named_graph_exists("urn:tenant:abc")
    assert result is False
