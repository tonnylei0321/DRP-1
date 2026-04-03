"""置信度评分算法：综合字段名语义、注释质量、值域推断、历史映射匹配。

返回 0.0~100.0 分，>=80 自动批准。
"""
import re

# 自动批准阈值
AUTO_APPROVE_THRESHOLD = 80.0

# 字段名关键词 → CTIO 语义匹配奖分
_SEMANTIC_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"acct.*no|account.*num|acct_id", re.IGNORECASE), 15.0),
    (re.compile(r"balance|bal\b", re.IGNORECASE), 12.0),
    (re.compile(r"currency|ccy\b|curr\b", re.IGNORECASE), 10.0),
    (re.compile(r"bank.*code|bic\b|swift", re.IGNORECASE), 12.0),
    (re.compile(r"entity.*id|legal.*entity|corp.*id", re.IGNORECASE), 10.0),
    (re.compile(r"risk|restricted|freeze", re.IGNORECASE), 8.0),
    (re.compile(r"status|state\b", re.IGNORECASE), 5.0),
    (re.compile(r"amount|amt\b", re.IGNORECASE), 8.0),
    (re.compile(r"date|created_at|updated_at|timestamp", re.IGNORECASE), 5.0),
    (re.compile(r"pool|cash.*pool", re.IGNORECASE), 12.0),
]

# 注释质量分（字符数基础分）
_COMMENT_BASE = 20.0
_COMMENT_MAX_CHARS = 50

# 历史映射精确匹配奖分
_HISTORY_EXACT_BONUS = 30.0
_HISTORY_TABLE_BONUS = 10.0


def _semantic_score(field_name: str) -> float:
    """基于字段名语义的匹配分（0~30）。"""
    score = 0.0
    for pattern, pts in _SEMANTIC_PATTERNS:
        if pattern.search(field_name):
            score += pts
    return min(score, 30.0)


def _comment_score(comment: str) -> float:
    """注释质量分（0~20）：有注释且内容充实则给满分。"""
    if not comment:
        return 0.0
    chars = min(len(comment.strip()), _COMMENT_MAX_CHARS)
    return round(chars / _COMMENT_MAX_CHARS * _COMMENT_BASE, 2)


def _type_score(data_type: str, target_property: str) -> float:
    """值域推断分（0~20）：类型与目标属性匹配性。"""
    dt = data_type.upper()
    tp = target_property.lower()
    score = 0.0

    if any(k in dt for k in ("DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "MONEY")):
        if any(k in tp for k in ("balance", "amount", "value", "rate")):
            score += 20.0
        else:
            score += 5.0

    elif any(k in dt for k in ("VARCHAR", "CHAR", "TEXT", "NVARCHAR")):
        if any(k in tp for k in ("name", "code", "id", "label")):
            score += 15.0
        else:
            score += 5.0

    elif any(k in dt for k in ("DATE", "TIMESTAMP", "DATETIME")):
        if any(k in tp for k in ("date", "time", "at")):
            score += 20.0
        else:
            score += 5.0

    elif any(k in dt for k in ("INT", "BIGINT", "SMALLINT")):
        if any(k in tp for k in ("count", "num", "qty")):
            score += 15.0
        else:
            score += 8.0

    return min(score, 20.0)


def _history_score(
    source_table: str,
    source_field: str,
    target_property: str,
    history: list[dict],
) -> float:
    """历史映射匹配分（0~30）。"""
    if not history:
        return 0.0

    for rec in history:
        # 精确匹配：同表、同字段、同目标
        if (
            rec.get("source_table", "").lower() == source_table.lower()
            and rec.get("source_field", "").lower() == source_field.lower()
            and rec.get("target_property", "") == target_property
        ):
            return _HISTORY_EXACT_BONUS

    # 同表不同字段或不同表同字段
    for rec in history:
        if rec.get("source_table", "").lower() == source_table.lower():
            return _HISTORY_TABLE_BONUS

    return 0.0


def compute_confidence(
    field_name: str,
    data_type: str,
    comment: str,
    target_property: str,
    source_table: str = "",
    history: list[dict] | None = None,
) -> float:
    """计算映射置信度分（0.0~100.0）。

    Args:
        field_name: 源字段名
        data_type: 源字段类型
        comment: 字段注释
        target_property: 候选目标 CTIO/FIBO 属性 IRI
        source_table: 源表名（用于历史查询）
        history: 历史映射记录列表

    Returns:
        0.0~100.0 的置信度分
    """
    score = (
        _semantic_score(field_name)
        + _comment_score(comment)
        + _type_score(data_type, target_property)
        + _history_score(source_table, field_name, target_property, history or [])
    )
    return round(min(score, 100.0), 2)


def should_auto_approve(confidence: float) -> bool:
    """置信度达到阈值时自动批准。"""
    return confidence >= AUTO_APPROVE_THRESHOLD
