"""DDL 生成器往返一致性测试。

Property 1: DDL 解析往返一致性
Property 2: INSERT 与 DDL 列一致性
Property 3: 表 COMMENT 完整性
"""
import sys
import os
import re

# 将 scripts 目录加入 path 以便导入 generate_test_data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from generate_test_data import DOMAIN_TABLES, TestDataFactory, ENTITY_HIERARCHY, TABLE_ROW_COUNTS, generate_ddl, generate_insert
from drp.mapping.ddl_parser import parse_ddl


class TestDdlRoundtrip:
    """Property 1: DDL 解析往返一致性"""
    # Feature: e2e-test-data-pipeline, Property 1: DDL 解析往返一致性

    def test_all_tables_parseable(self):
        """所有生成的 DDL 都能被 DDL_Parser 成功解析"""
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                ddl = generate_ddl(table_def)
                parsed = parse_ddl(ddl)
                assert len(parsed) >= 1, f"表 {table_def.name} 解析失败"
                assert parsed[0].name == table_def.name, f"表名不一致: {parsed[0].name} != {table_def.name}"

    def test_column_names_match(self):
        """解析后的列名与生成时一致"""
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                ddl = generate_ddl(table_def)
                parsed = parse_ddl(ddl)
                assert len(parsed) >= 1
                parsed_col_names = {c.name.lower() for c in parsed[0].columns}
                expected_col_names = {c.name.lower() for c in table_def.columns}
                assert parsed_col_names == expected_col_names, \
                    f"表 {table_def.name} 列名不一致: 多出 {parsed_col_names - expected_col_names}, 缺少 {expected_col_names - parsed_col_names}"

    def test_column_comments_match(self):
        """解析后的列注释与生成时一致"""
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                ddl = generate_ddl(table_def)
                parsed = parse_ddl(ddl)
                assert len(parsed) >= 1
                parsed_comments = {c.name.lower(): c.comment for c in parsed[0].columns if c.comment}
                for col in table_def.columns:
                    if col.comment:
                        assert col.name.lower() in parsed_comments, \
                            f"表 {table_def.name} 列 {col.name} 注释丢失"
                        assert parsed_comments[col.name.lower()] == col.comment, \
                            f"表 {table_def.name} 列 {col.name} 注释不一致"


class TestInsertDdlConsistency:
    """Property 2: INSERT 与 DDL 列一致性"""
    # Feature: e2e-test-data-pipeline, Property 2: 生成器 INSERT 与 DDL 列一致性

    def test_insert_columns_match_ddl(self):
        """INSERT 列名集合与 CREATE TABLE 列名集合完全一致"""
        factory = TestDataFactory(ENTITY_HIERARCHY)
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                count = TABLE_ROW_COUNTS.get(table_def.name, 5)
                rows = factory.generate(table_def, min(count, 3))  # 只生成少量数据验证
                if not rows:
                    continue
                insert_sql = generate_insert(table_def, rows)
                # 提取 INSERT INTO ... (...) 中的列名
                match = re.search(r'INSERT INTO \w+ \(([^)]+)\)', insert_sql)
                assert match, f"表 {table_def.name} INSERT 语句格式错误"
                insert_cols = {c.strip().lower() for c in match.group(1).split(',')}
                ddl_cols = {c.name.lower() for c in table_def.columns}
                assert insert_cols == ddl_cols, \
                    f"表 {table_def.name} INSERT 列与 DDL 列不一致"

    def test_insert_value_count_matches_columns(self):
        """INSERT 值数量等于列数"""
        factory = TestDataFactory(ENTITY_HIERARCHY)
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                count = TABLE_ROW_COUNTS.get(table_def.name, 5)
                rows = factory.generate(table_def, min(count, 3))
                if not rows:
                    continue
                for row in rows:
                    assert len(row) == len(table_def.columns), \
                        f"表 {table_def.name} 行数据列数 {len(row)} != DDL 列数 {len(table_def.columns)}"


class TestCommentCompleteness:
    """Property 3: 表 COMMENT 完整性"""
    # Feature: e2e-test-data-pipeline, Property 3: 生成表 COMMENT 完整性

    def test_all_tables_have_comment(self):
        """每张表都有表级 COMMENT"""
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                assert table_def.comment, f"表 {table_def.name} 缺少表级 COMMENT"

    def test_all_columns_have_comment(self):
        """每列都有非空列级 COMMENT"""
        for domain_key, tables in DOMAIN_TABLES.items():
            for table_def in tables:
                for col in table_def.columns:
                    assert col.comment, f"表 {table_def.name} 列 {col.name} 缺少 COMMENT"
