/**
 * RiskRadar — 红线雷达盘：6轴展示4条红线指标
 */
import { useEffect, useRef, useState } from 'react';

export interface RadarAxis {
  label: string;
  code: string;
  currentValue: number;  // 0-100（百分比）
  redLine: number;        // 红线阈值
  unit: string;
  isInverse: boolean; // true=越小越好（如背书链深度）
}

interface RiskRadarProps {
  axes: RadarAxis[];
}

function polarToXY(angle: number, radius: number, cx: number, cy: number): [number, number] {
  const rad = (angle - 90) * (Math.PI / 180);
  return [cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)];
}

export default function RiskRadar({ axes }: RiskRadarProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100);
    return () => clearTimeout(t);
  }, []);

  const cx = 130;
  const cy = 110;
  const maxR = 80;

  if (axes.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
        暂无红线指标
      </div>
    );
  }

  const angleStep = 360 / axes.length;

  // 生成六边形网格
  const rings = [0.25, 0.5, 0.75, 1.0];
  const gridPolygons = rings.map(r => {
    const points = axes.map((_, i) => {
      const angle = i * angleStep;
      const [x, y] = polarToXY(angle, maxR * r, cx, cy);
      return `${x},${y}`;
    }).join(' ');
    return points;
  });

  // 数据折线
  const dataPoints = axes.map((axis, i) => {
    const angle = i * angleStep;
    // 归一化：对于正向指标 currentValue/100，对于反向（越小越好）redLine/currentValue
    let ratio = axis.isInverse
      ? Math.min(axis.redLine / Math.max(axis.currentValue, 0.01), 1)
      : Math.min(axis.currentValue / 100, 1);
    if (!animated) ratio = 0;
    const [x, y] = polarToXY(angle, maxR * ratio, cx, cy);
    return { x, y, axis };
  });

  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ') + ' Z';
  const dataArea = dataPath;

  // 绘制轴线和标签
  const axisLines = axes.map((axis, i) => {
    const angle = i * angleStep;
    const [ex, ey] = polarToXY(angle, maxR, cx, cy);
    const [lx, ly] = polarToXY(angle, maxR + 18, cx, cy);
    const isBelow = axis.currentValue < axis.redLine;

    return { axis, ex, ey, lx, ly, angle, isBelow };
  });

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '10px 12px',
      gap: '6px',
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '10px',
        color: 'var(--text-muted)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}>
        红线雷达
      </div>

      <svg ref={svgRef} viewBox="0 0 260 180" preserveAspectRatio="xMidYMid meet" style={{ flex: 1, minHeight: 0 }}>
        {/* 网格六边形 */}
        {gridPolygons.map((pts, i) => (
          <polygon
            key={`ring-${i}`}
            points={pts}
            fill="none"
            stroke="rgba(0,216,255,0.12)"
            strokeWidth="0.5"
          />
        ))}

        {/* 轴线 */}
        {axisLines.map(({ ex, ey, angle }, i) => (
          <line
            key={`axis-${i}`}
            x1={cx} y1={cy}
            x2={ex} y2={ey}
            stroke="rgba(0,216,255,0.15)"
            strokeWidth="0.5"
          />
        ))}

        {/* 数据区域 */}
        <path
          d={dataArea}
          fill="rgba(0,216,255,0.15)"
          stroke="rgba(0,216,255,0.6)"
          strokeWidth="1.5"
          style={{ transition: 'all 0.8s ease' }}
        />

        {/* 数据点 */}
        {dataPoints.map((p, i) => {
          const isDanger = p.axis.currentValue < p.axis.redLine;
          return (
            <circle
              key={`dot-${i}`}
              cx={p.x}
              cy={p.y}
              r={isDanger ? 4 : 3}
              fill={isDanger ? '#ff2020' : '#00d8ff'}
              style={{
                filter: isDanger ? 'drop-shadow(0 0 4px #ff2020)' : 'drop-shadow(0 0 3px #00d8ff)',
                transition: 'all 0.8s ease',
              }}
            />
          );
        })}

        {/* 标签 */}
        {axisLines.map(({ axis, lx, ly, angle, isBelow }, i) => {
          const textAnchor =
            lx < cx - 5 ? 'end' :
            lx > cx + 5 ? 'start' : 'middle';
          const dy = ly < cy - 5 ? '-0.3em' : ly > cy + 5 ? '1em' : '0.35em';

          return (
            <g key={`label-${i}`}>
              <text
                x={lx}
                y={ly}
                textAnchor={textAnchor}
                dominantBaseline="middle"
                fill={isBelow ? '#ff2020' : 'var(--text-secondary)'}
                fontSize="9"
                fontFamily="Share Tech Mono, monospace"
              >
                {axis.label}
              </text>
              <text
                x={lx}
                y={ly + (ly < cy ? 10 : -6)}
                textAnchor={textAnchor}
                dominantBaseline="middle"
                fill={isBelow ? '#ff2020' : 'var(--cyan)'}
                fontSize="11"
                fontWeight="700"
                fontFamily="Orbitron, monospace"
              >
                {axis.currentValue.toFixed(1)}{axis.unit}
              </text>
            </g>
          );
        })}

        {/* 红线标注 */}
        {axes.map((axis, i) => {
          const angle = i * angleStep;
          const [rx, ry] = polarToXY(angle, maxR * Math.min(axis.redLine / (axis.isInverse ? axis.redLine : 100), 1), cx, cy);
          return (
            <circle
              key={`redline-${i}`}
              cx={rx} cy={ry}
              r={2}
              fill="#ff2020"
              opacity={0.5}
            />
          );
        })}
      </svg>

      {/* 图例 */}
      <div style={{
        display: 'flex',
        gap: '12px',
        fontFamily: 'var(--font-mono)',
        fontSize: '9px',
        justifyContent: 'center',
      }}>
        <span style={{ color: '#ff2020' }}>◆ 红线以下</span>
        <span style={{ color: 'var(--cyan)' }}>◆ 安全区域</span>
      </div>
    </div>
  );
}
