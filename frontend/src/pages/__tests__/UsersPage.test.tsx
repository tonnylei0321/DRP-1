import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { MOCK_USERS } from '../../test/mocks/handlers';
import UsersPage from '../UsersPage';
import { clearToken, setToken } from '../../api/client';
import type { UserItem } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
  setToken('test-token');
});

// ─── 渲染测试 ────────────────────────────────────────────────────────────────

describe('UsersPage 渲染', () => {
  it('调用 usersApi.list 并显示用户表格（邮箱、用户名、全名、状态、创建时间列）', async () => {
    render(<UsersPage />);

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // 验证表头列
    expect(screen.getByText('邮箱')).toBeInTheDocument();
    expect(screen.getByText('用户名')).toBeInTheDocument();
    expect(screen.getByText('全名')).toBeInTheDocument();
    expect(screen.getByText('状态')).toBeInTheDocument();
    expect(screen.getByText('创建时间')).toBeInTheDocument();

    // 验证两条 mock 用户数据
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('管理员')).toBeInTheDocument();
    expect(screen.getByText('普通用户')).toBeInTheDocument();
  });
});

// ─── 新建用户 ────────────────────────────────────────────────────────────────

describe('UsersPage 新建用户', () => {
  it('点击"新建用户" → 显示 Modal → 填写表单 → 提交 → 调用 usersApi.create → 刷新列表', async () => {
    let listCallCount = 0;
    const newUser: UserItem = {
      id: 'user-new',
      email: 'new@example.com',
      username: 'newuser',
      full_name: '新用户',
      status: 'active',
      tenant_id: 't-1',
      created_at: new Date().toISOString(),
    };

    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          return HttpResponse.json([...MOCK_USERS, newUser]);
        }
        return HttpResponse.json(MOCK_USERS);
      }),
    );

    const user = userEvent.setup();
    render(<UsersPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // 点击"新建用户"按钮
    await user.click(screen.getByRole('button', { name: /新建用户/ }));

    // 验证 Modal 显示（通过 heading 查找标题）
    expect(screen.getByRole('heading', { name: '新建用户' })).toBeInTheDocument();

    // 通过 label 文本定位 Modal 表单中的输入框（限定在 form 元素内查找，避免与表头冲突）
    const form = document.querySelector('form')!;
    const getInputByLabel = (labelText: string) => {
      const labels = form.querySelectorAll('label');
      const label = Array.from(labels).find(l => l.textContent === labelText)!;
      return label.closest('div')!.querySelector('input')!;
    };

    const emailField = getInputByLabel('邮箱*');
    const usernameField = getInputByLabel('用户名');
    const fullNameField = getInputByLabel('全名');
    const passwordField = getInputByLabel('密码*');

    await user.type(emailField, 'new@example.com');
    await user.type(usernameField, 'newuser');
    await user.type(fullNameField, '新用户');
    await user.type(passwordField, 'password123');

    // 提交表单
    await user.click(screen.getByRole('button', { name: '创建' }));

    // 等待列表刷新，新用户出现
    await waitFor(() => {
      expect(screen.getByText('new@example.com')).toBeInTheDocument();
    });

    // Modal 已关闭
    expect(screen.queryByRole('heading', { name: '新建用户' })).not.toBeInTheDocument();
  });
});

// ─── 删除用户 ────────────────────────────────────────────────────────────────

describe('UsersPage 删除用户', () => {
  it('点击"删除" → 显示自定义确认 Modal → 点击确认 → 调用 usersApi.delete → 刷新列表', async () => {
    let listCallCount = 0;

    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          return HttpResponse.json([MOCK_USERS[1]]);
        }
        return HttpResponse.json(MOCK_USERS);
      }),
    );

    const user = userEvent.setup();
    render(<UsersPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // 点击第一个用户的"删除"按钮
    const deleteButtons = screen.getAllByRole('button', { name: '删除' });
    await user.click(deleteButtons[0]);

    // 验证确认 Modal 显示（标题是 heading）
    expect(screen.getByRole('heading', { name: '确认删除' })).toBeInTheDocument();
    expect(screen.getByText(/确认删除该用户/)).toBeInTheDocument();

    // 点击"确认删除"按钮
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    // 等待列表刷新，第一个用户消失
    await waitFor(() => {
      expect(screen.queryByText('admin@example.com')).not.toBeInTheDocument();
    });

    // 第二个用户仍在
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
  });
});

// ─── 删除取消 ────────────────────────────────────────────────────────────────

describe('UsersPage 删除取消', () => {
  it('确认 Modal 中点击"取消" → 关闭 Modal → 列表不变', async () => {
    const user = userEvent.setup();
    render(<UsersPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // 点击第一个用户的"删除"按钮
    const deleteButtons = screen.getAllByRole('button', { name: '删除' });
    await user.click(deleteButtons[0]);

    // 验证确认 Modal 显示
    expect(screen.getByRole('heading', { name: '确认删除' })).toBeInTheDocument();

    // 点击 Modal 中的"取消"按钮
    await user.click(screen.getByRole('button', { name: '取消' }));

    // Modal 关闭
    expect(screen.queryByRole('heading', { name: '确认删除' })).not.toBeInTheDocument();

    // 列表不变，两个用户都在
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
  });
});

// ─── 空用户列表 ──────────────────────────────────────────────────────────────

describe('UsersPage 空列表', () => {
  it('usersApi.list 返回空数组时显示 EmptyState', async () => {
    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        return HttpResponse.json([]);
      }),
    );

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('暂无用户')).toBeInTheDocument();
    });
  });
});

// ─── 错误处理 ────────────────────────────────────────────────────────────────

describe('UsersPage 错误处理', () => {
  it('usersApi.list 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
      }),
    );

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});

// ─── statusVariant 分支 ─────────────────────────────────────────────────────

describe('UsersPage statusVariant 分支', () => {
  it('渲染 locked 和 suspended 状态的用户', async () => {
    server.use(
      http.get(`${BASE_URL}/auth/users`, () => {
        return HttpResponse.json([
          { ...MOCK_USERS[0], id: 'u-locked', status: 'locked', email: 'locked@test.com', full_name: '锁定用户' },
          { ...MOCK_USERS[0], id: 'u-susp', status: 'suspended', email: 'susp@test.com', full_name: '暂停用户' },
        ]);
      }),
    );

    render(<UsersPage />);

    await waitFor(() => {
      expect(screen.getByText('locked@test.com')).toBeInTheDocument();
    });

    expect(screen.getByText('locked')).toBeInTheDocument();
    expect(screen.getByText('suspended')).toBeInTheDocument();
  });
});
