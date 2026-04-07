import { render, screen, waitFor, within, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import App from '../App';
import { setToken, clearToken, getToken } from '../api/client';

const BASE_URL = 'http://localhost:8000';

// ─── WebSocket Mock ──────────────────────────────────────────────────────────

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  readyState = 0;
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
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

/** 设置已登录状态 */
function loginWithToken() {
  setToken('test-token');
}

/** 获取侧边栏导航区域 */
function getSidebar() {
  return screen.getByRole('navigation');
}

// ─── 1. 未登录渲染 LoginPage ─────────────────────────────────────────────────

describe('App 未登录状态', () => {
  it('无 token 时渲染 LoginPage', () => {
    render(<App />);
    // LoginPage 包含登录按钮和 DRP 标题
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
    expect(screen.getByText('穿透式资金监管平台')).toBeInTheDocument();
  });
});

// ─── 2. 登录后渲染主布局 ─────────────────────────────────────────────────────

describe('App 登录后状态', () => {
  it('渲染主布局（侧边栏导航 + 主内容区）', async () => {
    loginWithToken();
    render(<App />);

    // 侧边栏标题
    expect(screen.getByText('DRP 管理后台')).toBeInTheDocument();
    expect(screen.getByText('资金监管平台')).toBeInTheDocument();

    // 导航区域存在
    expect(getSidebar()).toBeInTheDocument();

    // 退出登录按钮
    expect(screen.getByRole('button', { name: /退出登录/ })).toBeInTheDocument();
  });
});

// ─── 3. 导航切换 ─────────────────────────────────────────────────────────────

describe('App 导航切换', () => {
  it('点击侧边栏导航项 → 主内容区切换对应页面', async () => {
    loginWithToken();
    render(<App />);
    const user = userEvent.setup();
    const nav = getSidebar();

    // 先点击"用户管理"导航项（默认页面可能不是用户管理）
    const userBtn = within(nav).getByRole('button', { name: /用户管理/ });
    await user.click(userBtn);

    // 用户管理页面应显示（导航项 + PageHeader 标题 = 至少 2 处）
    await waitFor(() => {
      const matches = screen.getAllByText('用户管理');
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });

    // 点击"审计日志"导航项
    const auditBtn = within(nav).getByRole('button', { name: /审计日志/ });
    await user.click(auditBtn);

    // 应该切换到审计日志页面（导航项 + PageHeader 标题 = 至少 2 处）
    await waitFor(() => {
      const headings = screen.getAllByText('审计日志');
      expect(headings.length).toBeGreaterThanOrEqual(2);
    });

    // 用户管理的 PageHeader 标题应该消失（只剩导航项中的 1 处）
    const userMgmtTexts = screen.getAllByText('用户管理');
    expect(userMgmtTexts.length).toBe(1);
  });
});

// ─── 4. 退出登录 ─────────────────────────────────────────────────────────────

describe('App 退出登录', () => {
  it('点击"退出登录" → 调用 clearToken → 返回 LoginPage', async () => {
    loginWithToken();
    render(<App />);
    const user = userEvent.setup();

    // 确认已登录
    expect(screen.getByText('DRP 管理后台')).toBeInTheDocument();

    // 点击退出登录
    await user.click(screen.getByRole('button', { name: /退出登录/ }));

    // 应该回到登录页
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
    expect(screen.getByText('穿透式资金监管平台')).toBeInTheDocument();

    // token 应该被清除
    expect(getToken()).toBeNull();
  });
});

// ─── 5. 侧边栏导航项完整性 ──────────────────────────────────────────────────

describe('App 侧边栏导航项', () => {
  it('显示全部 12 个导航项', () => {
    loginWithToken();
    render(<App />);

    const expectedLabels = [
      '监管看板', '用户管理', '用户组', '角色权限', '审计日志',
      'DDL 上传', '映射审核', 'ETL 监控', '租户管理', '数据质量',
      '行级规则', '列级规则',
    ];

    const nav = getSidebar();
    for (const label of expectedLabels) {
      expect(within(nav).getByRole('button', { name: new RegExp(label) })).toBeInTheDocument();
    }
  });
});

// ─── 6. 401 后路由恢复 ──────────────────────────────────────────────────────

describe('App 401 后路由恢复', () => {
  it('用户在某页面 → 401 auth-expired → 登录页 → 重新登录 → 恢复之前页面', async () => {
    loginWithToken();
    render(<App />);
    const user = userEvent.setup();

    // 1. 导航到"审计日志"页面
    const nav = getSidebar();
    await user.click(within(nav).getByRole('button', { name: /审计日志/ }));

    // 确认已在审计日志页面
    await waitFor(() => {
      const headings = screen.getAllByText('审计日志');
      expect(headings.length).toBeGreaterThanOrEqual(2);
    });

    // 2. 模拟 401 auth-expired 事件（API Client 在 401 时 dispatch）
    act(() => {
      clearToken();
      window.dispatchEvent(new CustomEvent('drp-auth-expired'));
    });

    // 3. 应该跳转到登录页
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
    });

    // 4. 重新登录：填写凭据并提交
    const emailInput = screen.getByPlaceholderText('admin@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');
    await user.type(emailInput, 'admin@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(screen.getByRole('button', { name: '登录' }));

    // 5. 登录成功后应恢复到审计日志页面（而非默认的用户管理页）
    await waitFor(() => {
      expect(screen.getByText('DRP 管理后台')).toBeInTheDocument();
    });

    // 验证恢复到审计日志页面：审计日志文本出现至少 2 次（导航项 + 页面标题）
    await waitFor(() => {
      const headings = screen.getAllByText('审计日志');
      expect(headings.length).toBeGreaterThanOrEqual(2);
    });
  });
});
