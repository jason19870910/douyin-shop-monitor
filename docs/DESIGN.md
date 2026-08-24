# 项目设计文档

## 1. 项目概述
本项目是 **抖音数据监控平台**（`monitor`），通过定时抓取商品、订单、创作者等业务数据并提供统一的 RESTful API 给前端展示。原始实现使用抖音开放平台 API，后期改为通过可配置的外部数据服务 URL 进行数据获取，以便在不同业务场景下灵活对接。

## 2. 系统架构
```
+-------------------+      +-------------------+      +-------------------+
|   Frontend React  | <--->|   Flask API（app）| <--->| External Data API |
+-------------------+      +-------------------+      +-------------------+
       ^   ^                     ^   ^                     ^   ^
       |   |                     |   |                     |   |
       |   |                     |   |                     |   +--- HTTP GET (JSON)
       |   |                     |   +--- Celery Beat + Workers
       |   +--- Nginx 反向代理   +--- Docker / Docker‑Compose
       +--- Systemd service (doudian_monitor.service)
       |                                 |
       |                                 v
       |                         +-------------------+
       +------------------------->|   共享缓存        |
                                  |   (Redis)         |
                                  +-------------------+
```

- **前端**：React 18 SPA (Vite)，所有请求均指向 `http://<host>/api/*`，通过 `frontend/src/api/index.ts` 设置 `baseURL`。采用**深色主题**设计系统，基于 CSS Variables 实现 Design Tokens，全量覆盖 Ant Design 5.x 组件默认样式。
- **后端**：Flask 应用 (`app.py`) 提供统一的 API 路由，使用 **Celery Beat** 触发周期性任务，由 **Celery Worker** 执行数据同步与告警检查。
- **共享缓存**：**Redis** (`redis_cache.RedisCache`) 作为跨进程共享缓存层，支持原子操作（Lua 脚本）、列表/哈希操作、TTL 过期策略与发布/订阅通知，解决多 Worker 下的数据一致性问题。
- **数据同步**：同步逻辑集中在 `services.fetcher.fetch_and_store_*` 系列函数，统一使用 `_request` 调用外部服务，结果写入 Redis 缓存与本地 JSON 文件 (`data/` 目录) 持久化。
- **告警**：基于阈值检查（销量下降、库存不足、转化率下降）在 `check_alerts` 中产生告警并可通过邮件发送（配置 `ALERT_EMAIL`）。
- **部署**：支持 Docker 镜像 (`Dockerfile`)、Docker‑Compose、Systemd service 以及 Nginx 反向代理。

## 3. 数据流
1. **调度触发**：**Celery Beat** 触发 `scheduled_job_task` → 依次执行 `fetch_and_store_products`、`fetch_and_store_orders`、`fetch_and_store_creators` 等。
2. **外部请求**：每个 `fetch_and_store_*` 通过 `_request(endpoint, params)` 向 `Config.FXG_BASE_URL` / `Config.CREATOR_BASE_URL` 拼接对应路径发起 GET/POST 请求。
3. **字段标准化**：返回的 JSON 若缺失关键字段（如 `sales_yesterday`、`conversion_rate_today` 等），在函数内部使用 `.get(..., default)` 补全默认值，确保前端始终能读取到有效数值。
4. **持久化**：标准化后的数据写入 `data/` 目录下的 `products.json`、`orders.json`、`creators.json` 等，并同步写入 **Redis 缓存**。
5. **API 提供**：Flask 路由如 `/api/products`、`/api/orders`、`/api/creators` 直接读取 **Redis 缓存** 返回；`/api/dashboard/stats` 进一步聚合统计。

## 4. 配置说明 (`config.py`)
| 配置项 | 含义 | 默认值 | 备注 |
|--------|------|--------|------|
| `FXG_BASE_URL` | FXG 外部数据服务根地址 | - | 通过 `.env` 覆盖 |
| `CREATOR_BASE_URL` | 创作者中心外部数据服务根地址 | - | 通过 `.env` 覆盖 |
| `FXG_COOKIES` / `CREATOR_COOKIES` | 外部 API 认证 Cookie | - | 通过 Docker Secret 或 `.env` 配置 |
| `DATA_DIR` | 本地 JSON 数据目录 | `.../data` | 通过环境变量 `DATA_DIR` 调整 |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Celery Redis 地址 | `redis://localhost:6379/0` | 通过 `.env` 配置 |
| `ALERT_EMAIL` | 告警邮件收件人 | 空 | 可选 |

## 5. 外部 API 集成细节
- **请求函数** `_request` 统一处理 URL 拼接、Header 注入、签名生成、异常日志与重试（指数退避）。
- **返回约定**：外部服务必须返回形如 `{"data": {"products": [...]} }` 或相似结构；如字段名称与内部不一致，可在相应 `fetch_and_store_*` 中做映射。
- **示例**：
```bash
curl -H "Authorization: Bearer <token>" \
     "https://api.example.com/monitor/products"
```
返回示例（简化）：
```json
{ "data": { "products": [ { "product_id": "p1", "product_name": "A", "sales_today": 120, "sales_yesterday": 100, "inventory": 30, "conversion_rate": 0.12 } ] } }
```
- 若外部服务不提供 `sales_yesterday` 或 `conversion_rate_yesterday`，函数内部会使用当天值或 `0` 进行填充。

## 6. 调度与告警
- **Celery Beat**：`celery_config.py` 定义 `beat_schedule`，包含：
  - `fetch-products-every-15-minutes`：每 15 分钟抓取商品
  - `fetch-orders-every-15-minutes`：每 15 分钟抓取订单
  - `fetch-creators-every-hour`：每小时抓取创作者
  - `check-alerts-every-5-minutes`：每 5 分钟检查告警
- **告警阈值**：`DEFAULT_ALERT_CONFIG` 中可配置销量下降阈值、转化率下降阈值、库存阈值以及是否开启告警。
- **告警渠道**：当前实现为日志打印及可选的 Email（`send_alert_notification` 为占位实现，生产环境建议接入 SMTP 或企业微信）。

## 7. 前端架构设计

### 7.1 技术栈
- **框架**：React 18 (Vite 5.x)
- **UI 组件库**：Ant Design 5.x
- **状态管理**：React Hooks + Context
- **数据请求**：`axios` 封装（统一注入 `User-Agent`）
- **路由**：React Router v6
- **图表**：Recharts
- **样式方案**：CSS Modules + CSS Variables (Design Tokens)
- **TypeScript**：严格模式

### 7.2 主题系统
- **统一深色主题**：采用左侧栏色调 (`#001529`)，全站统一深色背景
- **设计令牌**：`src/theme/variables.css` 定义 200+ CSS Variables，涵盖颜色、间距、圆角、阴影、字体、断点、动画、Z-index、布局尺寸
- **语义化分类**：Primary/Success/Warning/Error/Neutral/Status/Sider/Trend
- **组件覆盖**：`src/index.css` 全量覆盖 Ant Design 组件默认样式（Card、Button、Input、Select、Table、Pagination、Tag、Modal、Drawer、Alert、Dropdown、Tabs、Tooltip、Popover、Menu、Breadcrumb、Spin、Empty、Divider、滚动条、焦点、选区）

### 7.3 核心页面
| 页面 | 路由 | 核心功能 |
|------|------|----------|
| 仪表盘 | `/dashboard` | 指标卡片、趋势图表、热销商品、订单看板、创作者数据 |
| 商品管理 | `/dian/products` | 分页、搜索、详情抽屉、导出 |
| 订单管理 | `/dian/orders` | 分页、筛选、金额格式化、导出 |
| 合规管理 | `/dian/compliance` | 风险分布图表、违规列表、规则管理、一键检测 |
| 抖店告警 | `/alerts/dian` | 销量/退款率/合规阈值配置 |
| 抖音告警 | `/alerts/douyin` | 播放量/点赞/粉丝阈值配置 |
| 视频/创作者/账号 | `/douyin/*`, `/dian/*` | 列表管理、编辑占位页 |

### 7.4 组件架构
```
src/
 ├─ components/
 │    ├─ layout/        # PageContainer, PageHeader, TableCard, StatCard
 │    └─ dashboard/     # MetricCard, OrderStatusDistribution, OrderTrendMiniChart, CreatorDataCard
 ├─ hooks/useApi.ts     # 统一数据获取、重试、轮询
 ├─ utils/
 │    ├─ apiClient.ts   # axios 实例、拦截器、错误归一化
 │    └─ formatters.ts  # 格式化工具（数字、货币、百分比、日期、状态、趋势）
 └─ theme/
      ├─ variables.css  # CSS Variables 设计令牌
      └─ tokens.ts      # TypeScript 令牌定义
```

## 8. 部署指南

### 8.1 环境准备
```bash
# 安装 Docker 与 Docker‑Compose（推荐 2.20+）
# 如需本地运行 Python，请确保已安装 Python 3.11+ 与 pip
```
创建 `.env`（示例）：
> 项目运行所需的全部环境变量已在 **.env.example** 中列出，复制该文件为 `.env` 并填写真实值即可。必须填写的关键变量包括：
> - 双域名基础 URL：`FXG_BASE_URL`、`CREATOR_BASE_URL`
> - 认证签名参数：`__TOKEN`、`MS_TOKEN`、`a_bogus`、`verifyFp`、`fp`
> - 完整 Cookie：`FXG_COOKIES`（抖店）、`CREATOR_COOKIES`（创作者中心）
> - Celery：`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`
> - 其他：`DOUYIN_APP_ID`、`DOUYIN_APP_SECRET`、`ALERT_EMAIL` 等

```bash
cp .env.example .env
# 编辑 .env，填写上述真实值（Cookie 请从浏览器开发者工具完整复制）
```

### 8.2 Docker 镜像构建与启动（推荐生产部署）
```bash
cd path/to/monitor
docker-compose build
docker-compose up -d
```
- 服务端口：`monitor` 在 **5000** 端口提供 Flask API + 静态前端；`redis` 在 **6379** 端口。
- Nginx 已通过反向代理提供 HTTPS 服务（见下文）。

### 8.3 前端构建与部署
```bash
cd frontend
npm install
npm run build
# 将 build/ 目录同步至服务器
scp -r build/* root@server:/opt/douyin-platform/apps/monitor/frontend/build/
# 修复权限
ssh root@server "chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 /opt/douyin-platform/apps/monitor/frontend/build"
```

### 8.4 Nginx 反向代理配置
```nginx
# 主站配置
server {
    listen 80;
    server_name wlkj-tech.cn www.wlkj-tech.cn;
    return 301 https://wlkj-tech.cn$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wlkj-tech.cn www.wlkj-tech.cn;

    ssl_certificate /etc/letsencrypt/live/wlkj-tech.cn-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wlkj-tech.cn-0001/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 4;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    # 前端静态文件直接由 Nginx 服务
    root /opt/douyin-platform/apps/monitor/frontend/build;
    index index.html;

    # 静态资源专用路径 - 必须在 location / 之前
    location /assets/ {
        alias /opt/douyin-platform/apps/monitor/frontend/build/assets/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 请求代理到 Flask (5000)
    location ^~ /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 200M;
    }
}
```

### 8.5 Systemd 服务（生产部署）
```bash
sudo cp doudian_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable doudian_monitor
sudo systemctl start doudian_monitor
```

### 8.6 生产环境直接运行（无 Docker）
```bash
pip install -r requirements.txt
# Flask (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
# Celery Worker
celery -A celery_config worker -l info
# Celery Beat
celery -A celery_config beat -l info
```

## 9. 常见问题
- **为何抓取结果全是 0？** 检查外部 API 是否返回正确字段；若缺失，函数会使用默认值 0，前端会显示 0。请在外部服务确保返回 `sales_today`、`sales_yesterday`、`conversion_rate` 等。
- **修改了 `.env` 后不生效？** 需要重新启动 Flask 应用与 Celery Worker/Beat，使 `load_dotenv()` 重新读取环境变量。
- **如何切换回抖音官方 API？** 将 `fetch_and_store_*` 中的 `_request` 调用改回 `douyin_client.get_*` 并确保 `Config` 中的 `DOUYIN_*` 参数已配置。
- **多 Worker 下缓存不一致？** 已迁移至 Redis 共享缓存 (`redis_cache.RedisCache`)，所有 Worker 读写同一 Redis 实例，配合 Lua 脚本保证原子性。
- **前端 403 Forbidden？** 部署后需修复文件权限：`chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 ...`

## 10. 更新记录
- **2026-08-22**：统一深色主题，前端 Design Tokens 体系，全量 Ant Design 样式覆盖
- **2026-08-12**：重构外部 API 集成，双域名配置，Celery 4 服务编排
- **2026-08-01**：核心功能实现

---

> 本设计文档已同步至项目根目录 `DESIGN.md`，后续如有架构变更请及时更新，以避免代码与文档不一致。