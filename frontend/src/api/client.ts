/**
 * API 客户端 — 封装与后端的 HTTP 通信。
 * 自动注入 Authorization 头，统一错误处理。
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

let _token: string | null = localStorage.getItem('drp_token');

export function setToken(token: string) {
  _token = token;
  localStorage.setItem('drp_token', token);
}

export function clearToken() {
  _token = null;
  localStorage.removeItem('drp_token');
}

export function getToken(): string | null {
  return _token;
}

/** 默认请求超时时间（毫秒） */
export const REQUEST_TIMEOUT_MS = 30_000;

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const resp = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!resp.ok) {
      if (resp.status === 401) {
        clearToken();
        window.dispatchEvent(new CustomEvent('drp-auth-expired'));
      }
      const text = await resp.text().catch(() => '');
      throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
    }
    // 204 No Content
    if (resp.status === 204) return undefined as T;
    return resp.json() as Promise<T>;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error(`请求超时: ${method} ${path}`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ─── 认证 ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; expires_in: number }>(
      'POST', '/auth/login', { email, password }
    ),
};

// ─── 租户 ────────────────────────────────────────────────────────────────────

export interface Tenant {
  id: string;
  name: string;
  graph_iri: string;
  status: string;
  created_at: string;
}

export const tenantsApi = {
  list: () => request<Tenant[]>('GET', '/tenants'),
  get: (id: string) => request<Tenant>('GET', `/tenants/${id}`),
  create: (name: string) => request<Tenant>('POST', '/tenants', { name }),
  delete: (id: string) => request<void>('DELETE', `/tenants/${id}`),
};

// ─── 用户 & RBAC ─────────────────────────────────────────────────────────────

export interface UserItem {
  id: string;
  email: string;
  username: string | null;
  full_name: string | null;
  status: string;
  tenant_id: string | null;
  created_at: string;
  role_ids?: string[];
}

export const usersApi = {
  list: () => request<UserItem[]>('GET', '/auth/users'),
  get: (id: string) => request<UserItem>('GET', `/auth/users/${id}`),
  create: (data: Partial<UserItem> & { password: string }) =>
    request<UserItem>('POST', '/auth/users', data),
  update: (id: string, data: Partial<UserItem>) =>
    request<UserItem>('PUT', `/auth/users/${id}`, data),
  delete: (id: string) => request<void>('DELETE', `/auth/users/${id}`),
};

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
}

export const rolesApi = {
  list: () => request<Role[]>('GET', '/auth/roles'),
  create: (data: Partial<Role>) => request<Role>('POST', '/auth/roles', data),
  update: (id: string, data: Partial<Role>) => request<Role>('PUT', `/auth/roles/${id}`, data),
  delete: (id: string) => request<void>('DELETE', `/auth/roles/${id}`),
};

// ─── 审计日志 ─────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string;
  user_id: string;
  event_type: string;
  resource: string | null;
  ip_address: string | null;
  created_at: string;
  detail: Record<string, unknown> | null;
}

export const auditApi = {
  list: (params?: { page?: number; per_page?: number; event_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.page != null) qs.set('page', String(params.page));
    if (params?.per_page != null) qs.set('per_page', String(params.per_page));
    if (params?.event_type) qs.set('event_type', params.event_type);
    return request<AuditLog[]>('GET', `/auth/audit-logs?${qs}`);
  },
};

// ─── DDL 上传 & 映射 ──────────────────────────────────────────────────────────

export interface MappingSpec {
  id: string;
  source_table: string;
  source_field: string;
  data_type: string;
  target_property: string;
  confidence: number;
  auto_approved: boolean;
  status: string;
  created_at: string;
}

export const mappingApi = {
  generate: (ddl: string) =>
    request<{ mappings: MappingSpec[]; mapping_yaml: string }>(
      'POST', '/mappings/generate', { ddl }
    ),
  list: () => request<MappingSpec[]>('GET', '/mappings'),
  approve: (id: string) => request<MappingSpec>('PUT', `/mappings/${id}/approve`),
  reject: (id: string, reason?: string) =>
    request<MappingSpec>('PUT', `/mappings/${id}/reject`, { reason }),
  exportYaml: () =>
    request<{ mapping_yaml: string }>('GET', '/mappings/export-yaml'),
  batchApprove: (mode: 'all' | 'threshold', threshold?: number) =>
    request<{ approved_count: number; skipped_count: number; total_pending: number }>(
      'POST', '/mappings/batch-approve', { mode, threshold }
    ),
};

// ─── ETL 任务 ─────────────────────────────────────────────────────────────────

export interface EtlJob {
  id: string;
  tenant_id: string;
  job_type: string;
  status: string;
  triples_written: number | null;
  error_message: string | null;
  created_at: string;
  finished_at: string | null;
}

export const etlApi = {
  list: () => request<EtlJob[]>('GET', '/etl/jobs'),
  trigger: (tenant_id: string, table: string, mapping_yaml: string) =>
    request<{ job_id: string }>('POST', '/etl/sync', { tenant_id, table, mapping_yaml }),
};

// ─── 数据质量 ─────────────────────────────────────────────────────────────────

export interface DataQuality {
  tenant_id: string;
  null_rate: number;
  latency_seconds: number;
  format_compliance: number;
  overall: number;
  is_healthy: boolean;
}

export const qualityApi = {
  get: (tenantId: string) =>
    request<DataQuality>('GET', `/etl/quality/${tenantId}`),
};
