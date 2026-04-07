"""表达式解析器单元测试。

覆盖：简单条件、复合条件、IN、BETWEEN、LIKE、NOT、
超长输入拒绝、SQL 注入拒绝、非白名单列名拒绝、函数调用拒绝、空输入拒绝、NULL 值处理。
"""

import pytest

from drp.scope.expr_parser import MAX_CONDITION_LENGTH, ParseResult, parse_condition

# 测试用白名单列
ALLOWED = ["region", "amount", "status", "name", "dept_id", "created_by", "age", "price"]


# ---------------------------------------------------------------------------
# 简单条件
# ---------------------------------------------------------------------------

class TestSimpleCondition:
    def test_string_equal(self):
        result = parse_condition("region = 'Beijing'", ALLOWED)
        assert result.sql_fragment == "region = :p0"
        assert result.bind_params == {"p0": "Beijing"}
        assert result.referenced_columns == ["region"]

    def test_number_greater_than(self):
        result = parse_condition("amount > 1000", ALLOWED)
        assert result.sql_fragment == "amount > :p0"
        assert result.bind_params == {"p0": 1000}
        assert result.referenced_columns == ["amount"]

    def test_float_comparison(self):
        result = parse_condition("price >= 99.5", ALLOWED)
        assert result.sql_fragment == "price >= :p0"
        assert result.bind_params == {"p0": 99.5}

    def test_not_equal(self):
        result = parse_condition("status != 'deleted'", ALLOWED)
        assert result.sql_fragment == "status != :p0"
        assert result.bind_params == {"p0": "deleted"}

    def test_less_than(self):
        result = parse_condition("age < 30", ALLOWED)
        assert result.sql_fragment == "age < :p0"
        assert result.bind_params == {"p0": 30}

    def test_less_equal(self):
        result = parse_condition("age <= 30", ALLOWED)
        assert result.sql_fragment == "age <= :p0"
        assert result.bind_params == {"p0": 30}


# ---------------------------------------------------------------------------
# 复合条件（AND / OR）
# ---------------------------------------------------------------------------

class TestCompoundCondition:
    def test_and(self):
        result = parse_condition("region = 'Beijing' AND amount > 1000", ALLOWED)
        assert result.sql_fragment == "(region = :p0 AND amount > :p1)"
        assert result.bind_params == {"p0": "Beijing", "p1": 1000}
        assert set(result.referenced_columns) == {"region", "amount"}

    def test_or(self):
        result = parse_condition("region = 'Beijing' OR region = 'Shanghai'", ALLOWED)
        assert result.sql_fragment == "(region = :p0 OR region = :p1)"
        assert result.bind_params == {"p0": "Beijing", "p1": "Shanghai"}

    def test_and_or_combined(self):
        result = parse_condition(
            "region = 'Beijing' AND amount > 1000 OR status = 'active'", ALLOWED
        )
        # OR 优先级低于 AND
        assert "OR" in result.sql_fragment
        assert "AND" in result.sql_fragment
        assert len(result.bind_params) == 3

    def test_multiple_and(self):
        result = parse_condition(
            "region = 'Beijing' AND amount > 100 AND status = 'active'", ALLOWED
        )
        assert result.sql_fragment == "(region = :p0 AND amount > :p1 AND status = :p2)"


# ---------------------------------------------------------------------------
# IN 条件
# ---------------------------------------------------------------------------

class TestInCondition:
    def test_in_strings(self):
        result = parse_condition("status IN ('active', 'pending')", ALLOWED)
        assert result.sql_fragment == "status IN (:p0, :p1)"
        assert result.bind_params == {"p0": "active", "p1": "pending"}

    def test_in_numbers(self):
        result = parse_condition("dept_id IN (1, 2, 3)", ALLOWED)
        assert result.sql_fragment == "dept_id IN (:p0, :p1, :p2)"
        assert result.bind_params == {"p0": 1, "p1": 2, "p2": 3}

    def test_in_single_value(self):
        result = parse_condition("status IN ('active')", ALLOWED)
        assert result.sql_fragment == "status IN (:p0)"
        assert result.bind_params == {"p0": "active"}


# ---------------------------------------------------------------------------
# BETWEEN 条件
# ---------------------------------------------------------------------------

class TestBetweenCondition:
    def test_between_numbers(self):
        result = parse_condition("amount BETWEEN 100 AND 500", ALLOWED)
        assert result.sql_fragment == "amount BETWEEN :p0 AND :p1"
        assert result.bind_params == {"p0": 100, "p1": 500}

    def test_between_strings(self):
        result = parse_condition("name BETWEEN 'A' AND 'Z'", ALLOWED)
        assert result.sql_fragment == "name BETWEEN :p0 AND :p1"
        assert result.bind_params == {"p0": "A", "p1": "Z"}


# ---------------------------------------------------------------------------
# LIKE 条件
# ---------------------------------------------------------------------------

class TestLikeCondition:
    def test_like_prefix(self):
        result = parse_condition("name LIKE 'test%'", ALLOWED)
        assert result.sql_fragment == "name LIKE :p0"
        assert result.bind_params == {"p0": "test%"}

    def test_like_suffix(self):
        result = parse_condition("name LIKE '%test'", ALLOWED)
        assert result.sql_fragment == "name LIKE :p0"
        assert result.bind_params == {"p0": "%test"}


# ---------------------------------------------------------------------------
# NOT 条件
# ---------------------------------------------------------------------------

class TestNotCondition:
    def test_not_simple(self):
        result = parse_condition("NOT region = 'Beijing'", ALLOWED)
        assert result.sql_fragment == "NOT (region = :p0)"
        assert result.bind_params == {"p0": "Beijing"}

    def test_not_compound(self):
        result = parse_condition("NOT (region = 'Beijing' AND amount > 100)", ALLOWED)
        assert "NOT" in result.sql_fragment
        assert len(result.bind_params) == 2


# ---------------------------------------------------------------------------
# NULL 值处理
# ---------------------------------------------------------------------------

class TestNullHandling:
    def test_equal_null(self):
        result = parse_condition("dept_id = NULL", ALLOWED)
        assert result.sql_fragment == "dept_id IS NULL"
        assert result.bind_params == {}

    def test_not_equal_null(self):
        result = parse_condition("dept_id != NULL", ALLOWED)
        assert result.sql_fragment == "dept_id IS NOT NULL"
        assert result.bind_params == {}


# ---------------------------------------------------------------------------
# 括号分组
# ---------------------------------------------------------------------------

class TestParentheses:
    def test_grouped_or(self):
        result = parse_condition(
            "(region = 'Beijing' OR region = 'Shanghai') AND amount > 100", ALLOWED
        )
        assert "OR" in result.sql_fragment
        assert "AND" in result.sql_fragment
        assert len(result.bind_params) == 3


# ---------------------------------------------------------------------------
# 错误处理：超长输入
# ---------------------------------------------------------------------------

class TestOverlength:
    def test_overlength_rejected(self):
        long_expr = "region = '" + "x" * 500 + "'"
        assert len(long_expr) > MAX_CONDITION_LENGTH
        with pytest.raises(ValueError, match="超过最大长度限制"):
            parse_condition(long_expr, ALLOWED)

    def test_exact_limit_accepted(self):
        # 构造一个恰好 500 字符的合法表达式
        # "region = 'xxx...'" 其中 xxx 填充到 500 字符
        prefix = "region = '"
        suffix = "'"
        padding = "a" * (MAX_CONDITION_LENGTH - len(prefix) - len(suffix))
        expr = prefix + padding + suffix
        assert len(expr) == MAX_CONDITION_LENGTH
        result = parse_condition(expr, ALLOWED)
        assert result.bind_params["p0"] == padding


# ---------------------------------------------------------------------------
# 错误处理：SQL 注入拒绝
# ---------------------------------------------------------------------------

class TestSQLInjection:
    def test_select_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("region = 'a' AND SELECT 1", ALLOWED)

    def test_drop_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("DROP TABLE users", ALLOWED)

    def test_union_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("region = 'a' UNION SELECT 1", ALLOWED)

    def test_semicolon_rejected(self):
        with pytest.raises(ValueError, match="禁止包含"):
            parse_condition("region = 'a'; DROP TABLE users", ALLOWED)

    def test_comment_dash_rejected(self):
        with pytest.raises(ValueError, match="禁止包含"):
            parse_condition("region = 'a' -- comment", ALLOWED)

    def test_comment_block_rejected(self):
        with pytest.raises(ValueError, match="禁止包含"):
            parse_condition("region = 'a' /* comment */", ALLOWED)

    def test_insert_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("INSERT INTO users VALUES (1)", ALLOWED)

    def test_update_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("UPDATE users SET name = 'x'", ALLOWED)

    def test_delete_rejected(self):
        with pytest.raises(ValueError, match="禁止使用 SQL 关键字"):
            parse_condition("DELETE FROM users", ALLOWED)


# ---------------------------------------------------------------------------
# 错误处理：非白名单列名
# ---------------------------------------------------------------------------

class TestColumnWhitelist:
    def test_unknown_column_rejected(self):
        with pytest.raises(ValueError, match="列 secret_col 不存在于目标业务表"):
            parse_condition("secret_col = 'value'", ALLOWED)

    def test_case_insensitive_column(self):
        # 列名大小写不敏感匹配
        result = parse_condition("Region = 'Beijing'", ALLOWED)
        assert result.sql_fragment == "Region = :p0"


# ---------------------------------------------------------------------------
# 错误处理：函数调用拒绝
# ---------------------------------------------------------------------------

class TestFunctionCallRejection:
    def test_upper_function(self):
        with pytest.raises(ValueError, match="禁止函数调用"):
            parse_condition("UPPER(name) = 'TEST'", ["name"])

    def test_concat_function(self):
        with pytest.raises(ValueError, match="禁止函数调用"):
            parse_condition("CONCAT(name, region) = 'test'", ["name", "region"])


# ---------------------------------------------------------------------------
# 错误处理：空输入
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_string(self):
        with pytest.raises(ValueError, match="表达式不能为空"):
            parse_condition("", ALLOWED)

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="表达式不能为空"):
            parse_condition("   ", ALLOWED)

    def test_none_like_empty(self):
        with pytest.raises(ValueError):
            parse_condition("", ALLOWED)


# ---------------------------------------------------------------------------
# Unicode NFC 规范化
# ---------------------------------------------------------------------------

class TestUnicodeNormalization:
    def test_nfc_normalized(self):
        """确保 Unicode 组合字符经 NFC 规范化后正确处理。"""
        # 使用 NFC 和 NFD 形式的同一字符串
        # é 的 NFC 形式是 \u00e9，NFD 形式是 e + \u0301
        nfd_expr = "region = 'caf\u0065\u0301'"  # NFD
        result = parse_condition(nfd_expr, ALLOWED)
        assert result.bind_params["p0"] == "caf\u00e9"  # NFC


# ---------------------------------------------------------------------------
# 绑定参数安全性
# ---------------------------------------------------------------------------

class TestBindParamSafety:
    def test_no_literal_in_sql(self):
        """确保 SQL 片段中不包含用户提供的字面量值。"""
        result = parse_condition("region = 'Beijing' AND amount > 1000", ALLOWED)
        assert "Beijing" not in result.sql_fragment
        assert "1000" not in result.sql_fragment
        # 只有绑定参数占位符
        assert ":p0" in result.sql_fragment
        assert ":p1" in result.sql_fragment

    def test_string_with_special_chars(self):
        """字符串中的特殊字符作为绑定参数传递，不出现在 SQL 中。"""
        result = parse_condition("name = 'O''Brien'", ALLOWED)
        assert "O'Brien" not in result.sql_fragment
        assert result.bind_params["p0"] == "O'Brien"
