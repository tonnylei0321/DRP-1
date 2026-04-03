"""第5章：DDL 解析器、置信度评分、YAML/RML 生成器单元测试。"""
import pytest

from drp.mapping.confidence import (
    AUTO_APPROVE_THRESHOLD,
    compute_confidence,
    should_auto_approve,
)
from drp.mapping.ddl_parser import parse_ddl
from drp.mapping.rml_compiler import compile_to_rml
from drp.mapping.yaml_generator import generate_mapping_yaml, parse_mapping_yaml

# ─── DDL 解析器 ───────────────────────────────────────────────────────────────

_MYSQL_DDL = """
CREATE TABLE `account` (
    `id` INT NOT NULL,
    `acct_no` VARCHAR(50) NOT NULL COMMENT '账号',
    `balance` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '余额',
    `currency` CHAR(3) NOT NULL COMMENT '币种',
    `status` VARCHAR(20) NULL COMMENT '状态',
    PRIMARY KEY (`id`)
) COMMENT='银行账户表';
"""

_PG_DDL = """
CREATE TABLE "account" (
    id UUID NOT NULL,
    acct_no VARCHAR(50) NOT NULL,
    balance NUMERIC(18,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
COMMENT ON COLUMN "account".acct_no IS '账户编号';
COMMENT ON COLUMN "account".balance IS '账户余额';
"""

_ORACLE_DDL = """
CREATE TABLE ACCOUNT (
    ID NUMBER(19) NOT NULL,
    ACCT_NO VARCHAR2(50) NOT NULL,
    BALANCE NUMBER(18,2),
    CURRENCY CHAR(3)
);
COMMENT ON TABLE ACCOUNT IS '账户信息';
COMMENT ON COLUMN ACCOUNT.ACCT_NO IS '账户号码';
"""


def test_mysql_解析列数():
    tables = parse_ddl(_MYSQL_DDL)
    assert len(tables) == 1
    table = tables[0]
    assert table.name.lower() == "account"
    # 去掉 PRIMARY KEY 约束行，应有 5 列
    assert len(table.columns) == 5


def test_mysql_解析注释():
    tables = parse_ddl(_MYSQL_DDL)
    acct_col = next(c for c in tables[0].columns if c.name == "acct_no")
    assert acct_col.comment == "账号"


def test_mysql_解析类型():
    tables = parse_ddl(_MYSQL_DDL)
    balance_col = next(c for c in tables[0].columns if c.name == "balance")
    assert "DECIMAL" in balance_col.data_type.upper()


def test_pg_解析外部注释():
    tables = parse_ddl(_PG_DDL)
    assert len(tables) == 1
    acct_col = next(c for c in tables[0].columns if c.name == "acct_no")
    assert acct_col.comment == "账户编号"


def test_oracle_解析列():
    tables = parse_ddl(_ORACLE_DDL)
    assert len(tables) == 1
    assert len(tables[0].columns) == 4


def test_多表解析():
    ddl = """
    CREATE TABLE foo (id INT NOT NULL, name VARCHAR(100));
    CREATE TABLE bar (id INT NOT NULL, code VARCHAR(10) NOT NULL);
    """
    tables = parse_ddl(ddl)
    assert len(tables) == 2
    names = {t.name.lower() for t in tables}
    assert names == {"foo", "bar"}


# ─── 置信度评分 ───────────────────────────────────────────────────────────────


def test_高置信度_账户号字段():
    score = compute_confidence(
        field_name="acct_no",
        data_type="VARCHAR",
        comment="银行账户号码",
        target_property="ctio:accountNumber",
    )
    assert score > 20  # 语义 + 注释分


def test_历史精确匹配加分():
    history = [{"source_table": "account", "source_field": "acct_no", "target_property": "ctio:accountNumber"}]
    score_with = compute_confidence("acct_no", "VARCHAR", "", "ctio:accountNumber", "account", history)
    score_without = compute_confidence("acct_no", "VARCHAR", "", "ctio:accountNumber", "account", [])
    assert score_with > score_without


def test_auto_approve_高分():
    assert should_auto_approve(AUTO_APPROVE_THRESHOLD) is True
    assert should_auto_approve(AUTO_APPROVE_THRESHOLD - 1) is False


def test_置信度上限100():
    score = compute_confidence(
        "acct_no", "VARCHAR", "账户号，关���字段", "ctio:accountNumber", "account",
        [{"source_table": "account", "source_field": "acct_no", "target_property": "ctio:accountNumber"}],
    )
    assert score <= 100.0


# ─── YAML 生成与解析 ──────────────────────────────────────────────────────────


def _make_suggestions():
    from drp.mapping.llm_service import MappingSuggestion
    return [
        MappingSuggestion("account", "acct_no", "VARCHAR", "ctio:accountNumber", "", 92.5, True),
        MappingSuggestion("account", "balance", "DECIMAL", "ctio:balance", "", 75.0, False),
    ]


def test_yaml_生成格式正确():
    yaml_str = generate_mapping_yaml(_make_suggestions())
    assert "mappings:" in yaml_str
    assert "acct_no" in yaml_str
    assert "ctio:accountNumber" in yaml_str


def test_yaml_往返解析():
    suggestions = _make_suggestions()
    yaml_str = generate_mapping_yaml(suggestions)
    parsed = parse_mapping_yaml(yaml_str)
    assert len(parsed) == 2
    assert parsed[0]["source_field"] == "acct_no"
    assert parsed[0]["auto_approved"] is True


# ─── RML 编译器 ───────────────────────────────────────────────────────────────


def test_rml_包含前缀():
    mappings = [
        {"source_table": "account", "source_field": "acct_no", "data_type": "VARCHAR",
         "target_property": "ctio:accountNumber", "transform_rule": ""},
    ]
    rml = compile_to_rml(mappings, "account")
    assert "@prefix rr:" in rml
    assert "TriplesMap" in rml


def test_rml_包含字段映射():
    mappings = [
        {"source_table": "account", "source_field": "balance", "data_type": "DECIMAL",
         "target_property": "ctio:balance", "transform_rule": ""},
    ]
    rml = compile_to_rml(mappings, "account")
    assert "ctio:balance" in rml
    assert "rml:reference" in rml
    assert "xsd:decimal" in rml


def test_rml_跳过无目标属性字段():
    mappings = [
        {"source_table": "account", "source_field": "misc", "data_type": "VARCHAR",
         "target_property": None, "transform_rule": ""},
    ]
    rml = compile_to_rml(mappings, "account")
    # 无目标属性的字段不应生成 predicateObjectMap
    assert "misc" not in rml
