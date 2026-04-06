/**
 * 9.2 用户管理页 — 增删改查、角色分配
 */
import React, { useEffect, useState } from 'react';
import { usersApi, rolesApi } from '../api/client';
import type { UserItem, Role } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Modal, Input } from '../components/ui';

export default function UsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  // 编辑用户
  const [editTarget, setEditTarget] = useState<UserItem | null>(null);
  const [editForm, setEditForm] = useState({ username: '', full_name: '', status: 'active' });
  const [editSaving, setEditSaving] = useState(false);

  // 角色绑定
  const [roleTarget, setRoleTarget] = useState<UserItem | null>(null);
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [roleSaving, setRoleSaving] = useState(false);
  const [rolesLoading, setRolesLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setUsers(await usersApi.list());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await usersApi.create(form);
      setShowCreate(false);
      setForm({ email: '', username: '', password: '', full_name: '' });
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    try {
      await usersApi.delete(deleteTarget);
      setDeleteTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  // 打开编辑弹窗
  function openEdit(user: UserItem) {
    setEditTarget(user);
    setEditForm({
      username: user.username || '',
      full_name: user.full_name || '',
      status: user.status,
    });
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editTarget) return;
    setEditSaving(true);
    try {
      await usersApi.update(editTarget.id, editForm);
      setEditTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '编辑失败');
    } finally {
      setEditSaving(false);
    }
  }

  // 打开角色绑定弹窗
  async function openRoleModal(user: UserItem) {
    setRoleTarget(user);
    setSelectedRoleIds(user.role_ids || []);
    setRolesLoading(true);
    try {
      setAllRoles(await rolesApi.list());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载角色失败');
    } finally {
      setRolesLoading(false);
    }
  }

  function toggleRole(roleId: string) {
    setSelectedRoleIds(prev =>
      prev.includes(roleId) ? prev.filter(id => id !== roleId) : [...prev, roleId]
    );
  }

  async function handleRoleSave() {
    if (!roleTarget) return;
    setRoleSaving(true);
    try {
      await usersApi.update(roleTarget.id, { role_ids: selectedRoleIds } as Partial<UserItem>);
      setRoleTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '保存角色失败');
    } finally {
      setRoleSaving(false);
    }
  }

  function statusVariant(s: string): 'success' | 'danger' | 'warn' {
    if (s === 'active') return 'success';
    if (s === 'locked') return 'danger';
    return 'warn';
  }

  return (
    <div>
      <PageHeader
        title="用户管理"
        action={<Btn onClick={() => setShowCreate(true)}>+ 新建用户</Btn>}
      />
      {error && <ErrorBox message={error} />}
      {loading ? <Spinner /> : users.length === 0 ? <EmptyState message="暂无用户" /> : (
        <table>
          <thead>
            <tr>
              <th>邮箱</th><th>用户名</th><th>全名</th><th>状态</th><th>创建时间</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>{u.username || '—'}</td>
                <td>{u.full_name || '—'}</td>
                <td><Badge label={u.status} variant={statusVariant(u.status)} /></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {new Date(u.created_at).toLocaleString('zh-CN')}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <Btn variant="ghost" size="sm" onClick={() => openEdit(u)}>编辑</Btn>
                    <Btn variant="ghost" size="sm" onClick={() => openRoleModal(u)}>角色</Btn>
                    <Btn variant="danger" size="sm" onClick={() => setDeleteTarget(u.id)}>删除</Btn>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* 新建用户 Modal */}
      {showCreate && (
        <Modal title="新建用户" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="邮箱*" type="email" required value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            <Input label="用户名" value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
            <Input label="全名" value={form.full_name}
              onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
            <Input label="密码*" type="password" required value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setShowCreate(false)}>取消</Btn>
              <Btn type="submit" disabled={saving}>{saving ? '保存中...' : '创建'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 编辑用户 Modal */}
      {editTarget && (
        <Modal title="编辑用户" onClose={() => setEditTarget(null)}>
          <form onSubmit={handleEditSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="邮箱" value={editTarget.email} disabled
              style={{ opacity: 0.6, cursor: 'not-allowed' }} />
            <Input label="用户名" value={editForm.username}
              onChange={e => setEditForm(f => ({ ...f, username: e.target.value }))} />
            <Input label="全名" value={editForm.full_name}
              onChange={e => setEditForm(f => ({ ...f, full_name: e.target.value }))} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500, letterSpacing: '0.03em' }}>
                状态
              </label>
              <select
                value={editForm.status}
                onChange={e => setEditForm(f => ({ ...f, status: e.target.value }))}
                style={{
                  background: 'rgba(31, 41, 55, 0.8)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: 'inherit',
                  fontSize: 'inherit',
                  fontFamily: 'inherit',
                }}
              >
                <option value="active">active</option>
                <option value="locked">locked</option>
                <option value="suspended">suspended</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setEditTarget(null)}>取消</Btn>
              <Btn type="submit" disabled={editSaving}>{editSaving ? '保存中...' : '保存'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 角色绑定 Modal */}
      {roleTarget && (
        <Modal title={`角色绑定 — ${roleTarget.username || roleTarget.email}`} onClose={() => setRoleTarget(null)}>
          {rolesLoading ? <Spinner /> : allRoles.length === 0 ? (
            <EmptyState message="暂无可用角色" />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {allRoles.map(role => (
                <label key={role.id} style={{
                  display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
                  padding: '8px 12px', borderRadius: '8px',
                  background: selectedRoleIds.includes(role.id) ? 'rgba(59,130,246,0.1)' : 'transparent',
                  border: `1px solid ${selectedRoleIds.includes(role.id) ? 'rgba(59,130,246,0.3)' : 'var(--border)'}`,
                  transition: 'all 0.2s',
                }}>
                  <input
                    type="checkbox"
                    style={{ width: 'auto' }}
                    checked={selectedRoleIds.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                  />
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '13px' }}>{role.name}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{role.description || '无描述'}</div>
                  </div>
                </label>
              ))}
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '12px' }}>
                <Btn variant="ghost" type="button" onClick={() => setRoleTarget(null)}>取消</Btn>
                <Btn onClick={handleRoleSave} disabled={roleSaving}>{roleSaving ? '保存中...' : '保存'}</Btn>
              </div>
            </div>
          )}
        </Modal>
      )}

      {/* 删除确认 Modal */}
      {deleteTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTarget(null)}>
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>确认删除该用户？此操作不可撤销。</p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Btn variant="ghost" type="button" onClick={() => setDeleteTarget(null)}>取消</Btn>
            <Btn variant="danger" onClick={handleDeleteConfirm}>确认删除</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}
