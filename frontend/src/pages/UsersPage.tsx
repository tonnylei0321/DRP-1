/**
 * 9.2 用户管理页 — 增删改查、角色分配
 */
import React, { useEffect, useState } from 'react';
import { usersApi } from '../api/client';
import type { UserItem } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Modal, Input } from '../components/ui';

export default function UsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

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
                  <Btn variant="danger" size="sm" onClick={() => setDeleteTarget(u.id)}>删除</Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

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
