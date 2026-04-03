/**
 * 管理后台主应用 — 侧边栏导航 + 页面路由
 */
import { useState } from 'react';
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

  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <aside style={{
        width: '220px', flexShrink: 0,
        background: 'var(--bg-card)', borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <div style={{
            width: '32px', height: '32px', background: 'var(--accent)', borderRadius: '8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: '14px',
          }}>DR</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px' }}>DRP 管理后台</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>资金监管平台</div>
          </div>
        </div>

        {/* 导航 */}
        <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                padding: '8px 12px', borderRadius: '8px', border: 'none',
                background: page === item.id ? 'rgba(59,130,246,0.15)' : 'transparent',
                color: page === item.id ? 'var(--accent)' : 'var(--text-muted)',
                fontSize: '13px', cursor: 'pointer', marginBottom: '2px',
                transition: 'background 0.15s',
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* 退出 */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid var(--border)' }}>
          <button
            onClick={() => { clearToken(); setAuthed(false); }}
            style={{
              width: '100%', padding: '8px 12px', borderRadius: '8px', border: 'none',
              background: 'transparent', color: 'var(--text-muted)', fontSize: '13px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '10px',
            }}
          >
            <span>🚪</span><span>退出登录</span>
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <main style={{ flex: 1, padding: page === 'dashboard' ? '0' : '28px', overflowY: 'auto' }}>
        <PageContent page={page} />
      </main>
    </div>
  );
}
