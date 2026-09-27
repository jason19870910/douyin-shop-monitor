---
title: 部署架构设计文档
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: DevOps Lead
reviewers: [Tech Lead, 架构师, 运维工程师]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-TECH-006
tags: [架构, 部署, 设计文档, Docker, Systemd, Nginx, K8s]
related_docs: [DOC-TECH-001, DOC-OPS-001, DOC-OPS-002]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - DevOps Lead
---

# 部署架构设计文档

## 1. 概述
本文档描述抖音电商数据监控平台的部署架构，覆盖开发、测试、预发布、生产环境的部署方案、拓扑结构、发布流程、回滚策略及运维操作规范。

---

## 2. 部署拓扑

### 2.1 生产环境物理/逻辑拓扑
```
┌─────────────────────────────────────────────────────────────────────┐
│                        生产环境 VPC                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    负载均衡层 (SLB/云 LB)                       │
│  │  • HTTPS 终止  • WAF 防护  • 健康检查  • 会话保持               │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │                                      │
│        ┌──────────────────────┼──────────────────────┐             │
│        ▼                      ▼                      ▼             │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐   │
│  │  Nginx #1   │        │  Nginx #2   │        │  Nginx #N   │   │
│  │  (静态资源)  │        │  (静态资源)  │        │  (静态资源)  │   │
│  │  (反向代理)  │        │  (反向代理)  │        │  (反向代理)  │   │
│  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘   │
│         │                      │                      │            │
│         └──────────────────────┼──────────────────────┘            │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    应用服务层 (Auto Scaling Group)             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │   │
│  │  │ Flask API #1│  │ Flask API #2│  │ Flask API #N│           │   │
│  │  │ (Gunicorn)  │  │ (Gunicorn)  │  │ (Gunicorn)  │           │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │   │
│  │  │ Celery Beat │  │Celery Worker│  │Celery Worker│           │   │
│  │  │  (调度器)    │  │  (sync)     │  │  (report)   │           │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                │                                    │
│         ┌──────────────────────┼──────────────────────┐             │
│         ▼                      ▼                      ▼             │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐   │
│  │  MySQL 主库  │◀──────▶│  MySQL 从库  │        │  MySQL 从库  │   │
│  │  (读写)      │  同步  │  (读)        │        │  (读/备)     │   │
│  └─────────────┘        └─────────────┘        └─────────────┘   │
│         │                                             │            │
│         ▼                                             ▼            │
│  ┌─────────────┐                              ┌─────────────┐   │
│  │  Redis 集群  │◀────────────────────────────▶│  Redis 从节点 │   │
│  │  (主从/哨兵)  │      Sentinel 监控           │  (只读/备)    │   │
│  └─────────────┘                              └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 单机/小规模部署拓扑 (当前状态)
```
单台服务器 (122.51.208.138) - Docker Compose 编排
┌─────────────────────────────────────────────────────────────┐
│                    Systemd 管理                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Nginx    │ │ Frontend │ │ Backend  │ │ Celery   │       │
│  │ (80/443) │ │ (静态)   │ │ (5000)   │ │ Workers  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│        │         │          │            │                   │
│        ▼         ▼          ▼            ▼                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Docker Network (douyin-network)         │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │    │
│  │  │ MySQL   │ │ Redis   │ │ Nginx   │ │ 卷挂载   │   │    │
│  │  │ (3306)  │ │ (6379)  │ │ (80)    │ │ (日志/配置)│   │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 容器化规范

### 3.1 Docker 镜像规范
| 服务 | 基础镜像 | 构建策略 | 关键配置 |
|------|---------|---------|---------|
| Frontend | `node:20-alpine` (build) → `nginx:alpine` (runtime) | 多阶段构建 | 静态资源 gzip/brotli 预压缩、CSP Header |
| Backend | `python:3.11-slim` | 单阶段 + 依赖缓存 | Gunicorn 4 workers、非 root 用户、健康检查 |
| Celery Worker | `python:3.11-slim` | 同 Backend | 并发数配置、内存限制、优雅关闭 |
| Celery Beat | `python:3.11-slim` | 同 Backend | 单实例、持久化 schedule |
| Nginx | `nginx:alpine` | 单阶段 | 反向代理、限流、SSL 终止、缓存策略 |

### 3.2 Dockerfile 最佳实践
```dockerfile
# Backend 示例
FROM python:3.11-slim AS base
# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 非 root 用户
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app

# 依赖安装 (利用缓存层)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 代码复制
COPY --chown=app:app . .

# 运行时配置
USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", \
     "--worker-class", "gevent", "--timeout", "60", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "app:create_app()"]
```

### 3.3 镜像标签策略
| 环境 | 标签格式 | 示例 | 保留策略 |
|------|---------|------|---------|
| 开发 | `dev-{git-short-sha}` | `dev-a1b2c3d` | 保留最新 10 个 |
| 测试 | `test-{git-short-sha}` | `test-a1b2c3d` | 保留最新 20 个 |
| 预发布 | `rc-{version}-{git-short-sha}` | `rc-1.2.0-a1b2c3d` | 保留最新 30 个 |
| 生产 | `v{version}` / `latest` | `v1.2.0` / `latest` | 永久保留 |

---

## 4. 环境配置管理

### 4.1 环境变量分层
```bash
# .env.production (示例)
# === 应用基础 ===
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=${VAULT:secret/data/douyin#secret_key}

# === 数据库 ===
DATABASE_URL=mysql+pymysql://${VAULT:secret/data/douyin/db#username}:${VAULT:secret/data/douyin/db#password}@mysql:3306/douyin?charset=utf8mb4
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# === Redis ===
REDIS_URL=redis://:${VAULT:secret/data/douyin/redis#password}@redis:6379/0
REDIS_RESULT_URL=redis://:${VAULT:secret/data/douyin/redis#password}@redis:6379/1

# === Celery ===
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_RESULT_URL}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=Asia/Shanghai

# === 外部 API ===
FXG_BASE_URL=https://fxg.jinritemai.com
FXG_COOKIES=${VAULT:secret/data/douyin/fxg#cookies}
FXG_TOKEN=${VAULT:secret/data/douyin/fxg#token}
CREATOR_BASE_URL=https://creator.douyin.com
CREATOR_ACCESS_TOKEN=${VAULT:secret/data/douyin/creator#access_token}

# === 告警通知 ===
WECOM_WEBHOOK_URL=${VAULT:secret/data/douyin/alert#wecom_webhook}
ALERT_EMAIL_SMTP=${VAULT:secret/data/douyin/alert#email_smtp}
ALERT_SMS_API_KEY=${VAULT:secret/data/douyin/alert#sms_api_key}

# === 监控 ===
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
SENTRY_DSN=${VAULT:secret/data/douyin/sentry#dsn}
```

### 4.2 配置管理原则
- **敏感配置**：存储在 Vault/KMS，**严禁**写入代码仓库、镜像、ConfigMap
- **非敏感配置**：通过 ConfigMap/环境变量文件注入
- **环境隔离**：每环境独立 Vault 路径，严禁跨环境引用
- **变更审计**：所有配置变更走变更管理流程，留存审计日志

---

## 5. 发布流程

### 5.1 CI/CD 流水线
```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   代码提交   │──▶│   CI 构建    │──▶│   自动化测试  │──▶│  镜像构建推送 │
│  (Git Push) │   │  (Lint/Test)│   │  (单元/集成) │   │  (Registry)  │
└─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘
                                                              │
                    ┌─────────────────────────────────────────┘
                    ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  生产部署    │◀──│  手动确认    │◀──│  预发布部署   │◀──│  测试部署    │
│  (蓝绿/滚动)  │   │  (业务/运维) │   │  (自动/手动)  │   │  (自动)      │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

### 5.2 发布策略对比
| 策略 | 适用场景 | 零停机 | 回滚速度 | 资源成本 | 风险 |
|------|---------|--------|---------|---------|------|
| 蓝绿部署 | 核心服务、大版本 | ✅ | 极快 (切换流量) | 2x | 低 |
| 滚动更新 | 日常迭代、小版本 | ✅ | 中等 (逐个替换) | 1x | 中 |
| 金丝雀发布 | 高风险变更、新功能 | ✅ | 快 (流量切回) | 1.1x | 低 |
| 重建部署 | 开发/测试、无状态 | ❌ | 慢 | 1x | 高 |

### 5.3 生产发布标准流程 (滚动更新)
```bash
# 1. 预检查
./scripts/pre_deploy_check.sh v1.2.0
#   - 镜像存在性、签名验证
#   - 数据库迁移脚本语法检查
#   - 配置变更 Diff 确认
#   - 依赖服务健康状态

# 2. 数据库迁移 (如有)
./scripts/run_migration.sh v1.2.0
#   - 备份当前 Schema
#   - 执行迁移 (事务化、可回滚)
#   - 验证关键表结构

# 3. 滚动部署应用
docker-compose -f docker-compose.prod.yml up -d --scale backend=3 --no-deps backend
#   - 等待健康检查通过 (30s 超时)
#   - 逐个替换旧容器
#   - Nginx 上游自动感知 (docker-gen / consul-template)

# 4. 部署 Celery Workers
docker-compose up -d --no-deps celery_beat celery_worker_sync celery_worker_report

# 5. 部署后验证
./scripts/post_deploy_verify.sh v1.2.0
#   - API 冒烟测试 (健康检查、核心接口)
#   - 关键业务流程验证 (同步任务、告警)
#   - 监控大盘无异常 (错误率、延迟、队列积压)
#   - 日志错误率检查

# 6. 通知相关方
#   - 企业微信群通知
#   - 更新部署记录
```

---

## 6. 回滚策略

### 6.1 回滚触发条件
| 条件 | 判定标准 | 自动/手动 |
|------|---------|---------|
| 核心 API 错误率 | > 5% 持续 5 分钟 | 自动触发告警，人工确认回滚 |
| 关键业务流程失败 | 同步任务连续 3 次失败 | 人工触发 |
| 用户投诉激增 | 客服反馈异常量 > 阈值 | 人工触发 |
| 监控关键指标异常 | P99 延迟 > 3s、CPU > 90% 持续 10min | 自动告警，人工决策 |
| 安全事件 | 检测到攻击/泄露 | 立即手动触发 |

### 6.2 回滚操作
```bash
# 1. 应用层回滚 (镜像标签回退)
docker-compose -f docker-compose.prod.yml up -d --scale backend=3 \
    --no-deps backend:v1.1.0

# 2. 数据库回滚 (如有迁移)
./scripts/rollback_migration.sh v1.1.0
#   - 执行回滚脚本 (下线迁移的逆操作)
#   - 验证数据完整性

# 3. Celery Workers 回滚
docker-compose up -d --no-deps \
    celery_beat:v1.1.0 \
    celery_worker_sync:v1.1.0 \
    celery_worker_report:v1.1.0

# 4. 验证回滚结果
./scripts/post_rollback_verify.sh v1.1.0
```

### 6.3 回滚时间目标 (RTO/RPO)
| 层级 | RTO (恢复时间目标) | RPO (恢复点目标) |
|------|-------------------|-----------------|
| 应用层 | < 5 分钟 | 0 (无状态) |
| 数据库 | < 30 分钟 | < 1 分钟 (Binlog) |
| Redis | < 10 分钟 | < 1 秒 (AOF) |
| 全站灾难 | < 4 小时 | < 1 小时 (异地备份) |

---

## 7. 扩缩容策略

### 7.1 水平扩缩容 (HPA)
| 服务 | 指标 | 阈值 | 最小/最大实例 | 冷却时间 |
|------|------|------|-------------|---------|
| Flask API | CPU 使用率 | > 70% | 3 / 20 | 300s |
| Flask API | 请求延迟 P99 | > 1s | 3 / 20 | 300s |
| Celery Worker (sync) | 队列积压 | > 100 | 2 / 10 | 180s |
| Celery Worker (report) | 队列积压 | > 50 | 1 / 5 | 300s |
| Nginx | 连接数 | > 1000/实例 | 2 / 10 | 60s |

### 7.2 垂直扩缩容 (VPA)
| 资源 | 触发条件 | 操作 |
|------|---------|------|
| 内存 | 容器 OOM 或持续 > 85% | 重建容器调整 Limit |
| CPU | 持续 > 90% | 重建容器调整 Limit |
| 磁盘 | > 80% | 扩容 PVC / 清理日志 |

---

## 8. 监控与可观测性部署

### 8.1 监控栈部署
```
┌─────────────────────────────────────────────────────────────┐
│                    监控命名空间                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ Prometheus  │ │  Alertmanager│ │   Grafana   │            │
│  │  (TSDB/规则) │ │  (告警路由)   │ │  (仪表盘)    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Node Exp.  │ │  Cadvisor   │ │  Blackbox   │            │
│  │  (主机指标)  │ │  (容器指标)  │ │  (探测)      │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 关键监控大盘
| 大盘 | 核心指标 | 告警规则 |
|------|---------|---------|
| 系统概览 | CPU/内存/磁盘/网络、节点存活 | 资源 > 85% |
| 应用性能 | QPS/延迟 P50/P95/P99/错误率 | 错误率 > 1%、P99 > 1s |
| 业务指标 | 同步成功率/耗时、告警触发数、活跃用户 | 同步失败、告警风暴 |
| 数据库 | 连接数/慢查询/复制延迟/表大小 | 慢查询 > 10、延迟 > 10s |
| Redis | 内存/命中率/连接数/键过期 | 内存 > 85%、命中率 < 90% |
| Celery | 队列长度/任务耗时/成功率/Worker 存活 | 积压 > 阈值、Worker 离线 |

---

## 9. 备份与灾难恢复

### 9.1 备份策略
| 对象 | 方式 | 频率 | 保留 | 存储位置 | 加密 |
|------|------|------|------|---------|------|
| MySQL 全量 | XtraBackup / mysqldump | 每日 03:00 | 30 天 | 对象存储 (异地) | AES-256 |
| MySQL 增量 | Binlog 实时同步 | 实时 | 7 天 | 对象存储 | AES-256 |
| Redis | RDB + AOF | 每 1 小时 / 实时 | 7 天 | 对象存储 | AES-256 |
| 配置/代码 | Git + 镜像仓库 | 持续 | 永久 | GitLab / Harbor | - |
| 文件卷 | 卷快照 | 每日 | 30 天 | 云快照 | 云厂商加密 |

### 9.2 恢复演练
| 场景 | 频率 | 参与者 | 验收标准 |
|------|------|--------|---------|
| 单表误删恢复 | 月度 | DBA + 运维 | < 30 分钟，数据零丢失 |
| MySQL 主库故障切换 | 季度 | DBA + 运维 | < 5 分钟，RPO < 1 分钟 |
| Redis 主节点故障 | 季度 | 运维 | < 2 分钟，自动故障转移 |
| 全站灾难恢复 | 半年 | 全团队 | < 4 小时，RPO < 1 小时 |
| 勒索软件模拟 | 年度 | 安全 + 运维 + 管理层 | 离线备份可用、重建流程验证 |

---

## 10. 运维操作规范

### 10.1 常用操作命令
```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志 (最近 100 行，跟踪)
docker-compose logs -f --tail=100 backend

# 进入容器调试
docker-compose exec backend bash

# 执行数据库迁移
docker-compose exec backend flask db upgrade

# 触发手动同步
docker-compose exec backend python -c "from tasks import sync_all_data; sync_all_data.delay()"

# 查看 Celery 任务状态
docker-compose exec backend celery -A celery_app inspect active

# 重启单个服务
docker-compose restart backend

# 优雅停止 (发送 SIGTERM，等待 30s)
docker-compose stop -t 30 backend
```

### 10.2 变更管理流程
```
1. 提交变更单 (Jira/GitHub Issue)
   ├── 变更描述、影响范围、风险评估
   ├── 回滚方案、验证步骤
   └── 审批人：Tech Lead + 运维 Lead

2. 变更窗口
   ├── 标准变更：工作日 10:00-18:00
   ├── 紧急变更：随时，需事后补单
   └── 重大变更：周末维护窗口

3. 执行与验证
   ├── 按操作手册执行
   ├── 关键步骤截图/录屏留存
   └── 验收签字

4. 变更复盘
   ├── 成功：归档
   ├── 失败/部分成功：根因分析、改进措施
```

---

## 11. 容量规划

### 11.1 当前资源基线 (单机)
| 资源 | 规格 | 当前使用 | 预留 | 扩容触发点 |
|------|------|---------|------|-----------|
| CPU | 8 vCPU | ~40% | 50% | > 70% 持续 15min |
| 内存 | 16 GB | ~60% | 30% | > 80% 持续 15min |
| 磁盘 | 200 GB SSD | ~45% | 30% | > 75% |
| MySQL | 50 GB | ~20 GB | 2x | > 70% |
| Redis | 4 GB | ~1.5 GB | 2x | > 75% |

### 11.2 扩容路线图
| 阶段 | 用户量/数据量 | 架构调整 | 预估时间 |
|------|-------------|---------|---------|
| 当前 | 10 店铺、日单 1 万 | 单机 Docker Compose | - |
| 阶段 1 | 50 店铺、日单 10 万 | 读写分离、Redis 哨兵、多节点 API | 3 个月 |
| 阶段 2 | 200 店铺、日单 50 万 | K8s 编排、MySQL 分库分表、Redis Cluster | 9 个月 |
| 阶段 3 | 1000+ 店铺、日单 500 万 | 多活架构、异地多活、服务网格 | 18 个月 |

---

## 12. 附录：环境清单

### 12.1 生产环境服务清单
| 服务 | 实例数 | 规格 | 端口 | 健康检查 | 备注 |
|------|-------|------|------|---------|------|
| Nginx | 2 | 2C4G | 80/443 | `/health` | SLB 后端 |
| Frontend | 2 | 1C2G | 80 (内部) | 静态资源 | Nginx 代理 |
| Backend API | 3 | 2C4G | 5000 | `/api/health` | Gunicorn 4W |
| Celery Beat | 1 | 1C2G | - | 进程存活 | 单实例 |
| Celery Worker (sync) | 2 | 2C4G | - | 队列消费 | 专用队列 |
| Celery Worker (report) | 1 | 2C4G | - | 队列消费 | 低优先级 |
| Celery Worker (alert) | 1 | 1C2G | - | 队列消费 | 高优先级 |
| MySQL | 1主2从 | 4C16G/500GB | 3306 | `SELECT 1` | GTID 复制 |
| Redis | 3主3从 | 4C8G/10GB | 6379 | `PING` | Sentinel 模式 |
| Prometheus | 1 | 2C8G/100GB | 9090 | `/-/healthy` | 单实例 |
| Grafana | 1 | 1C2G | 3000 | `/api/health` | 单实例 |
| Alertmanager | 1 | 1C1G | 9093 | `/-/healthy` | 单实例 |

### 12.2 域名与证书
| 域名 | 用途 | 证书类型 | 续期方式 |
|------|------|---------|---------|
| wlkj-tech.cn | 生产前端入口 | Let's Encrypt (通配符) | Certbot 自动续期 |
| api.wlkj-tech.cn | 生产 API 入口 | Let's Encrypt (通配符) | Certbot 自动续期 |
| monitor.wlkj-tech.cn | Grafana 监控 | Let's Encrypt | Certbot 自动续期 |
| *.test.douyin.internal | 测试环境 | 自签 CA | 手动管理 |
EOF