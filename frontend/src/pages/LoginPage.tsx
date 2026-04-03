/**
 * 9.1 登录页 — 支持本地账号 + SSO 跳转
 */
import React, { useState } from 'react';
import { authApi, setToken } from '../api/client';
import { Btn, Input, ErrorBox } from '../components/ui';

interface Props {
  onLogin: () => void;
}

export default function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      setError(err instanceof Error ? err.message : '登录失败，请检查账号和密码');
    } finally {
      setLoading(false);
    }
  }

  const ssoBaseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: 'var(--bg)',
    }}>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: '12px', padding: '40px', width: '380px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ color: 'var(--accent)', fontSize: '28px', fontWeight: 700 }}>DRP</div>
          <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>穿透式资金监管平台</div>
        </div>

        {error && <ErrorBox message={error} />}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="邮箱"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="admin@example.com"
            required
          />
          <Input
            label="密码"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
          <Btn type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
            {loading ? '登录中...' : '登录'}
          </Btn>
        </form>

        <div style={{ marginTop: '20px', borderTop: '1px solid var(--border)', paddingTop: '20px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '10px', textAlign: 'center' }}>
            或通过 SSO 登录
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <Btn
              variant="ghost"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => window.location.href = `${ssoBaseUrl}/auth/saml/login`}
            >
              SAML 2.0 ���业SSO
            </Btn>
            <Btn
              variant="ghost"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => window.location.href = `${ssoBaseUrl}/auth/oidc/login`}
            >
              OIDC / OAuth2
            </Btn>
          </div>
        </div>
      </div>
    </div>
  );
}
