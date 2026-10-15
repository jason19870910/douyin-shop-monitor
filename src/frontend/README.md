# 前端项目文档

> **适用范围**：`/opt/douyin-platform/src/frontend` 目录
> **维护周期**：每月评审一次，代码提交前自动校验
> **最后更新**：2026-10-07

---

## 目录
1. [快速开始](#1-快速开始)
2. [项目结构](#2-项目结构)
3. [5S 管理规范](#3-5s-管理规范)
4. [Storybook 组件文档](#4-storybook-组件文档)
5. [开发工作流](#5-开发工作流)
6. [常用命令](#6-常用命令)
7. [维护记录](#7-维护记录)

---

## 1. 快速开始

### 环境要求
- Node.js 18+
- npm 9+

### 安装依赖
```bash
cd /opt/douyin-platform/src/frontend
npm install
```

### 启动开发服务器
```bash
npm run dev          # 启动 Vite 开发服务器 (默认 http://localhost:3000)
```

### 构建生产版本
```bash
npm run build        # 生产构建 (tsc + vite build)，输出到 build/
```

### 预览构建产物
```bash
npm run preview      # 本地预览 build/ 目录
```

### 代码质量
```bash
npm run lint         # ESLint 检查
npm run lint --fix   # 自动修复
npx tsc --noEmit     # TypeScript 类型检查
```

### Storybook
```bash
npm run storybook           # 启动 Storybook
npm run build-storybook     # 构建静态文档
```

---

## 2. 项目结构

```
src/
├── api/               # API 接口定义与类型封装 (index.ts)
├── components/        # UI 组件
│   ├── dashboard/     # 仪表盘业务组件
│   ├── layout/        # 布局组件
│   ├── ...            # 通用组件 (按需创建)
├── hooks/             # React Hook 封装 (useApi.ts 等)
├── pages/             # 页面组件 (Dashboard.tsx, Products.tsx 等)
├── utils/             # 通用工具函数
│   ├── apiClient.ts   # 统一 HTTP 客户端 (单一入口)
│   ├── config.ts      # 环境配置
│   ├── formatters.ts  # 格式化工具
│   ├── env.ts         # 环境变量处理
├── theme/             # 主题/设计系统 (tokens.ts, variables.css)
├── Layout/            # 布局组件
├── App.tsx            # 应用根组件
├── index.tsx          # 应用入口
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 目录 | kebab-case | `components/dashboard/` |
| 组件文件 | PascalCase | `MetricCard.tsx` |
| 页面/工具文件 | camelCase | `formatters.ts` |
| 样式模块 | PascalCase.module.css | `MetricCard.module.css` |
| Hook | use + PascalCase | `useApi.ts` |

### 路径别名 (tsconfig.json)
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

### 导入顺序规范
```typescript
// 1. 类型导入
import type { Product, Order } from '@/api/index';

// 2. 外部库
import React from 'react';
import { Card, Button } from 'antd';

// 3. 内部模块 (使用 @ 别名)
import { useApi } from '@/hooks/useApi';
import { productApi } from '@/api/index';
import { formatNumber } from '@/utils/formatters';
```

---

## 3. 5S 管理规范

项目全链路贯彻 5S 管理原则保持代码整洁、有序、可持续。

### 3.1 整理 (Sort - 消除冗余)

**已完成**：
- [x] 统一 HTTP 客户端：仅保留 `src/utils/apiClient.ts` 作为单一入口
- [x] 清理冗余/过期 nginx 配置：`nginx-douyin.conf`、`nginx-main.conf`、`nginx-main-cors.conf`
- [x] 清理构建产物：`build/`、`node_modules/.cache`、`.vite` 缓存
- [x] 清理临时文件：`*.log`、`*.tmp`、`*.old`、`eslint-output.json`

**周期性自检**：
```bash
# 检查是否有重复 apiClient 实现
find src -name "apiClient.ts" -type f

# 检查遗留/缓存文件
find . -name "*.log" -o -name "*.tmp" -o -name "*.old" -o -name "*.cache" | grep -v node_modules

# 检查未跟踪文件
git status --porcelain
```

### 3.2 整顿 (Set in Order - 目录规范)

标准目录结构已在 [项目结构](#2-项目结构) 定义，新增文件需遵循：
- 组件放入 `components/` 对应业务域
- 页面放入 `pages/`
- Hook 放入 `hooks/`
- 工具函数放入 `utils/`
- 主题相关放入 `theme/`

### 3.3 清扫 (Shine - 清理产物)

**自动化清理脚本**：
```json
// package.json scripts
{
  "clean": "rimraf build dist .vite node_modules/.cache",
  "clean:all": "npm run clean && rimraf node_modules package-lock.json"
}
```

**CI/CD 集成**：
```yaml
# .github/workflows/ci.yml
- name: Clean workspace
  run: |
    npm run clean
    npm ci
```

### 3.4 标准化 (Standardize - 代码规范)

**ESLint 关键规则** (`eslint.config.mjs`)：
- TypeScript 推荐规则
- React Hooks 规范检查 (`react-hooks/exhaustive-deps`)
- 禁止 `any` (`@typescript-eslint/no-explicit-any: warn`)
- 禁止未使用变量 (`@typescript-eslint/no-unused-vars: warn`)

**Pre-commit 守护** (husky)：
```bash
# .husky/pre-commit
cd /opt/douyin-platform/src/frontend && npm run lint && npx tsc --noEmit
```

### 3.5 素养 (Sustain - 持续维护)

**维护 SOP**：

| 频次 | 动作 | 责任人 |
|------|------|--------|
| 每次提交 | husky pre-commit 自动执行 lint + tsc | 全员 |
| 每次 PR | CI 执行 lint + test + build | CI/CD |
| 每月 | 例行巡查目录结构、依赖更新、文档同步 | Tech Lead |
| 每季度 | 组件库梳理、大版本依赖升级、文档更新 | 全员 |

**依赖管理**：
- `package-lock.json` 锁定版本
- 定期 `npm audit` 检查安全漏洞
- 大版本升级需 PR 评审把关

**文档同步**：
- 代码变更同步更新类型定义
- API 变更需更新 `src/api/index.ts` 导出
- 新增组件需在对应 `index.ts` 导出

---

## 4. Storybook 组件文档

项目采用 [Storybook](https://storybook.js.org/) 构建组件文档，提供可视化的组件预览、交互测试和文档生成。

### 4.1 目录结构
```
frontend/
├── .storybook/
│   ├── main.ts          # Storybook 核心配置
│   └── preview.tsx      # 全局预览配置 (容器、主题、全局样式)
├── src/
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── formatters.stories.tsx      # 格式化工具函数故事
│   ├── pages/
│   │   ├── NotImplemented.tsx
│   │   ├── NotImplemented.stories.tsx  # 通用占位页面故事
│   │   ├── Dashboard.tsx
│   │   └── Dashboard.stories.tsx       # 仪表盘页面故事
│   ├── components/                     # 未来组件故事存放域
│       ├── Button/
│           ├── Button.tsx
│           ├── Button.stories.tsx
│           └── Button.module.css
```

### 4.2 故事编写规范

#### 基础组件故事模板
```tsx
// Component.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import Component from './Component';

const meta: Meta<typeof Component> = {
  title: 'Category/ComponentName',  // 便于目录树展示
  component: Component,
  parameters: {
    layout: 'centered',  // 或 'padded' 用于页面级组件
  },
  tags: ['autodocs'],    // 自动生成文档页面
  argTypes: {
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

export const Default: Story = {
  args: { children: '按钮文本', variant: 'primary', size: 'middle' },
};
export const Primary: Story = { args: { variant: 'primary' } };
export const Secondary: Story = { args: { variant: 'secondary' } };
export const Loading: Story = { args: { loading: true } };
```

#### 页面级故事模板
```tsx
// Dashboard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import Dashboard from './Dashboard';

const meta: Meta<typeof Dashboard> = {
  title: 'Pages/Dashboard',
  component: Dashboard,
  parameters: { layout: 'padded' },
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

export const Default: Story = { args: {} };
export const Loading: Story = { args: { loading: true } };
export const WithError: Story = { args: { error: new Error('网络错误') } };
export const EmptyData: Story = { args: { stats: { ...mockStats, total_sales_today: 0 } } };
```

#### 全局装饰器 (`.storybook/preview.tsx`)
```tsx
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

export const parameters = {
  backgrounds: {
    default: 'light',
    values: [
      { name: 'light', value: '#f0f2f5' },
      { name: 'dark', value: '#141414' },
      { name: 'white', value: '#ffffff' },
    ],
  },
  globalTypes: {
    locale: {
      description: '国际化语言',
      defaultValue: 'zh-CN',
      toolbar: { title: '语言', icon: 'globe', items: ['zh-CN', 'en-US'] },
    },
  },
};
```

### 4.3 现有故事清单

| 文件 | 标题 | 说明 |
|------|------|------|
| `formatters.stories.tsx` | Utilities/Formatters | 格式化工具函数可视化测试 |
| `NotImplemented.stories.tsx` | Pages/NotImplemented | 通用占位页面各种状态 |
| `Dashboard.stories.tsx` | Pages/Dashboard | 仪表盘页面各种状态 |

### 4.4 部署建议

**GitHub Pages**：
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

**Netlify/Vercel**：连接 Git 仓库，构建命令 `cd frontend && npm run build-storybook`，发布目录 `frontend/storybook-static`。

---

## 5. 开发工作流

1. **新建组件** → 同步创建 `Component.stories.tsx`
2. **编写故事** → 覆盖默认、异常、加载、交互等状态
3. **本地预览** → `npm run storybook` 实时查看
4. **交互测试** → 使用 Controls 面板调整 props、Actions 面板查看事件
5. **文档生成** → 自动生成 Docs 页面，支持 MDX 扩展
6. **构建部署** → `npm run build-storybook` → 部署静态站点

---

## 6. 常用命令速查

```bash
# 开发
npm run dev          # 启动开发服务器
npm run build        # 生产构建
npm run preview      # 预览构建产物

# 代码质量
npm run lint         # ESLint 检查
npm run lint --fix   # 自动修复
npx tsc --noEmit     # TypeScript 类型检查

# 清理
npm run clean        # 清理构建产物和缓存
npm run clean:all    # 彻底清理 (含 node_modules)

# Storybook
npm run storybook           # 启动 Storybook
npm run build-storybook     # 构建静态文档
```

---

## 7. 维护记录

| 日期 | 维护人 | 发现问题 | 处理措施 |
|------|--------|----------|----------|
| 2026-08-25 | 前端组 | 重复 nginx 配置、构建缓存残留、缺失 pre-commit | 清理冗余、配置 clean 脚本、添加 husky |
| 2026-10-07 | 前端组 | 文档分散 (README_5S.md、STORYBOOK_README.md) | 合并为统一 README.md |

---

> **原则**：整理整顿是持续前行的前提。5S 不是一次性大扫除，而是融入日常提交流程的自动化护栏。