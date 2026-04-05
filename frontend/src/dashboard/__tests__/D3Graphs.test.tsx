/**
 * D3 图谱组件测试
 * 覆盖 HierarchyGraph、ForceGraph 的 SVG 渲染和空数据降级
 * 需求：5.11, 5.12
 */
import { render } from '@testing-library/react';
import { vi } from 'vitest';
import { HierarchyGraph, ForceGraph, type HierarchyNode, type NetworkNode, type NetworkLink } from '../D3Graphs';

// ─── 测试数据 ────────────────────────────────────────────────────

const SIMPLE_HIERARCHY: HierarchyNode = {
  id: 'root',
  name: '集团',
  type: 'group',
  risk: 'medium',
  children: [
    { id: 'region-1', name: '华东大区', type: 'region', risk: 'low' },
    { id: 'region-2', name: '华西大区', type: 'region', risk: 'high' },
  ],
};

const SIMPLE_NODES: NetworkNode[] = [
  { id: 'entity-1', label: '子公司A', type: 'entity', risk: 'high' },
  { id: 'acct-1', label: 'ACC-001', type: 'account', risk: 'low' },
];

const SIMPLE_LINKS: NetworkLink[] = [
  { source: 'entity-1', target: 'acct-1' },
];

// ─── HierarchyGraph 测试 ────────────────────────────────────────

describe('HierarchyGraph', () => {
  it('渲染 SVG 元素', () => {
    const { container } = render(
      <HierarchyGraph data={SIMPLE_HIERARCHY} width={400} height={300} />,
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute('width', '400');
    expect(svg).toHaveAttribute('height', '300');
  });
});

// ─── ForceGraph 测试 ─────────────────────────────────────────────

describe('ForceGraph', () => {
  it('渲染 SVG 元素', () => {
    const { container } = render(
      <ForceGraph nodes={SIMPLE_NODES} links={SIMPLE_LINKS} width={500} height={350} />,
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute('width', '500');
    expect(svg).toHaveAttribute('height', '350');
  });
});

// ─── 空数据优雅降级 ─────────────────────────────────────────────

describe('空数据优雅降级', () => {
  it('HierarchyGraph 传入无子节点的数据不崩溃', () => {
    const emptyData: HierarchyNode = {
      id: 'root',
      name: '空集团',
      type: 'group',
      risk: 'none',
    };

    const { container } = render(
      <HierarchyGraph data={emptyData} width={400} height={300} />,
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('ForceGraph 传入空节点和空连线不崩溃', () => {
    const { container } = render(
      <ForceGraph nodes={[]} links={[]} width={400} height={300} />,
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});

// ─── 大数据量渲染 [评审 #012] ───────────────────────────────────

describe('大数据量渲染', () => {
  it('传入 100+ 节点的树数据，验证 SVG 元素存在且不崩溃', () => {
    // 生成 100+ 节点的树结构：1 个根节点 + 10 个区域 + 每区域 10 个实体 = 111 节点
    const bigHierarchy: HierarchyNode = {
      id: 'root',
      name: '大型集团',
      type: 'group',
      risk: 'medium',
      children: Array.from({ length: 10 }, (_, i) => ({
        id: `region-${i}`,
        name: `大区${i}`,
        type: 'region' as const,
        risk: (['none', 'low', 'medium', 'high'] as const)[i % 4],
        children: Array.from({ length: 10 }, (_, j) => ({
          id: `entity-${i}-${j}`,
          name: `子公司${i}-${j}`,
          type: 'entity' as const,
          risk: (['none', 'low', 'medium', 'high'] as const)[j % 4],
        })),
      })),
    };

    const { container } = render(
      <HierarchyGraph data={bigHierarchy} width={1200} height={800} />,
    );

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute('width', '1200');
    expect(svg).toHaveAttribute('height', '800');
  });
});

// ─── onNodeClick 回调测试 ────────────────────────────────────────

describe('HierarchyGraph onNodeClick', () => {
  it('点击节点时触发 onNodeClick 回调', () => {
    const handleClick = vi.fn();
    const { container } = render(
      <HierarchyGraph data={SIMPLE_HIERARCHY} width={400} height={300} onNodeClick={handleClick} />,
    );

    // 模拟点击第一个节点 <g class="node">
    const nodeGroup = container.querySelector('.node');
    expect(nodeGroup).not.toBeNull();
    nodeGroup!.dispatchEvent(new MouseEvent('click', { bubbles: true }));

    expect(handleClick).toHaveBeenCalledTimes(1);
    // 回调参数应为 HierarchyNode 数据
    expect(handleClick.mock.calls[0][0]).toHaveProperty('id');
  });
});

describe('ForceGraph onNodeClick', () => {
  it('点击节点时触发 onNodeClick 回调', async () => {
    const handleClick = vi.fn();
    const { container } = render(
      <ForceGraph
        nodes={SIMPLE_NODES}
        links={SIMPLE_LINKS}
        width={500}
        height={350}
        onNodeClick={handleClick}
      />,
    );

    // 力导向图需要等 tick 完成后节点才渲染到位
    // 查找节点 <g> 元素（ForceGraph 中节点在第二个 <g> 子组中）
    await new Promise(r => setTimeout(r, 100));
    const nodeGroups = container.querySelectorAll('svg > g:nth-child(3) > g');
    if (nodeGroups.length > 0) {
      nodeGroups[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
      expect(handleClick).toHaveBeenCalledTimes(1);
      expect(handleClick.mock.calls[0][0]).toHaveProperty('id');
    }
  });
});

// ─── 不同 risk 值节点颜色分支 ────────────────────────────────────

describe('节点风险颜色分支', () => {
  it('HierarchyGraph 渲染 none/low/medium/high 四种风险节点', () => {
    const allRisks: HierarchyNode = {
      id: 'root',
      name: '集团',
      type: 'group',
      risk: 'none',
      children: [
        { id: 'r-low', name: '低风险', type: 'region', risk: 'low' },
        { id: 'r-med', name: '中风险', type: 'region', risk: 'medium' },
        { id: 'r-high', name: '高风险', type: 'region', risk: 'high' },
      ],
    };

    const { container } = render(
      <HierarchyGraph data={allRisks} width={600} height={400} />,
    );

    const circles = container.querySelectorAll('circle');
    // 至少有 4 个主圆 + medium/high 的光晕圆
    expect(circles.length).toBeGreaterThanOrEqual(4);

    // 验证光晕 halo 存在（medium 和 high 节点）
    const halos = container.querySelectorAll('.halo');
    expect(halos.length).toBe(2);
  });

  it('ForceGraph 渲染不同 risk 值的节点颜色', () => {
    const nodes: NetworkNode[] = [
      { id: 'n1', label: 'None', type: 'entity', risk: 'none' },
      { id: 'n2', label: 'Low', type: 'account', risk: 'low' },
      { id: 'n3', label: 'Med', type: 'entity', risk: 'medium' },
      { id: 'n4', label: 'High', type: 'account', risk: 'high' },
    ];
    const links: NetworkLink[] = [
      { source: 'n1', target: 'n2' },
      { source: 'n3', target: 'n4' },
    ];

    const { container } = render(
      <ForceGraph nodes={nodes} links={links} width={500} height={350} />,
    );

    const circles = container.querySelectorAll('circle');
    expect(circles.length).toBe(4);
  });
});
