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

