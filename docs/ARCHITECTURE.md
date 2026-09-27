# 系统架构概览 (Architecture Overview)

## 整体结构

```
+-------------------+        +-------------------+        +-------------------+
|   前端 (React)    | <----> |   后端 (Flask)    | <----> |   数据存储 (Redis)  |
+-------------------+        +-------------------+        +-------------------+
        |                                 |
        |                                 v
        |                         +-------------------+
        |                         |   调度器 (Celery Beat) |
        |                         +-------------------+
        |                                 |
        |                                 v
        |                         +-------------------+
        +----------------------> |   外部 API 调用   |
                                  (FXG / Creator)
```

## 关键组件

- **Flask**：提供 RESTful API，对内服务（`/api/v1/*`）以及对外转发接口。
- **Celery Beat**：分布式定时任务调度，配合 Celery Worker 执行周期性数据抓取与告警检查。
- **Redis**：共享缓存层，解决多 Worker 进程下的数据一致性问题；支持原子操作（Lua 脚本）、发布/订阅跨进程通知。
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

1. **定时抓取**：Celery Beat 触发 `scheduled_job_task`，调用 `fetch_and_store_*` 系列函数，从外部 API 拉取商品、订单、创作者数据并写入 Redis 缓存与本地 JSON 文件。
2. **缓存**：抓取结果保存在 Redis (`redis_cache.RedisCache`)，供所有 API 路由实时读取；支持原子获取或设置（防缓存击穿）、列表/哈希操作、TTL 过期策略。
3. **告警**：抓取后立即执行 `check_alerts`，如满足阈值则触发 `send_alert_notification`（日志 + 邮件）。
4. **前端访问**：前端通过 `/api/v1/*` 调用获取商品列表、订单列表、创作者信息、仪表盘统计等。
5. **外部转发**：`/api/v1/products/stats`、`/api/v1/orders/stats`、`/api/v1/creators/overview` 等路由直接转发请求至对应外部服务，保持查询参数完整。

## 部署方案

- **Docker Compose 统一编排**：`docker-compose.yml` 定义完整服务栈，`docker compose up -d` 一键部署
- **服务拆分**：
  - `monitor` - Flask API 服务 (gunicorn, 5000端口)
  - `celery_worker` - Celery Worker (处理异步任务)
  - `celery_beat` - Celery Beat (定时任务调度)
  - `redis` - Redis 7 (缓存/消息队列/结果后端)
  - `frontend` - React + Nginx 静态服务 (80端口)
  - `nginx` - 反向代理 + SSL 终止 (80/443端口)
- **密钥管理**：Docker Secrets (`./secrets/`) 挂载到 `/run/secrets/`，代码通过 `_read_secret()` 读取
- **前端构建**：前端镜像构建时预编译 (`COPY build /usr/share/nginx/html`)，无需运行时构建
- **健康检查**：所有服务配置 `healthcheck`，Celery 服务依赖 `redis:service_healthy`
- **资源限制**：`deploy.resources.limits/reservations` 限制 CPU/内存
- **网络隔离**：自定义 bridge 网络 `douyin-network`，服务间通过服务名通信
- **日志**：结构化 JSON 日志（`python-json-logger` + `logging.yaml`），输出到 stdout，配合 ELK/Loki 实现集中化日志监控

## 网络拓扑

```
用户浏览器 (HTTPS: wlkj-tech.cn)
      │
      ▼
Nginx 容器 (443/80) ──► 静态资源 (/assets/, /index.html)  [frontend 容器]
      │
      ├─► /api/v1/* ──► monitor 容器 (5000) ──► redis 容器 (6379)
      │                    │
      │                    ├─► celery_worker 容器
      │                    │     ├─► fetch_products ──► FXG API (fxg.jinritemai.com)
      │                    │     ├─► fetch_orders ──► FXG API
      │                    │     ├─► fetch_creators ──► Creator API (creator.douyin.com)
      │                    │     ├─► fetch_creator_works ──► Creator API
      │                    │     ├─► check_alerts
      │                    │     ├─► scheduled_job (完整同步)
      │                    │     └─► refresh_oauth_token
      │                    │
      │                    └─► celery_beat 容器 (定时触发)
      │
      └─► 健康检查 /api/v1/health
```

## 核心外部 API 映射

| 业务模块 | 外部接口 | 方法 | 内部转发路径 | 说明 |
|---------|---------|------|-------------|------|
| 商品统计 | `/product/tproduct/aggsProductCount` | GET | `GET /api/v1/products/stats` | tab=onSale/stock/violation |
| 订单统计 | `/api/order/tabcnt` | GET | `GET /api/v1/orders/stats` | all/pay/cancel 计数与金额 |
| 创作者概览 | `/janus/douyin/creator/data/overview/dashboard` | POST | `GET /api/v1/creators/overview` | recent_days 参数，**内部已统一为 GET** |

## 配置管理

| 配置项 | 来源 | 说明 |
|--------|------|------|
| `FXG_BASE_URL` | `.env` / 环境变量 | 抖店外部数据服务根地址 |
| `CREATOR_BASE_URL` | `.env` / 环境变量 | 创作者中心外部数据服务根地址 |
| `FXG_COOKIES` | Docker Secret (`fxg_cookies`) | 抖店 API 认证 Cookie |
| `CREATOR_COOKIES` | Docker Secret (`creator_cookies`) | 创作者中心 API 认证 Cookie |
| `CELERY_BROKER_URL` | 环境变量 / `docker-compose.yml` | Redis 连接地址 (`redis://redis:6379/0`) |
| `CELERY_RESULT_BACKEND` | 环境变量 / `docker-compose.yml` | Redis 结果后端 (`redis://redis:6379/0`) |
| `ALERT_EMAIL` | `.env` / 环境变量 | 告警邮件收件人 |
| `DATA_DIR` | 环境变量 / `docker-compose.yml` | 本地 JSON 数据目录 (`/data`) |
| `API_KEY` | Docker Secret (`api_key`) | 内部 API 认证密钥 |
| 签名参数 (`__TOKEN`, `MS_TOKEN`, `a_bogus`, `verify_fp`, `fp`) | Docker Secrets | 抖店签名所需动态参数 |
| `FXG_SHOP_ID`, `FXG_LOG_ID` | Docker Secrets | 抖店店铺/日志 ID |
| `DOUYIN_APP_ID`, `DOUYIN_APP_SECRET` | Docker Secrets | 抖音开放平台应用凭证 |
| `OAUTH_REDIRECT_URI` | 环境变量 | OAuth 回调地址 |

## 监控与可观测性

- **健康检查**：`GET /api/v1/health` 返回服务状态、时间戳、最后同步时间
- **数据源告警**：前端首页实时显示模拟数据持续时间、阈值超标告警
- **日志**：结构化 JSON，含 trace_id、span_id，便于链路追踪
- **指标**：可接入 Prometheus + Grafana 监控 Celery 任务耗时、成功率、队列长度

## 扩展性设计

- **外部数据源**：新增数据源仅需在 `Config` 增加 BaseURL/Cookie，`_request` 复用现有重试/签名逻辑
- **告警渠道**：`send_alert_notification` 预留接口，可接入企业微信、钉钉、飞书
- **前端主题**：Design Tokens 体系支持一键切换主题（仅需替换 `variables.css` 变量值）
- **API 版本化**：`/api/v1/` 前缀预留，便于后续多版本共存

## 已知问题与修复记录 (2026-09-26)

| 问题 | 原因 | 修复 |
|------|------|------|
| 前端静态资源 403 | 容器内文件属主为 root，Nginx 以 nginx 用户运行 | `chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755` (已在 Dockerfile 中修复) |
| Celery 任务未注册 | beat_schedule 使用 'tasks.' 前缀，但任务名无前缀 | 修正 `celery_config.py` 中 beat_schedule 的 task 名称 |
| 定时任务缺失 | 未包含 fetch_creator_works、scheduled_job、refresh_oauth_token | 在 beat_schedule 中补充完整定时任务 |
| 401 Unauthorized | 前后端 API_KEY 不一致，鉴权头缺失 | 统一 `Config.API_KEY` 与 `VITE_API_KEY`，拦截器同时发送 `Authorization: Bearer` + `X-API-Key` |
| 405 Method Not Allowed | 创作者概览调用 POST `/creators/overview/dashboard` | 改为 GET `/creators/overview` |
| 404 Not Found | 路径拼接错误 `/api/v1/janus/...` | 修正 baseURL 为 `/api/v1` + 相对路径 `/creators/overview` |
| 资源取消加载 | 浏览器缓存旧构建 | 强制刷新 + 重新构建部署 |

---

*架构文档会随功能演进持续更新。最后更新：2026-09-26*