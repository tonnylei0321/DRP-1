/**
 * 10.2 深色主题设计系统 & 10.11 中英文切换
 */

// CSS 变量已在 index.css 中定义（bg/accent/warn/danger/gold）

// ─── 10.11 i18n ───────────────────────────────────────────────────────────────

export type Lang = 'zh' | 'en';

export const STRINGS: Record<Lang, Record<string, string>> = {
  zh: {
    title: '穿透式资金监管看板',
    allLayers: '全部图层',
    cashFlow: '资金流',
    accounts: '账户',
    violations: '违规节点',
    riskEvents: '风险事件',
    indicator: '指标',
    entity: '法人实体',
    account: '账户',
    value: '当前值',
    target: '目标值',
    threshold: '阈值',
    compliant: '达标',
    nonCompliant: '不达标',
    drillDown: '穿透查看',
    lastUpdated: '数据截至',
    connecting: '连接中...',
    connected: '已连接',
    disconnected: '已断线',
    noData: '暂无数据',
    lang: 'EN',
  },
  en: {
    title: 'Capital Supervision Dashboard',
    allLayers: 'All Layers',
    cashFlow: 'Cash Flow',
    accounts: 'Accounts',
    violations: 'Violations',
    riskEvents: 'Risk Events',
    indicator: 'Indicator',
    entity: 'Legal Entity',
    account: 'Account',
    value: 'Current Value',
    target: 'Target',
    threshold: 'Threshold',
    compliant: 'Compliant',
    nonCompliant: 'Non-Compliant',
    drillDown: 'Drill Down',
    lastUpdated: 'As of',
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
    noData: 'No Data',
    lang: '中',
  },
};

export function t(lang: Lang, key: string): string {
  return STRINGS[lang][key] ?? key;
}
