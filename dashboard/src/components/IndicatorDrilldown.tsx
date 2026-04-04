/**
 * IndicatorDrilldown — 指标钻取面板
 * 从热力矩阵点击域后展开，显示该域下所有指标
 */
import type { DomainMetric } from './DomainHeatmap';

export interface DomainIndicator {
  code: string;
  name: string;
  currentValue: number;
  targetValue: number;
  redLine: number;  // 红线阈值
  warnLine: number; // 预警阈值
  unit: string;
  status: 'ok' | 'warn' | 'critical';
}

interface IndicatorDrilldownProps {
  domain: DomainMetric | null;
  indicators: DomainIndicator[];
  onClose: () => void;
  onIndicatorClick?: (indicator: DomainIndicator) => void;
}

function statusColor(status: DomainIndicator['status']): string {
  if (status === 'critical') return '#ff2020';
  if (status === 'warn') return '#ffaa00';
  return '#00ffb3';
}

export default function IndicatorDrilldown({ domain, indicators, onClose, onIndicatorClick }: IndicatorDrilldownProps) {
  if (!domain) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 500,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'rgba(2, 8, 16, 0.85)',
      backdropFilter: 'blur(4px)',
    }}
    onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* 居中卡片 */}
      <div style={{
        width: '460px',
        maxHeight: '70vh',
        background: 'rgba(5, 13, 24, 0.98)',
        border: '1px solid rgba(0, 216, 255, 0.4)',
        borderRadius: '6px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 0 40px rgba(0, 0, 0, 0.9), 0 0 20px rgba(0, 216, 255, 0.1)',
      }}>
      {/* 头部 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(0, 216, 255, 0.05)',
      }}>
        <div>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '14px',
            fontWeight: 700,
            color: 'var(--cyan)',
          }}>
            {domain.code} — {domain.name}
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '10px',
            color: 'var(--text-muted)',
            marginTop: '2px',
          }}>
            {indicators.length} 项指标 · 合规率 {domain.compliantRate.toFixed(1)}%
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-muted)',
            borderRadius: '4px',
            padding: '4px 10px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
          }}
        >
          关闭
        </button>
      </div>

      {/* 指标列表 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {indicators.map(ind => (
          <div
            key={ind.code}
            onClick={() => onIndicatorClick?.(ind)}
            style={{
              background: `${statusColor(ind.status)}10`,
              border: `1px solid ${statusColor(ind.status)}40`,
              borderRadius: '4px',
              padding: '10px 12px',
              cursor: onIndicatorClick ? 'pointer' : 'default',
              transition: 'all 0.2s',
            }}
          >
            {/* 指标编号和名称 */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '6px',
            }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
                color: 'var(--cyan)',
              }}>
                {ind.code}
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
                padding: '1px 5px',
                borderRadius: '2px',
                background: `${statusColor(ind.status)}20`,
                color: statusColor(ind.status),
                border: `1px solid ${statusColor(ind.status)}50`,
              }}>
                {ind.status === 'critical' ? '红线' : ind.status === 'warn' ? '预警' : '正常'}
              </span>
            </div>
            <div style={{
              fontFamily: 'var(--font-label)',
              fontSize: '12px',
              color: 'var(--text-primary)',
              marginBottom: '8px',
            }}>
              {ind.name}
            </div>

            {/* 数值进度 */}
            <div style={{ marginBottom: '6px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
                color: 'var(--text-muted)',
                marginBottom: '3px',
              }}>
                <span>当前值</span>
                <span>目标值 / 红线</span>
              </div>
              <div style={{
                height: '4px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '2px',
                position: 'relative',
              }}>
                {/* 目标线标记 */}
                <div style={{
                  position: 'absolute',
                  left: `${Math.min((ind.targetValue / (ind.redLine * 1.5)) * 100, 100)}%`,
                  top: '-2px',
                  width: '1px',
                  height: '8px',
                  background: 'var(--cyan)',
                  opacity: 0.6,
                }} />
                <div style={{
                  width: `${Math.min((ind.currentValue / (ind.redLine * 1.5)) * 100, 100)}%`,
                  height: '100%',
                  background: statusColor(ind.status),
                  borderRadius: '2px',
                  transition: 'width 0.5s ease',
                  boxShadow: `0 0 6px ${statusColor(ind.status)}60`,
                }} />
              </div>
            </div>

            {/* 数值显示 */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: 'var(--font-display)',
              fontSize: '13px',
              fontWeight: 700,
            }}>
              <span style={{ color: statusColor(ind.status) }}>
                {ind.currentValue.toFixed(2)}{ind.unit}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: 400 }}>
                目标 {ind.targetValue.toFixed(1)}{ind.unit} / 红线 {ind.redLine.toFixed(1)}{ind.unit}
              </span>
            </div>
          </div>
        ))}
      </div>
      </div>
    </div>
  );
}
