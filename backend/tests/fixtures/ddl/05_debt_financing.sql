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

