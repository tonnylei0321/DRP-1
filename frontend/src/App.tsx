/**
 * 管理后台主应用 — 侧边栏导航 + 页面路由
 */
import { useState, useEffect, useRef, useMemo } from 'react';
import { clearToken, getToken, getPermissions } from './api/client';
import { useTheme } from './hooks/useTheme';
import type { ThemeMode } from './hooks/useTheme';
import LoginPage from './pages/LoginPage';
import UsersPage from './pages/UsersPage';
import { GroupsPage, RolesPage } from './pages/RbacPages';
import AuditPage from './pages/AuditPage';
import { DdlUploadPage, MappingsPage } from './pages/MappingPages';
import { EtlPage, TenantsPage, QualityPage } from './pages/AdminPages';
import Dashboard from './dashboard/Dashboard';
import { DataScopeRulesPage, ColumnMaskRulesPage } from './pages/DataScopePages';

type Page =
  | 'users' | 'groups' | 'roles' | 'audit'
  | 'ddl' | 'mappings' | 'etl' | 'tenants' | 'quality'
  | 'dashboard'
  | 'data-scope-rules' | 'data-scope-masks';

const NAV_ITEMS: { id: Page; label: string; icon: string; requiredPermission: string }[] = [
  { id: 'dashboard', label: '监管看板',        icon: '🖥️', requiredPermission: 'drill:read' },
  { id: 'users',    label: '用户管理',       icon: '👥', requiredPermission: 'user:read' },
  { id: 'groups',   label: '用户组',          icon: '🗂️', requiredPermission: 'user:read' },
  { id: 'roles',    label: '角色权限',        icon: '🔑', requiredPermission: 'role:read' },
  { id: 'audit',    label: '审计日志',        icon: '📋', requiredPermission: 'audit:read' },
  { id: 'ddl',      label: 'DDL 上传',        icon: '⬆️', requiredPermission: 'mapping:read' },
  { id: 'mappings', label: '映射审核',        icon: '🔀', requiredPermission: 'mapping:read' },
  { id: 'etl',      label: 'ETL 监控',        icon: '⚙️', requiredPermission: 'etl:read' },
  { id: 'tenants',  label: '租户管理',        icon: '🏢', requiredPermission: 'tenant:read' },
  { id: 'quality',  label: '数据质量',        icon: '📊', requiredPermission: 'etl:read' },
  { id: 'data-scope-rules', label: '行级规则', icon: '🛡️', requiredPermission: 'data_scope:read' },
  { id: 'data-scope-masks', label: '列级规则', icon: '🔒', requiredPermission: 'data_scope:read' },
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
    case 'data-scope-rules': return <DataScopeRulesPage />;
    case 'data-scope-masks': return <ColumnMaskRulesPage />;
  }
}

/** 根据当前 token 计算可见菜单 */
function getVisibleNavItems(): typeof NAV_ITEMS {
  const perms = getPermissions();
  return NAV_ITEMS.filter(item =>
    perms === null || perms.includes(item.requiredPermission)
  );
}

/** 取第一个有权限的页面，兜底 'dashboard' */
function getDefaultPage(): Page {
  const visible = getVisibleNavItems();
  return visible.length > 0 ? visible[0].id : 'dashboard';
}

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());
  const [tokenVersion, setTokenVersion] = useState(0);
  const [page, setPage] = useState<Page>(() => getToken() ? getDefaultPage() : 'dashboard');
  const savedPageRef = useRef<Page | null>(null);
  const { mode, setMode } = useTheme();

  // 根据权限过滤可见菜单
  // null 表示 token 无 permissions 字段，显示全部向后兼容
  const visibleNavItems = useMemo(() => {
    if (!authed) return NAV_ITEMS;
    return getVisibleNavItems();
  }, [authed, tokenVersion]);

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
    // 先计算可见菜单和默认页面（此时 _token 已由 LoginPage setToken 设置）
    const visible = getVisibleNavItems();
    const defaultPage = visible.length > 0 ? visible[0].id : 'dashboard';

    if (savedPageRef.current) {
      // 401 恢复场景：跳回之前的页面
      const restored = savedPageRef.current;
      savedPageRef.current = null;
      // 如果恢复的页面不在可见列表中，回退到默认页面
      setPage(visible.some(v => v.id === restored) ? restored : defaultPage);
    } else {
      setPage(defaultPage);
    }

    // 最后更新 authed + tokenVersion，触发 useMemo 重新计算
    setTokenVersion(v => v + 1);
    setAuthed(true);
  }

  if (!authed) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <aside style={{
        width: '240px', flexShrink: 0,
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: '12px',
        }}>
          <div style={{
            width: '36px', height: '36px',
            background: 'var(--logo-gradient)',
            borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: '14px',
            boxShadow: 'var(--accent-shadow)',
          }}>DR</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text)' }}>DRP 管理后台</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>资金监管平台</div>
          </div>
        </div>

        {/* 导航 */}
        <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
          {visibleNavItems.length === 0 ? (
            <div style={{ padding: '16px 12px', color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center' }}>
              暂无可访问的功能模块，请联系管理员分配权限
            </div>
          ) : visibleNavItems.map(item => {
            const isActive = page === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`nav-item${isActive ? ' active' : ''}`}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '9px 14px', paddingLeft: '16px',
                  borderRadius: '8px', border: 'none',
                  background: isActive ? 'var(--bg-nav-active)' : 'transparent',
                  color: isActive ? 'var(--text)' : 'var(--text-muted)',
                  fontSize: '13px', cursor: 'pointer', marginBottom: '2px',
                  transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                <span style={{ fontSize: '16px', color: isActive ? 'var(--text-icon)' : 'var(--text-muted)' }}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* 退出 */}
        {/* 主题切换 + 退出 */}
        <div style={{ padding: '8px', borderTop: '1px solid var(--border)' }}>
          <div className="theme-switcher" style={{ marginBottom: '6px' }}>
            <button
              className={mode === 'light' ? 'active' : ''}
              onClick={() => setMode('light')}
              title="浅色模式"
              aria-label="浅色模式"
            >☀️</button>
            <button
              className={mode === 'dark' ? 'active' : ''}
              onClick={() => setMode('dark')}
              title="深色模式"
              aria-label="深色模式"
            >🌙</button>
            <button
              className={mode === 'system' ? 'active' : ''}
              onClick={() => setMode('system')}
              title="跟随系统"
              aria-label="跟随系统"
            >💻</button>
          </div>
          <button
            onClick={() => { clearToken(); setAuthed(false); }}
            style={{
              width: '100%', padding: '9px 14px', borderRadius: '8px', border: 'none',
              background: 'transparent', color: 'var(--text-muted)', fontSize: '13px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '10px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '16px', color: 'var(--text-icon)' }}>🚪</span><span>退出登录</span>
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
        {visibleNavItems.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>🔒</div>
              <div style={{ fontSize: '16px', marginBottom: '8px' }}>暂无访问权限</div>
              <div style={{ fontSize: '13px', marginBottom: '20px' }}>请联系管理员为您分配功能权限</div>
              <button
                onClick={() => { clearToken(); setAuthed(false); }}
                style={{
                  padding: '10px 24px', borderRadius: '10px', border: 'none',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  color: '#fff', fontSize: '14px', cursor: 'pointer', fontWeight: 500,
                }}
              >
                重新登录
              </button>
            </div>
          </div>
        ) : (
          <PageContent page={page} />
        )}
      </main>
    </div>
  );
}
