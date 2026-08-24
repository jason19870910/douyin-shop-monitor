# 运维操作手册

> **版本**: 1.0.0  
> **更新日期**: 2026-08-18  
> **适用环境**: 生产 / Staging  
> **受众**: 运维工程师、SRE、Tech Lead

---

## 1. 服务拓扑与端口

| 服务 | 进程/容器 | 内部端口 | 外部暴露 | 依赖 |
|------|----------|---------|---------|------|
| Nginx | 宿主机 systemd | 80/443 | ✅ | Flask (5000) |
| Flask API | Docker `monitor` | 5000 | ❌ (仅内网) | Redis, Celery |
| Celery Worker | Docker `celery_worker` | - | ❌ | Redis, Flask |
| Celery Beat | Docker `celery_beat` | - | ❌ | Redis |
| Redis | Docker `redis` | 6379 | ❌ | - |
| 前端静态资源 | Flask `static` | 5000 | ✅ (经 Nginx) | - |

---

## 2. 常用操作命令速查

```bash
# ==================== 服务状态 ====================
# 查看所有容器状态
docker compose ps

# 查看 systemd 服务状态
systemctl status doudian_monitor

# 查看 Nginx 状态
systemctl status nginx
nginx -t  # 配置测试

# ==================== 日志查看 ====================
# Flask 应用日志
docker logs -f douyin_monitor --tail 200

# Celery Worker 日志
docker logs -f douyin_celery_worker --tail 200

# Celery Beat 日志
docker logs -f douyin_celery_beat --tail 200

# Nginx 访问/错误日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Systemd 日志
journalctl -u doudian_monitor -f

# ==================== 健康检查 ====================
# API 健康检查
curl -s https://wlkj-tech.cn/api/health | jq .

# 后端直连健康检查
curl -s http://127.0.0.1:5000/api/health | jq .

# Celery Worker 状态
docker exec douyin_celery_worker celery -A tasks inspect active

# Celery Beat 定时任务
docker exec douyin_celery_beat celery -A tasks inspect scheduled

# Redis 连通性
docker exec douyin_redis redis-cli ping

# ==================== 服务控制 ====================
# 重启全栈 (Docker Compose)
docker compose restart

# 仅重启 Flask
docker compose restart monitor

# 仅重启 Celery Worker
docker compose restart celery_worker

# 重载 Nginx 配置
nginx -t && systemctl reload nginx

# Systemd 方式重启
systemctl restart doudian_monitor

# ==================== 数据同步触发 ====================
# 手动触发全量同步
curl -X POST https://wlkj-tech.cn/api/sync

# 查看同步状态
curl -s https://wlkj-tech.cn/api/health | jq .data.last_update
```

---

## 3. 扩容操作

### 3.1 水平扩容 Celery Worker
```bash
# 临时扩容 (当前会话生效)
docker compose up -d --scale celery_worker=3

# 永久扩容 (修改 docker-compose.yml)
# services:
#   celery_worker:
#     deploy:
#       replicas: 3
# 然后重新部署
docker compose up -d --no-deps celery_worker
```

**验证**：
```bash
# 查看 worker 数量
docker exec douyin_celery_worker celery -A tasks inspect active | jq 'keys | length'

# 查看队列积压
docker exec douyin_redis redis-cli LLEN celery
```

### 3.2 Flask 多实例 (需 Nginx 上游配置)
```nginx
# nginx.conf upstream 块
upstream flask_backend {
    least_conn;
    server 127.0.0.1:5000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5001 weight=1 max_fails=3 fail_timeout=30s;  # 新实例
    keepalive 32;
}
```
然后 `systemctl reload nginx`。

---

## 4. 备份与恢复

### 4.1 备份内容清单
| 数据类型 | 位置 | 备份频率 | 保留策略 |
|---------|------|---------|---------|
| 业务数据 (JSON) | `/opt/douyin-platform/apps/monitor/data/` | 每日 02:00 | 30 天 |
| Redis 数据 | `redis` 容器卷 | 每日 03:00 | 7 天 |
| 配置文件 | `.env`, `docker-compose.yml`, `nginx.conf` | 变更时 | 永久 |
| Nginx SSL 证书 | `/etc/letsencrypt/` | 证书续期前 | 永久 |
| 应用日志 | `/var/log/douyin_monitor/` | 每周 | 90 天 |

### 4.2 备份脚本示例
```bash
#!/bin/bash
# backup.sh - 每日 02:00 cron 执行
set -euo pipefail

BACKUP_DIR="/backup/douyin_monitor/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. 业务数据
tar -czf "$BACKUP_DIR/data.tar.gz" -C /opt/douyin-platform/apps/monitor data/

# 2. Redis RDB
docker exec douyin_redis redis-cli BGSAVE
sleep 5
docker cp douyin_redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# 3. 配置文件
tar -czf "$BACKUP_DIR/config.tar.gz" \
  /opt/douyin-platform/apps/monitor/.env \
  /opt/douyin-platform/apps/monitor/docker-compose.yml \
  /etc/nginx/conf.d/wlkj-tech.cn.conf

# 4. 清理 30 天前备份
find /backup/douyin_monitor -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

### 4.3 恢复演练 (每季度必做)
```bash
# 1. 停止服务
docker compose down
systemctl stop nginx

# 2. 恢复数据
tar -xzf /backup/douyin_monitor/20260818/data.tar.gz -C /opt/douyin-platform/apps/monitor/
docker cp /backup/douyin_monitor/20260818/redis.rdb douyin_redis:/data/dump.rdb

# 3. 启动 Redis 并验证
docker compose up -d redis
docker exec douyin_redis redis-cli ping

# 4. 启动应用
docker compose up -d
systemctl start nginx

# 5. 验证
curl -s https://wlkj-tech.cn/api/health | jq .
```

---

## 5. 证书轮换

### 5.1 Let's Encrypt 自动续期 (已配置)
```bash
# 检查证书有效期
certbot certificates

# 手动续期测试 (dry-run)
certbot renew --dry-run

# 强制续期
certbot renew --force-renewal
systemctl reload nginx
```

### 5.2 证书到期告警
- 配置 `certbot` 系统定时器自动续期
- 添加监控规则：证书过期 < 14 天 → PagerDuty/企业微信告警

---

## 6. 故障排查决策树

### 6.1 症状：前端页面白屏 / 静态资源 404
```
START
  │
  ├─► 检查 Nginx 错误日志 → 有错? → 修复配置 → reload nginx
  │
  ├─► 检查构建产物是否存在 → ls /opt/.../build/assets/
  │       否 → 重新构建前端 → scp 部署
  │
  ├─► 检查 Nginx location /assets/ alias 路径是否匹配
  │
  └─► 浏览器 Network 面板 → 看具体资源请求 URL 是否正确
```

### 6.2 症状：API 返回 502/504 / `ERR_CONNECTION_REFUSED`
```
START
  │
  ├─► 检查 Flask 容器状态 → docker ps | grep monitor
  │       停止? → docker logs douyin_monitor → 修复 → docker compose restart monitor
  │
  ├─► 检查 Nginx upstream → upstream flask_backend 指向正确端口?
  │
  ├─► 检查防火墙/安全组 → 5000 端口内网互通?
  │
  └─► 检查 Flask 健康检查 → curl http://127.0.0.1:5000/api/health
```

### 6.3 症状：数据同步失败 / 定时任务不执行
```
START
  │
  ├─► 检查 Celery Beat 状态 → docker logs douyin_celery_beat
  │       无日志? → 重启 beat → docker compose restart celery_beat
  │
  ├─► 检查 Celery Worker 状态 → celery inspect active
  │       无 worker? → 扩容 worker / 重启 worker
  │
  ├─► 检查 Redis 连通性 → redis-cli ping
  │
  ├─► 检查任务是否入队 → redis-cli LLEN celery
  │
  ├─► 检查任务执行日志 → docker logs douyin_celery_worker
  │       报错? → 看具体异常 (外部 API 限流/签名失效/网络超时)
  │
  └─► 手动触发同步验证 → curl -X POST /api/sync
```

### 6.4 症状：外部 API 返回 403/429 / 签名失效
```
START
  │
  ├─► 检查 .env 中 Cookie/Token 是否过期 → 更新 FXG_COOKIES, CREATOR_COOKIES
  │
  ├─► 检查动态签名参数 → __TOKEN, MS_TOKEN, a_bogus, verifyFp, fp 是否有效
  │
  ├─► 检查 User-Agent 是否被拦截 → 更新为最新 Chrome UA
  │
  ├─► 检查请求频率 → 是否触发限流 (429) → 降低 Celery 并发/增加延迟
  │
  └─► 联系上游确认接口变更 → 更新 douyin_sign.py 签名逻辑
```

### 6.5 症状：磁盘空间不足 / 容器重启频繁
```
START
  │
  ├─► df -h → 看哪个分区满了
  │
  ├─► docker system df → 镜像/容器/卷占用
  │       清理: docker system prune -a --volumes
  │
  ├─► 日志文件过大 → /var/log/nginx/, /var/log/douyin_monitor/
  │       配置 logrotate 压缩保留 7 天
  │
  ├─► Redis 内存 → redis-cli INFO memory
  │       设置 maxmemory-policy allkeys-lru
  │
  └─► 业务数据 JSON 过大 → 归档历史数据 / 迁移至 PostgreSQL
```

---

## 7. 监控与告警规则

### 7.1 关键指标 (Prometheus + Grafana / Loki)
| 指标 | 告警阈值 | 严重级别 | 通知渠道 |
|------|---------|---------|---------|
| `api_health_status != 1` | 连续 3 次失败 | P0 (Critical) | 电话 + 企业微信 |
| `api_latency_p99 > 500ms` | 持续 5 分钟 | P1 (High) | 企业微信 |
| `celery_queue_length > 1000` | 持续 10 分钟 | P1 | 企业微信 |
| `celery_worker_count < 期望数` | 立即 | P0 | 电话 |
| `redis_memory_used > 80% maxmemory` | 持续 15 分钟 | P2 (Warning) | 企业微信 |
| `disk_usage > 85%` | 立即 | P1 | 企业微信 |
| `cert_expiry_days < 14` | 每日检查 | P2 | 企业微信 |
| `sync_last_update > 2 小时` | 立即 | P1 | 企业微信 |
| `external_api_error_rate > 5%` | 持续 5 分钟 | P1 | 企业微信 |

### 7.2 日志聚合查询 (Loki)
```logql
# 查看最近 1 小时错误日志
{job="douyin_monitor"} |= "ERROR" |~ "(?i)(exception|traceback|failed)"

# 查看同步任务耗时
{job="douyin_monitor"} |~ "sync.*completed" | json | duration > 30s

# 查看外部 API 错误
{job="douyin_monitor"} |= "external" |= "403" or |= "429" or |= "500"
```

---

## 8. 版本发布与回滚

### 8.1 发布流程
```bash
# 1. 创建 Release Tag (触发 CI 自动构建镜像)
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# 2. CI 自动: 构建镜像 → 推送 Docker Hub → 更新 CHANGELOG

# 3. 生产服务器拉取新镜像
docker compose pull

# 4. 滚动重启 (零停机)
docker compose up -d --no-deps monitor
# 等待健康检查通过
sleep 10
docker compose up -d --no-deps celery_worker
docker compose up -d --no-deps celery_beat
```

### 8.2 回滚流程
```bash
# 1. 查看历史镜像
docker images yourdockerhubuser/douyin_monitor

# 2. 回滚到上一版本
docker compose pull yourdockerhubuser/douyin_monitor:v1.2.2
docker compose up -d --no-deps monitor
# 同步回滚 Celery (镜像同源)
docker compose up -d --no-deps celery_worker celery_beat

# 3. 验证
curl -s https://wlkj-tech.cn/api/health | jq .
```

### 8.3 数据库/数据兼容性检查
- 发布前运行 `scripts/check_env.py` 确保配置兼容
- 如有 Schema 变更，提供迁移脚本并标记 `migration_required: true` 在 Release Note

---

## 9. 安全事件响应

### 9.1 密钥泄露
```bash
# 1. 立即轮换泄露的密钥
#   - 更新 .env 中对应变量
#   - 重启服务生效: docker compose restart monitor celery_worker celery_beat

# 2. 撤销泄露的 Token (如有上游管理控制台)

# 3. 审计日志确认是否被利用
grep "leaked_key" /var/log/douyin_monitor/*.log

# 4. 事后复盘记录到 Incident Report
```

### 9.2 疑似入侵
```bash
# 1. 隔离: 防火墙封禁可疑 IP
iptables -A INPUT -s <suspicious_ip> -j DROP

# 2. 保留现场: 复制日志、内存镜像
cp -r /var/log/douyin_monitor /evidence/
docker commit douyin_monitor forensic_$(date +%s)

# 3. 通报安全团队, 走应急响应流程
```

---

## 10. 联系人与升级路径

| 角色 | 姓名 | 电话/企业微信 | 责任范围 |
|------|------|--------------|---------|
| **主责运维** | 张三 | 138-xxxx-xxxx / @zhangsan | 日常巡检、发布、故障一线处理 |
| **备份运维** | 李四 | 139-xxxx-xxxx / @lisi | 主责不可用时接管 |
| **Tech Lead** | 王五 | 137-xxxx-xxxx / @wangwu | 架构决策、疑难故障、发布把关 |
| **安全负责人** | 赵六 | 136-xxxx-xxxx / @zhaoliu | 安全事件、密钥管理、合规 |
| **业务负责人** | 钱七 | 135-xxxx-xxxx / @qianqi | 业务影响评估、沟通协调 |

### 升级路径
```
L1 (运维) 15 分钟未解决 → L2 (Tech Lead) 30 分钟未解决 → L3 (架构师/VP) 1 小时未解决 → 启动重大事故流程
```

---

## 11. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2026-08-18 | 初始版本：服务拓扑、常用命令、扩容、备份恢复、证书轮换、故障决策树、监控告警、发布回滚、安全响应 | Auto |

---

> **使用提示**：
> 1. 本手册建议打印一份放在机房/运维工位，关键命令贴在显示器边
> 2. 每季度进行一次 **故障演练**，验证决策树有效性
> 3. 重大架构变更后 **必须同步更新** 本手册
> 4. 所有操作前先 **备份**、**快照**、**通知相关人员**