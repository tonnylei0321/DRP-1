/**
 * 9.8 ETL 任务监控页 — 同步历史、耗时、数据量、错误日志
 * 9.9 租户管理页 — 仅平台管理员可见
 * 9.10 数据质量面板 — 三维评分可视化
 */
import { useEffect, useState } from 'react';
import { etlApi, EtlJob, tenantsApi, Tenant, qualityApi, DataQuality } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card, Modal, Input } from '../components/ui';

// ─── ETL 任务监控 ────────────────────────────────────────────────────────────

export function EtlPage() {
  const [jobs, setJobs] = useState<EtlJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    try { setJobs(await etlApi.list()); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : '加载失败'); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  function statusBadge(s: string): 'success' | 'danger' | 'warn' | 'info' {
    if (s === 'success') return 'success';
    if (s === 'failed') return 'danger';
    if (s === 'running') return 'warn';
    return 'info';
  }

  function duration(job: EtlJob): string {
    if (!job.finished_at) return '—';
    const ms = new Date(job.finished_at).getTime() - new Date(job.created_at).getTime();
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
  }

  return (
    <div>
      <PageHeader
        title="ETL 任务监控"
        action={<Btn variant="ghost" size="sm" onClick={load}>刷新</Btn>}
      />
      {error && <ErrorBox message={error} />}
      {loading ? <Spinner /> : jobs.length === 0 ? <EmptyState message="暂无 ETL 任务记录" /> : (
        <table>
          <thead>
            <tr><th>任务 ID</th><th>类型</th><th>状态</th><th>写入三元组</th><th>耗时</th><th>开始时间</th><th>错误</th></tr>
          </thead>
          <tbody>
            {jobs.map(j => (
              <tr key={j.id}>
                <td style={{ fontFamily: 'monospace', fontSize: '11px' }}>{j.id.slice(0, 8)}...</td>
                <td><Badge label={j.job_type} variant="info" /></td>
                <td><Badge label={j.status} variant={statusBadge(j.status)} /></td>
                <td style={{ textAlign: 'right' }}>{j.triples_written?.toLocaleString() ?? '—'}</td>
                <td style={{ color: 'var(--text-muted)' }}>{duration(j)}</td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {new Date(j.created_at).toLocaleString('zh-CN')}
                </td>
                <td style={{ color: 'var(--danger)', fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {j.error_message || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ─── 租户管理 ────────────────────────────────────────────────────────────────

export function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleteTenantTarget, setDeleteTenantTarget] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try { setTenants(await tenantsApi.list()); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : '加载失败'); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await tenantsApi.create(name);
      setShowCreate(false);
      setName('');
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败');
    } finally { setSaving(false); }
  }

  async function handleDeleteConfirm() {
    if (!deleteTenantTarget) return;
    try {
      await tenantsApi.delete(deleteTenantTarget);
      setDeleteTenantTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  }

  function statusBadge(s: string): 'success' | 'warn' | 'danger' {
    if (s === 'active') return 'success';
    if (s === 'suspended') return 'warn';
    return 'danger';
  }

  return (
    <div>
      <PageHeader
        title="租户管理"
        action={<Btn onClick={() => setShowCreate(true)}>+ 新建租户</Btn>}
      />
      {error && <ErrorBox message={error} />}
      {loading ? <Spinner /> : tenants.length === 0 ? <EmptyState message="暂无租户" /> : (
        <table>
          <thead>
            <tr><th>名称</th><th>Graph IRI</th><th>状态</th><th>创建时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            {tenants.map(t => (
              <tr key={t.id}>
                <td style={{ fontWeight: 500 }}>{t.name}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--text-muted)' }}>{t.graph_iri}</td>
                <td><Badge label={t.status} variant={statusBadge(t.status)} /></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {new Date(t.created_at).toLocaleString('zh-CN')}
                </td>
                <td>
                  <Btn variant="danger" size="sm" onClick={() => setDeleteTenantTarget(t.id)}>删除</Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {showCreate && (
        <Modal title="新建租户" onClose={() => setShowCreate(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="租户名称*" value={name} onChange={e => setName(e.target.value)} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Btn variant="ghost" onClick={() => setShowCreate(false)}>取消</Btn>
              <Btn onClick={handleCreate} disabled={saving}>{saving ? '创建中...' : '创建'}</Btn>
            </div>
          </div>
        </Modal>
      )}
      {deleteTenantTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTenantTarget(null)}>
          <p style={{ color: 'var(--text)', marginBottom: '16px' }}>确认删除该租户？此操作将删除所有相关数据！</p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <Btn variant="ghost" onClick={() => setDeleteTenantTarget(null)}>取消</Btn>
            <Btn variant="danger" onClick={handleDeleteConfirm}>确认删除</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── 数据质量面板 ─────────────────────────────────────────────────────────────

interface QualityBarProps { label: string; value: number; max?: number; }

function QualityBar({ label, value, max = 100 }: QualityBarProps) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warn)' : 'var(--danger)';
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px' }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{value.toFixed(1)}{max === 100 ? '%' : 's'}</span>
      </div>
      <div style={{ background: 'var(--border)', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, transition: 'width 0.4s' }} />
      </div>
    </div>
  );
}

export function QualityPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [quality, setQuality] = useState<DataQuality | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    tenantsApi.list()
      .then(ts => { setTenants(ts); if (ts[0]) setSelected(ts[0].id); })
      .catch(e => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    qualityApi.get(selected)
      .then(setQuality)
      .catch(() => setQuality(null))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div>
      <PageHeader title="数据质量面板" />
      {error && <ErrorBox message={error} />}
      <div style={{ marginBottom: '16px' }}>
        <select value={selected} onChange={e => setSelected(e.target.value)} style={{ width: '240px' }}>
          {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>
      {loading ? <Spinner /> : !quality ? <EmptyState message="暂无质量数据" /> : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <Card>
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '4px' }}>综合质量评分</div>
              <div style={{ fontSize: '48px', fontWeight: 700, color: quality.is_healthy ? 'var(--success)' : 'var(--danger)' }}>
                {quality.overall.toFixed(1)}
              </div>
              <Badge
                label={quality.is_healthy ? '健康' : '需关注'}
                variant={quality.is_healthy ? 'success' : 'danger'}
              />
            </div>
            <QualityBar label="空值率评分（越低越好）" value={(1 - quality.null_rate) * 100} />
            <QualityBar label="格式合规率" value={quality.format_compliance * 100} />
          </Card>
          <Card>
            <div style={{ marginBottom: '16px', fontWeight: 600 }}>延迟监控</div>
            <div style={{ fontSize: '32px', fontWeight: 700, color: quality.latency_seconds < 3600 ? 'var(--success)' : 'var(--danger)' }}>
              {quality.latency_seconds < 60
                ? `${quality.latency_seconds.toFixed(0)}s`
                : `${(quality.latency_seconds / 60).toFixed(1)}min`}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>数据同步延迟</div>
            <div style={{ marginTop: '20px', color: 'var(--text-muted)', fontSize: '12px' }}>
              <div>空值率: {(quality.null_rate * 100).toFixed(1)}%</div>
              <div>格式合规率: {(quality.format_compliance * 100).toFixed(1)}%</div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
