import { http, HttpResponse } from 'msw';
import type { Tenant, UserItem, Role, AuditLog, MappingSpec, EtlJob, DataQuality } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

// ─── Mock 数据常量 ──────────────────────────────────────────────────────────

export const MOCK_USERS: UserItem[] = [
  {
    id: 'user-1',
    email: 'admin@example.com',
    username: 'admin',
    full_name: '管理员',
    status: 'active',
    tenant_id: 't-1',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'user-2',
    email: 'user@example.com',
    username: 'user',
    full_name: '普通用户',
    status: 'locked',
    tenant_id: 't-1',
    created_at: '2024-01-02T00:00:00Z',
  },
];

export const MOCK_TENANTS: Tenant[] = [
  {
    id: 't-1',
    name: '测试租户',
    graph_iri: 'urn:drp:tenant:t-1',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
  },
];

export const MOCK_ROLES: Role[] = [
  {
    id: 'role-1',
    name: 'admin',
    description: '管理员角色',
    permissions: ['test:perm_a', 'test:perm_b', 'test:perm_c'],
  },
];

export const MOCK_AUDIT_LOGS: AuditLog[] = [
  {
    id: 'log-1',
    user_id: 'user-1',
    event_type: 'login',
    resource: null,
    ip_address: '192.168.1.1',
    created_at: '2024-01-01T00:00:00Z',
    detail: null,
  },
  {
    id: 'log-2',
    user_id: 'user-2',
    event_type: 'update',
    resource: '/auth/users/user-2',
    ip_address: '192.168.1.2',
    created_at: '2024-01-02T00:00:00Z',
    detail: { field: 'status', old: 'active', new: 'locked' },
  },
];

export const MOCK_MAPPINGS: MappingSpec[] = [
  {
    id: 'map-1',
    source_table: 'accounts',
    source_field: 'balance',
    data_type: 'decimal',
    target_property: 'drp:balance',
    confidence: 85,
    auto_approved: false,
    status: 'pending',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'map-2',
    source_table: 'accounts',
    source_field: 'name',
    data_type: 'varchar',
    target_property: 'drp:name',
    confidence: 95,
    auto_approved: true,
    status: 'approved',
    created_at: '2024-01-01T00:00:00Z',
  },
];

export const MOCK_ETL_JOBS: EtlJob[] = [
  {
    id: 'job-1',
    tenant_id: 't-1',
    job_type: 'full_sync',
    status: 'success',
    triples_written: 1500,
    error_message: null,
    created_at: '2024-01-01T00:00:00Z',
    finished_at: '2024-01-01T00:01:00Z',
  },
];

export const MOCK_QUALITY: DataQuality = {
  tenant_id: 't-1',
  null_rate: 0.05,
  latency_seconds: 120,
  format_compliance: 0.95,
  overall: 90.5,
  is_healthy: true,
};

// ─── MSW v2 请求处理器 ──────────────────────────────────────────────────────

export const handlers = [
  // ── 认证 ──────────────────────────────────────────────────────────────────
  http.post(`${BASE_URL}/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 3600,
    });
  }),

  // ── 用户 ──────────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/auth/users`, () => {
    return HttpResponse.json(MOCK_USERS);
  }),

  http.get(`${BASE_URL}/auth/users/:id`, ({ params }) => {
    const user = MOCK_USERS.find((u) => u.id === params.id);
    return user
      ? HttpResponse.json(user)
      : HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.post(`${BASE_URL}/auth/users`, async ({ request }) => {
    const body = (await request.json()) as Partial<UserItem>;
    const newUser: UserItem = {
      id: 'user-new',
      email: body.email ?? 'new@example.com',
      username: body.username ?? 'newuser',
      full_name: body.full_name ?? '新用户',
      status: 'active',
      tenant_id: body.tenant_id ?? 't-1',
      created_at: new Date().toISOString(),
    };
    return HttpResponse.json(newUser, { status: 201 });
  }),

  http.put(`${BASE_URL}/auth/users/:id`, async ({ params, request }) => {
    const body = (await request.json()) as Partial<UserItem>;
    const existing = MOCK_USERS.find((u) => u.id === params.id);
    const updated: UserItem = {
      ...(existing ?? MOCK_USERS[0]),
      ...body,
      id: params.id as string,
    };
    return HttpResponse.json(updated);
  }),

  http.delete(`${BASE_URL}/auth/users/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // ── 角色 ──────────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/auth/roles`, () => {
    return HttpResponse.json(MOCK_ROLES);
  }),

  http.post(`${BASE_URL}/auth/roles`, async ({ request }) => {
    const body = (await request.json()) as Partial<Role>;
    const newRole: Role = {
      id: 'role-new',
      name: body.name ?? 'new-role',
      description: body.description ?? '新角色',
      permissions: body.permissions ?? [],
    };
    return HttpResponse.json(newRole, { status: 201 });
  }),

  http.put(`${BASE_URL}/auth/roles/:id`, async ({ params, request }) => {
    const body = (await request.json()) as Partial<Role>;
    const existing = MOCK_ROLES.find((r) => r.id === params.id);
    const updated: Role = {
      ...(existing ?? MOCK_ROLES[0]),
      ...body,
      id: params.id as string,
    };
    return HttpResponse.json(updated);
  }),

  http.delete(`${BASE_URL}/auth/roles/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // ── 审计日志 ──────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/auth/audit-logs`, () => {
    return HttpResponse.json(MOCK_AUDIT_LOGS);
  }),

  // ── 租户 ──────────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/tenants`, () => {
    return HttpResponse.json(MOCK_TENANTS);
  }),

  http.post(`${BASE_URL}/tenants`, async ({ request }) => {
    const body = (await request.json()) as { name: string };
    const newTenant: Tenant = {
      id: 't-new',
      name: body.name,
      graph_iri: `urn:drp:tenant:t-new`,
      status: 'active',
      created_at: new Date().toISOString(),
    };
    return HttpResponse.json(newTenant, { status: 201 });
  }),

  http.get(`${BASE_URL}/tenants/:id`, ({ params }) => {
    const tenant = MOCK_TENANTS.find((t) => t.id === params.id);
    return tenant
      ? HttpResponse.json(tenant)
      : HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.delete(`${BASE_URL}/tenants/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // ── 映射 ──────────────────────────────────────────────────────────────────
  http.post(`${BASE_URL}/mappings/generate`, () => {
    return HttpResponse.json({
      mappings: MOCK_MAPPINGS,
      mapping_yaml: 'test-yaml',
    });
  }),

  http.get(`${BASE_URL}/mappings`, () => {
    return HttpResponse.json(MOCK_MAPPINGS);
  }),

  http.put(`${BASE_URL}/mappings/:id/approve`, ({ params }) => {
    const existing = MOCK_MAPPINGS.find((m) => m.id === params.id);
    return HttpResponse.json({
      ...(existing ?? MOCK_MAPPINGS[0]),
      id: params.id as string,
      status: 'approved',
    });
  }),

  http.put(`${BASE_URL}/mappings/:id/reject`, ({ params }) => {
    const existing = MOCK_MAPPINGS.find((m) => m.id === params.id);
    return HttpResponse.json({
      ...(existing ?? MOCK_MAPPINGS[0]),
      id: params.id as string,
      status: 'rejected',
    });
  }),

  // ── ETL ───────────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/etl/jobs`, () => {
    return HttpResponse.json(MOCK_ETL_JOBS);
  }),

  http.post(`${BASE_URL}/etl/sync`, () => {
    return HttpResponse.json({ job_id: 'job-new' });
  }),

  // ── 数据质量 ──────────────────────────────────────────────────────────────
  http.get(`${BASE_URL}/etl/quality/:tenantId`, () => {
    return HttpResponse.json(MOCK_QUALITY);
  }),
];
