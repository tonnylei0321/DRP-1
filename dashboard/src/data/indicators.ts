/**
 * 监控指标数据 — 106 个 FIBO 标注指标 + CTIO 7域体系
 */
export interface Indicator {
  name: string;
  fiboName: string;
  value: number;
  unit: string;
  risk: 'none' | 'low' | 'medium' | 'high';
}

// ============================================================================
// CTIO 7域指标体系
// ============================================================================

/** CTIO 7大业务域 */
export type CtioDomainCode = 'BA' | 'CC' | 'ST' | 'BL' | 'DF' | 'DR' | 'SA';

export interface CtioIndicator {
  code: string;           // IND-BA-001 格式
  name: string;           // 指标名称
  domain: CtioDomainCode; // 所属域
  currentValue: number;   // 当前值
  targetValue: number;    // 目标值
  warnThreshold: number; // 预警阈值
  redLine: number;       // 红线阈值
  unit: string;           // 单位
  isInverse: boolean;    // 是否为反向指标（越小越好）
}

/** 7域指标集合（按 spec 的 6轴红线指标） */
export const CTIO_RADAR_INDICATORS: CtioIndicator[] = [
  // 轴1: 账户直联率 IND-BA-002 ≥95%
  { code: 'IND-BA-002', name: '账户直联率', domain: 'BA', currentValue: 96.8, targetValue: 98.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
  // 轴2: 全口径资金集中率 IND-CC-001 ≥95%
  { code: 'IND-CC-001', name: '全口径资金集中率', domain: 'CC', currentValue: 94.2, targetValue: 96.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
  // 轴3: 可归集资金集中率 IND-CC-002 ≥85%
  { code: 'IND-CC-002', name: '可归集资金集中率', domain: 'CC', currentValue: 87.6, targetValue: 90.0, warnThreshold: 85.0, redLine: 85.0, unit: '%', isInverse: false },
  // 轴4: 结算直联率 IND-ST-001 ≥95%
  { code: 'IND-ST-001', name: '结算直联率', domain: 'ST', currentValue: 97.1, targetValue: 98.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
  // 轴5: 票据背书链深度 IND-BL-001 ≤20层
  { code: 'IND-BL-001', name: '票据背书链深度', domain: 'BL', currentValue: 18, targetValue: 15, warnThreshold: 20, redLine: 20, unit: '层', isInverse: true },
  // 轴6: 6311还款完成率 IND-DF-001 ≥100%
  { code: 'IND-DF-001', name: '6311还款完成率', domain: 'DF', currentValue: 102.3, targetValue: 100.0, warnThreshold: 100.0, redLine: 100.0, unit: '%', isInverse: false },
];

/** 7域完整指标集 */
export const CTIO_DOMAIN_INDICATORS: Record<CtioDomainCode, CtioIndicator[]> = {
  BA: [ // 银行账户监管
    { code: 'IND-BA-001', name: '银行账户总数', domain: 'BA', currentValue: 287, targetValue: 300, warnThreshold: 320, redLine: 350, unit: '户', isInverse: true },
    { code: 'IND-BA-002', name: '账户直联率', domain: 'BA', currentValue: 96.8, targetValue: 98.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-BA-003', name: 'U-Key配置率', domain: 'BA', currentValue: 99.2, targetValue: 100.0, warnThreshold: 98.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-BA-004', name: '账户月均余额', domain: 'BA', currentValue: 56700, targetValue: 60000, warnThreshold: 45000, redLine: 30000, unit: '万元', isInverse: false },
    { code: 'IND-BA-005', name: '异常登录次数', domain: 'BA', currentValue: 3, targetValue: 0, warnThreshold: 5, redLine: 10, unit: '次', isInverse: true },
  ],
  CC: [ // 资金集中监管
    { code: 'IND-CC-001', name: '全口径资金集中率', domain: 'CC', currentValue: 94.2, targetValue: 96.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-CC-002', name: '可归集资金集中率', domain: 'CC', currentValue: 87.6, targetValue: 90.0, warnThreshold: 85.0, redLine: 85.0, unit: '%', isInverse: false },
    { code: 'IND-CC-003', name: '资金归集账户数', domain: 'CC', currentValue: 156, targetValue: 160, warnThreshold: 150, redLine: 140, unit: '户', isInverse: false },
    { code: 'IND-CC-004', name: '归集现金池数', domain: 'CC', currentValue: 12, targetValue: 15, warnThreshold: 18, redLine: 20, unit: '个', isInverse: true },
    { code: 'IND-CC-005', name: '跨境资金归集额', domain: 'CC', currentValue: 8900, targetValue: 10000, warnThreshold: 12000, redLine: 15000, unit: '万元', isInverse: true },
  ],
  ST: [ // 结算监管
    { code: 'IND-ST-001', name: '结算直联率', domain: 'ST', currentValue: 97.1, targetValue: 98.0, warnThreshold: 95.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-ST-002', name: '自动结算率', domain: 'ST', currentValue: 94.5, targetValue: 96.0, warnThreshold: 93.0, redLine: 90.0, unit: '%', isInverse: false },
    { code: 'IND-ST-003', name: '结算失败率', domain: 'ST', currentValue: 0.12, targetValue: 0.05, warnThreshold: 0.2, redLine: 0.5, unit: '%', isInverse: true },
    { code: 'IND-ST-004', name: '跨境结算额', domain: 'ST', currentValue: 45600, targetValue: 50000, warnThreshold: 60000, redLine: 80000, unit: '万元', isInverse: true },
    { code: 'IND-ST-005', name: '人工干预率', domain: 'ST', currentValue: 5.5, targetValue: 4.0, warnThreshold: 7.0, redLine: 10.0, unit: '%', isInverse: true },
  ],
  BL: [ // 票据监管
    { code: 'IND-BL-001', name: '票据背书链深度', domain: 'BL', currentValue: 18, targetValue: 15, warnThreshold: 20, redLine: 20, unit: '层', isInverse: true },
    { code: 'IND-BL-002', name: '票据承兑余额', domain: 'BL', currentValue: 23400, targetValue: 25000, warnThreshold: 30000, redLine: 35000, unit: '万元', isInverse: true },
    { code: 'IND-BL-003', name: '商业票据贴现量', domain: 'BL', currentValue: 8900, targetValue: 10000, warnThreshold: 12000, redLine: 15000, unit: '万元', isInverse: true },
    { code: 'IND-BL-004', name: '票据拒付率', domain: 'BL', currentValue: 0.08, targetValue: 0.0, warnThreshold: 0.1, redLine: 0.3, unit: '%', isInverse: true },
    { code: 'IND-BL-005', name: '票据逾期率', domain: 'BL', currentValue: 0.23, targetValue: 0.1, warnThreshold: 0.5, redLine: 1.0, unit: '%', isInverse: true },
  ],
  DF: [ // 债务融资监管
    { code: 'IND-DF-001', name: '6311还款完成率', domain: 'DF', currentValue: 102.3, targetValue: 100.0, warnThreshold: 100.0, redLine: 100.0, unit: '%', isInverse: false },
    { code: 'IND-DF-002', name: '担保合规率', domain: 'DF', currentValue: 96.7, targetValue: 98.0, warnThreshold: 95.0, redLine: 92.0, unit: '%', isInverse: false },
    { code: 'IND-DF-003', name: '对外担保总额', domain: 'DF', currentValue: 56700, targetValue: 50000, warnThreshold: 60000, redLine: 80000, unit: '万元', isInverse: true },
    { code: 'IND-DF-004', name: '关联担保比例', domain: 'DF', currentValue: 34.5, targetValue: 30.0, warnThreshold: 40.0, redLine: 50.0, unit: '%', isInverse: true },
    { code: 'IND-DF-005', name: '融资成本率', domain: 'DF', currentValue: 4.28, targetValue: 4.0, warnThreshold: 4.5, redLine: 5.0, unit: '%', isInverse: true },
  ],
  DR: [ // 决策风险
    { code: 'IND-DR-001', name: '资金决策合规率', domain: 'DR', currentValue: 97.8, targetValue: 99.0, warnThreshold: 96.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-DR-002', name: '关联交易合规率', domain: 'DR', currentValue: 95.2, targetValue: 98.0, warnThreshold: 95.0, redLine: 92.0, unit: '%', isInverse: false },
    { code: 'IND-DR-003', name: '重大决策审批率', domain: 'DR', currentValue: 99.5, targetValue: 100.0, warnThreshold: 98.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-DR-004', name: '决策追溯覆盖率', domain: 'DR', currentValue: 92.3, targetValue: 95.0, warnThreshold: 90.0, redLine: 85.0, unit: '%', isInverse: false },
    { code: 'IND-DR-005', name: '违规决策数', domain: 'DR', currentValue: 2, targetValue: 0, warnThreshold: 3, redLine: 5, unit: '项', isInverse: true },
  ],
  SA: [ // 国资委考核
    { code: 'IND-SA-001', name: '报表提交及时率', domain: 'SA', currentValue: 99.8, targetValue: 100.0, warnThreshold: 98.0, redLine: 95.0, unit: '%', isInverse: false },
    { code: 'IND-SA-002', name: '资金管理评级', domain: 'SA', currentValue: 1, targetValue: 1, warnThreshold: 2, redLine: 3, unit: '级', isInverse: true },
    { code: 'IND-SA-003', name: '内控评价得分', domain: 'SA', currentValue: 94.5, targetValue: 95.0, warnThreshold: 90.0, redLine: 85.0, unit: '分', isInverse: false },
    { code: 'IND-SA-004', name: '审计问题整改率', domain: 'SA', currentValue: 97.2, targetValue: 100.0, warnThreshold: 95.0, redLine: 90.0, unit: '%', isInverse: false },
    { code: 'IND-SA-005', name: '重大风险事件数', domain: 'SA', currentValue: 0, targetValue: 0, warnThreshold: 1, redLine: 3, unit: '件', isInverse: true },
  ],
};

/** 域元数据 */
export const CTIO_DOMAINS: Record<CtioDomainCode, { name: string; description: string }> = {
  BA: { name: '银行账户监管', description: '直联率、U-Key配置率' },
  CC: { name: '资金集中监管', description: '全口径集中率、可归集集中率' },
  ST: { name: '结算监管', description: '结算直联率、自动结算率' },
  BL: { name: '票据监管', description: '背书链深度、票据承兑' },
  DF: { name: '债务融资监管', description: '6311还款完成率、担保合规率' },
  DR: { name: '决策风险', description: '资金决策合规率、关联交易合规率' },
  SA: { name: '国资委考核', description: '报表提交及时率、资金管理评级' },
};

/** 计算域合规率 */
export function computeDomainMetrics(): Array<{
  code: CtioDomainCode;
  name: string;
  count: number;
  compliantCount: number;
  compliantRate: number;
  riskLevel: 'critical' | 'warn' | 'info' | 'ok';
}> {
  return (Object.keys(CTIO_DOMAIN_INDICATORS) as CtioDomainCode[]).map(code => {
    const indicators = CTIO_DOMAIN_INDICATORS[code];
    const count = indicators.length;
    const compliantCount = indicators.filter(ind => {
      if (ind.isInverse) {
        return ind.currentValue <= ind.warnThreshold;
      }
      return ind.currentValue >= ind.warnThreshold;
    }).length;
    const compliantRate = count > 0 ? (compliantCount / count) * 100 : 0;
    let riskLevel: 'critical' | 'warn' | 'info' | 'ok' = 'ok';
    if (compliantRate < 90) riskLevel = 'critical';
    else if (compliantRate < 95) riskLevel = 'warn';
    else if (compliantRate < 98) riskLevel = 'info';
    return { code, name: CTIO_DOMAINS[code].name, count, compliantCount, compliantRate, riskLevel };
  });
}

/** 计算雷达轴数据 */
export function computeRadarAxes() {
  return CTIO_RADAR_INDICATORS.map(ind => ({
    label: ind.name,
    code: ind.code,
    currentValue: ind.isInverse
      ? Math.max(0, 100 - (ind.currentValue / ind.redLine) * 50) // 反向指标归一化
      : Math.min(100, (ind.currentValue / ind.redLine) * 100),
    redLine: 80, // 红线基准（80%为警戒线）
    unit: ind.unit,
    isInverse: ind.isInverse,
  }));
}

// 106 个指标（按 FIBO 分类）
export const INDICATORS: Indicator[] = [
  // 集团层级
  { name: '集团总资产', fiboName: 'fibobe:TotalAssets', value: 125670000, unit: '万元', risk: 'none' },
  { name: '集团净资产', fiboName: 'fibobe:NetAssets', value: 89340000, unit: '万元', risk: 'none' },
  { name: '合并报表子公司数', fiboName: 'fibobe:ConsolidatedSubsidiaries', value: 47, unit: '家', risk: 'none' },
  { name: '境外子公司数', fiboName: 'fibobe:ForeignSubsidiaries', value: 12, unit: '家', risk: 'low' },
  { name: '关联交易总额', fiboName: 'fibobe:RelatedPartyTransactionTotal', value: 2340000, unit: '万元', risk: 'medium' },
  { name: '担保总额', fiboName: 'fibobe:GuaranteeTotal', value: 5670000, unit: '万元', risk: 'high' },
  { name: '对外担保', fiboName: 'fibobe:ExternalGuarantee', value: 3200000, unit: '万元', risk: 'high' },
  { name: '关联担保', fiboName: 'fibobe:RelatedGuarantee', value: 2450000, unit: '万元', risk: 'medium' },
  { name: '资金归集率', fiboName: 'fibobe:CashPoolingRate', value: 87.3, unit: '%', risk: 'none' },
  { name: '集中度风险', fiboName: 'fibobe:ConcentrationRisk', value: 23.5, unit: '%', risk: 'low' },
  // 区域维度
  { name: '华东大区资产', fiboName: 'fibobe:RegionalAssets', value: 45670000, unit: '万元', risk: 'none' },
  { name: '华北大区资产', fiboName: 'fibobe:RegionalAssets', value: 28900000, unit: '万元', risk: 'none' },
  { name: '华南大区资产', fiboName: 'fibobe:RegionalAssets', value: 31200000, unit: '万元', risk: 'none' },
  { name: '华西大区资产', fiboName: 'fibobe:RegionalAssets', value: 19800000, unit: '万元', risk: 'none' },
  { name: '境外区域资产', fiboName: 'fibobe:OverseasAssets', value: 15600000, unit: '万元', risk: 'medium' },
  // 穿透维度
  { name: '实际控制人穿透深度', fiboName: 'fibobe:ControlDepth', value: 4, unit: '层', risk: 'none' },
  { name: '股权嵌套层级', fiboName: 'fibobe:EquityNestingLevel', value: 3, unit: '层', risk: 'low' },
  { name: 'SPV 数量', fiboName: 'fibobe:SPVCount', value: 23, unit: '个', risk: 'medium' },
  { name: '特殊目的载体', fiboName: 'fibobe:SpecialPurposeVehicle', value: 23, unit: '个', risk: 'medium' },
  { name: '通道类资产', fiboName: 'fibobe:ChannelAssets', value: 890000, unit: '万元', risk: 'high' },
  // 资金流维度
  { name: '经营性现金流', fiboName: 'fibobe:OperatingCashFlow', value: 3456000, unit: '万元', risk: 'none' },
  { name: '投资性现金流', fiboName: 'fibobe:InvestingCashFlow', value: -1230000, unit: '万元', risk: 'low' },
  { name: '筹资性现金流', fiboName: 'fibobe:FinancingCashFlow', value: -890000, unit: '万元', risk: 'low' },
  { name: '净现金流', fiboName: 'fibobe:NetCashFlow', value: 1336000, unit: '万元', risk: 'none' },
  { name: '资金占用额', fiboName: 'fibobe:FundOccupation', value: 456000, unit: '万元', risk: 'high' },
  // 合规维度
  { name: '监管评级', fiboName: 'fibobe:RegulatoryRating', value: 2, unit: '级', risk: 'none' },
  { name: '合规检查通过率', fiboName: 'fibobe:CompliancePassRate', value: 96.5, unit: '%', risk: 'none' },
  { name: '违规笔数', fiboName: 'fibobe:ViolationCount', value: 3, unit: '笔', risk: 'medium' },
  { name: '行政处罚次数', fiboName: 'fibobe:AdministrativePenalty', value: 0, unit: '次', risk: 'none' },
  { name: '重大诉讼数量', fiboName: 'fibobe:MajorLitigationCount', value: 1, unit: '件', risk: 'medium' },
  // 账户维度
  { name: '银行账户总数', fiboName: 'fibobe:BankAccountCount', value: 287, unit: '户', risk: 'none' },
  { name: '直联账户数', fiboName: 'fibobe:DirectlyLinkedAccountCount', value: 234, unit: '户', risk: 'none' },
  { name: '非直联账户数', fiboName: 'fibobe:NonDirectAccountCount', value: 53, unit: '户', risk: 'medium' },
  { name: '休眠账户数', fiboName: 'fibobe:DormantAccountCount', value: 12, unit: '户', risk: 'low' },
  { name: '账户集中度', fiboName: 'fibobe:AccountConcentration', value: 34.2, unit: '%', risk: 'low' },
  // 结算维度
  { name: '结算笔数', fiboName: 'fibobe:SettlementCount', value: 45678, unit: '笔', risk: 'none' },
  { name: '自动结算率', fiboName: 'fibobe:AutoSettlementRate', value: 94.5, unit: '%', risk: 'none' },
  { name: '人工干预率', fiboName: 'fibobe:ManualInterventionRate', value: 5.5, unit: '%', risk: 'low' },
  { name: '结算失败率', fiboName: 'fibobe:SettlementFailureRate', value: 0.12, unit: '%', risk: 'none' },
  { name: '跨境结算额', fiboName: 'fibobe:CrossBorderSettlementAmount', value: 8900000, unit: '万元', risk: 'medium' },
  // 风险维度
  { name: '流动性比例', fiboName: 'fibobe:LiquidityRatio', value: 156.7, unit: '%', risk: 'none' },
  { name: '杠杆率', fiboName: 'fibobe:LeverageRatio', value: 68.4, unit: '%', risk: 'low' },
  { name: '不良资产率', fiboName: 'fibobe:NonPerformingAssetRatio', value: 1.23, unit: '%', risk: 'low' },
  { name: '拨备覆盖率', fiboName: 'fibobe:ProvisionCoverage', value: 234.5, unit: '%', risk: 'none' },
  { name: '资本充足率', fiboName: 'fibobe:CapitalAdequacyRatio', value: 14.56, unit: '%', risk: 'none' },
  // ... 继续补充到 106 个
  { name: '客户集中度', fiboName: 'fibobe:CustomerConcentration', value: 28.3, unit: '%', risk: 'low' },
  { name: '供应商集中度', fiboName: 'fibobe:SupplierConcentration', value: 35.6, unit: '%', risk: 'medium' },
  { name: '收入集中度', fiboName: 'fibobe:RevenueConcentration', value: 42.1, unit: '%', risk: 'medium' },
  { name: '单一最大客户占比', fiboName: 'fibobe:LargestCustomerRatio', value: 15.7, unit: '%', risk: 'low' },
  { name: '应收账款周转天数', fiboName: 'fibobe:DSO', value: 87.3, unit: '天', risk: 'none' },
  { name: '存货周转天数', fiboName: 'fibobe:DIO', value: 45.6, unit: '天', risk: 'none' },
  { name: '应付账款周转天数', fiboName: 'fibobe:DPO', value: 67.8, unit: '天', risk: 'none' },
  { name: '现金周转周期', fiboName: 'fibobe:CashConversionCycle', value: 65.1, unit: '天', risk: 'none' },
  { name: '总资产周转率', fiboName: 'fibobe:TotalAssetTurnover', value: 0.56, unit: '次', risk: 'none' },
  { name: '净资产收益率', fiboName: 'fibobe:ROE', value: 12.34, unit: '%', risk: 'none' },
  { name: '总资产报酬率', fiboName: 'fibobe:ROA', value: 3.45, unit: '%', risk: 'none' },
  { name: '营业利润率', fiboName: 'fibobe:OperatingMargin', value: 18.67, unit: '%', risk: 'none' },
  { name: '成本收入比', fiboName: 'fibobe:CostToIncomeRatio', value: 35.2, unit: '%', risk: 'low' },
  { name: '资产负债率', fiboName: 'fibobe:DebtToAssetRatio', value: 68.4, unit: '%', risk: 'low' },
  { name: '流动比率', fiboName: 'fibobe:CurrentRatio', value: 1.56, unit: '', risk: 'none' },
  { name: '速动比率', fiboName: 'fibobe:QuickRatio', value: 1.23, unit: '', risk: 'none' },
  { name: '利息保障倍数', fiboName: 'fibobe:InterestCoverageRatio', value: 4.56, unit: '倍', risk: 'none' },
  { name: ' EBITDA', fiboName: 'fibobe:EBITDA', value: 8760000, unit: '万元', risk: 'none' },
  { name: '金融负债比例', fiboName: 'fibobe:FinancialLiabilityRatio', value: 45.6, unit: '%', risk: 'low' },
  { name: '短期债务占比', fiboName: 'fibobe:ShortTermDebtRatio', value: 38.9, unit: '%', risk: 'low' },
  { name: '长期债务占比', fiboName: 'fibobe:LongTermDebtRatio', value: 61.1, unit: '%', risk: 'none' },
  { name: '直接债务规模', fiboName: 'fibobe:DirectDebtScale', value: 34500000, unit: '万元', risk: 'medium' },
  { name: '间接债务规模', fiboName: 'fibobe:IndirectDebtScale', value: 12300000, unit: '万元', risk: 'high' },
  { name: '隐性债务', fiboName: 'fibobe:ContingentLiability', value: 8900000, unit: '万元', risk: 'high' },
  { name: '、或有负债', fiboName: 'fibobe:ContingentLiability', value: 5600000, unit: '万元', risk: 'medium' },
  { name: '对外捐赠', fiboName: 'fibobe:CharitableContributions', value: 1230, unit: '万元', risk: 'none' },
  { name: '税收贡献', fiboName: 'fibobe:TaxContribution', value: 56700, unit: '万元', risk: 'none' },
  { name: '就业人数', fiboName: 'fibobe:EmployeeCount', value: 23456, unit: '人', risk: 'none' },
  { name: '研发投入', fiboName: 'fibobe:R&DExpenditure', value: 89000, unit: '万元', risk: 'none' },
  { name: '专利数量', fiboName: 'fibobe:PatentCount', value: 567, unit: '项', risk: 'none' },
  { name: '营收增长率', fiboName: 'fibobe:RevenueGrowthRate', value: 12.3, unit: '%', risk: 'none' },
  { name: '利润增长率', fiboName: 'fibobe:ProfitGrowthRate', value: 15.6, unit: '%', risk: 'none' },
  { name: '资产增长率', fiboName: 'fibobe:AssetGrowthRate', value: 8.9, unit: '%', risk: 'low' },
  { name: '市场份额', fiboName: 'fibobe:MarketShare', value: 23.4, unit: '%', risk: 'none' },
  { name: '行业排名', fiboName: 'fibobe:IndustryRanking', value: 3, unit: '位', risk: 'none' },
  { name: '客户满意度', fiboName: 'fibobe:CustomerSatisfaction', value: 92.3, unit: '%', risk: 'none' },
  { name: '供应商稳定性', fiboName: 'fibobe:SupplierStability', value: 87.6, unit: '%', risk: 'low' },
  { name: '内控评分', fiboName: 'fibobe:InternalControlScore', value: 94.5, unit: '分', risk: 'none' },
  { name: '审计意见', fiboName: 'fibobe:AuditOpinion', value: 1, unit: '无保留', risk: 'none' },
  { name: '信息系统评级', fiboName: 'fibobe:ITSystemRating', value: 4, unit: '级', risk: 'none' },
  { name: '数据完整率', fiboName: 'fibobe:DataCompleteness', value: 99.2, unit: '%', risk: 'none' },
  { name: '数据时效性', fiboName: 'fibobe:DataTimeliness', value: 98.7, unit: '%', risk: 'none' },
  { name: '模型准确率', fiboName: 'fibobe:ModelAccuracy', value: 96.5, unit: '%', risk: 'none' },
  { name: '预警准确率', fiboName: 'fibobe:AlertAccuracy', value: 94.3, unit: '%', risk: 'none' },
  { name: '误报率', fiboName: 'fibobe:FalsePositiveRate', value: 3.2, unit: '%', risk: 'low' },
  { name: '漏报率', fiboName: 'fibobe:FalseNegativeRate', value: 0.8, unit: '%', risk: 'none' },
  { name: '响应时效', fiboName: 'fibobe:ResponseTime', value: 4.5, unit: '小时', risk: 'none' },
  { name: '穿透成功率', fiboName: 'fibobe:PenetrationSuccessRate', value: 97.8, unit: '%', risk: 'none' },
  { name: '匹配精度', fiboName: 'fibobe:MatchPrecision', value: 98.2, unit: '%', risk: 'none' },
  { name: '覆盖率', fiboName: 'fibobe:CoverageRate', value: 95.6, unit: '%', risk: 'none' },
];

// 示例实体树数据
export const DEMO_ENTITY_TREE = {
  id: 'root',
  name: '国有资本运营集团',
  type: 'group' as const,
  risk: 'medium' as const,
  children: [
    {
      id: 'region-east',
      name: '华东大区',
      type: 'region' as const,
      risk: 'low' as const,
      lat: 31.23,
      lon: 121.47,
      children: [
        { id: 'entity-1', name: '华东子公司A', type: 'entity' as const, risk: 'low' as const, lat: 31.23, lon: 121.47 },
        { id: 'entity-2', name: '华东子公司B', type: 'entity' as const, risk: 'high' as const, lat: 30.57, lon: 122.21 },
        { id: 'entity-3', name: '华东子公司C', type: 'entity' as const, risk: 'none' as const, lat: 32.06, lon: 118.78 },
      ],
    },
    {
      id: 'region-north',
      name: '华北大区',
      type: 'region' as const,
      risk: 'medium' as const,
      lat: 39.90,
      lon: 116.41,
      children: [
        { id: 'entity-4', name: '华北子公司A', type: 'entity' as const, risk: 'medium' as const, lat: 39.90, lon: 116.41 },
        { id: 'entity-5', name: '华北子公司B', type: 'entity' as const, risk: 'low' as const, lat: 40.15, lon: 117.21 },
      ],
    },
    {
      id: 'region-south',
      name: '华南大区',
      type: 'region' as const,
      risk: 'low' as const,
      lat: 23.13,
      lon: 113.26,
      children: [
        { id: 'entity-6', name: '华南子公司A', type: 'entity' as const, risk: 'none' as const, lat: 23.13, lon: 113.26 },
        { id: 'entity-7', name: '华南子公司B', type: 'entity' as const, risk: 'low' as const, lat: 22.54, lon: 114.06 },
      ],
    },
    {
      id: 'region-west',
      name: '华西大区',
      type: 'region' as const,
      risk: 'medium' as const,
      lat: 30.57,
      lon: 104.07,
      children: [
        { id: 'entity-8', name: '华西子公司A', type: 'entity' as const, risk: 'medium' as const, lat: 30.57, lon: 104.07 },
        { id: 'entity-9', name: '华西子公司B', type: 'entity' as const, risk: 'none' as const, lat: 29.56, lon: 106.55 },
      ],
    },
    {
      id: 'overseas',
      name: '境外区域',
      type: 'region' as const,
      risk: 'high' as const,
      lat: 51.51,
      lon: -0.13,
      children: [
        { id: 'entity-10', name: '香港SPV', type: 'entity' as const, risk: 'high' as const, lat: 22.32, lon: 114.17 },
        { id: 'entity-11', name: '开曼基金', type: 'entity' as const, risk: 'high' as const, lat: 19.30, lon: -81.25 },
        { id: 'entity-12', name: '新加坡分部', type: 'entity' as const, risk: 'low' as const, lat: 1.35, lon: 103.82 },
      ],
    },
  ],
};
