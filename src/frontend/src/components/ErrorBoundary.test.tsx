import { describe, it, expect, vi, afterEach, beforeAll, afterAll } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

// 抑制 React 错误边界 console.error 输出
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    const first = args[0];
    if (typeof first === 'string' && first.includes('The above error occurred in the')) {
      return;
    }
    originalError.call(console, ...args);
  };
});
afterAll(() => {
  console.error = originalError;
});

// 测试用的会抛出错误的子组件
const ThrowOnRender = ({ error }: { error: Error }) => {
  throw error;
};

// 测试用的会抛出错误的子组件（带条件）
const ConditionalThrow = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Conditional error');
  }
  return <div data-testid="child-content">正常内容</div>;
};

describe('ErrorBoundary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('无错误时应正常渲染子组件', () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">Hello World</div>
      </ErrorBoundary>,
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('子组件抛出错误时应显示默认错误 UI', () => {
    render(
      <ErrorBoundary>
        <ThrowOnRender error={new Error('Test crash')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('应用发生错误')).toBeInTheDocument();
    expect(screen.getByText('Test crash')).toBeInTheDocument();
    expect(screen.getByText('重新加载')).toBeInTheDocument();
  });

  it('提供 fallback 时应使用自定义 fallback', () => {
    render(
      <ErrorBoundary fallback={<div data-testid="custom-fallback">自定义错误</div>}>
        <ThrowOnRender error={new Error('Crash')} />
      </ErrorBoundary>,
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.queryByText('应用发生错误')).not.toBeInTheDocument();
  });

  it('onError 回调应被调用', () => {
    const onError = vi.fn();
    const error = new Error('Callback test');

    render(
      <ErrorBoundary onError={onError}>
        <ThrowOnRender error={error} />
      </ErrorBoundary>,
    );

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledWith(
      error,
      expect.objectContaining({
        componentStack: expect.any(String),
      }),
    );
  });

  it('点击"重新加载"按钮应重置错误状态', async () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowOnRender error={new Error('Reset test')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('应用发生错误')).toBeInTheDocument();

    // 先 rerender 不抛错的 children（但 ErrorBoundary 仍显示错误，因为 hasError=true）
    rerender(
      <ErrorBoundary>
        <ConditionalThrow shouldThrow={false} />
      </ErrorBoundary>,
    );

    // 点击"重新加载"重置 hasError，然后渲染新的不抛错的 children
    await fireEvent.click(screen.getByText('重新加载'));

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.queryByText('应用发生错误')).not.toBeInTheDocument();
  });

  it('resetKeys 变化时应重置错误状态', () => {
    const { rerender } = render(
      <ErrorBoundary resetKeys={[1]}>
        <ThrowOnRender error={new Error('Key reset')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('应用发生错误')).toBeInTheDocument();

    // 改变 resetKeys
    rerender(
      <ErrorBoundary resetKeys={[2]}>
        <ConditionalThrow shouldThrow={false} />
      </ErrorBoundary>,
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('resetOnPropsChange=true 且 children 变化时应重置', () => {
    const { rerender } = render(
      <ErrorBoundary resetOnPropsChange>
        <ThrowOnRender error={new Error('Props reset')} />
      </ErrorBoundary>,
    );

    expect(screen.getByText('应用发生错误')).toBeInTheDocument();

    rerender(
      <ErrorBoundary resetOnPropsChange>
        <ConditionalThrow shouldThrow={false} />
      </ErrorBoundary>,
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });
});
