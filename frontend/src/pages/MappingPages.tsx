/**
 * 9.6 DDL 上传页 — 文件上传 + 解析结果预览
 * 9.7 映射审核队列页 — 置信度展示、确认/修改/忽略操作
 */
import React, { useEffect, useState } from 'react';
import { mappingApi, MappingSpec } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card, Modal, Input } from '../components/ui';

// ─── DDL 上传页 ──────────────────────────────────────────────────────────────

export function DdlUploadPage() {
  const [ddl, setDdl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ mappings: MappingSpec[]; mapping_yaml: string } | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => setDdl(ev.target?.result as string ?? '');
    reader.readAsText(file);
  }

  async function handleGenerate() {
    if (!ddl.trim()) return;
    setError('');
    setLoading(true);
    try {
      setResult(await mappingApi.generate(ddl));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败');
    } finally {
      setLoading(false);
    }
  }

  function confidenceBadge(c: number): 'success' | 'warn' | 'danger' {
    if (c >= 80) return 'success';
    if (c >= 60) return 'warn';
    return 'danger';
  }

  return (
    <div>
      <PageHeader title="DDL 上传与映射生成" />
      {error && <ErrorBox message={error} />}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Card>
          <div style={{ marginBottom: '12px', color: 'var(--text-muted)', fontSize: '13px' }}>
            支持 MySQL / PostgreSQL / Oracle DDL
          </div>
          <div style={{ marginBottom: '12px' }}>
            <input type="file" accept=".sql,.ddl,.txt" onChange={handleFileChange}
              style={{ width: 'auto', background: 'none', border: 'none', color: 'var(--text)' }} />
          </div>
          <textarea
            value={ddl}
            onChange={e => setDdl(e.target.value)}
            placeholder="或直接粘贴 DDL..."
            style={{ height: '240px', resize: 'vertical', fontFamily: 'monospace', fontSize: '12px' }}
          />
          <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
            <Btn onClick={handleGenerate} disabled={loading || !ddl.trim()}>
              {loading ? '分析中...' : '生成映射建议'}
            </Btn>
          </div>
        </Card>

        <Card>
          <div style={{ marginBottom: '12px', fontWeight: 600 }}>解析结果预览</div>
          {!result ? (
            <EmptyState message="上传 DDL 后将在此显示映射建议" />
          ) : (
            <div style={{ overflowY: 'auto', maxHeight: '340px' }}>
              <div style={{ marginBottom: '8px', color: 'var(--text-muted)', fontSize: '12px' }}>
                共 {result.mappings.length} 条映射建议
              </div>
              <table>
                <thead><tr><th>源字段</th><th>目标属性</th><th>置信度</th></tr></thead>
                <tbody>
                  {result.mappings.map(m => (
                    <tr key={m.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{m.source_table}.{m.source_field}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent)' }}>{m.target_property}</td>
                      <td><Badge label={`${m.confidence.toFixed(0)}%`} variant={confidenceBadge(m.confidence)} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

// ─── 映射审核队列 ─────────────────────────────────────────────────────────────

export function MappingsPage() {
  const [mappings, setMappings] = useState<MappingSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rejectTarget, setRejectTarget] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  async function load() {
    setLoading(true);
    try {
      setMappings(await mappingApi.list());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleApprove(id: string) {
    await mappingApi.approve(id);
    load();
  }

  function handleReject(id: string) {
    setRejectTarget(id);
    setRejectReason('');
  }

  async function handleRejectConfirm() {
    if (!rejectTarget) return;
    await mappingApi.reject(rejectTarget, rejectReason);
    setRejectTarget(null);
    setRejectReason('');
    load();
  }

  function handleRejectCancel() {
    setRejectTarget(null);
    setRejectReason('');
  }

  function statusBadge(s: string): 'success' | 'danger' | 'warn' | 'info' {
    if (s === 'approved') return 'success';
    if (s === 'rejected') return 'danger';
    if (s === 'pending') return 'warn';
    return 'info';
  }

  function confidenceColor(c: number): string {
    if (c >= 80) return 'var(--success)';
    if (c >= 60) return 'var(--warn)';
    return 'var(--danger)';
  }

  const pending = mappings.filter(m => m.status === 'pending');
  const reviewed = mappings.filter(m => m.status !== 'pending');

  return (
    <div>
      <PageHeader title="映射审核队列" />
      {error && <ErrorBox message={error} />}
      {loading ? <Spinner /> : (
        <>
          {pending.length > 0 && (
            <>
              <div style={{ marginBottom: '12px', color: 'var(--warn)', fontWeight: 500 }}>
                待审核 ({pending.length})
              </div>
              <table style={{ marginBottom: '24px' }}>
                <thead>
                  <tr><th>源字段</th><th>目标属性</th><th>数据类型</th><th>置信度</th><th>操作</th></tr>
                </thead>
                <tbody>
                  {pending.map(m => (
                    <tr key={m.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{m.source_table}.{m.source_field}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent)' }}>{m.target_property}</td>
                      <td><Badge label={m.data_type} variant="info" /></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            width: '80px', height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden',
                          }}>
                            <div style={{
                              width: `${m.confidence}%`, height: '100%',
                              background: confidenceColor(m.confidence),
                            }} />
                          </div>
                          <span style={{ color: confidenceColor(m.confidence), fontSize: '12px' }}>
                            {m.confidence.toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <Btn size="sm" onClick={() => handleApprove(m.id)}>确认</Btn>
                          <Btn size="sm" variant="danger" onClick={() => handleReject(m.id)}>拒绝</Btn>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {reviewed.length > 0 && (
            <>
              <div style={{ marginBottom: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>
                已审核 ({reviewed.length})
              </div>
              <table>
                <thead>
                  <tr><th>源字段</th><th>目标属性</th><th>状态</th></tr>
                </thead>
                <tbody>
                  {reviewed.map(m => (
                    <tr key={m.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{m.source_table}.{m.source_field}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{m.target_property}</td>
                      <td><Badge label={m.status} variant={statusBadge(m.status)} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {mappings.length === 0 && <EmptyState message="暂无映射记录" />}
        </>
      )}

      {rejectTarget && (
        <Modal title="拒绝映射" onClose={handleRejectCancel}>
          <div style={{ marginBottom: '16px' }}>
            <Input
              label="拒绝原因（可选）"
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="请输入拒绝原因..."
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <Btn variant="ghost" onClick={handleRejectCancel}>取消</Btn>
            <Btn variant="danger" onClick={handleRejectConfirm}>确认拒绝</Btn>
          </div>
        </Modal>
      )}
    </div>
  );
}
