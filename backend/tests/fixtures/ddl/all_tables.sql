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
('b8261a54-a0a1-4e9c-88a0-648455979682', 'test_sub_north_a', 'BOC', '6222****5506', '244967364.62', 'CNY', true, 'configured', NULL, false, '2024-03-12 23:06:43'),
('7988aef0-0008-4942-b065-1c55a7e82512', 'test_sub_north_a', 'SPDB', '6222****7912', '31879501.21', 'CNY', true, 'configured', NULL, false, '2024-02-17 06:14:32'),
('97482b17-e6f5-4866-9d99-b0872a0d8645', 'test_sub_north_a', 'ICBC', '6228****9928', '419577868.98', 'CNY', true, 'configured', NULL, false, '2024-08-17 18:17:51'),
('821cdd30-63ba-4ecc-b734-ac8425391a4e', 'test_sub_east_a', 'CCB', '6225****6574', '277943554.54', 'CNY', true, 'configured', NULL, false, '2024-04-20 10:06:05'),
('31dc489e-2bae-4997-9baf-3a7f9bb62b23', 'test_sub_east_b', 'BOC', '6217****6635', '603765658.76', 'CNY', true, 'configured', NULL, false, '2024-01-23 23:29:34'),
('def8c7f4-3b80-4696-a651-f88640c5cecd', 'test_sub_east_a', 'CITIC', '6222****5803', '829421723.79', 'CNY', true, 'configured', NULL, false, '2024-11-12 11:36:12'),
('50202db0-3bb3-4836-a1bc-5db652c915cd', 'test_sub_north_a', 'BOC', '6222****4733', '773091033.95', 'CNY', true, 'configured', NULL, false, '2024-02-10 07:55:06'),
('0e2aee04-b18b-4716-b5fb-5cabb26aceed', 'test_sub_east_b', 'BOCOM', '6225****6977', '162737831.75', 'CNY', true, 'configured', NULL, false, '2024-06-30 06:42:17'),
('9a432fc3-327f-431a-97a7-516ce5d3e024', 'test_sub_north_a', 'BOC', '6228****9751', '729153885.27', 'CNY', true, 'configured', NULL, false, '2024-03-24 14:24:17'),
('24153c54-ddc1-4847-b7ec-e9c461bc1d03', 'test_sub_north_a', 'SPDB', '6228****6313', '842867635.00', 'CNY', true, 'configured', NULL, false, '2024-01-29 07:52:02'),
('0745f02b-3d08-4a61-913f-e400d6a5bca9', 'test_sub_east_b', 'CITIC', '6217****2084', '211061745.30', 'CNY', true, 'configured', NULL, false, '2024-10-17 22:20:13'),
('e672e41b-2596-4c98-96e0-540fb5cf3b69', 'test_sub_north_a', 'CEB', '6225****8517', '142957303.28', 'CNY', true, 'configured', NULL, false, '2024-03-12 07:47:35'),
('2a989d0c-91ef-402c-b031-971ec9296263', 'test_sub_north_a', 'BOCOM', '6225****7543', '362060244.07', 'CNY', true, 'configured', NULL, false, '2024-03-11 16:31:05'),
('35e68042-43f4-438a-9563-193aaafb1d43', 'test_sub_east_a', 'BOC', '6228****3621', '792100156.43', 'CNY', true, 'configured', NULL, false, '2024-08-04 19:04:24'),
('ebb3b672-5439-49b4-a615-fc256453b975', 'test_sub_east_b', 'CEB', '6217****1188', '680315381.92', 'CNY', true, 'configured', NULL, false, '2024-02-28 21:56:34'),
('125725a5-7535-4f8b-b396-7d51040805e4', 'test_sub_east_b', 'CMB', '6222****5808', '434821774.14', 'CNY', true, 'configured', NULL, false, '2024-08-20 00:46:56'),
('91472382-b5ef-4977-92a1-ac8c277b4390', 'test_sub_north_a', 'BOCOM', '6228****9317', '912636576.56', 'CNY', true, 'configured', NULL, false, '2024-11-16 09:53:40'),
('621e1d8d-cc9d-4e83-bc99-5790927eddc6', 'test_sub_north_a', 'ABC', '6228****7126', '762534549.00', 'CNY', true, 'configured', NULL, false, '2024-10-03 16:58:00'),
('122737a2-526b-4846-b2bc-bfbb1bdd0af3', 'test_sub_north_a', 'CMB', '6225****1319', '111956538.55', 'CNY', true, 'configured', NULL, false, '2024-07-04 09:15:03'),
('ddbf1119-a077-4939-886e-6f00a043c0dd', 'test_sub_east_a', 'BOC', '6222****8962', '816041651.09', 'CNY', true, 'configured', NULL, false, '2024-09-29 04:08:42'),
('c2921287-1629-44a7-be54-2ed80703e9c6', 'test_sub_east_b', 'SPDB', '6228****5342', '527721020.04', 'CNY', true, 'configured', NULL, false, '2024-11-06 13:13:59'),
('23a29487-2b1c-4b46-befc-e2c82e2f6365', 'test_sub_north_a', 'ABC', '6217****7537', '995149841.73', 'CNY', true, 'configured', NULL, false, '2024-11-28 11:28:57'),
('447b8b23-9fcf-4474-b1a2-433ab5b8eb12', 'test_sub_north_a', 'CEB', '6222****5061', '224774867.30', 'CNY', true, 'configured', NULL, false, '2024-06-22 00:37:35'),
('7ad1eeee-41bb-4d9a-9d38-2a5ce716a3bc', 'test_sub_east_a', 'ABC', '6222****2163', '707870162.45', 'CNY', true, 'configured', NULL, false, '2024-01-31 07:04:57'),
('41339adb-4c5c-4ce4-8d69-ee93b1f72594', 'test_sub_east_a', 'CMB', '6222****9423', '238080833.91', 'CNY', true, 'configured', NULL, false, '2024-12-08 15:13:34'),
('e7c2c457-232a-484e-b086-1a47a9968994', 'test_sub_east_a', 'CEB', '6228****8749', '807516248.07', 'CNY', true, 'configured', NULL, false, '2024-04-07 03:06:42'),
('9baece30-910a-4724-abfa-903ba98f9318', 'test_sub_east_b', 'CMB', '6225****7735', '467077965.57', 'CNY', true, 'configured', NULL, false, '2024-01-28 21:41:41'),
('f7549ce9-dbb1-4690-ad16-d8e68390984f', 'test_sub_east_a', 'ICBC', '6225****6559', '800612451.61', 'CNY', true, 'configured', NULL, false, '2024-02-25 07:12:12'),
('6771a83e-74bf-4ac7-bc85-569a4dadf51c', 'test_sub_north_a', 'CEB', '6228****7912', '183569686.98', 'CNY', true, 'configured', NULL, false, '2024-08-24 07:55:59'),
('e60071e3-0a24-48f6-b5be-612a99bc97b4', 'test_sub_east_a', 'CEB', '6222****1828', '652179679.51', 'CNY', true, 'configured', NULL, false, '2024-10-03 00:05:59'),
('820008e1-4d27-4f88-b8fe-15dbc6db88e3', 'test_sub_east_a', 'CCB', '6225****8956', '481410282.13', 'CNY', true, 'configured', NULL, false, '2024-07-24 01:10:24'),
('757bf211-5887-4973-947d-a398417ad1ed', 'test_sub_east_a', 'CITIC', '6217****8454', '285320704.02', 'CNY', true, 'configured', NULL, false, '2024-12-22 23:50:35'),
('55376a0d-e004-4c1a-be64-7210d481b0f4', 'test_sub_north_a', 'CEB', '6228****4111', '296778154.71', 'CNY', true, 'configured', NULL, false, '2024-01-30 18:47:34'),
('092689f5-19d3-44c7-829b-e95186a65e7d', 'test_sub_east_a', 'CMB', '6222****1821', '584219176.70', 'CNY', true, 'configured', NULL, false, '2024-09-14 16:10:03'),
('cdc6e65c-7867-4559-81b1-b21aad77cd46', 'test_sub_north_a', 'BOC', '6228****2122', '595075602.94', 'CNY', true, 'configured', NULL, false, '2024-12-11 07:25:07'),
('9a421993-6484-4127-a95c-caccc87094d9', 'test_sub_north_a', 'ABC', '6222****2343', '419282992.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-25 18:33:20'),
('b7e01e49-4196-47a4-9bec-613ab4821519', 'test_sub_east_b', 'ABC', '6217****4910', '265687951.08', 'CNY', true, 'unconfigured', NULL, false, '2024-03-08 21:41:19'),
('7ae922d0-8bb9-4605-aa54-2d52ae668a6f', 'test_sub_east_b', 'CMB', '6222****1152', '458339694.07', 'CNY', true, 'unconfigured', NULL, false, '2024-10-15 03:04:34'),
('017c177a-9bb1-4280-87b8-6e2ba2c7712f', 'test_sub_east_a', 'SPDB', '6217****3170', '933266052.06', 'CNY', true, 'unconfigured', NULL, false, '2024-02-05 07:23:18'),
('82d669ea-17c6-4888-87cd-d61939fbf553', 'test_sub_east_a', 'CEB', '6217****9666', '7922324.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 09:59:42'),
('850177f8-297b-461c-ba31-97f2674fe225', 'test_sub_east_a', 'CCB', '6217****2891', '889723735.74', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 04:17:18'),
('d993fe03-fc24-452f-9de5-2a9a4fc23768', 'test_sub_north_a', 'ABC', '6217****4335', '687528379.09', 'CNY', true, 'unconfigured', NULL, false, '2024-05-15 16:31:16'),
('2ef7c59b-f40f-415d-83a0-1e3a7ce56cc4', 'test_sub_east_a', 'BOC', '6225****5533', '44182353.12', 'CNY', true, 'unconfigured', NULL, false, '2024-06-19 04:40:16'),
('29eb15ac-5866-40e9-aa50-ea81f0320a5d', 'test_sub_east_a', 'CEB', '6225****1158', '111962693.20', 'CNY', true, 'unconfigured', NULL, false, '2024-12-19 04:34:02'),
('c1167795-481f-4e78-8a1f-5ed457a48789', 'test_sub_east_b', 'SPDB', '6228****8041', '127532774.73', 'CNY', true, 'unconfigured', NULL, false, '2024-06-06 11:57:59'),
('e8ee4e83-ba4c-4e1e-86c0-ffb12c2aa572', 'test_sub_east_a', 'CMB', '6228****5088', '666966717.29', 'CNY', false, 'configured', NULL, false, '2024-06-30 17:56:55'),
('ef85fd7d-ede8-4480-bb82-102cd2b7d0a8', 'test_sub_east_b', 'CCB', '6228****3662', '976208412.33', 'CNY', false, 'configured', NULL, false, '2024-03-31 13:01:11'),
('99d2ded9-1cd6-473e-be93-6824140789ff', 'test_sub_north_a', 'CMB', '6225****5065', '266879029.02', 'CNY', false, 'configured', NULL, false, '2024-12-25 03:24:55'),
('4b938950-8e97-492d-93a4-12eed4cc4ba6', 'test_sub_east_a', 'CEB', '6228****4269', '816604946.94', 'CNY', false, 'configured', NULL, false, '2024-08-23 11:19:52'),
('683f057e-12fb-4ccb-84a7-0f5d57a04ec6', 'test_sub_east_a', 'ABC', '6222****4164', '398526131.97', 'CNY', false, 'configured', NULL, false, '2024-05-22 02:49:17');

INSERT INTO internal_deposit_account (id, entity_id, pool_id, balance, interest_rate, maturity_date, created_at) VALUES
('2fa92899-a5ca-4041-8e9f-65084776ff24', 'test_sub_east_b', '194021af-e323-4e88-ba90-bf0a0eb134c1', '200139352.99', '0.0392', '2025-12-02', '2024-06-18 00:07:56'),
('e36db426-740f-437a-8dc2-d72a54713081', 'test_sub_east_b', '6036e268-182f-475f-9e98-73ca932ac7cb', '481285890.72', '0.0254', '2025-02-27', '2024-01-20 03:38:27'),
('a9311e19-b471-4c80-872f-59256750b64a', 'test_sub_east_b', 'e448530a-bbf3-459c-99ec-748c27f5269e', '157181818.44', '0.0419', '2025-11-06', '2024-02-29 12:57:36'),
('44ee019d-26c7-42d3-b215-8b6d7a9a5252', 'test_sub_east_a', '08e8e746-eb70-4064-ad49-e427eb8fd07b', '354538249.28', '0.0276', '2024-06-02', '2024-09-23 17:43:46'),
('bd638c93-ef29-404b-9dcd-faef0d823c1a', 'test_sub_north_a', '80ebf07d-1825-4d2d-adf8-13626498c6f3', '98919046.99', '0.0421', '2025-08-16', '2024-02-05 21:58:21'),
('78594770-a8ae-4ccb-881b-12190200be41', 'test_sub_north_a', 'ed9d912c-cc62-4fde-9b9b-c74479e23848', '424083632.11', '0.0294', '2025-04-04', '2024-09-16 09:42:26'),
('39f8cc0a-1342-46e5-a5cc-647d08666c77', 'test_sub_east_b', '88670eaf-ed5b-4732-849c-7a954ee59d7e', '148179773.66', '0.0321', '2024-10-09', '2024-04-08 13:42:24'),
('2dc58a81-9aba-4476-9275-78e484fceb15', 'test_sub_north_a', '9a382c6c-d03d-4897-9e1d-dd2824f53300', '87426657.93', '0.0150', '2025-04-05', '2024-07-26 17:53:00'),
('a26fefa7-9cf3-4846-a95e-ee79e82513b4', 'test_sub_east_b', 'bdd88d10-6020-4d34-9519-6f91fa025daa', '215229130.92', '0.0150', '2025-04-26', '2024-08-26 14:28:43'),
('a876527c-03d0-4b01-b606-9de4f46c12ba', 'test_sub_east_a', '25d00d37-ee5e-4921-b138-0c3cc7060904', '396970831.85', '0.0080', '2024-11-21', '2024-12-03 02:18:32');

INSERT INTO restricted_account (id, entity_id, acct_no, restriction_type, status_6311, frozen_amount, created_at) VALUES
('46f55e05-6030-4371-804e-7325398f620e', 'test_sub_north_a', '6217****2530', 'regulatory_hold', NULL, '33672503.96', '2024-04-25 06:09:01'),
('225aa75d-0264-41f4-973e-e374583faef9', 'test_sub_east_a', '6228****8784', 'judicial_freeze', NULL, '22825266.80', '2024-11-18 18:12:45'),
('bcb14a26-e5b9-416d-a076-0f0370e3af93', 'test_sub_north_a', '6225****9099', 'escrow', NULL, '12274823.53', '2024-12-01 22:00:57'),
('6866746c-00b7-4da1-a04b-e96f4c4a4742', 'test_sub_east_a', '6225****4585', 'regulatory_hold', 'restricted', '40225081.82', '2024-12-22 16:29:03'),
('6f4d194e-8700-49e6-90ee-72d5af788541', 'test_sub_north_a', '6228****2988', 'escrow', 'restricted', '6753621.37', '2024-08-25 21:33:35');


-- 资金集中域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO cash_pool (id, entity_id, pool_name, total_balance, concentration_rate, created_at) VALUES
('0351c860-2570-439b-bfa4-636935c3231e', 'test_sub_north_a', '资金池_华北子公司A_1', '3778697567.64', '0.8476', '2024-08-14 19:52:46'),
('27a7aaeb-5a3b-442e-bdb4-0fd6af89a877', 'test_sub_north_a', '资金池_华北子公司A_2', '4535205104.98', '0.8640', '2024-08-16 05:47:55'),
('fd9819d8-9f37-406c-ba11-5e266582cb33', 'test_sub_east_b', '资金池_华东子公司B_3', '3761366164.64', '0.8675', '2024-11-22 08:49:49'),
('0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', 'test_sub_north_a', '资金池_华北子公司A_4', '2428139115.18', '0.7200', '2024-05-02 08:28:04'),
('c2060dc1-caae-4e33-be1c-f7de73b795b8', 'test_sub_north_a', '资金池_华北子公司A_5', '1435783472.81', '0.6000', '2024-05-19 10:20:57');

INSERT INTO collection_record (id, pool_id, source_acct, amount, collection_date, status, created_at) VALUES
('920a9f0e-194f-4371-bbc5-a6cda6719e06', '0351c860-2570-439b-bfa4-636935c3231e', '6228****3471', '23164584.90', '2024-12-21', 'completed', '2024-03-19 22:13:04'),
('34c848dd-3727-4b0d-a16d-4d5d6c780417', '0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', '6217****9890', '46619134.12', '2024-02-01', 'completed', '2024-04-15 13:24:57'),
('abfd5314-4062-49f2-8816-62a5e0686205', '0351c860-2570-439b-bfa4-636935c3231e', '6225****8814', '639313.55', '2024-06-29', 'completed', '2024-06-01 12:54:57'),
('7f3b7f66-91f1-48ce-8024-a3f0b0f247b4', 'c2060dc1-caae-4e33-be1c-f7de73b795b8', '6228****8999', '21981192.38', '2024-08-11', 'completed', '2024-09-05 00:24:21'),
('8e927c0d-c0f8-49af-a937-a5fd52596108', '0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', '6228****8657', '91958184.99', '2024-11-14', 'completed', '2024-09-30 00:58:25'),
('03c4ef70-d727-4622-b91d-2abf11a179f4', 'c2060dc1-caae-4e33-be1c-f7de73b795b8', '6222****2375', '64292827.32', '2024-03-10', 'completed', '2024-08-24 05:03:16'),
('3f3b8263-75e5-452a-9a09-ec503c3acd3e', 'fd9819d8-9f37-406c-ba11-5e266582cb33', '6228****8449', '32718238.20', '2024-07-13', 'completed', '2024-05-22 13:16:53'),
('3d1399bc-e2fd-41c4-a5b9-10867c566acc', '0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', '6222****9837', '5255956.54', '2024-06-28', 'completed', '2024-04-24 20:04:49'),
('571eaa07-9fcc-4aad-ad0c-606ede9e9efa', '0351c860-2570-439b-bfa4-636935c3231e', '6222****5051', '19976100.20', '2024-01-11', 'completed', '2024-11-14 04:15:08'),
('3a0abcc2-f692-46e1-bdf1-07585164faef', '0351c860-2570-439b-bfa4-636935c3231e', '6228****8619', '69961523.88', '2024-07-07', 'completed', '2024-03-26 19:38:47'),
('22ff0391-b67a-4ccb-a203-f990935ae157', '0351c860-2570-439b-bfa4-636935c3231e', '6228****6096', '10854470.03', '2024-01-14', 'completed', '2024-06-08 18:43:58'),
('27ba8115-3414-4f23-951e-4583211402ee', '0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', '6228****2245', '59230181.23', '2024-11-17', 'completed', '2024-05-04 03:44:49'),
('3196b87e-d27a-423f-aa5b-f9daafca1672', 'c2060dc1-caae-4e33-be1c-f7de73b795b8', '6222****1672', '34753016.34', '2024-08-07', 'completed', '2024-12-04 11:04:32'),
('e7e4c010-a3ad-409d-baa4-8116f47efaba', 'fd9819d8-9f37-406c-ba11-5e266582cb33', '6222****7882', '82241975.26', '2024-02-24', 'completed', '2024-08-09 11:40:57'),
('3090f431-9df1-4f1e-9012-df4db7696064', '27a7aaeb-5a3b-442e-bdb4-0fd6af89a877', '6228****9548', '96549099.44', '2024-05-18', 'pending', '2024-11-11 17:49:30'),
('e24185ca-f4b3-4911-bae7-eae688fa6f8a', '0d86bc71-5fe0-4dcd-8b6e-ba2f6b6a001f', '6217****6280', '85178730.34', '2024-02-14', 'failed', '2024-05-22 14:15:48'),
('665cea38-5c63-4c94-a5d6-33cb3e873fe5', 'c2060dc1-caae-4e33-be1c-f7de73b795b8', '6225****6511', '2918564.78', '2024-06-15', 'failed', '2024-04-03 15:13:22'),
('d5576f26-e61b-4ecb-87eb-43aec7587482', 'fd9819d8-9f37-406c-ba11-5e266582cb33', '6217****1166', '51686893.81', '2024-04-07', 'pending', '2024-02-13 07:46:26'),
('492bedfc-e515-4e77-9867-5c5044021c6c', 'c2060dc1-caae-4e33-be1c-f7de73b795b8', '6225****9041', '44845046.23', '2024-01-09', 'completed', '2024-02-17 09:14:25'),
('c7855fb2-1ec0-4d62-8e8d-ec0cdd861ef9', '27a7aaeb-5a3b-442e-bdb4-0fd6af89a877', '6217****8753', '55369621.85', '2024-06-25', 'pending', '2024-08-05 23:35:21');


-- 结算域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO settlement_record (id, entity_id, channel, amount, currency, counterparty, is_cross_bank, is_cross_border, is_internal, status, settled_at) VALUES
('1f83f2dc-f8e3-46bb-a15a-69ab93e529cd', 'test_sub_east_b', 'bank_transfer', '35145718.56', 'CNY', '国电投资', true, false, false, 'settled', '2024-06-05 08:14:07'),
('7ff91a07-410a-4c8d-8064-0a9afcc1b508', 'test_sub_north_a', 'online_banking', '9637288.83', 'CNY', '华能集团', false, false, false, 'settled', '2024-10-01 22:11:12'),
('7d2dd554-4682-4570-99b8-44937936a56e', 'test_sub_east_a', 'bill_payment', '36932846.63', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-28 16:38:18'),
('89957ffc-6d82-4f42-aa48-aa611f376ce6', 'test_sub_east_a', 'letter_of_credit', '41633091.88', 'USD', '中石化财务', false, true, false, 'settled', '2024-07-03 05:19:00'),
('b9e0a9d3-0060-4980-bdd6-47e2bb6eabfe', 'test_sub_north_a', 'guarantee_payment', '26711413.11', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-24 01:35:18'),
('9f481323-bc24-4e91-bd21-de316024403b', 'test_sub_north_a', 'collection', '47205039.84', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-22 00:36:18'),
('c8dad014-1252-4c43-b71c-e5812437b135', 'test_sub_east_b', 'remittance', '23940923.29', 'CNY', '国电投资', true, false, false, 'settled', '2024-04-04 01:16:55'),
('186e93c1-669c-49d1-9a14-62bae3d2314b', 'test_sub_east_b', 'entrusted_collection', '5713216.16', 'CNY', '华能集团', false, false, false, 'settled', '2024-07-24 15:04:36'),
('046c2c00-92dc-41d4-8202-a1a4cc4db069', 'test_sub_north_a', 'direct_debit', '34325686.40', 'CNY', '中石化财务', false, false, true, 'settled', '2024-03-17 18:19:05'),
('6172b172-4741-4c73-8a99-2349b54d589e', 'test_sub_east_a', 'bank_transfer', '5931393.59', 'CNY', '中铁建设', true, false, false, 'settled', '2024-11-06 19:50:39'),
('d62df5e6-3f35-44eb-98f3-0b6341f44f7b', 'test_sub_east_a', 'online_banking', '38786920.05', 'CNY', '中铁建设', false, false, false, 'settled', '2024-08-18 14:19:55'),
('5ca5a7b4-5d91-45cd-a61e-1014275a4a0c', 'test_sub_north_a', 'bill_payment', '49501662.71', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-18 19:03:39'),
('8a219f7e-0534-4e61-932c-2f0e89764dea', 'test_sub_north_a', 'letter_of_credit', '4970686.40', 'CNY', '中石化财务', false, true, false, 'settled', '2024-05-15 21:05:10'),
('13fb7db0-1308-4f4b-9946-1a0904d80e85', 'test_sub_east_a', 'guarantee_payment', '8698939.28', 'CNY', '华能集团', false, false, false, 'settled', '2024-03-21 00:26:28'),
('9606db19-223c-45d0-98f9-cf037c08a56e', 'test_sub_north_a', 'collection', '29694621.64', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-17 07:18:45'),
('3c78f8f4-47e4-48e2-b612-8c21f991d8aa', 'test_sub_east_b', 'remittance', '35152348.03', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-06 21:14:59'),
('43ab473b-c06a-4e9c-8511-18e94aca937b', 'test_sub_east_b', 'entrusted_collection', '39393523.05', 'CNY', '中交集团', false, false, false, 'settled', '2024-12-04 06:27:07'),
('183da869-50a8-438d-95b8-ac7064655531', 'test_sub_north_a', 'direct_debit', '11248224.42', 'CNY', '中石化财务', false, false, true, 'settled', '2024-05-16 04:04:03'),
('f98f9c04-5fec-43e0-90b8-54913c0dec23', 'test_sub_east_a', 'bank_transfer', '39633502.03', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-18 09:28:07'),
('f541b5a1-7914-4bd5-bab6-797bfec4d294', 'test_sub_east_b', 'online_banking', '34437012.78', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-19 16:34:31'),
('ededec0c-f1ac-44d4-9e72-61b29c400be8', 'test_sub_east_b', 'bill_payment', '4031288.18', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-09 23:20:38'),
('17aeb2d5-546a-4e66-9930-9afefbed14b2', 'test_sub_east_b', 'letter_of_credit', '1302985.97', 'CNY', '中交集团', false, true, false, 'settled', '2024-10-27 00:48:43'),
('a718a46a-e3c0-4bc0-9d87-7245a33e7b3c', 'test_sub_east_b', 'guarantee_payment', '28816586.76', 'CNY', '中石化财务', false, false, false, 'settled', '2024-08-28 16:41:28'),
('a5ffed39-3d7e-458e-ac4a-6a2821d81475', 'test_sub_east_b', 'collection', '9082642.47', 'CNY', '中交集团', false, false, false, 'settled', '2024-08-11 20:52:31'),
('1096f1d4-9ade-4b8a-a7cd-e3842e81c04e', 'test_sub_east_a', 'remittance', '23505819.64', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-19 10:42:06'),
('d57abbfa-3faf-460e-aafd-d1c130f38123', 'test_sub_east_a', 'entrusted_collection', '16496885.14', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-27 21:25:52'),
('52f16e56-b605-40c9-a201-207e2bee7781', 'test_sub_north_a', 'direct_debit', '1844489.54', 'CNY', '华能集团', false, false, true, 'settled', '2024-06-10 08:20:07'),
('7b8b050b-e136-4560-a058-11a70943fe3b', 'test_sub_east_b', 'bank_transfer', '43246880.10', 'CNY', '华能集团', true, false, false, 'settled', '2024-12-02 17:29:26'),
('e8cb4b12-6417-444c-b3d7-6e551dbc534b', 'test_sub_east_a', 'online_banking', '9387251.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-11-14 15:40:28'),
('f6ccf224-6b54-4027-bc6b-028a3f533f01', 'test_sub_east_a', 'bill_payment', '10185876.34', 'CNY', '中交集团', false, false, false, 'settled', '2024-03-08 09:28:56'),
('217b52b4-5427-41f2-beac-c45f76c4f9e2', 'test_sub_north_a', 'letter_of_credit', '24240742.73', 'CNY', '中交集团', false, true, false, 'settled', '2024-05-02 22:10:19'),
('e4a632dd-8b45-4752-83a9-1946a75f0948', 'test_sub_north_a', 'guarantee_payment', '693586.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-17 07:53:58'),
('3789b2d5-3586-4a51-a002-f9ef3bfe6299', 'test_sub_east_a', 'collection', '23077780.23', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-27 04:31:59'),
('6f3e5302-5686-4ff0-8ed0-1690c884a42c', 'test_sub_north_a', 'remittance', '14600159.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-07-31 15:30:15'),
('ef0e64f4-01f4-41e7-858b-4c6c76891d5e', 'test_sub_east_b', 'entrusted_collection', '27567741.19', 'CNY', '中铁建设', false, false, false, 'settled', '2024-04-07 19:32:47'),
('bd501dda-5d31-4bc2-9d84-5616ce4c42d2', 'test_sub_east_a', 'direct_debit', '43202706.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-07-31 10:59:50'),
('2d99f34c-fb60-4a30-a3be-8f4f1fc2e6de', 'test_sub_north_a', 'bank_transfer', '13365961.43', 'CNY', '华能集团', true, false, false, 'settled', '2024-05-24 23:19:53'),
('5d72e8cc-5df5-4e45-beec-edca6d019538', 'test_sub_north_a', 'online_banking', '29000369.96', 'CNY', '中铁建设', false, false, false, 'settled', '2024-03-17 14:34:30'),
('437cfda7-7c81-4168-8e8b-8c7ae0127f0c', 'test_sub_east_b', 'bill_payment', '16628673.39', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-12 14:59:20'),
('1502553d-af3f-4070-9ae9-475efe3c58ea', 'test_sub_east_a', 'letter_of_credit', '49038923.82', 'CNY', '中交集团', false, true, false, 'settled', '2024-07-15 07:54:49'),
('8a707dd1-bd70-494f-81f8-3217d4533dbd', 'test_sub_east_b', 'guarantee_payment', '2191928.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-27 12:24:42'),
('a549bdfc-6531-440f-be91-b1ce8235e053', 'test_sub_north_a', 'collection', '49041098.75', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-19 04:32:37'),
('35efa2fa-bf2f-4f64-a8dd-f744845dccff', 'test_sub_east_b', 'remittance', '43486318.66', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-21 16:58:29'),
('9460c61d-cca3-4bd3-b35f-3b16b757cccb', 'test_sub_east_a', 'entrusted_collection', '36124966.94', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-01 04:04:30'),
('3b9538b0-81f1-4521-bed0-680d4c82d84c', 'test_sub_east_b', 'direct_debit', '16934676.09', 'CNY', '中铁建设', false, false, true, 'settled', '2024-11-28 02:54:21'),
('fcabfccc-1bb7-4544-a6b2-895f4fc56219', 'test_sub_north_a', 'bank_transfer', '42968515.79', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-11 20:45:56'),
('35f2fe5d-0188-43dd-a576-34e6373f120f', 'test_sub_east_b', 'online_banking', '43620427.04', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-12 02:15:40'),
('6e0e4bc8-0504-4849-b3eb-d3efa60bed28', 'test_sub_north_a', 'bill_payment', '46047245.65', 'CNY', '中石化财务', false, false, false, 'settled', '2024-02-16 13:06:48'),
('93d31918-1bd8-48cd-95b6-02883a19eea1', 'test_sub_north_a', 'letter_of_credit', '35197502.56', 'CNY', '中铁建设', false, true, false, 'settled', '2024-03-26 22:19:57'),
('a363d318-5775-4faa-85c7-08062c4ce879', 'test_sub_east_a', 'guarantee_payment', '2309088.52', 'CNY', '华能集团', false, false, false, 'settled', '2024-05-30 11:23:27'),
('f4520420-8f6f-4d31-8230-7ebf4d50d504', 'test_sub_east_a', 'collection', '12217429.63', 'CNY', '中铁建设', false, false, false, 'settled', '2024-10-16 21:50:11'),
('4da46f75-e703-41da-97da-4062cfb2635e', 'test_sub_east_a', 'remittance', '8761717.06', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-14 19:43:15'),
('836bc004-977e-48b7-9f8a-7887c6c70545', 'test_sub_east_b', 'entrusted_collection', '45642322.51', 'CNY', '中石化财务', false, false, false, 'settled', '2024-04-28 14:40:16'),
('0f218f13-b6c8-4633-ae33-bb5f00b8cb5b', 'test_sub_east_b', 'direct_debit', '12773782.14', 'CNY', '华能集团', false, false, true, 'settled', '2024-08-26 09:43:34'),
('34fa04a4-76c4-496a-9cf6-436be663f1d4', 'test_sub_east_a', 'bank_transfer', '3702356.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-10-27 09:40:27'),
('28f96493-04da-4f62-afb7-723cc661a998', 'test_sub_north_a', 'online_banking', '12512410.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-04-11 12:54:30'),
('5ca2118a-e22e-45c7-98e5-bbd1149596ca', 'test_sub_east_a', 'bill_payment', '11867913.04', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-02 18:18:44'),
('88c1cdc9-6928-4435-96ed-2027c2edbca2', 'test_sub_east_b', 'letter_of_credit', '1106760.50', 'EUR', '中铁建设', false, true, false, 'settled', '2024-05-20 00:36:55'),
('f0b94d50-3d91-4db5-9419-b18193e86f45', 'test_sub_north_a', 'guarantee_payment', '38917797.67', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-06 23:31:53'),
('f21d60a0-09a2-4810-b696-a366ec46b770', 'test_sub_east_b', 'collection', '38789291.57', 'CNY', '中石化财务', false, false, false, 'settled', '2024-11-06 11:14:40'),
('dff73eee-79e4-4af2-ba60-a51caa1cedac', 'test_sub_east_a', 'remittance', '31048349.24', 'CNY', '中石化财务', true, false, false, 'settled', '2024-11-17 03:57:40'),
('2c51d5e7-5d83-471a-b7c2-f418235ba1bf', 'test_sub_north_a', 'entrusted_collection', '1980734.47', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-18 18:23:46'),
('5bcc3aab-7085-43b5-952a-0744185d7c72', 'test_sub_east_a', 'direct_debit', '4515767.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-06-16 23:26:11'),
('d8764365-6c43-41f0-9637-5f8c91b970d2', 'test_sub_east_a', 'bank_transfer', '6616668.29', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-06 16:32:58'),
('bee136e9-0d59-4c4a-95bf-3a277fe8051a', 'test_sub_east_b', 'online_banking', '41525326.25', 'CNY', '国电投资', false, false, false, 'settled', '2024-09-03 09:47:55'),
('9ad1dcf4-30a8-4e45-a7ea-a708e4904591', 'test_sub_east_b', 'bill_payment', '40213584.60', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-08 04:48:14'),
('47bdddb7-18cd-4fda-9443-ca66b8ff951d', 'test_sub_north_a', 'letter_of_credit', '36213593.44', 'USD', '中交集团', false, true, false, 'settled', '2024-07-06 02:50:25'),
('afe05a45-34ba-4dec-827b-e0b5d79a239d', 'test_sub_east_a', 'guarantee_payment', '13230284.33', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-20 11:43:47'),
('8a6eaf7f-df1c-4abe-b632-ad8688b780ed', 'test_sub_north_a', 'collection', '13115448.80', 'CNY', '中铁建设', false, false, false, 'settled', '2024-11-22 11:06:43'),
('2bc0bbe0-ba26-4e8a-b5a9-9c8852ea9ab3', 'test_sub_east_a', 'remittance', '23579128.63', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-14 10:58:39'),
('8db2fb3e-461c-4673-bcf3-15197911fea4', 'test_sub_east_a', 'entrusted_collection', '32386142.51', 'CNY', '中铁建设', false, false, false, 'pending', '2024-12-24 09:41:26'),
('0ff6f833-6b4c-4b02-80c9-5da1b294e95e', 'test_sub_east_a', 'direct_debit', '6997452.86', 'CNY', '华能集团', false, false, true, 'pending', '2024-06-04 15:07:06'),
('28c8be00-ea14-41b1-b4dc-7bfc559bb69c', 'test_sub_east_a', 'bank_transfer', '44364092.83', 'CNY', '中石化财务', true, false, false, 'pending', '2024-07-17 14:23:42'),
('50f47419-8ddc-4689-9a2b-c3f4de78d540', 'test_sub_north_a', 'online_banking', '34827234.74', 'CNY', '中交集团', false, false, false, 'pending', '2024-08-02 18:47:46'),
('4407cf06-dc95-4147-9821-2a3f68a6d157', 'test_sub_east_a', 'bill_payment', '44271835.06', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-07 19:26:17'),
('b274ac4b-cbc9-4388-98ee-401e5d8eb9ca', 'test_sub_east_a', 'letter_of_credit', '34517130.38', 'CNY', '中铁建设', false, true, false, 'pending', '2024-08-15 07:54:23'),
('6652493a-7901-4328-9c53-288de7ed22a6', 'test_sub_east_a', 'guarantee_payment', '49046576.64', 'CNY', '国电投资', false, false, false, 'pending', '2024-10-05 20:22:03'),
('0f0fa08a-b750-4361-97a1-6147a3afbf54', 'test_sub_east_b', 'collection', '13801313.23', 'CNY', '华能集团', false, false, false, 'pending', '2024-08-20 02:42:13'),
('72e572e0-0075-488b-90a5-f1678dcb6268', 'test_sub_north_a', 'remittance', '31978251.00', 'CNY', '华能集团', true, false, false, 'pending', '2024-01-26 10:15:08'),
('afd228aa-8e9f-4eee-9ad9-05d96e3f9d36', 'test_sub_north_a', 'entrusted_collection', '10268226.70', 'CNY', '中交集团', false, false, false, 'pending', '2024-04-16 18:13:52'),
('d817689c-8c47-4fad-a9f4-a902ad8b6afd', 'test_sub_east_a', 'direct_debit', '16434692.08', 'CNY', '中石化财务', false, false, true, 'pending', '2024-11-01 00:17:54'),
('0d782c76-7e95-4ecd-8ed8-01de4342a191', 'test_sub_east_a', 'bank_transfer', '49376489.95', 'CNY', '中交集团', true, false, false, 'pending', '2024-05-08 05:07:42'),
('61e5671a-11d1-4445-9f0b-f7e413966da1', 'test_sub_east_a', 'online_banking', '6598843.45', 'CNY', '国电投资', false, false, false, 'pending', '2024-05-01 18:20:01'),
('eee37299-ad71-4d39-9f8e-088f8c76efcb', 'test_sub_east_a', 'bill_payment', '13275721.74', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-03 16:07:47'),
('1e495496-f343-4dbc-819a-31048ed36abe', 'test_sub_east_a', 'letter_of_credit', '23817535.81', 'USD', '中交集团', false, true, false, 'pending', '2024-10-30 03:28:32'),
('1ccf562b-5c76-4c88-8d1d-8e148132a4ac', 'test_sub_east_a', 'guarantee_payment', '47271327.99', 'CNY', '华能集团', false, false, false, 'pending', '2024-12-03 16:19:29'),
('bd2b6a58-a210-4640-9db2-f0f9a5d2fbbb', 'test_sub_north_a', 'collection', '48201668.89', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-02 12:27:43'),
('ec832b66-5d8f-4f71-bf5f-0ff1cd586987', 'test_sub_east_a', 'remittance', '24518540.02', 'CNY', '中铁建设', true, false, false, 'pending', '2024-02-07 02:20:38'),
('74f2330b-e6b0-4497-8a4a-a8c75bd82935', 'test_sub_east_a', 'entrusted_collection', '3293454.84', 'CNY', '国电投资', false, false, false, 'pending', '2024-11-15 20:37:35'),
('c4fc310f-9148-4f67-98ba-bdef0d1ba790', 'test_sub_north_a', 'direct_debit', '16266020.31', 'CNY', '中交集团', false, false, true, 'pending', '2024-09-28 09:29:32'),
('5231ff19-d7ca-40c7-9e30-d37ec169e96f', 'test_sub_north_a', 'bank_transfer', '21515664.30', 'CNY', '华能集团', true, false, false, 'pending', '2024-12-01 20:56:49'),
('6bbeed9f-218e-43a8-b97c-bd4817b4d95b', 'test_sub_north_a', 'online_banking', '36044787.43', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-08 14:56:14'),
('c36da480-f9d7-49d2-9cda-2b9956dbc46b', 'test_sub_east_b', 'bill_payment', '16953191.63', 'CNY', '中铁建设', false, false, false, 'pending', '2024-07-23 13:46:06'),
('4b1ba3ce-caac-4333-aa5c-917d7e56d99c', 'test_sub_east_b', 'letter_of_credit', '21343932.67', 'EUR', '国电投资', false, true, false, 'pending', '2024-07-10 04:43:59'),
('6cf133d4-3867-40d5-b207-e7638bd36491', 'test_sub_east_b', 'guarantee_payment', '3365994.07', 'CNY', '华能集团', false, false, false, 'pending', '2024-02-17 13:06:47'),
('ffcdb9ce-6167-44ed-9dcf-49d56f739ede', 'test_sub_north_a', 'collection', '18638616.50', 'CNY', '中石化财务', false, false, false, 'pending', '2024-10-11 01:37:35'),
('3ada1c62-0fe5-49fa-89b5-84007af9336c', 'test_sub_north_a', 'remittance', '16489002.61', 'CNY', '华能集团', true, false, false, 'pending', '2024-07-29 11:55:42'),
('53ed1e61-e790-45e5-a891-bc9ecb8a6e39', 'test_sub_east_b', 'entrusted_collection', '43405926.52', 'CNY', '华能集团', false, false, false, 'pending', '2024-05-27 19:19:22'),
('1b30d5ba-04d9-4051-bb9c-1cd31d4715e2', 'test_sub_east_a', 'direct_debit', '28900146.73', 'CNY', '中石化财务', false, false, true, 'pending', '2024-03-20 21:30:14'),
('4d7a7e04-3bee-4296-b4c8-f3be1b6e20ec', 'test_sub_east_a', 'bank_transfer', '17512198.57', 'CNY', '中交集团', true, false, false, 'pending', '2024-07-07 03:48:17');

INSERT INTO payment_channel (id, channel_name, channel_type, is_direct_linked, daily_limit) VALUES
('58fa040d-eedd-4aeb-8283-7436b1d820a2', '银行转账', 'bank_transfer', true, '23389750.34'),
('1dd4caa5-b133-4f7b-ae02-872b152019b1', '网上银行', 'online_banking', true, '84670360.97'),
('4a462f6b-1df7-49ac-84e9-339e2d40ed37', '票据支付', 'bill_payment', true, '61743754.77'),
('f6604e40-8c77-4374-8c2a-ecccb25fd3dd', '信用证', 'letter_of_credit', true, '56117235.76'),
('5fe0d53b-7886-49f1-9355-e6b5822b6539', '保函支付', 'guarantee_payment', true, '92979344.81'),
('fc7a74bf-21f1-47bf-b0d9-0d5e77bb44e6', '托收', 'collection', true, '27477324.79'),
('fc340652-a59d-4d78-8401-631be278a37b', '汇款', 'remittance', true, '28053768.48'),
('d77c158b-1d14-4e59-99e5-b38840554a43', '委托收款', 'entrusted_collection', true, '92232214.58'),
('0290f6ba-c1e8-49b7-af98-fec069d47136', '直接扣款', 'direct_debit', false, '1604473.15');


-- 票据域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO bill (id, entity_id, bill_type, face_value, issue_date, maturity_date, status, is_overdue, created_at) VALUES
('6594112d-11f6-4bec-a628-f7fc18ea02fc', 'test_sub_east_a', 'commercial_draft', '3572312.52', '2024-05-24', '2025-03-15', 'active', false, '2024-11-20 00:05:47'),
('7202ffb8-da1f-4687-8718-b07a95f3822b', 'test_sub_north_a', 'bank_acceptance', '21049641.44', '2024-02-25', '2024-12-03', 'active', false, '2024-06-23 05:23:19'),
('99be2766-cc97-499c-8669-ad22a7629556', 'test_sub_north_a', 'electronic_commercial', '44178775.01', '2024-03-24', '2024-08-04', 'active', false, '2024-03-20 05:48:39'),
('7e6b478e-d4c8-4ab3-b95a-d103acc0d5b3', 'test_sub_east_a', 'commercial_draft', '13677931.89', '2024-06-21', '2024-10-30', 'active', false, '2024-12-04 13:31:38'),
('38ddeed8-ecc9-453b-a29c-00fb2255fd13', 'test_sub_east_b', 'bank_acceptance', '10856891.37', '2024-04-16', '2024-12-01', 'active', false, '2024-09-19 03:22:27'),
('cd6d6980-1955-48a2-997b-07ea48bff680', 'test_sub_east_a', 'electronic_commercial', '26394011.95', '2024-03-13', '2025-02-15', 'active', false, '2024-06-06 01:14:25'),
('48abcd19-5448-40b9-aa92-ff88cdfdc44f', 'test_sub_north_a', 'commercial_draft', '10300713.91', '2024-01-15', '2024-04-17', 'active', false, '2024-04-18 04:48:16'),
('4c2fdc82-8189-4cdf-8a98-3d0de57edab3', 'test_sub_east_b', 'bank_acceptance', '485722.34', '2024-03-24', '2024-08-22', 'active', false, '2024-08-08 05:08:24'),
('e2daaa38-088b-4ace-9ccd-fedabb971218', 'test_sub_north_a', 'electronic_commercial', '25063091.09', '2024-06-29', '2025-01-22', 'active', false, '2024-12-08 11:04:25'),
('c324ae4a-737f-4765-9618-dd8501dc4a71', 'test_sub_north_a', 'commercial_draft', '1035202.68', '2024-01-11', '2024-11-19', 'active', false, '2024-02-09 10:36:27'),
('787c0849-e3f5-41da-98f6-2f89bfd11658', 'test_sub_north_a', 'bank_acceptance', '14546808.76', '2024-04-13', '2025-02-10', 'active', false, '2024-07-26 00:20:10'),
('a031b13e-1039-4aa3-8005-9a1b77e48fda', 'test_sub_north_a', 'electronic_commercial', '4497681.08', '2024-04-27', '2025-01-27', 'active', false, '2024-02-24 07:27:37'),
('50b0e0f9-d1b0-4419-8ddb-d1b4a3cb37cc', 'test_sub_east_b', 'commercial_draft', '19848758.17', '2024-05-14', '2024-09-21', 'active', false, '2024-06-07 23:21:14'),
('594e5a6b-8042-4d47-8803-94d6f8f3ee13', 'test_sub_east_b', 'bank_acceptance', '25573115.90', '2024-02-13', '2024-06-21', 'active', false, '2024-02-28 16:32:12'),
('d2d12532-eb61-4614-82f5-c7764650000d', 'test_sub_east_b', 'electronic_commercial', '11889815.56', '2024-03-30', '2024-09-11', 'active', false, '2024-03-15 08:12:11'),
('9dd2fde0-2b4c-4fd6-8f1c-9ccf6a928000', 'test_sub_north_a', 'commercial_draft', '8939591.83', '2024-02-09', '2024-06-16', 'active', false, '2024-11-17 15:29:48'),
('12b49bcd-8773-4676-8445-4b57095d24d1', 'test_sub_north_a', 'bank_acceptance', '34088560.57', '2024-05-28', '2025-04-12', 'active', false, '2024-10-16 20:40:39'),
('81c67d44-4272-4ce1-8cd5-04e2279b422d', 'test_sub_east_b', 'electronic_commercial', '7632774.33', '2024-06-09', '2025-02-15', 'active', false, '2024-02-04 15:28:40'),
('0157785c-70d5-484c-8c20-04b8ea9afd0a', 'test_sub_east_b', 'commercial_draft', '17661916.91', '2024-03-11', '2024-07-07', 'active', false, '2024-02-07 09:29:28'),
('bee3cfec-aaa8-4bbe-8269-263d146269b5', 'test_sub_east_a', 'bank_acceptance', '41601661.92', '2024-01-15', '2024-10-19', 'active', false, '2024-02-09 20:55:54'),
('74286ce8-254d-42a2-b8ee-a96c9575d505', 'test_sub_east_a', 'electronic_commercial', '19285675.58', '2024-06-06', '2025-05-21', 'active', false, '2024-10-24 17:50:47'),
('0513c204-a4ad-4a97-804e-b56b155eb3a4', 'test_sub_east_a', 'commercial_draft', '16144185.47', '2024-04-25', '2024-10-28', 'pending', false, '2024-08-31 16:09:03'),
('34eed210-f089-441c-ae96-ae489070edc4', 'test_sub_east_b', 'bank_acceptance', '49121040.50', '2024-01-27', '2024-10-18', 'pending', false, '2024-02-13 16:41:11'),
('2b0ed39f-29f7-4a7f-82a8-3d5bdc994239', 'test_sub_east_a', 'electronic_commercial', '49550202.53', '2024-03-04', '2025-01-12', 'pending', false, '2024-09-25 16:39:10'),
('324a4958-38bb-4c82-9186-fdd92c07070f', 'test_sub_east_b', 'commercial_draft', '19432086.32', '2024-04-05', '2024-11-25', 'pending', false, '2024-06-22 21:38:03'),
('b9f5d8de-19be-4786-92ad-48eda7aed0f0', 'test_sub_north_a', 'bank_acceptance', '3389001.53', '2024-06-14', '2025-03-02', 'pending', false, '2024-02-18 17:43:24'),
('440371ee-0d26-47a7-a8ff-754e6cc1da33', 'test_sub_east_b', 'electronic_commercial', '16734765.60', '2024-03-05', '2024-08-18', 'pending', false, '2024-10-25 21:09:58'),
('c59bee8e-74f9-4c82-9a0b-5e997eaad298', 'test_sub_east_b', 'commercial_draft', '6534687.75', '2024-03-20', '2025-01-04', 'overdue', true, '2024-12-28 02:19:35'),
('5d243c30-ea7a-4865-aa6f-1295ea34a105', 'test_sub_east_b', 'bank_acceptance', '40677920.71', '2024-06-13', '2025-02-26', 'overdue', true, '2024-12-09 22:53:47'),
('1bd51fd6-130f-4bc3-816b-a0a11c527e28', 'test_sub_north_a', 'electronic_commercial', '32336638.55', '2024-05-14', '2024-09-28', 'overdue', true, '2024-08-04 16:23:01');

INSERT INTO endorsement_chain (id, bill_id, endorser_id, endorsee_id, endorse_date, sequence_no) VALUES
('e4ff39f7-38df-4dba-aabd-4e5c69441489', 'c324ae4a-737f-4765-9618-dd8501dc4a71', 'test_sub_east_a', 'test_sub_north_a', '2024-06-23', 1),
('28d88433-ee72-4833-a0cc-dbbc662a159f', '48abcd19-5448-40b9-aa92-ff88cdfdc44f', 'test_sub_east_a', 'test_sub_north_a', '2024-03-20', 2),
('f39744c6-6202-4d09-ac70-ef9e40c6e736', 'c324ae4a-737f-4765-9618-dd8501dc4a71', 'test_sub_east_a', 'test_sub_north_a', '2024-12-04', 3),
('f9baf8a4-f9ba-47b1-8c53-5da4f322074b', '5d243c30-ea7a-4865-aa6f-1295ea34a105', 'test_sub_north_a', 'test_sub_east_a', '2024-11-01', 4),
('ab863ced-f57e-4192-818d-12863bd06b10', '38ddeed8-ecc9-453b-a29c-00fb2255fd13', 'test_sub_east_a', 'test_sub_north_a', '2024-12-20', 5),
('53f6228b-ec2e-4f0b-b2fe-878d9aa38ed7', 'b9f5d8de-19be-4786-92ad-48eda7aed0f0', 'test_sub_east_a', 'test_sub_east_b', '2024-01-23', 6),
('768cf610-5c5b-42a9-9eec-e0c358638d3c', 'a031b13e-1039-4aa3-8005-9a1b77e48fda', 'test_sub_north_a', 'test_sub_east_a', '2024-08-15', 7),
('447ac1da-d07f-46c2-be07-c7fbf4d016cb', 'c324ae4a-737f-4765-9618-dd8501dc4a71', 'test_sub_north_a', 'test_sub_east_b', '2024-04-29', 8),
('aa407ec4-92c5-45ed-9aa9-f1db6e095215', '4c2fdc82-8189-4cdf-8a98-3d0de57edab3', 'test_sub_east_b', 'test_sub_north_a', '2024-04-09', 9),
('37e2a4c4-272f-478b-b7a8-179bfbff2846', '0513c204-a4ad-4a97-804e-b56b155eb3a4', 'test_sub_north_a', 'test_sub_east_b', '2024-08-24', 10),
('97d8f2fe-a771-4b15-bfa2-4a2c5e79c06c', '324a4958-38bb-4c82-9186-fdd92c07070f', 'test_sub_east_b', 'test_sub_north_a', '2024-03-23', 11),
('e311a512-47cb-418b-8547-db6cbad82d3e', 'b9f5d8de-19be-4786-92ad-48eda7aed0f0', 'test_sub_north_a', 'test_sub_east_a', '2024-05-08', 12),
('031b6b65-7b12-45ae-841a-55473f42166b', '74286ce8-254d-42a2-b8ee-a96c9575d505', 'test_sub_east_b', 'test_sub_north_a', '2024-10-10', 13),
('cf8fa014-236b-427c-b530-fd66776dca46', '34eed210-f089-441c-ae96-ae489070edc4', 'test_sub_north_a', 'test_sub_east_a', '2024-05-25', 14),
('8f87f298-387c-4ad1-8519-cd40c2b391e7', '324a4958-38bb-4c82-9186-fdd92c07070f', 'test_sub_east_a', 'test_sub_east_b', '2024-08-18', 15);


-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('9f964448-7109-4717-b54d-6c883e597ee5', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('aadd633e-1f98-45be-9c19-d60c61345697', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('79cc152c-6e2a-471c-9e05-4dc994d03255', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('ae2c91c9-637c-4194-a93c-f7fd390070d5', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('746b96c6-715b-44bf-9569-c8f280b40eca', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('06e89e46-da5e-407d-a5c4-f83e2ad7e835', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('511dc81d-f505-4378-8d47-19ab24881964', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('7846d896-052a-4336-9cc2-e5772d999282', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('276bbd1b-e7e6-4baf-ad58-46accbdfb3ab', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('53ff9b4a-26f9-48ae-aca1-008b95a641e1', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('c14a9ce6-254e-47bc-a49f-50d9abb9fc0f', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('5a212d2f-78f3-4341-88ef-84d877ed7a7c', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('f8ac3f09-7aca-4808-8dd4-1c2bf4ae97f1', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('deac6065-b7ef-4147-ac71-231eb303afbe', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('92b11531-b134-42bb-890b-d7e1c4751a98', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('08b0f3b7-bf30-4690-9c45-53b2fd987e8c', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('cdb7aa94-0005-4a57-a139-363fe9383a18', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('b0517c2f-7d60-41cc-80d8-1ceb6b37670a', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('1f4d442a-2ff1-4622-8112-ae54b700179d', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('a0d2c09e-c9f3-46dc-a2b8-2a28b1432625', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');


-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('623dac87-4a5e-4568-b6d9-66213b0aef90', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('242cccf9-dfb6-4ee5-9dce-55465cce98f1', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('ac30351e-dc5a-489a-ba2d-f10de4703baa', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('3eebda0c-773f-407e-8f5b-45b4899620e0', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('075143c4-d4c2-40ef-ac1d-bb8e03e628f3', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('13aacd97-b48b-40cf-8256-34353b806158', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('0ddd50fe-3f37-45ed-adbe-95bc1f86a478', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('0e3a103c-6b59-4a96-8fe0-3522fcfc24c7', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('2f4d0c42-554b-414b-9b95-4eb18afff66a', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('c4a316ff-a4ca-438c-ae67-ddf368e0ac9a', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('4e8c198a-b1ca-49db-b200-987d38ae2a94', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('20c82c38-0da6-4394-b4cb-9884e665744e', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('7177c527-f0fe-4143-b718-b7f33b492ecc', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('7de8abec-511a-47da-8638-80b196ff870a', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('c61e51ca-6efc-4c83-8286-3a31e1843af6', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('932ec08d-da13-4a45-be86-a0df3836b6fc', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('7aaa87be-357a-46dc-b211-c6db21953426', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('e91445ca-0b92-411d-bd32-04c529f687e6', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('85fc906b-fe37-4cf3-b7f4-fe0460943f94', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('1394c447-e5c8-47d7-8129-61bc17236226', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('2ad2b39b-9fd7-49dc-af0f-e24f16dbf886', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('82e86031-aa5a-4059-b845-83a3a8fba486', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('9c0bcf32-696b-4b60-9c36-a324f2a18036', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('fb59301e-9b04-4e64-855b-42a6c91c5297', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('6196bc48-09aa-4cdc-bdf8-109147f4f4b6', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('1cfb21f4-a41b-46a5-8643-3a6b915ddb39', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('d6a2dcd7-dab2-46d1-9c78-3fe47ba350d6', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('34ab134c-f7f3-4f97-acae-a345f1a0010f', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('656d6b88-60a2-421a-802c-19d1e050aa54', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('9f8e928c-b8e7-4ed2-a384-5e32280b6966', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');


-- 国资委考核域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO financial_report (id, entity_id, report_type, period, total_asset, net_asset, revenue, profit, rd_expense, employee_count, operating_cash_flow) VALUES
('ad8424f2-4660-4181-984b-eee0138e2503', 'test_group_hq', 'annual', '2024', '47861229725.12', '18299038102.21', '6437712433.76', '717436878.38', '164842161.67', 42507, '926315918.56'),
('57a0cf64-ecf6-4ac2-b608-547728ea834a', 'test_region_east', 'annual', '2024', '8555519077.10', '4257396222.61', '7346011300.15', '811836290.54', '518274321.86', 37437, '301852087.26'),
('c8989d44-47c9-4d88-b132-513ac0ce7a20', 'test_region_north', 'annual', '2024', '4979919889.78', '2911082170.28', '7824712503.55', '598321264.29', '255465147.94', 37995, '2141275239.95'),
('15fe7315-15f0-4b0d-a203-393b9ea8406d', 'test_sub_east_a', 'annual', '2024', '2484009030.49', '1407685593.63', '5682986093.70', '648944324.54', '216667520.45', 16548, '4042971955.66'),
('d0e5389f-754e-45b0-b625-0b7e390b53f7', 'test_sub_east_b', 'annual', '2024', '20898533810.48', '9113082362.28', '7041828930.89', '463408993.06', '316440812.83', 30937, '1099712766.46'),
('8d94868f-d736-49a4-b20e-f477450d9939', 'test_sub_north_a', 'annual', '2024', '8039765866.97', '4489771254.78', '3533505730.14', '525793910.26', '143892245.92', 26630, '740754142.61');

INSERT INTO assessment_indicator (id, entity_id, indicator_code, indicator_name, target_value, actual_value, period) VALUES
('c90d0d31-e96c-4eee-9c47-5a21b1d6b59f', 'test_group_hq', 'AI001', '净资产收益率', '0.1272', '0.1313', '2024'),
('226bacd7-b445-400e-b4b4-e264ce2b8cc4', 'test_group_hq', 'AI002', '营业收入利润率', '0.1200', '0.1296', '2024'),
('c5c4741e-8ff5-4ffb-bbc7-06752a444746', 'test_group_hq', 'AI003', '研发投入强度', '0.0711', '0.0722', '2024'),
('45dd8b91-b56f-4220-9d09-bbbfde91d051', 'test_group_hq', 'AI004', '全员劳动生产率', '0.1796', '0.2021', '2024'),
('a7306785-e26c-482f-a584-8fc976f11947', 'test_group_hq', 'AI005', '资产负债率', '0.1720', '0.2202', '2024'),
('6624d46d-19e5-4470-a283-98d9eff370ca', 'test_group_hq', 'AI006', '经营性现金流比率', '0.0969', '0.1191', '2024'),
('2dfed0f6-fa17-44f4-9556-967d0a8718c4', 'test_group_hq', 'AI007', '总资产周转率', '0.1994', '0.2273', '2024'),
('6eac688f-6d1d-48ff-ac28-e2d5b03421ee', 'test_group_hq', 'AI008', '成本费用利润率', '0.1246', '0.1280', '2024'),
('69491a18-758d-4413-9c4f-7b069f16c143', 'test_group_hq', 'AI009', '国有资本保值增值率', '0.1258', '0.1623', '2024'),
('c7f472dc-7525-4b0b-b8e3-d05dcb1e903e', 'test_region_east', 'AI001', '净资产收益率', '0.1375', '0.1395', '2024'),
('ab5f6d3b-ba8f-427b-83c1-4a5441b00821', 'test_region_east', 'AI002', '营业收入利润率', '0.1242', '0.1571', '2024'),
('1e2ea790-637d-428d-aef4-328d74e23b2a', 'test_region_east', 'AI003', '研发投入强度', '0.1509', '0.1638', '2024'),
('ee14905b-3c9c-40ed-adba-a982da498da1', 'test_region_east', 'AI004', '全员劳动生产率', '0.1771', '0.2000', '2024'),
('53c6b967-8f42-4b8f-aca1-756b72156af5', 'test_region_east', 'AI005', '资产负债率', '0.1591', '0.1956', '2024'),
('ac85eae4-df49-44cb-a7c8-071964a1288a', 'test_region_east', 'AI006', '经营性现金流比率', '0.0568', '0.0577', '2024'),
('50eed2bc-ab08-4b17-85c6-099d4fab1f05', 'test_region_east', 'AI007', '总资产周转率', '0.0792', '0.0923', '2024'),
('5f8283d1-f79c-45fd-9d55-018af9c15e93', 'test_region_east', 'AI008', '成本费用利润率', '0.1080', '0.1226', '2024'),
('27e80117-db40-45ce-82a8-124cbc6ac3d0', 'test_region_east', 'AI009', '国有资本保值增值率', '0.0920', '0.1193', '2024'),
('d9c5fa3c-6194-4c94-a9a4-98dee6480d37', 'test_region_north', 'AI001', '净资产收益率', '0.1417', '0.1472', '2024'),
('6cdadd92-af42-4160-b07e-38efd3d85003', 'test_region_north', 'AI002', '营业收入利润率', '0.1091', '0.1351', '2024'),
('25d05dd9-c7f2-43c1-b852-5427bfbac109', 'test_region_north', 'AI003', '研发投入强度', '0.1337', '0.1484', '2024'),
('f53cdd15-454a-4936-bfac-4a2525a89854', 'test_region_north', 'AI004', '全员劳动生产率', '0.0799', '0.0921', '2024'),
('c179b8b8-69d0-4a3f-843d-d9e6a1628719', 'test_region_north', 'AI005', '资产负债率', '0.0560', '0.0567', '2024'),
('09e14458-7e4e-4e7d-896a-8e9503624f81', 'test_region_north', 'AI006', '经营性现金流比率', '0.1000', '0.1142', '2024'),
('15f2eea6-8209-409c-8a3e-6500ab6c23f9', 'test_region_north', 'AI007', '总资产周转率', '0.0723', '0.0917', '2024'),
('2478b8f5-8039-43fb-8f3c-d4307b8c53e7', 'test_region_north', 'AI008', '成本费用利润率', '0.0992', '0.1174', '2024'),
('590cc275-13f4-45c5-8e06-ceb2bd44d1d4', 'test_region_north', 'AI009', '国有资本保值增值率', '0.1089', '0.1290', '2024'),
('0e304262-d256-40da-846b-92f65790a70f', 'test_sub_east_a', 'AI001', '净资产收益率', '0.1391', '0.1603', '2024'),
('7d613c46-ad8a-4510-be77-bb906621b191', 'test_sub_east_a', 'AI002', '营业收入利润率', '0.1299', '0.1575', '2024'),
('ae979668-f18a-400a-abb0-762a7f7a4fa0', 'test_sub_east_a', 'AI003', '研发投入强度', '0.1212', '0.1218', '2024'),
('58f19690-3e7e-4b80-aa9e-d20eab79abdd', 'test_sub_east_a', 'AI004', '全员劳动生产率', '0.1511', '0.1955', '2024'),
('23cf935e-42a0-47a3-84d7-1c16cd606ea3', 'test_sub_east_a', 'AI005', '资产负债率', '0.0962', '0.1221', '2024'),
('f983336f-742b-477c-b04f-b65297d08457', 'test_sub_east_a', 'AI006', '经营性现金流比率', '0.1444', '0.1703', '2024'),
('ee3031db-3fea-42ea-a5ee-ac0bea5f3418', 'test_sub_east_a', 'AI007', '总资产周转率', '0.1951', '0.2409', '2024'),
('c62890b0-f1bb-4518-b552-93cb2b0d7373', 'test_sub_east_a', 'AI008', '成本费用利润率', '0.1366', '0.1662', '2024'),
('1d854ff3-3e9d-4321-a3b4-a15243aceeef', 'test_sub_east_a', 'AI009', '国有资本保值增值率', '0.1221', '0.1413', '2024'),
('1cab061a-9e6d-4416-9df1-35aa1013e5da', 'test_sub_east_b', 'AI001', '净资产收益率', '0.1430', '0.1791', '2024'),
('42c8d39f-dad0-4a38-a57d-f6f6296ab52e', 'test_sub_east_b', 'AI002', '营业收入利润率', '0.1732', '0.1531', '2024'),
('89d09645-64d5-4331-8343-de594c6f6244', 'test_sub_east_b', 'AI003', '研发投入强度', '0.1922', '0.1663', '2024'),
('c14d5ab5-1e42-4463-b35f-9ac3578e6572', 'test_sub_east_b', 'AI004', '全员劳动生产率', '0.1162', '0.1056', '2024'),
('db2d07dd-2b11-4fcc-b314-4288e5dccd1d', 'test_sub_east_b', 'AI005', '资产负债率', '0.1536', '0.1394', '2024'),
('3c9aa7b9-7794-4fca-ab5a-c9bbb7eb97c7', 'test_sub_east_b', 'AI006', '经营性现金流比率', '0.1881', '0.1829', '2024'),
('9f0e553e-e899-497a-a843-b0cb29edb7f6', 'test_sub_east_b', 'AI007', '总资产周转率', '0.1591', '0.1510', '2024'),
('3ff49a1a-4218-4e5a-8443-14e193687e72', 'test_sub_east_b', 'AI008', '成本费用利润率', '0.0811', '0.0726', '2024'),
('36c27e4c-4ea6-4fad-ac08-82644f6a8f0b', 'test_sub_east_b', 'AI009', '国有资本保值增值率', '0.1218', '0.1100', '2024'),
('3bec50e8-47c4-4a33-a33c-4b92938b39b4', 'test_sub_north_a', 'AI001', '净资产收益率', '0.1189', '0.1099', '2024'),
('24c05f20-5fa8-4418-b7af-838fabee6cd2', 'test_sub_north_a', 'AI002', '营业收入利润率', '0.1031', '0.0988', '2024'),
('c8c28976-4784-4c8d-af0a-362e4e165edf', 'test_sub_north_a', 'AI003', '研发投入强度', '0.1521', '0.1464', '2024'),
('8b962bf7-41e7-4d98-a0e3-f091c6341a6b', 'test_sub_north_a', 'AI004', '全员劳动生产率', '0.1415', '0.0789', '2024'),
('0219b078-53ca-4eeb-9581-167f9a322ce7', 'test_sub_north_a', 'AI005', '资产负债率', '0.0919', '0.0542', '2024'),
('054ddec1-d976-4679-8258-096c2c444307', 'test_sub_north_a', 'AI006', '经营性现金流比率', '0.1657', '0.1179', '2024'),
('a7c4d07f-45f0-48c4-a130-d58b5b61494f', 'test_sub_north_a', 'AI007', '总资产周转率', '0.1557', '0.0927', '2024'),
('6471f7cc-297f-4877-af94-4294425ef43f', 'test_sub_north_a', 'AI008', '成本费用利润率', '0.1341', '0.1046', '2024'),
('da5eb645-c40c-42c8-a32e-a4665ab22859', 'test_sub_north_a', 'AI009', '国有资本保值增值率', '0.0910', '0.0488', '2024');

