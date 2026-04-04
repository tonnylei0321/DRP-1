/**
 * 大屏登录页 — 预填管理员账号
 */
import { useState } from 'react';
import { authApi, setToken } from '../api/client';

interface Props {
  onLogin: () => void;
}

export default function LoginPanel({ onLogin }: Props) {
  const [email] = useState('admin@drp.local');
  const [password] = useState('DrpAdmin123!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const resp = await authApi.login(email, password);
      setToken(resp.access_token);
      onLogin();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '登录失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: '#0a0e1a',
    }}>
      <div style={{
        background: '#111827', border: '1px solid #374151',
        borderRadius: '12px', padding: '40px', width: '380px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ color: '#3b82f6', fontSize: '28px', fontWeight: 700, letterSpacing: '0.1em' }}>
            DRP
          </div>
          <div style={{ color: '#6b7280', marginTop: '4px', fontSize: '14px' }}>
            监管大屏
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444',
            color: '#ef4444', padding: '10px', borderRadius: '6px',
            marginBottom: '16px', fontSize: '13px',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', color: '#6b7280', fontSize: '12px', marginBottom: '6px' }}>
              邮箱
            </label>
            <input
              type="email"
              value={email}
              readOnly
              style={{
                width: '100%', background: '#1f2937', border: '1px solid #374151',
                color: '#e5e7eb', borderRadius: '6px', padding: '10px 12px',
                fontSize: '14px', outline: 'none',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#6b7280', fontSize: '12px', marginBottom: '6px' }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              readOnly
              style={{
                width: '100%', background: '#1f2937', border: '1px solid #374151',
                color: '#e5e7eb', borderRadius: '6px', padding: '10px 12px',
                fontSize: '14px', outline: 'none',
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '12px', background: '#3b82f6',
              color: '#fff', border: 'none', borderRadius: '6px',
              fontSize: '14px', fontWeight: 600, cursor: 'pointer',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? '登录中...' : '进入大屏'}
          </button>
        </form>
      </div>
    </div>
  );
}
