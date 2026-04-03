/**
 * 10.3 D3 层级骨架图 — 集团 → 大区 → 子公司，节点按风险着色
 * 10.4 D3 力导向子图 — 点击法人节点展开账户网络
 * 10.5 战术节点组件 — 圆形节点 + 呼吸光晕 + 风险状态动画
 */
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

// ─── 数据类型 ────────────────────────────────────────────────────────────────

export interface HierarchyNode {
  id: string;
  name: string;
  type: 'group' | 'region' | 'entity';
  risk: 'none' | 'low' | 'medium' | 'high';
  value?: number;
  children?: HierarchyNode[];
}

export interface NetworkNode {
  id: string;
  label: string;
  type: 'entity' | 'account';
  risk: 'none' | 'low' | 'medium' | 'high';
  x?: number;
  y?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
}

// ─── 颜色映射 ────────────────────────────────────────────────────────��────────

const RISK_COLORS: Record<string, string> = {
  none: '#3b82f6',
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
};

const RISK_GLOW: Record<string, string> = {
  none: 'rgba(59,130,246,0.3)',
  low: 'rgba(16,185,129,0.3)',
  medium: 'rgba(245,158,11,0.35)',
  high: 'rgba(239,68,68,0.4)',
};

// ─── HierarchyGraph — 10.3 ────────────────────────────────────────────────────

interface HierarchyGraphProps {
  data: HierarchyNode;
  width?: number;
  height?: number;
  onNodeClick?: (node: HierarchyNode) => void;
}

export function HierarchyGraph({ data, width = 800, height = 500, onNodeClick }: HierarchyGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g').attr('transform', `translate(${width / 2},60)`);

    const root = d3.hierarchy(data);
    const treeLayout = d3.tree<HierarchyNode>().size([width - 80, height - 120]);
    treeLayout(root);

    // 连线
    g.selectAll('.link')
      .data(root.links())
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#374151')
      .attr('stroke-width', 1.5)
      .attr('d', d3.linkVertical<d3.HierarchyPointLink<HierarchyNode>, d3.HierarchyPointNode<HierarchyNode>>()
        .x(d => (d as d3.HierarchyPointNode<HierarchyNode>).x - width / 2)
        .y(d => (d as d3.HierarchyPointNode<HierarchyNode>).y)
      );

    // 节点组
    const node = g.selectAll('.node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${(d as d3.HierarchyPointNode<HierarchyNode>).x - width / 2},${(d as d3.HierarchyPointNode<HierarchyNode>).y})`)
      .style('cursor', 'pointer')
      .on('click', (_evt, d) => onNodeClick?.(d.data));

    const r = (d: d3.HierarchyNode<HierarchyNode>) => d.depth === 0 ? 22 : d.depth === 1 ? 16 : 12;

    // 呼吸光晕（高风险节点）
    node.filter(d => d.data.risk === 'high' || d.data.risk === 'medium')
      .append('circle')
      .attr('r', d => r(d) + 6)
      .attr('fill', d => RISK_GLOW[d.data.risk])
      .attr('class', 'halo');

    // 节点主圆
    node.append('circle')
      .attr('r', r)
      .attr('fill', d => RISK_COLORS[d.data.risk])
      .attr('stroke', '#111827')
      .attr('stroke-width', 2);

    // 标签
    node.append('text')
      .attr('dy', d => r(d) + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', '#e5e7eb')
      .attr('font-size', '11px')
      .text(d => d.data.name.length > 8 ? d.data.name.slice(0, 8) + '…' : d.data.name);

  }, [data, width, height, onNodeClick]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ background: 'transparent', overflow: 'visible' }}
    />
  );
}

// ─── ForceGraph — 10.4 ───────────────────────────────────────────────────────

interface ForceGraphProps {
  nodes: NetworkNode[];
  links: NetworkLink[];
  width?: number;
  height?: number;
  onNodeClick?: (node: NetworkNode) => void;
}

export function ForceGraph({ nodes, links, width = 600, height = 400, onNodeClick }: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 箭头标记
    svg.append('defs').append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 18).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#6b7280');

    const simulation = d3.forceSimulation<NetworkNode>(nodes)
      .force('link', d3.forceLink<NetworkNode, NetworkLink>(links)
        .id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(25));

    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#374151')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrow)');

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('click', (_evt, d) => onNodeClick?.(d))
      .call(d3.drag<SVGGElement, NetworkNode>()
        .on('start', (evt, d) => {
          if (!evt.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (evt, d) => { d.fx = evt.x; d.fy = evt.y; })
        .on('end', (evt, d) => {
          if (!evt.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );

    node.append('circle')
      .attr('r', d => d.type === 'entity' ? 16 : 10)
      .attr('fill', d => RISK_COLORS[d.risk])
      .attr('stroke', '#0a0e1a')
      .attr('stroke-width', 2);

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 24)
      .attr('fill', '#9ca3af')
      .attr('font-size', '10px')
      .text(d => d.label.length > 10 ? d.label.slice(0, 10) + '…' : d.label);

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as NetworkNode).x ?? 0)
        .attr('y1', d => (d.source as NetworkNode).y ?? 0)
        .attr('x2', d => (d.target as NetworkNode).x ?? 0)
        .attr('y2', d => (d.target as NetworkNode).y ?? 0);
      node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => { simulation.stop(); };
  }, [nodes, links, width, height, onNodeClick]);

  return (
    <svg ref={svgRef} width={width} height={height}
      style={{ background: 'transparent', overflow: 'visible' }} />
  );
}
