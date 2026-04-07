"""CSV 元数据解析器：将 CSV 格式的表结构描述转换为 TableInfo 列表。

CSV 表头格式：
  数据库名,表名,表说明,字段名,数据类型,允许空值,默认值,额外信息(如自增),字段说明

每行描述一个字段，同一张表的多个字段通过"表名"列聚合。
"""
from __future__ import annotations

import csv
import io
import logging

from drp.mapping.ddl_parser import ColumnInfo, TableInfo

logger = logging.getLogger(__name__)

# CSV 表头映射（支持中英文表头）
_HEADER_MAP = {
    "数据库名": "db_name",
    "表名": "table_name",
    "表说明": "table_comment",
    "字段名": "column_name",
    "数据类型": "data_type",
    "允许空值": "nullable",
    "默认值": "default_value",
    "额外信息(如自增)": "extra",
    "额外信息": "extra",
    "字段说明": "column_comment",
    # 英文别名
    "database": "db_name",
    "table": "table_name",
    "table_comment": "table_comment",
    "column": "column_name",
    "type": "data_type",
    "nullable": "nullable",
    "default": "default_value",
    "extra": "extra",
    "comment": "column_comment",
}


def _normalize_header(header: str) -> str:
    """规范化表头名称。"""
    h = header.strip().lower()
    return _HEADER_MAP.get(header.strip(), _HEADER_MAP.get(h, h))


def _is_nullable(value: str) -> bool:
    """解析允许空值字段。"""
    v = value.strip().upper()
    if v in ("YES", "Y", "TRUE", "1", "是", "允许"):
        return True
    if v in ("NO", "N", "FALSE", "0", "否", "不允许", "NOT NULL"):
        return False
    return True  # 默认允许空值


def parse_csv(content: str) -> list[TableInfo]:
    """解析 CSV 内容，返回 TableInfo 列表。

    Args:
        content: CSV 文本内容（UTF-8）

    Returns:
        按表名聚合的 TableInfo 列表

    Raises:
        ValueError: CSV 格式不合法时抛出
    """
    # 自动检测分隔符
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(content[:2048])
    except csv.Error:
        dialect = csv.excel  # type: ignore[assignment]

    reader = csv.DictReader(io.StringIO(content), dialect=dialect)

    if not reader.fieldnames:
        raise ValueError("CSV 文件为空或缺少表头")

    # 规范化表头
    normalized_fields = [_normalize_header(f) for f in reader.fieldnames]

    # 校验必需列
    required = {"table_name", "column_name", "data_type"}
    missing = required - set(normalized_fields)
    if missing:
        raise ValueError(f"CSV 缺少必需列：{', '.join(missing)}（需要：表名、字段名、数据类型）")

    # 构建表头索引映射
    field_index = {norm: orig for norm, orig in zip(normalized_fields, reader.fieldnames)}

    tables: dict[str, TableInfo] = {}

    for row_num, row in enumerate(reader, start=2):
        table_name = row.get(field_index.get("table_name", ""), "").strip()
        column_name = row.get(field_index.get("column_name", ""), "").strip()
        data_type = row.get(field_index.get("data_type", ""), "").strip()

        if not table_name or not column_name:
            logger.warning("CSV 第 %d 行缺少表名或字段名，跳过", row_num)
            continue

        if not data_type:
            data_type = "VARCHAR(255)"  # 默认类型

        # 获取或创建表
        table_key = table_name.lower()
        if table_key not in tables:
            table_comment = row.get(field_index.get("table_comment", ""), "").strip()
            tables[table_key] = TableInfo(
                name=table_name,
                comment=table_comment,
            )

        # 解析列信息
        nullable_str = row.get(field_index.get("nullable", ""), "YES").strip()
        default_val = row.get(field_index.get("default_value", ""), "").strip() or None
        col_comment = row.get(field_index.get("column_comment", ""), "").strip()
        extra = row.get(field_index.get("extra", ""), "").strip()

        # 将额外信息追加到注释
        if extra and col_comment:
            col_comment = f"{col_comment}（{extra}）"
        elif extra:
            col_comment = extra

        col = ColumnInfo(
            name=column_name,
            data_type=data_type,
            nullable=_is_nullable(nullable_str),
            comment=col_comment,
            default=default_val,
        )
        tables[table_key].columns.append(col)

    if not tables:
        raise ValueError("CSV 中未找到有效的表定义")

    result = list(tables.values())
    logger.info("CSV 解析完成：%d 张表，%d 个字段",
                len(result), sum(len(t.columns) for t in result))
    return result
