/**
 * 10.7 WebSocket 客户端 — 订阅风险事件流，驱动节点状态更新
 * 支持指数退避重连策略
 */
import { useCallback, useEffect, useRef, useState } from 'react';

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

export type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

/** 认证失败关闭码，不触发重连 */
const AUTH_FAILURE_CODE = 4401;
/** 初始重连间隔（毫秒） */
const INITIAL_RETRY_INTERVAL = 1000;
/** 最大重连间隔（毫秒） */
const MAX_RETRY_INTERVAL = 30000;
/** 最大重试次数 */
const MAX_RETRIES = 5;

const WS_URL = (import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000') + '/ws/risk-events';

export function useRiskEvents(tenantId: string | null) {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [status, setStatus] = useState<WsStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback((tid: string) => {
    setStatus(retryCountRef.current > 0 ? 'reconnecting' : 'connecting');
    const ws = new WebSocket(`${WS_URL}?tenant_id=${tid}`);
    wsRef.current = ws;

    ws.onopen = () => {
      retryCountRef.current = 0;
      setStatus('connected');
    };

    ws.onclose = (evt: CloseEvent) => {
      wsRef.current = null;
      // 认证失败不重连
      if (evt.code === AUTH_FAILURE_CODE) {
        setStatus('disconnected');
        return;
      }
      // 尝试重连
      if (retryCountRef.current < MAX_RETRIES) {
        const delay = Math.min(
          INITIAL_RETRY_INTERVAL * Math.pow(2, retryCountRef.current),
          MAX_RETRY_INTERVAL,
        );
        retryCountRef.current += 1;
        setStatus('reconnecting');
        retryTimerRef.current = setTimeout(() => {
          connect(tid);
        }, delay);
      } else {
        setStatus('disconnected');
      }
    };

    ws.onerror = () => {
      // onerror 之后浏览器会自动触发 onclose，重连逻辑在 onclose 中处理
    };

    ws.onmessage = (evt: MessageEvent) => {
      try {
        const data = JSON.parse(evt.data) as RiskEvent;
        if (data.type === 'risk_event') {
          setEvents(prev => [{ ...data, timestamp: new Date().toISOString() }, ...prev].slice(0, 200));
        }
      } catch {
        // 忽略非法消息
      }
    };
  }, []);

  useEffect(() => {
    // 清理旧连接和定时器
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // 防止触发重连
      wsRef.current.close();
      wsRef.current = null;
    }
    retryCountRef.current = 0;

    // 切换 tenantId 时清空 events
    setEvents([]);

    if (!tenantId) {
      setStatus('disconnected');
      return;
    }

    connect(tenantId);

    return () => {
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // 防止触发重连
        wsRef.current.close();
        wsRef.current = null;
      }
      retryCountRef.current = 0;
    };
  }, [tenantId, connect]);

  return { events, status };
}
