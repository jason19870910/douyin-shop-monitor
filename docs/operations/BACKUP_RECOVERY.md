---
title: 备份恢复策略
version: 1.1.0
status: Published
last_updated: 2026-10-16
owner: DevOps Lead
reviewers: [架构师, 运维工程师]
approvers: [Tech Lead]
classification: Confidential
doc_id: DOC-OPS-004
tags: [运维, 备份, 恢复, 灾难恢复, RPO, RTO]
related_docs: [DOC-OPS-001, DOC-OPS-003, DOC-RISK-003]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - DevOps Lead
  v1.1.0 (2026-10-16): 移除 MySQL 相关内容，统一为 Redis/AOF 架构描述 - DevOps Lead
---

# 备份恢复策略

## 1. 概述
本文档定义抖音电商数据监控平台的数据备份策略、恢复流程、RPO/RTO 目标及演练要求，确保数据安全性和业务连续性。

---

## 2. 备份策略矩阵

| 数据资产 | 备份方式 | 频率 | 保留周期 | 存储位置 | 加密 | RPO | RTO | 验证方式 |
|---------|---------|------|---------|---------|------|-----|-----|---------|
| **Redis 核心数据 (业务/缓存)** | RDB 快照 (BGSAVE) + AOF 增量 | 全量：每日 03:00<br>增量：AOF 实时 fsync | 全量：30 天<br>AOF：7 天 | 对象存储 (同城+异地双份) | AES-256 (传输+存储) | < 1 秒 | < 10 分钟 | 月度恢复演练 |
| **应用配置/密钥 (config/.env)** | 文件加密备份 + Git | 变更触发 + 每日 | 90 天 | 对象存储 / GitLab | AES-256 / Git 签名 | 0 | < 5 分钟 | 变更后即时验证 |
| **源码/Docker 镜像** | Git + Registry 复制 | 源码：提交即同步<br>镜像：推送即同步 | 永久 (语义化版本) | GitLab / Harbor (主备) | Git 签名 / 镜像签名 | 0 | < 5 分钟 | 部署时自动验证 |
| **Nginx/系统配置** | Git + Etckeeper | 变更触发 | 永久 | GitLab | Git 签名 | 0 | < 10 分钟 | 变更后即时验证 |
| **监控数据** | 压缩归档 | 每日 | 30 天 | 对象存储 | 无 (非敏感) | 24 小时 | < 1 小时 | 按需恢复验证 |
| **日志数据** | 冷热分离 + 压缩 | 热：实时流式 (Loki)<br>冷：每日打包 | 热：30 天<br>冷：1 年 | Loki / 对象存储 | 无 | 1 小时 | < 30 分钟 | 查询验证 |

---

## 3. Redis 备份详细设计

### 3.1 备份架构
```
┌─────────────────────────────────────────────────────────────────┐
│                      Redis 备份架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  douyin_redis ──▶ BGSAVE (RDB 快照) ───────▶ 对象存储            │
│      │                │                              │            │
│      │                ▼                              ▼            │
│      │         本地暂存 (redis_data 卷)          同城存储桶         │
│      │                │                              │            │
│      │                ▼                              ▼            │
│      └────────▶ AOF 拷贝 (appendfsync=everysec) ▶ 异地存储桶      │
│                                                          (跨区复制) │
│                                                                   │
│  调度器: Cron + 备份脚本 (幂等、可重入、进度上报)                 │
│  监控: 备份耗时/大小/成功率 → Prometheus → 告警                  │
│  校验: 定期随机抽样恢复到测试容器，redis-check-rdb 校验          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 备份脚本关键参数
```bash
# redis_backup.sh - 每日 03:00 执行 (app 容器内 Cron 调度)
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backup/redis/$(date +%Y%m%d_%H%M%S)"
RDB_BUCKET="s3://douyin-backup-prod/redis/rdb/"
AOF_BUCKET="s3://douyin-backup-prod/redis/aof/"
ENCRYPT_KEY_ID="alias/douyin-backup-key"

# 1. 触发 BGSAVE (非阻塞)
docker exec douyin_redis redis-cli BGSAVE

# 2. 等待 RDB 落盘完成 (轮询 LASTSAVE)
LAST_SAVE=$(docker exec douyin_redis redis-cli LASTSAVE)
while true; do
    sleep 5
    NEW_SAVE=$(docker exec douyin_redis redis-cli LASTSAVE)
    [ "${NEW_SAVE}" -gt "${LAST_SAVE}" ] && break
done

# 3. 拷贝 RDB 上传 (也可用 docker exec douyin_redis redis-cli --rdb /tmp/dump.rdb 直接拉取快照)
mkdir -p "${BACKUP_DIR}"
docker cp douyin_redis:/data/dump.rdb "${BACKUP_DIR}/dump.rdb"
gzip -c "${BACKUP_DIR}/dump.rdb" | \
    aws s3 cp - "${RDB_BUCKET}dump_$(date +%Y%m%d_%H%M%S).rdb.gz" \
        --sse aws:kms --sse-kms-key-id "${ENCRYPT_KEY_ID}" \
        --storage-class STANDARD_IA

# 4. 拷贝 AOF 文件上传 (压缩为 tar.gz)
docker cp douyin_redis:/data/appendonlydir "${BACKUP_DIR}/appendonlydir"
tar -czf "${BACKUP_DIR}/aof_$(date +%Y%m%d_%H%M%S).tar.gz" -C "${BACKUP_DIR}" appendonlydir
aws s3 cp "${BACKUP_DIR}/aof_$(date +%Y%m%d_%H%M%S).tar.gz" "${AOF_BUCKET}" \
    --sse aws:kms --sse-kms-key-id "${ENCRYPT_KEY_ID}"

# 5. 上传成功后清理本地 (保留 48 小时)
find /backup/redis -type f -mmin +2880 -delete
```

### 3.3 增量备份 (AOF 实时)
redis 服务以 `--appendonly yes` 启动 (appendfsync 默认 everysec)，写操作实时持久化到 `redis_data` 卷的 `/data/appendonlydir`，构成秒级增量能力：
```bash
# 确认 AOF 开启及 fsync 策略
docker exec douyin_redis redis-cli CONFIG GET appendonly
docker exec douyin_redis redis-cli CONFIG GET appendfsync

# 定期拷贝 AOF 文件 (与 3.2 RDB 备份同脚本调度，可按小时执行)
docker cp douyin_redis:/data/appendonlydir "/backup/redis/aof_$(date +%Y%m%d_%H%M%S)"
```

### 3.4 恢复流程
```bash
# 恢复到指定备份点
# 1. 下载最近的 RDB 备份并校验
aws s3 cp s3://douyin-backup-prod/redis/rdb/dump_20261016_030000.rdb.gz /tmp/
gunzip -c /tmp/dump_20261016_030000.rdb.gz > /tmp/dump.rdb
redis-check-rdb /tmp/dump.rdb

# 2. 停止写入 (维护模式: 暂停客户端，避免恢复期数据变更)
docker exec douyin_redis redis-cli CLIENT PAUSE ALL 300000

# 3. RDB 全量恢复: 灌入 dump.rdb 并重启容器加载
docker exec douyin_redis redis-cli CONFIG SET appendonly no
docker stop douyin_redis
docker cp /tmp/dump.rdb douyin_redis:/data/dump.rdb
docker start douyin_redis
docker exec douyin_redis redis-cli CONFIG SET appendonly yes

# 4. AOF 增量恢复 (可选): 拷贝 AOF 目录，重启由 redis-server --appendonly yes 重放
tar -xzf /tmp/aof_20261016_120000.tar.gz -C /tmp/aof_restore
docker cp /tmp/aof_restore/appendonlydir douyin_redis:/data/appendonlydir
docker restart douyin_redis

# 5. 校验数据完整性并生成新基线
docker exec douyin_redis redis-cli BGSAVE
docker exec douyin_redis redis-cli INFO keyspace
docker exec douyin_redis redis-cli DBSIZE
```

---

## 4. 灾难恢复演练

### 4.1 演练计划
| 演练场景 | 频率 | 参与角色 | 预计耗时 | 成功标准 |
|---------|------|---------|---------|---------|
| 单 Key 误删恢复 | 月度 | 运维 + 业务 | < 30 分钟 | 数据零丢失、应用正常访问 |
| Redis 数据恢复 | 季度 | 运维 + 业务 | < 10 分钟 | RDB/AOF 灌入成功、应用自动重连 |
| Redis 主节点故障 | 季度 | 运维 | < 2 分钟 | Sentinel 自动切主、缓存命中率恢复 |
| 全量备份恢复到测试环境 | 月度 | 运维 | < 2 小时 | Checksum 校验通过、应用冒烟测试通过 |
| 全站灾难恢复 (异地) | 半年 | 全团队 | < 4 小时 | 核心业务可用、RPO < 1 小时 |
| 勒索软件模拟恢复 | 年度 | 安全 + 运维 + 管理层 | < 8 小时 | 离线备份可用、重建流程验证 |

### 4.2 演练记录模板
```markdown
# 恢复演练记录 - YYYYMMDD

## 1. 基本信息
- 演练编号: DRIL-YYYYMMDD-XXX
- 演练场景: Redis 数据恢复
- 执行时间: YYYY-MM-DD HH:MM - HH:MM
- 参与人员: 王五 (运维)、李四 (运维)

## 2. 执行步骤与耗时
| 步骤 | 操作 | 开始时间 | 结束时间 | 耗时 | 结果 |
|------|------|----------|----------|------|------|
| 1 | 模拟数据损坏 (停止 redis 容器) | 10:00:00 | 10:00:05 | 5s | 成功 |
| 2 | 检测故障并告警 | 10:00:05 | 10:00:15 | 10s | 自动检测 |
| 3 | 恢复 RDB 备份并重启容器 | 10:00:15 | 10:00:35 | 20s | 成功 |
| 4 | 应用重连验证 | 10:00:35 | 10:01:00 | 25s | 成功 |
| 5 | 业务验证 (下单/查询) | 10:01:00 | 10:05:00 | 4m | 成功 |

## 3. 实际 RTO/RPO
- RTO 实际: 1 分钟 5 秒 (目标 < 5 分钟) ✅
- RPO 实际: 0 秒 (AOF 重放) ✅

## 4. 发现问题与改进
| 问题 | 影响 | 改进措施 | 负责人 | 截止日期 |
|------|------|----------|--------|----------|
| 恢复脚本拷贝 RDB 耗时 10s | 延长 RTO | 优化脚本并行化 | 王五 | 2026-10-15 |
| 监控大盘未自动刷新 | 观测盲区 | 增加 Redis 重启事件触发刷新 | 李四 | 2026-10-10 |

## 5. 结论
- 演练结果: ✅ 通过
- 实际 RTO: 1分05秒 < 5分钟目标
- 实际 RPO: 0秒 < 1分钟目标
- 签字确认: 王五 (运维)、李四 (运维)
```

---

## 6. 异地多活备份架构 (规划)

### 6.1 目标架构
```
┌─────────────────────────────────────────────────────────────────────┐
│                     异地多活备份架构 (规划中)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    ┌─────────────┐           专线/云联网           ┌─────────────┐   │
│    │   主站       │ ◀──────────── 实时同步 ──────────▶ │   备站     │   │
│    │  (北京/华北)  │       Redis 异步复制            │  (上海/华东) │   │
│    │              │           双向复制                │             │   │
│    └──────┬────────┘                                    └──────┬──────┘   │
│           │                                                    │          │
│           ▼                                                    ▼          │
│    ┌─────────────────────┐                            ┌─────────────────┐│
│    │  SLB (主入口)        │                            │  SLB (备入口)   ││
│    │  - 健康检查           │                            │  - 同步配置     ││
│    │  - 故障自动切换        │                            │  - 就绪待命     ││
│    └─────────────────────┘                            └─────────────────┘│
│                                                                      │
│  切换策略: DNS 级故障转移 (TTL 60s) + 健康检查 + 手动确认            │
│  RPO 目标: < 1 分钟 (异步复制) / RTO 目标: < 5 分钟 (DNS 切换)        │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 实施路线图
| 阶段 | 目标 | 关键里程碑 | 预计时间 |
|------|------|-----------|---------|
| Phase 1 | 备份异地化 | 对象存储跨区域复制、AOF 实时同步 | 1 个月 |
| Phase 2 | 备站就绪 | 备站 Redis 部署、单向同步验证 | 2 个月 |
| Phase 3 | 双向同步 | 双主复制、冲突解决、数据一致性校验 | 3 个月 |
| Phase 4 | 自动故障转移 | DNS 健康检查、切换演练、业务验证 | 6 个月 |

---

## 7. 备份监控与告警

### 7.1 关键监控指标
| 指标 | 数据源 | 正常范围 | 告警阈值 | 告警级别 |
|------|-------|---------|---------|---------|
| 全量备份成功率 | 备份脚本上报 | 100% | < 100% | P1 |
| 全量备份耗时 | 备份脚本上报 | < 30 分钟 | > 60 分钟 | P2 |
| 备份文件大小 | S3 API | 稳定增长 | 突变 > 50% | P2 |
| 增量备份延迟 | AOF 拷贝进度 | < 1 分钟 | > 5 分钟 | P1 |
| 备份文件完整性 | 校验任务 | 通过 | 失败 | P0 |
| 恢复演练通过率 | 手动记录 | 100% | < 100% | P1 |
| 对象存储可用容量 | 云监控 | > 20% | < 10% | P2 |

### 7.2 告警通知
```yaml
# Alertmanager 路由示例
route:
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'wecom-backup'
  routes:
  - match:
      severity: 'critical'
    receiver: 'wecom-backup-critical'
    continue: true
  - match:
      alertname: 'BackupFailed'
    receiver: 'wecom-backup-pagerduty'
```

---

## 8. 合规与审计

### 8.1 合规要求
- **数据安全法**: 重要数据备份加密、异地存储、访问控制
- **ISO 27001 A.12.3**: 备份策略、备份测试、备份保护
- **等保 2.0 三级**: 备份存储介质管理、备份恢复测试记录
- **行业监管**: 金融/电商数据保留年限合规

### 8.2 审计清单
| 审计项 | 频率 | 证据材料 |
|-------|------|---------|
| 备份策略文档有效性 | 年度 | 本文档版本记录 |
| 备份执行日志完整性 | 月度 | 备份脚本日志、S3 访问日志 |
| 恢复演练记录 | 每次演练后 | 演练记录文档、签字确认 |
| 备份加密合规性 | 季度 | KMS 密钥策略、加密算法确认 |
| 异地备份可用性 | 半年 | 跨区域复制状态、恢复演练报告 |
| 权限最小化 | 季度 | 备份账号权限审计、Vault 访问日志 |

---

## 9. 附录

### 9.1 备份账号权限最小化
```bash
# Redis 备份专用账号 (ACL) - 仅授予备份所需命令
redis-cli ACL SETUSER backup_user on >complex_password ~* \
  +bgsave +lastsave +config|get +info +client|list +memory +keyspace
```

### 9.2 对象存储生命周期策略
```json
{
  "Rules": [
    {
      "ID": "redis-rdb-full-lifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "redis/rdb/"},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"},
        {"Days": 365, "StorageClass": "DEEP_ARCHIVE"}
      ],
      "Expiration": {"Days": 2555}
    },
    {
      "ID": "redis-aof-lifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "redis/aof/"},
      "Expiration": {"Days": 7}
    },
    {
      "ID": "redis-rdb-lifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "redis/"},
      "Transitions": [
        {"Days": 7, "StorageClass": "STANDARD_IA"},
        {"Days": 30, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 90}
    }
  ]
}
```

### 9.3 紧急恢复联系单
| 场景 | 联系人 | 电话 | 企业微信 | 备注 |
|------|--------|------|---------|------|
| Redis 恢复 | 运维 王五 | 137-xxxx-xxxx | @王五 | 运维主力 |
| Redis 恢复备选 | 运维 赵六 | 139-xxxx-xxxx | @赵六 | 备选运维 |
| 对象存储/权限 | 云平台支持 | 400-xxx-xxxx | - | 提交 P0 工单 |
| 网络/专线 | 网络团队 | 136-xxxx-xxxx | @网络组长 | 专线故障联系 |
| 管理层升级 | CTO | 135-xxxx-xxxx | @CTO | 重大灾难决策 |