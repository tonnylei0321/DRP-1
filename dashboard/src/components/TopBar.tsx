/**
 * TopBar — 顶部栏：Logo + 状态
 */
import { useEffect, useState } from 'react';

interface TopBarProps {
  onLogout: () => void;
}

export default function TopBar({ onLogout }: TopBarProps) {
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');

  useEffect(() => {
    const t = setTimeout(() => setWsStatus('connected'), 1500);
    return () => clearTimeout(t);
  }, []);

  const statusColor = { connected: '#00ffb3', connecting: '#ffaa00', disconnected: '#ff2020' }[wsStatus];
  const statusLabel = { connected: 'CONNECTED', connecting: 'CONNECTING', disconnected: 'OFFLINE' }[wsStatus];

  return (
    <header>
      <div className="logo">DRP // VANGUARD OMNIS</div>
      <div className="status-bar">
        <span>ONTOLOGY: <b style={{ color: '#00d8ff' }}>{wsStatus === 'connected' ? 'CONNECTED' : 'OFFLINE'}</b></span>
        <span>SPARQL ENGINE: <b style={{ color: '#00ffb3' }}>ACTIVE</b></span>
        <span>TENANT: <b style={{ color: '#cde8f8' }}>SASAC_HQ_01</b></span>
        <span style={{ color: statusColor }}>▊ {statusLabel}</span>
      </div>
    </header>
  );
}
