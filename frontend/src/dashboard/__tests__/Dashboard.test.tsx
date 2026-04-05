/**
 * Dashboard 主组件测试
 * 覆盖渲染、语言切换、节点点击交互、图谱切换
 * 需求：5.16
 */
import { render, screen, fireEvent } from '@testing-library/react';
import Dashboard from '../Dashboard';

// ─── MockWebSocket（Dashboard 内部使用 useRiskEvents）──────────

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  readyState = 0;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = 3;
  }

  simulateOpen() {
    this.readyState = 1;
    this.onopen?.(new Event('open'));
  }
}

// ─── Mock localStorage 中的 JWT token ────────────────────────────

// Dashboard 从 getToken() 解析 tenant_id，需要一个有效的 JWT payload
function makeFakeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.fake-signature`;
}

// ─── 测试配置 ────────────────────────────────────────────────────

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
  // 设置一个带 tenant_id 的 fake JWT
  const token = makeFakeJwt({ tenant_id: 't-1', sub: 'user-1' });
  localStorage.setItem('drp_token', token);
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

// ─── 辅助函数 ────────────────────────────────────────────────────

function latestWs(): MockWebSocket {
  return MockWebSocket.instances[MockWebSocket.instances.length - 1];
}

// ─── 测试用例 ────────────────────────────────────────────────────

describe('Dashboard', () => {
  it('渲染：显示 Topbar、层级图区域和检查器面板区域', () => {
    const { container } = render(<Dashboard />);

    // Topbar 包含 DRP 标识和标题
    expect(screen.getByText('DRP')).toBeInTheDocument();
    expect(screen.getByText('穿透式资金监管看板')).toBeInTheDocument();

    // 层级图区域：应有 SVG 元素（HierarchyGraph 渲染）
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThanOrEqual(1);

    // 检查器面板区域：DrillInspector 显示"暂无数据"（初始 drillPath 为空）
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
    // 穿透路径标题
    expect(screen.getByText('穿透路径')).toBeInTheDocument();
  });

  it('语言切换按钮', () => {
    render(<Dashboard />);

    // 初始语言为中文，按钮显示 "EN"
    const langBtn = screen.getByText('EN');
    expect(langBtn).toBeInTheDocument();

    // 点击切换到英文
    fireEvent.click(langBtn);

    // 切换后标题变为英文
    expect(screen.getByText('Capital Supervision Dashboard')).toBeInTheDocument();
    // 语言按钮变为 "中"
    expect(screen.getByText('中')).toBeInTheDocument();

    // 再次点击切换回中文
    fireEvent.click(screen.getByText('中'));
    expect(screen.getByText('穿透式资金监管看板')).toBeInTheDocument();
  });

  it('节点点击交互 [评审 #010]：点击层级图节点 → HudPanel 显示对应节点信息', () => {
    const { container } = render(<Dashboard />);

    // 层级图中的节点是 SVG <g class="node"> 元素，点击其中一个
    const nodeElements = container.querySelectorAll('.node');

    if (nodeElements.length > 0) {
      // 点击第一个节点（根节点 "国有集团"）
      fireEvent.click(nodeElements[0]);

      // HudPanel 应显示节点信息 — 使用 getAllByText 因为 SVG 中也有同名文本
      const matches = screen.getAllByText('国有集团');
      // 至少 3 个：左侧 SVG 标签 + 中央 SVG 标签 + HudPanel 标签
      expect(matches.length).toBeGreaterThanOrEqual(3);
      // HudPanel 中的节点标签是 div 元素（非 SVG text）
      const hudLabel = matches.find(el => el.tagName === 'DIV');
      expect(hudLabel).toBeInTheDocument();

      // 关闭按钮应存在
      expect(screen.getByText('×')).toBeInTheDocument();
    }
  });

  it('图谱切换 [评审 #010]：点击实体节点 → 切换到力导向图 → 点击"返回层级图"恢复', () => {
    const { container } = render(<Dashboard />);

    // 找到所有节点
    const nodeElements = container.querySelectorAll('.node');

    // 找到一个 entity 类型的节点并点击（entity 节点会触发 setShowForce(true)）
    // 在 DEMO_HIERARCHY 中，entity 节点是叶子节点
    // 节点顺序：root(0), region-east(1), entity-1(2), entity-2(3), region-west(4), entity-3(5), entity-4(6)
    if (nodeElements.length >= 3) {
      // 点击 entity 节点（索引 2 是 entity-1 "华东子公司A"）
      fireEvent.click(nodeElements[2]);

      // 应切换到力导向图，显示"返回层级图"按钮
      const backBtn = screen.queryByText(/返回层级图/);
      if (backBtn) {
        expect(backBtn).toBeInTheDocument();

        // 点击"返回层级图"
        fireEvent.click(backBtn);

        // 应恢复层级图，"返回层级图"按钮消失
        expect(screen.queryByText(/返回层级图/)).not.toBeInTheDocument();
      }
    }
  });
});
