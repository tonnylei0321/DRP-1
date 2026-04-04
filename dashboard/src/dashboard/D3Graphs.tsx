/**
 * D3Graphs — 穿透式拓扑图
 * 层级骨架图（默认）+ 力导向子图（选中实体展开）
 */
import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { DEMO_ENTITY_TREE } from '../data/indicators';

interface GraphNode {
  id: string;
  label: string;
  type: 'group' | 'region' | 'entity' | 'account';
  risk: 'none' | 'low' | 'medium' | 'high';
}

interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

const RISK_COLORS: Record<string, string> = {
  none: '#00d8ff',
  low: '#22d3ee',
  medium: '#ffaa00',
  high: '#ff2020',
};

const RISK_GLOW: Record<string, string> = {
  none: 'rgba(0,216,255,0.3)',
  low: 'rgba(34,211,238,0.3)',
  medium: 'rgba(255,170,0,0.35)',
  high: 'rgba(255,32,32,0.4)',
};

export default function D3Graphs() {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dims, setDims] = useState({ width: 800, height: 600 });

  // 响应容器尺寸
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setDims({ width, height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // 渲染层级骨架图
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dims;

    // 背景
    svg.append('rect').attr('width', width).attr('height', height).attr('fill', '#020810');

    // ── 层级骨架图（默认总览）────────────────────────────────
    const root = d3.hierarchy(DEMO_ENTITY_TREE);
    const treeLayout = d3.tree<typeof DEMO_ENTITY_TREE>().size([width - 80, height - 100]);
    treeLayout(root as any);

    const g = svg.append('g').attr('transform', `translate(40,40)`);

    // 连线
    g.selectAll('.link').data(root.links() as any).join('path')
      .attr('class', 'link').attr('fill', 'none')
      .attr('stroke', 'rgba(0,216,255,0.15)').attr('stroke-width', 1.5)
      .attr('d', d3.linkVertical<any, any>()
        .x((d: any) => d.x).y((d: any) => d.y) as any);

    // 节点
    const node = g.selectAll('.node').data(root.descendants() as any).join('g')
      .attr('class', 'node')
      .attr('transform', (d: any) => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer');

    const r = (d: any) => d.depth === 0 ? 22 : d.depth === 1 ? 16 : 12;

    node.filter((d: any) => d.data.risk === 'high' || d.data.risk === 'medium')
      .append('circle').attr('r', (d: any) => r(d) + 8)
      .attr('fill', (d: any) => RISK_GLOW[d.data.risk]);

    node.append('circle')
      .attr('r', r)
      .attr('fill', (d: any) => RISK_COLORS[d.data.risk])
      .attr('stroke', '#0c2038').attr('stroke-width', 2);

    node.append('text')
      .attr('dy', (d: any) => r(d) + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', '#cde8f8').attr('font-size', '11px')
      .text((d: any) => d.data.name.length > 10 ? d.data.name.slice(0, 10) + '…' : d.data.name);

    return () => { if (svgRef.current) d3.select(svgRef.current).selectAll('*').remove(); };
  }, [dims]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <svg ref={svgRef} width={dims.width} height={dims.height} style={{ display: 'block' }} />
    </div>
  );
}

function findNode(node: any, id: string): any {
  if (node.id === id) return node;
  if (node.children) for (const c of node.children) { const f = findNode(c, id); if (f) return f; }
  return null;
}
