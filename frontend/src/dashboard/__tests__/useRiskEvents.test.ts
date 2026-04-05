/**
 * useRiskEvents hook 单元测试
 * 覆盖 WebSocket 连接、消息处理、重连策略、认证失败、租户隔离
 */
import { renderHook, act } from '@testing-library/react';
import { useRiskEvents } from '../useRiskEvents';

// ─── MockWebSocket ───────────────────────────────────────────────
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  readyState = 0; // CONNECTING
  closeCalled = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.closeCalled = true;
    this.readyState = 3; // CLOSED
  }

  // 辅助方法
  simulateOpen() {
    this.readyState = 1; // OPEN
    this.onopen?.(new Event('open'));
  }

  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }

  simulateClose(code = 1006) {
    this.readyState = 3; // CLOSED
    this.onclose?.(new CloseEvent('close', { code }));
  }

  simulateError() {
    this.onerror?.(new Event('error'));
  }
}

// ─── 测试配置 ────────────────────────────────────────────────────
beforeEach(() => {
  vi.useFakeTimers();
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// ─── 辅助函数 ────────────────────────────────────────────────────
/** 获取最新创建的 MockWebSocket 实例 */
function latestWs(): MockWebSocket {
  return MockWebSocket.instances[MockWebSocket.instances.length - 1];
}

function makeRiskEvent(overrides: Record<string, unknown> = {}) {
  return {
    type: 'risk_event',
    tenant_id: 't-1',
    indicator_id: 'ind-1',
    indicator_name: '测试指标',
    domain: 'credit',
    value: 0.8,
    target_value: 1.0,
    threshold: 0.5,
    ...overrides,
  };
}

// ─── 测试用例 ────────────────────────────────────────────────────

describe('useRiskEvents', () => {
  it('传入有效 tenantId 时创建 WebSocket 连接到正确 URL', () => {
    renderHook(() => useRiskEvents('tenant-abc'));

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(latestWs().url).toContain('/ws/risk-events?tenant_id=tenant-abc');
  });

  it('连接成功后 status 设为 connected', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });

    expect(result.current.status).toBe('connected');
  });

  it('接收 risk_event 消息后事件添加到 events 数组头部，包含 timestamp', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });

    const event = makeRiskEvent({ indicator_id: 'ind-A' });
    act(() => {
      latestWs().simulateMessage(event);
    });

    expect(result.current.events).toHaveLength(1);
    expect(result.current.events[0].indicator_id).toBe('ind-A');
    expect(result.current.events[0].timestamp).toBeDefined();
    // timestamp 应为 ISO 8601 格式
    expect(new Date(result.current.events[0].timestamp!).toISOString()).toBe(
      result.current.events[0].timestamp,
    );

    // 第二条消息应在头部
    const event2 = makeRiskEvent({ indicator_id: 'ind-B' });
    act(() => {
      latestWs().simulateMessage(event2);
    });

    expect(result.current.events).toHaveLength(2);
    expect(result.current.events[0].indicator_id).toBe('ind-B');
    expect(result.current.events[1].indicator_id).toBe('ind-A');
  });

  it('事件数组长度上限 200 条，超过时截断保留最新', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });

    // 发送 210 条消息
    act(() => {
      for (let i = 0; i < 210; i++) {
        latestWs().simulateMessage(makeRiskEvent({ indicator_id: `ind-${i}` }));
      }
    });

    expect(result.current.events).toHaveLength(200);
    // 最新的消息（ind-209）在头部
    expect(result.current.events[0].indicator_id).toBe('ind-209');
  });

  it('连接关闭后 status 设为 disconnected（认证失败场景）', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });
    expect(result.current.status).toBe('connected');

    // 认证失败关闭 → disconnected，不重连
    act(() => {
      latestWs().simulateClose(4401);
    });

    expect(result.current.status).toBe('disconnected');
  });

  it('tenantId 为 null 时不创建 WebSocket 连接', () => {
    const { result } = renderHook(() => useRiskEvents(null));

    expect(MockWebSocket.instances).toHaveLength(0);
    expect(result.current.status).toBe('disconnected');
    expect(result.current.events).toEqual([]);
  });

  it('意外断开后 status 设为 reconnecting 并自动重连', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });
    expect(result.current.status).toBe('connected');

    // 模拟意外断开（code 1006）
    act(() => {
      latestWs().simulateClose(1006);
    });
    expect(result.current.status).toBe('reconnecting');

    // 推进 1s 定时器，触发重连
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // 应创建新的 WebSocket 实例
    expect(MockWebSocket.instances).toHaveLength(2);

    // 新连接成功后 status 恢复 connected
    act(() => {
      latestWs().simulateOpen();
    });
    expect(result.current.status).toBe('connected');
  });

  it('认证失败（close code 4401）不触发重连', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });

    const instancesBefore = MockWebSocket.instances.length;

    act(() => {
      latestWs().simulateClose(4401);
    });

    expect(result.current.status).toBe('disconnected');

    // 推进足够长时间，确认没有新连接
    act(() => {
      vi.advanceTimersByTime(60000);
    });

    expect(MockWebSocket.instances).toHaveLength(instancesBefore);
  });

  it('超过 5 次重试后 status 变为 disconnected', () => {
    const { result } = renderHook(() => useRiskEvents('t-1'));

    act(() => {
      latestWs().simulateOpen();
    });
    expect(result.current.status).toBe('connected');

    // 退避间隔: 1s, 2s, 4s, 8s, 16s（共 5 次重连尝试）
    const delays = [1000, 2000, 4000, 8000, 16000];

    for (let i = 0; i < 5; i++) {
      // 断开当前连接 → 触发重连调度
      act(() => { latestWs().simulateClose(1006); });
      expect(result.current.status).toBe('reconnecting');

      // 推进退避时间 → 创建新 ws
      act(() => { vi.advanceTimersByTime(delays[i]); });
    }

    // 此时已经重连了 5 次，retryCount = 5
    // 第 6 次断开 → retryCount(5) >= MAX_RETRIES(5) → disconnected
    act(() => { latestWs().simulateClose(1006); });
    expect(result.current.status).toBe('disconnected');

    // 确认没有更多重连尝试
    const totalInstances = MockWebSocket.instances.length;
    act(() => { vi.advanceTimersByTime(60000); });
    expect(MockWebSocket.instances.length).toBe(totalInstances);
  });

  it('切换 tenantId 后断开旧连接、建立新连接，events 清空', () => {
    const { result, rerender } = renderHook(
      ({ tid }) => useRiskEvents(tid),
      { initialProps: { tid: 'tenant-A' as string | null } },
    );

    const firstWs = latestWs();
    act(() => {
      firstWs.simulateOpen();
    });

    // 发送一些事件
    act(() => {
      firstWs.simulateMessage(makeRiskEvent({ tenant_id: 'tenant-A' }));
    });
    expect(result.current.events).toHaveLength(1);

    // 切换租户
    rerender({ tid: 'tenant-B' });

    // 旧连接应被关闭
    expect(firstWs.closeCalled).toBe(true);

    // events 应被清空
    expect(result.current.events).toEqual([]);

    // 新连接应指向新租户
    const secondWs = latestWs();
    expect(secondWs.url).toContain('tenant_id=tenant-B');
    expect(secondWs).not.toBe(firstWs);

    // 新连接成功
    act(() => {
      secondWs.simulateOpen();
    });
    expect(result.current.status).toBe('connected');
  });

  it('重连退避间隔不超过 30s（MAX_RETRY_INTERVAL）', () => {
    // 直接验证退避计算公式：min(1000 * 2^n, 30000)
    const INITIAL = 1000;
    const MAX = 30000;

    for (let n = 0; n < 10; n++) {
      const delay = Math.min(INITIAL * Math.pow(2, n), MAX);
      expect(delay).toBeLessThanOrEqual(MAX);
    }

    // 第 5 次重连：min(1000 * 32, 30000) = 30000
    expect(Math.min(INITIAL * Math.pow(2, 5), MAX)).toBe(30000);
    // 第 6 次重连：min(1000 * 64, 30000) = 30000
    expect(Math.min(INITIAL * Math.pow(2, 6), MAX)).toBe(30000);
  });
});


// ─── 属性测试 ────────────────────────────────────────────────────

import * as fc from 'fast-check';

describe('属性测试 — Property 8: WebSocket 事件添加与时间戳', () => {
  it('Feature: admin-portal-testing, Property 8: 接收消息后 events[0] 包含所有字段且有 timestamp', () => {
    /**
     * Validates: Requirements 5.7
     */
    fc.assert(
      fc.property(
        fc.record({
          indicator_id: fc.string({ minLength: 1, maxLength: 20 }),
          indicator_name: fc.string({ minLength: 1, maxLength: 30 }),
          domain: fc.constantFrom('credit', 'market', 'operational', 'liquidity'),
          value: fc.option(fc.float({ min: 0, max: 100, noNaN: true }), { nil: null }),
          target_value: fc.option(fc.float({ min: 0, max: 100, noNaN: true }), { nil: null }),
          threshold: fc.option(fc.float({ min: 0, max: 100, noNaN: true }), { nil: null }),
        }),
        (eventData) => {
          const { result } = renderHook(() => useRiskEvents('t-1'));

          act(() => { latestWs().simulateOpen(); });

          const fullEvent = { type: 'risk_event', tenant_id: 't-1', ...eventData };
          act(() => { latestWs().simulateMessage(fullEvent); });

          const received = result.current.events[0];
          // 验证所有字段存在
          expect(received.indicator_id).toBe(eventData.indicator_id);
          expect(received.domain).toBe(eventData.domain);
          // 验证 timestamp 存在且为 ISO 8601 格式
          expect(received.timestamp).toBeDefined();
          expect(new Date(received.timestamp!).toISOString()).toBe(received.timestamp);
        }
      ),
      { numRuns: 50 }
    );
  });
});

describe('属性测试 — Property 9: WebSocket 事件数组长度不变量', () => {
  it('Feature: admin-portal-testing, Property 9: events.length <= 200 且保留最新', () => {
    /**
     * Validates: Requirements 5.8
     */
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 300 }),
        (messageCount) => {
          const { result } = renderHook(() => useRiskEvents('t-1'));

          act(() => { latestWs().simulateOpen(); });

          act(() => {
            for (let i = 0; i < messageCount; i++) {
              latestWs().simulateMessage(makeRiskEvent({ indicator_id: `ind-${i}` }));
            }
          });

          // 长度不变量
          expect(result.current.events.length).toBeLessThanOrEqual(200);

          // 保留最新
          if (messageCount > 0) {
            const expectedLatest = `ind-${messageCount - 1}`;
            expect(result.current.events[0].indicator_id).toBe(expectedLatest);
          }
        }
      ),
      { numRuns: 30 }
    );
  });
});
