"""DDL 解析器：支持 MySQL / PostgreSQL / Oracle DDL，提取表/字段/类型/注释。

使用正则解析，无需引入完整 SQL 解析库。
"""
import re
from dataclasses import dataclass, field


@dataclass
class ColumnInfo:
    """单个字段的元数据。"""
    name: str
    data_type: str
    nullable: bool = True
    comment: str = ""
    default: str | None = None


@dataclass
class TableInfo:
    """单张表的元数据。"""
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    comment: str = ""


# 匹配 CREATE TABLE（含或不含 IF NOT EXISTS，支持 schema.table）
_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"`?\"?(\w+)`?\"?\s*\.\s*`?\"?(\w+)`?\"?\s*\(|"
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?\"?(\w+)`?\"?\s*\(",
    re.IGNORECASE,
)

# 匹配 MySQL / PostgreSQL 列级 COMMENT（COMMENT '...' 或 COMMENT ON COLUMN ...）
_INLINE_COMMENT_RE = re.compile(r"COMMENT\s+['\"]([^'\"]*)['\"]", re.IGNORECASE)

# 匹配 NOT NULL
_NOT_NULL_RE = re.compile(r"\bNOT\s+NULL\b", re.IGNORECASE)

# 匹配 DEFAULT 值
_DEFAULT_RE = re.compile(r"\bDEFAULT\s+(\S+)", re.IGNORECASE)

# PostgreSQL/Oracle COMMENT ON TABLE/COLUMN 语句
_EXT_TABLE_COMMENT_RE = re.compile(
    r"COMMENT\s+ON\s+TABLE\s+\S+\s+IS\s+'([^']*)'", re.IGNORECASE
)
_EXT_COL_COMMENT_RE = re.compile(
    r"COMMENT\s+ON\s+COLUMN\s+(\S+)\.(\S+)\s+IS\s+'([^']*)'", re.IGNORECASE
)


def _extract_table_body(ddl: str, start: int) -> str:
    """从 CREATE TABLE ... ( 之后提取括号内的完整内容。"""
    depth = 1
    pos = start
    while pos < len(ddl) and depth > 0:
        if ddl[pos] == "(":
            depth += 1
        elif ddl[pos] == ")":
            depth -= 1
        pos += 1
    return ddl[start : pos - 1]


def _parse_column_line(line: str) -> ColumnInfo | None:
    """解析单行列定义，返回 ColumnInfo 或 None（跳过约束行）。"""
    line = line.strip().rstrip(",")
    if not line:
        return None

    # 跳过约束关键字开头的行
    skip_keywords = ("PRIMARY", "UNIQUE", "KEY", "INDEX", "CONSTRAINT",
                     "FOREIGN", "CHECK", ")", "(")
    if any(line.upper().startswith(k) for k in skip_keywords):
        return None

    # 提取列名（支持反引号/双引号包裹）
    name_match = re.match(r'^`?"?(\w+)`?"?\s+(.+)', line)
    if not name_match:
        return None

    col_name = name_match.group(1)
    rest = name_match.group(2)

    # 提取类型（取到第一个空格或约束关键字）
    type_match = re.match(r"([A-Za-z_]+(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?)", rest)
    data_type = type_match.group(1).strip() if type_match else rest.split()[0]

    nullable = _NOT_NULL_RE.search(rest) is None

    default_m = _DEFAULT_RE.search(rest)
    default = default_m.group(1) if default_m else None

    comment_m = _INLINE_COMMENT_RE.search(rest)
    comment = comment_m.group(1) if comment_m else ""

    return ColumnInfo(
        name=col_name,
        data_type=data_type,
        nullable=nullable,
        comment=comment,
        default=default,
    )


def parse_ddl(ddl: str) -> list[TableInfo]:
    """解析 DDL 字符串，返回所有表的元数据列表。

    支持：
    - MySQL（反引号标识符、COMMENT '...'）
    - PostgreSQL（双引号标识符、COMMENT ON COLUMN ... IS '...'）
    - Oracle（双引号标识符、COMMENT ON TABLE/COLUMN ... IS '...'）
    """
    tables: dict[str, TableInfo] = {}

    # 1. 提取所有 CREATE TABLE 块
    for m in _TABLE_RE.finditer(ddl):
        # 解析表名（支持 schema.table 和普通 table）
        if m.group(1):
            table_name = m.group(2)  # schema.table 格式取第二组
        else:
            table_name = m.group(3)

        body_start = m.end()
        body = _extract_table_body(ddl, body_start)

        table = TableInfo(name=table_name)
        for line in body.splitlines():
            col = _parse_column_line(line)
            if col:
                table.columns.append(col)

        # MySQL 内联 TABLE COMMENT
        suffix = ddl[body_start + len(body):]
        inline_tbl_m = re.search(r"COMMENT\s*=\s*['\"]([^'\"]*)['\"]", suffix[:200], re.IGNORECASE)
        if inline_tbl_m:
            table.comment = inline_tbl_m.group(1)

        tables[table_name.lower()] = table

    # 2. 提取 PostgreSQL/Oracle 外部注释
    for m in _EXT_TABLE_COMMENT_RE.finditer(ddl):
        tname = m.group(1).strip('"').lower()
        if tname in tables:
            tables[tname].comment = m.group(1)  # 原始注释

    for m in _EXT_COL_COMMENT_RE.finditer(ddl):
        tname = m.group(1).strip('"').lower()
        cname = m.group(2).strip('"').lower()
        comment = m.group(3)
        if tname in tables:
            for col in tables[tname].columns:
                if col.name.lower() == cname:
                    col.comment = comment

    return list(tables.values())
