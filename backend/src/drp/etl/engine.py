"""ETL 同步引擎：全量/增量同步，含指数退避重试。

实际运行时由 Celery task 调用，可独立测试核心逻辑。
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from drp.etl.cleaner import clean_row
from drp.etl.hash_diff import build_snapshot, diff_rows
from drp.mapping.rml_compiler import compile_to_rml
from drp.mapping.yaml_generator import parse_mapping_yaml

logger = logging.getLogger(__name__)

# 最大重试 3 次，指数退避 2^n 秒（4s、8s、16s）
_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    reraise=True,
)


class EtlSyncEngine:
    """ETL 同步引擎：将源库数据通过 RML 映射写入 GraphDB Named Graph。

    设计为无状态，依赖注入所有外部资源（便于测试 mock）。
    """

    def __init__(
        self,
        *,
        source_fetcher,
        graphdb_client,
        mapping_yaml: str,
        tenant_id: str,
    ) -> None:
        """
        Args:
            source_fetcher: 可调��对象，签名 (table, watermark?) -> list[dict]
            graphdb_client: GraphDBClient 实例
            mapping_yaml: MappingSpec YAML 内容
            tenant_id: 租户 UUID 字符串
        """
        self._fetch = source_fetcher
        self._graphdb = graphdb_client
        self._mappings = parse_mapping_yaml(mapping_yaml)
        self._tenant_id = tenant_id
        self._graph_iri = f"urn:tenant:{tenant_id}"

    @_RETRY_DECORATOR
    async def full_sync(self, table: str) -> int:
        """全量同步：读源库全量 → RML 转换 → 写 Named Graph。

        Returns:
            写入的三元组数量（估算）
        """
        logger.info("[全量同步] 租户=%s 表=%s 开始", self._tenant_id, table)
        rows = await self._fetch(table)
        rows = [clean_row(row) for row in rows]
        triples = await self._write_to_graphdb(table, rows)
        logger.info("[全量同步] 租户=%s 表=%s 完成，三元组=%d", self._tenant_id, table, triples)
        return triples

    @_RETRY_DECORATOR
    async def incremental_sync(self, table: str, watermark: datetime | None) -> tuple[int, datetime]:
        """增量同步：基于 updated_at 水位线，只同步变更数据。

        Returns:
            (写入三元组数, 新水位线)
        """
        logger.info("[增量同步] 租户=%s 表=%s 水位线=%s", self._tenant_id, table, watermark)
        rows = await self._fetch(table, watermark)
        rows = [clean_row(row) for row in rows]
        triples = await self._write_to_graphdb(table, rows)
        new_watermark = datetime.now(timezone.utc)
        logger.info("[增量同步] 租户=%s 表=%s 三元组=%d", self._tenant_id, table, triples)
        return triples, new_watermark

    @_RETRY_DECORATOR
    async def hash_diff_sync(
        self,
        table: str,
        pk_fields: list[str],
        snapshot: dict[str, str],
    ) -> tuple[int, dict[str, str]]:
        """无时间戳表的哈希比对同步。

        Returns:
            (写入三元组数, 新快照)
        """
        logger.info("[哈希同步] 租户=%s 表=%s", self._tenant_id, table)
        all_rows = await self._fetch(table)
        all_rows = [clean_row(row) for row in all_rows]

        upserts, _, deleted_keys = diff_rows(all_rows, snapshot, pk_fields)

        triples = 0
        if upserts:
            triples = await self._write_to_graphdb(table, upserts)

        # 删除已消失��记录（SPARQL DELETE）
        if deleted_keys:
            await self._delete_by_keys(table, pk_fields, deleted_keys)

        new_snapshot = build_snapshot(all_rows, pk_fields)
        logger.info("[哈希同步] 租户=%s 表=%s upsert=%d delete=%d", self._tenant_id, table, len(upserts), len(deleted_keys))
        return triples, new_snapshot

    async def _write_to_graphdb(self, table: str, rows: list[dict[str, Any]]) -> int:
        """将行数据通过 RML 映射生成 SPARQL INSERT，写入 Named Graph。"""
        if not rows:
            return 0

        # 筛选当前表的映射
        table_mappings = [m for m in self._mappings if m.get("source_table") == table and m.get("target_property")]

        if not table_mappings:
            logger.warning("表 %s 无有效映射，跳过写入", table)
            return 0

        triple_count = 0
        for row in rows:
            triples = self._row_to_triples(row, table, table_mappings)
            if triples:
                sparql = self._build_insert_sparql(triples)
                await self._graphdb._sparql_update(
                    f"INSERT DATA {{ GRAPH <{self._graph_iri}> {{ {sparql} }} }}"
                )
                triple_count += len(triples)

        return triple_count

    @staticmethod
    def _row_to_triples(
        row: dict[str, Any], table: str, mappings: list[dict]
    ) -> list[tuple[str, str, str]]:
        """将一行数据转换为 (subject, predicate, object) 三元组列表。"""
        # 确定主键（取第一个映射字段作为 ID 来源）
        pk_val = row.get("id") or row.get("ID") or next(iter(row.values()), "unknown")
        subject = f"urn:entity:{table}:{pk_val}"
        triples = []

        for m in mappings:
            field = m["source_field"]
            target = m["target_property"]
            val = row.get(field)
            if val is None:
                continue
            # 简单类型序列化
            if isinstance(val, str):
                triples.append((subject, target, f'"{val}"'))
            elif isinstance(val, (int, float)):
                triples.append((subject, target, str(val)))
            elif isinstance(val, datetime):
                triples.append((subject, target, f'"{val.isoformat()}"^^xsd:dateTime'))
            else:
                triples.append((subject, target, f'"{val}"'))

        return triples

    @staticmethod
    def _build_insert_sparql(triples: list[tuple[str, str, str]]) -> str:
        parts = []
        for s, p, o in triples:
            parts.append(f"<{s}> {p} {o} .")
        return " ".join(parts)

    async def _delete_by_keys(
        self, table: str, pk_fields: list[str], deleted_keys: list[str]
    ) -> None:
        """删除已消失记录的三元组。"""
        for pk_key in deleted_keys:
            subject = f"urn:entity:{table}:{pk_key}"
            sparql = f"""
                DELETE {{ GRAPH <{self._graph_iri}> {{ <{subject}> ?p ?o }} }}
                WHERE  {{ GRAPH <{self._graph_iri}> {{ <{subject}> ?p ?o }} }}
            """
            await self._graphdb._sparql_update(sparql)
