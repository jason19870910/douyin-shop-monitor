# 部署与同步指南

## 服务器信息
- **IP**: 122.51.208.138
- **用户**: root
- **SSH Key**: `C:\Users\Administrator\.ssh\id_rsa`
- **远程基础目录**: `/opt/douyin-platform`

## 脚本说明

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
- 服务器已安装 Docker 和 Docker Compose
- 服务器已配置好 nginx（SSL 证书在 `/etc/letsencrypt/live/wlkj-tech.cn-0001/`）
- SSH 密钥免密登录已配置

---

### 2. `sync.ps1` - 快速同步脚本（开发/测试环境）
仅同步文件，不构建、不重启服务

```powershell
# 同步所有（前端源码+后端代码+构建产物）
.\sync.ps1

# 仅同步前端
.\sync.ps1 -Target frontend

# 仅同步后端
.\sync.ps1 -Target backend

# 仅同步配置文件
.\sync.ps1 -Target config

# 试运行（查看会同步哪些文件，不实际传输）
.\sync.ps1 -DryRun

# 删除远程多余文件（慎用）
.\sync.ps1 -Delete
```

---

## 目录结构映射

| 本地路径 | 远程路径 | 说明 |
|---------|---------|------|
| `opt/douyin-platform/apps/monitor/` | `/opt/douyin-platform/apps/monitor/` | 后端代码 |
| `opt/douyin-platform/apps/monitor/frontend/` | `/opt/douyin-platform/apps/monitor/frontend/` | 前端源码 |
| `opt/douyin-platform/apps/monitor/frontend/build/` | `/opt/douyin-platform/apps/monitor/frontend/build/` | 前端构建产物 |

---

## 服务器端目录结构
```
/opt/douyin-platform/
├── apps/
│   └── monitor/
│       ├── .env                    # 后端环境变量
│       ├── docker-compose.yml      # 后端服务编排
│       ├── app.py                  # Flask 入口
│       ├── requirements.txt        # Python 依赖
│       ├── frontend/
│       │   ├── .env                # 前端环境变量
│       │   ├── docker-compose.yml  # 前端服务编排
│       │   ├── Dockerfile          # 前端镜像构建
│       │   ├── nginx.conf          # 容器内 nginx 配置
│       │   ├── build/              # 构建产物（由部署脚本同步）
│       │   │   ├── index.html
│       │   │   ├── assets/
│       │   │   └── ...
│       │   └── src/                # 前端源码
│       └── ...                     # 其他后端文件
```

---

## 首次部署步骤

### 1. 服务器初始化
```bash
# 在服务器上执行
mkdir -p /opt/douyin-platform/apps/monitor

# 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker

# 安装 Docker Compose
docker plugin install docker/compose:latest

# 安装 nginx（用于 SSL 终止）
apt-get update && apt-get install -y nginx certbot python3-certbot-nginx

# 申请 SSL 证书
certbot --nginx -d wlkj-tech.cn -d www.wlkj-tech.cn
```

### 2. 配置 nginx（宿主机层）
编辑 `/etc/nginx/sites-available/wlkj-tech.cn`：
```nginx
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

    # 前端静态文件直接由宿主机 nginx 服务
    location / {
        root /opt/douyin-platform/apps/monitor/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # API 代理到 Flask (5000)
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/wlkj-tech.cn /etc/nginx/sites-enabled/
nginx -t && nginx -s reload
```

### 3. 本地首次部署
```powershell
# 1. 确保 .env 文件已配置好（包含生产环境密钥）
# 2. 执行完整部署
.\deploy.ps1
```

---

## 常用运维命令

### 查看服务状态
```bash
# 后端服务
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor && docker-compose ps"
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor && docker-compose logs -f"

# 前端服务
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor/frontend && docker-compose ps"
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor/frontend && docker-compose logs -f"
```

### 手动重启服务
```bash
# 后端
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor && docker-compose restart"

# 前端
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor/frontend && docker-compose restart"
```

### 查看日志
```bash
# Nginx 访问日志
ssh root@122.51.208.138 "tail -f /var/log/nginx/access.log"

# Nginx 错误日志
ssh root@122.51.208.138 "tail -f /var/log/nginx/error.log"
```

---

## 故障排查

### 部署后前端显示空白
1. 检查 `build/index.html` 中的资源路径是否正确
2. 检查 nginx 配置中的 `root` 路径
3. 检查浏览器控制台网络请求是否 404

### API 请求 401/500
1. 检查后端服务是否正常：`curl http://127.0.0.1:5000/health`
2. 检查前端 `.env` 中的 `VITE_API_URL` 是否正确
3. 检查 Authorization header 是否正确传递

### 同步失败
1. 确认 SSH 密钥权限：`chmod 600 ~/.ssh/id_rsa`
2. 测试连接：`ssh -i ~/.ssh/id_rsa root@122.51.208.138 "echo ok"`
3. 检查远程磁盘空间：`df -h`

---

## 环境变量配置

### 后端 `.env` (`/opt/douyin-platform/apps/monitor/.env`)
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
DOUYIN_APP_ID=your-app-id
DOUYIN_APP_SECRET=your-app-secret
```

### 前端 `.env` (`/opt/douyin-platform/apps/monitor/frontend/.env`)
```env
VITE_API_URL=https://wlkj-tech.cn
VITE_API_KEY=your-api-key
VITE_DEV_MODE=false
```

---

## 自动化部署 (GitHub Actions / GitLab CI)

可参考 `.github/workflows/ci.yml` 配置自动部署，触发条件：
- 推送到 `main` 分支
- 创建 Release 标签
- 手动触发