# Storybook 组件文档

本项目使用 [Storybook](https://storybook.js.org/) 构建组件库文档，提供可视化的组件预览、交互测试和文档生成。

## 🚀 快速开始

### 安装依赖
```bash
cd frontend
npm install
```

### 启动开发服务器
```bash
npm run storybook
```
访问 http://localhost:6006 查看组件文档。

### 构建静态文档
```bash
npm run build-storybook
```
生成的静态文件在 `storybook-static/` 目录，可部署到 GitHub Pages、Netlify 等静态托管平台。

## 📁 目录结构

```
frontend/
├── .storybook/
│   ├── main.ts          # Storybook 核心配置
│   └── preview.tsx      # 全局预览配置（装饰器、主题、背景等）
├── src/
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── formatters.stories.tsx      # 格式化工具函数故事
│   ├── pages/
│   │   ├── NotImplemented.tsx
│   │   ├── NotImplemented.stories.tsx  # 通用占位页面故事
│   │   ├── Dashboard.tsx
│   │   └── Dashboard.stories.tsx       # 仪表盘页面故事
│   └── components/                     # 未来可复用组件目录
│       └── Button/
│           ├── Button.tsx
│           ├── Button.stories.tsx
│           └── Button.module.css
```

## 🎨 编写故事指南

### 1. 基础故事模板
```tsx
// Component.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import Component from './Component';

const meta: Meta<typeof Component> = {
  title: 'Category/ComponentName',  // 侧边栏显示路径
  component: Component,
  parameters: {
    layout: 'centered',  // 或 'padded' 用于页面级组件
  },
  tags: ['autodocs'],    // 自动生成文档页
  argTypes: {
    // 定义控件类型
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger'],
    },
    size: {
      control: 'radio',
      options: ['small', 'middle', 'large'],
    },
    onClick: { action: 'clicked' },  // 记录交互
  },
};

export default meta;
type Story = StoryObj<typeof Component>;

// 默认故事
export const Default: Story = {
  args: {
    children: '按钮文字',
    variant: 'primary',
    size: 'middle',
  },
};

// 变体故事
export const Primary: Story = {
  args: { variant: 'primary' },
};

export const Secondary: Story = {
  args: { variant: 'secondary' },
};

export const Loading: Story = {
  args: { loading: true },
};
```

### 2. 复杂组件/页面故事
```tsx
// Dashboard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import Dashboard from './Dashboard';

const meta: Meta<typeof Dashboard> = {
  title: 'Pages/Dashboard',
  component: Dashboard,
  parameters: {
    layout: 'padded',  // 页面级组件使用 padded
  },
  decorators: [
    (Story) => (
      <ConfigProvider locale={zhCN}>
        <Story />
      </ConfigProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Dashboard>;

// 默认状态
export const Default: Story = {
  args: {},
};

// 加载状态
export const Loading: Story = {
  args: { loading: true },
};

// 错误状态
export const WithError: Story = {
  args: { error: new Error('网络错误') },
};

// 空数据
export const EmptyData: Story = {
  args: { stats: { ...mockStats, total_sales_today: 0 } },
};

// 高增长场景
export const HighGrowth: Story = {
  args: { stats: { ...mockStats, total_sales_today: 20000 } },
};
```

### 3. 使用装饰器提供上下文
```tsx
// .storybook/preview.tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

export const decorators = [
  (Story) => (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1890ff' } }}>
      <div style={{ minWidth: 320, padding: 16 }}>
        <Story />
      </div>
    </ConfigProvider>
  ),
];
```

## 🛠 常用配置

### 全局参数 (`.storybook/preview.tsx`)
```tsx
export const parameters = {
  backgrounds: {
    default: 'light',
    values: [
      { name: 'light', value: '#f0f2f5' },
      { name: 'dark', value: '#141414' },
      { name: 'white', value: '#ffffff' },
    ],
  },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/i,
    },
  },
  globalTypes: {
    locale: {
      description: '国际化语言',
      defaultValue: 'zh-CN',
      toolbar: {
        title: '语言',
        icon: 'globe',
        items: ['zh-CN', 'en-US'],
      },
    },
  },
};
```

### 布局模式
| 模式 | 适用场景 |
|------|---------|
| `centered` | 单个组件、按钮、卡片等居中展示 |
| `padded` | 页面级组件、表单、列表等需要内边距 |
| `fullscreen` | 全屏页面、布局组件 |

## 📦 现有故事清单

| 文件 | 标题 | 说明 |
|------|------|------|
| `formatters.stories.tsx` | Utilities/Formatters | 格式化工具函数可视化测试 |
| `NotImplemented.stories.tsx` | Pages/NotImplemented | 通用占位页面各种变体 |
| `Dashboard.stories.tsx` | Pages/Dashboard | 仪表盘完整页面各种状态 |

## 🔧 开发工作流

1. **新建组件** → 同目录创建 `Component.stories.tsx`
2. **编写故事** → 覆盖默认、加载、错误、边界等状态
3. **本地预览** → `npm run storybook` 实时查看
4. **交互测试** → 使用 Controls 面板调整 props，Actions 面板查看事件
5. **文档生成** → 自动生成 Docs 页，支持 MDX 扩展
6. **构建部署** → `npm run build-storybook` → 部署静态站点

## 🌐 部署建议

### GitHub Pages
```yaml
# .github/workflows/storybook.yml
name: Deploy Storybook
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with: { node-version: '18' }
      - run: cd frontend && npm ci && npm run build-storybook
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/storybook-static
```

### Netlify/Vercel
直接连接 Git 仓库，设置构建命令 `cd frontend && npm run build-storybook`，发布目录 `frontend/storybook-static`。

## 📚 扩展阅读

- [Storybook 官方文档](https://storybook.js.org/docs)
- [Writing Stories](https://storybook.js.org/docs/react/writing-stories/introduction)
- [Essential Addons](https://storybook.js.org/addons)
- [Testing with Storybook](https://storybook.js.org/docs/react/writing-tests/introduction)
- [Chromatic 视觉回归测试](https://www.chromatic.com/)