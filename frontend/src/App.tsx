/**
 * 管理后台主应用 — 侧边栏导航 + 页面路由
 */
import { useState, useEffect, useRef } from 'react';
import { clearToken, getToken } from './api/client';
import LoginPage from './pages/LoginPage';
import UsersPage from './pages/UsersPage';
import { GroupsPage, RolesPage } from './pages/RbacPages';
import AuditPage from './pages/AuditPage';
import { DdlUploadPage, MappingsPage } from './pages/MappingPages';
import { EtlPage, TenantsPage, QualityPage } from './pages/AdminPages';
import Dashboard from './dashboard/Dashboard';

type Page =
  | 'users' | 'groups' | 'roles' | 'audit'
  | 'ddl' | 'mappings' | 'etl' | 'tenants' | 'quality'
  | 'dashboard';

const NAV_ITEMS: { id: Page; label: string; icon: string }[] = [
  { id: 'dashboard', label: '监管看板',        icon: '🖥️' },
  { id: 'users',    label: '用户管理',       icon: '👥' },
  { id: 'groups',   label: '用户组',          icon: '🗂️' },
  { id: 'roles',    label: '角色权限',        icon: '🔑' },
  { id: 'audit',    label: '审计日志',        icon: '📋' },
  { id: 'ddl',      label: 'DDL 上传',        icon: '⬆️' },
  { id: 'mappings', label: '映射审核',        icon: '🔀' },
  { id: 'etl',      label: 'ETL 监控',        icon: '⚙️' },
  { id: 'tenants',  label: '租户管理',        icon: '🏢' },
  { id: 'quality',  label: '数据质量',        icon: '📊' },
];

function PageContent({ page }: { page: Page }) {
  switch (page) {
    case 'dashboard': return <Dashboard />;
    case 'users':    return <UsersPage />;
    case 'groups':   return <GroupsPage />;
    case 'roles':    return <RolesPage />;
    case 'audit':    return <AuditPage />;
    case 'ddl':      return <DdlUploadPage />;
    case 'mappings': return <MappingsPage />;
    case 'etl':      return <EtlPage />;
    case 'tenants':  return <TenantsPage />;
    case 'quality':  return <QualityPage />;
  }
}

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());
  const [page, setPage] = useState<Page>('users');
  const savedPageRef = useRef<Page | null>(null);

  // 监听 401 auth-expired 事件，保存当前 page 并跳转登录页
  useEffect(() => {
    function handleAuthExpired() {
      savedPageRef.current = page;
      setAuthed(false);
    }
    window.addEventListener('drp-auth-expired', handleAuthExpired);
    return () => window.removeEventListener('drp-auth-expired', handleAuthExpired);
  }, [page]);

  function handleLogin() {
    setAuthed(true);
    if (savedPageRef.current) {
      setPage(savedPageRef.current);
      savedPageRef.current = null;
    }
  }

  if (!authed) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* 侧边栏 — 玻璃态 */}
      <aside style={{
        width: '240px', flexShrink: 0,
        background: 'rgba(17, 24, 39, 0.7)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          display: 'flex', alignItems: 'center', gap: '12px',
        }}>
          <div style={{
            width: '36px', height: '36px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: '14px',
            boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
          }}>DR</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text)' }}>DRP 管理后台</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>资金监管平台</div>
          </div>
        </div>

        {/* 导航 */}
        <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
          {NAV_ITEMS.map(item => {
            const isActive = page === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '9px 14px', borderRadius: '10px', border: 'none',
                  background: isActive
                    ? 'linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.1) 100%)'
                    : 'transparent',
                  color: isActive ? '#93c5fd' : 'var(--text-muted)',
                  fontSize: '13px', cursor: 'pointer', marginBottom: '2px',
                  transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                  fontWeight: isActive ? 600 : 400,
                  ...(isActive && {
                    boxShadow: '0 0 0 1px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255,255,255,0.05)',
                  }),
                }}
              >
                <span style={{ fontSize: '16px' }}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* 退出 */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <button
            onClick={() => { clearToken(); setAuthed(false); }}
            style={{
              width: '100%', padding: '9px 14px', borderRadius: '10px', border: 'none',
              background: 'transparent', color: 'var(--text-muted)', fontSize: '13px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '10px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '16px' }}>🚪</span><span>退出登录</span>
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main style={{
        flex: 1,
        padding: page === 'dashboard' ? '0' : '28px',
        overflowY: 'auto',
        background: 'transparent',
      }}>
        <PageContent page={page} />
      </main>
    </div>
  );
}
