# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> 登录流程 >> 输入有效凭据 → 登录成功 → 主布局可见且侧边栏可见
- Location: e2e/login.spec.ts:64:3

# Error details

```
Test timeout of 10000ms exceeded.
```

```
Error: locator.fill: Test timeout of 10000ms exceeded.
Call log:
  - waiting for getByPlaceholder('admin@example.com')

```

# Test source

```ts
  1   | /**
  2   |  * E2E 测试 — 登录流程
  3   |  * 使用 Playwright route mock 拦截 API 请求
  4   |  * 需求：7.1, 7.2
  5   |  */
  6   | import { test, expect, Page } from '@playwright/test';
  7   | 
  8   | // ─── Mock 数据 ───────────────────────────────────────────────────────────────
  9   | 
  10  | const MOCK_LOGIN_SUCCESS = {
  11  |   access_token: 'test-token',
  12  |   token_type: 'bearer',
  13  |   expires_in: 3600,
  14  | };
  15  | 
  16  | const MOCK_USERS = [
  17  |   { id: 'user-1', email: 'admin@example.com', username: 'admin', full_name: '管理员', status: 'active', tenant_id: 't-1', created_at: '2024-01-01T00:00:00Z' },
  18  | ];
  19  | 
  20  | const MOCK_TENANTS = [
  21  |   { id: 't-1', name: '测试租户', graph_iri: 'urn:drp:tenant:t-1', status: 'active', created_at: '2024-01-01T00:00:00Z' },
  22  | ];
  23  | 
  24  | const MOCK_ROLES = [
  25  |   { id: 'role-1', name: 'admin', description: '管理员角色', permissions: ['test:perm_a', 'test:perm_b'] },
  26  | ];
  27  | 
  28  | const MOCK_AUDIT_LOGS = [
  29  |   { id: 'log-1', user_id: 'user-1', event_type: 'login', resource: null, ip_address: '192.168.1.1', created_at: '2024-01-01T00:00:00Z', detail: null },
  30  | ];
  31  | 
  32  | // ─── 辅助：设置通用 API mock ─────────────────────────────────────────────────
  33  | 
  34  | async function setupApiMocks(page: Page) {
  35  |   await page.route('**/auth/users', route => {
  36  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USERS) });
  37  |   });
  38  |   await page.route('**/auth/roles', route => {
  39  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ROLES) });
  40  |   });
  41  |   await page.route('**/auth/audit-logs*', route => {
  42  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_AUDIT_LOGS) });
  43  |   });
  44  |   await page.route('**/tenants', route => {
  45  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TENANTS) });
  46  |   });
  47  |   await page.route('**/etl/jobs', route => {
  48  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
  49  |   });
  50  |   await page.route('**/mappings', route => {
  51  |     route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
  52  |   });
  53  |   await page.route('**/etl/quality/*', route => {
  54  |     route.fulfill({
  55  |       status: 200, contentType: 'application/json',
  56  |       body: JSON.stringify({ tenant_id: 't-1', null_rate: 0.05, latency_seconds: 120, format_compliance: 0.95, overall: 90.5, is_healthy: true }),
  57  |     });
  58  |   });
  59  | }
  60  | 
  61  | // ─── 测试 ────────────────────────────────────────────────────────────────────
  62  | 
  63  | test.describe('登录流程', () => {
  64  |   test('输入有效凭据 → 登录成功 → 主布局可见且侧边栏可见', async ({ page }) => {
  65  |     // mock 登录接口返回成功
  66  |     await page.route('**/auth/login', route => {
  67  |       route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_LOGIN_SUCCESS) });
  68  |     });
  69  |     await setupApiMocks(page);
  70  | 
  71  |     await page.goto('/');
  72  | 
  73  |     // 填写登录表单
> 74  |     await page.getByPlaceholder('admin@example.com').fill('admin@example.com');
      |                                                      ^ Error: locator.fill: Test timeout of 10000ms exceeded.
  75  |     await page.getByPlaceholder('••••••••').fill('password123');
  76  |     await page.getByRole('button', { name: '登录' }).click();
  77  | 
  78  |     // 验证主布局可见
  79  |     await expect(page.getByText('DRP 管理后台')).toBeVisible();
  80  |     // 验证侧边栏导航项可见
  81  |     await expect(page.getByText('用户管理')).toBeVisible();
  82  |     await expect(page.getByText('审计日志')).toBeVisible();
  83  |     await expect(page.getByText('监管看板')).toBeVisible();
  84  |   });
  85  | 
  86  |   test('输入错误密码 → 显示错误提示信息', async ({ page }) => {
  87  |     // mock 登录接口返回 401
  88  |     await page.route('**/auth/login', route => {
  89  |       route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: '账号或密码错误' }) });
  90  |     });
  91  | 
  92  |     await page.goto('/');
  93  | 
  94  |     // 填写登录表单
  95  |     await page.getByPlaceholder('admin@example.com').fill('admin@example.com');
  96  |     await page.getByPlaceholder('••••••••').fill('wrong-password');
  97  |     await page.getByRole('button', { name: '登录' }).click();
  98  | 
  99  |     // 验证错误提示可见（ErrorBox 组件会显示错误信息）
  100 |     await expect(page.locator('text=401')).toBeVisible();
  101 |   });
  102 | });
  103 | 
```