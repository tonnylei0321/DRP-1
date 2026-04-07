/**
 * 数据权限管理页面 — 行级规则 + 列级规则 + 熔断开关
 */
import React, { useEffect, useState, useCallback } from 'react';
import { dataScopeApi, usersApi, rolesApi, getPermissions } from '../api/client';
import type { DataScopeRule, ColumnMaskRule, TableMeta, CircuitBreakerStatus, UserItem, Role } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card, Modal, Input } from '../components/ui';

// ─── 通用样式 ────────────────────────────────────────────────────────────────

const selectStyle: React.CSSProperties = {
  background: 'rgba(31, 41, 55, 0.8)',
  backdropFilter: 'blur(8px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: '8px',
  padding: '10px 14px',
  color: 'inherit',
  fontSize: 'inherit',
  fontFamily: 'inherit',
};

const radioLabelStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: '8px',
  padding: '6px 12px', borderRadius: '6px', cursor: 'pointer',
  fontSize: '13px',
};

function hasPermission(perm: string): boolean {
  const perms = getPermissions();
  return perms === null || perms.includes(perm);
}

const SCOPE_TYPE_LABELS: Record<string, string> = {
  all: '全部数据', dept: '本部门及下级', self: '仅本人', custom: '自定义条件',
};

const MASK_STRATEGY_LABELS: Record<string, string> = {
  mask: '部分遮蔽', hide: '完全隐藏', none: '不脱敏',
};

const MASK_PATTERN_LABELS: Record<string, string> = {
  phone: '手机号', id_card: '身份证号', email: '邮箱', custom_regex: '自定义正则',
};

// ═══════════════════════════════════════════════════════════════════════════════
// DataScopeRulesPage — 行级规则管理
// ═══════════════════════════════════════════════════════════════════════════════

export function DataScopeRulesPage() {
  const [rules, setRules] = useState<DataScopeRule[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [tables, setTables] = useState<TableMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterUserId, setFilterUserId] = useState('');

  // 创建 Modal
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    user_id: '', table_name: '', scope_type: 'self', custom_condition: '',
  });
  const [saving, setSaving] = useState(false);
  const [conflictWarning, setConflictWarning] = useState('');

  // 删除确认
  const [deleteTarget, setDeleteTarget] = useState<DataScopeRule | null>(null);
  const [deleteWarning, setDeleteWarning] = useState('');

  // all 类型二次确认
  const [confirmAllCreate, setConfirmAllCreate] = useState(false);
  const [pendingCreateData, setPendingCreateData] = useState<typeof createForm | null>(null);

  const canWrite = hasPermission('data_scope:write');

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      setRules(await dataScopeApi.listRules(filterUserId || undefined));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载规则失败');
    } finally {
      setLoading(false);
    }
  }, [filterUserId]);

  useEffect(() => { loadRules(); }, [loadRules]);

  useEffect(() => {
    usersApi.list().then(setUsers).catch(() => {});
    dataScopeApi.getTables().then(setTables).catch(() => {});
  }, []);

  function getUserName(userId: string): string {
    const u = users.find(u => u.id === userId);
    return u ? (u.username || u.email) : userId.slice(0, 8);
  }

  async function doCreateRule(form: typeof createForm) {
    setSaving(true);
    setConflictWarning('');
    try {
      // 使用第一个用户的 tenant_id 作为默认值
      const user = users.find(u => u.id === form.user_id);
      const tenantId = user?.tenant_id || '';
      const result = await dataScopeApi.createRule({
        tenant_id: tenantId,
        user_id: form.user_id,
        table_name: form.table_name,
        scope_type: form.scope_type,
        custom_condition: form.scope_type === 'custom' ? form.custom_condition : undefined,
      });
      if (result.warning) {
        setConflictWarning(result.warning);
      }
      setShowCreate(false);
      setCreateForm({ user_id: '', table_name: '', scope_type: 'self', custom_condition: '' });
      loadRules();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (createForm.scope_type === 'all') {
      setPendingCreateData({ ...createForm });
      setConfirmAllCreate(true);
      return;
    }
    await doCreateRule(createForm);
  }

  async function handleConfirmAllCreate() {
    if (pendingCreateData) {
      await doCreateRule(pendingCreateData);
    }
    setConfirmAllCreate(false);
    setPendingCreateData(null);
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      const result = await dataScopeApi.deleteRule(deleteTarget.id);
      if (result.warning) {
        setDeleteWarning(result.warning);
      }
      setDeleteTarget(null);
      loadRules();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  // 检查是否为最后一条规则
  function isLastRule(rule: DataScopeRule): boolean {
    return rules.filter(r =>
      r.user_id === rule.user_id && r.table_name === rule.table_name
    ).length <= 1;
  }

  return (
    <div>
      <PageHeader
        title="行级数据权限规则"
        action={canWrite ? <Btn onClick={() => setShowCreate(true)}>+ 新建规则</Btn> : undefined}
      />
      {error && <ErrorBox message={error} />}
      {conflictWarning && (
        <div style={{
          background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: '10px', padding: '12px 16px', color: '#eab308',
          marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px',
        }}>
          <span>⚠️</span> {conflictWarning}
          <Btn variant="ghost" size="sm" onClick={() => setConflictWarning('')} style={{ marginLeft: 'auto' }}>关闭</Btn>
        </div>
      )}
      {deleteWarning && (
        <div style={{
          background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: '10px', padding: '12px 16px', color: '#eab308',
          marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px',
        }}>
          <span>⚠️</span> {deleteWarning}
          <Btn variant="ghost" size="sm" onClick={() => setDeleteWarning('')} style={{ marginLeft: 'auto' }}>关闭</Btn>
        </div>
      )}

      {/* 用户筛选 */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>按用户筛选</label>
          <select value={filterUserId} onChange={e => setFilterUserId(e.target.value)} style={{ ...selectStyle, width: '280px' }}>
            <option value="">全部用户</option>
            {users.map(u => <option key={u.id} value={u.id}>{u.username || u.email}</option>)}
          </select>
        </div>
      </div>

      {loading ? <Spinner /> : rules.length === 0 ? <EmptyState message="暂无行级规则" /> : (
        <table>
          <thead>
            <tr><th>用户</th><th>业务表</th><th>范围类型</th><th>自定义条件</th><th>创建时间</th>{canWrite && <th>操作</th>}</tr>
          </thead>
          <tbody>
            {rules.map(r => (
              <tr key={r.id}>
                <td>{getUserName(r.user_id)}</td>
                <td><Badge label={r.table_name} variant="info" /></td>
                <td><Badge label={SCOPE_TYPE_LABELS[r.scope_type] || r.scope_type} variant={r.scope_type === 'all' ? 'warn' : 'success'} /></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.custom_condition || '—'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {new Date(r.created_at).toLocaleString('zh-CN')}
                </td>
                {canWrite && (
                  <td>
                    <Btn variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>删除</Btn>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* 创建规则 Modal */}
      {showCreate && (
        <Modal title="新建行级规则" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>用户*</label>
              <select required value={createForm.user_id} onChange={e => setCreateForm(f => ({ ...f, user_id: e.target.value }))} style={selectStyle}>
                <option value="">请选择用户</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.username || u.email}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>业务表*</label>
              <select required value={createForm.table_name} onChange={e => setCreateForm(f => ({ ...f, table_name: e.target.value }))} style={selectStyle}>
                <option value="">请选择业务表</option>
                {tables.map(t => <option key={t.table_name} value={t.table_name}>{t.table_name}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>范围类型*</label>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {Object.entries(SCOPE_TYPE_LABELS).map(([val, label]) => (
                  <label key={val} style={{
                    ...radioLabelStyle,
                    background: createForm.scope_type === val ? 'rgba(59,130,246,0.1)' : 'transparent',
                    border: `1px solid ${createForm.scope_type === val ? 'rgba(59,130,246,0.3)' : 'var(--border)'}`,
                  }}>
                    <input type="radio" name="scope_type" value={val} checked={createForm.scope_type === val}
                      onChange={e => setCreateForm(f => ({ ...f, scope_type: e.target.value }))} style={{ width: 'auto' }} />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            {createForm.scope_type === 'custom' && (
              <Input label="自定义条件*" required value={createForm.custom_condition}
                placeholder="例: region = 'Beijing' AND amount > 1000"
                onChange={e => setCreateForm(f => ({ ...f, custom_condition: e.target.value }))} />
            )}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setShowCreate(false)}>取消</Btn>
              <Btn type="submit" disabled={saving}>{saving ? '保存中...' : '创建'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* all 类型二次确认 */}
      {confirmAllCreate && (
        <Modal title="确认创建" onClose={() => { setConfirmAllCreate(false); setPendingCreateData(null); }}>
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>
            ⚠️ 此操作将授予该用户对该表的全部数据访问权限，确认继续？
          </p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Btn variant="ghost" type="button" onClick={() => { setConfirmAllCreate(false); setPendingCreateData(null); }}>取消</Btn>
            <Btn variant="danger" onClick={handleConfirmAllCreate}>确认创建</Btn>
          </div>
        </Modal>
      )}

      {/* 删除确认 Modal */}
      {deleteTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTarget(null)}>
          {isLastRule(deleteTarget) && (
            <div style={{
              background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: '8px', padding: '10px 14px', marginBottom: '12px',
              color: 'var(--danger)', fontSize: '13px',
            }}>
              ⚠️ 这是该用户对此表的最后一条规则，删除后该用户将无法访问此表数据
            </div>
          )}
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>确认删除该行级规则？此操作不可撤销。</p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Btn variant="ghost" type="button" onClick={() => setDeleteTarget(null)}>取消</Btn>
            <Btn variant="danger" onClick={handleDelete}>确认删除</Btn>
          </div>
        </Modal>
      )}

      {/* 熔断开关面板 */}
      {hasPermission('data_scope:circuit_breaker') && <CircuitBreakerPanel />}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// ColumnMaskRulesPage — 列级脱敏规则管理
// ═══════════════════════════════════════════════════════════════════════════════

export function ColumnMaskRulesPage() {
  const [rules, setRules] = useState<ColumnMaskRule[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [tables, setTables] = useState<TableMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterRoleId, setFilterRoleId] = useState('');

  // 创建 Modal
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    role_id: '', table_name: '', column_name: '',
    mask_strategy: 'mask', mask_pattern: 'phone', regex_expression: '',
  });
  const [saving, setSaving] = useState(false);

  // 删除确认
  const [deleteTarget, setDeleteTarget] = useState<ColumnMaskRule | null>(null);

  const canWrite = hasPermission('data_scope:write');

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      setRules(await dataScopeApi.listMaskRules(filterRoleId || undefined));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载规则失败');
    } finally {
      setLoading(false);
    }
  }, [filterRoleId]);

  useEffect(() => { loadRules(); }, [loadRules]);

  useEffect(() => {
    rolesApi.list().then(setRoles).catch(() => {});
    dataScopeApi.getTables().then(setTables).catch(() => {});
  }, []);

  function getRoleName(roleId: string): string {
    const r = roles.find(r => r.id === roleId);
    return r ? r.name : roleId.slice(0, 8);
  }

  // 获取选中表的列列表
  function getColumnsForTable(tableName: string): string[] {
    const t = tables.find(t => t.table_name === tableName);
    return t ? Object.keys(t.columns) : [];
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const role = roles.find(r => r.id === createForm.role_id);
      // 使用第一个可用的 tenant_id
      const tenantId = role ? '' : '';
      await dataScopeApi.createMaskRule({
        tenant_id: tenantId,
        role_id: createForm.role_id,
        table_name: createForm.table_name,
        column_name: createForm.column_name,
        mask_strategy: createForm.mask_strategy,
        mask_pattern: createForm.mask_strategy === 'mask' ? createForm.mask_pattern : undefined,
        regex_expression: createForm.mask_pattern === 'custom_regex' ? createForm.regex_expression : undefined,
      });
      setShowCreate(false);
      setCreateForm({ role_id: '', table_name: '', column_name: '', mask_strategy: 'mask', mask_pattern: 'phone', regex_expression: '' });
      loadRules();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await dataScopeApi.deleteMaskRule(deleteTarget.id);
      setDeleteTarget(null);
      loadRules();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  return (
    <div>
      <PageHeader
        title="列级脱敏规则"
        action={canWrite ? <Btn onClick={() => setShowCreate(true)}>+ 新建规则</Btn> : undefined}
      />
      {error && <ErrorBox message={error} />}

      {/* 角色筛选 */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>按角色筛选</label>
          <select value={filterRoleId} onChange={e => setFilterRoleId(e.target.value)} style={{ ...selectStyle, width: '280px' }}>
            <option value="">全部角色</option>
            {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </div>
      </div>

      {loading ? <Spinner /> : rules.length === 0 ? <EmptyState message="暂无列级规则" /> : (
        <table>
          <thead>
            <tr><th>角色</th><th>业务表</th><th>列名</th><th>脱敏策略</th><th>脱敏模式</th>{canWrite && <th>操作</th>}</tr>
          </thead>
          <tbody>
            {rules.map(r => (
              <tr key={r.id}>
                <td>{getRoleName(r.role_id)}</td>
                <td><Badge label={r.table_name} variant="info" /></td>
                <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{r.column_name}</td>
                <td><Badge label={MASK_STRATEGY_LABELS[r.mask_strategy] || r.mask_strategy}
                  variant={r.mask_strategy === 'hide' ? 'danger' : r.mask_strategy === 'mask' ? 'warn' : 'success'} /></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {r.mask_pattern ? (MASK_PATTERN_LABELS[r.mask_pattern] || r.mask_pattern) : '—'}
                </td>
                {canWrite && (
                  <td>
                    <Btn variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>删除</Btn>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* 创建规则 Modal */}
      {showCreate && (
        <Modal title="新建列级规则" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>角色*</label>
              <select required value={createForm.role_id} onChange={e => setCreateForm(f => ({ ...f, role_id: e.target.value }))} style={selectStyle}>
                <option value="">请选择角色</option>
                {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>业务表*</label>
              <select required value={createForm.table_name}
                onChange={e => setCreateForm(f => ({ ...f, table_name: e.target.value, column_name: '' }))}
                style={selectStyle}>
                <option value="">请选择业务表</option>
                {tables.map(t => <option key={t.table_name} value={t.table_name}>{t.table_name}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>列名*</label>
              <select required value={createForm.column_name}
                onChange={e => setCreateForm(f => ({ ...f, column_name: e.target.value }))}
                style={selectStyle} disabled={!createForm.table_name}>
                <option value="">请选择列名</option>
                {getColumnsForTable(createForm.table_name).map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>脱敏策略*</label>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {Object.entries(MASK_STRATEGY_LABELS).map(([val, label]) => (
                  <label key={val} style={{
                    ...radioLabelStyle,
                    background: createForm.mask_strategy === val ? 'rgba(59,130,246,0.1)' : 'transparent',
                    border: `1px solid ${createForm.mask_strategy === val ? 'rgba(59,130,246,0.3)' : 'var(--border)'}`,
                  }}>
                    <input type="radio" name="mask_strategy" value={val} checked={createForm.mask_strategy === val}
                      onChange={e => setCreateForm(f => ({ ...f, mask_strategy: e.target.value }))} style={{ width: 'auto' }} />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            {createForm.mask_strategy === 'mask' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500 }}>脱敏模式*</label>
                <select required value={createForm.mask_pattern}
                  onChange={e => setCreateForm(f => ({ ...f, mask_pattern: e.target.value }))}
                  style={selectStyle}>
                  {Object.entries(MASK_PATTERN_LABELS).map(([val, label]) => (
                    <option key={val} value={val}>{label}</option>
                  ))}
                </select>
              </div>
            )}
            {createForm.mask_strategy === 'mask' && createForm.mask_pattern === 'custom_regex' && (
              <Input label="正则表达式*" required value={createForm.regex_expression}
                placeholder="例: (\d{3})\d{4}(\d{4})"
                onChange={e => setCreateForm(f => ({ ...f, regex_expression: e.target.value }))} />
            )}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Btn variant="ghost" type="button" onClick={() => setShowCreate(false)}>取消</Btn>
              <Btn type="submit" disabled={saving}>{saving ? '保存中...' : '创建'}</Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 删除确认 Modal */}
      {deleteTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTarget(null)}>
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>确认删除该列级规则？此操作不可撤销。</p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Btn variant="ghost" type="button" onClick={() => setDeleteTarget(null)}>取消</Btn>
            <Btn variant="danger" onClick={handleDelete}>确认删除</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// CircuitBreakerPanel — 熔断开关面板
// ═══════════════════════════════════════════════════════════════════════════════

function CircuitBreakerPanel() {
  const [status, setStatus] = useState<CircuitBreakerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [password, setPassword] = useState('');
  const [autoRecover, setAutoRecover] = useState('');
  const [toggling, setToggling] = useState(false);
  const [cooldownDisplay, setCooldownDisplay] = useState(0);

  async function loadStatus() {
    setLoading(true);
    try {
      setStatus(await dataScopeApi.getCircuitBreaker());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载熔断状态失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadStatus(); }, []);

  // 冷却期倒计时
  useEffect(() => {
    if (!status || status.cooldown_remaining <= 0) {
      setCooldownDisplay(0);
      return;
    }
    setCooldownDisplay(status.cooldown_remaining);
    const timer = setInterval(() => {
      setCooldownDisplay(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [status]);

  async function handleToggle() {
    if (!status || !password) return;
    setToggling(true);
    setError('');
    try {
      const newStatus = await dataScopeApi.setCircuitBreaker({
        enabled: !status.enabled,
        password,
        auto_recover_minutes: autoRecover ? parseInt(autoRecover, 10) : undefined,
      });
      setStatus(newStatus);
      setPassword('');
      setAutoRecover('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '操作失败');
    } finally {
      setToggling(false);
    }
  }

  // 计算持续时间
  function getDuration(): string {
    if (!status?.disabled_at) return '';
    const ms = Date.now() - new Date(status.disabled_at).getTime();
    const mins = Math.floor(ms / 60000);
    if (mins < 60) return `${mins} 分钟`;
    const hours = Math.floor(mins / 60);
    return `${hours} 小时 ${mins % 60} 分钟`;
  }

  if (loading) return <Card style={{ marginTop: '24px' }}><Spinner /></Card>;

  return (
    <Card style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <span style={{ fontSize: '20px' }}>🔌</span>
        <div style={{ fontWeight: 600, fontSize: '15px' }}>熔断开关</div>
        {status && (
          <Badge
            label={status.enabled ? '数据过滤已启用' : '数据过滤已禁用（熔断中）'}
            variant={status.enabled ? 'success' : 'danger'}
          />
        )}
      </div>

      {error && <ErrorBox message={error} />}

      {status && !status.enabled && status.disabled_at && (
        <div style={{
          background: 'rgba(239,68,68,0.06)', borderRadius: '8px', padding: '10px 14px',
          marginBottom: '12px', fontSize: '13px', color: 'var(--text-muted)',
        }}>
          已禁用 {getDuration()}
          {status.auto_recover_at && (
            <span> · 预计自动恢复: {new Date(status.auto_recover_at).toLocaleString('zh-CN')}</span>
          )}
        </div>
      )}

      {cooldownDisplay > 0 && (
        <div style={{
          background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: '8px', padding: '10px 14px', marginBottom: '12px',
          color: '#eab308', fontSize: '13px',
        }}>
          ⏳ 冷却期剩余 {cooldownDisplay} 秒，期间无法切换
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <Input label="操作密码*" type="password" value={password}
          onChange={e => setPassword(e.target.value)} placeholder="输入密码以验证身份" />
        <Input label="自动恢复（分钟）" type="number" value={autoRecover}
          onChange={e => setAutoRecover(e.target.value)} placeholder="可选" style={{ width: '120px' }} />
        <Btn
          variant={status?.enabled ? 'danger' : 'primary'}
          onClick={handleToggle}
          disabled={toggling || !password || cooldownDisplay > 0}
        >
          {toggling ? '操作中...' : status?.enabled ? '禁用数据过滤' : '启用数据过滤'}
        </Btn>
      </div>
    </Card>
  );
}
