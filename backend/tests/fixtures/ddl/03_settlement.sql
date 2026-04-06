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

