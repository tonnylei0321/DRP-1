/**
 * 9.3 用户组管理页 — 占位（API 待实现时展示友好提示）
 * 9.4 角色管理页 — 权限树配置
 */
import React, { useEffect, useState } from 'react';
import { rolesApi } from '../api/client';
import type { Role } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card, Modal, Input } from '../components/ui';

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

/** 权限按菜单分组定义 */
const PERMISSION_GROUPS = [
  {
    menu: '监管看板',
    icon: '🖥️',
    permissions: [
      { key: 'drill:read', label: '查看看板' },
    ],
  },
  {
    menu: '用户管理',
    icon: '👥',
    permissions: [
      { key: 'user:read', label: '查看用户' },
      { key: 'user:write', label: '编辑用户' },
      { key: 'user:delete', label: '删除用户' },
    ],
  },
  {
    menu: '角色权限',
    icon: '🔑',
    permissions: [
      { key: 'user:read', label: '查看角色' },
      { key: 'user:write', label: '编辑角色' },
    ],
  },
  {
    menu: '审计日志',
    icon: '📋',
    permissions: [
      { key: 'audit:read', label: '查看日志' },
    ],
  },
  {
    menu: 'DDL 上传',
    icon: '⬆️',
    permissions: [
      { key: 'mapping:read', label: '查看映射' },
      { key: 'mapping:write', label: '上传 DDL' },
    ],
  },
  {
    menu: '映射审核',
    icon: '🔀',
    permissions: [
      { key: 'mapping:read', label: '查看映射' },
      { key: 'mapping:approve', label: '审核映射' },
    ],
  },
  {
    menu: 'ETL 监控',
    icon: '⚙️',
    permissions: [
      { key: 'etl:read', label: '查看任务' },
      { key: 'etl:write', label: '触发同步' },
    ],
  },
  {
    menu: '租户管理',
    icon: '🏢',
    permissions: [
      { key: 'tenant:read', label: '查看租户' },
      { key: 'tenant:write', label: '编辑租户' },
      { key: 'tenant:delete', label: '删除租户' },
    ],
  },
  {
    menu: '数据质量',
    icon: '📊',
    permissions: [
      { key: 'etl:read', label: '查看质量' },
    ],
  },
];

export function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Role | null>(null);
  const [deleteRoleTarget, setDeleteRoleTarget] = useState<string | null>(null);

  // 搜索
  const [search, setSearch] = useState('');

  // 新建角色
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '' });
  const [createSaving, setCreateSaving] = useState(false);

  // 编辑角色
  const [editTarget, setEditTarget] = useState<Role | null>(null);
  const [editForm, setEditForm] = useState({ name: '', description: '' });
  const [editSaving, setEditSaving] = useState(false);

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

  async function handleDeleteConfirm() {
    if (!deleteRoleTarget) return;
    try {
      await rolesApi.delete(deleteRoleTarget);
      setDeleteRoleTarget(null);
      if (selected?.id === deleteRoleTarget) setSelected(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCreateSaving(true);
    try {
      await rolesApi.create({ name: createForm.name, description: createForm.description, permissions: [] });
      setShowCreate(false);
      setCreateForm({ name: '', description: '' });
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败');
    } finally {
      setCreateSaving(false);
    }
  }

  function openEdit(role: Role) {
    setEditTarget(role);
    setEditForm({ name: role.name, description: role.description || '' });
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editTarget) return;
    setEditSaving(true);
    try {
      await rolesApi.update(editTarget.id, { name: editForm.name, description: editForm.description });
      setEditTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '编辑失败');
    } finally {
      setEditSaving(false);
    }
  }

  // 前端过滤
  const filteredRoles = roles.filter(r => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return r.name.toLowerCase().includes(q) || (r.description || '').toLowerCase().includes(q);
  });

  return (
    <div>
      <PageHeader
        title="角色管理"
        action={<Btn onClick={() => setShowCreate(true)}>+ 新建角色</Btn>}
      />
      {error && <ErrorBox message={error} />}

      {/* 搜索框 */}
      <div style={{ marginBottom: '16px' }}>
        <Input
          placeholder="搜索角色名称或描述..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* 角色列表 */}
        <Card>
          {loading ? <Spinner /> : filteredRoles.length === 0 ? <EmptyState message="暂无角色" /> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredRoles.map(role => (
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
                    <Btn variant="ghost" size="sm" onClick={e => { e.stopPropagation(); openEdit(role); }}>
                      编辑
                    </Btn>
                    <Btn variant="danger" size="sm" onClick={e => { e.stopPropagation(); setDeleteRoleTarget(role.id); }}>
                      删除
                    </Btn>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* 权限树 — 按菜单分组 */}
        <Card>
          {selected ? (
            <div>
              <div style={{ fontWeight: 600, marginBottom: '16px' }}>{selected.name} — 权限配置</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {PERMISSION_GROUPS.map((group, gi) => {
                  // 该组所有唯一权限 key
                  const groupKeys = [...new Set(group.permissions.map(p => p.key))];
                  const allChecked = groupKeys.every(k => selected.permissions.includes(k));
                  const someChecked = !allChecked && groupKeys.some(k => selected.permissions.includes(k));

                  return (
                    <div key={group.menu + gi}>
                      {/* 分组标题 — 可点击全选/全不选 */}
                      <div
                        onClick={() => {
                          if (allChecked) {
                            // 全不选：移除该组所有权限
                            const perms = selected.permissions.filter(p => !groupKeys.includes(p));
                            setSelected({ ...selected, permissions: perms });
                          } else {
                            // 全选：添加该组缺失的权限
                            const perms = [...new Set([...selected.permissions, ...groupKeys])];
                            setSelected({ ...selected, permissions: perms });
                          }
                        }}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '8px',
                          padding: '8px 10px', borderRadius: '8px', cursor: 'pointer',
                          background: 'rgba(255,255,255,0.03)',
                          transition: 'background 0.2s',
                        }}
                      >
                        <input
                          type="checkbox"
                          style={{ width: 'auto', accentColor: 'var(--accent)' }}
                          checked={allChecked}
                          ref={el => { if (el) el.indeterminate = someChecked; }}
                          readOnly
                        />
                        <span style={{ fontSize: '15px' }}>{group.icon}</span>
                        <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text)' }}>
                          {group.menu}
                        </span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginLeft: 'auto' }}>
                          {groupKeys.filter(k => selected.permissions.includes(k)).length}/{groupKeys.length}
                        </span>
                      </div>

                      {/* 该组的功能权限列表 */}
                      <div style={{ paddingLeft: '36px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {group.permissions.map((perm, pi) => (
                          <label
                            key={`${group.menu}-${perm.key}-${pi}`}
                            style={{
                              display: 'flex', alignItems: 'center', gap: '8px',
                              padding: '5px 10px', borderRadius: '6px', cursor: 'pointer',
                              transition: 'background 0.15s',
                            }}
                          >
                            <input
                              type="checkbox"
                              style={{ width: 'auto', accentColor: 'var(--accent)' }}
                              checked={selected.permissions.includes(perm.key)}
                              onChange={() => {
                                const perms = selected.permissions.includes(perm.key)
                                  ? selected.permissions.filter(p => p !== perm.key)
                                  : [...selected.permissions, perm.key];
                                setSelected({ ...selected, permissions: perms });
                              }}
                            />
                            <span style={{ fontSize: '13px', color: 'var(--text)' }}>{perm.label}</span>
                            <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)' }}>
                              {perm.key}
                            </span>
                          </label>
                        ))}
                      </div>

                      {/* 分隔线（最后一组不加） */}
                      {gi < PERMISSION_GROUPS.length - 1 && (
                        <div style={{
                          height: '1px', background: 'rgba(255,255,255,0.06)',
                          margin: '6px 0',
                        }} />
                      )}
                    </div>
                  );
                })}
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

      {/* 新建角色 Modal */}
      {showCreate && (
        <Modal title="新建角色" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="角色名称*" required value={createForm.name}
              onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))} />
            <Input label="描述" value={createForm.description}
              onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))} />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setShowCreate(false)}>取消</Btn>
              <Btn type="submit" disabled={createSaving}>{createSaving ? '保存中...' : '创建'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 编辑角色 Modal */}
      {editTarget && (
        <Modal title="编辑角色" onClose={() => setEditTarget(null)}>
          <form onSubmit={handleEditSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="角色名称*" required value={editForm.name}
              onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} />
            <Input label="描述" value={editForm.description}
              onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setEditTarget(null)}>取消</Btn>
              <Btn type="submit" disabled={editSaving}>{editSaving ? '保存中...' : '保存'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 删除确认 Modal */}
      {deleteRoleTarget && (
        <Modal title="确认删除" onClose={() => setDeleteRoleTarget(null)}>
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>确认删除该角色？此操作不可撤销。</p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Btn variant="ghost" type="button" onClick={() => setDeleteRoleTarget(null)}>取消</Btn>
            <Btn variant="danger" onClick={handleDeleteConfirm}>确认删除</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}
