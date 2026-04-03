/**
 * 10.6 HUD 浮窗组件 — 节点详情卡 + 连接线 + 角框装饰
 * 10.8 底部 Ticker 组件 — 风险事件滚动播报
 * 10.9 右侧检查器面板 — 三级穿透路径展示
 * 10.10 图层过滤器
 */
import React from 'react';
import type { Lang } from './i18n';
import { t } from './i18n';
import type { RiskEvent } from './useRiskEvents';

// ─── HUD 浮窗 — 10.6 ─────────────────────────────────────────────────────────

export interface HudNode {
  id: string;
  label: string;
  type: string;
  risk: string;
  properties: Record<string, string | number | boolean | null>;
}

interface HudProps {
  node: HudNode | null;
  lang: Lang;
  onClose: () => void;
  onDrillDown?: (id: string) => void;
}

export function HudPanel({ node, lang, onClose, onDrillDown }: HudProps) {
  if (!node) return null;

  const riskColor = {
    none: 'var(--accent)', low: 'var(--success)',
    medium: 'var(--warn)', high: 'var(--danger)',
  }[node.risk] ?? 'var(--text)';

  const cornerStyle: React.CSSProperties = {
    position: 'absolute', width: '12px', height: '12px',
    borderColor: 'var(--accent)', borderStyle: 'solid',
  };

  return (
    <div style={{
      position: 'relative',
      background: 'rgba(10,14,26,0.92)',
      border: `1px solid ${riskColor}`,
      borderRadius: '8px', padding: '16px',
      minWidth: '240px', backdropFilter: 'blur(8px)',
    }}>
      {/* 角框装饰 */}
      <div style={{ ...cornerStyle, top: -1, left: -1, borderWidth: '2px 0 0 2px', borderTopLeftRadius: '8px' }} />
      <div style={{ ...cornerStyle, top: -1, right: -1, borderWidth: '2px 2px 0 0', borderTopRightRadius: '8px' }} />
      <div style={{ ...cornerStyle, bottom: -1, left: -1, borderWidth: '0 0 2px 2px', borderBottomLeftRadius: '8px' }} />
      <div style={{ ...cornerStyle, bottom: -1, right: -1, borderWidth: '0 2px 2px 0', borderBottomRightRadius: '8px' }} />

      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            {t(lang, node.type.toLowerCase()) || node.type}
          </div>
          <div style={{ fontWeight: 600, color: riskColor }}>{node.label}</div>
        </div>
        <button onClick={onClose}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '16px' }}>
          ×
        </button>
      </div>

      {/* 属性列表 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {Object.entries(node.properties).map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{k}</span>
            <span style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text)' }}>
              {v !== null && v !== undefined ? String(v) : '—'}
            </span>
          </div>
        ))}
      </div>

      {/* 穿透按钮 */}
      {onDrillDown && (
        <button
          onClick={() => onDrillDown(node.id)}
          style={{
            marginTop: '12px', width: '100%', padding: '6px', border: `1px solid ${riskColor}`,
            background: 'transparent', color: riskColor, borderRadius: '4px',
            fontSize: '12px', cursor: 'pointer',
          }}
        >
          {t(lang, 'drillDown')} →
        </button>
      )}
    </div>
  );
}

// ─── Ticker — 10.8 ────────────────────────────────────────────────────────────

interface TickerProps {
  events: RiskEvent[];
  lang: Lang;
}

export function RiskTicker({ events, lang }: TickerProps) {
  if (events.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
      background: 'rgba(10,14,26,0.95)', borderTop: '1px solid var(--border)',
      padding: '6px 20px', display: 'flex', alignItems: 'center', gap: '16px',
      overflow: 'hidden',
    }}>
      <div style={{ flexShrink: 0, color: 'var(--danger)', fontWeight: 700, fontSize: '11px' }}>
        ⚠ {t(lang, 'riskEvents').toUpperCase()}
      </div>
      <div style={{
        flex: 1, overflow: 'hidden',
        display: 'flex', gap: '32px',
        animation: 'ticker-scroll 20s linear infinite',
      }}>
        {events.slice(0, 10).map((e, i) => (
          <span key={i} style={{ flexShrink: 0, fontSize: '12px', color: 'var(--warn)', whiteSpace: 'nowrap' }}>
            [{e.domain}] {e.indicator_name} = {e.value?.toFixed(2) ?? '—'}
            {e.threshold != null && ` (阈值: ${e.threshold})`}
          </span>
        ))}
      </div>
      <style>{`
        @keyframes ticker-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}

// ─── 右侧检查器 — 10.9 ───────────────────────────────────────────────────────

interface InspectorProps {
  drillPath: Array<{ step: number; node_iri: string; node_type: string; node_label: string | null }>;
  lang: Lang;
}

export function DrillInspector({ drillPath, lang }: InspectorProps) {
  const icons: Record<string, string> = {
    RegulatoryIndicator: '📊', LegalEntity: '🏢', Account: '💳',
  };

  return (
    <div style={{
      width: '260px', flexShrink: 0,
      background: 'rgba(17,24,39,0.9)', borderLeft: '1px solid var(--border)',
      padding: '16px', overflowY: 'auto',
    }}>
      <div style={{ fontWeight: 600, marginBottom: '16px', fontSize: '13px', color: 'var(--accent)' }}>
        穿透路径
      </div>
      {drillPath.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{t(lang, 'noData')}</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {drillPath.map((node, idx) => (
            <React.Fragment key={node.node_iri}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: '10px',
                padding: '10px', borderRadius: '6px', background: 'rgba(59,130,246,0.05)',
                border: '1px solid rgba(59,130,246,0.15)',
              }}>
                <div style={{ fontSize: '16px', marginTop: '2px' }}>
                  {icons[node.node_type] ?? '🔷'}
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Step {node.step} · {node.node_type}
                  </div>
                  <div style={{ fontSize: '13px', wordBreak: 'break-all' }}>
                    {node.node_label || node.node_iri?.split(':').pop() || '—'}
                  </div>
                </div>
              </div>
              {idx < drillPath.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4px', color: 'var(--text-muted)' }}>
                  ↓
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── 图层过滤器 — 10.10 ──────────────────────────────────────────────────────

export type LayerFilter = 'all' | 'cashflow' | 'accounts' | 'violations';

interface LayerFilterProps {
  active: LayerFilter;
  lang: Lang;
  onChange: (layer: LayerFilter) => void;
}

export function LayerFilterBar({ active, lang, onChange }: LayerFilterProps) {
  const layers: { id: LayerFilter; labelKey: string }[] = [
    { id: 'all',        labelKey: 'allLayers' },
    { id: 'cashflow',   labelKey: 'cashFlow' },
    { id: 'accounts',  labelKey: 'accounts' },
    { id: 'violations', labelKey: 'violations' },
  ];

  return (
    <div style={{ display: 'flex', gap: '6px' }}>
      {layers.map(l => (
        <button
          key={l.id}
          onClick={() => onChange(l.id)}
          style={{
            padding: '5px 12px', borderRadius: '20px', border: 'none',
            background: active === l.id ? 'var(--accent)' : 'rgba(255,255,255,0.05)',
            color: active === l.id ? '#fff' : 'var(--text-muted)',
            fontSize: '12px', cursor: 'pointer',
          }}
        >
          {t(lang, l.labelKey)}
        </button>
      ))}
    </div>
  );
}
