/**
 * E2E 测试 — 登录流程
 * 使用 Playwright route mock 拦截 API 请求
 * 需求：7.1, 7.2
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_LOGIN_SUCCESS = {
  access_token: 'test-token',
  token_type: 'bearer',
  expires_in: 3600,
};

const MOCK_USERS = [
  { id: 'user-1', email: 'admin@example.com', username: 'admin', full_name: '管理员', status: 'active', tenant_id: 't-1', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_TENANTS = [
  { id: 't-1', name: '测试租户', graph_iri: 'urn:drp:tenant:t-1', status: 'active', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_ROLES = [
  { id: 'role-1', name: 'admin', description: '管理员角色', permissions: ['test:perm_a', 'test:perm_b'] },
];

const MOCK_AUDIT_LOGS = [
  { id: 'log-1', user_id: 'user-1', event_type: 'login', resource: null, ip_address: '192.168.1.1', created_at: '2024-01-01T00:00:00Z', detail: null },
];

// ─── 辅助：设置通用 API mock ─────────────────────────────────────────────────

async function setupApiMocks(page: Page) {
  await page.route('**/localhost:8000/auth/users', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USERS) });
  });
  await page.route('**/localhost:8000/auth/roles', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ROLES) });
  });
  await page.route('**/localhost:8000/auth/audit-logs*', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_AUDIT_LOGS) });
  });
  await page.route('**/localhost:8000/tenants', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TENANTS) });
  });
  await page.route('**/localhost:8000/etl/jobs', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
  });
  await page.route('**/localhost:8000/mappings', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
  });
  await page.route('**/localhost:8000/etl/quality/*', route => {
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true }),
    });
  });
}

// ─── 测试 ────────────────────────────────────────────────────────────────────

test.describe('登录流程', () => {
  test('输入有效凭据 → 登录成功 → 主布局可见且侧边栏可见', async ({ page }) => {
    // mock 登录接口返回成功
    await page.route('**/localhost:8000/auth/login', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LOGIN_SUCCESS) });
    });
    await setupApiMocks(page);

    await page.goto('/');

    // 填写登录表单
    await page.getByPlaceholder('admin@example.com').fill('admin@example.com');
    await page.getByPlaceholder('••••••••').fill('password123');
    await page.getByRole('button', { name: '登录' }).click();

    // 验证主布局可见
    await expect(page.getByText('DRP 管理后台')).toBeVisible();
    // 验证侧边栏导航项可见
    await expect(page.getByText('用户管理')).toBeVisible();
    await expect(page.getByText('审计日志')).toBeVisible();
    await expect(page.getByText('监管看板')).toBeVisible();
  });

  test('输入错误密码 → 显示错误提示信息', async ({ page }) => {
    // mock 登录接口返回 401
    await page.route('**/localhost:8000/auth/login', route => {
      route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: '账号或密码错误' }) });
    });

    await page.goto('/');

    // 填写登录表单
    await page.getByPlaceholder('admin@example.com').fill('admin@example.com');
    await page.getByPlaceholder('••••••••').fill('wrong-password');
    await page.getByRole('button', { name: '登录' }).click();

    // 验证错误提示可见（ErrorBox 组件会显示错误信息）
    await expect(page.locator('text=401')).toBeVisible();
  });
});
