import { Component, ErrorInfo, ReactNode } from 'react';
import { Card, Button, Alert, Space, Typography } from 'antd';
import { ReloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { isBrowser } from '@/utils/env';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: unknown[];
  resetOnPropsChange?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ error, errorInfo });
    if (isBrowser() && import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (this.state.hasError && this.props.resetKeys) {
      const hasResetKeyChanged = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index],
      );
      if (hasResetKeyChanged) {
        this.reset();
      }
    }
    if (
      this.state.hasError &&
      this.props.resetOnPropsChange &&
      this.props.children !== prevProps.children
    ) {
      this.reset();
    }
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleRetry = (): void => {
    this.reset();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 24,
            backgroundColor: 'var(--bg-hover)',
          }}
        >
          <Card
            style={{ maxWidth: 600, width: '100%' }}
            title="应用发生错误"
            extra={
              <Button type="primary" onClick={this.handleRetry} icon={<ReloadOutlined />}>
                重新加载
              </Button>
            }
          >
            <Alert
              message="发生了意外错误"
              description={
                <>
                  <Typography.Text code>{this.state.error?.message}</Typography.Text>
                  {isBrowser() && this.state.errorInfo?.componentStack && (
                    <>
                      <Typography.Paragraph style={{ marginTop: 16 }}>
                        <strong>堆栈跟踪:</strong>
                      </Typography.Paragraph>
                      <Typography.Text
                        code
                        style={{
                          display: 'block',
                          maxHeight: 300,
                          overflow: 'auto',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}
                      >
                        {this.state.errorInfo.componentStack}
                      </Typography.Text>
                    </>
                  )}
                </>
              }
              type="error"
              showIcon
              icon={<ExclamationCircleOutlined />}
              style={{ marginBottom: 24 }}
            />
            <Space direction="vertical" style={{ width: '100%' }}>
              <Typography.Text>
                请尝试点击右上角的&ldquo;重新加载&rdquo;按钮恢复应用。
              </Typography.Text>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                如果问题持续存在，请联系技术支持。
              </Typography.Text>
            </Space>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
