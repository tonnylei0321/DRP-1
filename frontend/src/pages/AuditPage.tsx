/**
 * 9.5 审计日志页 — 时间/用户/操作类型过滤、导出
 */
import { useEffect, useState } from 'react';
import { auditApi, AuditLog } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox } from '../components/ui';

const EVENT_TYPES = ['', 'login', 'login_failed', 'logout', 'permission_denied', 'user_created', 'user_deleted', 'role_changed'];

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [eventType, setEventType] = useState('');
  const [page, setPage] = useState(1);

  async function load() {
    setLoading(true);
    try {
      setLogs(await auditApi.list({ page, per_page: 20, event_type: eventType || undefined }));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [eventType, page]);

  function eventVariant(t: string): 'success' | 'danger' | 'warn' | 'info' {
    if (t === 'login') return 'success';
    if (t.includes('failed') || t.includes('denied') || t.includes('deleted')) return 'danger';
    if (t.includes('created') || t.includes('changed')) return 'warn';
    return 'info';
  }

  function sanitizeCsvField(value: string): string {
    if (/^[=+\-@\t\r]/.test(value)) {
      return `'${value}`;
    }
    return value;
  }

  function handleExport() {
    const csv = [
      'ID,UserID,EventType,Resource,IP,CreatedAt',
      ...logs.map(l =>
        [l.id, l.user_id, l.event_type, l.resource || '', l.ip_address || '', l.created_at]
          .map(sanitizeCsvField)
          .join(',')
      ),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <PageHeader
        title="审计日志"
        action={<Btn variant="ghost" onClick={handleExport}>导出 CSV</Btn>}
      />
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <select
          value={eventType}
          onChange={e => { setEventType(e.target.value); setPage(1); }}
          style={{ width: '200px' }}
        >
          {EVENT_TYPES.map(t => (
            <option key={t} value={t}>{t || '全部事件类型'}</option>
          ))}
        </select>
      </div>
      {error && <ErrorBox message={error} />}
      {loading ? <Spinner /> : logs.length === 0 ? <EmptyState message="暂无审计日志" /> : (
        <>
          <table>
            <thead>
              <tr><th>事件类型</th><th>用户ID</th><th>资源</th><th>IP 地址</th><th>时间</th></tr>
            </thead>
            <tbody>
              {logs.map(l => (
                <tr key={l.id}>
                  <td><Badge label={l.event_type} variant={eventVariant(l.event_type)} /></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{l.user_id.slice(0, 8)}...</td>
                  <td>{l.resource || '—'}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{l.ip_address || '—'}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                    {new Date(l.created_at).toLocaleString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
            <Btn variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Btn>
            <span style={{ color: 'var(--text-muted)', lineHeight: '28px' }}>第 {page} 页</span>
            <Btn variant="ghost" size="sm" onClick={() => setPage(p => p + 1)}>下一页</Btn>
          </div>
        </>
      )}
    </div>
  );
}
