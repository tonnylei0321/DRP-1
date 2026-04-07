"""规则冲突检测：检测 all 类型规则与其他类型规则的冲突。

核心接口：
- detect_conflict(existing_rules, new_scope_type) → str | None
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def detect_conflict(
    existing_rules: list[dict],
    new_scope_type: str,
) -> str | None:
    """检测新增规则与已有规则的冲突。

    冲突场景：
    1. 已有 all 规则时新增其他类型 → 返回警告
    2. 新增 all 规则时已有其他类型 → 返回警告
    3. 无冲突 → 返回 None

    Args:
        existing_rules: 已有规则列表，每个元素包含 scope_type 字段
        new_scope_type: 新增规则的 scope_type

    Returns:
        警告信息字符串，或 None 表示无冲突
    """
    existing_types = {r.get("scope_type") for r in existing_rules if r.get("scope_type")}

    # 场景 1：已有 all 规则，新增其他类型
    if "all" in existing_types and new_scope_type != "all":
        return (
            f"已存在 all 类型规则（全部数据可见），新增 {new_scope_type} 类型规则后，"
            f"OR 合并结果仍等价于 all（全部数据可见），新规则实际不会产生额外限制效果。"
        )

    # 场景 2：新增 all 规则，已有其他类型
    if new_scope_type == "all" and existing_types - {"all"}:
        other_types = sorted(existing_types - {"all"})
        return (
            f"新增 all 类型规则（全部数据可见），已有 {', '.join(other_types)} 类型规则，"
            f"OR 合并后等价于 all（全部数据可见），已有规则将不再产生限制效果。"
        )

    return None
