/**
 * E2E 测试 — 管理页面（ETL / 租户 / 数据质量）
 * 验证：ETL 页面加载 → 任务表格可见；租户创建流程；数据质量页切换租户 → 评分更新
 * 需求：7.8, 7.9, 7.10
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_ETL_JOBS = [
  { id: 'job-1', tenant_id: 't-1', job_type: 'full_sync', status: 'success', triples_written: 1500, error_message: null, created_at: '2024-01-01T00:00:00Z', finished_at: '2024-01-01T00:01:00Z' },
];

const MOCK_TENANTS = [
  { id: 't-1', name: '测试租户', graph_iri: 'urn:drp:tenant:t-1', status: 'active', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_NEW_TENANT = {
  id: 't-new', name: '新租户', graph_iri: 'urn:drp:tenant:t-new', status: 'active', created_at: new Date().toISOString(),
};

const MOCK_QUALITY_T1 = {
  tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true,
};

const MOCK_QUALITY_T_NEW = {
  tenant_id: 't-new', null_rate: 0.15, latency_seconds: 300, format_compliance: 0.80, overall: 72.0, is_healthy: false,
};

// ─── 辅助：登录 ──────────────────────────────────────────────────────────────

async function login(page: Page) {
  await page.route('**/localhost:8000/auth/login', route => {
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

test.describe('管理页面', () => {
  test.beforeEach(async ({ page }) => {
    let tenantCreated = false;

    // mock ETL 任务列表
    await page.route('**/localhost:8000/etl/jobs', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ETL_JOBS) });
    });

    // mock 租户列表 — 创建后返回包含新租户的列表
    await page.route('**/localhost:8000/tenants', route => {
      if (route.request().method() === 'POST') {
        tenantCreated = true;
        route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(MOCK_NEW_TENANT) });
      } else {
        const list = tenantCreated ? [...MOCK_TENANTS, MOCK_NEW_TENANT] : MOCK_TENANTS;
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(list) });
      }
    });

    // mock 数据质量 — 根据 tenantId 返回不同数据
    await page.route('**/localhost:8000/etl/quality/*', route => {
      const url = route.request().url();
      if (url.includes('t-new')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUALITY_T_NEW) });
      } else {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUALITY_T1) });
      }
    });

    // mock 其他必要 API
    await page.route('**/localhost:8000/auth/users', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/localhost:8000/auth/roles', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/localhost:8000/auth/audit-logs*', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/localhost:8000/mappings', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });

    await login(page);
  });

  test('ETL 页面加载 → 任务表格可见', async ({ page }) => {
    // 导航到 ETL 监控页
    await page.getByText('ETL 监控').click();
    await expect(page.getByText('ETL 任务监控')).toBeVisible();

    // 验证任务表格可见
    await expect(page.locator('table')).toBeVisible();
    // 验证任务数据显示
    await expect(page.getByText('full_sync')).toBeVisible();
    await expect(page.getByText('success')).toBeVisible();
    await expect(page.getByText('1,500')).toBeVisible();
  });

  test('租户创建流程 → 新租户出现在列表中', async ({ page }) => {
    // 导航到租户管理页
    await page.getByText('租户管理').click();
    await expect(page.getByText('租户管理').first()).toBeVisible();

    // 验证初始租户列表
    await expect(page.getByText('测试租户')).toBeVisible();

    // 点击新建租户
    await page.getByRole('button', { name: '+ 新建租户' }).click();

    // 验证 Modal 弹出
    await expect(page.getByText('新建租户').nth(1)).toBeVisible();

    // 填写租户名称
    await page.locator('label:has-text("租户名称") + input').fill('新租户');

    // 提交
    await page.getByRole('button', { name: '创建' }).click();

    // 验证新租户出现在列表中
    await expect(page.getByText('新租户')).toBeVisible();
  });

  test('数据质量页切换租户 → 评分更新', async ({ page }) => {
    // 先创建新租户使列表有多个选项
    // 通过直接设置 tenantCreated 状态来模拟
    // 重新 mock 租户列表返回两个租户
    await page.route('**/localhost:8000/tenants', route => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify([...MOCK_TENANTS, MOCK_NEW_TENANT]),
        });
      } else {
        route.continue();
      }
    });

    // 导航到数据质量页
    await page.getByText('数据质量').click();
    await expect(page.getByText('数据质量面板')).toBeVisible();

    // 验证初始评分（t-1 的评分 90.5）
    await expect(page.getByText('90.5')).toBeVisible();
    await expect(page.getByText('健康')).toBeVisible();

    // 切换到新租户
    await page.locator('select').selectOption('t-new');

    // 验证评分更新（t-new 的评分 72.0）
    await expect(page.getByText('72.0')).toBeVisible();
    await expect(page.getByText('需关注')).toBeVisible();
  });
});
