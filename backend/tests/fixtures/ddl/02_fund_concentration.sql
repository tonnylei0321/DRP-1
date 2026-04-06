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

