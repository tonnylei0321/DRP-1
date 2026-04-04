/**
 * HUDPanel — HUD 风格弹窗，带动态连线指向地图点位
 */
import { useEffect, useRef, useState } from 'react';

export interface HUDNode {
  id: string;
  label: string;
  type: 'group' | 'region' | 'entity' | 'account';
  risk: 'none' | 'low' | 'medium' | 'high';
  properties: Record<string, string | number>;
  fiboClass?: string;
}

interface HUDPanelProps {
  node: HUDNode;
  dotPosition: [number, number]; // 地图上的像素坐标
  mapContainerRect: DOMRect;
  onClose: () => void;
}

const RISK_COLORS = {
  none: '#00ffb3',
  low: '#22d3ee',
  medium: '#ffaa00',
  high: '#ff2020',
};

const RISK_LABEL = { none: '正常', low: '低风险', medium: '中风险', high: '高风险' };

export default function HUDPanel({ node, dotPosition, mapContainerRect, onClose }: HUDPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [panelPos, setPanelPos] = useState({ x: 0, y: 0 });
  const [linePath, setLinePath] = useState('');

  // 计算弹窗位置和连线
  useEffect(() => {
    if (!panelRef.current) return;

    const panel = panelRef.current;
    const pw = panel.offsetWidth;
    const ph = panel.offsetHeight;

    // 目标位置（地图点位在容器中的坐标）
    const tx = dotPosition[0];
    const ty = dotPosition[1];

    // 计算面板位置（优先放右边，偏出边界则放左边）
    let px = tx + 20;
    let py = ty - ph / 2;

    // 右边界检测
    if (px + pw > mapContainerRect.width - 10) {
      px = tx - pw - 20;
    }

    // 上下边界检测
    if (py < 10) py = 10;
    if (py + ph > mapContainerRect.height - 10) py = mapContainerRect.height - ph - 10;

    setPanelPos({ x: px, y: py });

    // 连线：从面板左侧中点 → 点位
    const lineX1 = px;
    const lineY1 = py + ph / 2;
    const lineX2 = tx;
    const lineY2 = ty;

    // 贝塞尔曲线
    const cx = (lineX1 + lineX2) / 2;
    setLinePath(`M ${lineX1} ${lineY1} Q ${cx} ${lineY1}, ${cx} ${(lineY1 + lineY2) / 2} T ${lineX2} ${lineY2}`);
  }, [dotPosition, mapContainerRect]);

  return (
    <>
      {/* SVG 连线层 */}
      <svg style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 999,
      }}>
        <path
          d={linePath}
          className="hud-connector"
        />
        {/* 点位端点高亮 */}
        <circle
          cx={dotPosition[0]}
          cy={dotPosition[1]}
          r={6}
          fill={RISK_COLORS[node.risk]}
          style={{ filter: `drop-shadow(0 0 6px ${RISK_COLORS[node.risk]})` }}
        />
      </svg>

      {/* HUD 面板 */}
      <div
        ref={panelRef}
        className="hud-panel"
        style={{
          position: 'absolute',
          left: panelPos.x,
          top: panelPos.y,
        }}
      >
        <div className="hud-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '10px', height: '10px', borderRadius: '50%',
              background: RISK_COLORS[node.risk],
              boxShadow: `0 0 8px ${RISK_COLORS[node.risk]}`,
            }} />
            <span className="hud-title">{node.label}</span>
          </div>
          <button className="hud-close" onClick={onClose}>×</button>
        </div>

        <div className="hud-body">
          {/* 基础属性 */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
            <span className={`risk-badge ${node.risk}`}>{RISK_LABEL[node.risk]}</span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)',
              background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '2px',
            }}>
              {node.type.toUpperCase()}
            </span>
            {node.fiboClass && (
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--purple)',
                background: 'rgba(168,85,247,0.1)', padding: '2px 6px', borderRadius: '2px',
              }}>
                FIBO:{node.fiboClass}
              </span>
            )}
          </div>

          {/* 属性列表 */}
          {Object.entries(node.properties).map(([key, val]) => (
            <div key={key} className="hud-row">
              <span className="hud-label">{key}</span>
              <span className="hud-value">{String(val)}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
