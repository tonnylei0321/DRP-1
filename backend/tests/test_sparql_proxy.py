"""SPARQL 代理层单元测试（不依赖外部服务）。"""
import pytest

from drp.sparql.proxy import (
    TenantContextMissingError,
    _inject_graph_context,
    set_tenant_context,
    sparql_query,
    sparql_update,
)

TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
GRAPH_IRI = f"urn:tenant:{TENANT_ID}"


# ─── _inject_graph_context 改写逻辑 ───────────────────────────────────────────


def test_注入select查询():
    """SELECT WHERE 应被包入 GRAPH 子句。"""
    sparql = "SELECT ?s WHERE { ?s ?p ?o }"
    result = _inject_graph_context(sparql, TENANT_ID)
    assert f"GRAPH <{GRAPH_IRI}>" in result
    assert "?s ?p ?o" in result
    # 原始 WHERE 被替换
    assert "WHERE { GRAPH" in result


def test_注入construct查询():
    """CONSTRUCT WHERE 应被包入 GRAPH 子句。"""
    sparql = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    result = _inject_graph_context(sparql, TENANT_ID)
    assert f"GRAPH <{GRAPH_IRI}>" in result


def test_注入ask查询():
    """ASK WHERE 应被包入 GRAPH 子句。"""
    sparql = "ASK WHERE { ?s a <http://example.org/Foo> }"
    result = _inject_graph_context(sparql, TENANT_ID)
    assert f"GRAPH <{GRAPH_IRI}>" in result


def test_注入多级嵌套():
    """嵌套花括号应正确识别最外层 WHERE 范围。"""
    sparql = "SELECT ?s WHERE { ?s a ?t . FILTER(?t = <http://ex/A>) }"
    result = _inject_graph_context(sparql, TENANT_ID)
    assert f"GRAPH <{GRAPH_IRI}>" in result
    assert "FILTER" in result


def test_无where子句原样返回():
    """INSERT DATA 无 WHERE 子句时原样返回（调用方负责正确构造）。"""
    sparql = "INSERT DATA { <s> <p> <o> }"
    result = _inject_graph_context(sparql, TENANT_ID)
    # 无 WHERE，原样返回
    assert result == sparql


# ─── 缺少租户上下文时拒绝查询 ─────────────────────────────────────────────────


async def test_sparql_query_缺少上下文时抛异常():
    """未设置租户 ID 且不传参数时，应抛出 TenantContextMissingError。"""
    # 重置 ContextVar（默认 None）
    with pytest.raises(TenantContextMissingError):
        await sparql_query("SELECT * WHERE { ?s ?p ?o }")


async def test_sparql_update_缺少上下文时抛异常():
    """未设置租户 ID 且不传参数时，应抛出 TenantContextMissingError。"""
    with pytest.raises(TenantContextMissingError):
        await sparql_update("DELETE WHERE { ?s ?p ?o }")


# ─── ContextVar 行为 ──────────────────────────────────────────────────────────


def test_set_tenant_context_可读取():
    """set_tenant_context 应能在同一协程中读取。"""
    from drp.sparql.proxy import get_tenant_context
    set_tenant_context("tenant-abc")
    assert get_tenant_context() == "tenant-abc"
