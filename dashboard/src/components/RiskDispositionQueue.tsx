/**
 * RiskDispositionQueue — 风险处置队列（横向卡片行，向上滚动播报）
 * CRITICAL 立即处置 / WARN 7天整改 / INFO 持续关注
 */
import { useEffect, useRef, useState } from 'react';

export type RiskLevel = 'CRITICAL' | 'WARN' | 'INFO';

export interface RiskEventItem {
  id: string;
  level: RiskLevel;
  entityName: string;
  indicatorId: string;
  indicatorName: string;
  currentValue: number;
  threshold: number;
  unit: string;
  triggeredAt: string;
  status: 'pending' | 'in_progress' | 'resolved';
  deadline?: string;
}

interface RiskDispositionQueueProps {
  events: RiskEventItem[];
  onEventClick: (event: RiskEventItem) => void;
  filter: 'all' | RiskLevel;
  onFilterChange: (f: 'all' | RiskLevel) => void;
}

const LEVEL_CONFIG = {
  CRITICAL: { color: '#ff2020', bg: 'rgba(255,32,32,0.12)', border: 'rgba(255,32,32,0.4)', label: '立即处置' },
  WARN: { color: '#ffaa00', bg: 'rgba(255,170,0,0.10)', border: 'rgba(255,170,0,0.35)', label: '7天整改' },
  INFO: { color: '#22d3ee', bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.25)', label: '持续关注' },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return `${Math.floor(hours / 24)}天前`;
}

function DispositionCard({ event, onClick }: { event: RiskEventItem; onClick: () => void }) {
  const cfg = LEVEL_CONFIG[event.level];

  return (
    <div
      onClick={onClick}
      style={{
        flexShrink: 0,
        width: '180px',
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        borderRadius: '3px',
        padding: '5px 8px',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
      }}
    >
      {/* 头部：级别标签 + 企业名 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{
            background: `${cfg.color}25`,
            border: `1px solid ${cfg.color}`,
            color: cfg.color,
            fontFamily: 'var(--font-mono)',
            fontSize: '7px',
            fontWeight: 700,
            padding: '0px 3px',
            borderRadius: '2px',
          }}>
            {event.level}
          </span>
          <span style={{
            fontFamily: 'var(--font-label)',
            fontSize: '10px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: '90px',
          }}>
            {event.entityName}
          </span>
        </div>
        <div style={{
          width: '5px', height: '5px', borderRadius: '50%',
          background: cfg.color,
          boxShadow: `0 0 4px ${cfg.color}`,
          flexShrink: 0,
        }} />
      </div>

      {/* 指标 */}
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '8px',
        color: 'var(--text-secondary)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        <span style={{ color: 'var(--cyan)', marginRight: '2px' }}>{event.indicatorId}</span>
        {event.indicatorName}
      </div>

      {/* 数值 */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px' }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '12px',
          fontWeight: 700,
          color: cfg.color,
        }}>
          {event.currentValue.toFixed(1)}{event.unit}
        </span>
        <span style={{ color: 'var(--text-muted)', fontSize: '7px', fontFamily: 'var(--font-mono)' }}>
          /{event.threshold.toFixed(1)}
        </span>
      </div>

      {/* 底部：状态 + 时间 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: '7px',
        color: 'var(--text-muted)',
      }}>
        <span style={{ color: cfg.color }}>
          {event.level === 'WARN' && event.deadline ? event.deadline : cfg.label}
        </span>
        <span>{timeAgo(event.triggeredAt)}</span>
      </div>
    </div>
  );
}

export default function RiskDispositionQueue({ events, onEventClick, filter, onFilterChange }: RiskDispositionQueueProps) {
  const filtered = filter === 'all' ? events : events.filter(e => e.level === filter);
  const critCount = events.filter(e => e.level === 'CRITICAL').length;
  const warnCount = events.filter(e => e.level === 'WARN').length;
  const infoCount = events.filter(e => e.level === 'INFO').length;
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = useState(false);

  // 向上滚动（从下往上）
  useEffect(() => {
    if (isPaused) return;
    const el = scrollRef.current;
    if (!el) return;
    const id = setInterval(() => {
      el.scrollTop += 1;
      if (el.scrollTop >= el.scrollHeight - el.clientHeight) {
        el.scrollTop = 0;
      }
    }, 40);
    return () => clearInterval(id);
  }, [isPaused, filtered.length]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '6px 10px',
      gap: '4px',
      overflow: 'hidden',
    }}>
      {/* 标题 + 过滤器 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '9px',
          color: 'var(--text-muted)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}>
          风险处置
        </div>
        <div style={{ display: 'flex', gap: '2px' }}>
          {(['all', 'CRITICAL', 'WARN', 'INFO'] as const).map(f => {
            const count = f === 'all' ? events.length : f === 'CRITICAL' ? critCount : f === 'WARN' ? warnCount : infoCount;
            const isActive = filter === f;
            return (
              <button
                key={f}
                onClick={() => onFilterChange(f)}
                style={{
                  background: isActive ? 'rgba(0,216,255,0.15)' : 'transparent',
                  border: `1px solid ${isActive ? 'var(--cyan)' : 'var(--border)'}`,
                  color: isActive ? 'var(--cyan)' : 'var(--text-muted)',
                  borderRadius: '2px',
                  padding: '1px 5px',
                  fontSize: '8px',
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer',
                }}
              >
                {f === 'all' ? '全部' : f} {count > 0 && `(${count})`}
              </button>
            );
          })}
        </div>
      </div>

      {/* 横向卡片列表（向上滚动） */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
          overflowY: 'auto',
          scrollbarWidth: 'none',
        }}
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        {filtered.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '10px',
          }}>
            暂无风险事件
          </div>
        ) : (
          filtered.map(event => (
            <DispositionCard
              key={event.id}
              event={event}
              onClick={() => onEventClick(event)}
            />
          ))
        )}
      </div>
    </div>
  );
}
