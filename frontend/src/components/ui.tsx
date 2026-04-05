/**
 * 共享 UI 组件库 — 按钮、卡片、表格、徽章等
 */
import React from 'react';

// ─── Button ──────────────────────────────────────��───────────────────────────

interface BtnProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
}

export function Btn({ variant = 'primary', size = 'md', style, children, ...rest }: BtnProps) {
  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', gap: '6px',
    border: 'none', borderRadius: '6px', fontWeight: 500, fontFamily: 'inherit',
    transition: 'background 0.15s',
    padding: size === 'sm' ? '4px 10px' : '8px 16px',
    fontSize: size === 'sm' ? '12px' : '14px',
    ...(variant === 'primary' && { background: 'var(--accent)', color: '#fff' }),
    ...(variant === 'danger' && { background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', border: '1px solid var(--danger)' }),
    ...(variant === 'ghost' && { background: 'transparent', color: 'var(--text-muted)', border: '1px solid var(--border)' }),
    ...style,
  };
  return <button className={`btn btn-${variant}`} style={base} {...rest}>{children}</button>;
}

// ─── Card ────────────────────────────────────────────────────────────────────

export function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div className="card" style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: '10px', padding: '20px', ...style,
    }}>
      {children}
    </div>
  );
}

// ─── PageHeader ───────────────────────────────────────────────���──────────────

export function PageHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
      <h2 style={{ color: 'var(--text)', fontSize: '18px', fontWeight: 600 }}>{title}</h2>
      {action}
    </div>
  );
}

// ─── Badge ───────────────────────────────────────────────────────────────────

type BadgeVariant = 'success' | 'warn' | 'danger' | 'info';
export function Badge({ label, variant }: { label: string; variant: BadgeVariant }) {
  return <span className={`badge badge-${variant}`}>{label}</span>;
}

// ─── Input ───────────────────────────────────────────────────���───────────────

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}
export function Input({ label, style, ...rest }: InputProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && <label style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{label}</label>}
      <input style={style} {...rest} />
    </div>
  );
}

// ─── Modal ───────────────────────────────────────────────────────────────────

export function Modal({ title, onClose, children }: {
  title: string; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999,
    }}>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: '12px', padding: '24px', minWidth: '400px', maxWidth: '600px', width: '90%',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ color: 'var(--text)', fontSize: '16px' }}>{title}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '18px', cursor: 'pointer' }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── EmptyState ──────────────────────────────────────────────────────────────

export function EmptyState({ message }: { message: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
      {message}
    </div>
  );
}

// ─── LoadingSpinner ──────────────────────────────────────────────────────────

export function Spinner() {
  return (
    <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
      加载中...
    </div>
  );
}

// ─── ErrorBox ────────────────────────────────────────────────────────────────

// 脱敏函数：过滤内部路径、SQL 关键字、堆栈跟踪
export function sanitizeErrorMessage(message: string): string {
  const sensitivePatterns = [
    /\/app\/src\/[^\s]+/g,           // 内部路径
    /File "[^"]+", line \d+/g,       // Python 文件路径
    /Traceback \(most recent/gi,     // Python 堆栈跟踪
    /relation "[^"]+" does not exist/gi, // PostgreSQL 错误
    /at [A-Z]\w+\.[a-z]\w+\s*\(/g,  // JS 堆栈跟踪
  ];

  for (const pattern of sensitivePatterns) {
    if (pattern.test(message)) {
      return '操作失败，请稍后重试或联系管理员';
    }
  }
  return message;
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div style={{
      background: 'rgba(239,68,68,0.1)', border: '1px solid var(--danger)',
      borderRadius: '8px', padding: '12px 16px', color: 'var(--danger)', marginBottom: '16px',
    }}>
      {sanitizeErrorMessage(message)}
    </div>
  );
}
