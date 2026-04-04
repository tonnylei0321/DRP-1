/**
 * 10.1 监管看板整体布局 — Topbar + 左侧树 + 中央图谱 + 右侧检查器 + 底部 Ticker
 */
import { useEffect, useState } from 'react';
import { getToken } from '../api/client';
import type { Lang } from './i18n';
import { t } from './i18n';
import { useRiskEvents } from './useRiskEvents';
import { HierarchyGraph, ForceGraph, type HierarchyNode, type NetworkNode, type NetworkLink } from './D3Graphs';
import {
  HudPanel, type HudNode,
  RiskTicker,
  DrillInspector,
  LayerFilterBar, type LayerFilter,
} from './DashComponents';

// ─── 示例数据（真实环境通过 API 加载）────────────────────────────────────────

const DEMO_HIERARCHY: HierarchyNode = {
  id: 'root', name: '国有集团', type: 'group', risk: 'medium',
  children: [
    {
      id: 'region-east', name: '华东大区', type: 'region', risk: 'low',
      children: [
        { id: 'entity-1', name: '华东子公司A', type: 'entity', risk: 'low' },
        { id: 'entity-2', name: '华东子公司B', type: 'entity', risk: 'high' },
      ],
    },
    {
      id: 'region-west', name: '华西大区', type: 'region', risk: 'medium',
      children: [
        { id: 'entity-3', name: '华西子公司C', type: 'entity', risk: 'medium' },
        { id: 'entity-4', name: '华西子公司D', type: 'entity', risk: 'none' },
      ],
    },
  ],
};

const DEMO_NETWORK_NODES: NetworkNode[] = [
  { id: 'entity-2', label: '华东子公司B', type: 'entity', risk: 'high' },
  { id: 'acct-1', label: 'ACC-2024-001', type: 'account', risk: 'high' },
  { id: 'acct-2', label: 'ACC-2024-002', type: 'account', risk: 'medium' },
  { id: 'acct-3', label: 'ACC-2024-003', type: 'account', risk: 'none' },
];

const DEMO_NETWORK_LINKS: NetworkLink[] = [
  { source: 'entity-2', target: 'acct-1' },
  { source: 'entity-2', target: 'acct-2' },
  { source: 'entity-2', target: 'acct-3' },
];

// ─── 看板主组件 ───────────────────────────────────────────────────────────────

interface DashboardProps {
  onDataLoad?: () => void;
  onDataError?: () => void;
}

export default function Dashboard({ onDataLoad, onDataError }: DashboardProps) {
  const [lang, setLang] = useState<Lang>('zh');
  const [layer, setLayer] = useState<LayerFilter>('all');
  const [selectedNode, setSelectedNode] = useState<HudNode | null>(null);
  const [showForce, setShowForce] = useState(false);
  const [drillPath] = useState<Array<{ step: number; node_iri: string; node_type: string; node_label: string | null }>>([]);

  // 数据加载成功/失败回调
  useEffect(() => {
    if (onDataLoad) onDataLoad();
  }, [onDataLoad]);

  // 从 JWT 解析 tenant_id（简单 base64 解码）
  const [tenantId, setTenantId] = useState<string | null>(null);
  useEffect(() => {
    const token = getToken();
    if (!token) return;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setTenantId(payload.tenant_id ?? null);
    } catch { /* 忽略解析错误 */ }
  }, []);

  const { events, status } = useRiskEvents(tenantId);

  const wsStatusColor = { connecting: 'var(--warn)', connected: 'var(--success)', disconnected: 'var(--danger)' }[status];

  function handleHierarchyNodeClick(node: HierarchyNode) {
    setSelectedNode({
      id: node.id, label: node.name, type: node.type, risk: node.risk,
      properties: { ID: node.id, 风险等级: node.risk, 类型: node.type },
    });
    if (node.type === 'entity') setShowForce(true);
  }

  function handleNetworkNodeClick(node: NetworkNode) {
    setSelectedNode({
      id: node.id, label: node.label, type: node.type, risk: node.risk,
      properties: { ID: node.id, 风险等级: node.risk, 类型: node.type },
    });
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg)' }}>
      {/* Topbar — 10.1 */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 20px', background: 'rgba(17,24,39,0.9)',
        borderBottom: '1px solid var(--border)', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ color: 'var(--gold)', fontWeight: 700, fontSize: '15px', letterSpacing: '0.1em' }}>
            DRP
          </div>
          <div style={{ color: 'var(--text)', fontSize: '13px' }}>{t(lang, 'title')}</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <LayerFilterBar active={layer} lang={lang} onChange={setLayer} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: wsStatusColor }} />
            <span style={{ color: wsStatusColor }}>{t(lang, status)}</span>
          </div>
          <button
            onClick={() => setLang(l => l === 'zh' ? 'en' : 'zh')}
            style={{
              background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)',
              color: 'var(--text)', borderRadius: '4px', padding: '4px 10px',
              fontSize: '12px', cursor: 'pointer',
            }}
          >
            {t(lang, 'lang')}
          </button>
        </div>
      </header>

      {/* 主体区域 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：层级树 */}
        <aside style={{
          width: '320px', flexShrink: 0,
          background: 'rgba(17,24,39,0.7)', borderRight: '1px solid var(--border)',
          padding: '16px', overflowY: 'auto',
        }}>
          <div style={{ marginBottom: '12px', fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
            集团层级视图
          </div>
          <HierarchyGraph
            data={DEMO_HIERARCHY}
            width={280}
            height={360}
            onNodeClick={handleHierarchyNodeClick}
          />
          {/* 风险图例 */}
          <div style={{ marginTop: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {(['none', 'low', 'medium', 'high'] as const).map(r => (
              <div key={r} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: { none: 'var(--accent)', low: 'var(--success)', medium: 'var(--warn)', high: 'var(--danger)' }[r] }} />
                <span style={{ color: 'var(--text-muted)' }}>{r}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* 中央：图谱区 */}
        <main style={{ flex: 1, position: 'relative', overflow: 'hidden', padding: '16px' }}>
          <div style={{
            position: 'absolute', inset: 0,
            background: 'radial-gradient(circle at 50% 50%, rgba(59,130,246,0.03) 0%, transparent 70%)',
          }} />

          {showForce ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowForce(false)}
                style={{
                  position: 'absolute', top: 0, left: 0, zIndex: 10,
                  background: 'rgba(59,130,246,0.2)', border: '1px solid var(--accent)',
                  color: 'var(--accent)', borderRadius: '4px', padding: '4px 10px',
                  fontSize: '12px', cursor: 'pointer',
                }}
              >
                ← 返回层级图
              </button>
              <ForceGraph
                nodes={DEMO_NETWORK_NODES}
                links={DEMO_NETWORK_LINKS}
                width={600}
                height={400}
                onNodeClick={handleNetworkNodeClick}
              />
            </div>
          ) : (
            <HierarchyGraph
              data={DEMO_HIERARCHY}
              width={700}
              height={480}
              onNodeClick={handleHierarchyNodeClick}
            />
          )}

          {/* HUD 浮窗 */}
          {selectedNode && (
            <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 50 }}>
              <HudPanel
                node={selectedNode}
                lang={lang}
                onClose={() => setSelectedNode(null)}
              />
            </div>
          )}
        </main>

        {/* 右侧：检查器 */}
        <DrillInspector drillPath={drillPath} lang={lang} />
      </div>

      {/* 底部 Ticker */}
      <RiskTicker events={events} lang={lang} />
    </div>
  );
}
