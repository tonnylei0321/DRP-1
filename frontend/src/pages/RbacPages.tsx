/**
 * 9.3 用户组管理页 — 占位（API 待实现时展示友好提示）
 * 9.4 角色管理页 — 权限树配置
 */
import { useEffect, useState } from 'react';
import { rolesApi, Role } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card } from '../components/ui';

// ─── 用户组管理（占位） ─────────────────────────────────────────────────────

export function GroupsPage() {
  return (
    <div>
      <PageHeader title="用户组管理" />
      <Card>
        <EmptyState message="用户组功能开发中，请通过 API 直接管理" />
      </Card>
    </div>
  );
}

// ─── 角色管理 ──────────────────────────────────────────────────────────────

const ALL_PERMISSIONS = [
  'tenant:read', 'tenant:write', 'tenant:delete',
  'user:read', 'user:write', 'user:delete',
  'mapping:read', 'mapping:write', 'mapping:approve',
  'etl:read', 'etl:write',
  'drill:read',
  'audit:read',
];

export function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Role | null>(null);

  async function load() {
    setLoading(true);
    try {
      setRoles(await rolesApi.list());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleDeleteRole(id: string) {
    if (!confirm('确认删除该角色？')) return;
    try {
      await rolesApi.delete(id);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  return (
    <div>
      <PageHeader title="角色管理" />
      {error && <ErrorBox message={error} />}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* 角色列表 */}
        <Card>
          {loading ? <Spinner /> : roles.length === 0 ? <EmptyState message="暂无角色" /> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {roles.map(role => (
                <div key={role.id}
                  onClick={() => setSelected(role)}
                  style={{
                    padding: '12px', borderRadius: '8px', cursor: 'pointer',
                    background: selected?.id === role.id ? 'rgba(59,130,246,0.1)' : 'transparent',
                    border: `1px solid ${selected?.id === role.id ? 'var(--accent)' : 'var(--border)'}`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 500 }}>{role.name}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {role.description || '无描述'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <Badge label={`${role.permissions.length} 权限`} variant="info" />
                    <Btn variant="danger" size="sm" onClick={e => { e.stopPropagation(); handleDeleteRole(role.id); }}>
                      删除
                    </Btn>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* 权限树 */}
        <Card>
          {selected ? (
            <div>
              <div style={{ fontWeight: 600, marginBottom: '16px' }}>{selected.name} — 权限配置</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {ALL_PERMISSIONS.map(perm => (
                  <label key={perm} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      style={{ width: 'auto' }}
                      checked={selected.permissions.includes(perm)}
                      onChange={() => {
                        const perms = selected.permissions.includes(perm)
                          ? selected.permissions.filter(p => p !== perm)
                          : [...selected.permissions, perm];
                        setSelected({ ...selected, permissions: perms });
                      }}
                    />
                    <span style={{ fontFamily: 'monospace', fontSize: '13px' }}>{perm}</span>
                  </label>
                ))}
              </div>
              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
                <Btn onClick={async () => {
                  await rolesApi.update(selected.id, { permissions: selected.permissions });
                  load();
                }}>保存权限</Btn>
              </div>
            </div>
          ) : (
            <EmptyState message="请从左侧选择角色以配置权限" />
          )}
        </Card>
      </div>
    </div>
  );
}
