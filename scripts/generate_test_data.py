#!/usr/bin/env python3
"""端到端测试数据生成器。

独立 Python 脚本，不依赖后端服务。
生成覆盖 7 大业务域的 DDL 文件和测试数据（INSERT 语句）。

输出目录：
  - backend/tests/fixtures/ddl/   — DDL 文件（CREATE TABLE + COMMENT）
  - backend/tests/fixtures/data/  — INSERT 数据文件
  - backend/tests/fixtures/ddl/all_tables.sql — 合并文件

用法：
  python scripts/generate_test_data.py
"""

from __future__ import annotations

import os
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class ColumnDef:
    """列定义"""
    name: str
    data_type: str
    nullable: bool = True
    comment: str = ""


@dataclass
class TableDef:
    """表定义"""
    name: str
    columns: list[ColumnDef]
    comment: str = ""


@dataclass
class Entity:
    """法人实体"""
    id: str
    level: int
    name: str
    parent: str | None = None


class Distribution(Enum):
    """数据分布类型"""
    NORMAL = "normal"      # 70% — 指标达标
    WARNING = "warning"    # 20% — 接近阈值
    REDLINE = "redline"    # 10% — 超过红线


# ---------------------------------------------------------------------------
# 法人实体层级（test_ 前缀，防止与生产数据冲突）
# ---------------------------------------------------------------------------

ENTITY_HIERARCHY: list[Entity] = [
    Entity("test_group_hq", 0, "国有资本运营集团"),
    Entity("test_region_east", 1, "华东大区", "test_group_hq"),
    Entity("test_region_north", 1, "华北大区", "test_group_hq"),
    Entity("test_sub_east_a", 2, "华东子公司A", "test_region_east"),
    Entity("test_sub_east_b", 2, "华东子公司B", "test_region_east"),
    Entity("test_sub_north_a", 2, "华北子公司A", "test_region_north"),
]

# 子公司级别实体（用于数据生成）
SUB_ENTITIES = [e for e in ENTITY_HIERARCHY if e.level == 2]


# ---------------------------------------------------------------------------
# 7 大域表结构定义（根据 registry.py 中 SPARQL 查询反推）
# ---------------------------------------------------------------------------

DOMAIN_TABLES: dict[str, list[TableDef]] = {
    # ── 银行账户域（001-031）──────────────────────────────────────────────
    "01_bank_account": [
        TableDef("direct_linked_account", comment="直联账户表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("bank_code", "VARCHAR(20)", True, "银行编码"),
            ColumnDef("acct_no", "VARCHAR(50) NOT NULL", False, "账号"),
            ColumnDef("balance", "DECIMAL(18,2)", True, "余额"),
            ColumnDef("currency", "CHAR(3) DEFAULT 'CNY'", True, "币种"),
            ColumnDef("is_active", "BOOLEAN DEFAULT true", True, "是否活跃"),
            ColumnDef("ukey_status", "VARCHAR(20) DEFAULT 'configured'", True, "UKey状态"),
            ColumnDef("status_6311", "VARCHAR(20)", True, "6311受限状态"),
            ColumnDef("is_restricted", "BOOLEAN DEFAULT false", True, "是否受限"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
        TableDef("internal_deposit_account", comment="内部存款账户表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("pool_id", "VARCHAR(50)", True, "资金池ID"),
            ColumnDef("balance", "DECIMAL(18,2)", True, "余额"),
            ColumnDef("interest_rate", "DECIMAL(5,4)", True, "利率"),
            ColumnDef("maturity_date", "DATE", True, "到期日"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
        TableDef("restricted_account", comment="受限账户表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("acct_no", "VARCHAR(50)", True, "账号"),
            ColumnDef("restriction_type", "VARCHAR(50)", True, "受限类型"),
            ColumnDef("status_6311", "VARCHAR(20)", True, "6311受限状态"),
            ColumnDef("frozen_amount", "DECIMAL(18,2)", True, "冻结金额"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
    ],
    # ── 资金集中域（032-041）──────────────────────────────────────────────
    "02_fund_concentration": [
        TableDef("cash_pool", comment="资金池表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("pool_name", "VARCHAR(100)", True, "资金池名称"),
            ColumnDef("total_balance", "DECIMAL(18,2)", True, "总余额"),
            ColumnDef("concentration_rate", "DECIMAL(5,4)", True, "集中率"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
        TableDef("collection_record", comment="归集记录表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("pool_id", "VARCHAR(50) NOT NULL", False, "资金池ID"),
            ColumnDef("source_acct", "VARCHAR(50)", True, "来源账户"),
            ColumnDef("amount", "DECIMAL(18,2)", True, "归集金额"),
            ColumnDef("collection_date", "DATE", True, "归集日期"),
            ColumnDef("status", "VARCHAR(20) DEFAULT 'completed'", True, "状态"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
    ],
    # ── 结算域（042-068）─────────────────────────────────────────────────
    "03_settlement": [
        TableDef("settlement_record", comment="结算记录表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("channel", "VARCHAR(30) NOT NULL", False, "结算渠道"),
            ColumnDef("amount", "DECIMAL(18,2)", True, "结算金额"),
            ColumnDef("currency", "CHAR(3) DEFAULT 'CNY'", True, "币种"),
            ColumnDef("counterparty", "VARCHAR(100)", True, "交易对手"),
            ColumnDef("is_cross_bank", "BOOLEAN DEFAULT false", True, "是否跨行"),
            ColumnDef("is_cross_border", "BOOLEAN DEFAULT false", True, "是否跨境"),
            ColumnDef("is_internal", "BOOLEAN DEFAULT false", True, "是否内部"),
            ColumnDef("status", "VARCHAR(20) DEFAULT 'settled'", True, "结算状态"),
            ColumnDef("settled_at", "TIMESTAMP DEFAULT NOW()", True, "结算时间"),
        ]),
        TableDef("payment_channel", comment="支付渠道表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("channel_name", "VARCHAR(50)", True, "渠道名称"),
            ColumnDef("channel_type", "VARCHAR(30)", True, "渠道类型"),
            ColumnDef("is_direct_linked", "BOOLEAN DEFAULT true", True, "是否直联"),
            ColumnDef("daily_limit", "DECIMAL(18,2)", True, "日限额"),
        ]),
    ],
    # ── 票据域（069-078）─────────────────────────────────────────────────
    "04_bill": [
        TableDef("bill", comment="票据表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("bill_type", "VARCHAR(30) NOT NULL", False, "票据类型"),
            ColumnDef("face_value", "DECIMAL(18,2)", True, "票面金额"),
            ColumnDef("issue_date", "DATE", True, "出票日期"),
            ColumnDef("maturity_date", "DATE", True, "到期日"),
            ColumnDef("status", "VARCHAR(20) DEFAULT 'active'", True, "状态"),
            ColumnDef("is_overdue", "BOOLEAN DEFAULT false", True, "是否逾期"),
            ColumnDef("created_at", "TIMESTAMP DEFAULT NOW()", True, "创建时间"),
        ]),
        TableDef("endorsement_chain", comment="背书链表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("bill_id", "VARCHAR(50) NOT NULL", False, "票据ID"),
            ColumnDef("endorser_id", "VARCHAR(50)", True, "背书人ID"),
            ColumnDef("endorsee_id", "VARCHAR(50)", True, "被背书人ID"),
            ColumnDef("endorse_date", "DATE", True, "背书日期"),
            ColumnDef("sequence_no", "INTEGER", True, "背书序号"),
        ]),
    ],
    # ── 债务融资域（079-085）─────────────────────────────────────────────
    "05_debt_financing": [
        TableDef("loan", comment="贷款表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("bank_code", "VARCHAR(20)", True, "银行编码"),
            ColumnDef("principal", "DECIMAL(18,2)", True, "本金"),
            ColumnDef("interest_rate", "DECIMAL(5,4)", True, "利率"),
            ColumnDef("start_date", "DATE", True, "起始日"),
            ColumnDef("end_date", "DATE", True, "到期日"),
            ColumnDef("status", "VARCHAR(20) DEFAULT 'active'", True, "状态"),
        ]),
        TableDef("bond", comment="债券表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("bond_code", "VARCHAR(30)", True, "债券代码"),
            ColumnDef("face_value", "DECIMAL(18,2)", True, "面值"),
            ColumnDef("coupon_rate", "DECIMAL(5,4)", True, "票面利率"),
            ColumnDef("maturity_date", "DATE", True, "到期日"),
            ColumnDef("status", "VARCHAR(20) DEFAULT 'active'", True, "状态"),
        ]),
        TableDef("finance_lease", comment="融资租赁表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("lessor", "VARCHAR(100)", True, "出租方"),
            ColumnDef("lease_amount", "DECIMAL(18,2)", True, "租赁金额"),
            ColumnDef("monthly_payment", "DECIMAL(18,2)", True, "月付金额"),
            ColumnDef("start_date", "DATE", True, "起始日"),
            ColumnDef("end_date", "DATE", True, "到期日"),
        ]),
    ],
    # ── 决策风险域（086-097）─────────────────────────────────────────────
    "06_risk_decision": [
        TableDef("credit_line", comment="授信表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("bank_code", "VARCHAR(20)", True, "银行编码"),
            ColumnDef("credit_limit", "DECIMAL(18,2)", True, "授信额度"),
            ColumnDef("used_amount", "DECIMAL(18,2)", True, "已用额度"),
            ColumnDef("expire_date", "DATE", True, "到期日"),
        ]),
        TableDef("guarantee", comment="担保表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("guarantor_id", "VARCHAR(50) NOT NULL", False, "担保人ID"),
            ColumnDef("beneficiary_id", "VARCHAR(50)", True, "受益人ID"),
            ColumnDef("amount", "DECIMAL(18,2)", True, "担保金额"),
            ColumnDef("guarantee_type", "VARCHAR(30)", True, "担保类型"),
            ColumnDef("start_date", "DATE", True, "起始日"),
            ColumnDef("end_date", "DATE", True, "到期日"),
        ]),
        TableDef("related_transaction", comment="关联交易表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_a_id", "VARCHAR(50) NOT NULL", False, "交易方A"),
            ColumnDef("entity_b_id", "VARCHAR(50) NOT NULL", False, "交易方B"),
            ColumnDef("amount", "DECIMAL(18,2)", True, "交易金额"),
            ColumnDef("transaction_type", "VARCHAR(30)", True, "交易类型"),
            ColumnDef("transaction_date", "DATE", True, "交易日期"),
        ]),
        TableDef("derivative", comment="衍生品表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("instrument_type", "VARCHAR(30)", True, "工具类型"),
            ColumnDef("notional_amount", "DECIMAL(18,2)", True, "名义金额"),
            ColumnDef("market_value", "DECIMAL(18,2)", True, "市值"),
            ColumnDef("maturity_date", "DATE", True, "到期日"),
        ]),
    ],
    # ── 国资委考核域（098-106）───────────────────────────────────────────
    "07_sasoe_assessment": [
        TableDef("financial_report", comment="财务报表表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("report_type", "VARCHAR(30)", True, "报表类型"),
            ColumnDef("period", "VARCHAR(10)", True, "报告期"),
            ColumnDef("total_asset", "DECIMAL(18,2)", True, "总资产"),
            ColumnDef("net_asset", "DECIMAL(18,2)", True, "净资产"),
            ColumnDef("revenue", "DECIMAL(18,2)", True, "营业收入"),
            ColumnDef("profit", "DECIMAL(18,2)", True, "利润"),
            ColumnDef("rd_expense", "DECIMAL(18,2)", True, "研发费用"),
            ColumnDef("employee_count", "INTEGER", True, "员工人数"),
            ColumnDef("operating_cash_flow", "DECIMAL(18,2)", True, "经营性现金流"),
        ]),
        TableDef("assessment_indicator", comment="考核指标表", columns=[
            ColumnDef("id", "UUID PRIMARY KEY DEFAULT gen_random_uuid()", False, "主键"),
            ColumnDef("entity_id", "VARCHAR(50) NOT NULL", False, "法人实体ID"),
            ColumnDef("indicator_code", "VARCHAR(10)", True, "指标编码"),
            ColumnDef("indicator_name", "VARCHAR(100)", True, "指标名称"),
            ColumnDef("target_value", "DECIMAL(18,4)", True, "目标值"),
            ColumnDef("actual_value", "DECIMAL(18,4)", True, "实际值"),
            ColumnDef("period", "VARCHAR(10)", True, "考核期"),
        ]),
    ],
}


# ---------------------------------------------------------------------------
# 每张表的数据量配置
# ---------------------------------------------------------------------------

TABLE_ROW_COUNTS: dict[str, int] = {
    "direct_linked_account": 50,
    "internal_deposit_account": 10,
    "restricted_account": 5,
    "cash_pool": 5,
    "collection_record": 20,
    "settlement_record": 100,
    "payment_channel": 9,  # 每种渠道一条
    "bill": 30,
    "endorsement_chain": 15,
    "loan": 10,
    "bond": 5,
    "finance_lease": 5,
    "credit_line": 10,
    "guarantee": 5,
    "related_transaction": 10,
    "derivative": 5,
    "financial_report": 6,       # 每个实体一条
    "assessment_indicator": 54,  # 每个实体 9 条考核指标
}

# 结算渠道列表
SETTLEMENT_CHANNELS = [
    "bank_transfer", "online_banking", "bill_payment",
    "letter_of_credit", "guarantee_payment", "collection",
    "remittance", "entrusted_collection", "direct_debit",
]

# 票据类型
BILL_TYPES = ["commercial_draft", "bank_acceptance", "electronic_commercial"]

# 银行编码
BANK_CODES = ["ICBC", "BOC", "CCB", "ABC", "BOCOM", "CMB", "CITIC", "CEB", "SPDB"]

# 考核指标定义（9 条）
ASSESSMENT_INDICATORS = [
    ("AI001", "净资产收益率"),
    ("AI002", "营业收入利润率"),
    ("AI003", "研发投入强度"),
    ("AI004", "全员劳动生产率"),
    ("AI005", "资产负债率"),
    ("AI006", "经营性现金流比率"),
    ("AI007", "总资产周转率"),
    ("AI008", "成本费用利润率"),
    ("AI009", "国有资本保值增值率"),
]


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


def _random_date(start: date = date(2024, 1, 1), end: date = date(2024, 12, 31)) -> date:
    """在指定范围内生成随机日期"""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _random_decimal(low: float, high: float, precision: int = 2) -> str:
    """生成随机小数字符串"""
    val = random.uniform(low, high)
    return f"{val:.{precision}f}"


def _random_acct_no() -> str:
    """生成模拟账号"""
    prefix = random.choice(["6222", "6228", "6217", "6225"])
    suffix = f"{random.randint(1000, 9999)}"
    return f"{prefix}****{suffix}"


def _random_entity() -> Entity:
    """随机选择一个子公司实体"""
    return random.choice(SUB_ENTITIES)


def _random_timestamp(start: date = date(2024, 1, 1), end: date = date(2024, 12, 31)) -> str:
    """生成随机时间戳字符串"""
    d = _random_date(start, end)
    h, m, s = random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)
    return f"{d} {h:02d}:{m:02d}:{s:02d}"



# ---------------------------------------------------------------------------
# TestDataFactory — 测试数据工厂
# ---------------------------------------------------------------------------

class TestDataFactory:
    """按 70/20/10 分布生成测试数据。

    - 正常值（70%）：指标达标
    - 预警值（20%）：接近阈值
    - 红线值（10%）：超过红线
    """

    def __init__(self, entities: list[Entity]):
        self.entities = entities
        self.sub_entities = [e for e in entities if e.level == 2]
        # 用于跨表引用
        self._pool_ids: list[str] = []
        self._bill_ids: list[str] = []

    def generate(self, table: TableDef, count: int) -> list[dict]:
        """按 70/20/10 分布生成测试数据"""
        rows: list[dict] = []
        for i in range(count):
            entity = random.choice(self.sub_entities)
            if i < int(count * 0.7):
                dist = Distribution.NORMAL
            elif i < int(count * 0.9):
                dist = Distribution.WARNING
            else:
                dist = Distribution.REDLINE
            row = self._generate_row(table.name, entity, i, dist)
            rows.append(row)
        return rows

    def _generate_row(self, table_name: str, entity: Entity, idx: int, dist: Distribution) -> dict:
        """根据表名分发到具体的行生成方法"""
        generators = {
            "direct_linked_account": self._gen_direct_linked_account,
            "internal_deposit_account": self._gen_internal_deposit_account,
            "restricted_account": self._gen_restricted_account,
            "cash_pool": self._gen_cash_pool,
            "collection_record": self._gen_collection_record,
            "settlement_record": self._gen_settlement_record,
            "payment_channel": self._gen_payment_channel,
            "bill": self._gen_bill,
            "endorsement_chain": self._gen_endorsement_chain,
            "loan": self._gen_loan,
            "bond": self._gen_bond,
            "finance_lease": self._gen_finance_lease,
            "credit_line": self._gen_credit_line,
            "guarantee": self._gen_guarantee,
            "related_transaction": self._gen_related_transaction,
            "derivative": self._gen_derivative,
            "financial_report": self._gen_financial_report,
            "assessment_indicator": self._gen_assessment_indicator,
        }
        gen = generators.get(table_name)
        if gen is None:
            raise ValueError(f"未知表名: {table_name}")
        return gen(entity, idx, dist)

    # ── 银行账户域 ──────────────────────────────────────────────────────

    def _gen_direct_linked_account(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        row = {
            "id": _uuid(),
            "entity_id": entity.id,
            "bank_code": random.choice(BANK_CODES),
            "acct_no": _random_acct_no(),
            "balance": _random_decimal(100000, 1000000000),
            "currency": "CNY",
            "is_active": True,
            "ukey_status": "configured",
            "status_6311": None,
            "is_restricted": False,
            "created_at": _random_timestamp(),
        }
        if dist == Distribution.WARNING:
            # 预警：UKey 未配置
            row["ukey_status"] = "unconfigured"
        elif dist == Distribution.REDLINE:
            # 红线：账户不活跃（降低直联率）
            row["is_active"] = False
        return row

    def _gen_internal_deposit_account(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        pool_id = random.choice(self._pool_ids) if self._pool_ids else _uuid()
        rate = float(_random_decimal(0.02, 0.05, 4))
        if dist == Distribution.WARNING:
            rate = 0.0150
        elif dist == Distribution.REDLINE:
            rate = 0.0080
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "pool_id": pool_id,
            "balance": _random_decimal(500000, 500000000),
            "interest_rate": f"{rate:.4f}",
            "maturity_date": str(_random_date(date(2024, 6, 1), date(2025, 12, 31))),
            "created_at": _random_timestamp(),
        }

    def _gen_restricted_account(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        restriction_types = ["judicial_freeze", "regulatory_hold", "pledge", "escrow"]
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "acct_no": _random_acct_no(),
            "restriction_type": random.choice(restriction_types),
            "status_6311": "restricted" if dist != Distribution.NORMAL else None,
            "frozen_amount": _random_decimal(100000, 50000000),
            "created_at": _random_timestamp(),
        }

    # ── 资金集中域 ──────────────────────────────────────────────────────

    def _gen_cash_pool(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        pid = _uuid()
        self._pool_ids.append(pid)
        if dist == Distribution.NORMAL:
            rate = float(_random_decimal(0.80, 0.95, 4))
        elif dist == Distribution.WARNING:
            # 预警：接近 0.7 阈值但未超过
            rate = 0.7200
        else:
            # 红线：低于 0.7 阈值
            rate = 0.6000
        return {
            "id": pid,
            "entity_id": entity.id,
            "pool_name": f"资金池_{entity.name}_{idx+1}",
            "total_balance": _random_decimal(10000000, 5000000000),
            "concentration_rate": f"{rate:.4f}",
            "created_at": _random_timestamp(),
        }

    def _gen_collection_record(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        pool_id = random.choice(self._pool_ids) if self._pool_ids else _uuid()
        statuses = ["completed", "pending", "failed"]
        status = "completed" if dist == Distribution.NORMAL else random.choice(statuses)
        return {
            "id": _uuid(),
            "pool_id": pool_id,
            "source_acct": _random_acct_no(),
            "amount": _random_decimal(50000, 100000000),
            "collection_date": str(_random_date()),
            "status": status,
            "created_at": _random_timestamp(),
        }

    # ── 结算域 ──────────────────────────────────────────────────────────

    def _gen_settlement_record(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        channel = SETTLEMENT_CHANNELS[idx % len(SETTLEMENT_CHANNELS)]
        is_cross_bank = channel in ("bank_transfer", "remittance")
        is_cross_border = channel == "letter_of_credit"
        is_internal = channel == "direct_debit"
        counterparties = ["华能集团", "中石化财务", "国电投资", "中铁建设", "中交集团"]
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "channel": channel,
            "amount": _random_decimal(10000, 50000000),
            "currency": "CNY" if not is_cross_border else random.choice(["CNY", "USD", "EUR"]),
            "counterparty": random.choice(counterparties),
            "is_cross_bank": is_cross_bank,
            "is_cross_border": is_cross_border,
            "is_internal": is_internal,
            "status": "settled" if dist == Distribution.NORMAL else "pending",
            "settled_at": _random_timestamp(),
        }

    def _gen_payment_channel(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        """每种渠道一条，共 9 条"""
        channel = SETTLEMENT_CHANNELS[idx % len(SETTLEMENT_CHANNELS)]
        channel_names = {
            "bank_transfer": "银行转账",
            "online_banking": "网上银行",
            "bill_payment": "票据支付",
            "letter_of_credit": "信用证",
            "guarantee_payment": "保函支付",
            "collection": "托收",
            "remittance": "汇款",
            "entrusted_collection": "委托收款",
            "direct_debit": "直接扣款",
        }
        return {
            "id": _uuid(),
            "channel_name": channel_names.get(channel, channel),
            "channel_type": channel,
            "is_direct_linked": dist != Distribution.REDLINE,
            "daily_limit": _random_decimal(1000000, 100000000),
        }

    # ── 票据域 ──────────────────────────────────────────────────────────

    def _gen_bill(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        bid = _uuid()
        self._bill_ids.append(bid)
        bill_type = BILL_TYPES[idx % len(BILL_TYPES)]
        issue = _random_date(date(2024, 1, 1), date(2024, 6, 30))
        maturity = issue + timedelta(days=random.randint(90, 365))
        is_overdue = dist == Distribution.REDLINE
        status = "overdue" if is_overdue else ("active" if dist == Distribution.NORMAL else "pending")
        return {
            "id": bid,
            "entity_id": entity.id,
            "bill_type": bill_type,
            "face_value": _random_decimal(100000, 50000000),
            "issue_date": str(issue),
            "maturity_date": str(maturity),
            "status": status,
            "is_overdue": is_overdue,
            "created_at": _random_timestamp(),
        }

    def _gen_endorsement_chain(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        bill_id = random.choice(self._bill_ids) if self._bill_ids else _uuid()
        entities_pair = random.sample(SUB_ENTITIES, 2)
        return {
            "id": _uuid(),
            "bill_id": bill_id,
            "endorser_id": entities_pair[0].id,
            "endorsee_id": entities_pair[1].id,
            "endorse_date": str(_random_date()),
            "sequence_no": idx + 1,
        }

    # ── 债务融资域 ──────────────────────────────────────────────────────

    def _gen_loan(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        start = _random_date(date(2023, 1, 1), date(2024, 6, 30))
        end = start + timedelta(days=random.randint(180, 1095))
        rate = float(_random_decimal(0.03, 0.06, 4))
        if dist == Distribution.REDLINE:
            rate = float(_random_decimal(0.07, 0.08, 4))
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "bank_code": random.choice(BANK_CODES),
            "principal": _random_decimal(1000000, 500000000),
            "interest_rate": f"{rate:.4f}",
            "start_date": str(start),
            "end_date": str(end),
            "status": "active",
        }

    def _gen_bond(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "bond_code": f"BD{random.randint(100000, 999999)}",
            "face_value": _random_decimal(10000000, 1000000000),
            "coupon_rate": _random_decimal(0.03, 0.06, 4),
            "maturity_date": str(_random_date(date(2025, 1, 1), date(2029, 12, 31))),
            "status": "active",
        }

    def _gen_finance_lease(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        lessors = ["远东宏信", "中银租赁", "工银租赁", "交银租赁", "招银租赁"]
        start = _random_date(date(2023, 1, 1), date(2024, 6, 30))
        end = start + timedelta(days=random.randint(365, 1825))
        lease_amt = float(_random_decimal(5000000, 200000000))
        months = max(1, (end - start).days // 30)
        monthly = lease_amt / months
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "lessor": random.choice(lessors),
            "lease_amount": f"{lease_amt:.2f}",
            "monthly_payment": f"{monthly:.2f}",
            "start_date": str(start),
            "end_date": str(end),
        }

    # ── 决策风险域 ──────────────────────────────────────────────────────

    def _gen_credit_line(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        limit_val = float(_random_decimal(10000000, 1000000000))
        if dist == Distribution.NORMAL:
            used_ratio = random.uniform(0.3, 0.6)
        elif dist == Distribution.WARNING:
            used_ratio = random.uniform(0.7, 0.85)
        else:
            used_ratio = random.uniform(0.9, 0.99)
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "bank_code": random.choice(BANK_CODES),
            "credit_limit": f"{limit_val:.2f}",
            "used_amount": f"{limit_val * used_ratio:.2f}",
            "expire_date": str(_random_date(date(2025, 1, 1), date(2026, 12, 31))),
        }

    def _gen_guarantee(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        entities_pair = random.sample(SUB_ENTITIES, 2)
        guarantee_types = ["general", "joint", "pledge", "mortgage"]
        start = _random_date(date(2024, 1, 1), date(2024, 6, 30))
        end = start + timedelta(days=random.randint(180, 730))
        return {
            "id": _uuid(),
            "guarantor_id": entities_pair[0].id,
            "beneficiary_id": entities_pair[1].id,
            "amount": _random_decimal(5000000, 500000000),
            "guarantee_type": random.choice(guarantee_types),
            "start_date": str(start),
            "end_date": str(end),
        }

    def _gen_related_transaction(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        entities_pair = random.sample(SUB_ENTITIES, 2)
        txn_types = ["purchase", "sale", "loan", "guarantee", "lease", "service"]
        return {
            "id": _uuid(),
            "entity_a_id": entities_pair[0].id,
            "entity_b_id": entities_pair[1].id,
            "amount": _random_decimal(100000, 100000000),
            "transaction_type": random.choice(txn_types),
            "transaction_date": str(_random_date()),
        }

    def _gen_derivative(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        instrument_types = ["interest_rate_swap", "fx_forward", "fx_option", "commodity_future"]
        notional = float(_random_decimal(10000000, 500000000))
        # 市值偏离
        if dist == Distribution.NORMAL:
            mv_ratio = random.uniform(0.95, 1.05)
        elif dist == Distribution.WARNING:
            mv_ratio = random.uniform(0.80, 0.90)
        else:
            mv_ratio = random.uniform(0.50, 0.70)
        return {
            "id": _uuid(),
            "entity_id": entity.id,
            "instrument_type": random.choice(instrument_types),
            "notional_amount": f"{notional:.2f}",
            "market_value": f"{notional * mv_ratio:.2f}",
            "maturity_date": str(_random_date(date(2025, 1, 1), date(2027, 12, 31))),
        }

    # ── 国资委考核域 ────────────────────────────────────────────────────

    def _gen_financial_report(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        """每个实体一条"""
        # 按实体索引分配
        ent = self.entities[idx % len(self.entities)]
        total_asset = float(_random_decimal(1000000000, 50000000000))
        net_asset = total_asset * random.uniform(0.3, 0.6)
        revenue = float(_random_decimal(500000000, 10000000000))
        profit = revenue * random.uniform(0.05, 0.15)
        rd = revenue * random.uniform(0.02, 0.08)
        return {
            "id": _uuid(),
            "entity_id": ent.id,
            "report_type": "annual",
            "period": "2024",
            "total_asset": f"{total_asset:.2f}",
            "net_asset": f"{net_asset:.2f}",
            "revenue": f"{revenue:.2f}",
            "profit": f"{profit:.2f}",
            "rd_expense": f"{rd:.2f}",
            "employee_count": random.randint(500, 50000),
            "operating_cash_flow": _random_decimal(100000000, 5000000000),
        }

    def _gen_assessment_indicator(self, entity: Entity, idx: int, dist: Distribution) -> dict:
        """每个实体 9 条考核指标"""
        ent_idx = idx // len(ASSESSMENT_INDICATORS)
        ind_idx = idx % len(ASSESSMENT_INDICATORS)
        ent = self.entities[ent_idx % len(self.entities)]
        code, name = ASSESSMENT_INDICATORS[ind_idx]
        target = float(_random_decimal(0.05, 0.20, 4))
        if dist == Distribution.NORMAL:
            actual = target * random.uniform(1.0, 1.3)
        elif dist == Distribution.WARNING:
            actual = target * random.uniform(0.85, 0.99)
        else:
            actual = target * random.uniform(0.50, 0.80)
        return {
            "id": _uuid(),
            "entity_id": ent.id,
            "indicator_code": code,
            "indicator_name": name,
            "target_value": f"{target:.4f}",
            "actual_value": f"{actual:.4f}",
            "period": "2024",
        }


# ---------------------------------------------------------------------------
# SQL 生成器
# ---------------------------------------------------------------------------

def _col_type_for_ddl(col: ColumnDef) -> str:
    """提取纯数据类型（去掉 DEFAULT / NOT NULL 等约束，用于 DDL 列定义）"""
    return col.data_type


def generate_ddl(table: TableDef) -> str:
    """生成 CREATE TABLE + COMMENT 语句（PostgreSQL 语法）"""
    lines = [f"CREATE TABLE {table.name} ("]
    col_lines = []
    for col in table.columns:
        col_lines.append(f"    {col.name} {col.data_type}")
    lines.append(",\n".join(col_lines))
    lines.append(");")
    ddl = "\n".join(lines)

    # 表级 COMMENT
    ddl += f"\nCOMMENT ON TABLE {table.name} IS '{table.comment}';"

    # 列级 COMMENT
    for col in table.columns:
        ddl += f"\nCOMMENT ON COLUMN {table.name}.{col.name} IS '{col.comment}';"

    return ddl


def _sql_value(val) -> str:
    """将 Python 值转为 SQL 字面量"""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return f"{val}"
    # 字符串类型：转义单引号
    s = str(val)
    s = s.replace("'", "''")
    return f"'{s}'"


def generate_insert(table: TableDef, rows: list[dict]) -> str:
    """生成 INSERT 语句"""
    if not rows:
        return f"-- {table.name}: 无数据\n"

    col_names = [col.name for col in table.columns]
    header = f"INSERT INTO {table.name} ({', '.join(col_names)}) VALUES"
    value_lines = []
    for row in rows:
        vals = [_sql_value(row.get(c)) for c in col_names]
        value_lines.append(f"({', '.join(vals)})")

    return header + "\n" + ",\n".join(value_lines) + ";\n"


# ---------------------------------------------------------------------------
# 文件输出
# ---------------------------------------------------------------------------

# 域名称映射（用于 SQL 文件头注释）
DOMAIN_NAMES: dict[str, str] = {
    "01_bank_account": "银行账户域",
    "02_fund_concentration": "资金集中域",
    "03_settlement": "结算域",
    "04_bill": "票据域",
    "05_debt_financing": "债务融资域",
    "06_risk_decision": "决策风险域",
    "07_sasoe_assessment": "国资委考核域",
}


def write_files(
    ddl_dir: Path,
    data_dir: Path,
    domain_tables: dict[str, list[TableDef]],
    factory: TestDataFactory,
) -> None:
    """生成所有 DDL 和 INSERT 文件"""
    os.makedirs(ddl_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    all_ddl_parts: list[str] = []
    all_insert_parts: list[str] = []

    for domain_key, tables in domain_tables.items():
        domain_name = DOMAIN_NAMES.get(domain_key, domain_key)
        ddl_content = f"-- {domain_name}\n-- 自动生成，请勿手动修改\n\n"
        data_content = f"-- {domain_name} 测试数据\n-- 自动生成，请勿手动修改\n\n"

        for table in tables:
            # DDL
            ddl_sql = generate_ddl(table)
            ddl_content += ddl_sql + "\n\n"

            # 数据
            count = TABLE_ROW_COUNTS.get(table.name, 10)
            rows = factory.generate(table, count)
            insert_sql = generate_insert(table, rows)
            data_content += insert_sql + "\n"

        # 写入域 DDL 文件
        ddl_file = ddl_dir / f"{domain_key}.sql"
        ddl_file.write_text(ddl_content, encoding="utf-8")
        print(f"  ✓ DDL:  {ddl_file}")

        # 写入域数据文件
        data_file = data_dir / f"{domain_key}_data.sql"
        data_file.write_text(data_content, encoding="utf-8")
        print(f"  ✓ DATA: {data_file}")

        all_ddl_parts.append(ddl_content)
        all_insert_parts.append(data_content)

    # 合并文件：DDL + INSERT
    all_file = ddl_dir / "all_tables.sql"
    all_content = "-- 全部表结构与测试数据（合并文件）\n"
    all_content += "-- 自动生成，请勿手动修改\n\n"
    all_content += "-- ============ DDL ============\n\n"
    all_content += "\n".join(all_ddl_parts)
    all_content += "\n-- ============ INSERT DATA ============\n\n"
    all_content += "\n".join(all_insert_parts)
    all_file.write_text(all_content, encoding="utf-8")
    print(f"  ✓ ALL:  {all_file}")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main() -> None:
    """脚本入口"""
    print("=" * 60)
    print("端到端测试数据生成器")
    print("=" * 60)

    # 固定随机种子，确保可重复
    random.seed(42)

    # 输出目录（相对于项目根目录）
    project_root = Path(__file__).resolve().parent.parent
    ddl_dir = project_root / "backend" / "tests" / "fixtures" / "ddl"
    data_dir = project_root / "backend" / "tests" / "fixtures" / "data"

    print(f"\n输出目录:")
    print(f"  DDL:  {ddl_dir}")
    print(f"  DATA: {data_dir}")
    print()

    # 创建数据工厂
    factory = TestDataFactory(ENTITY_HIERARCHY)

    # 生成文件
    write_files(ddl_dir, data_dir, DOMAIN_TABLES, factory)

    print(f"\n{'=' * 60}")
    print("生成完成！")
    print(f"  DDL 文件数:  {len(DOMAIN_TABLES) + 1} (含 all_tables.sql)")
    print(f"  数据文件数:  {len(DOMAIN_TABLES)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
