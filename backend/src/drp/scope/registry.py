"""业务表注册表：自动发现标记了 __data_scope__ = True 的 SQLAlchemy 模型。

提供表名校验、列名校验、supports_self 检查等接口，
供 Scope_Admin_API 和 Data_Scope_Interceptor 使用。
"""

from __future__ import annotations

import logging
from typing import TypedDict

from drp.db.base import Base

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 类型定义
# ---------------------------------------------------------------------------


class TableMeta(TypedDict):
    table_name: str
    columns: dict[str, str]  # column_name -> data_type
    supports_self: bool  # 是否包含 created_by 列


# ---------------------------------------------------------------------------
# 模块级注册表（应用启动时由 build_registry() 填充）
# ---------------------------------------------------------------------------

_registry: dict[str, TableMeta] = {}


# ---------------------------------------------------------------------------
# 构建注册表
# ---------------------------------------------------------------------------


def build_registry() -> dict[str, TableMeta]:
    """扫描所有继承自 Base 的 SQLAlchemy 模型，注册标记了 __data_scope__ = True 的模型。

    返回构建好的注册表字典，同时更新模块级变量 _registry。
    """
    global _registry
    registry: dict[str, TableMeta] = {}

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if not getattr(cls, "__data_scope__", False):
            continue

        table = mapper.local_table
        table_name = table.name

        columns: dict[str, str] = {}
        for col in table.columns:
            columns[col.name] = str(col.type)

        supports_self = "created_by" in columns

        registry[table_name] = TableMeta(
            table_name=table_name,
            columns=columns,
            supports_self=supports_self,
        )
        logger.info(
            "注册业务表: %s (列数=%d, supports_self=%s)",
            table_name,
            len(columns),
            supports_self,
        )

    _registry = registry
    logger.info("业务表注册表构建完成，共 %d 张表", len(_registry))
    return _registry


# ---------------------------------------------------------------------------
# 公开查询接口
# ---------------------------------------------------------------------------


def get_registry() -> dict[str, TableMeta]:
    """返回所有已注册业务表的元数据。"""
    return _registry


def is_table_registered(table_name: str) -> bool:
    """检查表是否在注册表中。"""
    return table_name in _registry


def is_column_valid(table_name: str, column_name: str) -> bool:
    """检查列是否存在于指定表中。

    如果表未注册，返回 False。
    """
    meta = _registry.get(table_name)
    if meta is None:
        return False
    return column_name in meta["columns"]
