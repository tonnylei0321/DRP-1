/**
 * 10.7 WebSocket 客户端 — 订阅风险事件流，驱动节点状态更新
 */
import { useEffect, useRef, useState } from 'react';

export interface RiskEvent {
  type: 'risk_event';
  tenant_id: string;
  indicator_id: string;
  indicator_name: string;
  domain: string;
  value: number | null;
  target_value: number | null;
  threshold: number | null;
  timestamp?: string;
}

type WsStatus = 'connecting' | 'connected' | 'disconnected';

const WS_URL = (import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000') + '/ws/risk-events';

export function useRiskEvents(tenantId: string | null) {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [status, setStatus] = useState<WsStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!tenantId) return;

    setStatus('connecting');
    const ws = new WebSocket(`${WS_URL}?tenant_id=${tenantId}`);
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');
    ws.onclose = () => setStatus('disconnected');
    ws.onerror = () => setStatus('disconnected');
    ws.onmessage = evt => {
      try {
        const data = JSON.parse(evt.data) as RiskEvent;
        if (data.type === 'risk_event') {
          setEvents(prev => [{ ...data, timestamp: new Date().toISOString() }, ...prev].slice(0, 200));
        }
      } catch {
        // 忽略非法消息
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [tenantId]);

  return { events, status };
}
