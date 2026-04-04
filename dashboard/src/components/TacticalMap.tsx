/**
 * TacticalMap — D3 Natural Earth 投影战术地图
 * 支持点位渲染、HUD 弹窗、动态连线
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';

export interface MapDot {
  id: string;
  lat: number;
  lon: number;
  label: string;
  type: 'group' | 'region' | 'entity' | 'account';
  risk: 'none' | 'low' | 'medium' | 'high';
  fiboClass?: string;
}

interface TacticalMapProps {
  dots: MapDot[];
  selectedDotId: string | null;
  onDotClick: (dot: MapDot, projectedPos: [number, number]) => void;
  isChina?: boolean;
}

const RISK_COLORS = {
  none: '#00ffb3',
  low: '#22d3ee',
  medium: '#ffaa00',
  high: '#ff2020',
};

const PROJECTION_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

export default function TacticalMap({ dots, selectedDotId, onDotClick, isChina = false }: TacticalMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [worldData, setWorldData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dotPositions, setDotPositions] = useState<Map<string, [number, number]>>(new Map());
  const [selectedPos, setSelectedPos] = useState<[number, number] | null>(null);

  // 加载世界地图数据
  useEffect(() => {
    fetch(PROJECTION_URL)
      .then(r => r.json())
      .then((data: any) => {
        setWorldData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // 渲染地图
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !worldData) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    // 投影
    const projection = d3.geoNaturalEarth1()
      .fitSize([width, height], isChina ? d3.geoGraticule()() as any : { type: 'Sphere' });

    const path = d3.geoPath().projection(projection);

    // SVG Defs（辉光滤镜）
    const defs = svg.append('defs');

    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%').attr('y', '-50%')
      .attr('width', '200%').attr('height', '200%');

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '2')
      .attr('result', 'coloredBlur');

    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // 深色背景
    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', '#020810');

    // 经纬网
    const graticule = d3.geoGraticule();
    svg.append('path')
      .datum(graticule())
      .attr('d', path)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,216,255,0.06)')
      .attr('stroke-width', 0.5);

    // 国家
    const countries = topojson.feature(
      worldData,
      worldData.objects['countries'] as any
    );

    svg.append('path')
      .datum(countries)
      .attr('d', path)
      .attr('fill', 'rgba(0,216,255,0.08)')
      .attr('stroke', 'rgba(0,216,255,0.25)')
      .attr('stroke-width', 0.5)
      .attr('filter', 'url(#glow)');

    // 记录点位投影位置
    const positions = new Map<string, [number, number]>();

    // 渲染点位
    dots.forEach(dot => {
      const projected = projection([dot.lon, dot.lat]);
      if (!projected) return;

      const [x, y] = projected;
      positions.set(dot.id, [x, y]);

      const g = svg.append('g')
        .attr('class', `map-dot${dot.risk === 'high' ? ' pulse-high' : ''}`)
        .style('cursor', 'pointer')
        .on('click', () => {
          setSelectedPos([x, y]);
          onDotClick(dot, [x, y]);
        });

      // 外圈
      g.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 5)
        .attr('fill', 'none')
        .attr('stroke', RISK_COLORS[dot.risk])
        .attr('stroke-width', 1.5)
        .attr('opacity', 0.6);

      // 核心点
      g.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 3)
        .attr('fill', RISK_COLORS[dot.risk])
        .style('filter', `drop-shadow(0 0 4px ${RISK_COLORS[dot.risk]})`);

      // 标签
      if (dot.type === 'entity' || dot.type === 'region') {
        g.append('text')
          .attr('x', x)
          .attr('y', y - 10)
          .attr('text-anchor', 'middle')
          .attr('fill', 'var(--text-secondary)')
          .attr('font-size', '10px')
          .attr('font-family', 'Share Tech Mono, monospace')
          .text(dot.label);
      }
    });

    setDotPositions(positions);

    // 扫描线
    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', 'none')
      .attr('stroke', 'none')
      .style('position', 'relative')
      .append('div')
      .attr('class', 'scanline-beam');

  }, [worldData, dots, isChina]);

  // 更新选中点位置
  useEffect(() => {
    if (selectedDotId && dotPositions.has(selectedDotId)) {
      setSelectedPos(dotPositions.get(selectedDotId)!);
    } else {
      setSelectedPos(null);
    }
  }, [selectedDotId, dotPositions]);

  // 队列→地图导航：监听 focus-dot 事件
  useEffect(() => {
    function handleFocusDot(e: Event) {
      const custom = e as CustomEvent<{ dot: MapDot }>;
      const dot = custom.detail.dot;
      if (dotPositions.has(dot.id)) {
        const pos = dotPositions.get(dot.id)!;
        setSelectedPos(pos);
        onDotClick(dot, pos);
      }
    }
    // 监听全局 focus-dot 事件（由处置队列触发）
    window.addEventListener('focus-dot', handleFocusDot);
    return () => window.removeEventListener('focus-dot', handleFocusDot);
  }, [dotPositions, onDotClick]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      {loading && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--cyan)', fontFamily: 'var(--font-mono)', fontSize: '12px',
        }}>
          加载地图数据...
        </div>
      )}

      {/* 扫描线 */}
      <div className="scanline-beam" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(to bottom, transparent, rgba(0,216,255,0.15), transparent)', animation: 'scanline 6s linear infinite', pointerEvents: 'none', zIndex: 10 }} />

      <svg ref={svgRef} style={{ display: 'block' }} />
    </div>
  );
}
