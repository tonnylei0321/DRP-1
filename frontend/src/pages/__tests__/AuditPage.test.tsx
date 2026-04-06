import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { MOCK_AUDIT_LOGS } from '../../test/mocks/handlers';
import AuditPage from '../AuditPage';
import { clearToken, setToken } from '../../api/client';
import type { AuditLog } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
  setToken('test-token');
});

// ─── 渲染测试 ────────────────────────────────────────────────────────────────

describe('AuditPage 渲染', () => {
  it('调用 auditApi.list 并显示审计日志表格（事件类型、用户ID、资源、IP地址、时间列）', async () => {
    render(<AuditPage />);

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 验证表头列
    expect(screen.getByText('事件类型')).toBeInTheDocument();
    expect(screen.getByText('用户ID')).toBeInTheDocument();
    expect(screen.getByText('资源')).toBeInTheDocument();
    expect(screen.getByText('IP 地址')).toBeInTheDocument();
    expect(screen.getByText('时间')).toBeInTheDocument();

    // 验证两条 mock 审计日志数据
    expect(screen.getByText('user.update')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.2')).toBeInTheDocument();
  });
});

// ─── 过滤测试 ────────────────────────────────────────────────────────────────

describe('AuditPage 过滤', () => {
  it('选择事件类型过滤器 → 以新 action 参数重新调用 auditApi.list', async () => {
    let capturedUrl = '';

    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json(MOCK_AUDIT_LOGS);
      }),
    );

    const user = userEvent.setup();
    render(<AuditPage />);

    // 等待初始加载
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 选择 "login" 事件类型过滤
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'login');

    // 验证重新调用时 URL 包含 action=login
    await waitFor(() => {
      expect(capturedUrl).toContain('action=login');
    });
  });
});


// ─── CSV 导出测试 ─────────────────────────────────────────────────────────────

describe('AuditPage CSV 导出', () => {
  it('点击"导出 CSV" → 生成 CSV 文件并触发下载', async () => {
    // 拦截 Blob 构造函数来捕获 CSV 内容
    let capturedCsvContent = '';
    const OriginalBlob = globalThis.Blob;
    vi.spyOn(globalThis, 'Blob').mockImplementation((parts?: BlobPart[], options?: BlobPropertyBag) => {
      if (parts && parts.length > 0) {
        capturedCsvContent = String(parts[0]);
      }
      return new OriginalBlob(parts, options);
    });

    const mockUrl = 'blob:http://localhost/fake-url';
    const createObjectURLSpy = vi.fn().mockReturnValue(mockUrl);
    const revokeObjectURLSpy = vi.fn();
    globalThis.URL.createObjectURL = createObjectURLSpy;
    globalThis.URL.revokeObjectURL = revokeObjectURLSpy;

    const clickSpy = vi.fn();
    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'a') {
        const anchor = originalCreateElement('a') as HTMLAnchorElement;
        anchor.click = clickSpy;
        return anchor;
      }
      return originalCreateElement(tag);
    });

    const user = userEvent.setup();
    render(<AuditPage />);

    // 等待数据加载
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 点击导出按钮
    await user.click(screen.getByRole('button', { name: /导出 CSV/ }));

    // 验证触发下载
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalledWith(mockUrl);

    // 验证 CSV 内容包含表头和数据
    expect(capturedCsvContent).toContain('ID,UserID,EventType,Resource,IP,CreatedAt');
    expect(capturedCsvContent).toContain('log-1');
    expect(capturedCsvContent).toContain('log-2');

    vi.restoreAllMocks();
  });
});

// ─── CSV 注入防护测试 ─────────────────────────────────────────────────────────

describe('AuditPage CSV 注入防护', () => {
  it('包含恶意内容的字段被正确转义（添加单引号前缀）', async () => {
    // mock 包含恶意内容的审计日志
    const maliciousLogs: AuditLog[] = [
      {
        id: 'log-evil-1',
        user_id: 'user-1',
        tenant_id: null,
        action: 'user.update',
        resource_type: "=CMD('calc')",
        resource_id: null,
        ip_address: '+1234567',
        created_at: '2024-01-01T00:00:00Z',
        detail: null,
      },
      {
        id: 'log-evil-2',
        user_id: 'user-2',
        tenant_id: null,
        action: 'user.login',
        resource_type: '-1+1',
        resource_id: null,
        ip_address: '@SUM(A1)',
        created_at: '2024-01-02T00:00:00Z',
        detail: null,
      },
    ];

    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, () => {
        return HttpResponse.json(maliciousLogs);
      }),
    );

    // 拦截 Blob 构造函数来捕获 CSV 内容
    let capturedCsvContent = '';
    const OriginalBlob = globalThis.Blob;
    vi.spyOn(globalThis, 'Blob').mockImplementation((parts?: BlobPart[], options?: BlobPropertyBag) => {
      if (parts && parts.length > 0) {
        capturedCsvContent = String(parts[0]);
      }
      return new OriginalBlob(parts, options);
    });

    globalThis.URL.createObjectURL = vi.fn().mockReturnValue('blob:fake');
    globalThis.URL.revokeObjectURL = vi.fn();

    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'a') {
        const anchor = originalCreateElement('a') as HTMLAnchorElement;
        anchor.click = vi.fn();
        return anchor;
      }
      return originalCreateElement(tag);
    });

    const user = userEvent.setup();
    render(<AuditPage />);

    // 等待恶意数据加载
    await waitFor(() => {
      expect(screen.getByText('user.update')).toBeInTheDocument();
    });

    // 点击导出
    await user.click(screen.getByRole('button', { name: /导出 CSV/ }));

    // 验证恶意字段被转义（添加单引号前缀）
    expect(capturedCsvContent).toContain("'=CMD('calc')");
    expect(capturedCsvContent).toContain("'+1234567");
    expect(capturedCsvContent).toContain("'-1+1");
    expect(capturedCsvContent).toContain("'@SUM(A1)");

    // 验证非恶意字段未被转义
    expect(capturedCsvContent).toContain('log-evil-1');
    expect(capturedCsvContent).toContain('log-evil-2');

    vi.restoreAllMocks();
  });
});

// ─── 分页交互测试 ─────────────────────────────────────────────────────────────

describe('AuditPage 分页交互', () => {
  it('点击"下一页" → page 参数递增 → 重新调用 auditApi.list', async () => {
    let capturedUrl = '';

    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json(MOCK_AUDIT_LOGS);
      }),
    );

    const user = userEvent.setup();
    render(<AuditPage />);

    // 等待初始加载
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 点击"下一页"
    await user.click(screen.getByRole('button', { name: '下一页' }));

    // 验证 page=2
    await waitFor(() => {
      expect(capturedUrl).toContain('page=2');
    });
  });

  it('点击"上一页" → page 参数递减', async () => {
    let capturedUrl = '';

    server.use(
      http.get(`${BASE_URL}/auth/audit-logs`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json(MOCK_AUDIT_LOGS);
      }),
    );

    const user = userEvent.setup();
    render(<AuditPage />);

    // 等待初始加载
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 先到第 2 页
    await user.click(screen.getByRole('button', { name: '下一页' }));
    await waitFor(() => {
      expect(capturedUrl).toContain('page=2');
    });

    // 再点"上一页"回到第 1 页
    await user.click(screen.getByRole('button', { name: '上一页' }));
    await waitFor(() => {
      expect(capturedUrl).toContain('page=1');
    });
  });

  it('第 1 页时"上一页"按钮 disabled', async () => {
    render(<AuditPage />);

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText('user.login')).toBeInTheDocument();
    });

    // 第 1 页时"上一页"按钮应该被禁用
    const prevButton = screen.getByRole('button', { name: '上一页' });
    expect(prevButton).toBeDisabled();
  });
});
