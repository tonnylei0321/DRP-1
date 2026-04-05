import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { MOCK_MAPPINGS } from '../../test/mocks/handlers';
import { DdlUploadPage, MappingsPage } from '../MappingPages';
import { clearToken, setToken } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
  setToken('test-token');
});

// ─── DdlUploadPage ──────────────────────────────────────────────────────────

describe('DdlUploadPage', () => {
  it('粘贴 DDL 文本 → 点击"生成映射建议" → 调用 mappingApi.generate → 右侧面板显示映射结果表格', async () => {
    const user = userEvent.setup();
    render(<DdlUploadPage />);

    // 在 textarea 中输入 DDL 文本
    const textarea = screen.getByPlaceholderText('或直接粘贴 DDL...');
    await user.type(textarea, 'CREATE TABLE accounts (balance DECIMAL, name VARCHAR(100));');

    // 点击"生成映射建议"按钮
    await user.click(screen.getByRole('button', { name: /生成映射建议/ }));

    // 等待结果表格显示
    await waitFor(() => {
      expect(screen.getByText(/共 2 条映射建议/)).toBeInTheDocument();
    });

    // 验证映射结果表格内容
    expect(screen.getByText('accounts.balance')).toBeInTheDocument();
    expect(screen.getByText('drp:balance')).toBeInTheDocument();
    expect(screen.getByText('accounts.name')).toBeInTheDocument();
    expect(screen.getByText('drp:name')).toBeInTheDocument();
  });
});

// ─── MappingsPage 渲染 ──────────────────────────────────────────────────────

describe('MappingsPage 渲染', () => {
  it('调用 mappingApi.list → 按 pending/已审核分组显示', async () => {
    render(<MappingsPage />);

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText(/待审核/)).toBeInTheDocument();
    });

    // 验证 pending 分组（map-1 是 pending）
    expect(screen.getByText('待审核 (1)')).toBeInTheDocument();
    expect(screen.getByText('accounts.balance')).toBeInTheDocument();

    // 验证已审核分组（map-2 是 approved）
    expect(screen.getByText('已审核 (1)')).toBeInTheDocument();
    expect(screen.getByText('accounts.name')).toBeInTheDocument();
  });
});


// ─── 确认操作 ────────────────────────────────────────────────────────────────

describe('MappingsPage 确认操作', () => {
  it('点击"确认" → 调用 mappingApi.approve → 刷新列表', async () => {
    let listCallCount = 0;

    server.use(
      http.get(`${BASE_URL}/mappings`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          // 刷新后 map-1 变为 approved
          return HttpResponse.json([
            { ...MOCK_MAPPINGS[0], status: 'approved' },
            MOCK_MAPPINGS[1],
          ]);
        }
        return HttpResponse.json(MOCK_MAPPINGS);
      }),
    );

    const user = userEvent.setup();
    render(<MappingsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('待审核 (1)')).toBeInTheDocument();
    });

    // 点击"确认"按钮
    await user.click(screen.getByRole('button', { name: '确认' }));

    // 等待列表刷新，待审核消失，已审核变为 2
    await waitFor(() => {
      expect(screen.getByText('已审核 (2)')).toBeInTheDocument();
    });

    expect(screen.queryByText('待审核')).not.toBeInTheDocument();
  });
});

// ─── 拒绝操作 ────────────────────────────────────────────────────────────────

describe('MappingsPage 拒绝操作', () => {
  it('点击"拒绝" → 显示原因输入 Modal → 填写原因 → 确认 → 调用 mappingApi.reject（含 reason 字段） → 刷新列表', async () => {
    let listCallCount = 0;
    let capturedRejectBody: { reason?: string } | null = null;

    server.use(
      http.get(`${BASE_URL}/mappings`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          // 刷新后 map-1 变为 rejected
          return HttpResponse.json([
            { ...MOCK_MAPPINGS[0], status: 'rejected' },
            MOCK_MAPPINGS[1],
          ]);
        }
        return HttpResponse.json(MOCK_MAPPINGS);
      }),
      http.put(`${BASE_URL}/mappings/:id/reject`, async ({ request, params }) => {
        capturedRejectBody = await request.json() as { reason?: string };
        return HttpResponse.json({
          ...MOCK_MAPPINGS[0],
          id: params.id as string,
          status: 'rejected',
        });
      }),
    );

    const user = userEvent.setup();
    render(<MappingsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('待审核 (1)')).toBeInTheDocument();
    });

    // 点击"拒绝"按钮
    await user.click(screen.getByRole('button', { name: '拒绝' }));

    // 验证 Modal 显示
    expect(screen.getByRole('heading', { name: '拒绝映射' })).toBeInTheDocument();

    // 填写拒绝原因
    const reasonInput = screen.getByPlaceholderText('请输入拒绝原因...');
    await user.type(reasonInput, '字段映射不准确');

    // 点击"确认拒绝"
    await user.click(screen.getByRole('button', { name: '确认拒绝' }));

    // 验证 API 调用包含 reason 字段
    await waitFor(() => {
      expect(capturedRejectBody).not.toBeNull();
    });
    expect(capturedRejectBody!.reason).toBe('字段映射不准确');

    // 等待列表刷新，已审核变为 2
    await waitFor(() => {
      expect(screen.getByText('已审核 (2)')).toBeInTheDocument();
    });

    // Modal 已关闭
    expect(screen.queryByRole('heading', { name: '拒绝映射' })).not.toBeInTheDocument();
  });
});

// ─── 拒绝取消 ────────────────────────────────────────────────────────────────

describe('MappingsPage 拒绝取消', () => {
  it('Modal 中点击取消 → 关闭 Modal → 列表不变', async () => {
    const user = userEvent.setup();
    render(<MappingsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('待审核 (1)')).toBeInTheDocument();
    });

    // 点击"拒绝"按钮
    await user.click(screen.getByRole('button', { name: '拒绝' }));

    // 验证 Modal 显示
    expect(screen.getByRole('heading', { name: '拒绝映射' })).toBeInTheDocument();

    // 点击"取消"按钮
    await user.click(screen.getByRole('button', { name: '取消' }));

    // Modal 关闭
    expect(screen.queryByRole('heading', { name: '拒绝映射' })).not.toBeInTheDocument();

    // 列表不变
    expect(screen.getByText('待审核 (1)')).toBeInTheDocument();
    expect(screen.getByText('已审核 (1)')).toBeInTheDocument();
  });
});

// ─── DdlUploadPage 错误处理 ──────────────────────────────────────────────────

describe('DdlUploadPage 错误处理', () => {
  it('mappingApi.generate 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.post(`${BASE_URL}/mappings/generate`, () => {
        return HttpResponse.json({ detail: '解析失败' }, { status: 500 });
      }),
    );

    const user = userEvent.setup();
    render(<DdlUploadPage />);

    const textarea = screen.getByPlaceholderText('或直接粘贴 DDL...');
    await user.type(textarea, 'INVALID DDL;');
    await user.click(screen.getByRole('button', { name: /生成映射建议/ }));

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});

// ─── DdlUploadPage 文件上传 ──────────────────────────────────────────────────

describe('DdlUploadPage 文件上传', () => {
  it('选择文件后 textarea 填充文件内容', async () => {
    const user = userEvent.setup();
    render(<DdlUploadPage />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeNull();

    const file = new File(['CREATE TABLE test (id INT);'], 'test.sql', { type: 'text/plain' });
    await user.upload(fileInput, file);

    await waitFor(() => {
      const textarea = screen.getByPlaceholderText('或直接粘贴 DDL...') as HTMLTextAreaElement;
      expect(textarea.value).toBe('CREATE TABLE test (id INT);');
    });
  });
});

// ─── MappingsPage 空列表 ────────────────────────────────────────────────────

describe('MappingsPage 空列表', () => {
  it('mappingApi.list 返回空数组时显示 EmptyState', async () => {
    server.use(
      http.get(`${BASE_URL}/mappings`, () => {
        return HttpResponse.json([]);
      }),
    );

    render(<MappingsPage />);

    await waitFor(() => {
      expect(screen.getByText('暂无映射记录')).toBeInTheDocument();
    });
  });
});

// ─── MappingsPage 错误处理 ──────────────────────────────────────────────────

describe('MappingsPage 错误处理', () => {
  it('mappingApi.list 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.get(`${BASE_URL}/mappings`, () => {
        return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
      }),
    );

    render(<MappingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});
