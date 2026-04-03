"""数据质量三维评分：空值率、延迟、格式合规率。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DataQualityScore:
    """三维数据质量评分结果。"""
    null_rate: float        # 空值率 0.0~1.0（越低越好）
    latency_seconds: float  # 数据延迟（秒，从 updated_at 到当前）
    format_compliance: float  # 格式合规率 0.0~1.0（越高越好）
    overall: float          # 综合分 0.0~100.0

    @property
    def is_healthy(self) -> bool:
        """综合分 >= 80 视为健康。"""
        return self.overall >= 80.0


def compute_null_rate(rows: list[dict[str, Any]], fields: list[str] | None = None) -> float:
    """计算空值率（NULL / 总单元格数）。"""
    if not rows:
        return 0.0
    check_fields = fields or list(rows[0].keys())
    total = len(rows) * len(check_fields)
    nulls = sum(
        1 for row in rows for f in check_fields
        if row.get(f) is None or str(row.get(f, "")).strip().upper() in ("NULL", "NONE", "")
    )
    return round(nulls / total, 4) if total > 0 else 0.0


def compute_latency(watermark: datetime | None) -> float:
    """计算数据延迟（秒）：当前时间 - 水位线时间。"""
    if watermark is None:
        return float("inf")
    now = datetime.now(timezone.utc)
    wm = watermark if watermark.tzinfo else watermark.replace(tzinfo=timezone.utc)
    return max(0.0, (now - wm).total_seconds())


def compute_format_compliance(
    rows: list[dict[str, Any]],
    rules: dict[str, str],
) -> float:
    """计算格式合规率。

    Args:
        rows: 数据行列表
        rules: {字段名: 正则规则} 字典

    Returns:
        0.0~1.0 的合规率
    """
    import re
    if not rows or not rules:
        return 1.0

    compiled = {f: re.compile(p) for f, p in rules.items()}
    total = len(rows) * len(rules)
    compliant = 0

    for row in rows:
        for field, pattern in compiled.items():
            val = row.get(field)
            if val is not None and pattern.match(str(val)):
                compliant += 1

    return round(compliant / total, 4) if total > 0 else 1.0


def compute_data_quality(
    rows: list[dict[str, Any]],
    watermark: datetime | None = None,
    format_rules: dict[str, str] | None = None,
    fields: list[str] | None = None,
    max_latency_seconds: float = 7200.0,
) -> DataQualityScore:
    """计算综合数据质量分。

    权重：空值率 40%，延迟 30%，格式合规率 30%。

    Args:
        rows: 数据样本行
        watermark: 最新数据时间戳（用于延迟计算）
        format_rules: {字段名: 正则规则}
        fields: 参与空值率计算的字段列表
        max_latency_seconds: 延迟上限（超过则得 0 分）
    """
    null_rate = compute_null_rate(rows, fields)
    latency = compute_latency(watermark)
    compliance = compute_format_compliance(rows, format_rules or {})

    # 各维度转换为 0~100 分
    null_score = (1.0 - null_rate) * 100
    latency_score = max(0.0, (1.0 - latency / max_latency_seconds) * 100) if latency != float("inf") else 0.0
    compliance_score = compliance * 100

    overall = round(null_score * 0.4 + latency_score * 0.3 + compliance_score * 0.3, 2)

    return DataQualityScore(
        null_rate=null_rate,
        latency_seconds=latency,
        format_compliance=compliance,
        overall=overall,
    )
