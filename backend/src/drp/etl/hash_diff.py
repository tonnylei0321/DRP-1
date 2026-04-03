"""无时间戳表的主键哈希比对模式。

通过对行数据做哈希，检测变更而不依赖 updated_at 字段。
"""
import hashlib
import json
from typing import Any


def row_hash(row: dict[str, Any], pk_fields: list[str], value_fields: list[str] | None = None) -> tuple[str, str]:
    """计算行的主键标识和值哈希。

    Args:
        row: 数据行
        pk_fields: 主键字段列表
        value_fields: 参与哈希的值字段（None 表示全部非主键字段）

    Returns:
        (pk_key, value_hash) 元组
    """
    pk_key = "|".join(str(row.get(f, "")) for f in pk_fields)

    if value_fields is None:
        value_fields = [k for k in sorted(row.keys()) if k not in pk_fields]

    value_data = {f: row.get(f) for f in value_fields}
    value_str = json.dumps(value_data, sort_keys=True, default=str)
    value_hash = hashlib.sha256(value_str.encode()).hexdigest()

    return pk_key, value_hash


def diff_rows(
    source_rows: list[dict[str, Any]],
    snapshot: dict[str, str],
    pk_fields: list[str],
    value_fields: list[str] | None = None,
) -> tuple[list[dict], list[dict], list[str]]:
    """与快照比对，返回新增/变更/删除的行。

    Args:
        source_rows: 当前源库全量数据
        snapshot: {pk_key: value_hash} 上次快照
        pk_fields: 主键字段
        value_fields: 参与比对的值字段

    Returns:
        (upserts, unchanged, deleted_keys)
        - upserts: 需要写入 GraphDB 的行（新增或变更）
        - unchanged: 无变化的行
        - deleted_keys: 已从源库消失的 pk_key
    """
    upserts: list[dict] = []
    unchanged: list[dict] = []
    current_keys: set[str] = set()

    for row in source_rows:
        pk_key, value_hash = row_hash(row, pk_fields, value_fields)
        current_keys.add(pk_key)

        if pk_key not in snapshot:
            # 新增
            upserts.append(row)
        elif snapshot[pk_key] != value_hash:
            # 变更
            upserts.append(row)
        else:
            unchanged.append(row)

    deleted_keys = [k for k in snapshot if k not in current_keys]
    return upserts, unchanged, deleted_keys


def build_snapshot(
    rows: list[dict[str, Any]],
    pk_fields: list[str],
    value_fields: list[str] | None = None,
) -> dict[str, str]:
    """从数据行构建快照字典 {pk_key: value_hash}。"""
    return {
        pk_key: value_hash
        for row in rows
        for pk_key, value_hash in [row_hash(row, pk_fields, value_fields)]
    }
