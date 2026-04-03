import httpx

from drp.config import settings


class GraphDBError(Exception):
    """GraphDB 操作失败。"""


class GraphDBClient:
    """GraphDB HTTP 客户端 — 仅负责 Named Graph 生命周期管理。

    使用 SPARQL Update/Query 端点，不依赖 GraphDB 私有 REST API。
    可注入 httpx.AsyncClient 便于测试时用 respx 拦截。
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._injected_client = client
        self._base_url = (
            f"{settings.graphdb_url}/repositories/{settings.graphdb_repository}"
        )
        self._auth = (settings.graphdb_username, settings.graphdb_password)

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(auth=self._auth, timeout=10.0)

    async def _sparql_update(self, sparql: str) -> None:
        """执行 SPARQL Update 语句。"""
        client = self._injected_client or self._make_client()
        should_close = self._injected_client is None
        try:
            resp = await client.post(
                f"{self._base_url}/statements",
                content=sparql,
                headers={"Content-Type": "application/sparql-update"},
            )
        finally:
            if should_close:
                await client.aclose()

        if resp.status_code not in (200, 204):
            raise GraphDBError(
                f"SPARQL Update 失败: {resp.status_code} — {resp.text[:200]}"
            )

    async def _sparql_ask(self, sparql: str) -> bool:
        """执行 SPARQL ASK，返回布尔值。"""
        client = self._injected_client or self._make_client()
        should_close = self._injected_client is None
        try:
            resp = await client.post(
                self._base_url,
                content=sparql,
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json",
                },
            )
        finally:
            if should_close:
                await client.aclose()

        if resp.status_code != 200:
            raise GraphDBError(
                f"SPARQL ASK 失败: {resp.status_code} — {resp.text[:200]}"
            )
        return bool(resp.json()["boolean"])

    async def create_named_graph(self, graph_iri: str) -> None:
        """创建 Named Graph（SILENT：已存在则跳过）。"""
        await self._sparql_update(f"CREATE SILENT GRAPH <{graph_iri}>")

    async def delete_named_graph(self, graph_iri: str) -> None:
        """删除 Named Graph 及其全部三元组（SILENT：不存在则跳过）。"""
        await self._sparql_update(f"DROP SILENT GRAPH <{graph_iri}>")

    async def named_graph_exists(self, graph_iri: str) -> bool:
        """检查 Named Graph 是否存在。"""
        return await self._sparql_ask(f"ASK {{ GRAPH <{graph_iri}> {{}} }}")
