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

