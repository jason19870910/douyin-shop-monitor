---
title: ADR-003: 采用 Design Tokens 实现统一深色主题
version: 1.0.0
status: Accepted
last_updated: 2026-08-22
owner: Frontend Lead
reviewers: [Tech Lead, UI/UX 设计师]
approvers: [Tech Lead]
classification: Internal
doc_id: ADR-003
tags: [ADR, 前端, Design Tokens, 深色主题, CSS Variables, 主题系统]
related_docs: [DOC-TECH-003, ADR-001]
changelog: |
  v1.0.0 (2026-08-22): 初版创建 - Frontend Lead
---

# ADR-003: 采用 Design Tokens 实现统一深色主题

## 状态
Accepted

## 背景
项目早期仅支持浅色主题，后期需求增加深色模式。直接覆盖 Ant Design 样式存在问题：
- 维护成本高：需覆盖 200+ 组件样式
- 一致性差：颜色值分散在各处，难以统一管理
- 切换闪烁：CSS-in-JS 方案首屏渲染闪烁
- 扩展性弱：新增主题（如高对比度、品牌色）需重写大量代码

## 决策
采用 **Design Tokens + CSS Variables** 方案实现主题系统：

### 架构设计
```
src/
├── design-tokens/
│   ├── tokens.json          # 单一事实来源
│   ├── themes/
│   │   ├── light.css        # 浅色主题变量
│   │   ├── dark.css         # 深色主题变量
│   │   └── high-contrast.css # 高对比度主题（预留）
│   └── index.ts             # TypeScript 类型导出
├── styles/
│   ├── variables.css        # 全局 CSS Variables 注入
│   └── global.css           # 全局基础样式
└── hooks/
    └── useTheme.ts          # 主题切换 Hook
```

### tokens.json 结构
```json
{
  "color": {
    "primary": { "value": "{blue.6}", "description": "品牌主色" },
    "background": { "value": "{gray.0}", "description": "页面背景" },
    "surface": { "value": "{white}", "description": "卡片/容器背景" },
    "text": { "value": "{gray.900}", "description": "主文本色" },
    "textSecondary": { "value": "{gray.500}", "description": "次要文本" },
    "border": { "value": "{gray.200}", "description": "边框色" },
    "success": { "value": "{green.6}", "description": "成功状态" },
    "warning": { "value": "{gold.6}", "description": "警告状态" },
    "error": { "value": "{red.6}", "description": "错误状态" }
  },
  "spacing": { "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px" },
  "borderRadius": { "sm": "2px", "md": "6px", "lg": "8px" },
  "shadow": { "sm": "0 1px 2px rgba(0,0,0,0.05)", "md": "0 4px 12px rgba(0,0,0,0.1)" },
  "fontSize": { "xs": "12px", "sm": "14px", "md": "16px", "lg": "20px", "xl": "24px" }
}
```

### 主题切换实现
```typescript
// useTheme.ts
export const useTheme = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  
  return { theme, toggleTheme: () => setTheme(t => t === 'light' ? 'dark' : 'light') };
};
```

```css
/* variables.css - 自动生成 */
:root[data-theme="light"] {
  --color-primary: #1677ff;
  --color-background: #ffffff;
  --color-surface: #fafafa;
  --color-text: #1a1a1a;
  /* ... */
}
:root[data-theme="dark"] {
  --color-primary: #177ddc;
  --color-background: #141414;
  --color-surface: #1f1f1f;
  --color-text: #ffffff;
  /* ... */
}
```

### Ant Design 5.x 集成
```tsx
// App.tsx
import { ConfigProvider, theme } from 'antd';

const darkAlgorithm = theme.darkAlgorithm;

export default function App() {
  const { theme: currentTheme } = useTheme();
  return (
    <ConfigProvider
      theme={{
        algorithm: currentTheme === 'dark' ? darkAlgorithm : undefined,
        token: {
          colorPrimary: 'var(--color-primary)',
          colorBgContainer: 'var(--color-surface)',
          colorText: 'var(--color-text)',
          borderRadius: 6,
        },
      }}
    >
      <AppContent />
    </ConfigProvider>
  );
}
```

## 备选方案
| 方案 | 优点 | 缺点 | 未选择原因 |
|------|------|------|------------|
| Ant Design ConfigProvider 仅用 token | 简单、原生支持 | 无法覆盖非 AntD 组件、无全局一致性 | 项目有大量自定义组件和图表 |
| CSS-in-JS (styled-components/emotion) | 动态主题强、TS 支持好 | 运行时开销、SSR 复杂、包体积大 | 性能敏感，首屏加载需优化 |
| Less 变量覆盖 | AntD 传统方案 | 仅构建时生效、无运行时切换 | 需支持运行时动态切换 |
| Tailwind CSS dark: | 原子化、暗色类名简单 | 需重写所有样式、学习成本高 | 现有代码基于 CSS Modules |

## 后果
### 正面影响
- **单一事实来源**：tokens.json 管理所有设计决策，修改一处全局生效
- **零闪烁切换**：CSS Variables 原生支持，首屏无 FOUC
- **全覆盖**：AntD 组件 + 自定义组件 + Recharts 图表 + 原生 HTML 均受控
- **类型安全**：tokens.json 自动生成 TypeScript 类型，IDE 智能提示
- **扩展性**：新增主题只需添加 CSS 文件，无需改业务代码
- **构建时优化**：Style Dictionary 生成 CSS，运行时零开销

### 负面影响/风险
- 构建链路增加：需集成 Style Dictionary 或自定义脚本生成 CSS
- 设计师协作：需要设计师理解 Tokens 概念，配合输出标准化设计稿
- 旧代码迁移：存量硬编码颜色需逐步替换为变量引用

### 需要的后续工作
- [x] 建立 tokens.json 规范和校验脚本
- [x] 配置 Style Dictionary 生成 light.css/dark.css
- [x] 实现 useTheme Hook 和 ConfigProvider 集成
- [x] 替换全项目硬编码颜色为 CSS Variables
- [x] 适配 Recharts 图表主题色（通过 CSS Variables 传递）
- [x] E2E 测试验证主题切换无闪烁、无布局抖动
- [ ] 设计师建立 Figma Tokens 同步流程
- [ ] 预留高对比度无障碍主题扩展

## 相关链接
- Design Tokens 规范: https://designtokens.org/
- Style Dictionary: https://amzn.github.io/style-dictionary/
- Ant Design 5.x 主题定制: https://ant.design/docs/react/customize-theme
- W3C Design Tokens Community Group: https://www.w3.org/community/design-tokens/
EOF