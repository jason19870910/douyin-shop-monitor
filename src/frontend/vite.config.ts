import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Inject VITE_API_KEY at build time from environment
const viteApiKey = process.env.VITE_API_KEY || 'your_api_key_here';

export default defineConfig({
  define: {
    'import.meta.env.VITE_API_KEY': JSON.stringify(viteApiKey),
  },
  plugins: [
    react(),
    {
      name: 'remove-crossorigin',
      transformIndexHtml(html) {
        // 移除 crossorigin 属性
        return html
          .replace(/<script type="module" crossorigin /g, '<script type="module" ')
          .replace(/<link rel="modulepreload" crossorigin /g, '<link rel="modulepreload" ')
          .replace(/<link rel="stylesheet" crossorigin /g, '<link rel="stylesheet" ');
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
        secure: false,
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