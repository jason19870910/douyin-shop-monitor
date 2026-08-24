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
- **Flask**：提供 RESTful API，对内服务（`/api/*`）以及对外转发接口。
- **Celery Beat**：分布式定时任务调度，配合 Celery Worker 执行周期性数据抓取与告警检查。
- **Redis**：共享缓存层，解决多 Worker 进程下的数据一致性问题；支持原子操作（Lua 脚本）、发布/订阅跨进程通知。
- **Config**：统一管理环境变量，包括双域名基础 URL、公共请求头、Cookie、动态签名参数等。
- **外部 API 调用**：通过 `services.fetcher._request` 函数，使用 `Config.FXG_BASE_URL`、`Config.CREATOR_BASE_URL`、`Config.COMMON_HEADERS`、`Config.FXG_COOKIES`/`Config.CREATOR_COOKIES` 完成安全请求。
- **告警系统**：`check_alerts` 检测销量、转化率、库存阈值，支持邮件通知（可后续接入企业微信）。

## 前端架构
- **框架**：React 18 + Vite 5.x + TypeScript 严格模式
- **UI 库**：Ant Design 5.x
- **主题系统**：统一深色主题，基于 CSS Variables (Design Tokens) 实现
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
   ├─ pages/            # 14 个业务页面
   ├─ theme/            # Design Tokens 系统
   ├─ utils/            # apiClient, formatters, config, env
   └─ Layout/           # 应用布局 + 路由
  ```

## 数据流
1. **定时抓取**：Celery Beat 触发 `scheduled_job_task`，调用 `fetch_and_store_*` 系列函数，从外部 API 拉取商品、订单、创作者数据并写入 Redis 缓存与本地 JSON 文件。
2. **缓存**：抓取结果保存在 Redis (`redis_cache.RedisCache`)，供所有 API 路由实时读取；支持原子获取或设置（防缓存击穿）、列表/哈希操作、TTL 过期策略。
3. **告警**：抓取后立即执行 `check_alerts`，如满足阈值则触发 `send_alert_notification`（日志 + 邮件）。
4. **前端访问**：前端通过 `/api/*` 调用获取商品列表、订单列表、创作者信息、仪表盘统计等。
5. **外部转发**：`/api/products/external`、`/api/orders/stats`、`/api/products/stats` 等路由直接转发请求至对应外部服务，保持查询参数完整。

## 部署方案
- **Docker**：`Dockerfile` + `docker-compose.yml`，容器化后通过 Nginx 反向代理提供 5000 端口的 Flask 服务。
- **Systemd**：生产环境可使用 `doudian_monitor.service` 管理容器或直接运行 `gunicorn`。
- **前端部署**：
  1. `npm run build` 构建生产包
  2. `scp` 同步至服务器 `/opt/douyin-platform/apps/monitor/frontend/build/`
  3. 修复权限：`chown -R monitor:project_admins ... && chmod -R 755 ...`
  4. Nginx 直接服务静态文件，`/assets/` 使用 alias，前端路由 fallback 到 `index.html`
- **日志**：结构化 JSON 日志（`python-json-logger` + `logging.yaml`），输出到 stdout 与轮转文件，配合 ELK/Loki 实现集中化日志监控。

## 网络拓扑
```
用户浏览器 (HTTPS)
      │
      ▼
Nginx (443/80) ──► 静态资源 (/assets/, /index.html)
      │
      ├─► /api/* ──► Flask (5000) ──► Redis (6379)
      │                    │
      │                    ├─► Celery Worker
      │                    │     ├─► fetch_products ──► FXG API
      │                    │     ├─► fetch_orders ──► FXG API
      │                    │     ├─► fetch_creators ──► Creator API
      │                    │     └─► check_alerts
      │                    │
      │                    └─► Celery Beat (定时触发)
      │
      └─► 健康检查 /api/health
```

## 配置管理
| 配置项 | 来源 | 说明 |
|--------|------|------|
| `FXG_BASE_URL` | `.env` | 抖店外部数据服务根地址 |
| `CREATOR_BASE_URL` | `.env` | 创作者中心外部数据服务根地址 |
| `FXG_COOKIES` | `.env` / Docker Secret | 抖店 API 认证 Cookie |
| `CREATOR_COOKIES` | `.env` / Docker Secret | 创作者中心 API 认证 Cookie |
| `CELERY_BROKER_URL` | `.env` | Redis 连接地址 |
| `CELERY_RESULT_BACKEND` | `.env` | Redis 结果后端 |
| `ALERT_EMAIL` | `.env` | 告警邮件收件人 |
| `DATA_DIR` | `.env` | 本地 JSON 数据目录 |

## 监控与可观测性
- **健康检查**：`/api/health` 返回服务状态、时间戳、最后同步时间
- **数据源告警**：前端仪表盘实时显示模拟数据持续时间、阈值超标告警
- **日志**：结构化 JSON，含 trace_id、span_id，便于链路追踪
- **指标**：可接入 Prometheus + Grafana 监控 Celery 任务耗时、成功率、队列长度

## 扩展性设计
- **外部数据源**：新增数据源仅需在 `Config` 增加 BaseURL/Cookie，`_request` 复用现有重试/签名逻辑
- **告警渠道**：`send_alert_notification` 预留接口，可接入企业微信、钉钉、飞书
- **前端主题**：Design Tokens 体系支持一键切换主题（仅需替换 `variables.css` 变量值）
- **API 版本化**：`/api/v1/` 前缀预留，便于后续多版本共存

---

*架构文档会随功能演进持续更新。最后更新：2026-08-22*