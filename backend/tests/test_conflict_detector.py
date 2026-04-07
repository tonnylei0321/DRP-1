"""规则冲突检测单元测试。

覆盖核心场景：
- 已有 all 规则时新增其他类型 → 返回警告
- 新增 all 规则时已有其他类型 → 返回警告
- 无冲突 → 返回 None
"""

from __future__ import annotations

import pytest

from drp.scope.conflict_detector import detect_conflict


class TestDetectConflict:
    """测试 detect_conflict 函数。"""

    def test_no_existing_rules_no_conflict(self):
        """无已有规则时无冲突。"""
        result = detect_conflict([], "self")
        assert result is None

    def test_no_conflict_same_non_all_types(self):
        """已有 self 规则，新增 dept 规则，无冲突。"""
        existing = [{"scope_type": "self"}]
        result = detect_conflict(existing, "dept")
        assert result is None

    def test_no_conflict_adding_same_type(self):
        """已有 self 规则，新增 self 规则，无冲突。"""
        existing = [{"scope_type": "self"}]
        result = detect_conflict(existing, "self")
        assert result is None

    def test_existing_all_new_self_warns(self):
        """已有 all 规则，新增 self 规则 → 返回警告。"""
        existing = [{"scope_type": "all"}]
        result = detect_conflict(existing, "self")
        assert result is not None
        assert "all" in result
        assert "self" in result

    def test_existing_all_new_dept_warns(self):
        """已有 all 规则，新增 dept 规则 → 返回警告。"""
        existing = [{"scope_type": "all"}]
        result = detect_conflict(existing, "dept")
        assert result is not None
        assert "all" in result
        assert "dept" in result

    def test_existing_all_new_custom_warns(self):
        """已有 all 规则，新增 custom 规则 → 返回警告。"""
        existing = [{"scope_type": "all"}]
        result = detect_conflict(existing, "custom")
        assert result is not None
        assert "all" in result

    def test_new_all_existing_self_warns(self):
        """新增 all 规则，已有 self 规则 → 返回警告。"""
        existing = [{"scope_type": "self"}]
        result = detect_conflict(existing, "all")
        assert result is not None
        assert "all" in result
        assert "self" in result

    def test_new_all_existing_multiple_warns(self):
        """新增 all 规则，已有多种类型规则 → 返回警告。"""
        existing = [
            {"scope_type": "self"},
            {"scope_type": "dept"},
            {"scope_type": "custom"},
        ]
        result = detect_conflict(existing, "all")
        assert result is not None
        assert "all" in result

    def test_existing_all_new_all_no_conflict(self):
        """已有 all 规则，新增 all 规则，无冲突。"""
        existing = [{"scope_type": "all"}]
        result = detect_conflict(existing, "all")
        assert result is None

    def test_empty_scope_type_ignored(self):
        """scope_type 为空的规则被忽略。"""
        existing = [{"scope_type": ""}, {"scope_type": None}]
        result = detect_conflict(existing, "self")
        assert result is None

    def test_mixed_existing_with_all_warns(self):
        """已有 all + self 规则，新增 dept → 返回警告。"""
        existing = [{"scope_type": "all"}, {"scope_type": "self"}]
        result = detect_conflict(existing, "dept")
        assert result is not None
        assert "all" in result
