"""数据清洗模块：NULL 处理、枚举归一化、编码转换。"""
import re
from typing import Any


# 常见枚举归一化映射（可按业务扩展）
_STATUS_NORM: dict[str, str] = {
    # 启用/禁用类
    "1": "active", "0": "inactive",
    "y": "active", "n": "inactive",
    "yes": "active", "no": "inactive",
    "true": "active", "false": "inactive",
    "enable": "active", "disable": "inactive",
    "enabled": "active", "disabled": "inactive",
    "open": "active", "close": "inactive",
    "正常": "active", "注销": "inactive", "冻结": "frozen",
    # 货币状态
    "restricted": "restricted", "限制": "restricted",
    "unrestricted": "unrestricted", "正常户": "unrestricted",
}

# 常见编码问题修复
_MOJIBAKE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"Ã©"), "é"),
    (re.compile(r"â€™"), "'"),
]


def clean_null(value: Any, default: Any = None) -> Any:
    """将空字符串、'NULL'、'null'、'None' 等统一转为 None（或指定默认值）。"""
    if value is None:
        return default
    if isinstance(value, str) and value.strip().upper() in ("NULL", "NONE", "N/A", "NA", ""):
        return default
    return value


def normalize_enum(value: str | None, mapping: dict[str, str] | None = None) -> str | None:
    """归一化枚举值为标准英文小写。

    Args:
        value: 原始值
        mapping: 自定义映射（覆盖默认映射）
    """
    if value is None:
        return None
    norm_map = {**_STATUS_NORM, **(mapping or {})}
    key = str(value).strip().lower()
    return norm_map.get(key, key)


def fix_encoding(value: str) -> str:
    """修复常见的字符编码乱码（Mojibake）。"""
    for pattern, replacement in _MOJIBAKE_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def clean_amount(value: Any) -> float | None:
    """清洗金额字段：去掉千位分隔符、货币符号，转为 float。"""
    if value is None:
        return None
    s = str(value).strip().replace(",", "").replace("¥", "").replace("$", "").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def clean_row(
    row: dict[str, Any],
    null_fields: list[str] | None = None,
    enum_fields: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """对一行数据进行完整清洗流程。

    Args:
        row: 原始数据行
        null_fields: 需要 NULL 归一化的字段名列表（留空则全量处理）
        enum_fields: {字段名: 枚举映射} 字典

    Returns:
        清洗后的数据行（不修改原始 dict）
    """
    result = {}
    for key, value in row.items():
        # NULL 处理
        if null_fields is None or key in (null_fields or []):
            value = clean_null(value)

        # 枚举归一化
        if enum_fields and key in enum_fields and isinstance(value, str):
            value = normalize_enum(value, enum_fields[key])

        # 编码修复
        if isinstance(value, str):
            value = fix_encoding(value)

        result[key] = value
    return result
