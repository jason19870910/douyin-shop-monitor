# 系统架构概览 (Architecture Overview)

> **📋 相关扩展文档（已归档）：**
> - [部署架构演进路线图 (K8s/MySQL/Prometheus/Grafana)](./archive/DEPLOYMENT_ARCHITECTURE.md) — 生产级目标架构
> - [数据流详细设计 (Celery/ETL/缓存策略)](./archive/DATA_FLOW.md) — 旧版 Celery 架构数据流
> - [安全架构规范 (零信任/Vault/等保)](./archive/SECURITY_ARCHITECTURE.md) — 安全合规规范
>
> 本文档反映**当前简化架构 (3容器、内置调度器)**，扩展文档描述**生产级目标架构**，供演进参考。

## 整体结构

```
+-------------------+        +-------------------+
|   前端 (React)    | <----> |   后端 (Flask +   |
+-------------------+        |   sync scheduler) |
        |                                 |
        v                                 v
+-------------------+
|   Redis (缓存)    |
+-------------------+
```

## 关键组件

- **Flask**：提供 RESTful API，对内服务（`/api/v1/*`）以及对外转发接口。内置定时同步调度器，周期性执行数据抓取与告警检查。
- **Redis**：共享缓存层，所有服务通过服务名 `redis` 通信；支持原子操作（Lua 脚本）、分布式锁（SET NX EX，5min TTL）、发布/订阅。作为缓存和分布式锁使用，保证多进程场景下的数据一致性。
- **Config**：统一管理环境变量，包括双域名基础 URL、公共请求头、Cookie、动态签名参数等。
- **外部 API 调用**：通过 `services.fetcher._request` 函数，使用 `Config.FXG_BASE_URL`、`Config.CREATOR_BASE_URL`、`Config.COMMON_HEADERS`、`Config.FXG_COOKIES`/`Config.CREATOR_COOKIES` 完成安全请求。
- **告警系统**：`check_alerts` 检测销量、转化率、库存阈值，支持邮件通知（可后续接入企业微信）。

## 前端架构

- **框架**：React 18 + Vite 5.x + TypeScript 严格模式
- **UI 库**：Ant Design 5.x
- **主题系统**：统一浅色主题，基于 CSS Variables (Design Tokens) 实现
  - 设计令牌文件：`src/theme/variables.css` (200+ CSS Variables)
  - TypeScript 令牌：`src/theme/tokens.ts`
  - 全量组件覆盖：`src/index.css` (Card、Button、Input、Select、Table、Pagination、Tag、Modal、Drawer、Alert、Dropdown、Tabs、Tooltip、Popover、Menu、Breadcrumb、Spin、Empty、Divider、滚动条、焦点、选区)
- **样式方案**：CSS Modules + CSS Variables，组件级样式隔离
- **状态管理**：React Hooks + Context，`useApi` 统一数据获取（加载、错误、重试、轮询）
- **数据层**：`axios` 实例封装（拦截器、错误归一化、取消令牌、User-Agent 注入）
- **路由**：React Router v6，动态侧边栏菜单（home/douyin/dian/alerts）
- **图表**：Recharts（趋势图、饼图、迷你图）
- **代码组织**：
  ```
  src/
   ├─ api/              # 后端交互封装
   ├─ components/
   │    ├─ layout/      # PageContainer, PageHeader, TableCard, StatCard
   │    └─ dashboard/   # MetricCard, OrderStatusDistribution, OrderTrendMiniChart, CreatorDataCard
   ├─ hooks/useApi.ts   # 数据获取 Hook
   ├─ pages/            # 14 个业务页面 + Home.tsx
   ├─ theme/            # Design Tokens 系统
   ├─ utils/            # apiClient, formatters, config, env
   └─ Layout/           # 应用布局 + 路由
  ```

## 数据流

1. **定时抓取**：内置调度器触发 `scheduled_job_task`，调用 `fetch_and_store_*` 系列函数，从外部 API 拉取商品、订单、创作者数据并写入 Redis 缓存与本地 JSON 文件。
2. **缓存**：抓取结果保存在 Redis，供所有 API 路由实时读取；支持原子获取或设置（防缓存击穿）、列表/哈希操作、TTL 过期策略。
3. **告警**：抓取后立即执行 `check_alerts`，如满足阈值则触发 `send_alert_notification`（日志 + 邮件）。
4. **前端访问**：前端通过 `/api/v1/*` 调用获取商品列表、订单列表、创作者信息、仪表盘统计等。
5. **外部转发**：`/api/v1/products/stats`、`/api/v1/orders/stats`、`/api/v1/creators/overview` 等路由直接转发请求至对应外部服务，保持查询参数完整。

## 部署方案

- **Docker Compose 统一编排**：`docker-compose.yml` 定义精简服务栈，`docker compose up -d` 一键部署
- **服务拆分**：
  - `app` - Flask API 服务 + 嵌入式 sync scheduler (gunicorn, 5000端口)
  - `redis` - Redis 7 (缓存/消息队列/结果后端/分布式锁)
  - `frontend` - React + Nginx 静态服务 (80端口)
- **密钥管理**：Docker Secrets (`./secrets/`) 挂载到 `/run/secrets/`，代码通过 `_read_secret()` 读取
- **前端构建**：前端镜像构建时预编译 (`COPY build /usr/share/nginx/html`)，无需运行时构建
- **健康检查**：所有服务配置 `healthcheck`，`app` 服务依赖 `redis:service_healthy`
- **资源限制**：`deploy.resources.limits/reservations` 限制 CPU/内存
- **网络隔离**：自定义 bridge 网络 `douyin-network`，服务间通过服务名通信
- **日志**：结构化 JSON 日志（`python-json-logger` + `logging.yaml`），输出到 stdout，配合 ELK/Loki 实现集中化日志监控
- **定时任务**：内置于 `app` 容器的 background thread，使用 `schedule` 库代替独立 `celery_beat` 进程

## 网络拓扑

```
用户浏览器 (HTTPS: wlkj-tech.cn)
      │
      ▼
Nginx 容器 (443/80) ──► 静态资源 (/assets/, /index.html)  [frontend 容器]
      │
      └─► /api/v1/* ──► app 容器 (5000) ──► redis 容器 (6379)
                   │
                   └─► 内置定时同步任务 (background thread, schedule库)
                   │
                   ├─► fetch_products ──► FXG API (fxg.jinritemai.com)
                   ├─► fetch_orders ──► FXG API
                   ├─► fetch_creators ──► Creator API (creator.douyin.com)
                   ├─► fetch_creator_works ──► Creator API
                   ├─► check_alerts
                   └─► scheduled_job (完整同步，60分钟间隔)

健康检查 /api/v1/health
```

分布式锁：Redis `SET NX EX`（5分钟 TTL），由 `app` 容器内的 sync 调度器使用

## 核心外部 API 映射

| 业务模块 | 外部接口 | 方法 | 内部转发路径 | 说明 |
|---------|---------|------|-------------|------|
| 商品统计 | `/product/tproduct/aggsProductCount` | GET | `GET /api/v1/products/stats` | tab=onSale/stock/violation |
| 订单统计 | `/api/order/tabcnt` | GET | `GET /api/v1/orders/stats` | all/pay/cancel 计数与金额 |
| 创作者概览 | `/janus/douyin/creator/data/overview/dashboard` | POST | `GET /api/v1/creators/overview` | recent_days 参数，**内部已统一为 GET** |
| 创作者收益汇总 | `/aweme/v1/creator/income/category/summary/` | GET | `GET /api/v1/external/creator/income/summary` | 系统级接口，分类汇总 day1/7/30 |
| 创作者收益明细 | `/aweme/v1/creator/income/category/detail/` | GET | `GET /api/v1/external/creator/income/detail` | 系统级接口，chart坐标 + 每日收入列表 |
| Compass 经营概况 | `/compass_api/shop/common/homepage/core_index_v3` | GET | `GET /api/v1/external/compass/shop/core-index` | 系统级接口，15 核心营业数据 |

## 配置管理

| 配置项 | 来源 | 说明 |
|--------|------|------|
| `FXG_BASE_URL` | `.env` / 环境变量 | 抖店外部数据服务根地址 |
| `CREATOR_BASE_URL` | `.env` / 环境变量 | 创作者中心外部数据服务根地址 |
| `FXG_COOKIES` | Docker Secret (`fxg_cookies`) | 抖店 API 认证 Cookie |
| `CREATOR_COOKIES` | Docker Secret (`creator_cookies`) | 创作者中心 API 认证 Cookie |
| `COMPASS_COOKIES` | 环境变量 / Docker Secret | 指南针 API 认证 Cookie |
| `SCHEDULER_INTERVAL_MINUTES` | `.env` / 环境变量 | 内置调度器间隔（分钟），默认 60 |
| `ALERT_EMAIL` | `.env` / 环境变量 | 告警邮件收件人 |
| `DATA_DIR` | 环境变量 / `docker-compose.yml` | 本地 JSON 数据目录 (`/data`) |
| `API_KEY` | Docker Secret (`api_key`) | 内部 API 认证密钥 |
| 签名参数 (`__TOKEN`, `MS_TOKEN`, `a_bogus`, `verify_fp`, `fp`) | Docker Secrets | 抖店签名所需动态参数 |
| `FXG_SHOP_ID`, `FXG_LOG_ID` | Docker Secrets | 抖店店铺/日志 ID |
| `DOUYIN_APP_ID`, `DOUYIN_APP_SECRET` | Docker Secrets | 抖音开放平台应用凭证 |
| `OAUTH_REDIRECT_URI` | 环境变量 | OAuth 回调地址 |

## 监控与可观测性

- **健康检查**：`GET /api/v1/health` 返回服务状态（`status: "healthy"`）、时间戳（CST +08:00）、最后同步时间（CST +08:00，来自 Redis `last_update`）
- **外部 API 健康检查**：`GET /api/v1/health/external` 检查 9 个外部 API（4 FXG + 2 Creator + 2 Creator收益 + 1 Compass）健康状态、响应时间、HTTP 状态码
- **数据源告警**：前端首页实时显示模拟数据持续时间、阈值超标告警
- **日志**：结构化 JSON，含 trace_id、span_id，便于链路追踪
- **指标**：可接入 Prometheus + Grafana 监控定时任务耗时、成功率、队列长度

## 扩展性设计

- **外部数据源**：新增数据源仅需在 `Config` 增加 BaseURL/Cookie，`_request` 复用现有重试/签名逻辑
- **告警渠道**：`send_alert_notification` 预留接口，可接入企业微信、钉钉、飞书
- **前端主题**：Design Tokens 体系支持一键切换主题（仅需替换 `variables.css` 变量值）
- **API 版本化**：`/api/v1/` 前缀预留，便于后续多版本共存

## 已知问题与修复记录 (2026-09-26)

| 问题 | 原因 | 修复 |
|------|------|------|
| 前端静态资源 403 | 容器内文件属主为 root，Nginx 以 nginx 用户运行 | `chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755` (已在 Dockerfile 中修复) |
| 401 Unauthorized | 前后端 API_KEY 不一致，鉴权头缺失 | 统一 `Config.API_KEY` 与 `VITE_API_KEY`，拦截器同时发送 `Authorization: Bearer` + `X-API-Key` |
| 405 Method Not Allowed | 创作者概览调用 POST `/creators/overview/dashboard` | 改为 GET `/creators/overview` |
| 404 Not Found | 路径拼接错误 `/api/v1/janus/...` | 修正 baseURL 为 `/api/v1` + 相对路径 `/creators/overview` |
| 资源取消加载 | 浏览器缓存旧构建 | 强制刷新 + 重新构建部署 |
| **5容器架构过于复杂** | `monitor` + `celery_worker` + `celery_beat` 三个独立进程，网络开销大 | **3容器架构精简**：合并 `monitor` + `celery_worker` 为单个 `app` 容器，移除 `celery_beat`，使用内置 scheduler |
| 订单列表签名错误 | 带过期 `msToken`/`a_bogus` 导致 `10001010A` (SIGNATURE_ERROR) | `_request()` 新增 `skip_sign` 参数，`_fetch_orders_from_api()` 显式传 `skip_sign=True` |
| **Nginx DNS 缓存导致反代失败** | 后端容器重建 IP 变化，nginx 启动时缓存旧 IP，导致 `Connection refused` | **方案 A**：`nginx.conf` 添加 `resolver 127.0.0.11 valid=10s ipv6=off` + `set $upstream_app http://app:5000` + `proxy_pass $upstream_app`，运行时解析，后端重启无需前端重启，最多 10 秒自动恢复 |
```