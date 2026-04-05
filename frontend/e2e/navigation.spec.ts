/**
 * E2E 测试 — 全局导航
 * 验证：依次点击所有侧边栏导航项 → 每个页面正确渲染且无控制台错误
 * 需求：7.7
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_USERS = [
  { id: 'user-1', email: 'admin@example.com', username: 'admin', full_name: '管理员', status: 'active', tenant_id: 't-1', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_TENANTS = [
  { id: 't-1', name: '测试租户', graph_iri: 'urn:drp:tenant:t-1', status: 'active', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_ROLES = [
  { id: 'role-1', name: 'admin', description: '管理员角色', permissions: ['test:perm_a'] },
];

const MOCK_AUDIT_LOGS = [
  { id: 'log-1', user_id: 'user-1', event_type: 'login', resource: null, ip_address: '192.168.1.1', created_at: '2024-01-01T00:00:00Z', detail: null },
];

const MOCK_MAPPINGS = [
  { id: 'map-1', source_table: 'accounts', source_field: 'balance', data_type: 'decimal', target_property: 'drp:balance', confidence: 85, auto_approved: false, status: 'pending', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_ETL_JOBS = [
  { id: 'job-1', tenant_id: 't-1', job_type: 'full_sync', status: 'success', triples_written: 1500, error_message: null, created_at: '2024-01-01T00:00:00Z', finished_at: '2024-01-01T00:01:00Z' },
];

const MOCK_QUALITY = {
  tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true,
};

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

test.describe('全局导航', () => {
  test.beforeEach(async ({ page }) => {
    // 设置所有 API mock
    await page.route('**/auth/users', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USERS) });
    });
    await page.route('**/auth/roles', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ROLES) });
    });
    await page.route('**/auth/audit-logs*', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_AUDIT_LOGS) });
    });
    await page.route('**/tenants', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TENANTS) });
    });
    await page.route('**/mappings/generate', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ mappings: MOCK_MAPPINGS, mapping_yaml: 'yaml' }) });
    });
    await page.route('**/mappings', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_MAPPINGS) });
    });
    await page.route('**/etl/jobs', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ETL_JOBS) });
    });
    await page.route('**/etl/quality/*', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUALITY) });
    });

    await login(page);
  });

  test('依次点击所有侧边栏导航项 → 每个页面正确渲染且无控制台错误', async ({ page }) => {
    // 收集控制台错误
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 导航项与对应页面标识
    const navItems = [
      { label: '监管看板', expectedText: 'svg' },       // Dashboard 包含 SVG 图谱
      { label: '用户管理', expectedText: '用户管理' },
      { label: '用户组', expectedText: '开发中' },       // GroupsPage 显示 EmptyState
      { label: '角色权限', expectedText: 'admin' },      // RolesPage 显示角色名
      { label: '审计日志', expectedText: '审计日志' },
      { label: 'DDL 上传', expectedText: 'DDL 上传与映射生成' },
      { label: '映射审核', expectedText: '映射审核队列' },
      { label: 'ETL 监控', expectedText: 'ETL 任务监控' },
      { label: '租户管理', expectedText: '租户管理' },
      { label: '数据质量', expectedText: '数据质量面板' },
    ];

    for (const item of navItems) {
      // 点击侧边栏导航项
      await page.getByText(item.label, { exact: true }).click();

      // 验证页面正确渲染
      if (item.label === '监管看板') {
        // Dashboard 页面验证 SVG 元素存在
        await expect(page.locator('svg').first()).toBeVisible({ timeout: 5000 });
      } else {
        await expect(page.getByText(item.expectedText).first()).toBeVisible({ timeout: 5000 });
      }
    }

    // 验证无控制台错误（过滤掉已知的非关键错误）
    const criticalErrors = consoleErrors.filter(
      err => !err.includes('favicon') && !err.includes('WebSocket')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
