-- 全部表结构与测试数据（合并文件）
-- 自动生成，请勿手动修改

-- ============ DDL ============

-- 银行账户域
-- 自动生成，请勿手动修改

CREATE TABLE direct_linked_account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    bank_code VARCHAR(20),
    acct_no VARCHAR(50) NOT NULL,
    balance DECIMAL(18,2),
    currency CHAR(3) DEFAULT 'CNY',
    is_active BOOLEAN DEFAULT true,
    ukey_status VARCHAR(20) DEFAULT 'configured',
    status_6311 VARCHAR(20),
    is_restricted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE direct_linked_account IS '直联账户表';
COMMENT ON COLUMN direct_linked_account.id IS '主键';
COMMENT ON COLUMN direct_linked_account.entity_id IS '法人实体ID';
COMMENT ON COLUMN direct_linked_account.bank_code IS '银行编码';
COMMENT ON COLUMN direct_linked_account.acct_no IS '账号';
COMMENT ON COLUMN direct_linked_account.balance IS '余额';
COMMENT ON COLUMN direct_linked_account.currency IS '币种';
COMMENT ON COLUMN direct_linked_account.is_active IS '是否活跃';
COMMENT ON COLUMN direct_linked_account.ukey_status IS 'UKey状态';
COMMENT ON COLUMN direct_linked_account.status_6311 IS '6311受限状态';
COMMENT ON COLUMN direct_linked_account.is_restricted IS '是否受限';
COMMENT ON COLUMN direct_linked_account.created_at IS '创建时间';

CREATE TABLE internal_deposit_account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    pool_id VARCHAR(50),
    balance DECIMAL(18,2),
    interest_rate DECIMAL(5,4),
    maturity_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE internal_deposit_account IS '内部存款账户表';
COMMENT ON COLUMN internal_deposit_account.id IS '主键';
COMMENT ON COLUMN internal_deposit_account.entity_id IS '法人实体ID';
COMMENT ON COLUMN internal_deposit_account.pool_id IS '资金池ID';
COMMENT ON COLUMN internal_deposit_account.balance IS '余额';
COMMENT ON COLUMN internal_deposit_account.interest_rate IS '利率';
COMMENT ON COLUMN internal_deposit_account.maturity_date IS '到期日';
COMMENT ON COLUMN internal_deposit_account.created_at IS '创建时间';

CREATE TABLE restricted_account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    acct_no VARCHAR(50),
    restriction_type VARCHAR(50),
    status_6311 VARCHAR(20),
    frozen_amount DECIMAL(18,2),
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE restricted_account IS '受限账户表';
COMMENT ON COLUMN restricted_account.id IS '主键';
COMMENT ON COLUMN restricted_account.entity_id IS '法人实体ID';
COMMENT ON COLUMN restricted_account.acct_no IS '账号';
COMMENT ON COLUMN restricted_account.restriction_type IS '受限类型';
COMMENT ON COLUMN restricted_account.status_6311 IS '6311受限状态';
COMMENT ON COLUMN restricted_account.frozen_amount IS '冻结金额';
COMMENT ON COLUMN restricted_account.created_at IS '创建时间';


-- 资金集中域
-- 自动生成，请勿手动修改

CREATE TABLE cash_pool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    pool_name VARCHAR(100),
    total_balance DECIMAL(18,2),
    concentration_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE cash_pool IS '资金池表';
COMMENT ON COLUMN cash_pool.id IS '主键';
COMMENT ON COLUMN cash_pool.entity_id IS '法人实体ID';
COMMENT ON COLUMN cash_pool.pool_name IS '资金池名称';
COMMENT ON COLUMN cash_pool.total_balance IS '总余额';
COMMENT ON COLUMN cash_pool.concentration_rate IS '集中率';
COMMENT ON COLUMN cash_pool.created_at IS '创建时间';

CREATE TABLE collection_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id VARCHAR(50) NOT NULL,
    source_acct VARCHAR(50),
    amount DECIMAL(18,2),
    collection_date DATE,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE collection_record IS '归集记录表';
COMMENT ON COLUMN collection_record.id IS '主键';
COMMENT ON COLUMN collection_record.pool_id IS '资金池ID';
COMMENT ON COLUMN collection_record.source_acct IS '来源账户';
COMMENT ON COLUMN collection_record.amount IS '归集金额';
COMMENT ON COLUMN collection_record.collection_date IS '归集日期';
COMMENT ON COLUMN collection_record.status IS '状态';
COMMENT ON COLUMN collection_record.created_at IS '创建时间';


-- 结算域
-- 自动生成，请勿手动修改

CREATE TABLE settlement_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    channel VARCHAR(30) NOT NULL,
    amount DECIMAL(18,2),
    currency CHAR(3) DEFAULT 'CNY',
    counterparty VARCHAR(100),
    is_cross_bank BOOLEAN DEFAULT false,
    is_cross_border BOOLEAN DEFAULT false,
    is_internal BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'settled',
    settled_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE settlement_record IS '结算记录表';
COMMENT ON COLUMN settlement_record.id IS '主键';
COMMENT ON COLUMN settlement_record.entity_id IS '法人实体ID';
COMMENT ON COLUMN settlement_record.channel IS '结算渠道';
COMMENT ON COLUMN settlement_record.amount IS '结算金额';
COMMENT ON COLUMN settlement_record.currency IS '币种';
COMMENT ON COLUMN settlement_record.counterparty IS '交易对手';
COMMENT ON COLUMN settlement_record.is_cross_bank IS '是否跨行';
COMMENT ON COLUMN settlement_record.is_cross_border IS '是否跨境';
COMMENT ON COLUMN settlement_record.is_internal IS '是否内部';
COMMENT ON COLUMN settlement_record.status IS '结算状态';
COMMENT ON COLUMN settlement_record.settled_at IS '结算时间';

CREATE TABLE payment_channel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_name VARCHAR(50),
    channel_type VARCHAR(30),
    is_direct_linked BOOLEAN DEFAULT true,
    daily_limit DECIMAL(18,2)
);
COMMENT ON TABLE payment_channel IS '支付渠道表';
COMMENT ON COLUMN payment_channel.id IS '主键';
COMMENT ON COLUMN payment_channel.channel_name IS '渠道名称';
COMMENT ON COLUMN payment_channel.channel_type IS '渠道类型';
COMMENT ON COLUMN payment_channel.is_direct_linked IS '是否直联';
COMMENT ON COLUMN payment_channel.daily_limit IS '日限额';


-- 票据域
-- 自动生成，请勿手动修改

CREATE TABLE bill (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    bill_type VARCHAR(30) NOT NULL,
    face_value DECIMAL(18,2),
    issue_date DATE,
    maturity_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    is_overdue BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE bill IS '票据表';
COMMENT ON COLUMN bill.id IS '主键';
COMMENT ON COLUMN bill.entity_id IS '法人实体ID';
COMMENT ON COLUMN bill.bill_type IS '票据类型';
COMMENT ON COLUMN bill.face_value IS '票面金额';
COMMENT ON COLUMN bill.issue_date IS '出票日期';
COMMENT ON COLUMN bill.maturity_date IS '到期日';
COMMENT ON COLUMN bill.status IS '状态';
COMMENT ON COLUMN bill.is_overdue IS '是否逾期';
COMMENT ON COLUMN bill.created_at IS '创建时间';

CREATE TABLE endorsement_chain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id VARCHAR(50) NOT NULL,
    endorser_id VARCHAR(50),
    endorsee_id VARCHAR(50),
    endorse_date DATE,
    sequence_no INTEGER
);
COMMENT ON TABLE endorsement_chain IS '背书链表';
COMMENT ON COLUMN endorsement_chain.id IS '主键';
COMMENT ON COLUMN endorsement_chain.bill_id IS '票据ID';
COMMENT ON COLUMN endorsement_chain.endorser_id IS '背书人ID';
COMMENT ON COLUMN endorsement_chain.endorsee_id IS '被背书人ID';
COMMENT ON COLUMN endorsement_chain.endorse_date IS '背书日期';
COMMENT ON COLUMN endorsement_chain.sequence_no IS '背书序号';


-- 债务融资域
-- 自动生成，请勿手动修改

CREATE TABLE loan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    bank_code VARCHAR(20),
    principal DECIMAL(18,2),
    interest_rate DECIMAL(5,4),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);
COMMENT ON TABLE loan IS '贷款表';
COMMENT ON COLUMN loan.id IS '主键';
COMMENT ON COLUMN loan.entity_id IS '法人实体ID';
COMMENT ON COLUMN loan.bank_code IS '银行编码';
COMMENT ON COLUMN loan.principal IS '本金';
COMMENT ON COLUMN loan.interest_rate IS '利率';
COMMENT ON COLUMN loan.start_date IS '起始日';
COMMENT ON COLUMN loan.end_date IS '到期日';
COMMENT ON COLUMN loan.status IS '状态';

CREATE TABLE bond (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    bond_code VARCHAR(30),
    face_value DECIMAL(18,2),
    coupon_rate DECIMAL(5,4),
    maturity_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);
COMMENT ON TABLE bond IS '债券表';
COMMENT ON COLUMN bond.id IS '主键';
COMMENT ON COLUMN bond.entity_id IS '法人实体ID';
COMMENT ON COLUMN bond.bond_code IS '债券代码';
COMMENT ON COLUMN bond.face_value IS '面值';
COMMENT ON COLUMN bond.coupon_rate IS '票面利率';
COMMENT ON COLUMN bond.maturity_date IS '到期日';
COMMENT ON COLUMN bond.status IS '状态';

CREATE TABLE finance_lease (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    lessor VARCHAR(100),
    lease_amount DECIMAL(18,2),
    monthly_payment DECIMAL(18,2),
    start_date DATE,
    end_date DATE
);
COMMENT ON TABLE finance_lease IS '融资租赁表';
COMMENT ON COLUMN finance_lease.id IS '主键';
COMMENT ON COLUMN finance_lease.entity_id IS '法人实体ID';
COMMENT ON COLUMN finance_lease.lessor IS '出租方';
COMMENT ON COLUMN finance_lease.lease_amount IS '租赁金额';
COMMENT ON COLUMN finance_lease.monthly_payment IS '月付金额';
COMMENT ON COLUMN finance_lease.start_date IS '起始日';
COMMENT ON COLUMN finance_lease.end_date IS '到期日';


-- 决策风险域
-- 自动生成，请勿手动修改

CREATE TABLE credit_line (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    bank_code VARCHAR(20),
    credit_limit DECIMAL(18,2),
    used_amount DECIMAL(18,2),
    expire_date DATE
);
COMMENT ON TABLE credit_line IS '授信表';
COMMENT ON COLUMN credit_line.id IS '主键';
COMMENT ON COLUMN credit_line.entity_id IS '法人实体ID';
COMMENT ON COLUMN credit_line.bank_code IS '银行编码';
COMMENT ON COLUMN credit_line.credit_limit IS '授信额度';
COMMENT ON COLUMN credit_line.used_amount IS '已用额度';
COMMENT ON COLUMN credit_line.expire_date IS '到期日';

CREATE TABLE guarantee (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guarantor_id VARCHAR(50) NOT NULL,
    beneficiary_id VARCHAR(50),
    amount DECIMAL(18,2),
    guarantee_type VARCHAR(30),
    start_date DATE,
    end_date DATE
);
COMMENT ON TABLE guarantee IS '担保表';
COMMENT ON COLUMN guarantee.id IS '主键';
COMMENT ON COLUMN guarantee.guarantor_id IS '担保人ID';
COMMENT ON COLUMN guarantee.beneficiary_id IS '受益人ID';
COMMENT ON COLUMN guarantee.amount IS '担保金额';
COMMENT ON COLUMN guarantee.guarantee_type IS '担保类型';
COMMENT ON COLUMN guarantee.start_date IS '起始日';
COMMENT ON COLUMN guarantee.end_date IS '到期日';

CREATE TABLE related_transaction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_a_id VARCHAR(50) NOT NULL,
    entity_b_id VARCHAR(50) NOT NULL,
    amount DECIMAL(18,2),
    transaction_type VARCHAR(30),
    transaction_date DATE
);
COMMENT ON TABLE related_transaction IS '关联交易表';
COMMENT ON COLUMN related_transaction.id IS '主键';
COMMENT ON COLUMN related_transaction.entity_a_id IS '交易方A';
COMMENT ON COLUMN related_transaction.entity_b_id IS '交易方B';
COMMENT ON COLUMN related_transaction.amount IS '交易金额';
COMMENT ON COLUMN related_transaction.transaction_type IS '交易类型';
COMMENT ON COLUMN related_transaction.transaction_date IS '交易日期';

CREATE TABLE derivative (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    instrument_type VARCHAR(30),
    notional_amount DECIMAL(18,2),
    market_value DECIMAL(18,2),
    maturity_date DATE
);
COMMENT ON TABLE derivative IS '衍生品表';
COMMENT ON COLUMN derivative.id IS '主键';
COMMENT ON COLUMN derivative.entity_id IS '法人实体ID';
COMMENT ON COLUMN derivative.instrument_type IS '工具类型';
COMMENT ON COLUMN derivative.notional_amount IS '名义金额';
COMMENT ON COLUMN derivative.market_value IS '市值';
COMMENT ON COLUMN derivative.maturity_date IS '到期日';


-- 国资委考核域
-- 自动生成，请勿手动修改

CREATE TABLE financial_report (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    report_type VARCHAR(30),
    period VARCHAR(10),
    total_asset DECIMAL(18,2),
    net_asset DECIMAL(18,2),
    revenue DECIMAL(18,2),
    profit DECIMAL(18,2),
    rd_expense DECIMAL(18,2),
    employee_count INTEGER,
    operating_cash_flow DECIMAL(18,2)
);
COMMENT ON TABLE financial_report IS '财务报表表';
COMMENT ON COLUMN financial_report.id IS '主键';
COMMENT ON COLUMN financial_report.entity_id IS '法人实体ID';
COMMENT ON COLUMN financial_report.report_type IS '报表类型';
COMMENT ON COLUMN financial_report.period IS '报告期';
COMMENT ON COLUMN financial_report.total_asset IS '总资产';
COMMENT ON COLUMN financial_report.net_asset IS '净资产';
COMMENT ON COLUMN financial_report.revenue IS '营业收入';
COMMENT ON COLUMN financial_report.profit IS '利润';
COMMENT ON COLUMN financial_report.rd_expense IS '研发费用';
COMMENT ON COLUMN financial_report.employee_count IS '员工人数';
COMMENT ON COLUMN financial_report.operating_cash_flow IS '经营性现金流';

CREATE TABLE assessment_indicator (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) NOT NULL,
    indicator_code VARCHAR(10),
    indicator_name VARCHAR(100),
    target_value DECIMAL(18,4),
    actual_value DECIMAL(18,4),
    period VARCHAR(10)
);
COMMENT ON TABLE assessment_indicator IS '考核指标表';
COMMENT ON COLUMN assessment_indicator.id IS '主键';
COMMENT ON COLUMN assessment_indicator.entity_id IS '法人实体ID';
COMMENT ON COLUMN assessment_indicator.indicator_code IS '指标编码';
COMMENT ON COLUMN assessment_indicator.indicator_name IS '指标名称';
COMMENT ON COLUMN assessment_indicator.target_value IS '目标值';
COMMENT ON COLUMN assessment_indicator.actual_value IS '实际值';
COMMENT ON COLUMN assessment_indicator.period IS '考核期';


-- ============ INSERT DATA ============

-- 银行账户域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO direct_linked_account (id, entity_id, bank_code, acct_no, balance, currency, is_active, ukey_status, status_6311, is_restricted, created_at) VALUES
('4ac699f7-2e9b-4b03-849c-635b1d19a555', 'test_sub_north_a', 'BOC', '6222****5506', '244967364.62', 'CNY', true, 'configured', NULL, false, '2024-03-12 23:06:43'),
('fbc3d1c6-dd42-4336-aaae-022fd196f2a5', 'test_sub_north_a', 'SPDB', '6222****7912', '31879501.21', 'CNY', true, 'configured', NULL, false, '2024-02-17 06:14:32'),
('b1b01d9f-3788-4b2c-9db9-429e0e79355e', 'test_sub_north_a', 'ICBC', '6228****9928', '419577868.98', 'CNY', true, 'configured', NULL, false, '2024-08-17 18:17:51'),
('a021e6d0-8c4d-488d-ba89-5d26d0a7bc00', 'test_sub_east_a', 'CCB', '6225****6574', '277943554.54', 'CNY', true, 'configured', NULL, false, '2024-04-20 10:06:05'),
('52641144-d975-4812-8204-1879ab028ac2', 'test_sub_east_b', 'BOC', '6217****6635', '603765658.76', 'CNY', true, 'configured', NULL, false, '2024-01-23 23:29:34'),
('bec16507-cdc8-4171-ad3e-e58353d63a4d', 'test_sub_east_a', 'CITIC', '6222****5803', '829421723.79', 'CNY', true, 'configured', NULL, false, '2024-11-12 11:36:12'),
('4ffe9fc6-69ee-4121-812a-c2020ca98adb', 'test_sub_north_a', 'BOC', '6222****4733', '773091033.95', 'CNY', true, 'configured', NULL, false, '2024-02-10 07:55:06'),
('635286e3-e430-4bb3-847f-d1bdfb0c1713', 'test_sub_east_b', 'BOCOM', '6225****6977', '162737831.75', 'CNY', true, 'configured', NULL, false, '2024-06-30 06:42:17'),
('0e50cc49-0588-426d-ab4b-dfe464c6c856', 'test_sub_north_a', 'BOC', '6228****9751', '729153885.27', 'CNY', true, 'configured', NULL, false, '2024-03-24 14:24:17'),
('f48afd48-068f-4213-a13b-8ca266d90920', 'test_sub_north_a', 'SPDB', '6228****6313', '842867635.00', 'CNY', true, 'configured', NULL, false, '2024-01-29 07:52:02'),
('368c2ab2-d6d4-4108-ba3b-de91fb319d17', 'test_sub_east_b', 'CITIC', '6217****2084', '211061745.30', 'CNY', true, 'configured', NULL, false, '2024-10-17 22:20:13'),
('4fa3ae3b-bdaa-4a23-b2e5-0833bfb7d182', 'test_sub_north_a', 'CEB', '6225****8517', '142957303.28', 'CNY', true, 'configured', NULL, false, '2024-03-12 07:47:35'),
('13b9c3a5-36fb-495e-9efc-dc62cfeab305', 'test_sub_north_a', 'BOCOM', '6225****7543', '362060244.07', 'CNY', true, 'configured', NULL, false, '2024-03-11 16:31:05'),
('329f1e59-a642-4e79-92e1-84488278d6da', 'test_sub_east_a', 'BOC', '6228****3621', '792100156.43', 'CNY', true, 'configured', NULL, false, '2024-08-04 19:04:24'),
('5cde1e5e-007c-41ee-afed-18a9c1706cab', 'test_sub_east_b', 'CEB', '6217****1188', '680315381.92', 'CNY', true, 'configured', NULL, false, '2024-02-28 21:56:34'),
('739d9828-08e0-4f73-9e9e-926f1525eeff', 'test_sub_east_b', 'CMB', '6222****5808', '434821774.14', 'CNY', true, 'configured', NULL, false, '2024-08-20 00:46:56'),
('66314318-14ea-4317-8fdd-d3a3ec94273e', 'test_sub_north_a', 'BOCOM', '6228****9317', '912636576.56', 'CNY', true, 'configured', NULL, false, '2024-11-16 09:53:40'),
('9f27ef9d-4f93-48c7-a1e5-b0e2b40091c7', 'test_sub_north_a', 'ABC', '6228****7126', '762534549.00', 'CNY', true, 'configured', NULL, false, '2024-10-03 16:58:00'),
('b856f5d4-54d8-424c-9061-a79b9a975c45', 'test_sub_north_a', 'CMB', '6225****1319', '111956538.55', 'CNY', true, 'configured', NULL, false, '2024-07-04 09:15:03'),
('4c6456d1-e5d4-463f-b4d2-4378f9bf31ed', 'test_sub_east_a', 'BOC', '6222****8962', '816041651.09', 'CNY', true, 'configured', NULL, false, '2024-09-29 04:08:42'),
('540ee8bc-c079-401f-9203-559616e5da87', 'test_sub_east_b', 'SPDB', '6228****5342', '527721020.04', 'CNY', true, 'configured', NULL, false, '2024-11-06 13:13:59'),
('5266832d-7b2d-49a0-8ee2-dcbc6bd583a4', 'test_sub_north_a', 'ABC', '6217****7537', '995149841.73', 'CNY', true, 'configured', NULL, false, '2024-11-28 11:28:57'),
('46ec1537-c4ed-4240-9769-1d8f01f8b576', 'test_sub_north_a', 'CEB', '6222****5061', '224774867.30', 'CNY', true, 'configured', NULL, false, '2024-06-22 00:37:35'),
('90ba62ca-1cf1-4ab3-b539-de01d111c08c', 'test_sub_east_a', 'ABC', '6222****2163', '707870162.45', 'CNY', true, 'configured', NULL, false, '2024-01-31 07:04:57'),
('4c3f116a-422b-4856-8df7-91554e6870fa', 'test_sub_east_a', 'CMB', '6222****9423', '238080833.91', 'CNY', true, 'configured', NULL, false, '2024-12-08 15:13:34'),
('a9d3d64e-dd1e-47b1-acbe-47035c750fea', 'test_sub_east_a', 'CEB', '6228****8749', '807516248.07', 'CNY', true, 'configured', NULL, false, '2024-04-07 03:06:42'),
('c5dd61b3-5932-4fe6-8662-6c7ac64f709c', 'test_sub_east_b', 'CMB', '6225****7735', '467077965.57', 'CNY', true, 'configured', NULL, false, '2024-01-28 21:41:41'),
('748de407-908b-4463-895e-29914f0a321a', 'test_sub_east_a', 'ICBC', '6225****6559', '800612451.61', 'CNY', true, 'configured', NULL, false, '2024-02-25 07:12:12'),
('6c5e3791-93d4-4c0d-b9b7-dff0cd885563', 'test_sub_north_a', 'CEB', '6228****7912', '183569686.98', 'CNY', true, 'configured', NULL, false, '2024-08-24 07:55:59'),
('0ff06673-7a96-46f9-a9a0-49f387923cc0', 'test_sub_east_a', 'CEB', '6222****1828', '652179679.51', 'CNY', true, 'configured', NULL, false, '2024-10-03 00:05:59'),
('9da88e23-48e4-4e15-b62c-e402b159cfb9', 'test_sub_east_a', 'CCB', '6225****8956', '481410282.13', 'CNY', true, 'configured', NULL, false, '2024-07-24 01:10:24'),
('0838553f-d188-424f-a3fe-42f8aa3576f6', 'test_sub_east_a', 'CITIC', '6217****8454', '285320704.02', 'CNY', true, 'configured', NULL, false, '2024-12-22 23:50:35'),
('559b2c36-7f1f-464c-ba97-a63d7490bb1b', 'test_sub_north_a', 'CEB', '6228****4111', '296778154.71', 'CNY', true, 'configured', NULL, false, '2024-01-30 18:47:34'),
('c166d53e-5d54-4019-827e-edd3e72ef33d', 'test_sub_east_a', 'CMB', '6222****1821', '584219176.70', 'CNY', true, 'configured', NULL, false, '2024-09-14 16:10:03'),
('41ede4fe-05e7-4314-8a14-bb2fe53337b6', 'test_sub_north_a', 'BOC', '6228****2122', '595075602.94', 'CNY', true, 'configured', NULL, false, '2024-12-11 07:25:07'),
('5cdaad0f-3890-47a0-9a44-15d3cf8a84c0', 'test_sub_north_a', 'ABC', '6222****2343', '419282992.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-25 18:33:20'),
('a06bdd11-7167-4e48-86f6-03d97c1c0469', 'test_sub_east_b', 'ABC', '6217****4910', '265687951.08', 'CNY', true, 'unconfigured', NULL, false, '2024-03-08 21:41:19'),
('b6ed1811-e51a-48b1-8365-8ae07ee8b347', 'test_sub_east_b', 'CMB', '6222****1152', '458339694.07', 'CNY', true, 'unconfigured', NULL, false, '2024-10-15 03:04:34'),
('7472f296-9c34-49e5-a194-962ce7c72b18', 'test_sub_east_a', 'SPDB', '6217****3170', '933266052.06', 'CNY', true, 'unconfigured', NULL, false, '2024-02-05 07:23:18'),
('57aa83d9-2f33-4345-84e6-35f525015cd8', 'test_sub_east_a', 'CEB', '6217****9666', '7922324.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 09:59:42'),
('21a5d6e8-a3a4-48e9-baa8-3bc03d4fc2b5', 'test_sub_east_a', 'CCB', '6217****2891', '889723735.74', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 04:17:18'),
('0eb6346c-4f4f-471a-8338-82600d0662bd', 'test_sub_north_a', 'ABC', '6217****4335', '687528379.09', 'CNY', true, 'unconfigured', NULL, false, '2024-05-15 16:31:16'),
('16cbbca3-78b1-409c-8192-569861211b69', 'test_sub_east_a', 'BOC', '6225****5533', '44182353.12', 'CNY', true, 'unconfigured', NULL, false, '2024-06-19 04:40:16'),
('0f812cd6-ea63-4a1a-a389-3f61c49e65bd', 'test_sub_east_a', 'CEB', '6225****1158', '111962693.20', 'CNY', true, 'unconfigured', NULL, false, '2024-12-19 04:34:02'),
('addf8dad-024c-474c-81fb-40565932baf8', 'test_sub_east_b', 'SPDB', '6228****8041', '127532774.73', 'CNY', true, 'unconfigured', NULL, false, '2024-06-06 11:57:59'),
('b5d4750d-5efc-4a9c-8179-76a6a26d17a7', 'test_sub_east_a', 'CMB', '6228****5088', '666966717.29', 'CNY', false, 'configured', NULL, false, '2024-06-30 17:56:55'),
('a1ac27b4-20db-44f2-936b-5be1379b0aeb', 'test_sub_east_b', 'CCB', '6228****3662', '976208412.33', 'CNY', false, 'configured', NULL, false, '2024-03-31 13:01:11'),
('4afac5dd-1cf7-456c-ab0e-2c82eb929446', 'test_sub_north_a', 'CMB', '6225****5065', '266879029.02', 'CNY', false, 'configured', NULL, false, '2024-12-25 03:24:55'),
('c41b8342-44af-4706-82d3-81feb27fb9ad', 'test_sub_east_a', 'CEB', '6228****4269', '816604946.94', 'CNY', false, 'configured', NULL, false, '2024-08-23 11:19:52'),
('bfe71b9a-47dd-4c74-b948-f1957bea5c51', 'test_sub_east_a', 'ABC', '6222****4164', '398526131.97', 'CNY', false, 'configured', NULL, false, '2024-05-22 02:49:17');

INSERT INTO internal_deposit_account (id, entity_id, pool_id, balance, interest_rate, maturity_date, created_at) VALUES
('3cc9b13f-7985-436b-a7a1-1bc2508752f9', 'test_sub_east_b', '2e38f3b5-ba9c-4204-a7dc-b1c104a976cf', '200139352.99', '0.0392', '2025-12-02', '2024-06-18 00:07:56'),
('11c874ca-e402-4866-821d-9053d243f501', 'test_sub_east_b', 'e35181ab-6ed6-449f-be44-18bff07a2053', '481285890.72', '0.0254', '2025-02-27', '2024-01-20 03:38:27'),
('cd19abf9-04e2-4285-8f05-b7e048efed38', 'test_sub_east_b', '4dda393c-bf64-4081-8ee5-b1a3c02f9ae6', '157181818.44', '0.0419', '2025-11-06', '2024-02-29 12:57:36'),
('796a00e8-e583-4bf8-b743-400b28b1967b', 'test_sub_east_a', '4a6ca2b8-ffb1-4aca-98d9-6a1c6bb26ff3', '354538249.28', '0.0276', '2024-06-02', '2024-09-23 17:43:46'),
('fec31651-0b5b-4046-9e05-d6a6cac05a00', 'test_sub_north_a', '28359c49-8006-4393-bebc-628713a886f7', '98919046.99', '0.0421', '2025-08-16', '2024-02-05 21:58:21'),
('fc104ae9-87e6-43a4-925a-82be9780a9dd', 'test_sub_north_a', '6f2e3bf1-8f1c-41c7-9cf4-463a62af538e', '424083632.11', '0.0294', '2025-04-04', '2024-09-16 09:42:26'),
('1b25e39b-0913-4d1f-a79d-71eda1abbdef', 'test_sub_east_b', '944eb2ea-fd69-4e76-9c91-2b7d19e53732', '148179773.66', '0.0321', '2024-10-09', '2024-04-08 13:42:24'),
('f03b63bb-52fa-4e64-9d55-3a48f4599883', 'test_sub_north_a', '4128279c-35e1-4cb2-ae7a-7c9baa382172', '87426657.93', '0.0150', '2025-04-05', '2024-07-26 17:53:00'),
('e43c75ed-5482-4178-941b-8f1bed34eff3', 'test_sub_east_b', '7c87d3ad-8545-4525-bf91-6768a12a9d69', '215229130.92', '0.0150', '2025-04-26', '2024-08-26 14:28:43'),
('1243ab6a-339e-4829-bebc-eb4262fd9ba1', 'test_sub_east_a', 'c858c5e7-59de-45b3-b016-82dbca794a9e', '396970831.85', '0.0080', '2024-11-21', '2024-12-03 02:18:32');

INSERT INTO restricted_account (id, entity_id, acct_no, restriction_type, status_6311, frozen_amount, created_at) VALUES
('ef3e1cf5-cd34-4909-91ce-b1a5cdfbb5bc', 'test_sub_north_a', '6217****2530', 'regulatory_hold', NULL, '33672503.96', '2024-04-25 06:09:01'),
('b729e3d0-b733-4d39-8504-39daa74e7f2f', 'test_sub_east_a', '6228****8784', 'judicial_freeze', NULL, '22825266.80', '2024-11-18 18:12:45'),
('730554e9-4d29-48ac-b2d2-d7a284afd5ba', 'test_sub_north_a', '6225****9099', 'escrow', NULL, '12274823.53', '2024-12-01 22:00:57'),
('1e152fd8-837b-46d7-9f8d-5c00a9a831d9', 'test_sub_east_a', '6225****4585', 'regulatory_hold', 'restricted', '40225081.82', '2024-12-22 16:29:03'),
('bc5cc2b3-8cc6-42d2-b3cd-4776eee38a30', 'test_sub_north_a', '6228****2988', 'escrow', 'restricted', '6753621.37', '2024-08-25 21:33:35');


-- 资金集中域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO cash_pool (id, entity_id, pool_name, total_balance, concentration_rate, created_at) VALUES
('0595f4d0-855b-4b42-a7ae-8d11b219959e', 'test_sub_north_a', '资金池_华北子公司A_1', '3778697567.64', '0.8476', '2024-08-14 19:52:46'),
('a2e6a99d-e38e-4f7d-b077-0b2227a42308', 'test_sub_north_a', '资金池_华北子公司A_2', '4535205104.98', '0.8640', '2024-08-16 05:47:55'),
('d8459795-c5f6-4b0b-8600-7cc38a5b5e18', 'test_sub_east_b', '资金池_华东子公司B_3', '3761366164.64', '0.8675', '2024-11-22 08:49:49'),
('d51498a2-4360-46f2-933f-dc5520eb3778', 'test_sub_north_a', '资金池_华北子公司A_4', '2428139115.18', '0.7200', '2024-05-02 08:28:04'),
('9574564a-ae53-4912-8ef2-769c90549292', 'test_sub_north_a', '资金池_华北子公司A_5', '1435783472.81', '0.6000', '2024-05-19 10:20:57');

INSERT INTO collection_record (id, pool_id, source_acct, amount, collection_date, status, created_at) VALUES
('6f223dda-a60e-4927-8b00-2c81e24ba5d6', '0595f4d0-855b-4b42-a7ae-8d11b219959e', '6228****3471', '23164584.90', '2024-12-21', 'completed', '2024-03-19 22:13:04'),
('80e77862-1832-442d-a955-dc1798ef0c50', 'd51498a2-4360-46f2-933f-dc5520eb3778', '6217****9890', '46619134.12', '2024-02-01', 'completed', '2024-04-15 13:24:57'),
('149b30ca-1725-4609-a3cf-84f5d859fd72', '0595f4d0-855b-4b42-a7ae-8d11b219959e', '6225****8814', '639313.55', '2024-06-29', 'completed', '2024-06-01 12:54:57'),
('1242bab5-128d-4196-8983-ce6344163ef7', '9574564a-ae53-4912-8ef2-769c90549292', '6228****8999', '21981192.38', '2024-08-11', 'completed', '2024-09-05 00:24:21'),
('8779fd80-d0a8-4137-a001-db28797641ab', 'd51498a2-4360-46f2-933f-dc5520eb3778', '6228****8657', '91958184.99', '2024-11-14', 'completed', '2024-09-30 00:58:25'),
('b6ef6b0e-da84-4889-9732-c4da06f971be', '9574564a-ae53-4912-8ef2-769c90549292', '6222****2375', '64292827.32', '2024-03-10', 'completed', '2024-08-24 05:03:16'),
('7c39b661-6d5f-4554-96fe-b72fe12e8c0a', 'd8459795-c5f6-4b0b-8600-7cc38a5b5e18', '6228****8449', '32718238.20', '2024-07-13', 'completed', '2024-05-22 13:16:53'),
('cef71c4d-07f2-4c7a-af6a-d15effba5042', 'd51498a2-4360-46f2-933f-dc5520eb3778', '6222****9837', '5255956.54', '2024-06-28', 'completed', '2024-04-24 20:04:49'),
('bae1ca7e-d5d5-4c1a-9e90-29bab2867eac', '0595f4d0-855b-4b42-a7ae-8d11b219959e', '6222****5051', '19976100.20', '2024-01-11', 'completed', '2024-11-14 04:15:08'),
('45b211d1-794c-4e9b-919d-4526d6929499', '0595f4d0-855b-4b42-a7ae-8d11b219959e', '6228****8619', '69961523.88', '2024-07-07', 'completed', '2024-03-26 19:38:47'),
('d3c2d114-c3bc-491e-b986-b043f7ff9787', '0595f4d0-855b-4b42-a7ae-8d11b219959e', '6228****6096', '10854470.03', '2024-01-14', 'completed', '2024-06-08 18:43:58'),
('ca9fe203-5d28-4384-b6ff-8b050aca75a1', 'd51498a2-4360-46f2-933f-dc5520eb3778', '6228****2245', '59230181.23', '2024-11-17', 'completed', '2024-05-04 03:44:49'),
('6414561e-38a8-404f-a329-809769f1c6b0', '9574564a-ae53-4912-8ef2-769c90549292', '6222****1672', '34753016.34', '2024-08-07', 'completed', '2024-12-04 11:04:32'),
('37c6d7a5-2026-4f43-a1e2-7a0bf1a40a0a', 'd8459795-c5f6-4b0b-8600-7cc38a5b5e18', '6222****7882', '82241975.26', '2024-02-24', 'completed', '2024-08-09 11:40:57'),
('3473dd14-09c6-4b8a-bf81-367707b5bf95', 'a2e6a99d-e38e-4f7d-b077-0b2227a42308', '6228****9548', '96549099.44', '2024-05-18', 'pending', '2024-11-11 17:49:30'),
('bb6a6533-23eb-4a89-9ed5-2dd49cb80248', 'd51498a2-4360-46f2-933f-dc5520eb3778', '6217****6280', '85178730.34', '2024-02-14', 'failed', '2024-05-22 14:15:48'),
('bfe0900c-fa9b-43eb-93f1-d3ea20bb7dc8', '9574564a-ae53-4912-8ef2-769c90549292', '6225****6511', '2918564.78', '2024-06-15', 'failed', '2024-04-03 15:13:22'),
('d5a5d961-1a66-4395-b085-4c2a93b2ef33', 'd8459795-c5f6-4b0b-8600-7cc38a5b5e18', '6217****1166', '51686893.81', '2024-04-07', 'pending', '2024-02-13 07:46:26'),
('99187de9-53c6-4914-b173-69bf3c2e3143', '9574564a-ae53-4912-8ef2-769c90549292', '6225****9041', '44845046.23', '2024-01-09', 'completed', '2024-02-17 09:14:25'),
('7d4422e6-ba10-4163-bb7c-3e96fe2c28a9', 'a2e6a99d-e38e-4f7d-b077-0b2227a42308', '6217****8753', '55369621.85', '2024-06-25', 'pending', '2024-08-05 23:35:21');


-- 结算域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO settlement_record (id, entity_id, channel, amount, currency, counterparty, is_cross_bank, is_cross_border, is_internal, status, settled_at) VALUES
('218d0ee4-150e-4142-a055-9dd846b1f34d', 'test_sub_east_b', 'bank_transfer', '35145718.56', 'CNY', '国电投资', true, false, false, 'settled', '2024-06-05 08:14:07'),
('325d8f10-d353-4aef-ab2f-fb61400e9510', 'test_sub_north_a', 'online_banking', '9637288.83', 'CNY', '华能集团', false, false, false, 'settled', '2024-10-01 22:11:12'),
('d35738c7-1f6c-44bd-bd75-0fe9d614f41e', 'test_sub_east_a', 'bill_payment', '36932846.63', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-28 16:38:18'),
('af2e338b-b308-42a7-ba3b-2fd5a0d106a2', 'test_sub_east_a', 'letter_of_credit', '41633091.88', 'USD', '中石化财务', false, true, false, 'settled', '2024-07-03 05:19:00'),
('15dab04a-9446-44bc-ae43-97768382ec38', 'test_sub_north_a', 'guarantee_payment', '26711413.11', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-24 01:35:18'),
('f980c7c6-8f37-4e94-a27e-30d446593f71', 'test_sub_north_a', 'collection', '47205039.84', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-22 00:36:18'),
('7bd21e13-2069-45a1-81f1-e565c7111d1f', 'test_sub_east_b', 'remittance', '23940923.29', 'CNY', '国电投资', true, false, false, 'settled', '2024-04-04 01:16:55'),
('a0f7feae-ec99-49db-9c62-b5f553380777', 'test_sub_east_b', 'entrusted_collection', '5713216.16', 'CNY', '华能集团', false, false, false, 'settled', '2024-07-24 15:04:36'),
('debf6943-d8d1-492f-8057-346a1a8cea73', 'test_sub_north_a', 'direct_debit', '34325686.40', 'CNY', '中石化财务', false, false, true, 'settled', '2024-03-17 18:19:05'),
('051d244e-6472-4cea-b4b5-78d67fbaae10', 'test_sub_east_a', 'bank_transfer', '5931393.59', 'CNY', '中铁建设', true, false, false, 'settled', '2024-11-06 19:50:39'),
('ffa6ab25-22f1-4402-8eca-d61bd4f5d8bb', 'test_sub_east_a', 'online_banking', '38786920.05', 'CNY', '中铁建设', false, false, false, 'settled', '2024-08-18 14:19:55'),
('9b65d7fe-cb6a-46fe-89bb-f384b6480a4d', 'test_sub_north_a', 'bill_payment', '49501662.71', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-18 19:03:39'),
('ff14aead-2e81-4892-85ea-fdd6d0e6ea4e', 'test_sub_north_a', 'letter_of_credit', '4970686.40', 'CNY', '中石化财务', false, true, false, 'settled', '2024-05-15 21:05:10'),
('1223cd64-309c-4576-ad07-34da5eef2741', 'test_sub_east_a', 'guarantee_payment', '8698939.28', 'CNY', '华能集团', false, false, false, 'settled', '2024-03-21 00:26:28'),
('9dc0a31a-2f5f-4f2c-a3ec-468ed4654ab6', 'test_sub_north_a', 'collection', '29694621.64', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-17 07:18:45'),
('542f1013-96e5-4206-8f58-2daf4a063f34', 'test_sub_east_b', 'remittance', '35152348.03', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-06 21:14:59'),
('2c497cf9-de0d-4275-b55c-94e33fa3dfa1', 'test_sub_east_b', 'entrusted_collection', '39393523.05', 'CNY', '中交集团', false, false, false, 'settled', '2024-12-04 06:27:07'),
('32fdd708-72a6-4cc2-acd1-f13805120f16', 'test_sub_north_a', 'direct_debit', '11248224.42', 'CNY', '中石化财务', false, false, true, 'settled', '2024-05-16 04:04:03'),
('e1ae6703-10e1-4bf6-8a35-7a13eba6bca4', 'test_sub_east_a', 'bank_transfer', '39633502.03', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-18 09:28:07'),
('88c096c1-a7b5-4c00-ad12-b18241f0929a', 'test_sub_east_b', 'online_banking', '34437012.78', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-19 16:34:31'),
('42522a59-57a5-4ac0-861a-6ea919d80788', 'test_sub_east_b', 'bill_payment', '4031288.18', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-09 23:20:38'),
('d2a1fd72-e582-407b-a1ef-00e9594cce50', 'test_sub_east_b', 'letter_of_credit', '1302985.97', 'CNY', '中交集团', false, true, false, 'settled', '2024-10-27 00:48:43'),
('6bc8134a-5e1a-4c9f-aaf1-d34f081188ba', 'test_sub_east_b', 'guarantee_payment', '28816586.76', 'CNY', '中石化财务', false, false, false, 'settled', '2024-08-28 16:41:28'),
('0c2fee71-1b5d-4b38-af27-148950f3dbd8', 'test_sub_east_b', 'collection', '9082642.47', 'CNY', '中交集团', false, false, false, 'settled', '2024-08-11 20:52:31'),
('bbd3c963-86a6-4b08-aa15-a587611e1bb7', 'test_sub_east_a', 'remittance', '23505819.64', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-19 10:42:06'),
('5595cf04-da27-44f1-af93-9d4c4a156f0c', 'test_sub_east_a', 'entrusted_collection', '16496885.14', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-27 21:25:52'),
('4553bad9-d7e5-42c8-9665-a232a7dfbcaa', 'test_sub_north_a', 'direct_debit', '1844489.54', 'CNY', '华能集团', false, false, true, 'settled', '2024-06-10 08:20:07'),
('59309201-c194-4b8b-8193-72b3ee8d1d45', 'test_sub_east_b', 'bank_transfer', '43246880.10', 'CNY', '华能集团', true, false, false, 'settled', '2024-12-02 17:29:26'),
('fec52156-0088-4ccf-88a0-3e5fcba50729', 'test_sub_east_a', 'online_banking', '9387251.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-11-14 15:40:28'),
('db5d673e-034d-4b5a-b2f2-b7cb0646b7b7', 'test_sub_east_a', 'bill_payment', '10185876.34', 'CNY', '中交集团', false, false, false, 'settled', '2024-03-08 09:28:56'),
('c940a614-d8a2-456d-8faa-a146256a6549', 'test_sub_north_a', 'letter_of_credit', '24240742.73', 'CNY', '中交集团', false, true, false, 'settled', '2024-05-02 22:10:19'),
('0c4cc8f7-9885-4025-8d2f-6cdf81f1a3d3', 'test_sub_north_a', 'guarantee_payment', '693586.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-17 07:53:58'),
('d21a1a32-670d-4c6c-bb85-fd69f8d9d1fd', 'test_sub_east_a', 'collection', '23077780.23', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-27 04:31:59'),
('e3a0432a-e4ce-4541-a8a3-a1a8c8a272bc', 'test_sub_north_a', 'remittance', '14600159.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-07-31 15:30:15'),
('67c84c52-1f94-4b2b-8358-2ce7b5a20342', 'test_sub_east_b', 'entrusted_collection', '27567741.19', 'CNY', '中铁建设', false, false, false, 'settled', '2024-04-07 19:32:47'),
('070cc058-173d-4ab9-bfe4-ff9d70fbc509', 'test_sub_east_a', 'direct_debit', '43202706.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-07-31 10:59:50'),
('a7ded264-6d3d-4127-a13e-6fa235681fec', 'test_sub_north_a', 'bank_transfer', '13365961.43', 'CNY', '华能集团', true, false, false, 'settled', '2024-05-24 23:19:53'),
('cb4dd4cd-c6bd-4b27-9b67-0ce8a2a1df3a', 'test_sub_north_a', 'online_banking', '29000369.96', 'CNY', '中铁建设', false, false, false, 'settled', '2024-03-17 14:34:30'),
('6b2f43f8-20f2-430e-96e2-99e72095d7c5', 'test_sub_east_b', 'bill_payment', '16628673.39', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-12 14:59:20'),
('ade4f5a5-6498-401d-b341-1672c46184fd', 'test_sub_east_a', 'letter_of_credit', '49038923.82', 'CNY', '中交集团', false, true, false, 'settled', '2024-07-15 07:54:49'),
('6f1aba51-edbd-46d8-a121-979348da337e', 'test_sub_east_b', 'guarantee_payment', '2191928.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-27 12:24:42'),
('a0718179-2943-489a-9535-dae788f1bc8e', 'test_sub_north_a', 'collection', '49041098.75', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-19 04:32:37'),
('df074da5-8cd9-489e-8c21-58418a03c340', 'test_sub_east_b', 'remittance', '43486318.66', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-21 16:58:29'),
('29c7f5e4-2739-42cb-95a7-1befcd639ce6', 'test_sub_east_a', 'entrusted_collection', '36124966.94', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-01 04:04:30'),
('8a409a8a-4dfd-4fa2-b570-a5a976a1bc95', 'test_sub_east_b', 'direct_debit', '16934676.09', 'CNY', '中铁建设', false, false, true, 'settled', '2024-11-28 02:54:21'),
('cc25ddb2-decf-4819-87e8-25ab7a033f00', 'test_sub_north_a', 'bank_transfer', '42968515.79', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-11 20:45:56'),
('7175f35e-302c-4dc4-a87c-f1d823ab7829', 'test_sub_east_b', 'online_banking', '43620427.04', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-12 02:15:40'),
('0543b0e9-069c-43ee-ae92-525951465211', 'test_sub_north_a', 'bill_payment', '46047245.65', 'CNY', '中石化财务', false, false, false, 'settled', '2024-02-16 13:06:48'),
('816d9fe4-1dc1-4001-b87d-e72ba174f757', 'test_sub_north_a', 'letter_of_credit', '35197502.56', 'CNY', '中铁建设', false, true, false, 'settled', '2024-03-26 22:19:57'),
('b3cd729d-c6b0-47ed-9b31-ed6f7ba206e9', 'test_sub_east_a', 'guarantee_payment', '2309088.52', 'CNY', '华能集团', false, false, false, 'settled', '2024-05-30 11:23:27'),
('7c534d89-fd3c-4b50-a2f8-d8353166308c', 'test_sub_east_a', 'collection', '12217429.63', 'CNY', '中铁建设', false, false, false, 'settled', '2024-10-16 21:50:11'),
('b73c2496-ea86-4b12-8215-4f9eccaccb4e', 'test_sub_east_a', 'remittance', '8761717.06', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-14 19:43:15'),
('e2fab8e7-a125-4f3e-b9fa-991ec64a8a2f', 'test_sub_east_b', 'entrusted_collection', '45642322.51', 'CNY', '中石化财务', false, false, false, 'settled', '2024-04-28 14:40:16'),
('629233e7-fd7b-4f39-bfa8-eb771a05fb09', 'test_sub_east_b', 'direct_debit', '12773782.14', 'CNY', '华能集团', false, false, true, 'settled', '2024-08-26 09:43:34'),
('59bf92e2-4a79-4bdd-a41a-9122a4a68c2a', 'test_sub_east_a', 'bank_transfer', '3702356.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-10-27 09:40:27'),
('41fdb4a1-040a-4029-b94b-3fe288ee647a', 'test_sub_north_a', 'online_banking', '12512410.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-04-11 12:54:30'),
('ad69722c-af7d-41cf-b6ce-b6f527babbd5', 'test_sub_east_a', 'bill_payment', '11867913.04', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-02 18:18:44'),
('568f9f5a-ba47-4b3d-895b-75423a1ab5cf', 'test_sub_east_b', 'letter_of_credit', '1106760.50', 'EUR', '中铁建设', false, true, false, 'settled', '2024-05-20 00:36:55'),
('7a419c6f-af38-4292-93c6-0e5defd51df7', 'test_sub_north_a', 'guarantee_payment', '38917797.67', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-06 23:31:53'),
('9ddac984-2a91-40ff-8972-e4363bff686e', 'test_sub_east_b', 'collection', '38789291.57', 'CNY', '中石化财务', false, false, false, 'settled', '2024-11-06 11:14:40'),
('20dfffd8-e0d3-4914-8e80-bba776e85026', 'test_sub_east_a', 'remittance', '31048349.24', 'CNY', '中石化财务', true, false, false, 'settled', '2024-11-17 03:57:40'),
('eea82265-8a5c-4bcf-92a4-1fc157adda37', 'test_sub_north_a', 'entrusted_collection', '1980734.47', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-18 18:23:46'),
('6625d319-50be-4d1a-98cf-ce2e4752b0e7', 'test_sub_east_a', 'direct_debit', '4515767.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-06-16 23:26:11'),
('caa6b75f-5e9f-4f36-9f23-dc4e3c4161f1', 'test_sub_east_a', 'bank_transfer', '6616668.29', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-06 16:32:58'),
('dd56cc2e-33a9-4607-bc73-eef0d826eaa7', 'test_sub_east_b', 'online_banking', '41525326.25', 'CNY', '国电投资', false, false, false, 'settled', '2024-09-03 09:47:55'),
('bbd5a98f-4326-469d-99eb-510bb9e77d27', 'test_sub_east_b', 'bill_payment', '40213584.60', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-08 04:48:14'),
('519091b0-a6bf-4e3a-8646-f7052d984399', 'test_sub_north_a', 'letter_of_credit', '36213593.44', 'USD', '中交集团', false, true, false, 'settled', '2024-07-06 02:50:25'),
('efe85341-411d-45ba-9769-b488825ff956', 'test_sub_east_a', 'guarantee_payment', '13230284.33', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-20 11:43:47'),
('13ffbca0-6559-4ca9-921e-9de336f01045', 'test_sub_north_a', 'collection', '13115448.80', 'CNY', '中铁建设', false, false, false, 'settled', '2024-11-22 11:06:43'),
('fce8aa1b-ad18-4772-b117-b2ecd6af07d0', 'test_sub_east_a', 'remittance', '23579128.63', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-14 10:58:39'),
('38e3b8bf-dd4f-453a-b279-a217651c3964', 'test_sub_east_a', 'entrusted_collection', '32386142.51', 'CNY', '中铁建设', false, false, false, 'pending', '2024-12-24 09:41:26'),
('79c6e0ce-540f-4af0-9c1b-966436a3aeb6', 'test_sub_east_a', 'direct_debit', '6997452.86', 'CNY', '华能集团', false, false, true, 'pending', '2024-06-04 15:07:06'),
('769eded8-d5be-48d3-899b-15e31e63020a', 'test_sub_east_a', 'bank_transfer', '44364092.83', 'CNY', '中石化财务', true, false, false, 'pending', '2024-07-17 14:23:42'),
('3fdfd059-d94d-44c6-bacd-7da9856eacbb', 'test_sub_north_a', 'online_banking', '34827234.74', 'CNY', '中交集团', false, false, false, 'pending', '2024-08-02 18:47:46'),
('424f7a4a-4394-41e9-91c5-045d2f3bcf79', 'test_sub_east_a', 'bill_payment', '44271835.06', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-07 19:26:17'),
('d3ea45f6-6374-4a3f-ba84-5b5d36367a24', 'test_sub_east_a', 'letter_of_credit', '34517130.38', 'CNY', '中铁建设', false, true, false, 'pending', '2024-08-15 07:54:23'),
('e5adae0a-85bf-4ad8-9f4f-beddb1d85254', 'test_sub_east_a', 'guarantee_payment', '49046576.64', 'CNY', '国电投资', false, false, false, 'pending', '2024-10-05 20:22:03'),
('f0f96dfe-5668-4197-ba33-d9dfa7effca5', 'test_sub_east_b', 'collection', '13801313.23', 'CNY', '华能集团', false, false, false, 'pending', '2024-08-20 02:42:13'),
('51dcbfbb-d9a1-4042-bf72-50022e88f6d6', 'test_sub_north_a', 'remittance', '31978251.00', 'CNY', '华能集团', true, false, false, 'pending', '2024-01-26 10:15:08'),
('1f86564d-194a-4df3-932c-d3739e202c36', 'test_sub_north_a', 'entrusted_collection', '10268226.70', 'CNY', '中交集团', false, false, false, 'pending', '2024-04-16 18:13:52'),
('42db41d1-4f8d-4f4f-95d3-b1b23d00b501', 'test_sub_east_a', 'direct_debit', '16434692.08', 'CNY', '中石化财务', false, false, true, 'pending', '2024-11-01 00:17:54'),
('31c28f18-2637-42ac-b940-67dc6a2d7d4b', 'test_sub_east_a', 'bank_transfer', '49376489.95', 'CNY', '中交集团', true, false, false, 'pending', '2024-05-08 05:07:42'),
('5910aca4-99f3-46da-bfde-be9e9bff979e', 'test_sub_east_a', 'online_banking', '6598843.45', 'CNY', '国电投资', false, false, false, 'pending', '2024-05-01 18:20:01'),
('c642de23-287e-4cd6-9281-0fb862667dba', 'test_sub_east_a', 'bill_payment', '13275721.74', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-03 16:07:47'),
('98142dfc-aad5-44cc-a7bb-a03dc82791e0', 'test_sub_east_a', 'letter_of_credit', '23817535.81', 'USD', '中交集团', false, true, false, 'pending', '2024-10-30 03:28:32'),
('95e0b80e-5d0e-4c1d-891c-2ed1d68d6047', 'test_sub_east_a', 'guarantee_payment', '47271327.99', 'CNY', '华能集团', false, false, false, 'pending', '2024-12-03 16:19:29'),
('fa606fa7-4ea0-483a-947e-e2a332e134c8', 'test_sub_north_a', 'collection', '48201668.89', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-02 12:27:43'),
('c9116628-c6f4-4a73-8057-b14cb833fc24', 'test_sub_east_a', 'remittance', '24518540.02', 'CNY', '中铁建设', true, false, false, 'pending', '2024-02-07 02:20:38'),
('fe14c092-e5ba-4a60-9786-54409b29b4eb', 'test_sub_east_a', 'entrusted_collection', '3293454.84', 'CNY', '国电投资', false, false, false, 'pending', '2024-11-15 20:37:35'),
('08aeccab-a479-4e33-911c-8b7dfb4dc29b', 'test_sub_north_a', 'direct_debit', '16266020.31', 'CNY', '中交集团', false, false, true, 'pending', '2024-09-28 09:29:32'),
('8994d192-f346-4896-9dd2-03eeae74b7a5', 'test_sub_north_a', 'bank_transfer', '21515664.30', 'CNY', '华能集团', true, false, false, 'pending', '2024-12-01 20:56:49'),
('5953bbd8-f961-458a-9a78-4ec7ccfebd39', 'test_sub_north_a', 'online_banking', '36044787.43', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-08 14:56:14'),
('d814e671-eee3-4c81-b7ff-63800841aae0', 'test_sub_east_b', 'bill_payment', '16953191.63', 'CNY', '中铁建设', false, false, false, 'pending', '2024-07-23 13:46:06'),
('6eac7580-45f3-4aa0-a6f3-f631e9054640', 'test_sub_east_b', 'letter_of_credit', '21343932.67', 'EUR', '国电投资', false, true, false, 'pending', '2024-07-10 04:43:59'),
('45b34ac7-91b1-494c-bcd4-e0b3d4c60bf8', 'test_sub_east_b', 'guarantee_payment', '3365994.07', 'CNY', '华能集团', false, false, false, 'pending', '2024-02-17 13:06:47'),
('ad46ffc0-bd63-4056-9dcf-aadfeada630a', 'test_sub_north_a', 'collection', '18638616.50', 'CNY', '中石化财务', false, false, false, 'pending', '2024-10-11 01:37:35'),
('2288e400-8d5f-4056-ad9d-d746c1951336', 'test_sub_north_a', 'remittance', '16489002.61', 'CNY', '华能集团', true, false, false, 'pending', '2024-07-29 11:55:42'),
('2acb7381-757b-4020-a104-005dd100f2f7', 'test_sub_east_b', 'entrusted_collection', '43405926.52', 'CNY', '华能集团', false, false, false, 'pending', '2024-05-27 19:19:22'),
('c91513da-0658-4148-ac43-d9b5cb79fc06', 'test_sub_east_a', 'direct_debit', '28900146.73', 'CNY', '中石化财务', false, false, true, 'pending', '2024-03-20 21:30:14'),
('031da414-532d-4b54-be0c-c5ff455dbfe4', 'test_sub_east_a', 'bank_transfer', '17512198.57', 'CNY', '中交集团', true, false, false, 'pending', '2024-07-07 03:48:17');

INSERT INTO payment_channel (id, channel_name, channel_type, is_direct_linked, daily_limit) VALUES
('ee237eb6-aed0-44c3-86f3-2bf471416365', '银行转账', 'bank_transfer', true, '23389750.34'),
('1035fe48-dc79-418b-b5a4-e4f96d36cce8', '网上银行', 'online_banking', true, '84670360.97'),
('3487bd22-8ac8-404e-89ad-a2da987d3d47', '票据支付', 'bill_payment', true, '61743754.77'),
('6d5c9fda-dc20-4a13-b0ef-583f47248aa8', '信用证', 'letter_of_credit', true, '56117235.76'),
('9b2f5f2f-a6a5-41e5-8f31-ba30ac0b019d', '保函支付', 'guarantee_payment', true, '92979344.81'),
('2b1a31be-9286-4c7b-94b7-7c36b1c1670c', '托收', 'collection', true, '27477324.79'),
('41181a11-5749-4556-9830-6d1894ca3de8', '汇款', 'remittance', true, '28053768.48'),
('0a865299-4b06-490f-b254-87bc8360a6a0', '委托收款', 'entrusted_collection', true, '92232214.58'),
('62b14cb6-8d6b-4053-954c-1c154053a8df', '直接扣款', 'direct_debit', false, '1604473.15');


-- 票据域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO bill (id, entity_id, bill_type, face_value, issue_date, maturity_date, status, is_overdue, created_at) VALUES
('bc8871ad-90d0-4d8b-9911-13bfba71755b', 'test_sub_east_a', 'commercial_draft', '3572312.52', '2024-05-24', '2025-03-15', 'active', false, '2024-11-20 00:05:47'),
('61938d41-8e06-4f4c-a684-a5b2b6614009', 'test_sub_north_a', 'bank_acceptance', '21049641.44', '2024-02-25', '2024-12-03', 'active', false, '2024-06-23 05:23:19'),
('2dd417a7-2db6-473a-bfbf-6911ab1e3d6f', 'test_sub_north_a', 'electronic_commercial', '44178775.01', '2024-03-24', '2024-08-04', 'active', false, '2024-03-20 05:48:39'),
('c408b5f0-aa8c-49b3-b0a5-9f2f6c170f0a', 'test_sub_east_a', 'commercial_draft', '13677931.89', '2024-06-21', '2024-10-30', 'active', false, '2024-12-04 13:31:38'),
('6fa5e02f-1cb8-4556-83a1-7d863f8ae9db', 'test_sub_east_b', 'bank_acceptance', '10856891.37', '2024-04-16', '2024-12-01', 'active', false, '2024-09-19 03:22:27'),
('8ae0a74c-471b-4700-a2af-73d230d9ebd6', 'test_sub_east_a', 'electronic_commercial', '26394011.95', '2024-03-13', '2025-02-15', 'active', false, '2024-06-06 01:14:25'),
('41162180-ff1b-4ccb-9cc2-1eb2b9bf4e16', 'test_sub_north_a', 'commercial_draft', '10300713.91', '2024-01-15', '2024-04-17', 'active', false, '2024-04-18 04:48:16'),
('4aa4dc20-9043-4c3c-83f2-6b5d00069cab', 'test_sub_east_b', 'bank_acceptance', '485722.34', '2024-03-24', '2024-08-22', 'active', false, '2024-08-08 05:08:24'),
('7ffd408b-26a2-4d63-b6a2-69b36efb67d7', 'test_sub_north_a', 'electronic_commercial', '25063091.09', '2024-06-29', '2025-01-22', 'active', false, '2024-12-08 11:04:25'),
('cbb702e3-e1f0-4608-81f7-0dd0c5286ce6', 'test_sub_north_a', 'commercial_draft', '1035202.68', '2024-01-11', '2024-11-19', 'active', false, '2024-02-09 10:36:27'),
('529c2bba-45d6-4c12-88e8-7384ec350e24', 'test_sub_north_a', 'bank_acceptance', '14546808.76', '2024-04-13', '2025-02-10', 'active', false, '2024-07-26 00:20:10'),
('2050dd12-105d-44cd-8e04-50798e9a60b1', 'test_sub_north_a', 'electronic_commercial', '4497681.08', '2024-04-27', '2025-01-27', 'active', false, '2024-02-24 07:27:37'),
('7946c7a0-f95d-400b-abe0-4544cb3e0277', 'test_sub_east_b', 'commercial_draft', '19848758.17', '2024-05-14', '2024-09-21', 'active', false, '2024-06-07 23:21:14'),
('297ec315-af85-40d0-a8a9-d151e982fb90', 'test_sub_east_b', 'bank_acceptance', '25573115.90', '2024-02-13', '2024-06-21', 'active', false, '2024-02-28 16:32:12'),
('0b5b5b37-0831-4075-aad5-152ba9881563', 'test_sub_east_b', 'electronic_commercial', '11889815.56', '2024-03-30', '2024-09-11', 'active', false, '2024-03-15 08:12:11'),
('cbe7402d-367f-43ef-91a9-78a51294feee', 'test_sub_north_a', 'commercial_draft', '8939591.83', '2024-02-09', '2024-06-16', 'active', false, '2024-11-17 15:29:48'),
('f623b5dd-2355-44c3-81bd-4d0b436090f8', 'test_sub_north_a', 'bank_acceptance', '34088560.57', '2024-05-28', '2025-04-12', 'active', false, '2024-10-16 20:40:39'),
('865b19ff-cffd-4b57-8b8e-d4afa8a807bb', 'test_sub_east_b', 'electronic_commercial', '7632774.33', '2024-06-09', '2025-02-15', 'active', false, '2024-02-04 15:28:40'),
('f28525fc-1171-4f5f-995b-e0f21260e9e5', 'test_sub_east_b', 'commercial_draft', '17661916.91', '2024-03-11', '2024-07-07', 'active', false, '2024-02-07 09:29:28'),
('992952e2-3e4b-4276-b65b-2dcbf7e9682c', 'test_sub_east_a', 'bank_acceptance', '41601661.92', '2024-01-15', '2024-10-19', 'active', false, '2024-02-09 20:55:54'),
('f4502759-c08d-435e-8af3-f7162dcdf70f', 'test_sub_east_a', 'electronic_commercial', '19285675.58', '2024-06-06', '2025-05-21', 'active', false, '2024-10-24 17:50:47'),
('607fe7e5-2047-40b4-8006-31921946fe19', 'test_sub_east_a', 'commercial_draft', '16144185.47', '2024-04-25', '2024-10-28', 'pending', false, '2024-08-31 16:09:03'),
('37f9581f-d839-4347-925a-6999af0d21e2', 'test_sub_east_b', 'bank_acceptance', '49121040.50', '2024-01-27', '2024-10-18', 'pending', false, '2024-02-13 16:41:11'),
('9187bb0f-ed92-4f47-a157-bccef5d62245', 'test_sub_east_a', 'electronic_commercial', '49550202.53', '2024-03-04', '2025-01-12', 'pending', false, '2024-09-25 16:39:10'),
('efc5599f-3b5a-447e-a87b-4058f449a170', 'test_sub_east_b', 'commercial_draft', '19432086.32', '2024-04-05', '2024-11-25', 'pending', false, '2024-06-22 21:38:03'),
('9a7e7d86-fd80-4136-89d0-d4dc23279bd7', 'test_sub_north_a', 'bank_acceptance', '3389001.53', '2024-06-14', '2025-03-02', 'pending', false, '2024-02-18 17:43:24'),
('9f83060d-560f-4d1b-b583-00172aec0555', 'test_sub_east_b', 'electronic_commercial', '16734765.60', '2024-03-05', '2024-08-18', 'pending', false, '2024-10-25 21:09:58'),
('4451a859-ea6e-4441-b00a-6940361379b7', 'test_sub_east_b', 'commercial_draft', '6534687.75', '2024-03-20', '2025-01-04', 'overdue', true, '2024-12-28 02:19:35'),
('2c9c4cf2-162d-4060-97b4-654f09c3a109', 'test_sub_east_b', 'bank_acceptance', '40677920.71', '2024-06-13', '2025-02-26', 'overdue', true, '2024-12-09 22:53:47'),
('efb775fb-af08-4023-8468-8ae4242873fe', 'test_sub_north_a', 'electronic_commercial', '32336638.55', '2024-05-14', '2024-09-28', 'overdue', true, '2024-08-04 16:23:01');

INSERT INTO endorsement_chain (id, bill_id, endorser_id, endorsee_id, endorse_date, sequence_no) VALUES
('41ff63a5-4c65-4bed-965a-c44c23ee15a5', 'cbb702e3-e1f0-4608-81f7-0dd0c5286ce6', 'test_sub_east_a', 'test_sub_north_a', '2024-06-23', 1),
('e99c8e1c-6187-4550-b6b1-19ba838860dd', '41162180-ff1b-4ccb-9cc2-1eb2b9bf4e16', 'test_sub_east_a', 'test_sub_north_a', '2024-03-20', 2),
('172e0009-9389-48b4-bdae-b407d18d28d7', 'cbb702e3-e1f0-4608-81f7-0dd0c5286ce6', 'test_sub_east_a', 'test_sub_north_a', '2024-12-04', 3),
('ccdb1ae4-8c4c-4edb-aa85-84f34c63b86d', '2c9c4cf2-162d-4060-97b4-654f09c3a109', 'test_sub_north_a', 'test_sub_east_a', '2024-11-01', 4),
('b3ee094d-d28f-4d92-bc4d-a650fbe361ad', '6fa5e02f-1cb8-4556-83a1-7d863f8ae9db', 'test_sub_east_a', 'test_sub_north_a', '2024-12-20', 5),
('33ead903-4a18-42f4-acc1-367aea512ed6', '9a7e7d86-fd80-4136-89d0-d4dc23279bd7', 'test_sub_east_a', 'test_sub_east_b', '2024-01-23', 6),
('fc95df8d-8cfc-4b3c-a4d9-8d28a7a501c3', '2050dd12-105d-44cd-8e04-50798e9a60b1', 'test_sub_north_a', 'test_sub_east_a', '2024-08-15', 7),
('a377bdb2-7de7-48d3-a85c-e3a263928775', 'cbb702e3-e1f0-4608-81f7-0dd0c5286ce6', 'test_sub_north_a', 'test_sub_east_b', '2024-04-29', 8),
('a292bb4f-1390-4cb8-928c-41ac8279967d', '4aa4dc20-9043-4c3c-83f2-6b5d00069cab', 'test_sub_east_b', 'test_sub_north_a', '2024-04-09', 9),
('b19e9154-b4f8-431c-aa9f-e09ca3804ffe', '607fe7e5-2047-40b4-8006-31921946fe19', 'test_sub_north_a', 'test_sub_east_b', '2024-08-24', 10),
('2e76129c-b4e4-488e-90e6-5ffddcedf7c6', 'efc5599f-3b5a-447e-a87b-4058f449a170', 'test_sub_east_b', 'test_sub_north_a', '2024-03-23', 11),
('c1935445-a0a1-44c9-8a66-7b886e27f9cd', '9a7e7d86-fd80-4136-89d0-d4dc23279bd7', 'test_sub_north_a', 'test_sub_east_a', '2024-05-08', 12),
('2f3bc891-f39c-48bd-9f61-09461096dc46', 'f4502759-c08d-435e-8af3-f7162dcdf70f', 'test_sub_east_b', 'test_sub_north_a', '2024-10-10', 13),
('bb724e9e-83bd-4253-992c-72cc04f185e4', '37f9581f-d839-4347-925a-6999af0d21e2', 'test_sub_north_a', 'test_sub_east_a', '2024-05-25', 14),
('1a87a3d9-2a80-4bdb-8640-5024f686c173', 'efc5599f-3b5a-447e-a87b-4058f449a170', 'test_sub_east_a', 'test_sub_east_b', '2024-08-18', 15);


-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('912f3138-308a-4828-b91d-8d2568c47f3d', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('55e1135d-c5b5-4454-ae8a-970ba0ed520d', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('1abd549f-1950-408c-92cd-04bc3e8b03bf', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('346e2865-bb46-4697-b93b-5956d2e1491c', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('070f8d2b-aa27-4fd6-b219-7241c4a222a4', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('11fb1b72-a3b9-427b-a533-266f4bc3ad91', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('11bb54fb-4abf-4813-80ba-611f599fb81b', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('b8b28776-f14e-414e-8976-416403dff825', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('3206eae0-e99f-4d44-9604-588724daaf70', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('1c60dcdb-295d-4b2c-9d25-2632824e997f', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('c3524722-d117-4f81-8840-b2073aa58245', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('983c4a25-196f-4f89-b711-ddc017399bdc', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('9b696e9f-ca91-465e-a55b-e16823e53bf7', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('7bcec8f7-58e0-441e-bd4a-c6daa82976de', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('85100bba-611d-446b-9fb3-4717283a1672', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('9d1ae5f8-366f-4795-99d2-979209ceb93a', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('e2d0b98b-c861-419d-b3d9-164df10b5882', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('a771bd8c-93cf-4d14-9613-1f3a8018b90a', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('52794b39-e60e-401b-bfa4-05e2b17b5ba8', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('c92373d8-7930-479b-818e-9f5d8ee7c421', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');


-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('471cbd82-5add-450f-b018-378219776352', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('3ddd94c1-a540-453b-a7e4-c55856cc200c', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('f919c662-00eb-4ec9-9fbd-1e7169926ad8', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('8bb47733-ff2d-4ada-9081-2745dc136a6c', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('2da97380-c884-4f90-b85e-2b7a6861e377', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('9e6029fa-cbc1-4c6e-9bbe-4d516e2c3c11', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('73dbba57-bbe2-435b-a556-1934ae5769aa', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('136ebf8e-5886-417a-b387-b72206add1d6', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('38eb5645-caa4-449a-9c5b-9af3f0dbce4d', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('7cebf390-f43a-4141-a8b7-d9a788fc96cf', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('50423251-da2e-46e2-84c4-64fb216ee19e', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('6f089ccf-e392-4698-96a9-adfc4e9771d1', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('df657def-cb57-4555-ab9d-c88998040955', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('2273878b-3b99-488d-a734-f262913e659f', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('13378b59-4cf3-454d-8c7b-4f2e2617eca3', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('5c892896-d580-4b1d-b965-5b8d79457be0', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('7da69a96-64dd-42b8-a629-b0578626d08e', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('12f21293-c93e-48e4-bbdb-a10df91cf92e', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('352aa557-8f7b-4222-989e-f311e9cba2f3', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('d8d9f89d-1254-4adb-9a5b-3012a10aa19c', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('e1434533-be54-46e5-be4d-2d880bce88a8', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('7bd54120-97bd-4c22-9e1b-5c34a3bb1109', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('014f0278-fc73-4afe-a6bd-a291a40189f7', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('0faee8bf-0248-42a0-bdba-26d8fdefad0a', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('397fe753-e27a-4fb0-a1ff-8b571136d6a0', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('18bbb970-0a2b-4a5f-8301-e67a7f6c9633', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('2202d9d7-1ad2-4fc7-acb4-2a3d398c8abe', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('37246c95-4079-4bb4-87b3-3c37e5ff7f5a', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('cc94c063-5220-40d3-9461-73d25852b72b', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('e7a4ec26-91ba-4663-8bf9-5d1f65fc342a', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');


-- 国资委考核域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO financial_report (id, entity_id, report_type, period, total_asset, net_asset, revenue, profit, rd_expense, employee_count, operating_cash_flow) VALUES
('921ae1d6-64e5-4ee3-8a64-d9a3fd8b7630', 'test_group_hq', 'annual', '2024', '47861229725.12', '18299038102.21', '6437712433.76', '717436878.38', '164842161.67', 42507, '926315918.56'),
('82278e0a-bbc1-4796-b374-921ee854f79c', 'test_region_east', 'annual', '2024', '8555519077.10', '4257396222.61', '7346011300.15', '811836290.54', '518274321.86', 37437, '301852087.26'),
('083fb059-37d2-4144-a324-8d931614d050', 'test_region_north', 'annual', '2024', '4979919889.78', '2911082170.28', '7824712503.55', '598321264.29', '255465147.94', 37995, '2141275239.95'),
('0eeee728-55b4-497a-a39a-4dfb0beef076', 'test_sub_east_a', 'annual', '2024', '2484009030.49', '1407685593.63', '5682986093.70', '648944324.54', '216667520.45', 16548, '4042971955.66'),
('8fa121a8-021d-4ef6-82a4-30ba414a8cf4', 'test_sub_east_b', 'annual', '2024', '20898533810.48', '9113082362.28', '7041828930.89', '463408993.06', '316440812.83', 30937, '1099712766.46'),
('7610efa2-cccf-480b-b33f-7f006bf0f2ce', 'test_sub_north_a', 'annual', '2024', '8039765866.97', '4489771254.78', '3533505730.14', '525793910.26', '143892245.92', 26630, '740754142.61');

INSERT INTO assessment_indicator (id, entity_id, indicator_code, indicator_name, target_value, actual_value, period) VALUES
('d46cabfd-9d1d-4632-8e85-b8027ab5a7f0', 'test_group_hq', 'AI001', '净资产收益率', '0.1272', '0.1313', '2024'),
('b87e082b-afa7-420b-994e-05c692d32d0e', 'test_group_hq', 'AI002', '营业收入利润率', '0.1200', '0.1296', '2024'),
('7de9b8d7-47ce-461c-9891-f62d0ad00205', 'test_group_hq', 'AI003', '研发投入强度', '0.0711', '0.0722', '2024'),
('664b7a76-f649-4985-afa4-17d31b0a13c3', 'test_group_hq', 'AI004', '全员劳动生产率', '0.1796', '0.2021', '2024'),
('cec21c3d-404b-430a-9b1e-eb1b9cea05b5', 'test_group_hq', 'AI005', '资产负债率', '0.1720', '0.2202', '2024'),
('69db0b3d-924c-42f6-8e97-7332895331af', 'test_group_hq', 'AI006', '经营性现金流比率', '0.0969', '0.1191', '2024'),
('4108e3d7-b6c8-44ce-9a0c-ab69440b838b', 'test_group_hq', 'AI007', '总资产周转率', '0.1994', '0.2273', '2024'),
('63dbf6a7-b3d1-401a-af11-506d68adb35b', 'test_group_hq', 'AI008', '成本费用利润率', '0.1246', '0.1280', '2024'),
('9e4366c7-6a46-4f74-99e2-0017ccf792a3', 'test_group_hq', 'AI009', '国有资本保值增值率', '0.1258', '0.1623', '2024'),
('2430a2b0-63ed-46e0-bb66-0d07e33a7004', 'test_region_east', 'AI001', '净资产收益率', '0.1375', '0.1395', '2024'),
('768322c3-05ea-4537-bf90-4b9f547e6fa5', 'test_region_east', 'AI002', '营业收入利润率', '0.1242', '0.1571', '2024'),
('139e6085-0724-4773-a7c3-eb44c262c48b', 'test_region_east', 'AI003', '研发投入强度', '0.1509', '0.1638', '2024'),
('9c8bbf7c-b3c1-47d8-a168-e418d2f51b74', 'test_region_east', 'AI004', '全员劳动生产率', '0.1771', '0.2000', '2024'),
('556af8fe-b047-4e18-9de5-9eb6d3d4ecac', 'test_region_east', 'AI005', '资产负债率', '0.1591', '0.1956', '2024'),
('e23d4f4d-a701-4035-980f-4ec5d27ba12e', 'test_region_east', 'AI006', '经营性现金流比率', '0.0568', '0.0577', '2024'),
('65b67a69-2023-4636-88da-255298a8ce84', 'test_region_east', 'AI007', '总资产周转率', '0.0792', '0.0923', '2024'),
('2c048a15-c4b1-47b8-9cd3-4cf66484a8f6', 'test_region_east', 'AI008', '成本费用利润率', '0.1080', '0.1226', '2024'),
('c10ea859-484c-43d8-a01c-fed60e985b09', 'test_region_east', 'AI009', '国有资本保值增值率', '0.0920', '0.1193', '2024'),
('568f208a-f9cd-45b3-878e-6461a34f869a', 'test_region_north', 'AI001', '净资产收益率', '0.1417', '0.1472', '2024'),
('c9625ccf-0f43-4ea8-8a25-80b10652c916', 'test_region_north', 'AI002', '营业收入利润率', '0.1091', '0.1351', '2024'),
('624b413b-9ca0-4fb7-90c0-88a45dc413e1', 'test_region_north', 'AI003', '研发投入强度', '0.1337', '0.1484', '2024'),
('2250e09e-12e8-464d-9fac-26f83c97339e', 'test_region_north', 'AI004', '全员劳动生产率', '0.0799', '0.0921', '2024'),
('73c36cfd-f389-4784-a5f3-4d07b3552824', 'test_region_north', 'AI005', '资产负债率', '0.0560', '0.0567', '2024'),
('752f05d8-559b-45d4-931c-37e4373237dc', 'test_region_north', 'AI006', '经营性现金流比率', '0.1000', '0.1142', '2024'),
('8b219a20-4a2d-4f13-8ced-46aa299c22b2', 'test_region_north', 'AI007', '总资产周转率', '0.0723', '0.0917', '2024'),
('cf8f4fc5-7532-4f3b-ba14-71c02ee6e2e4', 'test_region_north', 'AI008', '成本费用利润率', '0.0992', '0.1174', '2024'),
('8b8d853c-d121-42ba-a7cc-4079dcbf628e', 'test_region_north', 'AI009', '国有资本保值增值率', '0.1089', '0.1290', '2024'),
('26978df8-07d0-467b-bb87-83e109156695', 'test_sub_east_a', 'AI001', '净资产收益率', '0.1391', '0.1603', '2024'),
('e47fbd51-a3c5-416f-9f62-594d7ee231a3', 'test_sub_east_a', 'AI002', '营业收入利润率', '0.1299', '0.1575', '2024'),
('25554331-95cc-4661-9ce4-35d240975e7f', 'test_sub_east_a', 'AI003', '研发投入强度', '0.1212', '0.1218', '2024'),
('76058e8e-9e9a-4c73-a165-9607d25f636b', 'test_sub_east_a', 'AI004', '全员劳动生产率', '0.1511', '0.1955', '2024'),
('c0a18df0-39a7-40bc-9736-a29ccee6e10d', 'test_sub_east_a', 'AI005', '资产负债率', '0.0962', '0.1221', '2024'),
('53b0fc5b-c2d5-4ae3-b8a2-0c480050eb7d', 'test_sub_east_a', 'AI006', '经营性现金流比率', '0.1444', '0.1703', '2024'),
('bb9eec9b-20e7-49e8-bb46-0d8e20881e64', 'test_sub_east_a', 'AI007', '总资产周转率', '0.1951', '0.2409', '2024'),
('c75f5efe-594a-4eb2-8151-9c0536cd11a9', 'test_sub_east_a', 'AI008', '成本费用利润率', '0.1366', '0.1662', '2024'),
('5ea27183-32b4-4927-8f51-601862688254', 'test_sub_east_a', 'AI009', '国有资本保值增值率', '0.1221', '0.1413', '2024'),
('9a5c6801-1e33-4c8c-864f-ed9f2ee33b0d', 'test_sub_east_b', 'AI001', '净资产收益率', '0.1430', '0.1791', '2024'),
('1a5f3f9f-27b0-40f3-b2ab-2774c50926cc', 'test_sub_east_b', 'AI002', '营业收入利润率', '0.1732', '0.1531', '2024'),
('7ee0993e-57ab-4eb5-b8ca-3f6adf6af897', 'test_sub_east_b', 'AI003', '研发投入强度', '0.1922', '0.1663', '2024'),
('02ea7e36-73c8-494c-ae06-7d18cf80af7f', 'test_sub_east_b', 'AI004', '全员劳动生产率', '0.1162', '0.1056', '2024'),
('3e5265de-1e0e-4f90-8038-ec0581a56693', 'test_sub_east_b', 'AI005', '资产负债率', '0.1536', '0.1394', '2024'),
('c74efd60-935e-4976-bdfb-9a6fc2cebe55', 'test_sub_east_b', 'AI006', '经营性现金流比率', '0.1881', '0.1829', '2024'),
('a493f08f-7fa1-472f-8c8c-c77d2a9f5e60', 'test_sub_east_b', 'AI007', '总资产周转率', '0.1591', '0.1510', '2024'),
('a407a1bb-9d6d-4ea0-a1e4-383de1ca7355', 'test_sub_east_b', 'AI008', '成本费用利润率', '0.0811', '0.0726', '2024'),
('72c89016-4546-43b5-a9b5-0ea860677be0', 'test_sub_east_b', 'AI009', '国有资本保值增值率', '0.1218', '0.1100', '2024'),
('f0f175d0-1a91-4d7b-94de-0c5da4b6fdba', 'test_sub_north_a', 'AI001', '净资产收益率', '0.1189', '0.1099', '2024'),
('1bf68f27-a13b-4810-a3f0-1ba17a6a9c0c', 'test_sub_north_a', 'AI002', '营业收入利润率', '0.1031', '0.0988', '2024'),
('f2725c51-df30-4790-a887-bc3296a940b6', 'test_sub_north_a', 'AI003', '研发投入强度', '0.1521', '0.1464', '2024'),
('a3e8ef4b-25e3-406d-9ca5-c6ba9e148a79', 'test_sub_north_a', 'AI004', '全员劳动生产率', '0.1415', '0.0789', '2024'),
('b65fc5f5-fcf9-405d-8434-95d13be68478', 'test_sub_north_a', 'AI005', '资产负债率', '0.0919', '0.0542', '2024'),
('95b5c64f-619e-4877-b6c2-c3ba81687aaa', 'test_sub_north_a', 'AI006', '经营性现金流比率', '0.1657', '0.1179', '2024'),
('5366bbb5-ed6e-4d68-acdf-b7bd6d051e94', 'test_sub_north_a', 'AI007', '总资产周转率', '0.1557', '0.0927', '2024'),
('f85eb569-77b1-477e-ba9c-96a8ae8fb2dc', 'test_sub_north_a', 'AI008', '成本费用利润率', '0.1341', '0.1046', '2024'),
('e3873c0c-e689-411d-8f20-13362ef06919', 'test_sub_north_a', 'AI009', '国有资本保值增值率', '0.0910', '0.0488', '2024');

