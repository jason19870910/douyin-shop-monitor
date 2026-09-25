# 部署与同步指南

## 服务器信息
- **IP**: 122.51.208.138
- **用户**: root
- **SSH Key**: `C:\Users\Administrator\.ssh\id_rsa`
- **远程基础目录**: `/opt/douyin-platform`

## 当前架构（2026-08-29 更新）
```
┌─────────────────────────────────────────────────────────────────┐
│                    服务器 122.51.208.138                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Docker 网络: douyin-network                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │  nginx   │ │ frontend │ │ monitor  │ │  redis   │   │   │
│  │  │ :80/:443 │ │   :80    │ │  :5000   │ │  :6379   │   │   │
│  │  └──────────┘ └──────────┘ └────┬─────┘ └──────────┘   │   │
│  └─────────────────────────────────┼──────────────────────┘   │
│                                    │                          │
│  ┌─────────────────────┐ ┌─────────┴─────────┐ ┌───────────┐  │
│  │ celery_worker       │ │ celery_beat       │ │ certbot   │  │
│  │ (数据抓取/告警)      │ │ (定时调度)        │ │ (SSL续期) │  │
│  └─────────────────────┘ └───────────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心变更（重要）
- **统一 Nginx**: 使用 Docker 容器 `douyin_nginx` 管理所有子域名（wlkj-tech.cn, api.wlkj-tech.cn, cci.wlkj-tech.cn, docs.wlkj-tech.cn, status.wlkj-tech.cn）
- **宿主机 Nginx 已停用**: `systemctl stop nginx`，不再使用宿主机层反向代理
- **前端构建产物**: 由 `douyin_frontend` 容器内 Nginx 直接服务，不再同步到宿主机
- **Docker Compose 统一编排**: 根目录 `docker-compose.yml` 管理所有服务

---

## 部署脚本

### 1. `deploy.ps1` - 完整部署脚本（推荐生产环境）
包含：前端构建 → 文件同步 → Docker 服务重启 → 健康检查

```powershell
# 完整部署（构建+同步+重启）
.\deploy.ps1

# 仅部署前端（跳过后端）
.\deploy.ps1 -OnlyFrontend

# 仅部署后端（跳过前端构建）
.\deploy.ps1 -OnlyBackend

# 跳过前端构建（使用已有 build 目录）
.\deploy.ps1 -SkipBuild

# 指定环境
.\deploy.ps1 -Environment production
```

**前置条件**：
- 服务器已安装 Docker 和 Docker Compose (v2+)
- 服务器 SSL 证书在 `/etc/letsencrypt/live/wlkj-tech.cn/`
- SSH 密钥免密登录已配置
- 所有 Docker Secrets 已配置（见下文）

---

### 2. `sync.ps1` - 快速同步脚本（开发/测试环境）
仅同步文件，不构建、不重启服务

```powershell
# 同步所有（前端源码+后端代码+配置文件）
.\sync.ps1

# 仅同步前端源码
.\sync.ps1 -Target frontend

# 仅同步后端代码
.\sync.ps1 -Target backend

# 仅同步配置文件
.\sync.ps1 -Target config

# 试运行（查看会同步哪些文件，不实际传输）
.\sync.ps1 -DryRun

# 删除远程多余文件（慎用）
.\sync.ps1 -Delete
```

---

## 目录结构映射（当前）

| 本地路径 | 远程路径 | 说明 |
|---------|---------|------|
| `src/backend/` | `/opt/douyin-platform/src/backend/` | 后端代码 |
| `src/frontend/` | `/opt/douyin-platform/src/frontend/` | 前端源码 |
| `nginx/nginx.conf` | `/opt/douyin-platform/nginx/nginx.conf` | Nginx 主配置 |
| `nginx/conf.d/` | `/opt/douyin-platform/nginx/conf.d/` | Nginx 站点配置 |
| `config/.env` | `/opt/douyin-platform/config/.env` | 环境变量 |
| `docker-compose.yml` | `/opt/douyin-platform/docker-compose.yml` | 统一编排文件 |
| `secrets/` | `/opt/douyin-platform/secrets/` | Docker Secrets（敏感信息） |

---

## 服务器端目录结构（当前）
```
/opt/douyin-platform/
├── config/
│   └── .env                    # 环境变量（含 DOUYIN_SCOPE 等）
├── nginx/
│   ├── nginx.conf              # Nginx 主配置（含 Docker DNS resolver）
│   └── conf.d/
│       ├── wlkj-tech.cn.conf           # 当前项目：前端 + API
│       ├── api.wlkj-tech.cn.conf       # 其他应用：代理到 127.0.0.1:8080
│       ├── cci.wlkj-tech.cn.conf       # 其他应用
│       ├── docs.wlkj-tech.cn.conf      # 静态文档站点
│       ├── status.wlkj-tech.cn.conf    # 状态页
│       └── douyin-auto-publish.conf    # 抖音自动发布系统
├── secrets/
│   ├── fxg_cookies.txt              # 抖店 Cookie（完整字符串）
│   ├── creator_cookies.txt          # 创作者中心 Cookie
│   ├── token.txt                    # __TOKEN
│   ├── ms_token.txt                 # MS_TOKEN
│   ├── a_bogus.txt                  # a_bogus 签名
│   ├── verify_fp.txt                # verifyFp
│   ├── fp.txt                       # fp 指纹
│   ├── fxg_shop_id.txt              # 抖店店铺 ID
│   ├── fxg_log_id.txt               # 抖店日志 ID
│   ├── api_key.txt                  # API Key（可选）
│   ├── douyin_app_id.txt            # 抖音应用 ID
│   ├── douyin_app_secret.txt        # 抖音应用 Secret
│   ├── douyin_access_token.txt      # 抖音 Access Token
│   └── redirect_uri.txt             # OAuth 回调地址
├── src/
│   ├── backend/                     # 后端源码
│   └── frontend/                    # 前端源码
├── docker-compose.yml               # 统一编排（根文件）
├── docker-compose.prod.yml          # 生产环境覆盖（使用预构建镜像）
└── data/                            # 数据目录（容器内 /data，需手动创建）
```

---

## 首次部署步骤

### 1. 服务器初始化
```bash
# 在服务器上执行
mkdir -p /opt/douyin-platform/{config,nginx/conf.d,secrets,src,logs}

# 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker

# 安装 Docker Compose v2
docker plugin install docker/compose:latest

# 申请 SSL 证书（所有子域名）
certbot certonly --standalone -d wlkj-tech.cn -d www.wlkj-tech.cn \
  -d api.wlkj-tech.cn -d cci.wlkj-tech.cn \
  -d docs.wlkj-tech.cn -d status.wlkj-tech.cn
```

### 2. 配置 Docker Secrets
```bash
# 在 /opt/douyin-platform/secrets/ 创建所有 secret 文件
# 示例：
echo "your_fxg_cookies" > /opt/douyin-platform/secrets/fxg_cookies.txt
echo "your_creator_cookies" > /opt/douyin-platform/secrets/creator_cookies.txt
echo "your_token" > /opt/douyin-platform/secrets/token.txt
# ... 其他 secrets

# 设置权限
chmod 600 /opt/douyin-platform/secrets/*
```

### 3. 配置环境变量
```bash
# 复制模板并编辑
cp /opt/douyin-platform/config/.env.example /opt/douyin-platform/config/.env
# 编辑关键变量：
# - DOUYIN_SCOPE: 15个权限代码（见 PERMISSION.md）
# - ALERT_EMAIL: 告警邮箱
# - SCHEDULE_INTERVAL_MINUTES: 同步间隔
```

### 4. 本地首次部署
```powershell
# 1. 确保 .env 文件已配置好（包含生产环境密钥）
# 2. 执行完整部署
.\deploy.ps1
```

---

## 常用运维命令

### 查看服务状态
```bash
# 进入项目根目录
cd /opt/douyin-platform

# 查看所有服务状态
docker compose ps

# 查看特定服务日志
docker compose logs -f monitor
docker compose logs -f celery_worker
docker compose logs -f celery_beat
docker compose logs -f nginx
docker compose logs -f frontend
docker compose logs -f redis
```

### 手动重启服务
```bash
# 重启单个服务
docker compose restart monitor
docker compose restart nginx

# 重新构建并重启后端
docker compose up -d --build monitor

# 重新构建并重启前端
docker compose up -d --build frontend

# 优雅停止所有服务
docker compose down

# 强制停止并清理
docker compose down --remove-orphans -v
```

### 服务健康检查
```bash
# API 健康检查
curl -s https://wlkj-tech.cn/api/v1/health | jq .

# 前端页面检查
curl -I https://wlkj-tech.cn/

# OAuth 二维码接口
curl -s https://wlkj-tech.cn/api/v1/auth/qr-code | jq .

# 另一个应用 API
curl -I https://api.wlkj-tech.cn/health

# Redis 连通性
docker exec douyin_redis redis-cli ping

# Celery Worker 状态
docker exec douyin_celery_worker celery -A celery_config inspect active

# Celery Beat 调度状态
docker exec douyin_celery_beat celery -A celery_config inspect scheduled
```

### 数据操作
```bash
# 手动触发全量同步
docker exec douyin_monitor python -c "
from services.fetcher import scheduled_job
result = scheduled_job()
print(result)
"

# 手动触发单项任务
docker exec douyin_monitor python -c "
from tasks import fetch_products_task, fetch_orders_task
fetch_products_task.delay()
fetch_orders_task.delay()
"

# 查看缓存数据
docker exec douyin_redis redis-cli GET products | jq .
docker exec douyin_redis redis-cli GET orders | jq .

# 清理缓存 (谨慎操作)
docker exec douyin_redis redis-cli FLUSHDB
```

### 证书/密钥轮换
```bash
# 更新 Docker Secrets (在宿主机操作)
echo "new_fxg_cookies" > /opt/douyin-platform/secrets/fxg_cookies.txt
echo "new_creator_cookies" > /opt/douyin-platform/secrets/creator_cookies.txt

# 重载服务使新密钥生效
docker compose restart monitor celery_worker celery_beat
```

---

## 故障排查

### 部署后前端显示空白
1. 检查 `douyin_frontend` 容器日志：`docker compose logs frontend`
2. 检查容器内 Nginx 配置：`docker exec douyin_frontend cat /etc/nginx/conf.d/default.conf`
3. 检查浏览器控制台网络请求是否 404

### API 请求 401/500
1. 检查后端服务是否正常：`curl https://wlkj-tech.cn/api/v1/health`
2. 检查前端 `.env` 中的 `VITE_API_URL` 是否为 `https://wlkj-tech.cn`
3. 检查 Authorization header 是否正确传递（`localStorage.authToken`）

### 同步失败
1. 确认 SSH 密钥权限：`chmod 600 ~/.ssh/id_rsa`
2. 测试连接：`ssh -i ~/.ssh/id_rsa root@122.51.208.138 "echo ok"`
3. 检查远程磁盘空间：`df -h`

### Nginx 相关问题
```bash
# 测试 Nginx 配置
docker exec douyin_nginx nginx -t

# 重载 Nginx 配置
docker exec douyin_nginx nginx -s reload

# 查看 Nginx 错误日志
docker exec douyin_nginx tail -f /var/log/nginx/error.log

# 检查 upstream 解析
docker exec douyin_nginx cat /etc/nginx/nginx.conf | grep -A5 "upstream"
```

---

## 环境变量配置

### 后端配置 (`/opt/douyin-platform/config/.env`)
```env
# 基础配置
DATA_DIR=/data
SCHEDULE_INTERVAL_MINUTES=60
ALERT_EMAIL=262368285@qq.com
API_AUTH_TOKEN=your_api_auth_token
API_KEY=demo_key_123

# 抖音开放平台 OAuth
DOUYIN_APP_ID=aw370towtp6bg82b
DOUYIN_APP_SECRET=a4fae3b38c0b1ee982c849fb3b23b353
DOUYIN_ACCESS_TOKEN=your_access_token
OAUTH_REDIRECT_URI=https://wlkj-tech.cn/api/v1/auth/callback
# 仅包含应用在抖音开放平台控制台实际获得的 OAuth scope 代码
# 当前仅获得 user_info（授权登录能力/获取用户基本信息）
# 如需更多权限，需在控制台申请后添加对应 scope 代码（逗号分隔，不可包含中文名称）
DOUYIN_SCOPE=user_info

# 外部 API 基础 URL
FXG_BASE_URL=https://fxg.jinritemai.com
CREATOR_BASE_URL=https://creator.douyin.com

# 公共请求头
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Celery / Redis（仅 docker-compose.yml 使用）
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 前端配置 (`/opt/douyin-platform/src/frontend/.env.production`)
```env
VITE_API_URL=https://wlkj-tech.cn
VITE_API_KEY=demo_key_123
VITE_DEV_MODE=false
```

---

## Docker Secrets 配置清单（必填）

| Secret 文件 | 说明 | 获取方式 |
|------------|------|----------|
| `fxg_cookies.txt` | 抖店完整 Cookie | 浏览器登录 fxg.jinritemai.com → F12 Network → Cookie |
| `creator_cookies.txt` | 创作者中心完整 Cookie | 浏览器登录 creator.douyin.com → F12 Network → Cookie |
| `token.txt` | `__TOKEN` 长效签名 | 抖店页面脚本/抓包获取 |
| `ms_token.txt` | `MS_TOKEN` 动态令牌 | 抖店页面脚本获取 |
| `a_bogus.txt` | `a_bogus` 防爬签名 | 实时生成（V8 执行 JS） |
| `verify_fp.txt` | `verifyFp` 指纹 | 页面获取 |
| `fp.txt` | `fp` 指纹 | 页面获取 |
| `fxg_shop_id.txt` | 抖店店铺 ID | 抖店后台获取 |
| `fxg_log_id.txt` | 抖店日志 ID | 抖店后台获取 |
| `api_key.txt` | API Key（可选） | 自定义 |
| `douyin_app_id.txt` | 抖音应用 ID | 抖音开放平台应用配置 |
| `douyin_app_secret.txt` | 抖音应用 Secret | 抖音开放平台应用配置 |
| `douyin_access_token.txt` | 抖音 Access Token | OAuth 授权后获取 |
| `redirect_uri.txt` | OAuth 回调地址 | `https://wlkj-tech.cn/api/v1/auth/callback` |

---

## 自动化部署 (GitHub Actions)

可参考 `.github/workflows/deploy.yml` 配置自动部署，触发条件：
- 推送到 `main` 分支
- 创建 Release 标签
- 手动触发

---

## 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-08-29 | v2.0 | 统一 Docker Compose 架构，Docker Nginx 管理所有子域名，停用宿主机 Nginx，前端构建产物容器化，OAuth scope 更新为 15 个权限 |
| 2026-08-26 | v1.x | 旧架构：宿主机 Nginx + 手动同步构建产物 |

---

*文档维护：每次重大部署架构变更后更新*