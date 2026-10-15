import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './index.css';

export function mount() {
  const container = document.getElementById('root');
  if (!container) {
    throw new Error('Root element not found');
  }
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <ConfigProvider locale={zhCN}>
        <HashRouter>
          <App />
        </HashRouter>
      </ConfigProvider>
    </React.StrictMode>,
  );
}

// 立即执行并挂载到 window，防止被 tree-shaking 移除
if (typeof window !== 'undefined') {
  (window as any).__APP_MOUNT__ = mount;
  mount();
}