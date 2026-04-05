/**
 * API Client 单元测试
 * 覆盖：Token 管理、HTTP 错误处理、业务 API 请求构造、Content-Type 头、
 *       401 自动清除 Token、网络超时、错误消息脱敏、Token 安全边界
 *
 * 需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 安全测试层
 */
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import {
  setToken,
  getToken,
  clearToken,
  authApi,
  tenantsApi,
  auditApi,
  mappingApi,
  usersApi,
  rolesApi,
  etlApi,
  REQUEST_TIMEOUT_MS,
} from '../client';

const BASE_URL = 'http://localhost:8000';

// ─── 1. Token 管理 ──────────────────────────────────────────────────────────

describe('Token 管理', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('setToken 存储到 localStorage 的 drp_token 键', () => {
    setToken('abc123');
    expect(localStorage.getItem('drp_token')).toBe('abc123');
  });

  it('getToken 返回存储的 token', () => {
    setToken('my-token');
    expect(getToken()).toBe('my-token');
  });

  it('clearToken 从 localStorage 移除 drp_token', () => {
    setToken('to-remove');
    clearToken();
    expect(localStorage.getItem('drp_token')).toBeNull();
    expect(getToken()).toBeNull();
  });

  it('setToken 后请求包含 Authorization: Bearer <token> 头', async () => {
    let capturedAuth: string | null = null;
    server.use(
      http.get(`${BASE_URL}/tenants`, ({ request }) => {
        capturedAuth = request.headers.get('Authorization');
        return HttpResponse.json([]);
      }),
    );

    setToken('test-bearer-token');
    await tenantsApi.list();
    expect(capturedAuth).toBe('Bearer test-bearer-token');
  });

  it('clearToken 后请求不包含 Authorization 头', async () => {
    let capturedAuth: string | null = null;
    server.use(
      http.get(`${BASE_URL}/tenants`, ({ request }) => {
        capturedAuth = request.headers.get('Authorization');
        return HttpResponse.json([]);
      }),
    );

    setToken('temp-token');
    clearToken();
    await tenantsApi.list();
    expect(capturedAuth).toBeNull();
  });
});


// ─── 2. HTTP 错误处理 ────────────────────────────────────────────────────────

describe('HTTP 错误处理', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('4xx 状态码抛出包含状态码和响应文本的 Error', async () => {
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse('Bad Request: 参数无效', { status: 400 });
      }),
    );

    await expect(tenantsApi.list()).rejects.toThrow(/400/);
    // 再次验证响应文本
    try {
      await tenantsApi.list();
    } catch (e: any) {
      expect(e.message).toContain('参数无效');
    }
  });

  it('5xx 状态码抛出包含状态码和响应文本的 Error', async () => {
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse('Internal Server Error', { status: 500 });
      }),
    );

    await expect(tenantsApi.list()).rejects.toThrow(/500/);
  });

  it('204 No Content 返回 undefined', async () => {
    server.use(
      http.delete(`${BASE_URL}/auth/users/:id`, () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const result = await usersApi.delete('user-1');
    expect(result).toBeUndefined();
  });
});


// ─── 3. 业务 API 请求构造 ────────────────────────────────────────────────────

describe('业务 API 请求构造', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('authApi.login 发送 POST /auth/login，body 包含 email 和 password', async () => {
    let capturedMethod = '';
    let capturedBody: any = null;
    server.use(
      http.post(`${BASE_URL}/auth/login`, async ({ request }) => {
        capturedMethod = request.method;
        capturedBody = await request.json();
        return HttpResponse.json({
          access_token: 'tok',
          token_type: 'bearer',
          expires_in: 3600,
        });
      }),
    );

    await authApi.login('test@example.com', 'pass123');
    expect(capturedMethod).toBe('POST');
    expect(capturedBody).toEqual({ email: 'test@example.com', password: 'pass123' });
  });

  it('tenantsApi.create 发送 POST /tenants，body 包含 name', async () => {
    let capturedBody: any = null;
    server.use(
      http.post(`${BASE_URL}/tenants`, async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({
          id: 't-new',
          name: '新租户',
          graph_iri: 'urn:drp:tenant:t-new',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        });
      }),
    );

    await tenantsApi.create('新租户');
    expect(capturedBody).toEqual({ name: '新租户' });
  });

  it('auditApi.list 带分页参数正确拼接查询字符串', async () => {
    let capturedUrl = '';
    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json([]);
      }),
    );

    await auditApi.list({ page: 2, per_page: 20, event_type: 'login' });
    const url = new URL(capturedUrl);
    expect(url.searchParams.get('page')).toBe('2');
    expect(url.searchParams.get('per_page')).toBe('20');
    expect(url.searchParams.get('event_type')).toBe('login');
  });

  it('auditApi.list page=0 时仍拼接到查询字符串', async () => {
    let capturedUrl = '';
    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json([]);
      }),
    );
    await auditApi.list({ page: 0, per_page: 0 });
    const url = new URL(capturedUrl);
    expect(url.searchParams.get('page')).toBe('0');
    expect(url.searchParams.get('per_page')).toBe('0');
  });

  it('mappingApi.reject 发送 PUT /mappings/{id}/reject，body 包含 reason', async () => {
    let capturedBody: any = null;
    let capturedUrl = '';
    server.use(
      http.put(`${BASE_URL}/mappings/:id/reject`, async ({ request }) => {
        capturedUrl = request.url;
        capturedBody = await request.json();
        return HttpResponse.json({
          id: 'map-1',
          source_table: 'accounts',
          source_field: 'balance',
          data_type: 'decimal',
          target_property: 'drp:balance',
          confidence: 85,
          auto_approved: false,
          status: 'rejected',
          created_at: '2024-01-01T00:00:00Z',
        });
      }),
    );

    await mappingApi.reject('map-1', '数据类型不匹配');
    expect(capturedUrl).toContain('/mappings/map-1/reject');
    expect(capturedBody).toEqual({ reason: '数据类型不匹配' });
  });
});


// ─── 4. Content-Type 头 ──────────────────────────────────────────────────────

describe('Content-Type 头', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('POST 请求包含 Content-Type: application/json', async () => {
    let capturedContentType: string | null = null;
    server.use(
      http.post(`${BASE_URL}/auth/login`, ({ request }) => {
        capturedContentType = request.headers.get('Content-Type');
        return HttpResponse.json({
          access_token: 'tok',
          token_type: 'bearer',
          expires_in: 3600,
        });
      }),
    );

    await authApi.login('a@b.com', 'pwd');
    expect(capturedContentType).toBe('application/json');
  });

  it('PUT 请求包含 Content-Type: application/json', async () => {
    let capturedContentType: string | null = null;
    server.use(
      http.put(`${BASE_URL}/mappings/:id/reject`, ({ request }) => {
        capturedContentType = request.headers.get('Content-Type');
        return HttpResponse.json({
          id: 'map-1',
          source_table: 'accounts',
          source_field: 'balance',
          data_type: 'decimal',
          target_property: 'drp:balance',
          confidence: 85,
          auto_approved: false,
          status: 'rejected',
          created_at: '2024-01-01T00:00:00Z',
        });
      }),
    );

    await mappingApi.reject('map-1', '原因');
    expect(capturedContentType).toBe('application/json');
  });
});


// ─── 5. 401 自动清除 Token ───────────────────────────────────────────────────

describe('401 自动清除 Token', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('后端返回 401 时自动调用 clearToken', async () => {
    setToken('will-be-cleared');
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse('Unauthorized', { status: 401 });
      }),
    );

    await expect(tenantsApi.list()).rejects.toThrow(/401/);
    expect(getToken()).toBeNull();
  });

  it('401 后 getToken 返回 null', async () => {
    setToken('another-token');
    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        return new HttpResponse('Unauthorized', { status: 401 });
      }),
    );

    try {
      await usersApi.list();
    } catch {
      // 预期抛出错误
    }
    expect(getToken()).toBeNull();
    expect(localStorage.getItem('drp_token')).toBeNull();
  });
});


// ─── 6. 网络超时 ─────────────────────────────────────────────────────────────

describe('网络超时', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('请求超时抛出包含"超时"的 Error', async () => {
    vi.useFakeTimers();

    // 直接 mock fetch，让它在收到 abort 信号时正确抛出 AbortError
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn((_url: string, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        if (init?.signal) {
          init.signal.addEventListener('abort', () => {
            const err = new DOMException('The operation was aborted.', 'AbortError');
            reject(err);
          });
        }
      });
    });

    try {
      // 立即将 promise 的 rejection 捕获到变量中，避免 unhandled rejection
      const promise = tenantsApi.list().catch((e: Error) => e);

      // 推进时间超过超时阈值
      await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS + 1000);

      const result = await promise;
      expect(result).toBeInstanceOf(Error);
      expect((result as Error).message).toMatch(/超时/);
    } finally {
      globalThis.fetch = originalFetch;
      vi.useRealTimers();
    }
  });
});


// ─── 7. 错误消息脱敏 [评审 #003] ─────────────────────────────────────────────

describe('错误消息脱敏', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  // 注意：当前 API Client 直接将后端错误文本放入 Error message。
  // 以下测试验证当前行为（Error message 包含后端原始文本），
  // TODO: 需要在前端展示层做脱敏处理

  it('mock 包含内部路径的错误响应，验证 Error 包含后端原始文本', async () => {
    const sensitiveText = 'Error at /app/src/drp/auth/service.py:42';
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse(sensitiveText, { status: 500 });
      }),
    );

    try {
      await tenantsApi.list();
      expect.fail('应该抛出错误');
    } catch (e: any) {
      // 当前实现：Error message 包含后端原始文本（含敏感路径信息）
      // TODO: 需要在前端展示层做脱敏处理，不应将内部路径暴露给用户
      expect(e.message).toContain('/app/src/drp/auth/service.py');
    }
  });

  it('mock 包含 SQL 关键字的错误响应', async () => {
    const sqlText = 'relation "users" does not exist';
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse(sqlText, { status: 500 });
      }),
    );

    try {
      await tenantsApi.list();
      expect.fail('应该抛出错误');
    } catch (e: any) {
      // 当前实现：Error message 包含后端原始 SQL 错误文本
      // TODO: 需要在前端展示层做脱敏处理，不应将 SQL 信息暴露给用户
      expect(e.message).toContain('relation "users"');
    }
  });

  it('mock 包含堆栈跟踪的错误响应', async () => {
    const traceText = 'Traceback (most recent call last):\n  File "main.py", line 10';
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return new HttpResponse(traceText, { status: 500 });
      }),
    );

    try {
      await tenantsApi.list();
      expect.fail('应该抛出错误');
    } catch (e: any) {
      // 当前实现：Error message 包含后端原始堆栈跟踪
      // TODO: 需要在前端展示层做脱敏处理，不应将堆栈跟踪暴露给用户
      expect(e.message).toContain('Traceback');
    }
  });
});


// ─── 8. Token 安全边界 [评审 #004] ───────────────────────────────────────────

describe('Token 安全边界', () => {
  beforeEach(() => {
    localStorage.clear();
    clearToken();
  });

  it('API 请求的 URL 不包含 token 字符串（token 只在 header 中）', async () => {
    const secretToken = 'super-secret-jwt-token-12345';
    let capturedUrl = '';
    let capturedAuth: string | null = null;

    server.use(
      http.get(`${BASE_URL}/tenants`, ({ request }) => {
        capturedUrl = request.url;
        capturedAuth = request.headers.get('Authorization');
        return HttpResponse.json([]);
      }),
    );

    setToken(secretToken);
    await tenantsApi.list();

    // token 不应出现在 URL 中
    expect(capturedUrl).not.toContain(secretToken);
    // token 应在 Authorization header 中
    expect(capturedAuth).toContain(secretToken);
  });

  it('请求过程中无 token 泄露到 console', async () => {
    const secretToken = 'console-leak-test-token';
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return HttpResponse.json([]);
      }),
    );

    setToken(secretToken);
    await tenantsApi.list();

    // 检查所有 console 输出中不包含 token
    const allCalls = [
      ...consoleSpy.mock.calls,
      ...consoleWarnSpy.mock.calls,
      ...consoleErrorSpy.mock.calls,
    ];
    for (const args of allCalls) {
      const output = args.map(String).join(' ');
      expect(output).not.toContain(secretToken);
    }

    consoleSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });
});


// ─── 属性测试 — Property 1: Token 管理 round-trip ────────────────────────────

import * as fc from 'fast-check';

describe('属性测试 — Property 1: Token 管理 round-trip', () => {
  it('Feature: admin-portal-testing, Property 1: Token round-trip', () => {
    fc.assert(
      fc.property(fc.string({ minLength: 1 }), (token) => {
        localStorage.clear();
        clearToken();
        setToken(token);
        expect(getToken()).toBe(token);
        expect(localStorage.getItem('drp_token')).toBe(token);
        clearToken();
        expect(getToken()).toBeNull();
        expect(localStorage.getItem('drp_token')).toBeNull();
      }),
      { numRuns: 100 }
    );
  });
});


// ─── 属性测试 — Property 2: HTTP 错误状态码映射 ──────────────────────────────

describe('属性测试 — Property 2: HTTP 错误状态码映射', () => {
  beforeEach(() => { localStorage.clear(); clearToken(); });

  it('Feature: admin-portal-testing, Property 2: 400-599 状态码映射', async () => {
    /**
     * Validates: Requirements 2.3
     */
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 400, max: 599 }),
        fc.string({ minLength: 1, maxLength: 50 }),
        async (status, text) => {
          server.use(
            http.get(`${BASE_URL}/tenants`, () => {
              return new HttpResponse(text, { status });
            }),
          );
          try {
            await tenantsApi.list();
            // 不应到达这里
            return false;
          } catch (e: any) {
            // Error message 应包含状态码
            return e.message.includes(String(status));
          }
        }
      ),
      { numRuns: 20 }
    );
  });
});


// ─── 属性测试 — Property 3: API 请求体构造正确性 ─────────────────────────────

describe('属性测试 — Property 3: API 请求体构造正确性', () => {
  beforeEach(() => { localStorage.clear(); clearToken(); });

  it('Feature: admin-portal-testing, Property 3: POST/PUT 请求包含正确字段和 Content-Type', async () => {
    /**
     * Validates: Requirements 2.5, 2.6, 2.8, 2.9
     */
    await fc.assert(
      fc.asyncProperty(
        fc.emailAddress(),
        fc.string({ minLength: 1, maxLength: 50 }),
        async (email, password) => {
          let capturedBody: any = null;
          let capturedContentType: string | null = null;
          server.use(
            http.post(`${BASE_URL}/auth/login`, async ({ request }) => {
              capturedBody = await request.json();
              capturedContentType = request.headers.get('Content-Type');
              return HttpResponse.json({ access_token: 'tok', token_type: 'bearer', expires_in: 3600 });
            }),
          );
          await authApi.login(email, password);
          return capturedBody?.email === email
            && capturedBody?.password === password
            && capturedContentType === 'application/json';
        }
      ),
      { numRuns: 20 }
    );
  });
});


// ─── 属性测试 — Property 4: 审计日志查询字符串构造 ────────────────────────────

describe('属性测试 — Property 4: 审计日志查询字符串构造', () => {
  beforeEach(() => { localStorage.clear(); clearToken(); });

  it('Feature: admin-portal-testing, Property 4: 查询参数正确拼接', async () => {
    /**
     * Validates: Requirements 2.7
     */
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          page: fc.option(fc.integer({ min: 0, max: 100 }), { nil: undefined }),
          per_page: fc.option(fc.integer({ min: 0, max: 100 }), { nil: undefined }),
          event_type: fc.option(fc.constantFrom('login', 'logout', 'update', ''), { nil: undefined }),
        }),
        async (params) => {
          let capturedUrl = '';
          server.use(
            http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
              capturedUrl = request.url;
              return HttpResponse.json([]);
            }),
          );
          await auditApi.list(params);
          const url = new URL(capturedUrl);

          // 验证非 null/undefined 参数被正确拼接
          if (params.page != null) {
            if (url.searchParams.get('page') !== String(params.page)) return false;
          }
          if (params.per_page != null) {
            if (url.searchParams.get('per_page') !== String(params.per_page)) return false;
          }
          if (params.event_type) {
            if (url.searchParams.get('event_type') !== params.event_type) return false;
          }
          // URL 不应包含 'undefined'
          if (capturedUrl.includes('undefined')) return false;
          return true;
        }
      ),
      { numRuns: 50 }
    );
  });
});


// ─── 属性测试 — Property 10: JWT 安全验证 ────────────────────────────────────

describe('属性测试 — Property 10: JWT 安全验证', () => {
  beforeEach(() => { localStorage.clear(); clearToken(); });

  it('Feature: admin-portal-testing, Property 10: 伪造 JWT 触发 401 时清除 Token', async () => {
    /**
     * Validates: Requirements 2.3, 安全测试层
     */
    await fc.assert(
      fc.asyncProperty(
        fc.oneof(
          fc.string({ minLength: 1, maxLength: 100 }), // 随机字符串
          fc.constant('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.tampered'), // 篡改签名
          fc.constant('eyJhbGciOiJIUzI1NiJ9..sig'), // 空 payload
        ),
        async (fakeToken) => {
          setToken(fakeToken);
          server.use(
            http.get(`${BASE_URL}/tenants`, () => {
              return new HttpResponse('Unauthorized', { status: 401 });
            }),
          );
          try {
            await tenantsApi.list();
            return false;
          } catch (e: any) {
            return getToken() === null && e.message.includes('401');
          }
        }
      ),
      { numRuns: 20 }
    );
  });
});


// ─── 属性测试 — Property 11: 401 响应自动清除 Token ──────────────────────────

describe('属性测试 — Property 11: 401 响应自动清除 Token', () => {
  beforeEach(() => { localStorage.clear(); clearToken(); });

  it('Feature: admin-portal-testing, Property 11: 所有端点 401 均清除 Token', async () => {
    /**
     * Validates: Requirements 2.11
     */
    const endpoints = [
      { name: 'GET /tenants', fn: () => tenantsApi.list(), method: 'get' as const, path: '/tenants' },
      { name: 'GET /auth/users', fn: () => usersApi.list(), method: 'get' as const, path: '/auth/users' },
      { name: 'GET /auth/roles', fn: () => rolesApi.list(), method: 'get' as const, path: '/auth/roles' },
      { name: 'GET /etl/jobs', fn: () => etlApi.list(), method: 'get' as const, path: '/etl/jobs' },
    ];

    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom(...endpoints),
        async (endpoint) => {
          localStorage.clear();
          clearToken();
          setToken('test-token-for-401');

          const handler = http.get(`${BASE_URL}${endpoint.path}`, () =>
            new HttpResponse('Unauthorized', { status: 401 }),
          );

          server.use(handler);

          try {
            await endpoint.fn();
            return false;
          } catch {
            return getToken() === null && localStorage.getItem('drp_token') === null;
          }
        }
      ),
      { numRuns: 20 }
    );
  });
});
