# 前端设计文档 (Frontend Design)

## 技术栈

- **框架**：React 18 (Vite)
- **UI 组件库**：Ant Design 5.x
- **状态管理**：React Hooks + Context（暂不引入 Redux）
- **数据请求**：`axios` 封装（统一注入 `User-Agent`，在 `src/api/index.ts` 中实现）
- **路由**：React Router v6
- **图表**：Recharts（用于仪表盘趋势、TOP 商品等可视化）
- **样式方案**：CSS Modules + CSS Variables (Design Tokens)
- **构建工具**：Vite 5.x
- **TypeScript**：严格模式

## 主题系统 (Light Theme)

### 设计原则

- **统一浅色主题**：全站采用浅色背景，侧边栏 Menu theme="light"，variables.css 与 tokens.ts 统一维护
- **设计令牌**：所有颜色、间距、圆角、阴影、字体通过 CSS Variables 定义，集中维护在 `src/theme/variables.css` 与 `src/theme/tokens.ts`
- **语义化命名**：颜色变量按用途分类（Primary/Success/Warning/Error/Neutral/Status）

### 核心色板

```css
/* Primary - 统一主色调 */
--color-primary-500: #66A3FF;
--color-primary-600: #4A8CFF;

/* Light Theme Background */
--color-bg-page: #FFFFFF;
--color-bg-card: #FAFAFA;
--bg-primary: #FFFFFF;
--bg-secondary: #F5F5F5;

/* Light Theme Text */
--color-text-primary: #18181B;
--color-text-secondary: #52525B;
--color-text-tertiary: #71717A;
--color-text-inverted: #FFFFFF;

/* Borders */
--color-border-light: #E4E4E7;
--color-border-default: #D4D4D8;

/* Status Colors */
--color-status-published: #22C55E;
--color-status-draft: #66A3FF;
--color-status-pending: #F59E0B;
--color-status-rejected: #EF4444;
```

2026-09-21 更新：方案 2 统一浅色主题，Menu theme="dark" 改为 "light"，选中态文字色改为 `var(--color-text-inverted)` 提升对比，`chartWrapper` min-height 改为 auto 消除空白，移除侧边栏“色彩规范”菜单。

### 组件样式覆盖策略

在 `src/index.css` 中全量覆盖 Ant Design 组件默认样式：

- Card、Button、Input、Select、Table、Pagination、Tag
- Modal、Drawer、Alert、Dropdown、Tabs、Tooltip、Popover
- Menu、Breadcrumb、Spin、Empty、Divider
- 滚动条、焦点、选区样式

## 页面结构

### 侧边栏导航（根据当前路由动态切换）

| 侧边栏类型 | 显示路由 | 菜单项 |
|-----------|---------|--------|
| **home** (首页) | `/` | 🏠 首页、🎵 抖音管理、🏪 抖店管理、⚠️ 告警设置 |
| **douyin** (抖音管理) | `/douyin/*`, `/auth` | 🏠 首页、📺 视频管理、👤 创作者中心、🔐 授权管理 |
| **dian** (抖店管理) | `/dian/*` | 🏠 首页、📦 商品管理、📊 数据中心、⚠️ 合规管理、🎬 视频编辑、🖼️ 图片编辑、🔑 账号管理 |
| **alerts** (告警设置) | `/alerts/*` | 🏠 首页、🎵 抖音告警设置、🏪 抖店告警设置 |

> 2026-09-21 更新：已从所有分组 `SIDEBAR_MENUS` 中移除“色彩规范”菜单项，侧边栏不再展示该卡片。

### 路由映射表

| 路由路径 | 页面组件 | 侧边栏 | 说明 |
|---------|---------|--------|------|
| `/` | HomePage (首页) | home | **首页入口：4 模块竖向布局** |
| `/dashboard` | Dashboard | home | 仪表盘统计（保留原页面） |
| `/douyin` | 重定向 → `/douyin/videos` | douyin | 抖音管理入口 |
| `/douyin/videos` | Videos | douyin | 视频管理列表 |
| `/douyin/creator` | Creator | douyin | 创作者中心 |
| `/auth` | Auth | douyin | 授权管理 (OAuth) |
| `/dian` | 重定向 → `/dian/products` | dian | 抖店管理入口 |
| `/dian/products` | Products | dian | 商品列表 |
| `/dian/orders` | Orders | dian | 数据中心 (订单) |
| `/dian/compliance` | Compliance | dian | 合规管理 |
| `/dian/video-edit` | VideoEdit | dian | 视频编辑 |
| `/dian/image-edit` | ImageEdit | dian | 图片编辑 |
| `/dian/account` | Account | dian | 账号管理 |
| `/alerts` | 重定向 → `/alerts/douyin` | alerts | 告警设置入口 |
| `/alerts/douyin` | AlertsDouyin | alerts | 抖音告警配置 |
| `/alerts/dian` | AlertsDian | alerts | 抖店告警配置 |
| `/profile` | Profile | - | 个人中心 |

> **2026-09-23 重大变更**：路由 `path="/"` 由 DashboardPage 切换为 HomePage，首页实现 4 模块竖向布局（商品统计、订单统计、创作者概览、系统健康），左侧栏保持不变。

## 核心页面功能

### 1. 首页 — 新增 4 模块竖向布局

- **商品统计**：Tab 切换在售/库存/违规，调用 `productApi.getStats({ tab })` → `GET /api/v1/products/stats` → 外部 `/product/tproduct/aggsProductCount`
- **订单统计**：全部/支付/取消三列卡片，调用 `orderApi.getStats()` → `GET /api/v1/orders/stats` → 外部 `/api/order/tabcnt`
- **创作者中心概览**：总粉丝/总视频/近期播放/近期点赞，调用 `creatorApi.getCreatorOverview({ recent_days: 7 })` → `GET /api/v1/creators/overview` → 外部 `POST /janus/douyin/creator/data/overview/dashboard`（内部已统一为 GET）
- **系统健康**：状态/最后更新/时间戳/数据来源 + 立即同步按钮，调用 `healthApi.check()` → `GET /api/v1/health`

> 加载态使用 `Spin`，空数据提示友好 `Empty`，错误态显示“加载失败”

### 2. 仪表盘

- **核心指标卡片**：总销量、总收入、订单数、转化率、商品总数、创作者粉丝
- **趋势图表**：销量趋势、收入趋势、订单趋势、转化率趋势 (Recharts)
- **热销商品 TOP 10**：表格展示，含增长率、库存预警、转化率
- **订单看板**：今日订单、成交额、平均客单价、状态分布饼图、趋势迷你图、最新订单列表
- **创作者数据**：总粉丝、今日新增、平均互动率、粉丝增长趋势
- **数据源状态**：实时/模拟数据标识、健康检查时间、告警提示

### 3. 商品管理

- 分页列表、关键词搜索、日期范围筛选
- 商品详情抽屉（含违规明细）
- 导出 CSV

### 4. 订单管理

- 分页列表、多维筛选（日期、状态）
- 金额格式化、状态标签
- 导出 CSV

### 5. 合规管理

- 风险等级分布、处理状态分布图表
- 违规列表：风险徽章、合规分数环形进度条、违规详情
- 详情抽屉：违规明细、匹配关键词、检测批次
- 规则管理：增删改查、启用/禁用、严重程度、分类
- 一键合规检测、导出 CSV

### 6. 告警配置

- 抖店告警：销量下跌、退款率上升、合规风险等级
- 抖音告警：播放量下跌、点赞数下跌、粉丝流失
- 阈值配置：InputNumber 百分比格式化、邮件通知
- 表单验证、重置、保存状态反馈

### 7. 视频/创作者/账号管理

- 视频列表、创作者列表、账号管理
- 视频编辑、图片编辑（占位页）

## 组件架构

### 布局组件 (`src/components/layout/`)

- **PageContainer**：页面容器，统一内边距、背景色
- **PageHeader**：页面标题、筛选区、操作区
- **TableCard**：表格卡片封装（加载、错误、分页、空状态、横向滚动）
- **StatCard**：指标卡片（数值、趋势、图标、加载骨架屏）
- **PageHeader/StatCard/TableCard**：导出统一入口

### 仪表盘组件 (`src/components/dashboard/`)

- **MetricCard**：核心指标卡片
- **OrderStatusDistribution**：订单状态分布饼图 + 图例
- **OrderTrendMiniChart**：订单趋势迷你柱状图
- **CreatorDataCard**：创作者数据卡片 + 粉丝趋势图
- **SkeletonCard**：加载骨架屏

### 通用组件

- **ClientOnly**：仅客户端渲染（解决 SSR 水合问题）
- **ErrorBoundary**：错误边界捕获

## API 接口对应表（已按实际实现同步）

| 前端 API 调用 | 内部端点 | 外部端点 | 说明 |
|---|---|---|---|
| `dashboardApi.getStats()` | `GET /api/v1/dashboard/stats` | - | 仪表盘统计数据 |
| `productApi.getList(params)` | `GET /api/v1/products` | - | 商品分页列表（内部缓存） |
| `productApi.getExternal(params)` | `GET /api/v1/products/external` | `GET /product/tproduct/list` | 商品外部实时列表 |
| `productApi.getDetail(id)` | `GET /api/v1/products/:id` | - | 商品详情 |
| `productApi.getStats(params)` | `GET /api/v1/products/stats` | `GET /product/tproduct/aggsProductCount` | **商品统计** |
| `orderApi.getList(params)` | `GET /api/v1/orders` | - | 订单分页列表（内部缓存） |
| `orderApi.getStats(params)` | `GET /api/v1/orders/stats` | `GET /api/order/tabcnt` | **订单统计** |
| `creatorApi.getList(params)` | `GET /api/v1/creators` | - | 创作者列表 |
| `creatorApi.getDetail(id)` | `GET /api/v1/creators/:id` | - | 创作者详情 |
| `creatorApi.getWorks(params)` | `GET /api/v1/creators/works` | - | 创作者作品列表（缓存） |
| `creatorApi.getExternalWorks(params)` | `GET /api/v1/creators/works/external` | `GET /janus/douyin/creator/pc/work_list` | 创作者作品外部实时列表 |
| `creatorApi.getCreatorOverview(params)` | `GET /api/v1/creators/overview` | `POST /janus/douyin/creator/data/overview/dashboard` | **创作者概览**（内部已改 GET） |
| `complianceApi.getList(params)` | `GET /api/v1/compliance` | - | 合规列表 |
| `complianceApi.getStats()` | `GET /api/v1/compliance/stats` | - | 合规统计 |
| `complianceApi.getRules()` | `GET /api/v1/compliance/rules` | - | 合规规则列表 |
| `complianceApi.createRule(data)` | `POST /api/v1/compliance/rules` | - | 创建合规规则 |
| `complianceApi.updateRule(id, data)` | `PUT /api/v1/compliance/rules/:id` | - | 更新合规规则 |
| `complianceApi.deleteRule(id)` | `DELETE /api/v1/compliance/rules/:id` | - | 删除合规规则 |
| `complianceApi.triggerCheck()` | `POST /api/v1/compliance/check` | - | 触发合规检测 |
| `complianceApi.export(params)` | `GET /api/v1/compliance/export` | - | 导出合规报告 |
| `alertDianApi.getConfig()` | `GET /api/v1/alerts/dian/config` | - | 获取抖店告警配置 |
| `alertDianApi.updateConfig(data)` | `POST /api/v1/alerts/dian/config` | - | 更新抖店告警配置 |
| `alertDouyinApi.getConfig()` | `GET /api/v1/alerts/douyin/config` | - | 获取抖音告警配置 |
| `alertDouyinApi.updateConfig(data)` | `POST /api/v1/alerts/douyin/config` | - | 更新抖音告警配置 |
| `syncApi.manualSync()` | `POST /api/v1/sync` | - | 手动触发同步 |
| `healthApi.check()` | `GET /api/v1/health` | - | 健康检查 |

## 数据流与状态管理

### useApi Hook (`src/hooks/useApi.ts`)

- 统一封装 `axios` 请求：loading/error/data/refetch
- 自动重试机制（指数退避、可配置次数）
- 支持轮询 (`usePolling`) 与手动刷新
- 类型安全：泛型参数推断响应数据结构

### API 客户端 (`src/utils/apiClient.ts`)

- `axios` 实例：baseURL `/api/v1`、超时、拦截器
- 请求拦截：注入 `User-Agent`、动态 `Authorization: Bearer <API_KEY>` + `X-API-Key: <API_KEY>`
- 响应拦截：统一错误归一化 (`NormalizedError`)、自动重试判定
- 取消令牌：组件卸载时自动取消进行中请求

### 格式化工具 (`src/utils/formatters.ts`)

- `formatNumber`：万/亿单位转换
- `formatCurrency`：货币格式化
- `formatPercent`：百分比格式化
- `formatDate/formatDateTime`：日期本地化
- `formatStatus`：状态映射（语义化颜色 + 中文文本）
- `getTrendClass/calculateGrowth`：趋势判断、增长率计算

## 代码组织

```
src/
 ├─ api/              # 后端交互封装层
 │    └─ index.ts
 ├─ components/       # 可复用 UI 组件
 │    ├─ dashboard/   # 仪表盘专用组件
 │    └─ layout/      # 布局组件
 ├─ hooks/            # 自定义 Hooks
 │    └─ useApi.ts
 ├─ pages/            # 业务页面组件
 │    ├─ Home.tsx          # 首页（新增：4 模块竖向布局）
 │    ├─ Dashboard.tsx
 │    ├─ Products.tsx
 │    ├─ Orders.tsx
 │    ├─ Compliance.tsx
 │    ├─ Videos.tsx
 │    ├─ Creator.tsx
 │    ├─ Auth.tsx
 │    ├─ VideoEdit.tsx
 │    ├─ ImageEdit.tsx
 │    ├─ Account.tsx
 │    ├─ AlertsDouyin.tsx
 │    ├─ AlertsDian.tsx
 │    ├─ AlertConfig.tsx
 │    ├─ Profile.tsx
 │    └─ *.module.css # CSS Modules 样式
 ├─ theme/            # 设计令牌系统
 │    ├─ tokens.ts    # TypeScript 令牌定义（供 JS 使用）
 │    └─ variables.css # CSS Variables 定义（供样式使用）
 ├─ utils/            # 通用工具函数
 │    ├─ apiClient.ts
 │    ├─ config.ts
 │    ├─ env.ts
 │    └─ formatters.ts
 ├─ Layout/           # 应用布局
 │    ├─ Layout.tsx
 │    └─ Layout.module.css
 ├─ App.tsx           # 路由入口
 ├─ index.css         # 全局样式 + Ant Design 覆盖
 └─ index.tsx         # 应用挂载
```

## 运行指南

```bash
# 安装依赖
npm install

# 开发模式（代理至后端 http://localhost:5000）
npm run dev

# 类型检查
npm run lint

# 构建生产包
npm run build

# 预览生产构建
npm run preview

# 部署：将 `build/` 目录通过 docker cp 推送至容器 eb6af2f375fe
# 并执行 nginx -s reload
```

## 部署注意事项

1. **前端运行在 Docker 容器中**：`eb6af2f375fe` (douyin-platform-frontend)，Nginx 静态服务
2. **构建产物需 docker cp 到容器内**：`/usr/share/nginx/html`
3. **修改后必须执行**：`npm run build` → `docker cp` → `nginx -s reload`
4. **容器无需重启**：`restart: unless-stopped` 仅在崩溃时生效
5. **权限修复**：容器内文件需 `chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 ...`
6. **API 代理至 Flask (5000)**：`location ^~ /api/ { proxy_pass http://127.0.0.1:5000; }`

## 更新记录

- **2026-09-23**：首页重构为 4 模块竖向布局；统一 API 路径前缀 `/api/v1`；`creatorApi.getCreatorOverview` 从 POST 改为 GET；前端鉴权头同时发送 `Authorization: Bearer` + `X-API-Key`；Docker 部署流程修正为 `docker cp` + `nginx -s reload`；修复 403/401/405/404 系列问题
- **2026-09-21**：统一浅色主题，移除“色彩规范”菜单，ChartWrapper min-height 改为 auto
- **2026-08-22**：统一深色主题，全量覆盖 Ant Design 组件样式，更新设计令牌系统
- **2026-08-16**：初版前端设计文档

---

*前端设计会根据实际需求迭代更新，本文档最后更新：2026-09-23*