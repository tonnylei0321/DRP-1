import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import LoginPage from '../LoginPage';
import { setToken, getToken, clearToken } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
});

// ─── 渲染测试 ────────────────────────────────────────────────────────────────

describe('LoginPage 渲染', () => {
  it('显示邮箱输入框、密码输入框、登录按钮、SAML SSO 按钮、OIDC 按钮', () => {
    render(<LoginPage onLogin={() => {}} />);

    // 邮箱和密码输入框（通过 label 文本查找）
    expect(screen.getByText('邮箱')).toBeInTheDocument();
    expect(screen.getByText('密码')).toBeInTheDocument();

    // 登录按钮
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();

    // SSO 按钮
    expect(screen.getByRole('button', { name: /SAML/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /OIDC/i })).toBeInTheDocument();
  });
});

// ─── 登录成功 ────────────────────────────────────────────────────────────────

describe('LoginPage 登录成功', () => {
  it('提交有效凭据 → 调用 authApi.login → setToken → onLogin 回调', async () => {
    const onLogin = vi.fn();
    const user = userEvent.setup();

    render(<LoginPage onLogin={onLogin} />);

    // 填写邮箱和密码
    const emailInput = screen.getByPlaceholderText('admin@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');

    await user.type(emailInput, 'admin@example.com');
    await user.type(passwordInput, 'password123');

    // 提交表单
    await user.click(screen.getByRole('button', { name: '登录' }));

    // 等待异步操作完成
    await waitFor(() => {
      expect(onLogin).toHaveBeenCalledTimes(1);
    });

    // 验证 token 已设置（MSW handler 返回 'test-token'）
    expect(getToken()).toBe('test-token');
  });
});

// ─── 登录失败 ────────────────────────────────────────────────────────────────

describe('LoginPage 登录失败', () => {
  it('显示 ErrorBox 错误信息', async () => {
    // 覆盖默认 handler，模拟登录失败
    server.use(
      http.post(`${BASE_URL}/auth/login`, () => {
        return HttpResponse.json(
          { detail: '账号或密码错误' },
          { status: 401 },
        );
      }),
    );

    const onLogin = vi.fn();
    const user = userEvent.setup();

    render(<LoginPage onLogin={onLogin} />);

    const emailInput = screen.getByPlaceholderText('admin@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');

    await user.type(emailInput, 'wrong@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(screen.getByRole('button', { name: '登录' }));

    // 等待错误信息显示
    await waitFor(() => {
      expect(screen.getByText(/401/)).toBeInTheDocument();
    });

    // onLogin 不应被调用
    expect(onLogin).not.toHaveBeenCalled();
  });
});

// ─── SAML SSO 按钮 ──────────────────────────────────────────────────────────

describe('LoginPage SSO 跳转', () => {
  let originalLocation: Location;

  beforeEach(() => {
    // 保存原始 location 并 mock window.location.href setter
    originalLocation = window.location;
    // @ts-expect-error -- 测试中需要替换 window.location
    delete window.location;
    window.location = { ...originalLocation, href: '' } as Location;
    Object.defineProperty(window.location, 'href', {
      set: vi.fn(),
      get: () => '',
      configurable: true,
    });
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it('点击 SAML SSO 按钮后跳转 URL 包含 /auth/saml/login', async () => {
    const user = userEvent.setup();
    const hrefSetter = vi.fn();

    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '',
      configurable: true,
    });

    render(<LoginPage onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /SAML/i }));

    expect(hrefSetter).toHaveBeenCalledWith(
      expect.stringContaining('/auth/saml/login'),
    );
  });

  it('点击 OIDC 按钮后跳转 URL 包含 /auth/oidc/login', async () => {
    const user = userEvent.setup();
    const hrefSetter = vi.fn();

    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '',
      configurable: true,
    });

    render(<LoginPage onLogin={() => {}} />);

    await user.click(screen.getByRole('button', { name: /OIDC/i }));

    expect(hrefSetter).toHaveBeenCalledWith(
      expect.stringContaining('/auth/oidc/login'),
    );
  });
});
