import re
from contextvars import ContextVar

import httpx

from drp.config import settings

# FastAPI 中间件写入；Celery task 显式设置
_tenant_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)


class TenantContextMissingError(Exception):
    """未设置租户上下文，拒绝无边界 SPARQL 操作。"""


def set_tenant_context(tenant_id: str) -> None:
    """设置当前协程上下文的租户 ID（供中间件和 Celery 任务调用）。"""
    _tenant_ctx.set(tenant_id)


def get_tenant_context() -> str | None:
    """读取当前上下文的租户 ID。"""
    return _tenant_ctx.get()


def _graph_iri(tenant_id: str) -> str:
    return f"urn:tenant:{tenant_id}"


def _inject_graph_context(sparql: str, tenant_id: str) -> str:
    """将 SPARQL 查询改写为限定在租户 Named Graph 内。

    规则：找到最外层 WHERE { ... }，将其内容包入
    ``GRAPH <urn:tenant:{id}> { ... }``。

    支持 SELECT / CONSTRUCT / ASK / DELETE WHERE。
    INSERT DATA / DELETE DATA 若无 WHERE 子句，直接原样返回
    （调用方应手动构造带 GRAPH 的语句）。
    """
    iri = _graph_iri(tenant_id)
    pattern = re.compile(r"\bWHERE\s*\{", re.IGNORECASE)
    match = pattern.search(sparql)

    if not match:
        # 无 WHERE 子句（如裸 INSERT DATA），原样返回，调用方负责正确构造
        return sparql

    # 找到 WHERE { 的起始位置，向后扫描匹配右括号
    start = match.end()
    depth = 1
    pos = start
    while pos < len(sparql) and depth > 0:
        if sparql[pos] == "{":
            depth += 1
        elif sparql[pos] == "}":
            depth -= 1
        pos += 1

    # pos 现在指向最外层 } 之后一位
    end = pos - 1  # 最外层 } 的位置
    inner = sparql[start:end]
    prefix = sparql[: match.start()]
    suffix = sparql[end + 1 :]

    return f"{prefix}WHERE {{ GRAPH <{iri}> {{{inner}}} }}{suffix}"


async def sparql_query(
    sparql: str,
    tenant_id: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """执行 SPARQL SELECT，自动注入租户 Named Graph 上下文。

    Args:
        sparql: SPARQL SELECT 查询语句
        tenant_id: 显式传入租户 ID；若为 None，从 ContextVar 读取
        client: 可注入 httpx.AsyncClient（测试用）

    Returns:
        绑定结果列表，每项为 {变量名: 值} 字典

    Raises:
        TenantContextMissingError: 未设置租户上下文
    """
    tid = tenant_id or _tenant_ctx.get()
    if not tid:
        raise TenantContextMissingError("未设置租户上下文，拒绝无边界 SPARQL 查询")

    rewritten = _inject_graph_context(sparql, tid)
    base_url = (
        f"{settings.graphdb_url}/repositories/{settings.graphdb_repository}"
    )

    async def _do_query(c: httpx.AsyncClient) -> list[dict]:
        resp = await c.post(
            base_url,
            content=rewritten,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        vars_ = data["results"]["vars"]
        return [
            {v: binding.get(v, {}).get("value") for v in vars_}
            for binding in data["results"]["bindings"]
        ]

    if client is not None:
        return await _do_query(client)

    async with httpx.AsyncClient(
        auth=(settings.graphdb_username, settings.graphdb_password),
        timeout=30.0,
    ) as c:
        return await _do_query(c)


async def sparql_update(
    sparql: str,
    tenant_id: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """执行 SPARQL UPDATE，限定在租户 Named Graph 内。

    Args:
        sparql: SPARQL UPDATE 语句
        tenant_id: 显式传入租户 ID；若为 None，从 ContextVar 读取
        client: 可注入 httpx.AsyncClient（测试用）

    Raises:
        TenantContextMissingError: 未设置租户上下文
    """
    tid = tenant_id or _tenant_ctx.get()
    if not tid:
        raise TenantContextMissingError("未设置租户上下文，拒绝无边界 SPARQL UPDATE")

    rewritten = _inject_graph_context(sparql, tid)
    url = (
        f"{settings.graphdb_url}/repositories/{settings.graphdb_repository}/statements"
    )

    async def _do_update(c: httpx.AsyncClient) -> None:
        resp = await c.post(
            url,
            content=rewritten,
            headers={"Content-Type": "application/sparql-update"},
        )
        resp.raise_for_status()

    if client is not None:
        await _do_update(client)
        return

    async with httpx.AsyncClient(
        auth=(settings.graphdb_username, settings.graphdb_password),
        timeout=30.0,
    ) as c:
        await _do_update(c)
