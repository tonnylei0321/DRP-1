/**
 * E2E 测试 — DDL 上传与映射审核
 * 验证：粘贴 DDL → 生成 → 结果表格出现；确认/拒绝 → 状态更新
 * 需求：7.5, 7.6
 */
import { test, expect, Page } from '@playwright/test';

// ─── Mock 数据 ───────────────────────────────────────────────────────────────

const MOCK_MAPPINGS = [
  { id: 'map-1', source_table: 'accounts', source_field: 'balance', data_type: 'decimal', target_property: 'drp:balance', confidence: 85, auto_approved: false, status: 'pending', created_at: '2024-01-01T00:00:00Z' },
  { id: 'map-2', source_table: 'accounts', source_field: 'name', data_type: 'varchar', target_property: 'drp:name', confidence: 95, auto_approved: true, status: 'approved', created_at: '2024-01-01T00:00:00Z' },
];

const MOCK_GENERATE_RESULT = {
  mappings: MOCK_MAPPINGS,
  mapping_yaml: 'test-yaml-content',
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

test.describe('DDL 上传与映射审核', () => {
  test.beforeEach(async ({ page }) => {
    // mock 映射生成
    await page.route('**/localhost:8000/mappings/generate', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_GENERATE_RESULT) });
    });

    // mock 映射列表 — 跟踪审核状态变化
    let mappingsState = MOCK_MAPPINGS.map(m => ({ ...m }));

    await page.route('**/localhost:8000/mappings', route => {
      if (route.request().method() === 'GET') {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mappingsState) });
      } else {
        route.continue();
      }
    });

    // mock 确认操作
    await page.route('**/localhost:8000/mappings/*/approve', route => {
      const url = route.request().url();
      const id = url.match(/mappings\/([^/]+)\/approve/)?.[1];
      const mapping = mappingsState.find(m => m.id === id);
      if (mapping) mapping.status = 'approved';
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ ...mapping, status: 'approved' }),
      });
    });

    // mock 拒绝操作
    await page.route('**/localhost:8000/mappings/*/reject', route => {
      const url = route.request().url();
      const id = url.match(/mappings\/([^/]+)\/reject/)?.[1];
      const mapping = mappingsState.find(m => m.id === id);
      if (mapping) mapping.status = 'rejected';
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ ...mapping, status: 'rejected' }),
      });
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
    await page.route('**/localhost:8000/tenants', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/localhost:8000/etl/jobs', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
    await page.route('**/localhost:8000/etl/quality/*', route => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true }) });
    });

    await login(page);
  });

  test('粘贴 DDL → 生成 → 结果表格出现', async ({ page }) => {
    // 导航到 DDL 上传页
    await page.getByText('DDL 上传').click();
    await expect(page.getByText('DDL 上传与映射生成')).toBeVisible();

    // 粘贴 DDL 文本
    const ddlText = 'CREATE TABLE accounts (balance DECIMAL, name VARCHAR(100));';
    await page.locator('textarea').fill(ddlText);

    // 点击生成
    await page.getByRole('button', { name: '生成映射建议' }).click();

    // 验证结果表格出现
    await expect(page.getByText('解析结果预览')).toBeVisible();
    await expect(page.getByText('accounts.balance')).toBeVisible();
    await expect(page.getByText('drp:balance')).toBeVisible();
    await expect(page.getByText('accounts.name')).toBeVisible();
    await expect(page.getByText('drp:name')).toBeVisible();
  });

  test('确认映射 → 状态更新', async ({ page }) => {
    // 导航到映射审核页
    await page.getByText('映射审核').click();
    await expect(page.getByText('映射审核队列')).toBeVisible();

    // 验证待审核映射可见
    await expect(page.getByText('待审核')).toBeVisible();
    await expect(page.getByText('accounts.balance')).toBeVisible();

    // 点击确认按钮
    await page.getByRole('button', { name: '确认' }).click();

    // 验证状态更新 — 待审核区域应消失或减少
    await expect(page.getByText('已审核')).toBeVisible();
  });

  test('拒绝映射 → 填写原因 → 状态更新', async ({ page }) => {
    // 导航到映射审核页
    await page.getByText('映射审核').click();
    await expect(page.getByText('映射审核队列')).toBeVisible();

    // 点击拒绝按钮
    await page.getByRole('button', { name: '拒绝' }).click();

    // 验证拒绝原因 Modal 弹出
    await expect(page.getByText('拒绝映射')).toBeVisible();

    // 填写拒绝原因
    await page.locator('label:has-text("拒绝原因") + input').fill('数据类型不匹配');

    // 确认拒绝
    await page.getByRole('button', { name: '确认拒绝' }).click();

    // 验证状态更新
    await expect(page.getByText('已审核')).toBeVisible();
  });
});
