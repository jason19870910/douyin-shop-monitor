# 项目技术文档

**版本**：1.0 (2026-06-16)
**维护**：Claw
**状态**：生产就绪（部分接口占位）

---

## 目录

1. [项目概览](#项目概览)
2. [系统架构](#系统架构)
3. [数据流向](#数据流向)
4. [服务清单](#服务清单)
5. [Python 数据服务（doudian_monitor）](#python-数据服务doudian_monitor)
6. [Node 视频发布系统（douyin-auto-publish）](#node-视频发布系统douyin-auto-publish)
7. [Nginx 反向代理配置](#nginx-反向代理配置)
8. [部署与运维](#部署与运维)
9. [API 接口总览](#api-接口总览)
10. [配置清单](#配置清单)
11. [故障排查](#故障排查)
12. [未来规划](#未来规划)

---

## 项目概览

本项目由两大核心系统组成：

- **doudian_monitor**：Python Flask 服务，负责抓取抖音创作者与抖店后台数据，提供统一 REST API。
- **douyin-auto-publish**：Node.js Express 系统，实现视频自动发布与转发，含 Web 管理界面。

二者通过 Nginx 统一对外暴露 HTTPS 接口，共享域名 `wlkj-tech.cn`。

基础设施：Alibaba Cloud OpenCloudOS (122.51.208.138)，使用 systemd/PM2 托管进程。

---

## 系统架构

```
用户浏览器
    ↓ (HTTPS)
Nginx (443)
    ├─> /api/* → 127.0.0.1:5000 (doudian_monitor)
    └─> /*     → 127.0.0.1:3000 (douyin-auto-publish)
```

**组件**：
- **Nginx**：SSL 终端、反向代理、负载（单机）
- **doudian_monitor**：Flask + requests + APScheduler（定时/手动）
- **douyin-auto-publish**：Express + EJS + fluent-ffmpeg + axios
- **数据库**：暂未启用（PostgreSQL 规划中）
- **监控**：Uptime Kuma (3001)

---

## 数据流向

```
[抖音开放平台 / 抖店后台]
        ↓ (HTTP GET/POST + Cookie/CSRF)
[doudian_monitor] → 聚合/转换 → JSON API (/api/*)
        ↓
    Nginx 代理
        ↓
[前端大屏 / 第三方客户端]
```

```
[用户上传视频]
        ↓
[douyin-auto-publish] (前端直传) → 抖音 CDN → 发布到账号
        ↓ (aweme.forward)
[转发到日常] (如需)
```

---

## 服务清单

| 服务 | 路径 | 端口 | 托管方式 | 主功能 |
|------|------|------|----------|--------|
| doudian_monitor | `/opt/douyin-platform/apps/monitor` | 5000 (内网) | systemd (`doudian_monitor.service`) | 数据抓取 API |
| douyin-auto-publish | `/home/douyin-auto-publish` | 3000 (内网) | PM2 (`pm2 start ecosystem.config.js`) | 视频发布管理 |
| Nginx | `/etc/nginx` | 80/443 | systemd (`nginx`) | 反向代理 |
| Uptime Kuma | `/opt/uptime-kuma` | 3001 (内网) | systemd (`uptime-kuma`) | 监控告警 |

---

## Python 数据服务（doudian_monitor）

### 技术栈
- Python 3.10+
- Flask
- requests
- python-dotenv
- APScheduler
- smtplib (邮件)

### 目录结构
```
/opt/douyin-platform/apps/monitor/
├── app.py              # Flask 应用
├── config.py           # 从 .env 加载配置
├── .env                # 环境变量（!! 不可提交 !!）
├── requirements.txt    # Python 依赖
├── doudian_monitor.service  # systemd unit
├── data/               # 历史 JSON 存储
├── logs/
│   └── app.log        # 运行日志
└── tests/              # 测试脚本（可选）
```

### 核心函数

| 函数 | 说明 | 依赖配置 |
|------|------|----------|
| `fetch_homepage_metrics()` | 抖店首页运营指标 | `HOMEPAGE_URL`, `COOKIE` |
| `fetch_product_metrics()` | 商品统计（各状态计数） | `PRODUCT_URL`, `COOKIE` |
| `fetch_order_metrics()` | 订单统计（各状态金额/单量） | `ORDERS_URL`, `COOKIE` |
| `fetch_creator_metrics()` | 创作者中心指标 | `CREATOR_URL`, `CREATOR_COOKIE`, `CREATOR_CSRF_TOKEN` |
| `fetch_compass()` | *待实现* 罗盘数据（GMV/曝光/点击） | `COMPASS_URL` (待配置) |
| `fetch_products(page, limit)` | *待实现* 商品列表 | `PRODUCT_LIST_URL` (待配置) |
| `scheduled_job()` | 定时抓取 + 邮件报告 + 存档 | SMTP 配置 |

### 启动流程
1. `systemd` 加载 `/etc/nginx/conf.d/wlkj-tech.cn.conf` 并反代至 5000
2. `doudian_monitor.service` 执行 `/usr/bin/python3 /opt/douyin-platform/apps/monitor/app.py`
3. `load_dotenv()` 在 `import config` 前加载 `.env`
4. Flask 监听 `0.0.0.0:5000`

### API 路由

| 方法 | 路径 | 描述 | 状态 |
|------|------|------|------|
| GET | `/api/creator` | 创作者中心数据（粉丝、播放、点赞等） | ✅ 真实数据 |
| GET | `/api/shop-stats` | 商品统计（all, on_sale, sold_out, off_shelf, banned, reviewing, rejected, approved） | ✅ 真实计数 |
| GET | `/api/orders` | 订单统计（各状态金额/单量） | ✅ 结构正常，金额待完善 |
| GET | `/api/compass` | 罗盘数据（GMV、曝光、点击、转化率） | ⏳ 占位实现 |
| GET | `/api/products` | 商品列表（分页：page, limit） | ⏳ 占位实现 |
| GET | `/api/refresh` | 手动触发全量抓取并保存历史 | ✅ |
| GET | `/history` | 最近抓取历史（默认 100 条） | ✅ |
| GET | `/health` | 健康检查 | ✅ |

**响应格式示例** `/api/creator`：
```json
{
  "粉丝总数": 1240,
  "视频播放量": 6,
  "点赞量": 2,
  "主页浏览量": 5,
  "净增粉丝": 0,
  "分享数": 0,
  "评论数": 0,
  "取消关注": 0,
  "封面点击率": 0
}
```

---

## Node 视频发布系统（douyin-auto-publish）

### 技术栈
- Node.js 20+
- Express + EJS
- axios
- fluent-ffmpeg
- dotenv
- PM2 (process manager)

### 目录结构
```
/home/douyin-auto-publish/
├── server.js           # Express 主服务
├── douyinClient.js     # 抖音 API 客户端
├── queueManager.js     # 发布队列
├── .env                # 应用配置
├── ecosystem.config.js # PM2 配置
├── views/              # EJS 模板
│   └── index-clean.ejs
├── public/
│   └── app.js          # 前端直传逻辑
└── uploads/            # 临时视频文件（可选）
```

### 主要功能

1. **OAuth 授权**：通过 `https://open.douyin.com` 引导用户授权，保存 `access_token` 至 `auth.json`
2. **视频直传**：前端从浏览器直传抖音 CDN（不经过服务器）
3. **发布/转发**：调用 `/publish/direct` 或 `/forward/daily`
4. **队列管理**：任务状态追踪、失败重试、历史记录

### 路由（部分）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 管理界面 |
| GET | `/oauth/url` | 生成授权 URL |
| GET | `/oauth/callback` | 授权回调，保存 token |
| POST | `/api/upload/sign` | 获取直传签名 |
| POST | `/api/publish/direct` | 直接发布（使用直传 URL） |
| POST | `/api/forward/daily` | 转发视频到日常 |

### 启动
```bash
cd /home/douyin-auto-publish
pm2 start ecosystem.config.js
pm2 save && pm2 startup  # 持久化
```

---

## Nginx 反向代理配置

**文件**：`/etc/nginx/conf.d/wlkj-tech.cn.conf`

关键规则：

```nginx
server {
    listen 443 ssl http2;
    server_name wlkj-tech.cn www.wlkj-tech.cn;

    # SSL 证书由 certbot 管理
    ssl_certificate /etc/letsencrypt/live/wlkj-tech.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wlkj-tech.cn/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # API 代理（注意：proxy_pass 末尾无斜杠）
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cookie_domain localhost $host;
    }

    # 主应用（Node 管理后台）
    location / {
        client_max_body_size 200M;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**注意**：`location /api/` 的 `proxy_pass` 必须**不加尾随 `/`**，否则 `/api/creator` 会被转发为 `/creator`，导致 Flask 路由不匹配。

---

## 部署与运维

### 1. 首次部署（服务器）

```bash
# 拉取代码
git clone <repo> /opt/douyin-platform/apps/monitor  # Python 服务
git clone <repo> /home/douyin-auto-publish  # Node 服务

# Python 环境
cd /opt/douyin-platform/apps/monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 .env（参考 config.py 和本文档配置清单）
cp .env.example .env
# 编辑 .env 填入真实 Cookie/URL（从浏览器复制）

# 配置 systemd
cp doudian_monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable doudian_monitor
systemctl start doudian_monitor

# Node 服务
cd /home/douyin-auto-publish
npm install
cp .env.example .env
# 编辑应用密钥
pm2 start ecosystem.config.js
pm2 save
```

### 2. Nginx 配置
将 `docs/nginx_wlkj-tech.cn.conf` 复制到 `/etc/nginx/conf.d/`，执行：
```bash
nginx -t && systemctl reload nginx
```

### 3. SSL（如无）
```bash
certbot --nginx -d wlkj-tech.cn -d www.wlkj-tech.cn
```

### 4. 监控
- 访问 `https://status.wlkj-tech.cn`（Uptime Kuma）
- 添加监控项：HTTP(s) 探测 `/api/health`、端口探测 5000、3000

---

## API 接口总览

### 数据服务（Python）

| 路径 | 方法 | 功能 | 示例请求 |
|------|------|------|----------|
| `/api/creator` | GET | 创作者中心数据 | `curl https://wlkj-tech.cn/api/creator` |
| `/api/shop-stats` | GET | 商品统计 | `curl https://wlkj-tech.cn/api/shop-stats` |
| `/api/orders` | GET | 订单统计 | `curl https://wlkj-tech.cn/api/orders` |
| `/api/compass` | GET | 罗盘数据（占位） | `curl https://wlkj-tech.cn/api/compass` |
| `/api/products` | GET | 商品列表（分页） | `curl \"https://wlkj-tech.cn/api/products?page=1&limit=10\"` |
| `/api/refresh` | GET | 手动刷新全量数据 | `curl https://wlkj-tech.cn/api/refresh` |
| `/history` | GET | 最近抓取历史 | `curl https://wlkj-tech.cn/history?limit=50` |
| `/health` | GET | 健康检查 | `curl https://wlkj-tech.cn/health` |

### 视频发布系统（Node）

| 路径 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 管理界面 |
| `/oauth/url` | GET | 生成抖音授权链接 |
| `/oauth/callback` | GET | OAuth 回调，保存 token |
| `/api/upload/sign` | POST | 获取直传签名（JSON 含 `upload_token`, `video_id`）|
| `/api/publish/direct` | POST | 直接发布视频（需直传完成后调用） |
| `/api/forward/daily` | POST | 转发视频到日常 |

---

## 配置清单

### doudian_monitor `.env`

| 键 | 说明 | 示例 |
|----|------|------|
| `HOMEPAGE_URL` | 抖店首页 API（含动态 token） | 从浏览器开发者工具复制 |
| `PRODUCT_URL` | 商品统计 API | ... |
| `ORDERS_URL` | 订单统计 API | ... |
| `COOKIE` | 抖店登录 Cookie（多个域） | 长字符串，包含 `sessionid`, `passport_csrf_token` 等 |
| `CREATOR_URL` | 创作者 Dashboard 固定 URL | `https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard` |
| `CREATOR_COOKIE` | 创作者中心独立 Cookie | 长字符串 |
| `CREATOR_CSRF_TOKEN` | 创作者中心 `x-secsdk-csrf-token` 值 | 32 位 hex |
| `SMTP_SERVER` | 告警邮件服务器（可选） | `smtp.gmail.com` |
| `SMTP_PORT` | 邮件端口 | `587` |
| `EMAIL_FROM` / `EMAIL_PASSWORD` | 发件人凭证 | ... |
| `SCHEDULE_HOURS` | 定时任务小时列表（0-23） | `9,21` |
| `ALERT_THRESHOLDS` | JSON 告警阈值 | `{"播放量": 10000}` |

> 🔐 生产环境建议使用密钥管理服务，`.env` 禁止提交到版本库。

### douyin-auto-publish `.env`

| 键 | 说明 |
|----|------|
| `DOUYIN_APP_KEY` | 抖音开放平台 App Key |
| `DOUYIN_APP_SECRET` | App Secret（泄露后立即重生成） |
| `DOUYIN_REDIRECT_URI` | OAuth 回调地址（需与应用一致） |
| `PORT` | 运行端口（默认 3000） |

---

## 故障排查

### 1. `/api/creator` 返回 200 但数据为模拟值
- 检查 `CREATOR_COOKIE` 和 `CREATOR_CSRF_TOKEN` 是否有效（从前端 cURL 复制）
- 检查 `load_dotenv()` 是否在 `import config` 前调用

### 2. `/api/*` 返回 404
- 确认 Nginx `location /api/` 的 `proxy_pass` **不带**尾部 `/`
- 重载 Nginx：`nginx -t && systemctl reload nginx`

### 3. 订单/商品金额为 0
- `HOMEPAGE_URL`、`PRODUCT_URL` 中的 `__token`、`a_bogus` 可能过期
- 需要从浏览器最新请求中复制完整 URL

### 4. 转发功能 401/403
- 确认 `auth.json` 中的 `scope` 包含 `aweme.forward`
- 抖音应用需审核通过并开启该权限

### 5. 服务崩溃
- 查看日志：`journalctl -u doudian_monitor.service -f` 或 `pm2 logs`
- 内存不足：调整 `data/` 存档频率

---

## 未来规划

- [ ] 实现 `/api/products` 真实商品列表分页
- [ ] 实现 `/api/compass` 罗盘数据抓取（需 cURL）
- [ ] 金额字段填充（需最新抖店 URL 与 Cookie）
- [ ] 集成 PostgreSQL 存储历史数据（替代 JSON 文件）
- [ ] 前端大屏图表迁移到 `/docs` 静态托管
- [ ] HTTPS 自动续期监控
- [ ] 告警渠道扩展（企业微信/钉钉）

---

**文档维护**：每次新增 API 或修改配置时，请同步更新本文件。
