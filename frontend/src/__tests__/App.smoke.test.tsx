/**
 * 冒烟测试 — 核心流程最小可验证路径
 *
 * 通过 vitest.smoke.config.ts 单独运行：
 *   npx vitest --run --config vitest.smoke.config.ts
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from '../App';
import { setToken, clearToken } from '../api/client';

// ─── WebSocket Mock（Dashboard 使用 useRiskEvents）─────────────────────────

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  readyState = 0;
  close() {
    this.readyState = 3;
  }

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // 模拟连接成功
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.(new Event('open'));
    }, 0);
  }
}

beforeEach(() => {
  clearToken();
  localStorage.clear();
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ─── 辅助函数 ────────────────────────────────────────────────────────────────

/** 设置已登录状态并渲染 App */
function renderLoggedIn() {
  setToken('test-token');
  return render(<App />);
}

/** 获取侧边栏导航区域 */
function getNav() {
  return screen.getByRole('navigation');
}

/** 点击侧边栏导航项 */
async function clickNavItem(user: ReturnType<typeof userEvent.setup>, label: RegExp | string) {
  const nav = getNav();
  const btn = within(nav).getByRole('button', { name: typeof label === 'string' ? new RegExp(label) : label });
  await user.click(btn);
}

// ─── 冒烟用例 1：登录流程 ────────────────────────────────────────────────────

describe('冒烟测试', () => {
  it('用例1 — 登录流程：输入凭据 → 提交 → 5 秒内进入主布局', async () => {
    render(<App />);
    const user = userEvent.setup();

    // 确认在登录页
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();

    // 输入凭据
    await user.type(screen.getByPlaceholderText('admin@example.com'), 'admin@example.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123');

    // 提交登录
    await user.click(screen.getByRole('button', { name: '登录' }));

    // 5 秒内进入主布局
    await waitFor(() => {
      expect(screen.getByText('DRP 管理后台')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  // ─── 冒烟用例 2：用户管理页加载 ──────────────────────────────────────────

  it('用例2 — 用户管理页加载：已登录 → 导航到用户管理 → 用户列表表格可见', async () => {
    renderLoggedIn();
    const user = userEvent.setup();

    // 点击用户管理导航项
    await clickNavItem(user, '用户管理');

    // 用户列表表格可见
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
      // 验证表头包含关键列
      expect(screen.getByText('邮箱')).toBeInTheDocument();
      expect(screen.getByText('用户名')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  // ─── 冒烟用例 3：审计日志页加载 ──────────────────────────────────────────

  it('用例3 — 审计日志页加载：已登录 → 导航到审计日志 → 日志表格可见', async () => {
    renderLoggedIn();
    const user = userEvent.setup();

    // 点击审计日志导航项
    await clickNavItem(user, '审计日志');

    // 日志表格可见
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
      // 验证表头包含关键列
      expect(screen.getByText('事件类型')).toBeInTheDocument();
      expect(screen.getByText('IP 地址')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  // ─── 冒烟用例 4：全页面导航 ──────────────────────────────────────────────

  it('用例4 — 全页面导航：已登录 → 依次点击 12 个导航项 → 无渲染错误', async () => {
    renderLoggedIn();
    const user = userEvent.setup();

    // mock console.error 以检测渲染错误
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const navLabels = [
      '监管看板', '用户管理', '用户组', '角色权限', '审计日志',
      'DDL 上传', '映射审核', 'ETL 监控', '租户管理', '数据质量',
      '行级规则', '列级规则',
    ];

    for (const label of navLabels) {
      await clickNavItem(user, label);
      // 等待页面渲染完成（给异步加载一点时间）
      await waitFor(() => {
        // 导航区域始终可见，说明没有崩溃
        expect(screen.getByRole('navigation')).toBeInTheDocument();
      });
    }

    // 验证 console.error 未被调用（过滤掉 React 内部的非错误警告）
    const realErrors = consoleErrorSpy.mock.calls.filter(
      args => !String(args[0]).includes('act(') && !String(args[0]).includes('Warning:')
    );
    expect(realErrors).toHaveLength(0);

    consoleErrorSpy.mockRestore();
  });

  // ─── 冒烟用例 5：监管看板渲染 ────────────────────────────────────────────

  it('用例5 — 监管看板渲染：已登录 → 导航到看板 → SVG 图谱元素可见', async () => {
    renderLoggedIn();
    const user = userEvent.setup();

    // 点击监管看板导航项
    await clickNavItem(user, '监管看板');

    // SVG 图谱元素可见
    await waitFor(() => {
      const svgs = document.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    }, { timeout: 5000 });
  });

  // ─── 冒烟用例 6：快速页面切换无状态污染 [评审 #016] ──────────────────────

  it('用例6 — 快速页面切换无状态污染：快速连续切换 5 个页面 → 最终页面数据正确', async () => {
    renderLoggedIn();
    const user = userEvent.setup();

    // 快速连续切换 5 个页面（不等待中间页面加载完成）
    const pages = ['监管看板', '审计日志', '用户管理', '租户管理', '审计日志'];

    for (const label of pages) {
      await clickNavItem(user, label);
    }

    // 最终停留在审计日志页面，验证数据正确
    await waitFor(() => {
      // 审计日志页面应该有表格
      expect(screen.getByRole('table')).toBeInTheDocument();
      // 验证审计日志页面的表头（确认不是其他页面的表格）
      expect(screen.getByText('事件类型')).toBeInTheDocument();
      expect(screen.getByText('IP 地址')).toBeInTheDocument();
    }, { timeout: 5000 });

    // 验证不存在其他页面的特有内容（无状态污染）
    // 用户管理页的"新建用户"按钮不应出现
    expect(screen.queryByRole('button', { name: /新建用户/ })).not.toBeInTheDocument();
  });
});
