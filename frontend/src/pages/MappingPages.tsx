/**
 * 9.6 DDL/CSV 上传页 — 文件上传 + 异步任务 + 进度条 + 解析结果预览
 * 9.7 映射审核队列页 — 置信度展示、确认/修改/忽略操作
 */
import React, { useEffect, useState } from 'react';
import { mappingApi } from '../api/client';
import type { MappingSpec } from '../api/client';
import { Btn, Badge, PageHeader, EmptyState, Spinner, ErrorBox, Card, Modal, Input } from '../components/ui';

// ─── DDL/CSV 上传页 ──────────────────────────────────────────────────────────

export function DdlUploadPage() {
  const [content, setContent] = useState('');
  const [format, setFormat] = useState<'ddl' | 'csv'>('ddl');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ mappings: MappingSpec[]; mapping_yaml: string } | null>(null);

  // 异步任务状态
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStatus, setJobStatus] = useState('');
  const [jobCurrentTable, setJobCurrentTable] = useState('');
  const [jobDetail, setJobDetail] = useState('');
  const pollRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  React.useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');

    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!['sql', 'ddl', 'txt', 'csv'].includes(ext)) {
      setError('仅支持 .sql/.ddl/.txt/.csv 文件');
      return;
    }

    const maxSize = ext === 'csv' ? 209715200 : 5242880;
    const maxLabel = ext === 'csv' ? '200MB' : '5MB';
    if (file.size > maxSize) {
      setError(`文件大小不能超过 ${maxLabel}`);
      return;
    }

    if (ext === 'csv') { setFormat('csv'); } else { setFormat('ddl'); }

    const reader = new FileReader();
    reader.onload = ev => setContent(ev.target?.result as string ?? '');
    reader.readAsText(file);
  }

  function shouldUseAsync(): boolean {
    return content.length > 1048576 || format === 'csv';
  }

  function startPolling(id: string) {
    setJobId(id);
    setJobProgress(0);
    setJobStatus('pending');
    setJobCurrentTable('');
    setJobDetail('提交中...');

    pollRef.current = setInterval(async () => {
      try {
        const s = await mappingApi.getJobStatus(id);
        setJobProgress(s.progress);
        setJobStatus(s.status);
        setJobCurrentTable(s.current_table);
        setJobDetail(`${s.processed_tables}/${s.total_tables} 表，${s.processed_fields}/${s.total_fields} 字段`);

        if (s.status === 'completed') {
          if (pollRef.current) clearInterval(pollRef.current);
          setLoading(false);
          setJobDetail(`完成！共生成 ${s.result_count} 条映射建议`);
          try {
            const mappings = await mappingApi.list();
            setResult({ mappings, mapping_yaml: '' });
          } catch { /* ignore */ }
        } else if (s.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current);
          setLoading(false);
          setError(s.error || '任务失败');
        }
      } catch { /* 轮询失败不中断 */ }
    }, 2000);
  }

  async function handleGenerate() {
    if (!content.trim()) return;
    setError('');
    setResult(null);
    setJobId(null);
    setLoading(true);

    if (shouldUseAsync()) {
      try {
        const { job_id } = await mappingApi.generateAsync(content, format);
        startPolling(job_id);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : '提交任务失败');
        setLoading(false);
      }
    } else {
      try {
        setResult(await mappingApi.generate(content, format));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : '生成失败');
      } finally {
        setLoading(false);
      }
    }
  }

  function confidenceBadge(c: number): 'success' | 'warn' | 'danger' {
    if (c >= 80) return 'success';
    if (c >= 60) return 'warn';
    return 'danger';
  }

  return (
    <div>
      <PageHeader title="DDL / CSV 上传与映射生成" />
      {error && <ErrorBox message={error} />}

      {/* 异步任务进度条 */}
      {jobId && loading && (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: '10px', padding: '16px', marginBottom: '16px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text)' }}>
              {jobStatus === 'parsing' ? '📄 解析文件中...' :
               jobStatus === 'generating' ? `🤖 AI 分析中：${jobCurrentTable}` :
               '⏳ 等待处理...'}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--accent)', fontWeight: 600 }}>
              {jobProgress.toFixed(0)}%
            </span>
          </div>
          <div style={{
            width: '100%', height: '8px', background: 'var(--border)',
            borderRadius: '4px', overflow: 'hidden',
          }}>
            <div style={{
              width: `${jobProgress}%`, height: '100%',
              background: 'var(--accent)',
              borderRadius: '4px',
              transition: 'width 0.5s ease',
            }} />
          </div>
          <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
            {jobDetail}
          </div>
        </div>
      )}

      {/* 异步任务完成提示 */}
      {jobId && !loading && jobStatus === 'completed' && (
        <div style={{
          background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
          borderRadius: '10px', padding: '12px 16px', marginBottom: '16px',
          color: 'var(--success)', fontSize: '13px',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          <span>✅</span> {jobDetail}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Card>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <button onClick={() => setFormat('ddl')} style={{
              padding: '6px 16px', borderRadius: '6px', border: 'none', fontSize: '13px',
              background: format === 'ddl' ? 'var(--accent)' : 'var(--ghost-btn-bg)',
              color: format === 'ddl' ? '#fff' : 'var(--text-muted)',
              cursor: 'pointer', transition: 'all 0.2s', fontWeight: format === 'ddl' ? 600 : 400,
            }}>DDL 模式</button>
            <button onClick={() => setFormat('csv')} style={{
              padding: '6px 16px', borderRadius: '6px', border: 'none', fontSize: '13px',
              background: format === 'csv' ? 'var(--accent)' : 'var(--ghost-btn-bg)',
              color: format === 'csv' ? '#fff' : 'var(--text-muted)',
              cursor: 'pointer', transition: 'all 0.2s', fontWeight: format === 'csv' ? 600 : 400,
            }}>CSV 模式</button>
          </div>
          <div style={{ marginBottom: '12px', color: 'var(--text-muted)', fontSize: '13px' }}>
            {format === 'ddl'
              ? '支持 MySQL / PostgreSQL / Oracle DDL（≤ 5MB）'
              : 'CSV 表头：数据库名,表名,表说明,字段名,数据类型,允许空值,默认值,额外信息,字段说明（≤ 200MB）'}
          </div>
          <div style={{ marginBottom: '12px' }}>
            <input type="file" accept={format === 'csv' ? '.csv' : '.sql,.ddl,.txt,.csv'} onChange={handleFileChange}
              style={{ width: 'auto', background: 'none', border: 'none', color: 'var(--text)' }} />
          </div>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder={format === 'ddl' ? '或直接粘贴 DDL...' : '或直接粘贴 CSV 内容（含表头行）...'}
            style={{ height: '240px', resize: 'vertical', fontFamily: 'monospace', fontSize: '12px' }}
          />
          <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {shouldUseAsync() && content.trim() && (
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                📡 大文件将使用异步模式处理
              </span>
            )}
            <div style={{ marginLeft: 'auto' }}>
              <Btn onClick={handleGenerate} disabled={loading || !content.trim()}>
                {loading ? '处理中...' : '生成映射建议'}
              </Btn>
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ marginBottom: '12px', fontWeight: 600 }}>解析结果预览</div>
          {!result ? (
            <EmptyState message="上传 DDL 或 CSV 后将在此显示映射建议" />
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

  async function handleBatchApproveAll() {
    try {
      await mappingApi.batchApprove('all');
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '批量确认失败');
    }
  }

  async function handleBatchApproveThreshold() {
    try {
      await mappingApi.batchApprove('threshold', 80);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '按阈值确认失败');
    }
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
              <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ color: 'var(--warn)', fontWeight: 500 }}>
                  待审核 ({pending.length})
                </span>
                <Btn variant="primary" size="sm" onClick={handleBatchApproveAll}>全部确认</Btn>
                <Btn variant="primary" size="sm" onClick={handleBatchApproveThreshold}>按阈值确认(≥80%)</Btn>
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
