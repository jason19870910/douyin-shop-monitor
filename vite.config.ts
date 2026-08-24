import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'remove-crossorigin',
      transformIndexHtml(html) {
        // 首先移除 crossorigin
        html = html
          .replace(/<script type="module" crossorigin /g, '<script type="module" ')
          .replace(/<link rel="modulepreload" crossorigin /g, '<link rel="modulepreload" ')
          .replace(/<link rel="stylesheet" crossorigin /g, '<link rel="stylesheet" ');
        // 注入 bootstrap：双重保险 + 重试机制
        const mainModuleMatch = html.match(/<script type="module" src="(\/assets\/index-[^"]+\.js)"><\/script>/);
        if (mainModuleMatch) {
          const mainModule = mainModuleMatch[1];
          const bootstrapScript = `
  <script type="module">
    // 1. 导入主模块触发自动执行
    await import('${mainModule}');
    console.log('✅ 主模块加载完成');
  </script>
  <script>
    // 2. 兜底：带重试机制的全局 mount 调用
    let retryCount = 0;
    const maxRetries = 30; // 3秒最多重试 30 次
    const checkAndMount = () => {
      if (window.__APP_MOUNT__ && typeof window.__APP_MOUNT__ === 'function') {
        console.log('🔄 兜底调用 window.__APP_MOUNT__()');
        try {
          window.__APP_MOUNT__();
          console.log('✅ 兜底调用成功');
        } catch (e) {
          console.error('❌ 兜底调用失败:', e);
        }
        return true;
      }
      return false;
    };
    
    // 立即检查一次
    if (!checkAndMount()) {
      // 如果没找到，开始重试
      const interval = setInterval(() => {
        retryCount++;
        if (checkAndMount()) {
          clearInterval(interval);
        } else if (retryCount >= 30) {
          clearInterval(interval);
          console.warn('⚠️ 重试 30 次仍未找到 window.__APP_MOUNT__');
        }
      }, 100);
    }
  </script>
</body>`;
          html = html.replace('</body>', bootstrapScript);
        }
        return html;
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
    },
  },
});