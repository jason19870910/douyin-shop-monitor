import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import Layout from './Layout/Layout';
import { ClientOnly } from './components/ClientOnly';
import { ErrorBoundary } from './components/ErrorBoundary';
import { queryClient } from './hooks/queryClient';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary
        fallback={<div className="loading">应用加载失败，请刷新重试</div>}
        onError={(error) => {
          if (import.meta.env.DEV) {
            console.error('App ErrorBoundary:', error);
          }
        }}
      >
        <ClientOnly fallback={<div className="loading">加载中...</div>}>
          <Layout />
        </ClientOnly>
      </ErrorBoundary>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
