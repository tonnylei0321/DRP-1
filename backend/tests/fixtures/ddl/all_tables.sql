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
('743c795d-ff52-4fb9-8f26-58f8640fbb92', 'test_sub_north_a', 'BOC', '6222****5506', '244967364.62', 'CNY', true, 'configured', NULL, false, '2024-03-12 23:06:43'),
('f1b115af-2444-48a9-bd16-12bf6436cf7c', 'test_sub_north_a', 'SPDB', '6222****7912', '31879501.21', 'CNY', true, 'configured', NULL, false, '2024-02-17 06:14:32'),
('41eeecfb-e7fa-4fb4-bdc1-f302891fb62d', 'test_sub_north_a', 'ICBC', '6228****9928', '419577868.98', 'CNY', true, 'configured', NULL, false, '2024-08-17 18:17:51'),
('26a65d8f-0538-4a99-ad56-4c9cbe376ebb', 'test_sub_east_a', 'CCB', '6225****6574', '277943554.54', 'CNY', true, 'configured', NULL, false, '2024-04-20 10:06:05'),
('6e546a22-55bb-454a-b16d-dfa6b96b58f0', 'test_sub_east_b', 'BOC', '6217****6635', '603765658.76', 'CNY', true, 'configured', NULL, false, '2024-01-23 23:29:34'),
('84b3e1ac-a0b4-40c2-be63-cd7e9db21225', 'test_sub_east_a', 'CITIC', '6222****5803', '829421723.79', 'CNY', true, 'configured', NULL, false, '2024-11-12 11:36:12'),
('a46c5132-9b6a-4a35-afba-181afbd930a7', 'test_sub_north_a', 'BOC', '6222****4733', '773091033.95', 'CNY', true, 'configured', NULL, false, '2024-02-10 07:55:06'),
('35b0a006-8a75-42f6-94ce-f3bf0a26b1e7', 'test_sub_east_b', 'BOCOM', '6225****6977', '162737831.75', 'CNY', true, 'configured', NULL, false, '2024-06-30 06:42:17'),
('7160406f-e686-47d9-a2e0-de3fd6e6d504', 'test_sub_north_a', 'BOC', '6228****9751', '729153885.27', 'CNY', true, 'configured', NULL, false, '2024-03-24 14:24:17'),
('ebed91aa-43cb-481c-9e80-fd6961b57800', 'test_sub_north_a', 'SPDB', '6228****6313', '842867635.00', 'CNY', true, 'configured', NULL, false, '2024-01-29 07:52:02'),
('fe23cd96-afec-4977-8b30-91862d18e2bb', 'test_sub_east_b', 'CITIC', '6217****2084', '211061745.30', 'CNY', true, 'configured', NULL, false, '2024-10-17 22:20:13'),
('16bd991d-6c83-4ef6-aa65-d74ae615cde4', 'test_sub_north_a', 'CEB', '6225****8517', '142957303.28', 'CNY', true, 'configured', NULL, false, '2024-03-12 07:47:35'),
('0a78e288-a3af-48c4-bcd6-db2ce35dc71b', 'test_sub_north_a', 'BOCOM', '6225****7543', '362060244.07', 'CNY', true, 'configured', NULL, false, '2024-03-11 16:31:05'),
('bc45931b-5026-4bbb-9b7e-468afb4a22ec', 'test_sub_east_a', 'BOC', '6228****3621', '792100156.43', 'CNY', true, 'configured', NULL, false, '2024-08-04 19:04:24'),
('32a17450-900f-4b72-8e03-c62a0edecb72', 'test_sub_east_b', 'CEB', '6217****1188', '680315381.92', 'CNY', true, 'configured', NULL, false, '2024-02-28 21:56:34'),
('674cff34-620c-42c7-ac0d-97599c0eb64f', 'test_sub_east_b', 'CMB', '6222****5808', '434821774.14', 'CNY', true, 'configured', NULL, false, '2024-08-20 00:46:56'),
('bbda642a-68f6-4aab-b0c1-b5f60701c08a', 'test_sub_north_a', 'BOCOM', '6228****9317', '912636576.56', 'CNY', true, 'configured', NULL, false, '2024-11-16 09:53:40'),
('12f7e70e-f538-4a32-a305-5d2db0bac0b5', 'test_sub_north_a', 'ABC', '6228****7126', '762534549.00', 'CNY', true, 'configured', NULL, false, '2024-10-03 16:58:00'),
('b082ab8f-0ae2-409a-86ed-00002bcbba75', 'test_sub_north_a', 'CMB', '6225****1319', '111956538.55', 'CNY', true, 'configured', NULL, false, '2024-07-04 09:15:03'),
('68e4c026-a9f4-41f4-a4fb-ec138110d4fe', 'test_sub_east_a', 'BOC', '6222****8962', '816041651.09', 'CNY', true, 'configured', NULL, false, '2024-09-29 04:08:42'),
('86a22a20-ca71-4cd6-8ef2-8a3155e42e0f', 'test_sub_east_b', 'SPDB', '6228****5342', '527721020.04', 'CNY', true, 'configured', NULL, false, '2024-11-06 13:13:59'),
('d74fa432-8c9a-4927-a9fd-353036c15f74', 'test_sub_north_a', 'ABC', '6217****7537', '995149841.73', 'CNY', true, 'configured', NULL, false, '2024-11-28 11:28:57'),
('2ac642de-d2fd-40fb-bd3b-957ad9773c74', 'test_sub_north_a', 'CEB', '6222****5061', '224774867.30', 'CNY', true, 'configured', NULL, false, '2024-06-22 00:37:35'),
('24794347-c1e1-4939-a1c1-3cbe0a3b266a', 'test_sub_east_a', 'ABC', '6222****2163', '707870162.45', 'CNY', true, 'configured', NULL, false, '2024-01-31 07:04:57'),
('406a58f2-4386-4a23-bd5a-12b89cce49f8', 'test_sub_east_a', 'CMB', '6222****9423', '238080833.91', 'CNY', true, 'configured', NULL, false, '2024-12-08 15:13:34'),
('565ce184-664a-4735-8936-3e238340b848', 'test_sub_east_a', 'CEB', '6228****8749', '807516248.07', 'CNY', true, 'configured', NULL, false, '2024-04-07 03:06:42'),
('f8308bd9-f956-431e-8e90-49226bfdbd0e', 'test_sub_east_b', 'CMB', '6225****7735', '467077965.57', 'CNY', true, 'configured', NULL, false, '2024-01-28 21:41:41'),
('98445cf2-bc43-4602-9509-b554d7df64e6', 'test_sub_east_a', 'ICBC', '6225****6559', '800612451.61', 'CNY', true, 'configured', NULL, false, '2024-02-25 07:12:12'),
('e6a5f0b1-394b-4f3f-9929-b6d2af191759', 'test_sub_north_a', 'CEB', '6228****7912', '183569686.98', 'CNY', true, 'configured', NULL, false, '2024-08-24 07:55:59'),
('8dd4072d-1560-4a7b-8101-164108ad1313', 'test_sub_east_a', 'CEB', '6222****1828', '652179679.51', 'CNY', true, 'configured', NULL, false, '2024-10-03 00:05:59'),
('cfcac21e-36db-468c-b12c-2247490d93bc', 'test_sub_east_a', 'CCB', '6225****8956', '481410282.13', 'CNY', true, 'configured', NULL, false, '2024-07-24 01:10:24'),
('a3c57074-1f15-45b5-afb1-622937f62137', 'test_sub_east_a', 'CITIC', '6217****8454', '285320704.02', 'CNY', true, 'configured', NULL, false, '2024-12-22 23:50:35'),
('3b48c905-7e42-449e-86a4-48847a250f10', 'test_sub_north_a', 'CEB', '6228****4111', '296778154.71', 'CNY', true, 'configured', NULL, false, '2024-01-30 18:47:34'),
('63c88ca6-c13f-4e61-9e9c-d573f2696be4', 'test_sub_east_a', 'CMB', '6222****1821', '584219176.70', 'CNY', true, 'configured', NULL, false, '2024-09-14 16:10:03'),
('4d69fa1a-ef84-43f2-ae4b-1b28ed577f04', 'test_sub_north_a', 'BOC', '6228****2122', '595075602.94', 'CNY', true, 'configured', NULL, false, '2024-12-11 07:25:07'),
('bc90af59-323d-400d-8f7a-d97193260a91', 'test_sub_north_a', 'ABC', '6222****2343', '419282992.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-25 18:33:20'),
('abc49254-889b-4860-988c-0f9a8ba768fe', 'test_sub_east_b', 'ABC', '6217****4910', '265687951.08', 'CNY', true, 'unconfigured', NULL, false, '2024-03-08 21:41:19'),
('18755fcc-c349-4357-9fb7-bb35a2431d9e', 'test_sub_east_b', 'CMB', '6222****1152', '458339694.07', 'CNY', true, 'unconfigured', NULL, false, '2024-10-15 03:04:34'),
('a1b451e3-98c2-499a-b310-8445cb679058', 'test_sub_east_a', 'SPDB', '6217****3170', '933266052.06', 'CNY', true, 'unconfigured', NULL, false, '2024-02-05 07:23:18'),
('f71809b3-27cd-41f4-a086-fa068b7c086a', 'test_sub_east_a', 'CEB', '6217****9666', '7922324.84', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 09:59:42'),
('e8bd57fa-754b-4321-9aeb-32d135a22db8', 'test_sub_east_a', 'CCB', '6217****2891', '889723735.74', 'CNY', true, 'unconfigured', NULL, false, '2024-10-10 04:17:18'),
('59ce9b00-d289-46f0-a6f9-78d0dba8899b', 'test_sub_north_a', 'ABC', '6217****4335', '687528379.09', 'CNY', true, 'unconfigured', NULL, false, '2024-05-15 16:31:16'),
('72e9c9e0-cfe0-4867-93f3-8f364d990e74', 'test_sub_east_a', 'BOC', '6225****5533', '44182353.12', 'CNY', true, 'unconfigured', NULL, false, '2024-06-19 04:40:16'),
('c473e4bb-8a5b-4a44-a60d-18a9613dc39e', 'test_sub_east_a', 'CEB', '6225****1158', '111962693.20', 'CNY', true, 'unconfigured', NULL, false, '2024-12-19 04:34:02'),
('6df51dd4-9091-4991-b3a2-1b0d99252ce8', 'test_sub_east_b', 'SPDB', '6228****8041', '127532774.73', 'CNY', true, 'unconfigured', NULL, false, '2024-06-06 11:57:59'),
('4ffa59a9-d4eb-4e81-b1dd-bd0f1239ce9b', 'test_sub_east_a', 'CMB', '6228****5088', '666966717.29', 'CNY', false, 'configured', NULL, false, '2024-06-30 17:56:55'),
('546047e1-ef40-4cab-9661-4ec37ded5e8d', 'test_sub_east_b', 'CCB', '6228****3662', '976208412.33', 'CNY', false, 'configured', NULL, false, '2024-03-31 13:01:11'),
('509dc079-a5ac-487e-8ee9-f205bd89f40a', 'test_sub_north_a', 'CMB', '6225****5065', '266879029.02', 'CNY', false, 'configured', NULL, false, '2024-12-25 03:24:55'),
('a8c4f02c-54a3-4f6c-81b2-a1e19fb77bea', 'test_sub_east_a', 'CEB', '6228****4269', '816604946.94', 'CNY', false, 'configured', NULL, false, '2024-08-23 11:19:52'),
('87cd2491-37bc-4796-acad-4cfda19f665a', 'test_sub_east_a', 'ABC', '6222****4164', '398526131.97', 'CNY', false, 'configured', NULL, false, '2024-05-22 02:49:17');

INSERT INTO internal_deposit_account (id, entity_id, pool_id, balance, interest_rate, maturity_date, created_at) VALUES
('c92bed33-868c-46b2-a318-69704ec1df46', 'test_sub_east_b', '775c8a48-a809-48cb-911d-99ebe90c2641', '200139352.99', '0.0392', '2025-12-02', '2024-06-18 00:07:56'),
('5c226e9c-4ae3-43db-bca7-431dcd4c11ff', 'test_sub_east_b', '16d0a8ee-ef43-42d2-b3c9-9ea86c5ac03f', '481285890.72', '0.0254', '2025-02-27', '2024-01-20 03:38:27'),
('7990c9b3-52cd-4a1d-aed7-77154d28d973', 'test_sub_east_b', 'a983feaa-14e3-490a-85ea-3ebfd584279f', '157181818.44', '0.0419', '2025-11-06', '2024-02-29 12:57:36'),
('f9fc21f9-bff0-4b71-bef5-c617bd3615e2', 'test_sub_east_a', 'a5574d6f-85f0-4d09-8028-095b2c3947a6', '354538249.28', '0.0276', '2024-06-02', '2024-09-23 17:43:46'),
('5fc28772-ba6e-4652-81d5-9aaf45967515', 'test_sub_north_a', 'f1d3b579-bfb4-4dd0-ad4a-77b3bbf51177', '98919046.99', '0.0421', '2025-08-16', '2024-02-05 21:58:21'),
('9df8c9ed-c296-4362-a661-029191fcf65d', 'test_sub_north_a', 'ceb7ed5e-c637-4617-9f0d-1ccde04307c9', '424083632.11', '0.0294', '2025-04-04', '2024-09-16 09:42:26'),
('2aa76a66-dba7-4b92-90bc-288a4c4f112a', 'test_sub_east_b', '17ee22bc-ca41-41c6-b554-b91497d3fc7b', '148179773.66', '0.0321', '2024-10-09', '2024-04-08 13:42:24'),
('9e5c3bac-ff04-4343-b097-7375baf4952f', 'test_sub_north_a', '31d1e72e-7990-45ea-b6f2-0f421ef01aac', '87426657.93', '0.0150', '2025-04-05', '2024-07-26 17:53:00'),
('5a8fa525-27ad-430c-bedc-9279b9b9a5a5', 'test_sub_east_b', 'ec9adf75-9c4a-4d55-ac4e-93985be03535', '215229130.92', '0.0150', '2025-04-26', '2024-08-26 14:28:43'),
('8d6986de-b749-4d2f-8088-bdbfd68f0e79', 'test_sub_east_a', '0f07e075-88b9-4ace-9e78-08fa3c1cde8c', '396970831.85', '0.0080', '2024-11-21', '2024-12-03 02:18:32');

INSERT INTO restricted_account (id, entity_id, acct_no, restriction_type, status_6311, frozen_amount, created_at) VALUES
('c8fb8782-61d4-4ae5-bf78-31b62ee4828a', 'test_sub_north_a', '6217****2530', 'regulatory_hold', NULL, '33672503.96', '2024-04-25 06:09:01'),
('0ee285cb-b4d8-44b1-b8e4-cca93db55feb', 'test_sub_east_a', '6228****8784', 'judicial_freeze', NULL, '22825266.80', '2024-11-18 18:12:45'),
('8a4217aa-2bf4-4d12-b287-2c1cb34dcf62', 'test_sub_north_a', '6225****9099', 'escrow', NULL, '12274823.53', '2024-12-01 22:00:57'),
('55ec360f-33b5-4cde-bbc7-c50bd55a8008', 'test_sub_east_a', '6225****4585', 'regulatory_hold', 'restricted', '40225081.82', '2024-12-22 16:29:03'),
('f8c0bdd0-eb4c-4d37-b891-38e518b9a033', 'test_sub_north_a', '6228****2988', 'escrow', 'restricted', '6753621.37', '2024-08-25 21:33:35');


-- 资金集中域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO cash_pool (id, entity_id, pool_name, total_balance, concentration_rate, created_at) VALUES
('8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', 'test_sub_north_a', '资金池_华北子公司A_1', '3778697567.64', '0.8476', '2024-08-14 19:52:46'),
('a881dd64-cddb-484d-8ac1-f5ab788118a9', 'test_sub_north_a', '资金池_华北子公司A_2', '4535205104.98', '0.8640', '2024-08-16 05:47:55'),
('a72c76f9-1b0c-418b-95ee-080a927e4d8c', 'test_sub_east_b', '资金池_华东子公司B_3', '3761366164.64', '0.8675', '2024-11-22 08:49:49'),
('b3924181-5f1b-40b7-bd94-70fef83712e2', 'test_sub_north_a', '资金池_华北子公司A_4', '2428139115.18', '0.7200', '2024-05-02 08:28:04'),
('7ecf28d6-9b11-4dad-9e72-179cf267e168', 'test_sub_north_a', '资金池_华北子公司A_5', '1435783472.81', '0.6000', '2024-05-19 10:20:57');

INSERT INTO collection_record (id, pool_id, source_acct, amount, collection_date, status, created_at) VALUES
('3931927a-ae24-46de-b4fd-3f06e13506a0', '8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', '6228****3471', '23164584.90', '2024-12-21', 'completed', '2024-03-19 22:13:04'),
('e42e3181-b9d7-4fcc-a503-132b9804d078', 'b3924181-5f1b-40b7-bd94-70fef83712e2', '6217****9890', '46619134.12', '2024-02-01', 'completed', '2024-04-15 13:24:57'),
('d6fd8cb9-eecb-4e6c-bef2-9497569459d3', '8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', '6225****8814', '639313.55', '2024-06-29', 'completed', '2024-06-01 12:54:57'),
('f4d4571a-b374-40a0-88e8-404cf609ad1f', '7ecf28d6-9b11-4dad-9e72-179cf267e168', '6228****8999', '21981192.38', '2024-08-11', 'completed', '2024-09-05 00:24:21'),
('59dc59d0-e248-486d-903d-4aab0169e397', 'b3924181-5f1b-40b7-bd94-70fef83712e2', '6228****8657', '91958184.99', '2024-11-14', 'completed', '2024-09-30 00:58:25'),
('4d6583ab-389d-4184-b613-79086211ca48', '7ecf28d6-9b11-4dad-9e72-179cf267e168', '6222****2375', '64292827.32', '2024-03-10', 'completed', '2024-08-24 05:03:16'),
('9be30ccc-e8e8-415a-a5c6-2fd080ae04a9', 'a72c76f9-1b0c-418b-95ee-080a927e4d8c', '6228****8449', '32718238.20', '2024-07-13', 'completed', '2024-05-22 13:16:53'),
('a6453b3c-57e5-4d6b-92b3-c35220a5a0ff', 'b3924181-5f1b-40b7-bd94-70fef83712e2', '6222****9837', '5255956.54', '2024-06-28', 'completed', '2024-04-24 20:04:49'),
('04001356-e913-4ec3-a721-b95994af7e36', '8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', '6222****5051', '19976100.20', '2024-01-11', 'completed', '2024-11-14 04:15:08'),
('3d91911f-5772-4afb-897a-2acb8c07e167', '8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', '6228****8619', '69961523.88', '2024-07-07', 'completed', '2024-03-26 19:38:47'),
('626e4def-d54b-4cae-9cba-387951f63183', '8d0ad88c-6b5b-4ea3-93b5-b2f0a845e3de', '6228****6096', '10854470.03', '2024-01-14', 'completed', '2024-06-08 18:43:58'),
('b7597b01-64e8-43b9-9ce2-86381c8b910d', 'b3924181-5f1b-40b7-bd94-70fef83712e2', '6228****2245', '59230181.23', '2024-11-17', 'completed', '2024-05-04 03:44:49'),
('8488e76b-c6d4-4bcf-9ee9-4d6ad5f47c08', '7ecf28d6-9b11-4dad-9e72-179cf267e168', '6222****1672', '34753016.34', '2024-08-07', 'completed', '2024-12-04 11:04:32'),
('62b622d5-4716-4c8e-b459-530d20c0e9b1', 'a72c76f9-1b0c-418b-95ee-080a927e4d8c', '6222****7882', '82241975.26', '2024-02-24', 'completed', '2024-08-09 11:40:57'),
('592249c2-d46a-4f27-89c9-b3dbb5b0bbb1', 'a881dd64-cddb-484d-8ac1-f5ab788118a9', '6228****9548', '96549099.44', '2024-05-18', 'pending', '2024-11-11 17:49:30'),
('720bbbbf-ee2b-46d8-a9b6-9277edfaa3ba', 'b3924181-5f1b-40b7-bd94-70fef83712e2', '6217****6280', '85178730.34', '2024-02-14', 'failed', '2024-05-22 14:15:48'),
('6ad0b61d-e93d-48d6-9877-faaa9282ff86', '7ecf28d6-9b11-4dad-9e72-179cf267e168', '6225****6511', '2918564.78', '2024-06-15', 'failed', '2024-04-03 15:13:22'),
('c002a667-d672-4c5b-8521-c1ab5bfd7ab1', 'a72c76f9-1b0c-418b-95ee-080a927e4d8c', '6217****1166', '51686893.81', '2024-04-07', 'pending', '2024-02-13 07:46:26'),
('31705b07-54a9-471f-8f5d-129d29a76fed', '7ecf28d6-9b11-4dad-9e72-179cf267e168', '6225****9041', '44845046.23', '2024-01-09', 'completed', '2024-02-17 09:14:25'),
('c81c9989-6815-4ef9-ab9e-68358b2f1d15', 'a881dd64-cddb-484d-8ac1-f5ab788118a9', '6217****8753', '55369621.85', '2024-06-25', 'pending', '2024-08-05 23:35:21');


-- 结算域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO settlement_record (id, entity_id, channel, amount, currency, counterparty, is_cross_bank, is_cross_border, is_internal, status, settled_at) VALUES
('bbe629ee-e9b4-4b18-8bea-eea236a7b440', 'test_sub_east_b', 'bank_transfer', '35145718.56', 'CNY', '国电投资', true, false, false, 'settled', '2024-06-05 08:14:07'),
('b0a61dda-b43f-4335-8321-8db7685157e5', 'test_sub_north_a', 'online_banking', '9637288.83', 'CNY', '华能集团', false, false, false, 'settled', '2024-10-01 22:11:12'),
('c58ebb3e-af54-4b08-83ee-46376b1e087f', 'test_sub_east_a', 'bill_payment', '36932846.63', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-28 16:38:18'),
('16a0eeae-9b8e-4594-8e64-545afc5abed5', 'test_sub_east_a', 'letter_of_credit', '41633091.88', 'USD', '中石化财务', false, true, false, 'settled', '2024-07-03 05:19:00'),
('e05a92b4-329f-40e0-9bda-e2f2dce19355', 'test_sub_north_a', 'guarantee_payment', '26711413.11', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-24 01:35:18'),
('2b931d34-43af-48fa-a840-472efefa481d', 'test_sub_north_a', 'collection', '47205039.84', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-22 00:36:18'),
('36d25230-7528-426d-b5bb-bccd7f776ce8', 'test_sub_east_b', 'remittance', '23940923.29', 'CNY', '国电投资', true, false, false, 'settled', '2024-04-04 01:16:55'),
('cecf408d-b6ac-4aa4-b3a3-66e1122dfbe2', 'test_sub_east_b', 'entrusted_collection', '5713216.16', 'CNY', '华能集团', false, false, false, 'settled', '2024-07-24 15:04:36'),
('849ee9af-5fa1-4532-bddb-0342651cc1b0', 'test_sub_north_a', 'direct_debit', '34325686.40', 'CNY', '中石化财务', false, false, true, 'settled', '2024-03-17 18:19:05'),
('91e85ff1-fcf1-4a40-8b56-0d8776f1df78', 'test_sub_east_a', 'bank_transfer', '5931393.59', 'CNY', '中铁建设', true, false, false, 'settled', '2024-11-06 19:50:39'),
('058a3f2c-6707-49d3-8930-af2ecd8463d2', 'test_sub_east_a', 'online_banking', '38786920.05', 'CNY', '中铁建设', false, false, false, 'settled', '2024-08-18 14:19:55'),
('0ae5cec3-38d1-4724-a874-559c9669e4e9', 'test_sub_north_a', 'bill_payment', '49501662.71', 'CNY', '国电投资', false, false, false, 'settled', '2024-10-18 19:03:39'),
('f68160d5-6e1c-48f5-a627-3fbd9c8f5fe9', 'test_sub_north_a', 'letter_of_credit', '4970686.40', 'CNY', '中石化财务', false, true, false, 'settled', '2024-05-15 21:05:10'),
('36c37efc-773c-4015-9226-2f7ace5ba486', 'test_sub_east_a', 'guarantee_payment', '8698939.28', 'CNY', '华能集团', false, false, false, 'settled', '2024-03-21 00:26:28'),
('c6896083-35a4-423a-b101-6fa24daeef5a', 'test_sub_north_a', 'collection', '29694621.64', 'CNY', '国电投资', false, false, false, 'settled', '2024-01-17 07:18:45'),
('9a0b301e-cc80-444f-8c5e-98be9b2ceac2', 'test_sub_east_b', 'remittance', '35152348.03', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-06 21:14:59'),
('ef0a5656-dd1c-4255-83dd-40c8e8422164', 'test_sub_east_b', 'entrusted_collection', '39393523.05', 'CNY', '中交集团', false, false, false, 'settled', '2024-12-04 06:27:07'),
('cfea6ca8-8685-4279-8881-81e38f46e6ad', 'test_sub_north_a', 'direct_debit', '11248224.42', 'CNY', '中石化财务', false, false, true, 'settled', '2024-05-16 04:04:03'),
('d0c588ea-2d8c-4a10-843c-3b274a447f34', 'test_sub_east_a', 'bank_transfer', '39633502.03', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-18 09:28:07'),
('48c6cd95-97d3-46c6-84d8-0fcc2b3feb6b', 'test_sub_east_b', 'online_banking', '34437012.78', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-19 16:34:31'),
('d63d6199-c3ea-403c-ab70-2b9cf00a0e51', 'test_sub_east_b', 'bill_payment', '4031288.18', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-09 23:20:38'),
('083db92c-a9eb-40a0-9cb6-aa7e89fa4aab', 'test_sub_east_b', 'letter_of_credit', '1302985.97', 'CNY', '中交集团', false, true, false, 'settled', '2024-10-27 00:48:43'),
('cea094c5-1195-4f6c-92fc-c97c0ad89b8a', 'test_sub_east_b', 'guarantee_payment', '28816586.76', 'CNY', '中石化财务', false, false, false, 'settled', '2024-08-28 16:41:28'),
('d14e16f4-8e17-4f5b-8c0f-8701c0fd94f9', 'test_sub_east_b', 'collection', '9082642.47', 'CNY', '中交集团', false, false, false, 'settled', '2024-08-11 20:52:31'),
('fbe6134e-3be4-44db-b733-0fa9a416062e', 'test_sub_east_a', 'remittance', '23505819.64', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-19 10:42:06'),
('1a73f6d3-9908-4d65-83c7-6b1272706c35', 'test_sub_east_a', 'entrusted_collection', '16496885.14', 'CNY', '中铁建设', false, false, false, 'settled', '2024-05-27 21:25:52'),
('8f02a3d7-cccd-4635-affd-a4b72574b75c', 'test_sub_north_a', 'direct_debit', '1844489.54', 'CNY', '华能集团', false, false, true, 'settled', '2024-06-10 08:20:07'),
('f97344dc-641f-429e-8ad7-decc1984157c', 'test_sub_east_b', 'bank_transfer', '43246880.10', 'CNY', '华能集团', true, false, false, 'settled', '2024-12-02 17:29:26'),
('db15c93a-77f3-4a72-b117-f3035e610a0d', 'test_sub_east_a', 'online_banking', '9387251.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-11-14 15:40:28'),
('41fca6df-8fe8-4bc8-92e8-ba6dd01b0c26', 'test_sub_east_a', 'bill_payment', '10185876.34', 'CNY', '中交集团', false, false, false, 'settled', '2024-03-08 09:28:56'),
('cb4a638b-86cb-477a-88d6-0bf68b3fb923', 'test_sub_north_a', 'letter_of_credit', '24240742.73', 'CNY', '中交集团', false, true, false, 'settled', '2024-05-02 22:10:19'),
('62213ebc-cb1a-42ac-9049-bc5cc93f2ea0', 'test_sub_north_a', 'guarantee_payment', '693586.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-17 07:53:58'),
('206ecc3f-0ecd-45c2-a6a3-3a4e4b5f03e1', 'test_sub_east_a', 'collection', '23077780.23', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-27 04:31:59'),
('3df631a0-9b04-4651-a963-6f7e154ad5c9', 'test_sub_north_a', 'remittance', '14600159.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-07-31 15:30:15'),
('f6a71530-5c72-43ae-ae0d-d7e9adbefc79', 'test_sub_east_b', 'entrusted_collection', '27567741.19', 'CNY', '中铁建设', false, false, false, 'settled', '2024-04-07 19:32:47'),
('7680c1bc-7277-4ddc-9c99-949e26085590', 'test_sub_east_a', 'direct_debit', '43202706.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-07-31 10:59:50'),
('04f0a7be-bb7e-4a1c-a451-9e2ab3cb9d38', 'test_sub_north_a', 'bank_transfer', '13365961.43', 'CNY', '华能集团', true, false, false, 'settled', '2024-05-24 23:19:53'),
('bb69ffd7-d7d9-4823-a30a-1ef6a77179f8', 'test_sub_north_a', 'online_banking', '29000369.96', 'CNY', '中铁建设', false, false, false, 'settled', '2024-03-17 14:34:30'),
('f8daf84f-e8f0-4c75-a122-a05d695658e5', 'test_sub_east_b', 'bill_payment', '16628673.39', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-12 14:59:20'),
('c8b7e459-e29a-471a-b9e2-161e0a81d50e', 'test_sub_east_a', 'letter_of_credit', '49038923.82', 'CNY', '中交集团', false, true, false, 'settled', '2024-07-15 07:54:49'),
('a3280821-5104-45a9-b90b-e1d5a73718fc', 'test_sub_east_b', 'guarantee_payment', '2191928.48', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-27 12:24:42'),
('b9e656ab-e4d0-4646-b556-7d4ebf0c2983', 'test_sub_north_a', 'collection', '49041098.75', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-19 04:32:37'),
('c6b42025-9210-4cb4-a09b-0c08e8fd9c74', 'test_sub_east_b', 'remittance', '43486318.66', 'CNY', '中铁建设', true, false, false, 'settled', '2024-02-21 16:58:29'),
('1bc50a68-4411-4a76-bbb3-85a91a80b065', 'test_sub_east_a', 'entrusted_collection', '36124966.94', 'CNY', '中铁建设', false, false, false, 'settled', '2024-12-01 04:04:30'),
('238a58dd-0960-40d8-8157-fa145169be16', 'test_sub_east_b', 'direct_debit', '16934676.09', 'CNY', '中铁建设', false, false, true, 'settled', '2024-11-28 02:54:21'),
('50a5055e-7210-4186-9e8f-a1969acdee73', 'test_sub_north_a', 'bank_transfer', '42968515.79', 'CNY', '中铁建设', true, false, false, 'settled', '2024-06-11 20:45:56'),
('f0e371fa-fded-47e3-aa2d-2e6f0a2dc116', 'test_sub_east_b', 'online_banking', '43620427.04', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-12 02:15:40'),
('1db0ff7a-177b-4a34-9f3d-478c6224a6ea', 'test_sub_north_a', 'bill_payment', '46047245.65', 'CNY', '中石化财务', false, false, false, 'settled', '2024-02-16 13:06:48'),
('4fb20f1e-d85c-4648-9cba-54bcd5e4985f', 'test_sub_north_a', 'letter_of_credit', '35197502.56', 'CNY', '中铁建设', false, true, false, 'settled', '2024-03-26 22:19:57'),
('bdc24d35-a45d-4467-b226-9eb1c746073a', 'test_sub_east_a', 'guarantee_payment', '2309088.52', 'CNY', '华能集团', false, false, false, 'settled', '2024-05-30 11:23:27'),
('477e95d4-db43-4c48-a2e1-277b21fcf4bc', 'test_sub_east_a', 'collection', '12217429.63', 'CNY', '中铁建设', false, false, false, 'settled', '2024-10-16 21:50:11'),
('e5336be4-7ab1-4277-8b4c-34f60bec99bf', 'test_sub_east_a', 'remittance', '8761717.06', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-14 19:43:15'),
('93d30476-3e0f-43b8-ab9d-3ab44d6433f2', 'test_sub_east_b', 'entrusted_collection', '45642322.51', 'CNY', '中石化财务', false, false, false, 'settled', '2024-04-28 14:40:16'),
('edc8c760-e6c7-47bc-ba6a-25e4b1f675d7', 'test_sub_east_b', 'direct_debit', '12773782.14', 'CNY', '华能集团', false, false, true, 'settled', '2024-08-26 09:43:34'),
('81669cb6-528d-4da1-ba96-1693bf8ef7d4', 'test_sub_east_a', 'bank_transfer', '3702356.40', 'CNY', '国电投资', true, false, false, 'settled', '2024-10-27 09:40:27'),
('4fbc3c07-2285-4f3a-9a1c-796d8eec5943', 'test_sub_north_a', 'online_banking', '12512410.24', 'CNY', '国电投资', false, false, false, 'settled', '2024-04-11 12:54:30'),
('fabd7fd7-1820-4dc9-8b7c-b5d20eefa0a7', 'test_sub_east_a', 'bill_payment', '11867913.04', 'CNY', '中交集团', false, false, false, 'settled', '2024-07-02 18:18:44'),
('aef74ff7-f4d1-4b3f-b08b-1785bcb25b29', 'test_sub_east_b', 'letter_of_credit', '1106760.50', 'EUR', '中铁建设', false, true, false, 'settled', '2024-05-20 00:36:55'),
('6d1e80dc-ec12-44e2-a824-3d8b6542f6f4', 'test_sub_north_a', 'guarantee_payment', '38917797.67', 'CNY', '华能集团', false, false, false, 'settled', '2024-11-06 23:31:53'),
('441cda2a-91e4-4b62-b37d-84fe20b6e5a7', 'test_sub_east_b', 'collection', '38789291.57', 'CNY', '中石化财务', false, false, false, 'settled', '2024-11-06 11:14:40'),
('96f56d24-d33d-46fe-8f60-71f7921de39b', 'test_sub_east_a', 'remittance', '31048349.24', 'CNY', '中石化财务', true, false, false, 'settled', '2024-11-17 03:57:40'),
('51d9b44e-950b-4762-b187-e21e51fdfed0', 'test_sub_north_a', 'entrusted_collection', '1980734.47', 'CNY', '中铁建设', false, false, false, 'settled', '2024-01-18 18:23:46'),
('891a90f7-2a9a-4875-9d2b-53ce83bea5f3', 'test_sub_east_a', 'direct_debit', '4515767.45', 'CNY', '国电投资', false, false, true, 'settled', '2024-06-16 23:26:11'),
('32bc43e5-7e25-441e-be4b-509dd78cb1b6', 'test_sub_east_a', 'bank_transfer', '6616668.29', 'CNY', '中交集团', true, false, false, 'settled', '2024-07-06 16:32:58'),
('edd49304-7b83-438f-a9db-7011e97c82fa', 'test_sub_east_b', 'online_banking', '41525326.25', 'CNY', '国电投资', false, false, false, 'settled', '2024-09-03 09:47:55'),
('69d03264-6631-4632-a377-2fc069dca372', 'test_sub_east_b', 'bill_payment', '40213584.60', 'CNY', '中铁建设', false, false, false, 'settled', '2024-02-08 04:48:14'),
('63057e2c-98e9-461a-85d7-1f5d92c99c03', 'test_sub_north_a', 'letter_of_credit', '36213593.44', 'USD', '中交集团', false, true, false, 'settled', '2024-07-06 02:50:25'),
('24f0d7e9-d5a4-4aa0-b958-4d5436920233', 'test_sub_east_a', 'guarantee_payment', '13230284.33', 'CNY', '华能集团', false, false, false, 'settled', '2024-08-20 11:43:47'),
('19dc5a68-188e-49c0-ae67-90e39716ad32', 'test_sub_north_a', 'collection', '13115448.80', 'CNY', '中铁建设', false, false, false, 'settled', '2024-11-22 11:06:43'),
('dffc9ed6-2ff1-4084-839b-33332d7c5fbc', 'test_sub_east_a', 'remittance', '23579128.63', 'CNY', '中交集团', true, false, false, 'settled', '2024-10-14 10:58:39'),
('e45f8d06-3d9a-4040-b75a-9565b8f8a943', 'test_sub_east_a', 'entrusted_collection', '32386142.51', 'CNY', '中铁建设', false, false, false, 'pending', '2024-12-24 09:41:26'),
('c7c78cf0-c03d-4104-b1c3-7803271b4115', 'test_sub_east_a', 'direct_debit', '6997452.86', 'CNY', '华能集团', false, false, true, 'pending', '2024-06-04 15:07:06'),
('9c9f846f-b66f-488b-8aa9-3e6f4957d68d', 'test_sub_east_a', 'bank_transfer', '44364092.83', 'CNY', '中石化财务', true, false, false, 'pending', '2024-07-17 14:23:42'),
('d1d3123f-1ce3-4e28-a1c0-22b5ac7fb59f', 'test_sub_north_a', 'online_banking', '34827234.74', 'CNY', '中交集团', false, false, false, 'pending', '2024-08-02 18:47:46'),
('82dca71e-f26c-4a91-8aee-7231cbf8fd22', 'test_sub_east_a', 'bill_payment', '44271835.06', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-07 19:26:17'),
('0fd3c573-5574-4ee2-ab2d-d378ff249722', 'test_sub_east_a', 'letter_of_credit', '34517130.38', 'CNY', '中铁建设', false, true, false, 'pending', '2024-08-15 07:54:23'),
('0f159925-0166-4586-8eb3-48e5e7c0df8b', 'test_sub_east_a', 'guarantee_payment', '49046576.64', 'CNY', '国电投资', false, false, false, 'pending', '2024-10-05 20:22:03'),
('1b9463bb-a539-4c28-bcf8-43d003257095', 'test_sub_east_b', 'collection', '13801313.23', 'CNY', '华能集团', false, false, false, 'pending', '2024-08-20 02:42:13'),
('d1e66e2d-e10e-4bf5-9ac5-9ec29cec533e', 'test_sub_north_a', 'remittance', '31978251.00', 'CNY', '华能集团', true, false, false, 'pending', '2024-01-26 10:15:08'),
('b4bfdfdf-378a-4227-baf9-7e8a700d2110', 'test_sub_north_a', 'entrusted_collection', '10268226.70', 'CNY', '中交集团', false, false, false, 'pending', '2024-04-16 18:13:52'),
('dbe991ee-1c65-49e6-9fb3-bd25ecf6bcf6', 'test_sub_east_a', 'direct_debit', '16434692.08', 'CNY', '中石化财务', false, false, true, 'pending', '2024-11-01 00:17:54'),
('8e9fc901-fa4c-408e-a683-d898d9872004', 'test_sub_east_a', 'bank_transfer', '49376489.95', 'CNY', '中交集团', true, false, false, 'pending', '2024-05-08 05:07:42'),
('b7e90995-0494-4357-89fe-82d89eda6a14', 'test_sub_east_a', 'online_banking', '6598843.45', 'CNY', '国电投资', false, false, false, 'pending', '2024-05-01 18:20:01'),
('4ffc6b25-56ac-414d-831f-0ce2446cbd40', 'test_sub_east_a', 'bill_payment', '13275721.74', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-03 16:07:47'),
('09e20c23-99bf-493f-b91a-c667874b9bd4', 'test_sub_east_a', 'letter_of_credit', '23817535.81', 'USD', '中交集团', false, true, false, 'pending', '2024-10-30 03:28:32'),
('a46b5636-7f1b-4d61-b51f-d0d66b6d3bb3', 'test_sub_east_a', 'guarantee_payment', '47271327.99', 'CNY', '华能集团', false, false, false, 'pending', '2024-12-03 16:19:29'),
('218866ef-6ed3-48be-b7e7-ac192e876f7a', 'test_sub_north_a', 'collection', '48201668.89', 'CNY', '华能集团', false, false, false, 'pending', '2024-09-02 12:27:43'),
('8733a6da-0be5-4f91-b4c9-268eb4d5912c', 'test_sub_east_a', 'remittance', '24518540.02', 'CNY', '中铁建设', true, false, false, 'pending', '2024-02-07 02:20:38'),
('ce8093d6-a815-4d8e-a13a-a6a7e94ae46a', 'test_sub_east_a', 'entrusted_collection', '3293454.84', 'CNY', '国电投资', false, false, false, 'pending', '2024-11-15 20:37:35'),
('cb9843dd-7117-4e0d-9ffd-ddf205dc7e7c', 'test_sub_north_a', 'direct_debit', '16266020.31', 'CNY', '中交集团', false, false, true, 'pending', '2024-09-28 09:29:32'),
('3a648f86-97aa-4928-a29e-3ebdf23a518a', 'test_sub_north_a', 'bank_transfer', '21515664.30', 'CNY', '华能集团', true, false, false, 'pending', '2024-12-01 20:56:49'),
('44dc0904-da2b-4100-ad06-e2d3d7ea88d3', 'test_sub_north_a', 'online_banking', '36044787.43', 'CNY', '中石化财务', false, false, false, 'pending', '2024-08-08 14:56:14'),
('6a624c3f-54d4-499a-928c-edad856005f0', 'test_sub_east_b', 'bill_payment', '16953191.63', 'CNY', '中铁建设', false, false, false, 'pending', '2024-07-23 13:46:06'),
('ab6b7b1f-f089-4aaf-8457-18af192c5b3c', 'test_sub_east_b', 'letter_of_credit', '21343932.67', 'EUR', '国电投资', false, true, false, 'pending', '2024-07-10 04:43:59'),
('3aed274d-ad60-4370-b098-f2f6fd444fa0', 'test_sub_east_b', 'guarantee_payment', '3365994.07', 'CNY', '华能集团', false, false, false, 'pending', '2024-02-17 13:06:47'),
('8da46fdc-aeec-4d51-a18d-b5839a2eca47', 'test_sub_north_a', 'collection', '18638616.50', 'CNY', '中石化财务', false, false, false, 'pending', '2024-10-11 01:37:35'),
('38634035-e464-4caa-a338-0df1dfa65da7', 'test_sub_north_a', 'remittance', '16489002.61', 'CNY', '华能集团', true, false, false, 'pending', '2024-07-29 11:55:42'),
('a2ada833-d7e2-45f8-a314-146839e05ed8', 'test_sub_east_b', 'entrusted_collection', '43405926.52', 'CNY', '华能集团', false, false, false, 'pending', '2024-05-27 19:19:22'),
('074d8286-4cb6-4fb3-abae-72a9b99fb263', 'test_sub_east_a', 'direct_debit', '28900146.73', 'CNY', '中石化财务', false, false, true, 'pending', '2024-03-20 21:30:14'),
('e71dc460-ec09-4a8b-9190-4d73b4d5b101', 'test_sub_east_a', 'bank_transfer', '17512198.57', 'CNY', '中交集团', true, false, false, 'pending', '2024-07-07 03:48:17');

INSERT INTO payment_channel (id, channel_name, channel_type, is_direct_linked, daily_limit) VALUES
('0eac5185-a2d9-495b-981e-04dcdc48fce5', '银行转账', 'bank_transfer', true, '23389750.34'),
('e878db63-c42e-4016-9d57-b966f380b31d', '网上银行', 'online_banking', true, '84670360.97'),
('0c183697-eaaf-434d-8aed-4af059827525', '票据支付', 'bill_payment', true, '61743754.77'),
('a48bf0af-e204-4460-8a02-b616f71663c8', '信用证', 'letter_of_credit', true, '56117235.76'),
('7439a357-2f64-415d-987a-3d88e874815f', '保函支付', 'guarantee_payment', true, '92979344.81'),
('a2daf4e7-fef9-404b-b57c-777533edafa2', '托收', 'collection', true, '27477324.79'),
('7623c07a-1e46-49f5-b9df-8065a88ba9dd', '汇款', 'remittance', true, '28053768.48'),
('5b5f9d2c-d216-41e8-905f-9e796f3c7ee0', '委托收款', 'entrusted_collection', true, '92232214.58'),
('4abda100-5fd3-4257-b3ff-292c9200a7cd', '直接扣款', 'direct_debit', false, '1604473.15');


-- 票据域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO bill (id, entity_id, bill_type, face_value, issue_date, maturity_date, status, is_overdue, created_at) VALUES
('6346c2de-df8d-42db-a39b-fdc1ec1e39c2', 'test_sub_east_a', 'commercial_draft', '3572312.52', '2024-05-24', '2025-03-15', 'active', false, '2024-11-20 00:05:47'),
('dc33f995-534f-490b-9c8f-67ae18111689', 'test_sub_north_a', 'bank_acceptance', '21049641.44', '2024-02-25', '2024-12-03', 'active', false, '2024-06-23 05:23:19'),
('e657b2dd-8471-4e8d-98e5-eca8716c264f', 'test_sub_north_a', 'electronic_commercial', '44178775.01', '2024-03-24', '2024-08-04', 'active', false, '2024-03-20 05:48:39'),
('abc6e40d-9563-4c22-be97-6b6a37b3229a', 'test_sub_east_a', 'commercial_draft', '13677931.89', '2024-06-21', '2024-10-30', 'active', false, '2024-12-04 13:31:38'),
('6b82f599-60fe-4973-9492-a6cae514887a', 'test_sub_east_b', 'bank_acceptance', '10856891.37', '2024-04-16', '2024-12-01', 'active', false, '2024-09-19 03:22:27'),
('050e11d0-5c53-46c5-ac8c-8cece2dc8bb6', 'test_sub_east_a', 'electronic_commercial', '26394011.95', '2024-03-13', '2025-02-15', 'active', false, '2024-06-06 01:14:25'),
('cb5d1cd4-67ed-45d2-8fe9-e963dec1cbab', 'test_sub_north_a', 'commercial_draft', '10300713.91', '2024-01-15', '2024-04-17', 'active', false, '2024-04-18 04:48:16'),
('e50afa3f-e957-49f1-9328-9c3460de769f', 'test_sub_east_b', 'bank_acceptance', '485722.34', '2024-03-24', '2024-08-22', 'active', false, '2024-08-08 05:08:24'),
('cd7b3d65-52fd-40d2-9fb7-507788b6822a', 'test_sub_north_a', 'electronic_commercial', '25063091.09', '2024-06-29', '2025-01-22', 'active', false, '2024-12-08 11:04:25'),
('abc96dda-ac09-4375-a3c4-d47a6e27dd11', 'test_sub_north_a', 'commercial_draft', '1035202.68', '2024-01-11', '2024-11-19', 'active', false, '2024-02-09 10:36:27'),
('434a03df-a08b-47aa-9b1b-ba34e6db7b00', 'test_sub_north_a', 'bank_acceptance', '14546808.76', '2024-04-13', '2025-02-10', 'active', false, '2024-07-26 00:20:10'),
('fb35083e-32be-4da4-a71a-37d6bbf20b66', 'test_sub_north_a', 'electronic_commercial', '4497681.08', '2024-04-27', '2025-01-27', 'active', false, '2024-02-24 07:27:37'),
('60da955a-9dc0-42be-af62-8c3eb07febb0', 'test_sub_east_b', 'commercial_draft', '19848758.17', '2024-05-14', '2024-09-21', 'active', false, '2024-06-07 23:21:14'),
('61cb2e34-ea47-487f-84e4-3d6935cf613e', 'test_sub_east_b', 'bank_acceptance', '25573115.90', '2024-02-13', '2024-06-21', 'active', false, '2024-02-28 16:32:12'),
('091a9e81-6475-4b05-bc15-8a197f854366', 'test_sub_east_b', 'electronic_commercial', '11889815.56', '2024-03-30', '2024-09-11', 'active', false, '2024-03-15 08:12:11'),
('c63ee3ab-050a-47ac-a83c-dea535977046', 'test_sub_north_a', 'commercial_draft', '8939591.83', '2024-02-09', '2024-06-16', 'active', false, '2024-11-17 15:29:48'),
('60eef3dd-d2e7-4f81-8990-40546777b784', 'test_sub_north_a', 'bank_acceptance', '34088560.57', '2024-05-28', '2025-04-12', 'active', false, '2024-10-16 20:40:39'),
('4121bafe-13e1-4f59-8ca4-82060bdb55e2', 'test_sub_east_b', 'electronic_commercial', '7632774.33', '2024-06-09', '2025-02-15', 'active', false, '2024-02-04 15:28:40'),
('7a831823-af4f-45c0-a270-356279e6f7a7', 'test_sub_east_b', 'commercial_draft', '17661916.91', '2024-03-11', '2024-07-07', 'active', false, '2024-02-07 09:29:28'),
('fc3c856f-48ab-47bf-ac21-be32de614985', 'test_sub_east_a', 'bank_acceptance', '41601661.92', '2024-01-15', '2024-10-19', 'active', false, '2024-02-09 20:55:54'),
('83e68677-80dc-4f31-8add-5251b7c16b48', 'test_sub_east_a', 'electronic_commercial', '19285675.58', '2024-06-06', '2025-05-21', 'active', false, '2024-10-24 17:50:47'),
('fbdd86e0-2cd1-42ca-b303-f5f9156cbe6d', 'test_sub_east_a', 'commercial_draft', '16144185.47', '2024-04-25', '2024-10-28', 'pending', false, '2024-08-31 16:09:03'),
('c2c33c3b-ee3c-4805-8804-e5eec1f43d2c', 'test_sub_east_b', 'bank_acceptance', '49121040.50', '2024-01-27', '2024-10-18', 'pending', false, '2024-02-13 16:41:11'),
('8871b74f-9dbc-4817-9105-7e80b295cc31', 'test_sub_east_a', 'electronic_commercial', '49550202.53', '2024-03-04', '2025-01-12', 'pending', false, '2024-09-25 16:39:10'),
('91bfba6b-fa52-4ba5-80e7-dfa6bc68020d', 'test_sub_east_b', 'commercial_draft', '19432086.32', '2024-04-05', '2024-11-25', 'pending', false, '2024-06-22 21:38:03'),
('195779f5-8764-4391-b77f-0691027b1614', 'test_sub_north_a', 'bank_acceptance', '3389001.53', '2024-06-14', '2025-03-02', 'pending', false, '2024-02-18 17:43:24'),
('d1c9720b-0fda-49d8-a25f-29262b50f647', 'test_sub_east_b', 'electronic_commercial', '16734765.60', '2024-03-05', '2024-08-18', 'pending', false, '2024-10-25 21:09:58'),
('bf8f7b11-37b9-4f51-89b0-66b8d48b51af', 'test_sub_east_b', 'commercial_draft', '6534687.75', '2024-03-20', '2025-01-04', 'overdue', true, '2024-12-28 02:19:35'),
('1f043cb7-d97a-41f5-bbdd-21a2fa6e5b9c', 'test_sub_east_b', 'bank_acceptance', '40677920.71', '2024-06-13', '2025-02-26', 'overdue', true, '2024-12-09 22:53:47'),
('64e9215a-9a14-43e0-95c5-07c5b4ac8b93', 'test_sub_north_a', 'electronic_commercial', '32336638.55', '2024-05-14', '2024-09-28', 'overdue', true, '2024-08-04 16:23:01');

INSERT INTO endorsement_chain (id, bill_id, endorser_id, endorsee_id, endorse_date, sequence_no) VALUES
('01825a1b-2bfc-45d4-aca9-103740c72140', 'abc96dda-ac09-4375-a3c4-d47a6e27dd11', 'test_sub_east_a', 'test_sub_north_a', '2024-06-23', 1),
('4c281e90-6ffa-42c2-8192-31786f4960c5', 'cb5d1cd4-67ed-45d2-8fe9-e963dec1cbab', 'test_sub_east_a', 'test_sub_north_a', '2024-03-20', 2),
('a602ab9a-e229-46d2-86ea-251da59d2cb7', 'abc96dda-ac09-4375-a3c4-d47a6e27dd11', 'test_sub_east_a', 'test_sub_north_a', '2024-12-04', 3),
('d132bef7-a882-444c-b94f-3d26588e8335', '1f043cb7-d97a-41f5-bbdd-21a2fa6e5b9c', 'test_sub_north_a', 'test_sub_east_a', '2024-11-01', 4),
('eeb7f130-54d2-4502-8fae-12a09d69638c', '6b82f599-60fe-4973-9492-a6cae514887a', 'test_sub_east_a', 'test_sub_north_a', '2024-12-20', 5),
('b874c29a-cd73-47af-8431-36374efe744a', '195779f5-8764-4391-b77f-0691027b1614', 'test_sub_east_a', 'test_sub_east_b', '2024-01-23', 6),
('fbc92777-093a-40a9-b1ae-aed63e8b3184', 'fb35083e-32be-4da4-a71a-37d6bbf20b66', 'test_sub_north_a', 'test_sub_east_a', '2024-08-15', 7),
('05918229-82c6-4c35-a2f4-62891a6ad512', 'abc96dda-ac09-4375-a3c4-d47a6e27dd11', 'test_sub_north_a', 'test_sub_east_b', '2024-04-29', 8),
('0ca87a87-abfd-4c86-ad85-20f275cba543', 'e50afa3f-e957-49f1-9328-9c3460de769f', 'test_sub_east_b', 'test_sub_north_a', '2024-04-09', 9),
('a8b5f59e-2b5e-4d0d-9a65-5f7b34fdf90c', 'fbdd86e0-2cd1-42ca-b303-f5f9156cbe6d', 'test_sub_north_a', 'test_sub_east_b', '2024-08-24', 10),
('1ced3dea-dcb1-41a4-a612-79e1bc074c5b', '91bfba6b-fa52-4ba5-80e7-dfa6bc68020d', 'test_sub_east_b', 'test_sub_north_a', '2024-03-23', 11),
('ca564d64-a771-4ef4-b2b6-3e4ece2d99b7', '195779f5-8764-4391-b77f-0691027b1614', 'test_sub_north_a', 'test_sub_east_a', '2024-05-08', 12),
('c734eedb-4d4d-4a2c-8892-599f1d27915b', '83e68677-80dc-4f31-8add-5251b7c16b48', 'test_sub_east_b', 'test_sub_north_a', '2024-10-10', 13),
('a1822a1a-f975-4806-8b65-803bb7d8136b', 'c2c33c3b-ee3c-4805-8804-e5eec1f43d2c', 'test_sub_north_a', 'test_sub_east_a', '2024-05-25', 14),
('555f0558-7262-4bcb-aed4-85cb13e5953f', '91bfba6b-fa52-4ba5-80e7-dfa6bc68020d', 'test_sub_east_a', 'test_sub_east_b', '2024-08-18', 15);


-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('e6323be5-e3fe-4a36-bd5c-59c8ed4282b4', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('716d3db5-5bb1-4b37-8d25-a985fb0d4b8e', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('dacac26b-eb16-426f-b84b-f1d361cec452', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('7d9d9660-bb47-4bf8-b6fd-7b7319cf37f1', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('61b8f269-818a-4353-a433-c5192388b127', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('add6310e-8383-41a2-8e0a-27c2019397af', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('7f9c179b-2e64-4b06-a378-8dcdd1d3ba17', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('619d9247-d08d-491c-8f91-6d04f98e9d00', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('3306d1ad-c6c7-4ab6-af44-fa46e123f4de', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('117482c2-1160-4e08-a9c0-76148d633d76', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('61e22f73-567f-4e82-b7f0-a7268610587c', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('a84b9cbb-3379-4770-a95f-6a8a09cd6bc0', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('847bada8-4a92-4a5f-b00b-44f9d29a7d0f', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('17acb393-b2fc-4ee3-87e2-09d170f6beff', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('0b54afbb-e12e-4873-9d67-19dfea6a0f38', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('8cf9448f-328a-4a53-9a90-5ef47707c9ca', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('5f467a17-44ab-492a-a69f-b7334bfdb019', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('201be41d-ed51-4ba6-b968-a43d95124b07', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('443774c6-55ec-4eca-96ac-29fc32db7a3e', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('05e0182f-8a2d-428e-bbfd-cbd36ab43906', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');


-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('8fed502e-3f93-4574-8bee-979a24ce4ed6', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('83d74be6-4fd3-4cde-b980-4a51427bacef', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('93867a51-e165-4021-b3f6-a83adbf417e6', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('e08c470c-7c7f-4d21-95d3-383484d816b7', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('98db200b-c576-4a57-9f75-966a629445b5', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('adefab07-7860-40d5-9b03-4a2f2412492b', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('ec98ca57-6209-4edc-9c79-1622849ccfb6', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('8424d1a4-7266-4a09-bcda-6b47f4f145be', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('4d70e045-4fbd-43f3-9e97-0b021ba38483', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('968706e9-6b5c-48e3-bee1-aeec0787138f', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('ec67a601-6153-4d0c-b9d8-e8076a1244f6', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('8cf83b7a-660e-4cd8-9b45-482c05e8a53f', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('d6875d1d-c18c-4152-9146-de7009c18628', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('1561349a-8cab-4b44-ab67-158b05d19fe0', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('c77bd1a6-d368-4a31-b6f7-96514f45225e', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('28e03445-76d3-415b-9c31-e2774c8b4b26', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('502c7b1a-fdbf-4c85-a999-1b17631b5a59', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('6f85906c-7587-4e33-991d-e39c54f0da76', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('81878f74-53a7-4202-8668-07353165ad2e', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('de358acf-3a12-4efc-8be8-12a0529fd43f', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('59ddc590-7618-41af-a849-212152fc0e69', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('0e0a7f44-4c6d-492b-b457-87e3208355df', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('9d3ab5fc-e8f6-4524-9d2e-2dc271cd7760', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('7e072272-8919-42ec-9559-dd7e394f6bea', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('71e096bd-91f8-457b-9aab-7058050bd287', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('e183a228-f4af-4e31-818c-3f67da5d96e2', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('e0cd8697-3b57-44ff-b50e-f8b16a129dff', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('c23c5e4a-70d4-4cd5-befb-6883553239aa', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('42488c2f-3376-4d98-881e-fced6fbf677a', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('8a934f37-f263-481a-ac17-eac7c508cd9c', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');


-- 国资委考核域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO financial_report (id, entity_id, report_type, period, total_asset, net_asset, revenue, profit, rd_expense, employee_count, operating_cash_flow) VALUES
('474a36eb-ed03-4b5a-8055-d84015549a10', 'test_group_hq', 'annual', '2024', '47861229725.12', '18299038102.21', '6437712433.76', '717436878.38', '164842161.67', 42507, '926315918.56'),
('58c8435f-0a16-46b6-955a-5ecee91da249', 'test_region_east', 'annual', '2024', '8555519077.10', '4257396222.61', '7346011300.15', '811836290.54', '518274321.86', 37437, '301852087.26'),
('0db888fa-13ba-4e9a-9b2a-f72f733345fb', 'test_region_north', 'annual', '2024', '4979919889.78', '2911082170.28', '7824712503.55', '598321264.29', '255465147.94', 37995, '2141275239.95'),
('5680b1c0-9def-4582-b2f8-21da52ea7cb6', 'test_sub_east_a', 'annual', '2024', '2484009030.49', '1407685593.63', '5682986093.70', '648944324.54', '216667520.45', 16548, '4042971955.66'),
('ebec5750-33da-4b2c-8b41-c8b449ebd292', 'test_sub_east_b', 'annual', '2024', '20898533810.48', '9113082362.28', '7041828930.89', '463408993.06', '316440812.83', 30937, '1099712766.46'),
('e34ccd9c-0bb7-4ff7-9ccd-b3886baa0b96', 'test_sub_north_a', 'annual', '2024', '8039765866.97', '4489771254.78', '3533505730.14', '525793910.26', '143892245.92', 26630, '740754142.61');

INSERT INTO assessment_indicator (id, entity_id, indicator_code, indicator_name, target_value, actual_value, period) VALUES
('44ab1e0b-f54e-4837-9cf6-e24ac5df6517', 'test_group_hq', 'AI001', '净资产收益率', '0.1272', '0.1313', '2024'),
('a4cfcb21-5d77-49f7-b180-e5fcba5b6877', 'test_group_hq', 'AI002', '营业收入利润率', '0.1200', '0.1296', '2024'),
('4f27d5d7-2c5b-40ec-a1b3-008d796b4bdd', 'test_group_hq', 'AI003', '研发投入强度', '0.0711', '0.0722', '2024'),
('a4686b3a-3fa8-4e6a-85db-796229a2ae62', 'test_group_hq', 'AI004', '全员劳动生产率', '0.1796', '0.2021', '2024'),
('c38e02b1-5a04-4d08-a024-212ad6a529b6', 'test_group_hq', 'AI005', '资产负债率', '0.1720', '0.2202', '2024'),
('f05b987d-5802-4722-a13d-f9db5a4fe1ae', 'test_group_hq', 'AI006', '经营性现金流比率', '0.0969', '0.1191', '2024'),
('57ccc210-d2e8-40d0-baeb-f6511ca2e83a', 'test_group_hq', 'AI007', '总资产周转率', '0.1994', '0.2273', '2024'),
('2a8a9ba3-e591-44a6-bb4c-b22c15a61e69', 'test_group_hq', 'AI008', '成本费用利润率', '0.1246', '0.1280', '2024'),
('c767093a-66f7-4630-a2c5-69cc2b306db2', 'test_group_hq', 'AI009', '国有资本保值增值率', '0.1258', '0.1623', '2024'),
('76a4f6ba-fb3c-4c3d-acce-38b12bfbe20f', 'test_region_east', 'AI001', '净资产收益率', '0.1375', '0.1395', '2024'),
('0c90ec65-27b2-49ec-a958-8d236f890025', 'test_region_east', 'AI002', '营业收入利润率', '0.1242', '0.1571', '2024'),
('9c7dd8cf-3659-45e9-88dd-572299ae6731', 'test_region_east', 'AI003', '研发投入强度', '0.1509', '0.1638', '2024'),
('7f6ae5e5-913b-4100-aed2-653b65614e64', 'test_region_east', 'AI004', '全员劳动生产率', '0.1771', '0.2000', '2024'),
('b459d9ec-1900-4816-820f-0943eb00b840', 'test_region_east', 'AI005', '资产负债率', '0.1591', '0.1956', '2024'),
('a16165e5-6851-4e4f-8819-3c83402e968c', 'test_region_east', 'AI006', '经营性现金流比率', '0.0568', '0.0577', '2024'),
('51a4c858-20f5-4819-ba5c-5df1068f4ef8', 'test_region_east', 'AI007', '总资产周转率', '0.0792', '0.0923', '2024'),
('cb3e3e6d-029d-4f0e-a70d-6208383af8f8', 'test_region_east', 'AI008', '成本费用利润率', '0.1080', '0.1226', '2024'),
('d25d05bf-0a57-40a7-90fd-876b38b40efd', 'test_region_east', 'AI009', '国有资本保值增值率', '0.0920', '0.1193', '2024'),
('f7aada1a-8eb5-4ba1-9622-a754628bc49e', 'test_region_north', 'AI001', '净资产收益率', '0.1417', '0.1472', '2024'),
('2d7ee645-3e05-4c4f-afa1-c5c2764169ca', 'test_region_north', 'AI002', '营业收入利润率', '0.1091', '0.1351', '2024'),
('ee252cd5-962b-4337-8286-6ad61b8c15de', 'test_region_north', 'AI003', '研发投入强度', '0.1337', '0.1484', '2024'),
('42798303-4b5f-4b2b-b781-de1e0a765785', 'test_region_north', 'AI004', '全员劳动生产率', '0.0799', '0.0921', '2024'),
('becdae12-c24a-4a43-8185-c09a41a36a3c', 'test_region_north', 'AI005', '资产负债率', '0.0560', '0.0567', '2024'),
('10cead01-0853-4e75-b47f-9c3ab8f5a2cf', 'test_region_north', 'AI006', '经营性现金流比率', '0.1000', '0.1142', '2024'),
('79652558-34f6-4f97-9e89-a3a32175e3bb', 'test_region_north', 'AI007', '总资产周转率', '0.0723', '0.0917', '2024'),
('15ff2a6c-7a13-4640-a396-b11b253eb929', 'test_region_north', 'AI008', '成本费用利润率', '0.0992', '0.1174', '2024'),
('75c8d899-c8db-4328-92a5-5726892229cb', 'test_region_north', 'AI009', '国有资本保值增值率', '0.1089', '0.1290', '2024'),
('c6e398e6-8d45-403f-b759-ccbe7f07fb37', 'test_sub_east_a', 'AI001', '净资产收益率', '0.1391', '0.1603', '2024'),
('e92f7353-421d-4aaa-bac5-3961d75d464b', 'test_sub_east_a', 'AI002', '营业收入利润率', '0.1299', '0.1575', '2024'),
('b12a91d4-2ce3-4c0a-8cda-274d9d791ebe', 'test_sub_east_a', 'AI003', '研发投入强度', '0.1212', '0.1218', '2024'),
('5ec611d7-9b22-4478-be78-9bc4a232dbbb', 'test_sub_east_a', 'AI004', '全员劳动生产率', '0.1511', '0.1955', '2024'),
('0c04317d-c1be-4094-b9a4-3ab47d0c39f9', 'test_sub_east_a', 'AI005', '资产负债率', '0.0962', '0.1221', '2024'),
('68fc58d5-5ff3-48df-8ff2-0dbb55b2a58a', 'test_sub_east_a', 'AI006', '经营性现金流比率', '0.1444', '0.1703', '2024'),
('8fe9ce20-a856-4b12-bd61-e07b4af6b725', 'test_sub_east_a', 'AI007', '总资产周转率', '0.1951', '0.2409', '2024'),
('1136d7e5-ace8-4b74-a341-5b3a5866306d', 'test_sub_east_a', 'AI008', '成本费用利润率', '0.1366', '0.1662', '2024'),
('8fed6061-73d4-4114-ac0c-ed34aff784e5', 'test_sub_east_a', 'AI009', '国有资本保值增值率', '0.1221', '0.1413', '2024'),
('30642bae-48a8-4511-848b-55c893a39ff1', 'test_sub_east_b', 'AI001', '净资产收益率', '0.1430', '0.1791', '2024'),
('c8861560-1e30-4842-b4ef-35c7a083a1c3', 'test_sub_east_b', 'AI002', '营业收入利润率', '0.1732', '0.1531', '2024'),
('253ab7dd-a5ed-42fb-be2a-d2cf61203bfb', 'test_sub_east_b', 'AI003', '研发投入强度', '0.1922', '0.1663', '2024'),
('5b06c44a-feed-42ec-83da-76a8fdeb6375', 'test_sub_east_b', 'AI004', '全员劳动生产率', '0.1162', '0.1056', '2024'),
('1295ef77-f335-4284-a32f-36faa0ff194d', 'test_sub_east_b', 'AI005', '资产负债率', '0.1536', '0.1394', '2024'),
('ff6addae-1776-4b6a-85e4-a2bf211182f1', 'test_sub_east_b', 'AI006', '经营性现金流比率', '0.1881', '0.1829', '2024'),
('1166b5ff-0978-455b-a38e-bf4ed9d86243', 'test_sub_east_b', 'AI007', '总资产周转率', '0.1591', '0.1510', '2024'),
('b441be94-e5d1-418d-8938-5fb0b4133127', 'test_sub_east_b', 'AI008', '成本费用利润率', '0.0811', '0.0726', '2024'),
('f674b3e0-412b-422a-b7a2-1b34c5691df1', 'test_sub_east_b', 'AI009', '国有资本保值增值率', '0.1218', '0.1100', '2024'),
('791d11c8-08be-4beb-a96d-f8c7a55a7602', 'test_sub_north_a', 'AI001', '净资产收益率', '0.1189', '0.1099', '2024'),
('7f38fec9-fb02-477a-9933-1bd2e307e693', 'test_sub_north_a', 'AI002', '营业收入利润率', '0.1031', '0.0988', '2024'),
('26ea210f-2ca0-413f-814b-4771f580195e', 'test_sub_north_a', 'AI003', '研发投入强度', '0.1521', '0.1464', '2024'),
('d09aa53a-d6a1-4ad1-8302-6c2303dc3b5c', 'test_sub_north_a', 'AI004', '全员劳动生产率', '0.1415', '0.0789', '2024'),
('0170ea8b-ce35-40fd-85a9-728f694d9123', 'test_sub_north_a', 'AI005', '资产负债率', '0.0919', '0.0542', '2024'),
('869d9709-35f6-459a-b14f-415125fe243b', 'test_sub_north_a', 'AI006', '经营性现金流比率', '0.1657', '0.1179', '2024'),
('ad691452-9a38-4bde-a356-2db26e08d39e', 'test_sub_north_a', 'AI007', '总资产周转率', '0.1557', '0.0927', '2024'),
('5a98e904-d78c-48a8-b046-47b9292c9922', 'test_sub_north_a', 'AI008', '成本费用利润率', '0.1341', '0.1046', '2024'),
('8576933a-cc3d-4cc2-8755-74d230e8f875', 'test_sub_north_a', 'AI009', '国有资本保值增值率', '0.0910', '0.0488', '2024');

