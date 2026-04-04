/**
 * CTIO RiskEvent API
 * 获取风险事件列表 + WebSocket 实时推送
 */
import { request } from './client';
import type { RiskLevel } from '../components/RiskDispositionQueue';

export type RiskEventStatus = 'pending' | 'in_progress' | 'resolved';

export interface RiskEventResponse {
  id: string;
  level: RiskLevel;
  entityId: string;         // 关联实体ID
  entityName: string;      // 企业/节点名称
  indicatorId: string;     // 触发指标编号
  indicatorName: string;   // 触发指标名称
  currentValue: number;    // 当前值
  threshold: number;      // 红线/预警阈值
  unit: string;           // 单位
  triggeredAt: string;     // 触发时间 ISO8601
  deadline?: string;       // 整改期限（仅WARN）
  status: RiskEventStatus;
}

/** 获取全部风险事件（按严重等级和时间排序） */
export async function fetchRiskEvents(): Promise<RiskEventResponse[]> {
  return request<RiskEventResponse[]>('GET', '/risk-events');
}

/** 获取指定级别的风险事件 */
export async function fetchRiskEventsByLevel(level: RiskLevel): Promise<RiskEventResponse[]> {
  return request<RiskEventResponse[]>('GET', `/risk-events?level=${level}`);
}

/** 更新风险事件状态 */
export async function updateRiskEventStatus(
  id: string,
  status: RiskEventStatus
): Promise<RiskEventResponse> {
  return request<RiskEventResponse>('PATCH', `/risk-events/${id}`, { status });
}

// ============================================================================
// WebSocket 实时推送
// ============================================================================

export type RiskEventHandler = (event: RiskEventResponse) => void;

export class RiskEventWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Set<RiskEventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url: string;

  constructor(url: string) {
    const wsUrl = url.startsWith('ws') ? url : url.replace('http', 'ws');
    this.url = wsUrl;
  }

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${this.url}/ws/risk-events?token=${token}`);

    this.ws.onopen = () => {
      console.log('[RiskEventWebSocket] Connected');
    };

    this.ws.onmessage = (evt) => {
      try {
        const event: RiskEventResponse = JSON.parse(evt.data);
        this.handlers.forEach(h => h(event));
      } catch (e) {
        console.error('[RiskEventWebSocket] Parse error:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('[RiskEventWebSocket] Disconnected, reconnecting in 5s...');
      this.reconnectTimer = setTimeout(() => this.connect(token), 5000);
    };

    this.ws.onerror = (err) => {
      console.error('[RiskEventWebSocket] Error:', err);
    };
  }

  onEvent(handler: RiskEventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
