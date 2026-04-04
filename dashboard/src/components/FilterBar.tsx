/**
 * FilterBar — 风险等级过滤栏
 */
import type { RiskLevel } from './EntityTree';

interface FilterBarProps {
  active: RiskLevel;
  onChange: (risk: RiskLevel) => void;
}

const OPTIONS: { value: RiskLevel; label: string; color: string }[] = [
  { value: 'all', label: '全部', color: 'var(--text-secondary)' },
  { value: 'high', label: '高风险', color: 'var(--risk-high)' },
  { value: 'medium', label: '中风险', color: 'var(--risk-medium)' },
  { value: 'low', label: '低风险', color: 'var(--risk-low)' },
  { value: 'none', label: '正常', color: 'var(--risk-none)' },
];

export default function FilterBar({ active, onChange }: FilterBarProps) {
  return (
    <div style={{
      display: 'flex',
      gap: '4px',
      padding: '8px 10px',
      borderBottom: '1px solid var(--border)',
    }}>
      {OPTIONS.map(opt => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          style={{
            background: active === opt.value ? `${opt.color}20` : 'transparent',
            border: `1px solid ${active === opt.value ? opt.color : 'var(--border)'}`,
            color: active === opt.value ? opt.color : 'var(--text-muted)',
            borderRadius: '3px',
            padding: '3px 8px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
