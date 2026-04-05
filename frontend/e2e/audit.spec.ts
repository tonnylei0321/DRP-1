/**
 * E2E 测试 — 审计日志
 * 验证：选择事件类型过滤器 → 表格内容根据过滤条件更新
 * 需求：7.4
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_ALL_LOGS = [
  { id: 'log-1', user_id: 'user-1', event_type: 'login', resource: null, ip_address: '192.168.1.1', created_at: '2024-01-01T00:00:00Z', detail: null },
  { id: 'log-2', user_id: 'user-2', event_type: 'update', resource: '/auth/users/user-2', ip_address: '192.168.1.2', created_at: '2024-01-02T00:00:00Z', detail: null },
];

const MOCK_LOGIN_LOGS = [
  { id: 'log-1', user_id: 'user-1', event_type: 'login', resource: null, ip_address: '192.168.1.1', created_at: '2024-01-01T00:00:00Z', detail: null },
];

// ─── 辅助：登录 ──────────────────────────────────────────────────────────────

async function login(page: Page) {
  await page.route('**/auth/login', route => {
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ access_token: 'test-token', token_type: 'bearer', expires_in: 3600 }),
    });
  });
  await page.goto('/');
  await page.getByPlaceholder('admin@example.com').fill('admin@example.com');
  await page.getByPlaceholder('••••••••').fill('password123');
  await page.getByRole('button', { name: '登录' }).click();
  await page.waitForSelector('text=DRP 管理后台');
}

// ─── 测试 ────────────────────────────────────────────────────────────────────

test.describe('审计日志', () => {
  test.beforeEach(async ({ page }) => {
    // mock 审计日志 — 根据 event_type 参数返回不同数据
    await page.route('**/auth/audit-logs*', route => {
      const url = route.request().url();
      if (url.includes('event_type=login')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LOGIN_LOGS) });
      } else {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ALL_LOGS) });
      }
    });

    // mock 其他必要 API
    await page.route('**/auth/users', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/auth/roles', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/tenants', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/etl/jobs', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/mappings', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/etl/quality/*', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true }) });
    });

    await login(page);
  });

  test('选择事件类型过滤器 → 表格内容根据过滤条件更新', async ({ page }) => {
    // 导航到审计日志页
    await page.getByText('审计日志').click();

    // 验证初始加载显示全部日志
    await expect(page.locator('table')).toBeVisible();
    await expect(page.getByText('login').first()).toBeVisible();
    await expect(page.getByText('update')).toBeVisible();

    // 选择 "login" 过滤器
    await page.locator('select').selectOption('login');

    // 验证表格更新 — 只显示 login 类型的日志
    await expect(page.getByText('login').first()).toBeVisible();
    // update 类型的日志不应再显示
    await expect(page.getByText('update')).not.toBeVisible();
  });
});
