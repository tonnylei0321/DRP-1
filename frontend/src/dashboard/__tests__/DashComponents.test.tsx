/**
 * 看板子组件测试
 * 覆盖 HudPanel、RiskTicker、LayerFilterBar、DrillInspector
 * 需求：5.13, 5.14, 5.15
 */
import { render, screen, fireEvent } from '@testing-library/react';
import {
  HudPanel,
  RiskTicker,
  LayerFilterBar,
  DrillInspector,
  type HudNode,
  type LayerFilter,
} from '../DashComponents';
import type { RiskEvent } from '../useRiskEvents';

// ─── HudPanel 测试 ──────────────────────────────────────────────

describe('HudPanel', () => {
  const mockNode: HudNode = {
    id: 'entity-1',
    label: '华东子公司A',
    type: 'entity',
    risk: 'high',
    properties: { ID: 'entity-1', 风险等级: 'high', 类型: 'entity' },
  };

  it('显示节点标签、类型、风险等级和属性列表', () => {
    render(<HudPanel node={mockNode} lang="zh" onClose={() => {}} />);

    // 节点标签
    expect(screen.getByText('华东子公司A')).toBeInTheDocument();
    // 属性列表中的值
    expect(screen.getByText('entity-1')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('entity')).toBeInTheDocument();
    // 属性 key
    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('风险等级')).toBeInTheDocument();
    expect(screen.getByText('类型')).toBeInTheDocument();
  });

  it('点击关闭按钮触发 onClose', () => {
    const onClose = vi.fn();
    render(<HudPanel node={mockNode} lang="zh" onClose={onClose} />);

    // 关闭按钮是 ×
    fireEvent.click(screen.getByText('×'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('node 为 null 时不渲染任何内容', () => {
    const { container } = render(<HudPanel node={null} lang="zh" onClose={() => {}} />);
    expect(container.innerHTML).toBe('');
  });
});

// ─── RiskTicker 测试 ────────────────────────────────────────────

describe('RiskTicker', () => {
  it('非空 events 数组时显示风险事件滚动播报条', () => {
    const events: RiskEvent[] = [
      {
        type: 'risk_event',
        tenant_id: 't-1',
        indicator_id: 'ind-1',
        indicator_name: '资金集中度',
        domain: 'credit',
        value: 0.85,
        target_value: 1.0,
        threshold: 0.5,
        timestamp: '2024-01-01T00:00:00Z',
      },
    ];

    render(<RiskTicker events={events} lang="zh" />);

    // 应显示风险事件标题
    expect(screen.getByText(/风险事件/i)).toBeInTheDocument();
    // 应显示事件内容
    expect(screen.getByText(/credit/)).toBeInTheDocument();
    expect(screen.getByText(/资金集中度/)).toBeInTheDocument();
  });

  it('空 events 数组时不渲染任何内容', () => {
    const { container } = render(<RiskTicker events={[]} lang="zh" />);
    expect(container.innerHTML).toBe('');
  });
});

// ─── LayerFilterBar 测试 ────────────────────────────────────────

describe('LayerFilterBar', () => {
  it('点击按钮调用 onChange 回调并传入对应过滤值', () => {
    const onChange = vi.fn();
    render(<LayerFilterBar active="all" lang="zh" onChange={onChange} />);

    // 点击"资金流"按钮
    fireEvent.click(screen.getByText('资金流'));
    expect(onChange).toHaveBeenCalledWith('cashflow');

    // 点击"账户"按钮
    fireEvent.click(screen.getByText('账户'));
    expect(onChange).toHaveBeenCalledWith('accounts');

    // 点击"违规节点"按钮
    fireEvent.click(screen.getByText('违规节点'));
    expect(onChange).toHaveBeenCalledWith('violations');

    // 点击"全部图层"按钮
    fireEvent.click(screen.getByText('全部图层'));
    expect(onChange).toHaveBeenCalledWith('all');
  });
});

// ─── DrillInspector 测试 ────────────────────────────────────────

describe('DrillInspector', () => {
  it('空路径显示"暂无数据"', () => {
    render(<DrillInspector drillPath={[]} lang="zh" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('非空路径显示穿透步骤', () => {
    const drillPath = [
      { step: 1, node_iri: 'urn:drp:indicator:1', node_type: 'RegulatoryIndicator', node_label: '资金集中度' },
      { step: 2, node_iri: 'urn:drp:entity:1', node_type: 'LegalEntity', node_label: '华东子公司A' },
      { step: 3, node_iri: 'urn:drp:account:1', node_type: 'Account', node_label: 'ACC-001' },
    ];

    render(<DrillInspector drillPath={drillPath} lang="zh" />);

    // 应显示每个步骤的标签
    expect(screen.getByText('资金集中度')).toBeInTheDocument();
    expect(screen.getByText('华东子公司A')).toBeInTheDocument();
    expect(screen.getByText('ACC-001')).toBeInTheDocument();

    // 应显示步骤编号和类型
    expect(screen.getByText(/Step 1/)).toBeInTheDocument();
    expect(screen.getByText(/Step 2/)).toBeInTheDocument();
    expect(screen.getByText(/Step 3/)).toBeInTheDocument();
  });
});
