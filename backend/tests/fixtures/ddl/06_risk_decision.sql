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

