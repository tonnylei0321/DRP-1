"""第6章：ETL 管道单元测试。"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from drp.etl.cleaner import clean_null, clean_row, normalize_enum, clean_amount
from drp.etl.hash_diff import build_snapshot, diff_rows, row_hash
from drp.etl.quality import (
    compute_data_quality,
    compute_format_compliance,
    compute_latency,
    compute_null_rate,
)
from drp.etl.engine import EtlSyncEngine

# ─── 数据清洗 ─────────────────────────────────────────────────────────────────


def test_clean_null_空字符串():
    assert clean_null("") is None
    assert clean_null("NULL") is None
    assert clean_null("null") is None
    assert clean_null("N/A") is None


def test_clean_null_正常值保留():
    assert clean_null("abc") == "abc"
    assert clean_null(0) == 0
    assert clean_null(False) is False


def test_normalize_enum_状态映射():
    assert normalize_enum("1") == "active"
    assert normalize_enum("0") == "inactive"
    assert normalize_enum("正常") == "active"
    assert normalize_enum("冻结") == "frozen"
    assert normalize_enum(None) is None


def test_normalize_enum_自定义映射():
    custom = {"open": "running", "close": "stopped"}
    assert normalize_enum("open", custom) == "running"


def test_clean_amount_处理逗号和符号():
    assert clean_amount("1,234,567.89") == 1234567.89
    assert clean_amount("¥999.00") == 999.0
    assert clean_amount(None) is None
    assert clean_amount("") is None


def test_clean_row_全流程():
    row = {"name": "test", "status": "1", "amount": "¥1,000", "junk": "NULL"}
    result = clean_row(
        row,
        enum_fields={"status": {"1": "active"}},
    )
    assert result["junk"] is None
    assert result["status"] == "active"


# ─── 哈希比对 ─────────────────────────────────────────────────────────────────


def test_row_hash_相同行相同哈希():
    row = {"id": 1, "name": "test", "balance": 100}
    h1 = row_hash(row, ["id"])
    h2 = row_hash(row, ["id"])
    assert h1 == h2


def test_row_hash_不同值不同哈希():
    r1 = {"id": 1, "name": "foo"}
    r2 = {"id": 1, "name": "bar"}
    _, h1 = row_hash(r1, ["id"])
    _, h2 = row_hash(r2, ["id"])
    assert h1 != h2


def test_diff_rows_检测新增():
    source = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    snapshot = {}
    upserts, unchanged, deleted = diff_rows(source, snapshot, ["id"])
    assert len(upserts) == 2
    assert len(unchanged) == 0
    assert len(deleted) == 0


def test_diff_rows_检测变更():
    old_row = {"id": 1, "name": "old"}
    snapshot = build_snapshot([old_row], ["id"])
    new_row = {"id": 1, "name": "new"}
    upserts, _, _ = diff_rows([new_row], snapshot, ["id"])
    assert len(upserts) == 1


def test_diff_rows_检测删除():
    rows = [{"id": 1, "name": "a"}]
    snapshot = build_snapshot(rows, ["id"])
    # 源库已无该行
    upserts, _, deleted = diff_rows([], snapshot, ["id"])
    assert len(deleted) == 1
    assert "1" in deleted[0]


def test_diff_rows_无变化():
    rows = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    snapshot = build_snapshot(rows, ["id"])
    upserts, unchanged, deleted = diff_rows(rows, snapshot, ["id"])
    assert len(upserts) == 0
    assert len(unchanged) == 2
    assert len(deleted) == 0


# ─── 数据质量评分 ─────────────────────────────────────────────────────────────


def test_空值率_无空值():
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    assert compute_null_rate(rows) == 0.0


def test_空值率_含空值():
    rows = [{"a": None, "b": "x"}, {"a": 2, "b": None}]
    rate = compute_null_rate(rows)
    assert rate == 0.5


def test_延迟_近期水位线():
    watermark = datetime.now(timezone.utc) - timedelta(minutes=30)
    latency = compute_latency(watermark)
    assert latency < 3600


def test_延迟_无水位线为无穷大():
    assert compute_latency(None) == float("inf")


def test_格式合规率_全合规():
    rows = [{"phone": "13800138000"}, {"phone": "15012345678"}]
    rules = {"phone": r"1[3-9]\d{9}"}
    rate = compute_format_compliance(rows, rules)
    assert rate == 1.0


def test_格式合规率_部分违规():
    rows = [{"phone": "13800138000"}, {"phone": "invalid"}]
    rules = {"phone": r"1[3-9]\d{9}"}
    rate = compute_format_compliance(rows, rules)
    assert rate == 0.5


def test_综合质量分_健康数据():
    rows = [{"id": i, "name": f"row{i}"} for i in range(10)]
    watermark = datetime.now(timezone.utc) - timedelta(minutes=10)
    score = compute_data_quality(rows, watermark=watermark)
    assert score.overall > 80
    assert score.is_healthy


def test_综合质量分_延迟过大():
    rows = [{"id": 1, "name": "test"}]
    watermark = datetime.now(timezone.utc) - timedelta(hours=5)
    score = compute_data_quality(rows, watermark=watermark, max_latency_seconds=3600)
    # 延迟超过上限，延迟分为 0
    assert score.latency_seconds > 3600


# ─── EtlSyncEngine ────────────────────────────────────────────────────────────

_SIMPLE_YAML = """
mappings:
  - source_table: account
    source_field: acct_no
    data_type: VARCHAR
    target_property: ctio:accountNumber
    transform_rule: ""
    confidence: 92.5
    auto_approved: true
  - source_table: account
    source_field: balance
    data_type: DECIMAL
    target_property: ctio:balance
    transform_rule: ""
    confidence: 85.0
    auto_approved: true
"""


async def test_etl_engine_全量同步():
    """全量同步应调用 source_fetcher 并写入 GraphDB。"""
    rows = [{"id": 1, "acct_no": "001", "balance": 1000.0}]
    mock_fetcher = AsyncMock(return_value=rows)
    mock_graphdb = AsyncMock()
    mock_graphdb._sparql_update = AsyncMock()

    engine = EtlSyncEngine(
        source_fetcher=mock_fetcher,
        graphdb_client=mock_graphdb,
        mapping_yaml=_SIMPLE_YAML,
        tenant_id="test-tenant-123",
    )

    triples = await engine.full_sync("account")

    mock_fetcher.assert_called_once_with("account")
    mock_graphdb._sparql_update.assert_called()
    assert triples > 0


async def test_etl_engine_增量同步():
    """增量同步应传入水位线参数。"""
    watermark = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [{"id": 2, "acct_no": "002", "balance": 500.0}]
    mock_fetcher = AsyncMock(return_value=rows)
    mock_graphdb = AsyncMock()
    mock_graphdb._sparql_update = AsyncMock()

    engine = EtlSyncEngine(
        source_fetcher=mock_fetcher,
        graphdb_client=mock_graphdb,
        mapping_yaml=_SIMPLE_YAML,
        tenant_id="test-tenant-123",
    )

    triples, new_wm = await engine.incremental_sync("account", watermark)

    mock_fetcher.assert_called_once_with("account", watermark)
    assert triples > 0
    assert new_wm > watermark


async def test_etl_engine_空数据不写入():
    """源库返回空数据时，不应调用 GraphDB 写入。"""
    mock_fetcher = AsyncMock(return_value=[])
    mock_graphdb = AsyncMock()
    mock_graphdb._sparql_update = AsyncMock()

    engine = EtlSyncEngine(
        source_fetcher=mock_fetcher,
        graphdb_client=mock_graphdb,
        mapping_yaml=_SIMPLE_YAML,
        tenant_id="test-tenant-123",
    )

    triples = await engine.full_sync("account")
    assert triples == 0
    mock_graphdb._sparql_update.assert_not_called()
