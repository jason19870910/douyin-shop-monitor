# 运维手册 (RUNBOOK.md)

> **项目**: 抖音电商数据监控平台  
> **版本**: 2.0  
> **更新日期**: 2026-08-29  
> **适用环境**: 生产 / 预发布  
> **受众**: 运维工程师、后端工程师、值班人员

---

## 1. 系统架构速览（2026-08-29 更新）

```
                    ┌─────────────────────────────────────┐
                    │        服务器 122.51.208.138           │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │     Docker 网络             │    │
                    │  │     douyin-network          │    │
                    │  │  ┌────────┐ ┌──────────┐   │    │
                    │  │  │ nginx  │ │ frontend │   │    │
                    │  │  │ :80/443│ │   :80    │   │    │
                    │  │  └────────┘ └──────────┘   │    │
                    │  │  ┌────────┐ ┌──────────┐   │    │
                    │  │  │monitor │ │  redis   │   │    │
                    │  │  │ :5000  │ │  :6379   │   │    │
                    │  │  └────┬───┘ └──────────┘   │    │
                    │  └───────┼────────────────────┘    │
                    │          │                         │
                    │  ┌───────┴───────┐ ┌───────────┐   │
                    │  │celery_worker  │ │celery_beat│   │
                    │  │(数据抓取/告警) │ │(定时调度) │   │
                    │  └───────────────┘ └───────────┘   │
                    └─────────────────────────────────────┘
```

**核心服务**:

| 服务 | 容器名 | 端口 | 进程/配置 | 资源限制 | 健康检查 |
|------|--------|------|-----------|----------|----------|
| monitor | douyin_monitor | 5000 | gunicorn 4 workers | 1 CPU / 512MB | `/api/v1/health` |
| frontend | douyin_frontend | 80 (容器内) | nginx 静态服务 | 0.5 CPU / 256MB | `/health` |
| nginx | douyin_nginx | 80/443 | 反向代理 + SSL 终止 | 0.5 CPU / 128MB | - |
| celery_worker | douyin_celery_worker | - | 2 concurrency, prefork | 1 CPU / 512MB | 任务心跳 |
| celery_beat | douyin_celery_beat | - | 1 进程 | 0.5 CPU / 128MB | 调度心跳 |
| redis | douyin_redis | 6379 | redis-server | 0.5 CPU / 256MB | `redis-cli ping` |

**子域名路由** (由 Docker nginx 统一管理):

| 域名 | 目标服务 | 说明 |
|------|----------|------|
| `wlkj-tech.cn` | frontend + monitor API | 当前项目：前端页面 + `/api/*` |
| `api.wlkj-tech.cn` | 其他应用 | 代理到 `127.0.0.1:8080` |
| `cci.wlkj-tech.cn` | 其他应用 | 代理到 `172.20.0.1:8080` |
| `docs.wlkj-tech.cn` | 静态文档 | 服务 `/opt/douyin-platform/docs` |
| `status.wlkj-tech.cn` | 状态页 | 服务 `/var/www/status` |
| `122.51.208.138` | 抖音自动发布 | 代理到 `127.0.0.1:3000` |

---

## 2. 常用运维命令

### 2.1 Docker Compose 操作

```bash
# 进入项目根目录
cd /opt/douyin-platform

# 查看服务状态
docker compose ps

# 查看日志 (实时)
docker compose logs -f monitor
docker compose logs -f celery_worker
docker compose logs -f celery_beat
docker compose logs -f nginx
docker compose logs -f frontend
docker compose logs -f redis

# 重启单个服务
docker compose restart monitor
docker compose restart celery_worker
docker compose restart nginx
docker compose restart frontend

# 重新构建并重启
docker compose up -d --build monitor
docker compose up -d --build frontend

# 优雅停止
docker compose down

# 强制停止并清理
docker compose down --remove-orphans -v
```

### 2.2 服务健康检查

```bash
# API 健康检查 (HTTPS 生产环境)
curl -s https://wlkj-tech.cn/api/v1/health | jq .

# 前端页面检查
curl -I https://wlkj-tech.cn/

# OAuth 二维码接口
curl -s https://wlkj-tech.cn/api/v1/auth/qr-code | jq .

# 另一个应用 API 检查
curl -I https://api.wlkj-tech.cn/health

# Redis 连通性
docker exec douyin_redis redis-cli ping

# Celery Worker 状态
docker exec douyin_celery_worker celery -A celery_config inspect active

# Celery Beat 调度状态
docker exec douyin_celery_beat celery -A celery_config inspect scheduled

# 队列积压查看
docker exec douyin_redis redis-cli LLEN celery

# 查看 Nginx 配置测试
docker exec douyin_nginx nginx -t

# 重载 Nginx 配置
docker exec douyin_nginx nginx -s reload
```

### 2.3 数据操作

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

### 2.4 证书/密钥轮换

```bash
# 更新 Docker Secrets (需在宿主机操作)
echo "new_fxg_cookies" > /opt/douyin-platform/secrets/fxg_cookies.txt
echo "new_creator_cookies" > /opt/douyin-platform/secrets/creator_cookies.txt
echo "new_token" > /opt/douyin-platform/secrets/token.txt

# 重载服务使新密钥生效
docker compose restart monitor celery_worker celery_beat
```

---

## 3. 故障排查指南

### 3.1 Redis 故障

**现象**: 服务启动失败、健康检查不通过、缓存读写报错

**排查步骤**:
```bash
# 1. 检查 Redis 容器状态
docker compose ps redis

# 2. 查看 Redis 日志
docker compose logs redis | tail -50

# 3. 检查内存使用
docker exec douyin_redis redis-cli INFO memory

# 4. 检查连接数
docker exec douyin_redis redis-cli INFO clients

# 5. 检查持久化状态
docker exec douyin_redis redis-cli LASTSAVE
```

**常见原因及处理**:
| 原因 | 症状 | 处理 |
|------|------|------|
| 内存不足 | OOM Killer 杀进程 | 增加 `--maxmemory` 或清理过期键 |
| 磁盘满 | RDB/AOF 写入失败 | 清理磁盘或挂载更大卷 |
| 连接数耗尽 | `maxclients` 限制 | 调整 `redis.conf` 或重启 |
| 主从复制断开 | Slave 落后 | 检查网络/重启 Slave |

**应急预案**: 
- 切换到备用 Redis 实例 (修改 `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`)
- 降级模式: 禁用缓存，直接读取 JSON 文件

---

### 3.2 Cookie/Token 失效

**现象**: 外部 API 返回 401/403、数据抓取为空、告警 "抓取失败"

**排查步骤**:
```bash
# 1. 查看最近抓取日志
docker compose logs monitor | grep -i "error\|fail\|401\|403" | tail -20

# 2. 验证 Cookie 有效性 (在浏览器手工验证)

# 3. 检查 Secrets 文件是否存在
ls -la /opt/douyin-platform/secrets/

# 4. 手工测试 API 调用
docker exec douyin_monitor python -c "
from services.fetcher import get_fxg_cookies, get_creator_cookies
print('FXG:', get_fxg_cookies())
print('Creator:', get_creator_cookies())
"
```

**处理流程**:
1. **确认失效**: 对比浏览器登录状态
2. **获取新 Cookie**: 浏览器 F12 → Network → 任意请求 → Request Headers → Cookie
3. **更新 Secrets**: 
   ```bash
   echo "新的Cookie字符串" > /opt/douyin-platform/secrets/fxg_cookies.txt
   ```
4. **重载服务**: `docker compose restart monitor celery_worker celery_beat`
5. **验证恢复**: 观察日志 5 分钟，确认抓取成功

**预防措施**:
- 设置 Cookie 过期监控 (每 30 分钟检测一次)
- 建立多账号 Cookie 池，轮换使用
- 文档化 Cookie 获取 SOP

---

### 3.3 外部 API 不可用 / 频率限制

**现象**: 大量抓取任务失败、返回 429/5xx、Celery 任务重试耗尽

**排查步骤**:
```bash
# 1. 查看任务失败率
docker exec douyin_celery_worker celery -A celery_config inspect stats

# 2. 查看重试队列
docker exec douyin_redis redis-cli LLEN "celery:retry"

# 3. 测试外部 API 连通性
curl -I "https://fxg.jinritemai.com/product/tproduct/list"
curl -I "https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard"
```

**处理策略**:
| 场景 | 策略 |
|------|------|
| 429 Too Many Requests | 启用熔断器，暂停抓取 30 分钟，指数退避 |
| 5xx 服务端错误 | 指数退避重试 (最大 3 次)，记录告警 |
| 网络超时 | 增加超时时间，检查 DNS/防火墙 |
| 域名解析失败 | 检查 DNS 配置，添加 hosts 兜底 |

**熔断器配置** (待实现):
```python
# 在 fetcher.py 中添加
CIRCUIT_BREAKER_THRESHOLD = 5  # 连续 5 次失败触发熔断
CIRCUIT_BREAKER_TIMEOUT = 1800  # 熔断 30 分钟
```

---

### 3.4 Celery 任务堆积/超时

**现象**: 队列积压、任务执行超时、Worker 心跳丢失

**排查步骤**:
```bash
# 1. 查看队列长度
docker exec douyin_redis redis-cli LLEN celery

# 2. 查看活跃任务
docker exec douyin_celery_worker celery -A celery_config inspect active

# 3. 查看 Worker 状态
docker exec douyin_celery_worker celery -A celery_config inspect ping

# 4. 查看任务耗时分布
docker compose logs celery_worker | grep -E "Task .* succeeded|failed" | tail -20
```

**处理策略**:
| 原因 | 处理 |
|------|------|
| 任务耗时过长 | 优化 `_fetch_xxx_from_api`，增加并发限制 |
| Worker 数量不足 | `docker compose up -d --scale celery_worker=4` |
| 任务阻塞 (死锁) | 重启 Worker: `docker compose restart celery_worker` |
| 内存泄漏 | 设置 `--max-tasks-per-child=100` |

---

### 3.5 数据文件损坏/丢失

**现象**: 启动报 JSON 解析错误、数据为空、Pydantic 校验失败

**恢复步骤**:
```bash
# 1. 确认损坏文件
ls -la /opt/douyin-platform/data/

# 2. 从备份恢复 (对象存储/备份卷)
# 假设备份在 /backup/douyin-monitor/
cp /backup/douyin-monitor/products.json /opt/douyin-platform/data/

# 3. 或从 Redis 重建 (如果 Redis 正常)
docker exec douyin_monitor python -c "
from services.fetcher import cache, save_all_data
save_all_data()
print('数据已从 Redis 重建到 JSON 文件')
"

# 4. 重启服务
docker compose restart monitor
```

**备份策略** (待落实):
- 每日 02:00 全量备份到对象存储 (OSS/S3)
- 保留 30 天增量，90 天全量
- 定期恢复演练 (每季度)

---

### 3.6 Nginx 相关故障

**现象**: 域名无法访问、502 Bad Gateway、SSL 证书错误

**排查步骤**:
```bash
# 1. 检查 Nginx 容器状态
docker compose ps nginx

# 2. 测试 Nginx 配置
docker exec douyin_nginx nginx -t

# 3. 查看 Nginx 错误日志
docker exec douyin_nginx tail -f /var/log/nginx/error.log

# 4. 检查 upstream 解析 (Docker DNS resolver)
docker exec douyin_nginx cat /etc/nginx/nginx.conf | grep -A10 "resolver"

# 5. 检查 upstream 服务是否在同一网络
docker network inspect douyin-platform_douyin-network

# 6. 检查 SSL 证书是否存在
ls -la /etc/letsencrypt/live/wlkj-tech.cn/
```

**常见问题及处理**:
| 问题 | 原因 | 处理 |
|------|------|------|
| `host not found in upstream` | Docker DNS 未生效 | 确认 `resolver 127.0.0.11` 在 nginx.conf 中，重启 nginx 容器 |
| 502 Bad Gateway | upstream 服务未就绪 | 检查 monitor/health，确认服务健康后重载 nginx |
| SSL 证书过期 | certbot 未自动续期 | `certbot renew --dry-run` 检查，手动 `certbot renew` |
| 端口冲突 | 宿主机 nginx 占用 80/443 | `systemctl stop nginx` 停用宿主机 nginx |

---

### 3.7 安全事件 (敏感信息泄露)

**现象**: Git 历史发现 Cookie/Token、日志泄露、异常访问

**应急响应流程**:
1. **立即封禁**: 撤销泄露的 Token/Cookie
2. **轮换密钥**: 更新所有 Secrets，重启服务
3. **清理历史**: `git filter-repo` 或 BFG 清理 Git 历史
4. **通报**: 按公司安全流程上报
5. **复盘**: 根因分析，完善防泄露机制

**预防检查清单**:
- [ ] `.env` 在 `.gitignore` 中
- [ ] Docker Secrets 用于生产敏感信息
- [ ] CI 集成 `truffleHog`/`git-secrets` 扫描
- [ ] 定期轮换 (建议 30 天)
- [ ] 最小权限原则

---

## 4. 监控与告警

### 4.1 关键指标 (SLA)

| 指标 | 目标 | 告警阈值 | 采集方式 |
|------|------|----------|----------|
| API 可用性 | ≥ 99.9% | < 99.5% | 健康检查 + 日志 |
| 数据抓取成功率 | ≥ 99% | < 95% | Celery 任务状态 |
| 数据延迟 | ≤ 30 分钟 | > 60 分钟 | `last_update` 时间戳 |
| API P99 延迟 | ≤ 500ms | > 2s | Nginx/Flask 指标 |
| Redis 内存使用 | ≤ 80% | > 90% | Redis INFO |
| 队列积压 | ≤ 100 | > 500 | Redis LLEN |

### 4.2 告警渠道配置

```yaml
# 在 alert_config.json 中配置
{
  "channels": {
    "email": true,
    "wecom": true,
    "dingtalk": false
  },
  "thresholds": {
    "data_fetch_failure_rate": 0.05,
    "data_delay_minutes": 60,
    "queue_backlog": 500
  }
}
```

**企业微信 Webhook 配置**:
```bash
# 群聊 → 群设置 → 群机器人 → 添加 → 自定义 → 复制 Webhook URL
# 写入 Secrets 或环境变量
echo "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" > /opt/douyin-platform/secrets/wecom_webhook.txt
```

---

## 5. 部署与发布

### 5.1 标准发布流程

```bash
# 1. 代码合并到 main 分支 (PR 审核通过)
# 2. CI 自动运行: Lint → Test → Build Docker Image
# 3. 镜像推送到镜像仓库 (tag: git-short-sha)
# 4. 手动触发部署 (或自动部署到预发布)

# 生产部署命令
cd /opt/douyin-platform
docker compose pull
docker compose up -d --build

# 验证部署
curl -s https://wlkj-tech.cn/api/v1/health | jq .success
curl -I https://wlkj-tech.cn/
```

### 5.2 回滚流程

```bash
# 1. 查看镜像历史
docker images douyin-platform-monitor --format "table {{.Tag}}\t{{.CreatedAt}}"

# 2. 回滚到上一版本
docker tag douyin-platform-monitor:previous douyin-platform-monitor:latest
docker compose up -d --build

# 3. 或指定版本回滚
docker compose down
docker run -d --name douyin_monitor douyin-platform-monitor:v1.2.3
```

### 5.3 蓝绿部署 (推荐生产)

```bash
# 启动绿环境 (新版本)
docker compose -f docker-compose.yml -f docker-compose.green.yml up -d

# 验证绿环境
curl -s https://wlkj-tech.cn/api/v1/health

# 切换流量 (Nginx 修改 upstream)
# 验证 10 分钟无异常后，下线蓝环境
```

---

## 6. 容量规划

### 6.1 资源基线

| 资源 | 当前规格 | 使用率 (P95) | 扩容触发点 | 最大规格 |
|------|----------|--------------|------------|----------|
| Monitor CPU | 1 core | 45% | > 70% | 2 cores |
| Monitor Memory | 512MB | 60% | > 80% | 1GB |
| Redis Memory | 256MB | 55% | > 80% | 512MB |
| Redis Connections | 50 | 30% | > 80% | 10000 |
| Celery Workers | 2 | 50% | 队列 > 100 | 8 |
| Disk (data/) | 2GB | 10% | > 80% | 20GB |

### 6.2 扩容操作

```bash
# 水平扩展 Worker
docker compose up -d --scale celery_worker=4

# 垂直扩容 Monitor (修改 docker-compose.yml deploy.resources)
# 重启生效
docker compose up -d monitor

# Redis 扩容 (修改 maxmemory)
# 需重启 Redis
docker compose restart redis
```

---

## 7. 维护窗口与变更管理

### 7.1 维护窗口
- **日常维护**: 每天 02:00-04:00 (低峰期)
- **版本发布**: 周二/周四 10:00-12:00
- **紧急变更**: 随时，需变更审批

### 7.2 变更审批清单
- [ ] 变更描述与风险评估
- [ ] 回滚方案
- [ ] 测试验证记录
- [ ] 审批人签名
- [ ] 通知相关方

---

## 8. 联系人与升级路径

| 角色 | 姓名 | 电话 | 企业微信 | 职责 |
|------|------|------|----------|------|
| 项目经理 | - | - | - | 总协调、对外沟通 |
| 运维主责 | - | - | - | 基础设施、部署、监控 |
| 后端主责 | - | - | - | 业务逻辑、API、数据 |
| 前端主责 | - | - | - | 界面、构建、CI/CD |
| 安全负责人 | - | - | - | 漏洞、合规、应急响应 |

**升级路径**:
```
L1: 值班运维 (15分钟响应)
    ↓ 无法解决/超过30分钟
L2: 后端/运维主责 (30分钟响应)
    ↓ 涉及架构/数据安全/跨团队
L3: 项目经理 + 技术总监 (1小时响应)
    ↓ 重大安全/业务中断
L4: VP/CTO (立即响应)
```

---

## 9. 常用链接

| 系统 | 地址 | 备注 |
|------|------|------|
| Grafana 监控 | http://grafana.xxx | 需 VPN |
| Loki 日志 | http://loki.xxx | 需 VPN |
| GitLab 仓库 | http://gitlab.xxx/xxx | 代码/MR/CI |
| 镜像仓库 | http://harbor.xxx | Docker 镜像 |
| 文档中心 | http://wiki.xxx | 架构/设计/运维 |

---

## 10. 附录

### 10.1 环境变量速查

```bash
# 核心配置
DATA_DIR=/data
FXG_BASE_URL=https://fxg.jinritemai.com
CREATOR_BASE_URL=https://creator.douyin.com
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# 密钥 (通过 Docker Secrets 注入)
# FXG_COOKIES, CREATOR_COOKIES, TOKEN, MS_TOKEN, A_BOGUS, VERIFY_FP, FP
# FXG_SHOP_ID, FXG_LOG_ID, API_KEY

# OAuth 配置
DOUYIN_APP_ID=aw370towtp6bg82b
DOUYIN_APP_SECRET=a4fae3b38c0b1ee982c849fb3b23b353
# 仅包含抖音开放平台控制台实际授权的 OAuth scope 代码
# 当前仅获得 user_info（授权登录能力/获取用户基本信息）
# 如需更多权限，需在控制台申请对应 scope 后添加
DOUYIN_SCOPE=user_info
OAUTH_REDIRECT_URI=https://wlkj-tech.cn/api/v1/auth/callback
```

### 10.2 常用端口

| 服务 | 端口 | 协议 | 访问控制 |
|------|------|------|----------|
| Monitor API | 5000 | HTTP | Docker 网络内 + Nginx 反向代理 |
| Frontend | 80 | HTTP | Docker 网络内 + Nginx 反向代理 |
| Nginx (外部) | 80/443 | HTTP/HTTPS | 公网访问 |
| Redis | 6379 | TCP | Docker 网络内仅容器访问 |
| Celery Flower | 5555 | HTTP | 可选，监控用 |
| Prometheus | 9090 | HTTP | 内网仅监控访问 |

---

## 11. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-08-29 | v2.0 | 统一 Docker Compose 架构，Docker Nginx 管理所有子域名，停用宿主机 Nginx，前端容器化，OAuth scope 更新为 15 个权限 |
| 2026-08-26 | v1.x | 旧架构：宿主机 Nginx + 手动同步构建产物 |

---

> **文档维护**: 每次重大变更后更新  
> **下次审查**: 2026-09-29  
> **反馈渠道**: GitLab Issue / 企业微信运维群