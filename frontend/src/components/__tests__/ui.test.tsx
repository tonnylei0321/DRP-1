import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Btn, Card, Modal, Input, Badge, ErrorBox, EmptyState, Spinner, PageHeader, sanitizeErrorMessage } from '../ui';

// ─── Btn 组件 ────────────────────────────────────────────────────────────────

describe('Btn', () => {
  it('variant="primary" 渲染包含 btn-primary 类名的按钮', () => {
    render(<Btn variant="primary">确认</Btn>);
    const btn = screen.getByRole('button', { name: '确认' });
    expect(btn).toHaveClass('btn', 'btn-primary');
  });

  it('variant="danger" 渲染包含 btn-danger 类名的按钮', () => {
    render(<Btn variant="danger">删除</Btn>);
    const btn = screen.getByRole('button', { name: '删除' });
    expect(btn).toHaveClass('btn', 'btn-danger');
  });

  it('onClick 回调被触发恰好一次', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(<Btn onClick={handleClick}>点击</Btn>);
    await user.click(screen.getByRole('button', { name: '点击' }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

// ─── Modal 组件 ──────────────────────────────────────────────────────────────

describe('Modal', () => {
  it('显示标题文本和子内容', () => {
    render(
      <Modal title="测试标题" onClose={() => {}}>
        <p>子内容文本</p>
      </Modal>
    );
    expect(screen.getByText('测试标题')).toBeInTheDocument();
    expect(screen.getByText('子内容文本')).toBeInTheDocument();
  });

  it('点击关闭按钮调用 onClose 回调', () => {
    const handleClose = vi.fn();
    render(
      <Modal title="标题" onClose={handleClose}>
        <p>内容</p>
      </Modal>
    );
    fireEvent.click(screen.getByText('×'));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});


// ─── Input 组件 ──────────────────────────────────────────────────────────────

describe('Input', () => {
  it('传入 label 属性渲染 <label> 元素', () => {
    render(<Input label="用户名" />);
    expect(screen.getByText('用户名')).toBeInTheDocument();
    expect(screen.getByText('用户名').tagName).toBe('LABEL');
  });
});

// ─── Badge 组件 ──────────────────────────────────────────────────────────────

describe('Badge', () => {
  it('variant="success" 渲染包含 badge-success 类名的 span', () => {
    render(<Badge label="正常" variant="success" />);
    const badge = screen.getByText('正常');
    expect(badge.tagName).toBe('SPAN');
    expect(badge).toHaveClass('badge', 'badge-success');
  });
});

// ─── ErrorBox 组件 ───────────────────────────────────────────────────────────

describe('ErrorBox', () => {
  it('显示传入的错误消息文本', () => {
    render(<ErrorBox message="请求失败" />);
    expect(screen.getByText('请求失败')).toBeInTheDocument();
  });
});

// ─── ErrorBox 脱敏 ───────────────────────────────────────────────────────────

describe('ErrorBox 脱敏', () => {
  it('包含内部路径的错误消息被脱敏', () => {
    render(<ErrorBox message="Error at /app/src/drp/auth/service.py:42" />);
    expect(screen.queryByText(/\/app\/src/)).not.toBeInTheDocument();
    expect(screen.getByText(/操作失败/)).toBeInTheDocument();
  });

  it('包含 SQL 关键字的错误消息被脱敏', () => {
    render(<ErrorBox message='relation "users" does not exist' />);
    expect(screen.queryByText(/relation/)).not.toBeInTheDocument();
    expect(screen.getByText(/操作失败/)).toBeInTheDocument();
  });

  it('包含堆栈跟踪的错误消息被脱敏', () => {
    render(<ErrorBox message="Traceback (most recent call last):\n  File main.py" />);
    expect(screen.queryByText(/Traceback/)).not.toBeInTheDocument();
    expect(screen.getByText(/操作失败/)).toBeInTheDocument();
  });

  it('普通错误消息不被脱敏', () => {
    render(<ErrorBox message="请求失败" />);
    expect(screen.getByText('请求失败')).toBeInTheDocument();
  });
});

// ─── EmptyState 组件 ─────────────────────────────────────────────────────────

describe('EmptyState', () => {
  it('显示传入的提示消息文本', () => {
    render(<EmptyState message="暂无数据" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });
});

// ─── Spinner 组件 ────────────────────────────────────────────────────────────

describe('Spinner', () => {
  it('显示"加载中..."文本', () => {
    render(<Spinner />);
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });
});

// ─── Card 组件 ───────────────────────────────────────────────────────────────

describe('Card', () => {
  it('子元素包裹在 card 类名容器中', () => {
    render(<Card><span>卡片内容</span></Card>);
    const content = screen.getByText('卡片内容');
    expect(content.closest('.card')).toBeInTheDocument();
  });
});

// ─── PageHeader 组件 ─────────────────────────────────────────────────────────

describe('PageHeader', () => {
  it('显示标题文本', () => {
    render(<PageHeader title="用户管理" />);
    expect(screen.getByText('用户管理')).toBeInTheDocument();
  });

  it('渲染 action 区域', () => {
    render(<PageHeader title="标题" action={<button>新建</button>} />);
    expect(screen.getByRole('button', { name: '新建' })).toBeInTheDocument();
  });
});
