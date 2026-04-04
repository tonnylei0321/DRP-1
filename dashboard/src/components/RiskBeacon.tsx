/**
 * RiskBeacon — 风险灯塔：纵向4柱，CRITICAL/WARN/INFO/OK
 * 点击联动地图和处置队列
 */
interface RiskBeaconProps {
  counts: { critical: number; warn: number; info: number; ok: number };
  onFilter: (level: 'critical' | 'warn' | 'info' | 'ok' | 'all') => void;
  activeFilter: 'critical' | 'warn' | 'info' | 'ok' | 'all';
}

const LEVELS = [
  { key: 'critical' as const, label: 'CRITICAL', color: '#ff2020', glow: '0 0 10px rgba(255,32,32,0.8)', desc: '立即处置' },
  { key: 'warn' as const, label: 'WARN', color: '#ffaa00', glow: '0 0 8px rgba(255,170,0,0.6)', desc: '限期整改' },
  { key: 'info' as const, label: 'INFO', color: '#22d3ee', glow: '0 0 6px rgba(34,211,238,0.5)', desc: '持续关注' },
  { key: 'ok' as const, label: 'OK', color: '#00ffb3', glow: '0 0 6px rgba(0,255,179,0.5)', desc: '正常' },
];

export default function RiskBeacon({ counts, onFilter, activeFilter }: RiskBeaconProps) {
  const maxCount = Math.max(counts.critical, counts.warn, counts.info, counts.ok, 1);
  const total = counts.critical + counts.warn + counts.info + counts.ok;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      height: '100%',
      padding: '16px 12px',
      gap: '12px',
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '10px',
        color: 'var(--text-muted)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}>
        风险态势
      </div>

      {/* 4色图例 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
        {LEVELS.map(l => (
          <div key={l.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: l.color,
              boxShadow: l.glow,
            }} />
            <span style={{ fontSize: '8px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {counts[l.key]}
            </span>
          </div>
        ))}
      </div>

      {/* 4根柱状图 */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        gap: '10px',
        width: '100%',
      }}>
        {LEVELS.map(l => {
          const count = counts[l.key];
          const heightPct = (count / maxCount) * 100;
          const isActive = activeFilter === l.key;

          return (
            <div
              key={l.key}
              onClick={() => onFilter(isActive ? 'all' : l.key)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                cursor: 'pointer',
                width: '36px',
              }}
            >
              {/* 柱 */}
              <div style={{
                width: '100%',
                height: `${Math.max(heightPct, 4)}%`,
                minHeight: '4px',
                background: isActive ? l.color : `${l.color}60`,
                boxShadow: isActive ? l.glow : 'none',
                borderRadius: '2px 2px 0 0',
                transition: 'all 0.3s ease',
                opacity: activeFilter !== 'all' && !isActive ? 0.3 : 1,
              }} />

              {/* 数量 */}
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '16px',
                fontWeight: 700,
                color: isActive ? l.color : 'var(--text-secondary)',
                textShadow: isActive ? l.glow : 'none',
                transition: 'all 0.2s',
              }}>
                {count}
              </div>

              {/* 标签 */}
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '8px',
                color: isActive ? l.color : 'var(--text-muted)',
                letterSpacing: '0.05em',
                opacity: isActive ? 1 : 0.6,
              }}>
                {l.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* 风险说明 */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '9px',
        color: 'var(--text-muted)',
        textAlign: 'center',
        lineHeight: 1.4,
      }}>
        <div style={{ color: '#ff2020' }}>● CRITICAL 立即处置</div>
        <div style={{ color: '#ffaa00' }}>● WARN 7天内整改</div>
        <div style={{ color: '#22d3ee' }}>● INFO 持续关注</div>
      </div>

      {/* 全局总计 */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '10px',
        color: 'var(--text-muted)',
        borderTop: '1px solid var(--border)',
        paddingTop: '8px',
        width: '100%',
        textAlign: 'center',
      }}>
        监控指标 <span style={{ color: 'var(--cyan)', fontFamily: 'var(--font-display)' }}>{total}</span> 项
      </div>
    </div>
  );
}
