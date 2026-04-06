/**
 * 共享 UI 组件库 — 玻璃态深色主题
 * 支持：玻璃态卡片、渐变按钮、悬停动画、响应式布局
 */
import React from 'react';

// ─── Button — 渐变 + 悬停动画 ────────────────────────────────────────────────

interface BtnProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
}

export function Btn({ variant = 'primary', size = 'md', style, children, ...rest }: BtnProps) {
  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', gap: '6px',
    border: 'none', borderRadius: '8px', fontWeight: 600, fontFamily: 'inherit',
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    padding: size === 'sm' ? '5px 12px' : '9px 18px',
    fontSize: size === 'sm' ? '12px' : '13px',
    letterSpacing: '0.02em',
    cursor: 'pointer',
    ...(variant === 'primary' && {
      background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
      color: '#fff',
      boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
    }),
    ...(variant === 'danger' && {
      background: 'rgba(239,68,68,0.1)',
      color: 'var(--danger)',
      border: '1px solid rgba(239,68,68,0.3)',
      backdropFilter: 'blur(4px)',
    }),
    ...(variant === 'ghost' && {
      background: 'rgba(255,255,255,0.03)',
      color: 'var(--text-muted)',
      border: '1px solid rgba(255,255,255,0.08)',
      backdropFilter: 'blur(4px)',
    }),
    ...style,
  };
  return <button className={`btn btn-${variant}`} style={base} {...rest}>{children}</button>;
}

// ─── Card — 玻璃态 ──────────────────────────────────────────────────────────

export function Card({ children, style, hover = true }: {
  children: React.ReactNode;
  style?: React.CSSProperties;
  hover?: boolean;
}) {
  return (
    <div className={`card glass-card${hover ? ' hover-scale' : ''}`} style={{
      background: 'rgba(17, 24, 39, 0.6)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.3), 0 0 1px rgba(255, 255, 255, 0.05)',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      ...style,
    }}>
      {children}
    </div>
  );
}

// ─── PageHeader — 渐变标题 ──────────────────────────────────────────────────

export function PageHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      marginBottom: '24px', paddingBottom: '16px',
      borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    }}>
      <h2 style={{
        fontSize: '20px', fontWeight: 700, letterSpacing: '-0.01em',
        background: 'linear-gradient(135deg, #e5e7eb 0%, #9ca3af 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }}>{title}</h2>
      {action}
    </div>
  );
}

// ─── Badge — 微光效果 ───────────────────────────────────────────────────────

type BadgeVariant = 'success' | 'warn' | 'danger' | 'info';
export function Badge({ label, variant }: { label: string; variant: BadgeVariant }) {
  return <span className={`badge badge-${variant}`}>{label}</span>;
}

// ─── Input — 玻璃态输入框 ───────────────────────────────────────────────────

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}
export function Input({ label, style, ...rest }: InputProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label && <label style={{
        color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500,
        letterSpacing: '0.03em',
      }}>{label}</label>}
      <input style={{
        background: 'rgba(31, 41, 55, 0.8)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '8px',
        padding: '10px 14px',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        ...style,
      }} {...rest} />
    </div>
  );
}

// ─── Modal — 玻璃态弹窗 ────────────────────────────────────────────────────

export function Modal({ title, onClose, children }: {
  title: string; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999,
      animation: 'fadeIn 0.2s ease-out',
    }}>
      <div className="glass-card" style={{
        background: 'rgba(17, 24, 39, 0.9)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '28px',
        minWidth: '420px', maxWidth: '600px', width: '90%',
        boxShadow: '0 24px 48px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        animation: 'fadeIn 0.25s ease-out',
      }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: '20px', paddingBottom: '12px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        }}>
          <h3 style={{ color: 'var(--text)', fontSize: '16px', fontWeight: 600 }}>{title}</h3>
          <button onClick={onClose} style={{
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            color: 'var(--text-muted)', fontSize: '16px', cursor: 'pointer',
            width: '28px', height: '28px', borderRadius: '6px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s',
          }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── EmptyState ─────────────────────────────────────────────────────────────

export function EmptyState({ message }: { message: string }) {
  return (
    <div style={{
      textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)',
      background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px',
      border: '1px dashed rgba(255, 255, 255, 0.06)',
    }}>
      <div style={{ fontSize: '32px', marginBottom: '12px', opacity: 0.4 }}>📭</div>
      {message}
    </div>
  );
}

// ─── Spinner ────────────────────────────────────────────────────────────────

export function Spinner() {
  return (
    <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
      <div style={{
        width: '24px', height: '24px', margin: '0 auto 12px',
        border: '2px solid rgba(59, 130, 246, 0.2)',
        borderTopColor: 'var(--accent)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      加载中...
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ─── ErrorBox ───────────────────────────────────────────────────────────────

export function sanitizeErrorMessage(message: string): string {
  const sensitivePatterns = [
    /\/app\/src\/[^\s]+/g,
    /File "[^"]+", line \d+/g,
    /Traceback \(most recent/gi,
    /relation "[^"]+" does not exist/gi,
    /at [A-Z]\w+\.[a-z]\w+\s*\(/g,
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
      background: 'rgba(239,68,68,0.08)',
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(239,68,68,0.25)',
      borderRadius: '10px', padding: '12px 16px',
      color: 'var(--danger)', marginBottom: '16px',
      display: 'flex', alignItems: 'center', gap: '8px',
      fontSize: '13px',
    }}>
      <span style={{ fontSize: '16px' }}>⚠</span>
      {sanitizeErrorMessage(message)}
    </div>
  );
}
