/**
 * E2E 测试 — 用户管理
 * 验证：新建用户 → 填写表单 → 提交 → 新用户出现在列表中
 * 需求：7.3
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_USERS = [
  { id: 'user-1', email: 'admin@example.com', username: 'admin', full_name: '管理员', status: 'active', tenant_id: 't-1', created_at: '2024-01-01T00:00:00Z' },
  { id: 'user-2', email: 'user@example.com', username: 'user', full_name: '普通用户', status: 'locked', tenant_id: 't-1', created_at: '2024-01-02T00:00:00Z' },
];

const MOCK_NEW_USER = {
  id: 'user-new',
  email: 'new@example.com',
  username: 'newuser',
  full_name: '新用户',
  status: 'active',
  tenant_id: 't-1',
  created_at: new Date().toISOString(),
};

// ─── 辅助：登录并进入主布局 ──────────────────────────────────────────────────

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

test.describe('用户管理', () => {
  test.beforeEach(async ({ page }) => {
    let userCreated = false;

    // mock 用户列表 — 创建后返回包含新用户的列表
    await page.route('**/auth/users', route => {
      if (route.request().method() === 'POST') {
        userCreated = true;
        route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(MOCK_NEW_USER) });
      } else {
        const list = userCreated ? [...MOCK_USERS, MOCK_NEW_USER] : MOCK_USERS;
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(list) });
      }
    });

    // mock 其他必要 API
    await page.route('**/auth/roles', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/auth/audit-logs*', route => {
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

  test('新建用户 → 填写表单 → 提交 → 新用户出现在列表中', async ({ page }) => {
    // 默认登录后进入用户管理页（App 默认 page='users'）
    await expect(page.getByText('用户管理')).toBeVisible();

    // 验证初始用户列表
    await expect(page.getByText('admin@example.com')).toBeVisible();
    await expect(page.getByText('user@example.com')).toBeVisible();

    // 点击新建用户
    await page.getByRole('button', { name: '+ 新建用户' }).click();

    // 验证 Modal 弹出
    await expect(page.getByText('新建用户')).toBeVisible();

    // 填写表单 — 通过 label 定位 Input 组件
    await page.locator('label:has-text("邮箱") + input').fill('new@example.com');
    await page.locator('label:has-text("用户名") + input').fill('newuser');
    await page.locator('label:has-text("全名") + input').fill('新用户');
    await page.locator('label:has-text("密码") + input').fill('password123');

    // 提交
    await page.getByRole('button', { name: '创建' }).click();

    // 验证新用户出现在列表中
    await expect(page.getByText('new@example.com')).toBeVisible();
    await expect(page.getByText('新用户')).toBeVisible();
  });
});
