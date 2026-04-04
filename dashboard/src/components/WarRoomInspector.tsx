/**
 * WarRoomInspector — 右侧作战室审查器
 */
import type { EntityNode } from './EntityTree';

interface WarRoomInspectorProps {
  selectedNode: EntityNode | null;
}

const RISK_COLORS = {
  none: '#00ffb3',
  low: '#22d3ee',
  medium: '#ffaa00',
  high: '#ff2020',
};

export default function WarRoomInspector({ selectedNode }: WarRoomInspectorProps) {
  if (!selectedNode) {
    return (
      <div style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        flexDirection: 'column',
        gap: '12px',
      }}>
        <div style={{ fontSize: '32px', opacity: 0.3 }}>◇</div>
        <div>选择节点查看详情</div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto' }}>
      {/* 节点概览 */}
      <div className="panel" style={{ margin: '12px' }}>
        <div className="panel-header">节点详情</div>
        <div style={{ padding: '14px' }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '14px',
            color: 'var(--cyan)',
            marginBottom: '12px',
            textShadow: 'var(--cyan-glow)',
          }}>
            {selectedNode.name}
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
            <span className={`risk-badge ${selectedNode.risk}`}>
              {selectedNode.risk === 'none' ? '正常' : selectedNode.risk === 'low' ? '低风险' : selectedNode.risk === 'medium' ? '中风险' : '高风险'}
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)',
              background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '2px',
            }}>
              {selectedNode.type.toUpperCase()}
            </span>
          </div>

          <div className="hud-row">
            <span className="hud-label">节点 ID</span>
            <span className="hud-value" style={{ fontSize: '11px' }}>{selectedNode.id}</span>
          </div>

          {selectedNode.lat !== undefined && selectedNode.lon !== undefined && (
            <div className="hud-row">
              <span className="hud-label">坐标</span>
              <span className="hud-value" style={{ fontSize: '11px' }}>
                {selectedNode.lat.toFixed(4)}, {selectedNode.lon.toFixed(4)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 指标面板 */}
      <div className="panel" style={{ margin: '0 12px 12px' }}>
        <div className="panel-header">关键指标</div>
        <div style={{ padding: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {[
            { label: '归集率', value: '87.3%', risk: 'low' },
            { label: '资金穿透', value: '96.2%', risk: 'low' },
            { label: '合规率', value: '91.8%', risk: 'medium' },
            { label: '预警数', value: '3', risk: 'medium' },
          ].map(m => (
            <div key={m.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontFamily: 'var(--font-display)', fontWeight: 700, color: RISK_COLORS[m.risk as keyof typeof RISK_COLORS] }}>
                {m.value}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-label)' }}>
                {m.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 操作按钮 */}
      <div style={{ padding: '0 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button className="btn" style={{ width: '100%', justifyContent: 'center' }}>
          穿透溯源
        </button>
        <button className="btn btn-ghost" style={{ width: '100%', justifyContent: 'center' }}>
          查看历史
        </button>
        <button className="btn btn-ghost" style={{ width: '100%', justifyContent: 'center' }}>
          导出报告
        </button>
      </div>
    </div>
  );
}
