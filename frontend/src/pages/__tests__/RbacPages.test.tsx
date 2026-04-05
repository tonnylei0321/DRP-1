import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { MOCK_ROLES } from '../../test/mocks/handlers';
import { GroupsPage, RolesPage } from '../RbacPages';
import { clearToken, setToken } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
  setToken('test-token');
});

// ─── GroupsPage ──────────────────────────────────────────────────────────────

describe('GroupsPage', () => {
  it('显示"开发中"提示的 EmptyState 组件', () => {
    render(<GroupsPage />);
    expect(screen.getByText(/用户组功能开发中/)).toBeInTheDocument();
  });
});

// ─── RolesPage 渲染 ─────────────────────────────────────────────────────────

describe('RolesPage 渲染', () => {
  it('调用 rolesApi.list 并显示角色列表（名称、描述、权限数量）', async () => {
    render(<RolesPage />);

    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    // 验证描述
    expect(screen.getByText('管理员角色')).toBeInTheDocument();
    // 验证权限数量 badge
    expect(screen.getByText('3 权限')).toBeInTheDocument();
  });
});

// ─── RolesPage 权限配置 ─────────────────────────────────────────────────────

describe('RolesPage 权限配置', () => {
  it('选择角色 → 右侧面板显示权限树复选框列表', async () => {
    const user = userEvent.setup();
    render(<RolesPage />);

    // 等待角色列表加载
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    // 点击角色行
    await user.click(screen.getByText('admin'));

    // 右侧面板显示权限配置标题
    expect(screen.getByText('admin — 权限配置')).toBeInTheDocument();

    // 验证权限复选框列表（ALL_PERMISSIONS 中的权限项）
    const checkboxes = screen.getAllByRole('checkbox');
    // ALL_PERMISSIONS 有 13 项
    expect(checkboxes.length).toBe(13);

    // 验证部分权限标签可见
    expect(screen.getByText('tenant:read')).toBeInTheDocument();
    expect(screen.getByText('user:read')).toBeInTheDocument();
    expect(screen.getByText('audit:read')).toBeInTheDocument();

    // MOCK_ROLES 的权限是 test:perm_a/b/c，不在 ALL_PERMISSIONS 中，
    // 所以所有复选框都应该是未勾选状态
    checkboxes.forEach(cb => {
      expect(cb).not.toBeChecked();
    });
  });
});


// ─── RolesPage 删除角色 [评审 #005] ─────────────────────────────────────────

describe('RolesPage 删除角色', () => {
  it('点击"删除" → 显示确认 Modal → 点击确认 → 调用 rolesApi.delete → 刷新列表', async () => {
    let listCallCount = 0;
    let deletedUrl = '';

    server.use(
      http.get(`${BASE_URL}/auth/roles`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          // 删除后返回空列表
          return HttpResponse.json([]);
        }
        return HttpResponse.json(MOCK_ROLES);
      }),
      http.delete(`${BASE_URL}/auth/roles/:id`, ({ request }) => {
        deletedUrl = request.url;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const user = userEvent.setup();
    render(<RolesPage />);

    // 等待角色列表加载
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    // 点击"删除"按钮
    await user.click(screen.getByRole('button', { name: '删除' }));

    // 验证确认 Modal 显示
    expect(screen.getByRole('heading', { name: '确认删除' })).toBeInTheDocument();
    expect(screen.getByText(/确认删除该角色/)).toBeInTheDocument();

    // 点击"确认删除"
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    // 等待列表刷新，角色消失
    await waitFor(() => {
      expect(screen.queryByText('admin')).not.toBeInTheDocument();
    });

    // 验证 DELETE 请求 URL 包含正确的角色 ID
    expect(deletedUrl).toContain('/auth/roles/role-1');
  });

  it('点击"删除" → 显示确认 Modal → 点击取消 → 关闭 Modal → 列表不变', async () => {
    const user = userEvent.setup();
    render(<RolesPage />);

    // 等待角色列表加载
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    // 点击"删除"按钮
    await user.click(screen.getByRole('button', { name: '删除' }));

    // 验证确认 Modal 显示
    expect(screen.getByRole('heading', { name: '确认删除' })).toBeInTheDocument();

    // 点击"取消"
    await user.click(screen.getByRole('button', { name: '取消' }));

    // Modal 关闭
    expect(screen.queryByRole('heading', { name: '确认删除' })).not.toBeInTheDocument();

    // 列表不变
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('3 权限')).toBeInTheDocument();
  });
});

// ─── RolesPage 权限保存 [评审 #006] ─────────────────────────────────────────

describe('RolesPage 权限保存', () => {
  it('修改权限复选框 → 点击"保存权限" → 调用 rolesApi.update → 刷新列表', async () => {
    let updateCalled = false;
    let listCallCount = 0;

    const updatedRole = {
      ...MOCK_ROLES[0],
      permissions: ['test:perm_a', 'test:perm_b', 'test:perm_c', 'tenant:read'],
    };

    server.use(
      http.get(`${BASE_URL}/auth/roles`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          return HttpResponse.json([updatedRole]);
        }
        return HttpResponse.json(MOCK_ROLES);
      }),
      http.put(`${BASE_URL}/auth/roles/:id`, async () => {
        updateCalled = true;
        return HttpResponse.json(updatedRole);
      }),
    );

    const user = userEvent.setup();
    render(<RolesPage />);

    // 等待角色列表加载
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    // 选择角色
    await user.click(screen.getByText('admin'));

    // 等待权限面板显示
    expect(screen.getByText('admin — 权限配置')).toBeInTheDocument();

    // 找到 tenant:read 复选框并勾选（它当前未勾选）
    const tenantReadLabel = screen.getByText('tenant:read');
    await user.click(tenantReadLabel);

    // 点击"保存权限"
    await user.click(screen.getByRole('button', { name: '保存权限' }));

    // 验证 rolesApi.update 被调用
    await waitFor(() => {
      expect(updateCalled).toBe(true);
    });

    // 验证列表刷新后权限数量更新
    await waitFor(() => {
      expect(screen.getByText('4 权限')).toBeInTheDocument();
    });
  });
});
