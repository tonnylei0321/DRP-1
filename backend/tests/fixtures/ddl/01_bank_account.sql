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

