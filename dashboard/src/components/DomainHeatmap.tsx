/**
 * DomainHeatmap — 7域热力矩阵（横向单排）
 * CTIO 7大业务域合规率热力展示，点击钻取指标列表
 */

export interface DomainMetric {
  code: string;
  name: string;
  count: number;
  compliantCount: number;
  compliantRate: number; // 0-100
  riskLevel: 'critical' | 'warn' | 'info' | 'ok';
}

interface DomainHeatmapProps {
  domains: DomainMetric[];
  onDomainClick: (domain: DomainMetric) => void;
  selectedDomain: string | null;
}

function complianceColor(rate: number): string {
  if (rate >= 98) return 'rgba(0,255,179,0.9)';
  if (rate >= 95) return 'rgba(34,211,238,0.9)';
  if (rate >= 90) return 'rgba(255,170,0,0.9)';
  return 'rgba(255,32,32,0.9)';
}

const DOMAIN_ORDER = ['BA', 'CC', 'ST', 'BL', 'DF', 'DR', 'SA'];

export default function DomainHeatmap({ domains, onDomainClick, selectedDomain }: DomainHeatmapProps) {
  const domainMap = new Map(domains.map(d => [d.code, d]));

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '8px 10px',
      gap: '6px',
    }}>
      {/* 标题 */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '9px',
        color: 'var(--text-muted)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        flexShrink: 0,
      }}>
        集团7域合规热力
      </div>

      {/* 横向7域 */}
      <div style={{
        display: 'flex',
        flexDirection: 'row',
        gap: '6px',
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
      }}>
        {DOMAIN_ORDER.map(code => {
          const domain = domainMap.get(code);
          if (!domain) return null;

          const isSelected = selectedDomain === code;
          const color = complianceColor(domain.compliantRate);

          return (
            <div
              key={code}
              onClick={() => onDomainClick(domain)}
              style={{
                flex: 1,
                minWidth: 0,
                background: `${color}15`,
                border: `1px solid ${isSelected ? color : `${color}40`}`,
                borderRadius: '4px',
                padding: '6px 8px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s',
                boxShadow: isSelected ? `0 0 10px ${color}60` : 'none',
                position: 'relative',
              }}
            >
              {/* 风险指示点 */}
              <div style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                background: domain.riskLevel === 'critical' ? '#ff2020' : domain.riskLevel === 'warn' ? '#ffaa00' : domain.riskLevel === 'info' ? '#22d3ee' : '#00ffb3',
                boxShadow: `0 0 4px ${domain.riskLevel === 'critical' ? '#ff2020' : domain.riskLevel === 'warn' ? '#ffaa00' : '#22d3ee'}`,
              }} />

              {/* 域代码 */}
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '11px',
                fontWeight: 700,
                color: color,
                letterSpacing: '0.08em',
              }}>
                {code}
              </div>

              {/* 域名称 */}
              <div style={{
                fontFamily: 'var(--font-label)',
                fontSize: '9px',
                color: 'var(--text-muted)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {domain.name}
              </div>

              {/* 合规率（大数字） */}
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '16px',
                fontWeight: 900,
                color: color,
                lineHeight: 1,
                textShadow: `0 0 8px ${color}80`,
              }}>
                {domain.compliantRate.toFixed(1)}%
              </div>

              {/* 合规数 */}
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '8px',
                color: 'var(--text-muted)',
              }}>
                {domain.compliantCount}/{domain.count}
              </div>
            </div>
          );
        })}
      </div>

      {/* 色阶 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: '8px',
        color: 'var(--text-muted)',
        flexShrink: 0,
      }}>
        <span style={{ color: 'rgba(255,32,32,0.8)' }}>■ &lt;90%</span>
        <span style={{ color: 'rgba(255,170,0,0.85)' }}>■ 90-95%</span>
        <span style={{ color: 'rgba(34,211,238,0.8)' }}>■ 95-98%</span>
        <span style={{ color: 'rgba(0,255,179,0.85)' }}>■ ≥98%</span>
      </div>
    </div>
  );
}
