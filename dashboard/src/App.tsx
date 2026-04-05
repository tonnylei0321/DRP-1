/**
 * DRP 监管大屏 — 基于原型的三栏布局
 * 左：风险事件流 | 中：D3力导向图 | 右：WarRoom审查器
 */
import { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { getToken, clearToken } from './api/client';
import { RiskEventWebSocket, type RiskEventResponse } from './api/riskEventApi';
import LoginPanel from './pages/LoginPanel';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');
  const [riskEvents, setRiskEvents] = useState<RiskEventResponse[]>([]);
  const wsRef = useRef<RiskEventWebSocket | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    // 尝试加载真实数据
    fetch(`${BASE_URL}/risk-events`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then((data: RiskEventResponse[]) => { if (Array.isArray(data)) setRiskEvents(data); })
      .catch(() => setRiskEvents([]));

    // WebSocket
    wsRef.current = new RiskEventWebSocket(BASE_URL);
    wsRef.current.onEvent((e) => {
      setRiskEvents(prev => [e, ...prev.filter(p => p.id !== e.id)].slice(0, 30));
    });
    wsRef.current.connect(token);
    setWsStatus('connected');

    return () => { wsRef.current?.disconnect(); };
  }, [loggedIn]);

  // D3 力导向图初始化
  useEffect(() => {
    const container = document.getElementById('canvas-container');
    if (!container) return;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const svg = d3.select('#viz-canvas')
      .attr('viewBox', [0, 0, width, height]);

    const data = {
      nodes: [
        { id: 'Root', type: 'Entity', group: 1, label: '华北子公司 B', r: 25 },
        { id: 'Acc1', type: 'Account', group: 2, label: 'ICBC 8892', r: 15 },
        { id: 'Acc2', type: 'Account', group: 2, label: 'BOC 4410', r: 15 },
        { id: 'Person1', type: 'Person', group: 3, label: '法定代表人', r: 12 },
        { id: 'Contract1', type: 'Doc', group: 4, label: '授信合同', r: 10 },
      ],
      links: [
        { source: 'Root', target: 'Acc1', label: 'holdsAccount' },
        { source: 'Root', target: 'Acc2', label: 'holdsAccount' },
        { source: 'Root', target: 'Person1', label: 'hasSignatory' },
        { source: 'Acc1', target: 'Contract1', label: 'collateral' },
      ],
    };

    const simulation = d3.forceSimulation(data.nodes as any)
      .force('link', d3.forceLink(data.links as any).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g')
      .attr('stroke', 'rgba(0, 216, 255, 0.2)')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke-width', 1.5);

    const node = svg.append('g')
      .selectAll('g')
      .data(data.nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event: any, d: any) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (event: any, d: any) => { d.fx = event.x; d.fy = event.y; })
        .on('end', (event: any, d: any) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append('circle')
      .attr('r', (d: any) => d.r)
      .attr('fill', (d: any) => d.group === 1 ? '#00d8ff' : d.group === 2 ? '#a855f7' : '#0c2038')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    node.append('text')
      .text((d: any) => d.label)
      .attr('x', (d: any) => d.r + 5)
      .attr('y', 5)
      .attr('fill', '#cde8f8')
      .style('font-size', '12px');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });
  }, [loggedIn]);

  function handleLogout() { clearToken(); setLoggedIn(false); }
  function handleLogin() { setLoggedIn(true); setWsStatus('connected'); }

  if (!loggedIn) return <LoginPanel onLogin={handleLogin} />;

  const statusColor = wsStatus === 'connected' ? '#00ffb3' : wsStatus === 'connecting' ? '#ffaa00' : '#ff2020';
  const statusLabel = wsStatus === 'connected' ? 'CONNECTED' : wsStatus === 'connecting' ? 'CONNECTING' : 'OFFLINE';

  return (
    <div id="app">
      {/* 顶部导航 */}
      <header>
        <div className="logo">DRP // VANGUARD OMNIS</div>
        <div className="status-bar">
          <span>ONTOLOGY: <b style={{ color: '#00d8ff' }}>{wsStatus === 'connected' ? 'CONNECTED' : 'OFFLINE'}</b></span>
          <span>SPARQL ENGINE: <b style={{ color: '#00ffb3' }}>ACTIVE</b></span>
          <span>TENANT: <b style={{ color: '#cde8f8' }}>SASAC_HQ_01</b></span>
        </div>
      </header>

      {/* 三栏主体 */}
      <div id="main">
        {/* 左侧：风险事件流 */}
        <aside id="sidebar-left">
          <div className="section-title">
            <span>106 监管指标实时流</span>
            <span style={{ color: '#ff2020' }}>{riskEvents.length} ALERTS</span>
          </div>
          <div className="indicator-list" id="event-stream">
            {riskEvents.length === 0 && (
              <div style={{ padding: '20px', textAlign: 'center', color: '#6aafc8', fontFamily: 'Share Tech Mono, monospace', fontSize: '11px' }}>
                暂无告警事件
              </div>
            )}
            {riskEvents.map((evt, i) => {
              const borderColor = evt.level === 'CRITICAL' ? '#ff2020' : evt.level === 'WARN' ? '#ffaa00' : '#22d3ee';
              return (
                <div key={evt.id} className="risk-event" style={{ borderLeftColor: borderColor, animation: i === 0 ? 'pulse 2s infinite' : undefined }}>
                  <div className="event-title" style={{ color: borderColor }}>{evt.indicatorName}</div>
                  <div className="event-meta">ID: {evt.indicatorId} | 实体: {evt.entityName}</div>
                  <div className="event-meta">SHACL_REASON: {evt.level === 'CRITICAL' ? '连续3周期红线突破' : evt.level === 'WARN' ? '接近红线预警' : '持续监控'}</div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* 中央：D3力导向图 */}
        <section id="canvas-container">
          <div id="canvas-overlay">
            <div className="breadcrumb">GLOBAL &gt; NORTH_CHINA &gt; ENTITY_B &gt; ACCOUNTS</div>
            <h2 id="view-title">穿透式拓扑视图</h2>
          </div>
          <svg id="viz-canvas" width="100%" height="100%" />
        </section>

        {/* 右侧：WarRoom审查器 */}
        <aside id="sidebar-right">
          <div className="section-title">WAR ROOM INSPECTOR</div>
          <div className="detail-card" id="detail-panel">
            <div className="fibo-tag">FIBO:LegalPerson</div>
            <h3 style={{ color: '#cde8f8', marginBottom: '5px', fontSize: '14px' }}>华北子公司 B (二级法人)</h3>
            <p style={{ fontSize: '11px', opacity: 0.8 }}>所属区域：华北大区 | 穿透深度：Level 2</p>

            <div className="metric-grid">
              <div className="metric-box">
                <div className="metric-label">授信占用率</div>
                <div className="metric-value">92.4%</div>
              </div>
              <div className="metric-box">
                <div className="metric-label">LCR 覆盖率</div>
                <div className="metric-value" style={{ color: '#ff2020' }}>108%</div>
              </div>
              <div className="metric-box">
                <div className="metric-label">直联率</div>
                <div className="metric-value">96.8%</div>
              </div>
              <div className="metric-box">
                <div className="metric-label">资金集中率</div>
                <div className="metric-value">87.6%</div>
              </div>
            </div>

            <div style={{ marginTop: '20px' }}>
              <div className="section-title" style={{ background: 'none', padding: '0 0 8px 0', border: 'none' }}>底层账户穿透 (DRILLED)</div>
              <div className="path-node">
                <div className="fibo-tag" style={{ background: '#a855f7', color: '#fff' }}>CTIO:DirectLinkAccount</div>
                <div style={{ color: '#cde8f8', fontSize: '13px' }}>工商银行北京分行 - 结算户</div>
                <div className="event-meta">ACCOUNT: 6222 **** **** 8892</div>
                <div className="event-meta" style={{ color: '#00d8ff' }}>BALANCE: ¥128,440,000.00</div>
              </div>
              <div className="path-node">
                <div className="fibo-tag" style={{ background: '#ffd060', color: '#000' }}>CTIO:BillAccount</div>
                <div style={{ color: '#cde8f8', fontSize: '13px' }}>电子商业汇票池 - 存本</div>
                <div className="event-meta">NODE_ID: GRAPH-ND-992</div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* 底部状态栏 */}
      <footer>
        <span id="sys-time">SYSTEM_TIME: {new Date().toISOString().replace('T', ' ').slice(0, 19)} UTC</span>
        <span style={{ marginLeft: '20px' }}>ENGINE: Ontotext GraphDB 10.5</span>
        <span style={{ marginLeft: 'auto' }}>PROPRIETARY DATA: CONFIDENTIAL</span>
      </footer>
    </div>
  );
}
