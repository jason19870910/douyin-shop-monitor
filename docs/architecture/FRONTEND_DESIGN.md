# 前端设计文档 (Frontend Design)

## 技术栈

- **框架**：React 18 (Vite)
- **UI 组件库**：Ant Design 5.x
- **状态管理**：React Hooks + Context（暂不引入 Redux）
- **数据请求**：`axios` 封装（在 `src/utils/apiClient.ts` 中实现，含双鉴权头 X-API-Key + Bearer、401 处理、错误归一化）
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
--color-primary-600: #4A90E2;

/* Light Theme Background */
--bg-page: #FFFFFF;
--color-bg-primary: var(--bg-page);
--color-bg-card: #FAFAFA;
--bg-primary: #FFFFFF;
--bg-secondary: #F5F5F5;

/* Light Theme Text */
--color-text-primary: #18181B;
--color-text-secondary: #86868B;
--color-text-tertiary: #7C757F;
--color-text-inverted: #FFFFFF;

/* Borders */
--color-border-light: #D1D9E1;
--color-border-default: #D1D9E1;

/* Status Colors */
--color-status-published: #52c41a;
--color-status-draft: #66A3FF;
--color-status-pending: #faad14;
--color-status-rejected: #ff4d4f;
```

2026-09-21 更新：方案 2 统一浅色主题，Menu theme="dark" 改为 "light"，选中态文字色改为 `var(--color-text-inverted)` 提升对比，Dashboard 图表组件拆分消除空白，移除侧边栏“色彩规范”菜单。

### 组件样式覆盖策略

在 `src/index.css` 中全量覆盖 Ant Design 组件默认样式：

- Card、Button、Input、Select、Table、Pagination、Tag
- Modal、Drawer、Alert、Dropdown、Tabs、Tooltip、Popover
- Breadcrumb、Spin、Empty、Divider
- 滚动条、焦点、选区样式

> **Menu 组件样式**：侧边栏 Menu 的深度定制样式位于 `src/Layout/Layout.module.css`（`.menu .ant-menu-item` 等），而非 `index.css`。
>
> **注意**：`index.css` 中残留 "Dark Theme" 注释（如 `/* Ant Design 组件样式覆盖 - Dark Theme */`），但实际变量值均为浅色主题，项目已全面切换至 Light Theme（2026-09-21）。

## 页面结构

### 侧边栏导航与路由映射

详见 [页面路由映射表](./FRONTEND_DESIGN.md#路由映射表) —— 侧边栏类型（home/douyin/dian/alerts/system）、路由路径、页面组件与说明的完整映射。

> 本文档仅保留核心设计规范。完整的路由表、侧边栏菜单配置请参考 FRONTEND_DESIGN.md 中的「页面结构」章节。

### 核心页面组件

| 页面 | 路由 | 侧边栏 | 说明 |
|------|------|--------|------|
| 首页 | `/` | home | 4 模块竖向布局：商品统计、订单统计、创作者概览、系统健康 |
| 仪表盘 | `/dashboard` | home | 统计图表（保留原页面） |
| 视频管理 | `/douyin/videos` | douyin | 视频列表、编辑、发布 |
| 创作者中心 | `/douyin/creator` | douyin | 创作者数据概览 |
| 授权管理 | `/auth` | douyin | OAuth 登录/回调/Token刷新 |
| **收益概览** | `/douyin/earnings` | douyin | **创作者平台收益汇总（系统级接口）** |
| **收益趋势** | `/douyin/earnings/trend` | douyin | **创作者平台收益趋势/明细（系统级接口）** |
| 商品管理 | `/dian/products` | dian | 商品列表、统计 |
| 数据中心 | `/dian/orders` | dian | 订单列表、统计 |
| 合规管理 | `/dian/compliance` | dian | 规则检查、日志 |
| **经营概况** | `/dian/compass` | dian | **Compass店铺首页核心指标（15核心营业数据）** |
| 版本控制 | `/version` | system | 版本/变更/部署/环境配置 (4 Tab：当前版本/最近变更/部署状态/环境配置) |
| 告警设置 | `/alerts/douyin`, `/alerts/dian`, `/alerts/history` | alerts | 抖音/抖店告警配置、历史 |
| `/profile` | Profile | - | 个人中心 |

> **2026-09-23 重大变更**：路由 `path="/"` 由 DashboardPage 切换为 HomePage，首页实现 4 模块竖向布局（商品统计、订单统计、创作者概览、系统健康），左侧栏保持不变。

## 核心页面功能

### 1. 首页 — 新增 4 模块竖向布局

- **商品统计**：Tab 切换在售/库存/违规，调用 `productApi.getStats({ tab })` → `GET /api/v1/products/stats` → 外部 `/product/tproduct/aggsProductCount`
- **订单统计**：全部/支付/取消三列卡片，调用 `orderApi.getStats()` → `GET /api/v1/orders/stats` → 外部 `/api/order/tabcnt`
- **创作者中心概览**：总粉丝/总视频/近期播放/近期点赞，调用 `creatorApi.getOverview({ recent_days: 7 })` → `GET /api/v1/creators/overview` → 外部 `POST /janus/douyin/creator/data/overview/dashboard`（内部已统一为 GET）
- **系统健康**：状态/最后更新/时间戳/数据来源 + 立即同步按钮，调用 `healthApi.check()` → `GET /api/v1/health`
  - 返回 `status: "healthy"`、`last_update`（CST 时间，ISO 8601 含 +08:00）、`timestamp`（CST 时间，ISO 8601 含 +08:00）
  - 数据来源显示 `monitor`（来自 Redis `last_update` 键）

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

- 统计概览：总检查数、通过、失败、告警四项指标卡片
- 状态分布饼图（通过/失败/告警/已忽略/已下架）+ 分类分布柱状图
- 违规列表：状态徽章、关联规则、处理时间、行内操作（忽略/下架/恢复）
- 详情抽屉：记录全字段（状态、目标类型、关联规则、各处理时间）
- 规则管理：增删改查、启用/禁用开关、严重程度、分类、规则内容（KEYWORD 逗号关键词 / REGEX 正则 / 其他 JSON）、规则检查历史
- 一键合规检测、导出 CSV

### 6. 告警配置

- 抖店告警：销量下跌、退款率上升、合规风险等级
- 抖音告警：播放量下跌、点赞数下跌、粉丝流失
- 阈值配置：InputNumber 百分比格式化、邮件通知
- 表单验证、重置、保存状态反馈

### 7. 视频/创作者/账号管理

- 视频列表、创作者列表、账号管理
- 视频编辑、图片编辑（已接入媒体列表 API，支持视频/图片素材选择）

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
| `creatorApi.getOverview(params)` | `GET /api/v1/creators/overview` | `POST /janus/douyin/creator/data/overview/dashboard` | **创作者概览**（内部已改 GET） |
| `complianceApi.getList(params)` | `GET /api/v1/compliance` | - | 合规列表 |
| `complianceApi.getStats()` | `GET /api/v1/compliance/stats` | - | 合规统计 |
| `complianceApi.getRules()` | `GET /api/v1/compliance/rules` | - | 合规规则列表 |
| `complianceApi.createRule(data)` | `POST /api/v1/compliance/rules` | - | 创建合规规则 |
| `complianceApi.updateRule(id, data)` | `PUT /api/v1/compliance/rules/:id` | - | 更新合规规则 |
| `complianceApi.deleteRule(id)` | `DELETE /api/v1/compliance/rules/:id` | - | 删除合规规则 |
| `complianceApi.triggerCheck()` | `POST /api/v1/compliance/check` | - | 触发合规检测 |
| `complianceApi.export(params)` | `GET /api/v1/compliance/export` | - | 导出合规报告 |
| `versionApi.getVersion()` | `GET /api/v1/version` | - | **获取版本信息** (版本号、git commit、构建时间、API Key 状态) — 系统级接口 |
| `versionApi.getChanges()` | `GET /api/v1/changes` | - | **获取最近变更** (git commit 记录) — 系统级接口 |
| `versionApi.getStatus()` | `GET /api/v1/status` | - | **容器健康状态** (App/Redis/Frontend 健康检查) — 系统级接口 |
| `versionApi.getEnv()` | `GET /api/v1/env` | - | **环境变量配置** (VITE_API_KEY, VITE_DEV_MODE 等) — 系统级接口 |
| `alertDianApi.getConfig()` | `GET /api/v1/alerts/dian/config` | - | 获取抖店告警配置 |
| `alertDianApi.updateConfig(data)` | `POST /api/v1/alerts/dian/config` | - | 更新抖店告警配置 |
| `alertDouyinApi.getConfig()` | `GET /api/v1/alerts/douyin/config` | - | 获取抖音告警配置 |
| `alertDouyinApi.updateConfig(data)` | `POST /api/v1/alerts/douyin/config` | - | 更新抖音告警配置 |
| `syncApi.manualSync()` | `POST /api/v1/sync/manual` | - | 手动触发同步 |
| `healthApi.check()` | `GET /api/v1/health` | - | 健康检查 |
| `healthApi.checkExternal()` | `GET /api/v1/health/external` | - | **外部 API 状态检查**（新增） | 9 个外部 API（4 FXG + 2 Creator + 2 Creator收益 + 1 Compass）健康状态、响应时间、HTTP 状态码 |
| `earningsApi.getIncomeSummary()` | `GET /api/v1/external/creator/income/summary` | - | **创作者收益汇总**（系统级接口） |
| `earningsApi.getIncomeDetail()` | `GET /api/v1/external/creator/income/detail` | - | **创作者收益明细/趋势**（系统级接口） |
| `compassApi.getCoreIndex()` | `GET /api/v1/external/compass/shop/core-index` | - | **Compass 经营概况**（系统级接口） |
| `profileApi.getProfile()` | `GET /api/v1/auth/profile` | - | 获取用户资料（需认证） |

## 数据流与状态管理

### useApi Hook (`src/hooks/useApi.ts`)

- 统一封装 `axios` 请求：loading/error/data/refetch
- 自动重试机制（`retry: 2`，指数退避由 react-query 默认实现）
- 支持轮询（通过 `refetchInterval` 在 `useQueries.ts` 中配置）与手动刷新
- 类型安全：泛型参数推断响应数据结构

### API 客户端 (`src/utils/apiClient.ts`)

- `axios` 实例：baseURL `/api/v1`、超时、拦截器
- 请求拦截：动态 `Authorization: Bearer <API_KEY>` + `X-API-Key: <API_KEY>`
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
 │    ├─ index.ts
 │    └─ index.test.ts
 ├─ components/       # 可复用 UI 组件
 │    ├─ common/      # 通用基础组件
 │    │    ├─ DataTable.tsx       # 表格组件（含分页、排序、筛选）
 │    │    └─ index.ts
 │    ├─ dashboard/   # 仪表盘专用组件
 │    │    ├─ MetricCard.tsx              # 指标卡片
 │    │    ├─ MetricCard.module.css
 │    │    ├─ CreatorDataCard.tsx         # 创作者数据卡片（含趋势图）
 │    │    ├─ CreatorDataCard.module.css
 │    │    ├─ OrderTrendMiniChart.tsx     # 订单趋势迷你图
 │    │    ├─ OrderTrendMiniChart.module.css
 │    │    ├─ OrderStatusDistribution.tsx # 订单状态分布饼图
 │    │    ├─ OrderStatusDistribution.module.css
 │    │    ├─ SkeletonCard.tsx            # 骨架屏卡片
 │    │    ├─ SkeletonCard.module.css
 │    │    └─ index.ts
 │    ├─ layout/      # 布局组件
 │    │    ├─ PageContainer.tsx
 │    │    ├─ PageContainer.module.css
 │    │    ├─ PageHeader.tsx
 │    │    ├─ PageHeader.module.css
 │    │    ├─ StatCard.tsx
 │    │    ├─ StatCard.module.css
 │    │    ├─ TableCard.tsx
 │    │    ├─ TableCard.module.css
 │    │    └─ index.ts
 │    ├─ ErrorBoundary.tsx        # 错误边界
 │    ├─ ErrorBoundary.test.tsx
 │    └─ ClientOnly.tsx           # 仅客户端渲染包装器
 ├─ hooks/            # 自定义 Hooks
 │    ├─ useApi.ts
 │    ├─ useQueries.ts   # react-query 封装（数据查询 + 变更 + 轮询配置）
 │    ├─ queryClient.ts  # react-query 客户端实例
 │    └─ index.ts
 ├─ pages/            # 业务页面组件
 │    ├─ Home.tsx                # 首页（4 模块竖向布局）
 │    ├─ Dashboard.tsx           # 仪表盘（保留原页面）
 │    ├─ VersionControl.tsx      # 版本控制（4标签页：当前版本/最近变更/部署状态/环境配置）
 │    ├─ Products.tsx            # 商品管理
 │    ├─ Orders.tsx              # 数据中心（订单）
 │    ├─ Compliance.tsx          # 合规管理
 │    ├─ Videos.tsx              # 视频管理
 │    ├─ Creator.tsx             # 创作者中心
 │    ├─ Auth.tsx                # 授权管理
 │    ├─ VideoEdit.tsx           # 视频编辑
 │    ├─ ImageEdit.tsx           # 图片编辑
 │    ├─ Account.tsx             # 账号管理
 │    ├─ AlertsDouyin.tsx        # 抖音告警设置
 │    ├─ AlertsDian.tsx          # 抖店告警设置
 │    ├─ AlertHistory.tsx        # 告警历史
 │    ├─ Profile.tsx             # 个人中心
 │    ├─ Earnings.tsx            # 收益概览（/douyin/earnings）
 │    ├─ EarningsTrend.tsx       # 收益趋势（/douyin/earnings/trend）
 │    ├─ Compass.tsx             # 经营概况（/dian/compass）
 │    └─ *.module.css            # CSS Modules 样式
 ├─ theme/            # 设计令牌系统
 │    ├─ tokens.ts    # TypeScript 令牌定义（供 JS 使用）
 │    └─ variables.css # CSS Variables 定义（供样式使用）
 ├─ utils/            # 通用工具函数
 │    ├─ apiClient.ts
 │    ├─ apiClient.test.ts
 │    ├─ config.ts
 │    ├─ env.ts
 │    ├─ formatters.ts
 │    ├─ formatters.stories.tsx
 │    ├─ constants.ts
 │    └─ orderStatus.ts
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

# 部署：将 \`build/\` 目录通过 docker cp 推送至容器 \`douyin_frontend\`
# 并执行 nginx -s reload
# 详细部署步骤见：[README.md - 部署流程（前端）](../README.md#部署流程前端)
```

## 部署指引

前端部署流程详见：
- **快速部署**：[README.md - 部署流程（前端）](../README.md#部署流程前端)
- **架构与容器详情**：[ARCHITECTURE.md - 部署方案](./ARCHITECTURE.md#部署方案)
- **开发环境搭建**：[DEV_SETUP.md - 全栈（Docker）](../DEV_SETUP.md#全栈docker)

### 关键配置提要
- 容器名：`douyin_frontend` (Nginx 静态服务)
- 构建产物目录：`/usr/share/nginx/html`
- 环境变量：`VITE_API_KEY` 通过 `docker-compose.yml` 的 `env_file` 加载
- Nginx 配置：`src/frontend/nginx.conf` 已配置 `X-API-Key` 头转发至后端
- 权限修复：`chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 ...`

## 更新记录

- **2026-10-15**：
  - **首页 KPI 数据流重构**：Home.tsx 使用三个独立统计 Hook（`useProductsStats`、`useOrdersStats`、`useCreatorsOverview`）替代原 `useDashboardStats`，KPI 卡片聚合独立端点数据
  - **订单金额单位修复（关键）**：后端 `/orders/stats` 返回金额已除以 100 转为**元**，前端 `formatCurrency` 直接使用无需再除 100（修复首页显示 6,202 元应为 62.02 元的问题）
  - **商品价格单位统一（分转元）**：Products、Dashboard、Orders、Home 多处 `price_lower`/`market_price`/`discount_price` 字段在 `formatCurrency` 前显式 `/ 100`，导出 CSV 同步修正
  - **订单金额字段修正**：Dashboard、Orders 页面使用 `pay_amount`/`total_price` 替代不存在的 `amount` 字段（外部 API 返回字段名）
  - **首页趋势/TOP 数据恢复**：Home.tsx 复用 `useDashboardStats` 获取 `sales_trend` 和 `top_products`，KPI 用独立端点，趋势/TOP 用聚合端点
  - **TypeScript 构建修复**：`OrderStatusItem` 改为 named import、`DataTable` 移除 `pagination={false}`、清理未使用变量
  - **新增好货商品预览 API**：`src/frontend/src/api/index.ts` 新增 `HaohuoProductPreview` 类型定义、`haohuoApi.getProductPreview(promotionId)` 封装，支持详情图片、规格、价格/销量/协议配置、跳转链接等完整预览数据获取

- **2026-10-14**：
  - **健康检查响应格式修正**：`/api/v1/health` 返回 `status: "healthy"`（原 `ok`）、新增 `last_update` 字段（CST 时间 ISO 8601 含 +08:00）、`timestamp` 统一 CST 时区
  - **外部 API 健康检查扩展**：`/api/v1/health/external` 从 6 个扩展至 9 个端点（新增：创作者收益汇总、创作者收益明细、Compass 核心指标）
  - **时区统一**：所有后端时间字段返回 CST (UTC+8) 格式（ISO 8601 含 +08:00 偏移），前端无需额外转换
  - **同步时间修复**：手动同步后 `last_update` 正确显示同步完成时间（修复读取顺序问题）
  - **Google Fonts 国内镜像**：`index.html` 替换 `fonts.googleapis.com` → `fonts.loli.net`、`fonts.gstatic.com` → `fonts.gstatic.loli.net` 解决加载超时
  - **Nginx 配置优化**：静态资源缓存控制 + 双鉴权头透传（`X-API-Key`、`Authorization`）
  - **Nginx DNS 缓存根治**：后端容器重建 IP 变化导致前端反代连接失败（`Connection refused`），在 `nginx.conf` 添加 `resolver 127.0.0.11 valid=10s ipv6=off` + 变量 `set $upstream_app http://app:5000` + `proxy_pass $upstream_app` 强制运行时解析，后端重启无需重启前端，最多 10 秒自动恢复
  - **版本控制页面布局优化**（`VersionControl.tsx`）：
    - 新增顶部关键指标行：4 个 Statistic 卡片（整体健康度、API 认证状态、当前版本、实时服务器时间 CST）
    - Tab 切换为卡片式 (`type="card"`)，英文 key 避免编码问题
    - **当前版本**：网格式 Statistic 展示版本号/Commit/构建时间/环境，下方垂直 Descriptions 显示完整 Commit 与 API Key 状态
    - **最近变更**：卡片列表，Tag 按类型着色、消息加粗、时间次级色，底部分割线
    - **部署状态**：三容器健康度 Statistic 网格（绿/红色区分），下方最后部署时间
    - **环境配置**：垂直 Descriptions，敏感字段 (VITE_API_KEY) 仅显示前 8 位 + Tooltip 提示
    - **右侧系统快照**：垂直布局 Badge 状态点亮，含环境标签、最后部署时间，Card extra 显示整体状态
    - **响应式列宽**：`xs={24} lg={16} xxl={18}` / `xs={24} lg={8} xxl={6}`，大屏更宽、小屏自适应堆叠
    - **加载/空状态**：每个 Tab 独立 `isLoading` + `Empty` 组件，避免整页卡顿

*前端设计会根据实际需求迭代更新，本文档最后更新：2026-10-15*





