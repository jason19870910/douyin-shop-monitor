---
title: ADR-002: 采用 Celery + Redis 作为异步任务编排方案
version: 1.0.0
status: Accepted
last_updated: 2026-08-12
owner: Backend Lead
reviewers: [Tech Lead, 架构师, DevOps Lead]
approvers: [Tech Lead]
classification: Internal
doc_id: ADR-002
tags: [ADR, 后端, Celery, Redis, 异步任务, 架构决策]
related_docs: [DOC-TECH-001, DOC-OPS-001]
changelog: |
  v1.0.0 (2026-08-12): 初版创建 - Backend Lead
---

# ADR-002: 采用 Celery + Redis 作为异步任务编排方案

## 状态
Accepted

## 背景
项目需要处理以下异步场景：
- 定时任务：每日自动抓取抖店/抖音数据（Celery Beat）
- 长耗时操作：数据同步、报表生成、导出 CSV
- 重试机制：外部 API 调用失败自动重试
- 任务编排：多步骤流水线（抓取 -> 清洗 -> 存储 -> 告警检查）

原方案使用 Flask 内置的简单线程池，存在以下问题：
- 无持久化，重启丢失任务
- 无重试、死信队列
- 无法横向扩展 Worker
- 无监控和可视化

## 决策
采用 **Celery 5.x + Redis 7.x** 作为异步任务队列方案，包含：
- **Celery Beat**: 定时调度器（替代 crontab）
- **Celery Worker**: 4 个专用 Worker 服务
  - `worker_sync`: 数据同步任务（高优先级）
  - `worker_report`: 报表生成任务（低优先级）
  - `worker_alert`: 告警检查任务（高优先级）
  - `worker_default`: 通用任务
- **Redis**: 消息代理 + 结果后端

### 核心配置
```python
# celery_config.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_BEAT_SCHEDULE = {
    "daily-full-sync": {
        "task": "tasks.sync_all_data",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "sync"},
    },
    "hourly-incremental-sync": {
        "task": "tasks.sync_incremental",
        "schedule": crontab(minute=0),
        "options": {"queue": "sync"},
    },
}
```

## 备选方案
| 方案 | 优点 | 缺点 | 未选择原因 |
|------|------|------|------------|
| RQ (Redis Queue) | 简单轻量、Pythonic | 功能较弱、无 Beat、监控差 | 缺乏定时调度和优先级队列 |
| APScheduler | 内嵌调度、无需额外服务 | 单进程、无分布式、无重试 | 生产环境不够健壮 |
| Dramatiq | 性能好、Actor 模型 | 生态较小、无内置 Beat | 团队不熟悉，Celery 更成熟 |
| 自建 Go 任务系统 | 高性能、完全可控 | 开发维护成本极高 | 重复造轮子，ROI 低 |

## 后果
### 正面影响
- 任务持久化：Redis 存储，重启不丢失
- 自动重试：指数退避策略，配置 `autoretry_for=(Exception,)`
- 优先级队列：4 个队列隔离，关键任务不被阻塞
- 横向扩展：Worker 无状态，可随时增加实例
- 监控可视化：Flower 集成，实时查看任务状态
- 死信处理：失败任务进入 DLQ，支持人工重试

### 负面影响/风险
- 架构复杂度增加：新增 Redis、Celery 组件
- 运维成本：需监控 Redis 内存、Worker 存活、队列积压
- 结果后端压力：大量任务结果写入 Redis，需配置 TTL 清理
- 单点故障：Redis 单实例（后续可升级集群/哨兵）

### 需要的后续工作
- [x] 部署 Redis 7.x（配置 maxmemory、eviction policy）
- [x] 编写 4 类 Worker 启动脚本（Systemd 管理）
- [x] 集成 Flower 监控（端口 5555，内网访问）
- [x] 配置任务路由（task_routes 按队列分发）
- [x] 设置结果过期（CELERY_RESULT_EXPIRES=86400）
- [ ] 实现死信队列监控告警
- [ ] 压测验证 1000+ 并发任务处理能力

## 相关链接
- Celery 官方文档: https://docs.celeryq.dev/
- Redis 最佳实践: https://redis.io/docs/management/optimization/
- Flower 监控: https://flower.readthedocs.io/
EOF