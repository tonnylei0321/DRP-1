"""严格白名单 AST 表达式解析器：解析 custom_condition 表达式，生成参数化 SQL 片段。

安全约束：
- 输入最大长度 500 字符
- Unicode NFC 规范化预处理
- 仅允许 4 种 AST 节点：ColumnRef / Literal / CompareExpr / LogicalExpr
- 允许的比较运算符：= != > < >= <= IN BETWEEN LIKE
- 禁止子查询、函数调用、SQL 关键字注入
- 所有用户字面量值作为绑定参数输出
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

MAX_CONDITION_LENGTH = 500

# SQL 注入黑名单关键字（大写匹配）
_FORBIDDEN_KEYWORDS: set[str] = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION",
    "ALTER", "CREATE", "EXEC", "EXECUTE", "TRUNCATE", "MERGE",
    "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "SAVEPOINT",
}

# 允许的比较运算符
_COMPARE_OPS: set[str] = {"=", "!=", ">", "<", ">=", "<=", "IN", "BETWEEN", "LIKE"}

# 允许的逻辑关键字
_LOGIC_KEYWORDS: set[str] = {"AND", "OR", "NOT"}

# 禁止的字符序列
_FORBIDDEN_SEQUENCES: list[str] = [";", "--", "/*", "*/"]


# ---------------------------------------------------------------------------
# Token 类型
# ---------------------------------------------------------------------------

class TokenType(Enum):
    COLUMN_REF = "COLUMN_REF"
    STRING_LIT = "STRING_LIT"
    NUMBER_LIT = "NUMBER_LIT"
    NULL_LIT = "NULL_LIT"
    OPERATOR = "OPERATOR"
    KEYWORD = "KEYWORD"       # AND / OR / NOT
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int


# ---------------------------------------------------------------------------
# AST 节点
# ---------------------------------------------------------------------------

@dataclass
class ColumnRef:
    name: str


@dataclass
class Literal:
    value: Any  # str / int / float / None


@dataclass
class CompareExpr:
    column: ColumnRef
    op: str
    value: Any  # Literal / list[Literal]（IN）/ tuple[Literal, Literal]（BETWEEN）


@dataclass
class LogicalExpr:
    op: str  # AND / OR / NOT
    children: list  # CompareExpr / LogicalExpr


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    sql_fragment: str
    bind_params: dict[str, Any]
    referenced_columns: list[str]


# ---------------------------------------------------------------------------
# 词法分析器
# ---------------------------------------------------------------------------

# 标识符：字母/下划线开头，后跟字母/数字/下划线
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# 数字：整数或浮点
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


class Lexer:
    """将表达式字符串转换为 Token 流。"""

    def __init__(self, expr: str) -> None:
        self._expr = expr
        self._pos = 0
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while self._pos < len(self._expr):
            ch = self._expr[self._pos]

            # 跳过空白
            if ch.isspace():
                self._pos += 1
                continue

            # 单引号字符串
            if ch == "'":
                self._read_string()
                continue

            # 括号和逗号
            if ch == "(":
                self._tokens.append(Token(TokenType.LPAREN, "(", self._pos))
                self._pos += 1
                continue
            if ch == ")":
                self._tokens.append(Token(TokenType.RPAREN, ")", self._pos))
                self._pos += 1
                continue
            if ch == ",":
                self._tokens.append(Token(TokenType.COMMA, ",", self._pos))
                self._pos += 1
                continue

            # 双字符运算符
            two = self._expr[self._pos: self._pos + 2]
            if two in ("!=", ">=", "<="):
                self._tokens.append(Token(TokenType.OPERATOR, two, self._pos))
                self._pos += 2
                continue

            # 单字符运算符
            if ch in ("=", ">", "<"):
                self._tokens.append(Token(TokenType.OPERATOR, ch, self._pos))
                self._pos += 1
                continue

            # 数字（含负数，但负号前面不能是标识符/数字/右括号）
            if ch.isdigit() or (ch == "-" and self._peek_is_number()):
                self._read_number()
                continue

            # 标识符 / 关键字
            m = _IDENT_RE.match(self._expr, self._pos)
            if m:
                word = m.group()
                upper = word.upper()
                if upper in _FORBIDDEN_KEYWORDS:
                    raise ValueError(f"自定义条件表达式不合法：禁止使用 SQL 关键字 '{word}'")
                if upper in _LOGIC_KEYWORDS:
                    self._tokens.append(Token(TokenType.KEYWORD, upper, self._pos))
                elif upper in ("IN", "BETWEEN", "LIKE"):
                    self._tokens.append(Token(TokenType.OPERATOR, upper, self._pos))
                elif upper == "NULL":
                    self._tokens.append(Token(TokenType.NULL_LIT, "NULL", self._pos))
                else:
                    self._tokens.append(Token(TokenType.COLUMN_REF, word, self._pos))
                self._pos = m.end()
                continue

            raise ValueError(f"自定义条件表达式不合法：位置 {self._pos} 处存在非法字符 '{ch}'")

        self._tokens.append(Token(TokenType.EOF, "", self._pos))
        return self._tokens

    def _peek_is_number(self) -> bool:
        """检查负号后面是否跟着数字（用于区分负数和减号）。"""
        nxt = self._pos + 1
        if nxt < len(self._expr) and self._expr[nxt].isdigit():
            # 负号前面不能是标识符/数字/右括号（那样是减法）
            if self._tokens:
                prev = self._tokens[-1]
                if prev.type in (TokenType.COLUMN_REF, TokenType.NUMBER_LIT, TokenType.RPAREN):
                    return False
            return True
        return False

    def _read_string(self) -> None:
        start = self._pos
        self._pos += 1  # 跳过开头的 '
        buf: list[str] = []
        while self._pos < len(self._expr):
            ch = self._expr[self._pos]
            if ch == "'":
                # 检查转义的单引号 ''
                if self._pos + 1 < len(self._expr) and self._expr[self._pos + 1] == "'":
                    buf.append("'")
                    self._pos += 2
                    continue
                self._pos += 1  # 跳过结尾的 '
                self._tokens.append(Token(TokenType.STRING_LIT, "".join(buf), start))
                return
            buf.append(ch)
            self._pos += 1
        raise ValueError(f"自定义条件表达式不合法：位置 {start} 处的字符串未闭合")

    def _read_number(self) -> None:
        m = _NUMBER_RE.match(self._expr, self._pos)
        if m:
            self._tokens.append(Token(TokenType.NUMBER_LIT, m.group(), self._pos))
            self._pos = m.end()
        else:
            raise ValueError(f"自定义条件表达式不合法：位置 {self._pos} 处的数字格式错误")


# ---------------------------------------------------------------------------
# 语法分析器（递归下降）
# ---------------------------------------------------------------------------

class Parser:
    """严格白名单递归下降解析器。

    语法：
        expr        → or_expr
        or_expr     → and_expr ( 'OR' and_expr )*
        and_expr    → not_expr ( 'AND' not_expr )*
        not_expr    → 'NOT' not_expr | compare_expr | '(' or_expr ')'
        compare_expr→ COLUMN_REF op value
                     | COLUMN_REF 'IN' '(' value_list ')'
                     | COLUMN_REF 'BETWEEN' value 'AND' value
                     | COLUMN_REF 'LIKE' string_value
        value       → STRING_LIT | NUMBER_LIT | NULL_LIT
        value_list  → value ( ',' value )*
    """

    def __init__(self, tokens: list[Token], allowed_columns: list[str]) -> None:
        self._tokens = tokens
        self._pos = 0
        self._allowed = {c.lower() for c in allowed_columns}

    def parse(self) -> CompareExpr | LogicalExpr:
        node = self._or_expr()
        if self._current().type != TokenType.EOF:
            raise ValueError(
                f"自定义条件表达式不合法：位置 {self._current().pos} 处存在多余内容 '{self._current().value}'"
            )
        return node

    # -- 辅助 --

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, ttype: TokenType, value: str | None = None) -> Token:
        tok = self._current()
        if tok.type != ttype or (value is not None and tok.value != value):
            expected = f"{ttype.value}" + (f" '{value}'" if value else "")
            raise ValueError(
                f"自定义条件表达式不合法：位置 {tok.pos} 处期望 {expected}，实际为 '{tok.value}'"
            )
        return self._advance()

    # -- 语法规则 --

    def _or_expr(self) -> CompareExpr | LogicalExpr:
        left = self._and_expr()
        while self._current().type == TokenType.KEYWORD and self._current().value == "OR":
            self._advance()
            right = self._and_expr()
            if isinstance(left, LogicalExpr) and left.op == "OR":
                left.children.append(right)
            else:
                left = LogicalExpr(op="OR", children=[left, right])
        return left

    def _and_expr(self) -> CompareExpr | LogicalExpr:
        left = self._not_expr()
        while self._current().type == TokenType.KEYWORD and self._current().value == "AND":
            # 需要区分 BETWEEN ... AND ... 中的 AND 和逻辑 AND
            # 这里不需要特殊处理，因为 BETWEEN 的 AND 在 _compare_expr 中已消费
            self._advance()
            right = self._not_expr()
            if isinstance(left, LogicalExpr) and left.op == "AND":
                left.children.append(right)
            else:
                left = LogicalExpr(op="AND", children=[left, right])
        return left

    def _not_expr(self) -> CompareExpr | LogicalExpr:
        if self._current().type == TokenType.KEYWORD and self._current().value == "NOT":
            self._advance()
            child = self._not_expr()
            return LogicalExpr(op="NOT", children=[child])

        if self._current().type == TokenType.LPAREN:
            self._advance()
            node = self._or_expr()
            self._expect(TokenType.RPAREN)
            return node

        return self._compare_expr()

    def _compare_expr(self) -> CompareExpr:
        col_tok = self._expect(TokenType.COLUMN_REF)
        col_name = col_tok.value

        # 检查是否是函数调用（标识符后紧跟左括号）
        if self._current().type == TokenType.LPAREN:
            raise ValueError(f"自定义条件表达式不合法：禁止函数调用 '{col_name}(...)'")

        # 列名白名单校验
        if col_name.lower() not in self._allowed:
            raise ValueError(f"列 {col_name} 不存在于目标业务表")

        op_tok = self._current()
        if op_tok.type != TokenType.OPERATOR:
            raise ValueError(
                f"自定义条件表达式不合法：位置 {op_tok.pos} 处期望比较运算符，实际为 '{op_tok.value}'"
            )
        op = self._advance().value

        if op not in _COMPARE_OPS:
            raise ValueError(f"自定义条件表达式不合法：不支持的运算符 '{op}'")

        col_ref = ColumnRef(name=col_name)

        if op == "IN":
            self._expect(TokenType.LPAREN)
            values = self._value_list()
            self._expect(TokenType.RPAREN)
            return CompareExpr(column=col_ref, op="IN", value=values)

        if op == "BETWEEN":
            low = self._value()
            # BETWEEN 的 AND 是语法的一部分，不是逻辑 AND
            self._expect(TokenType.KEYWORD, "AND")
            high = self._value()
            return CompareExpr(column=col_ref, op="BETWEEN", value=(low, high))

        # 普通比较：= != > < >= <= LIKE
        val = self._value()
        return CompareExpr(column=col_ref, op=op, value=val)

    def _value(self) -> Literal:
        tok = self._current()
        if tok.type == TokenType.STRING_LIT:
            self._advance()
            return Literal(value=tok.value)
        if tok.type == TokenType.NUMBER_LIT:
            self._advance()
            # 解析为 int 或 float
            if "." in tok.value:
                return Literal(value=float(tok.value))
            return Literal(value=int(tok.value))
        if tok.type == TokenType.NULL_LIT:
            self._advance()
            return Literal(value=None)
        raise ValueError(
            f"自定义条件表达式不合法：位置 {tok.pos} 处期望值（字符串/数字/NULL），实际为 '{tok.value}'"
        )

    def _value_list(self) -> list[Literal]:
        values = [self._value()]
        while self._current().type == TokenType.COMMA:
            self._advance()
            values.append(self._value())
        return values


# ---------------------------------------------------------------------------
# SQL 生成器
# ---------------------------------------------------------------------------

class SQLGenerator:
    """遍历 AST 生成参数化 SQL 片段和绑定参数。"""

    def __init__(self) -> None:
        self._param_counter = 0
        self._bind_params: dict[str, Any] = {}
        self._referenced_columns: list[str] = []
        self._seen_columns: set[str] = set()

    def generate(self, node: CompareExpr | LogicalExpr) -> ParseResult:
        sql = self._visit(node)
        return ParseResult(
            sql_fragment=sql,
            bind_params=self._bind_params,
            referenced_columns=self._referenced_columns,
        )

    def _next_param(self) -> str:
        name = f"p{self._param_counter}"
        self._param_counter += 1
        return name

    def _track_column(self, name: str) -> None:
        if name not in self._seen_columns:
            self._seen_columns.add(name)
            self._referenced_columns.append(name)

    def _visit(self, node: CompareExpr | LogicalExpr) -> str:
        if isinstance(node, CompareExpr):
            return self._visit_compare(node)
        if isinstance(node, LogicalExpr):
            return self._visit_logical(node)
        raise ValueError(f"自定义条件表达式不合法：未知的 AST 节点类型 {type(node).__name__}")

    def _visit_compare(self, node: CompareExpr) -> str:
        col = node.column.name
        self._track_column(col)
        op = node.op

        if op == "IN":
            # value 是 list[Literal]
            params = []
            for lit in node.value:
                p = self._next_param()
                self._bind_params[p] = lit.value
                params.append(f":{p}")
            return f"{col} IN ({', '.join(params)})"

        if op == "BETWEEN":
            low_lit, high_lit = node.value
            p_low = self._next_param()
            p_high = self._next_param()
            self._bind_params[p_low] = low_lit.value
            self._bind_params[p_high] = high_lit.value
            return f"{col} BETWEEN :{p_low} AND :{p_high}"

        # 普通比较
        if isinstance(node.value, Literal) and node.value.value is None:
            # NULL 特殊处理
            if op == "=":
                return f"{col} IS NULL"
            if op == "!=":
                return f"{col} IS NOT NULL"
            # 其他运算符 + NULL 不合理，但仍生成绑定参数
            p = self._next_param()
            self._bind_params[p] = None
            return f"{col} {op} :{p}"

        p = self._next_param()
        self._bind_params[p] = node.value.value
        return f"{col} {op} :{p}"

    def _visit_logical(self, node: LogicalExpr) -> str:
        if node.op == "NOT":
            child_sql = self._visit(node.children[0])
            return f"NOT ({child_sql})"

        parts = [self._visit(child) for child in node.children]
        joiner = f" {node.op} "
        # 多个子节点时加括号保证优先级
        if len(parts) == 1:
            return parts[0]
        return f"({joiner.join(parts)})"


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def parse_condition(expr: str, allowed_columns: list[str]) -> ParseResult:
    """解析 custom_condition 表达式，返回参数化 SQL 片段和绑定参数。

    流程：
    1. 空输入校验
    2. 长度校验（≤ 500 字符）
    3. Unicode NFC 规范化
    4. 禁止字符序列检查
    5. 词法分析 → tokens
    6. 严格白名单 AST 构建
    7. 列名白名单校验（在解析阶段完成）
    8. 生成参数化 SQL 片段

    Raises:
        ValueError: 输入不合法时抛出，包含具体原因。
    """
    # 1. 空输入
    if not expr or not expr.strip():
        raise ValueError("自定义条件表达式不合法：表达式不能为空")

    # 2. 长度校验
    if len(expr) > MAX_CONDITION_LENGTH:
        raise ValueError("自定义条件表达式超过最大长度限制（500 字符）")

    # 3. Unicode NFC 规范化
    expr = unicodedata.normalize("NFC", expr)

    # 4. 禁止字符序列
    for seq in _FORBIDDEN_SEQUENCES:
        if seq in expr:
            raise ValueError(f"自定义条件表达式不合法：禁止包含 '{seq}'")

    # 5. 词法分析
    lexer = Lexer(expr)
    tokens = lexer.tokenize()

    # 6. 语法分析（含列名白名单校验）
    if not allowed_columns:
        raise ValueError("自定义条件表达式不合法：允许的列名列表不能为空")

    parser = Parser(tokens, allowed_columns)
    ast = parser.parse()

    # 7. 生成参数化 SQL
    generator = SQLGenerator()
    return generator.generate(ast)
