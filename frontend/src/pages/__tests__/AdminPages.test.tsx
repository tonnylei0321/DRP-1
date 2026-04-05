import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { MOCK_ETL_JOBS, MOCK_TENANTS, MOCK_QUALITY } from '../../test/mocks/handlers';
import { EtlPage, TenantsPage, QualityPage } from '../AdminPages';
import { clearToken, setToken } from '../../api/client';
import type { Tenant, DataQuality } from '../../api/client';

const BASE_URL = 'http://localhost:8000';

beforeEach(() => {
  clearToken();
  setToken('test-token');
});

// ─── EtlPage 测试 ────────────────────────────────────────────────────────────

describe('EtlPage', () => {
  it('调用 etlApi.list 并显示 ETL 任务表格（任务ID、类型、状态、写入三元组数、耗时、错误信息列）', async () => {
    render(<EtlPage />);

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText(/job-1/)).toBeInTheDocument();
    });

    // 验证表头列
    expect(screen.getByText('任务 ID')).toBeInTheDocument();
    expect(screen.getByText('类型')).toBeInTheDocument();
    expect(screen.getByText('状态')).toBeInTheDocument();
    expect(screen.getByText('写入三元组')).toBeInTheDocument();
    expect(screen.getByText('耗时')).toBeInTheDocument();
    expect(screen.getByText('错误')).toBeInTheDocument();

    // 验证 mock 数据渲染
    expect(screen.getByText('full_sync')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('1,500')).toBeInTheDocument();
  });
});

// ─── TenantsPage 测试 ─────────────────────────────────────────────────────────

describe('TenantsPage 渲染', () => {
  it('调用 tenantsApi.list 并显示租户列表', async () => {
    render(<TenantsPage />);

    await waitFor(() => {
      expect(screen.getByText('测试租户')).toBeInTheDocument();
    });

    // 验证表头
    expect(screen.getByText('名称')).toBeInTheDocument();
    expect(screen.getByText('Graph IRI')).toBeInTheDocument();
    expect(screen.getByText('状态')).toBeInTheDocument();
    expect(screen.getByText('创建时间')).toBeInTheDocument();
    expect(screen.getByText('操作')).toBeInTheDocument();

    // 验证 mock 数据
    expect(screen.getByText('urn:drp:tenant:t-1')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });
});

describe('TenantsPage 新建租户', () => {
  it('新建租户 → 调用 tenantsApi.create → 刷新列表', async () => {
    let listCallCount = 0;
    const newTenant: Tenant = {
      id: 't-new',
      name: '新租户',
      graph_iri: 'urn:drp:tenant:t-new',
      status: 'active',
      created_at: new Date().toISOString(),
    };

    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          return HttpResponse.json([...MOCK_TENANTS, newTenant]);
        }
        return HttpResponse.json(MOCK_TENANTS);
      }),
    );

    const user = userEvent.setup();
    render(<TenantsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('测试租户')).toBeInTheDocument();
    });

    // 点击"新建租户"按钮
    await user.click(screen.getByRole('button', { name: /新建租户/ }));

    // 验证 Modal 显示
    expect(screen.getByRole('heading', { name: '新建租户' })).toBeInTheDocument();

    // 填写租户名称 — Input 组件的 label 未通过 htmlFor 关联，直接查找 input
    const modal = document.querySelector('[style*="position: fixed"]')!;
    const nameInput = modal.querySelector('input')!;
    await user.type(nameInput, '新租户');

    // 提交
    await user.click(screen.getByRole('button', { name: '创建' }));

    // 等待列表刷新，新租户出现
    await waitFor(() => {
      expect(screen.getByText('新租户')).toBeInTheDocument();
    });

    // Modal 已关闭
    expect(screen.queryByRole('heading', { name: '新建租户' })).not.toBeInTheDocument();
  });
});

describe('TenantsPage 删除租户', () => {
  it('点击"删除" → 显示自定义确认 Modal → 点击确认 → 调用 tenantsApi.delete → 刷新列表', async () => {
    let listCallCount = 0;
    let deletedUrl = '';

    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        listCallCount++;
        if (listCallCount >= 2) {
          return HttpResponse.json([]);
        }
        return HttpResponse.json(MOCK_TENANTS);
      }),
      http.delete(`${BASE_URL}/tenants/:id`, ({ request }) => {
        deletedUrl = request.url;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const user = userEvent.setup();
    render(<TenantsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('测试租户')).toBeInTheDocument();
    });

    // 点击"删除"按钮
    await user.click(screen.getByRole('button', { name: '删除' }));

    // 验证确认 Modal 显示
    expect(screen.getByRole('heading', { name: '确认删除' })).toBeInTheDocument();
    expect(screen.getByText(/确认删除该租户/)).toBeInTheDocument();

    // 点击"确认删除"
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    // 等待列表刷新，租户消失
    await waitFor(() => {
      expect(screen.queryByText('测试租户')).not.toBeInTheDocument();
    });

    // 显示空状态
    expect(screen.getByText('暂无租户')).toBeInTheDocument();

    // 验证 DELETE 请求 URL 包含正确的租户 ID
    expect(deletedUrl).toContain('/tenants/t-1');
  });

  it('确认 Modal 中点击"取消" → 关闭 Modal → 列表不变', async () => {
    const user = userEvent.setup();
    render(<TenantsPage />);

    // 等待初始列表加载
    await waitFor(() => {
      expect(screen.getByText('测试租户')).toBeInTheDocument();
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
    expect(screen.getByText('测试租户')).toBeInTheDocument();
  });
});

// ─── QualityPage 测试 ─────────────────────────────────────────────────────────

describe('QualityPage', () => {
  it('调用 tenantsApi.list 获取租户列表 → 选择第一个租户 → 调用 qualityApi.get → 显示质量评分', async () => {
    render(<QualityPage />);

    // 等待租户列表加载并自动选择第一个租户
    await waitFor(() => {
      expect(screen.getByText('综合质量评分')).toBeInTheDocument();
    });

    // 验证质量评分数据渲染
    expect(screen.getByText('90.5')).toBeInTheDocument();
    expect(screen.getByText('健康')).toBeInTheDocument();

    // 验证租户下拉框包含 mock 租户
    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('t-1');
  });
});

// ─── 租户隔离测试 [评审 #002] ─────────────────────────────────────────────────

describe('QualityPage 租户隔离', () => {
  it('切换 tenant_id 后页面数据重新加载，API 请求携带正确 tenant_id', async () => {
    const qualityRequests: string[] = [];

    const tenant2: Tenant = {
      id: 't-2',
      name: '第二租户',
      graph_iri: 'urn:drp:tenant:t-2',
      status: 'active',
      created_at: '2024-02-01T00:00:00Z',
    };

    const quality2: DataQuality = {
      tenant_id: 't-2',
      null_rate: 0.10,
      latency_seconds: 300,
      format_compliance: 0.80,
      overall: 75.0,
      is_healthy: false,
    };

    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return HttpResponse.json([...MOCK_TENANTS, tenant2]);
      }),
      http.get(`${BASE_URL}/etl/quality/:tenantId`, ({ params }) => {
        const tenantId = params.tenantId as string;
        qualityRequests.push(tenantId);
        if (tenantId === 't-2') {
          return HttpResponse.json(quality2);
        }
        return HttpResponse.json(MOCK_QUALITY);
      }),
    );

    const user = userEvent.setup();
    render(<QualityPage />);

    // 等待初始加载（第一个租户的质量数据）
    await waitFor(() => {
      expect(screen.getByText('90.5')).toBeInTheDocument();
    });

    // 验证第一次请求携带 t-1
    expect(qualityRequests).toContain('t-1');

    // 切换到第二个租户
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 't-2');

    // 等待第二个租户的质量数据加载
    await waitFor(() => {
      expect(screen.getByText('75.0')).toBeInTheDocument();
    });

    // 验证第二次请求携带 t-2
    expect(qualityRequests).toContain('t-2');

    // 验证前一租户的数据不再显示
    expect(screen.queryByText('90.5')).not.toBeInTheDocument();

    // 验证健康状态更新
    expect(screen.getByText('需关注')).toBeInTheDocument();
  });
});

// ─── EtlPage 空列表 ─────────────────────────────────────────────────────────

describe('EtlPage 空列表', () => {
  it('etlApi.list 返回空数组时显示 EmptyState', async () => {
    server.use(
      http.get(`${BASE_URL}/etl/jobs`, () => {
        return HttpResponse.json([]);
      }),
    );

    render(<EtlPage />);

    await waitFor(() => {
      expect(screen.getByText('暂无 ETL 任务记录')).toBeInTheDocument();
    });
  });
});

// ─── EtlPage 错误处理 ───────────────────────────────────────────────────────

describe('EtlPage 错误处理', () => {
  it('etlApi.list 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.get(`${BASE_URL}/etl/jobs`, () => {
        return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
      }),
    );

    render(<EtlPage />);

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});

// ─── EtlPage statusBadge 分支 ───────────────────────────────────────────────

describe('EtlPage statusBadge 分支', () => {
  it('渲染 failed/running/pending 等不同状态的 ETL 任务', async () => {
    server.use(
      http.get(`${BASE_URL}/etl/jobs`, () => {
        return HttpResponse.json([
          { ...MOCK_ETL_JOBS[0], id: 'j-1', status: 'failed', error_message: '连接超时', finished_at: null },
          { ...MOCK_ETL_JOBS[0], id: 'j-2', status: 'running', finished_at: null },
          { ...MOCK_ETL_JOBS[0], id: 'j-3', status: 'pending', finished_at: null },
        ]);
      }),
    );

    render(<EtlPage />);

    await waitFor(() => {
      expect(screen.getByText('failed')).toBeInTheDocument();
    });

    expect(screen.getByText('running')).toBeInTheDocument();
    expect(screen.getByText('pending')).toBeInTheDocument();
    expect(screen.getByText('连接超时')).toBeInTheDocument();
  });
});

// ─── TenantsPage 错误处理 ───────────────────────────────────────────────────

describe('TenantsPage 错误处理', () => {
  it('tenantsApi.list 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
      }),
    );

    render(<TenantsPage />);

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});

// ─── TenantsPage statusBadge 分支 ───────────────────────────────────────────

describe('TenantsPage statusBadge 分支', () => {
  it('渲染 suspended 和 deleted 状态的租户', async () => {
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return HttpResponse.json([
          { ...MOCK_TENANTS[0], id: 't-s', name: '暂停租户', status: 'suspended' },
          { ...MOCK_TENANTS[0], id: 't-d', name: '已删除租户', status: 'deleted' },
        ]);
      }),
    );

    render(<TenantsPage />);

    await waitFor(() => {
      expect(screen.getByText('暂停租户')).toBeInTheDocument();
    });

    expect(screen.getByText('suspended')).toBeInTheDocument();
    expect(screen.getByText('deleted')).toBeInTheDocument();
  });
});

// ─── QualityPage 无质量数据 ─────────────────────────────────────────────────

describe('QualityPage 无质量数据', () => {
  it('qualityApi.get 返回错误时显示 EmptyState', async () => {
    server.use(
      http.get(`${BASE_URL}/etl/quality/:tenantId`, () => {
        return HttpResponse.json({ detail: '无数据' }, { status: 404 });
      }),
    );

    render(<QualityPage />);

    await waitFor(() => {
      expect(screen.getByText('暂无质量数据')).toBeInTheDocument();
    });
  });
});

// ─── QualityPage 租户列表加载失败 ───────────────────────────────────────────

describe('QualityPage 租户列表加载失败', () => {
  it('tenantsApi.list 返回错误时显示 ErrorBox', async () => {
    server.use(
      http.get(`${BASE_URL}/tenants`, () => {
        return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
      }),
    );

    render(<QualityPage />);

    await waitFor(() => {
      expect(screen.getByText(/500/)).toBeInTheDocument();
    });
  });
});
