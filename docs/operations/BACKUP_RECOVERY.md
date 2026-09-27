---
title: 备份恢复策略
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: DevOps Lead
reviewers: [DBA, 架构师, 运维工程师]
approvers: [Tech Lead]
classification: Confidential
doc_id: DOC-OPS-004
tags: [运维, 备份, 恢复, 灾难恢复, RPO, RTO]
related_docs: [DOC-OPS-001, DOC-OPS-003, DOC-RISK-003]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - DevOps Lead
---

# 备份恢复策略

## 1. 概述
本文档定义抖音电商数据监控平台的数据备份策略、恢复流程、RPO/RTO 目标及演练要求，确保数据安全性和业务连续性。

---

## 2. 备份策略矩阵

| 数据资产 | 备份方式 | 频率 | 保留周期 | 存储位置 | 加密 | RPO | RTO | 验证方式 |
|---------|---------|------|---------|---------|------|-----|-----|---------|
| **MySQL 核心业务数据** | 物理全量 (XtraBackup) + Binlog 增量 | 全量：每日 03:00<br>增量：实时流式 | 全量：30 天<br>增量：7 天 | 对象存储 (同城+异地双份) | AES-256 (传输+存储) | < 1 分钟 | < 30 分钟 | 月度恢复演练 |
| **MySQL 配置/权限/Schema** | 逻辑导出 | 每日 03:30 | 90 天 | 对象存储 | AES-256 | 24 小时 | < 1 小时 | 季度校验 |
| **Redis 缓存数据** | RDB 快照 + AOF | RDB：每 1 小时<br>AOF：每秒 fsync | 7 天 | 对象存储 | AES-256 | < 1 秒 | < 10 分钟 | 月度恢复演练 |
| **应用配置/密钥** | Vault 备份 + Git | 变更触发 + 每日 | 永久 (Git) / 90 天 (Vault) | Vault 存储 / GitLab | Vault 加密 / Git 签名 | 0 | < 5 分钟 | 变更后即时验证 |
| **Docker 镜像** | Registry 复制 | 推送即同步 | 永久 (语义化版本) | Harbor (主备) | 镜像签名 | 0 | < 5 分钟 | 部署时自动验证 |
| **Nginx/系统配置** | Git + Etckeeper | 变更触发 | 永久 | GitLab | Git 签名 | 0 | < 10 分钟 | 变更后即时验证 |
| **监控数据** | 压缩归档 | 每日 | 30 天 | 对象存储 | 无 (非敏感) | 24 小时 | < 1 小时 | 按需恢复验证 |
| **日志数据** | 冷热分离 + 压缩 | 热：实时流式 (Loki)<br>冷：每日打包 | 热：30 天<br>冷：1 年 | Loki / 对象存储 | 无 | 1 小时 | < 30 分钟 | 查询验证 |

---

## 3. MySQL 备份详细设计

### 3.1 备份架构
```
┌─────────────────────────────────────────────────────────────────┐
│                      MySQL 备份架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  MySQL 主库 ──▶ XtraBackup (物理流式备份) ──▶ 对象存储           │
│      │                │                              │            │
│      │                ▼                              ▼            │
│      │         本地暂存 (NVMe SSD)              同城存储桶         │
│      │                │                              │            │
│      │                ▼                              ▼            │
│      └────────▶ Binlog (实时同步) ──────────▶ 异地存储桶          │
│                   (GTID 模式)              (跨区域复制)           │
│                                                                   │
│  调度器: Cron + 备份脚本 (幂等、可重入、进度上报)                 │
│  监控: 备份耗时/大小/成功率 → Prometheus → 告警                  │
│  校验: 定期随机抽样恢复到测试库，Checksum 校验                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 备份脚本关键参数
```bash
# xtrabackup_full.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backup/mysql/full/$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="${BACKUP_DIR}"
S3_BUCKET="s3://douyin-backup-prod/mysql/full/"
ENCRYPT_KEY_ID="alias/douyin-backup-key"

# 并行备份，压缩，加密，上报进度
xtrabackup --backup \
    --target-dir="${TARGET_DIR}" \
    --parallel=4 \
    --compress \
    --compress-threads=2 \
    --encrypt=AES256 \
    --encrypt-key-file=/etc/backup/encrypt_key \
    --slave-info \
    --safe-slave-backup \
    --history-name="full_$(date +%Y%m%d_%H%M%S)" \
    --incremental-history-name="incr_$(date +%Y%m%d)" \
    --stream=xbstream 2>"${BACKUP_DIR}/backup.log" | \
    gzip -c | \
    aws s3 cp - "${S3_BUCKET}$(basename ${BACKUP_DIR}).xbstream.gz" \
        --sse aws:kms --sse-kms-key-id "${ENCRYPT_KEY_ID}" \
        --storage-class STANDARD_IA

# 上传成功后清理本地 (保留最近 2 份)
find /backup/mysql/full -type f -mtime +2 -delete
```

### 3.3 增量备份 (Binlog 实时)
```bash
# 使用 mysqlbinlog 实时流式传输到对象存储
mysqlbinlog --read-from-remote-server \
    --host=mysql-master \
    --user=backup_user \
    --password="${MYSQL_BACKUP_PASSWORD}" \
    --raw \
    --stop-never \
    --result-file="/backup/mysql/binlog/" \
    --binlog-format=ROW \
    --gtid-mode=ON \
    2>>/var/log/mysqlbinlog.log &
```

### 3.4 恢复流程
```bash
# 恢复到指定时间点 (PITR)
# 1. 下载最近的全量备份
aws s3 cp s3://douyin-backup-prod/mysql/full/full_20260925_030000.xbstream.gz /tmp/

# 2. 解压并准备
mkdir -p /restore/mysql
xbstream -x -C /restore/mysql < full_20260925_030000.xbstream
xtrabackup --decompress --target-dir=/restore/mysql
xtrabackup --prepare --target-dir=/restore/mysql --apply-log-only

# 3. 应用增量备份 (按时间顺序)
for inc in incr_20260925_040000 incr_20260925_080000 ...; do
    xbstream -x -C /restore/mysql < ${inc}.xbstream
    xtrabackup --prepare --target-dir=/restore/mysql --incremental-dir=/restore/mysql/${inc}
done

# 4. 应用 Binlog 到目标时间点
mysqlbinlog --start-datetime="2026-09-25 03:00:00" \
    --stop-datetime="2026-09-26 10:30:00" \
    /backup/mysql/binlog/mysql-bin.000123 | mysql -u root -p

# 5. 校验数据完整性
pt-table-checksum --databases douyin --chunk-size=10000
pt-table-sync --print --databases douyin h=localhost
```

---

## 4. Redis 备份详细设计

### 4.1 备份策略
```bash
# redis_backup.sh - 每小时执行
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backup/redis/$(date +%Y%m%d_%H%M%S)"
S3_BUCKET="s3://douyin-backup-prod/redis/"

# 触发 BGSAVE (非阻塞)
redis-cli -h redis-master -a "${REDIS_PASSWORD}" BGSAVE

# 等待完成 (轮询 LASTSAVE)
LAST_SAVE=$(redis-cli -h redis-master -a "${REDIS_PASSWORD}" LASTSAVE)
while true; do
    sleep 5
    NEW_SAVE=$(redis-cli -h redis-master -a "${REDIS_PASSWORD}" LASTSAVE)
    [ "${NEW_SAVE}" -gt "${LAST_SAVE}" ] && break
done

# 复制 RDB 文件并上传
cp /data/redis/dump.rdb "${BACKUP_DIR}/dump.rdb"
gzip -c "${BACKUP_DIR}/dump.rdb" | \
    aws s3 cp - "${S3_BUCKET}dump_$(date +%Y%m%d_%H%M%S).rdb.gz" \
        --sse aws:kms --sse-kms-key-id alias/douyin-backup-key

# 清理本地旧备份 (保留 48 小时)
find /backup/redis -type f -mmin +2880 -delete
```

### 4.2 Redis 恢复
```bash
# 1. 停止写入 (维护模式)
redis-cli -h redis-master -a "${REDIS_PASSWORD}" CONFIG SET requirepass ""
redis-cli -h redis-master -a "${REDIS_PASSWORD}" CLIENT PAUSE ALL 300000

# 2. 下载并恢复 RDB
aws s3 cp s3://douyin-backup-prod/redis/dump_20260926_100000.rdb.gz /tmp/
gzip -d -c /tmp/dump_20260926_100000.rdb.gz > /data/redis/dump.rdb

# 3. 重启 Redis 加载 RDB
systemctl restart redis

# 4. 验证数据
redis-cli -h redis-master -a "${REDIS_PASSWORD}" INFO keyspace
redis-cli -h redis-master -a "${REDIS_PASSWORD}" DBSIZE

# 5. 重建从节点 (如集群模式)
redis-cli -h redis-replica -a "${REDIS_PASSWORD}" REPLICAOF redis-master 6379
```

---

## 5. 灾难恢复演练

### 5.1 演练计划
| 演练场景 | 频率 | 参与角色 | 预计耗时 | 成功标准 |
|---------|------|---------|---------|---------|
| 单表误删恢复 | 月度 | DBA + 运维 | < 30 分钟 | 数据零丢失、应用正常访问 |
| MySQL 主库故障切换 | 季度 | DBA + 运维 + 业务 | < 5 分钟 | VIP 切换成功、应用自动重连 |
| Redis 主节点故障 | 季度 | 运维 | < 2 分钟 | Sentinel 自动切主、缓存命中率恢复 |
| 全量备份恢复到测试环境 | 月度 | DBA | < 2 小时 | Checksum 校验通过、应用冒烟测试通过 |
| 全站灾难恢复 (异地) | 半年 | 全团队 | < 4 小时 | 核心业务可用、RPO < 1 小时 |
| 勒索软件模拟恢复 | 年度 | 安全 + 运维 + 管理层 | < 8 小时 | 离线备份可用、重建流程验证 |

### 5.2 演练记录模板
```markdown
# 恢复演练记录 - YYYYMMDD

## 1. 基本信息
- 演练编号: DRIL-YYYYMMDD-XXX
- 演练场景: MySQL 主库故障切换
- 执行时间: YYYY-MM-DD HH:MM - HH:MM
- 参与人员: 张三 (DBA)、李四 (运维)、王五 (业务)

## 2. 执行步骤与耗时
| 步骤 | 操作 | 开始时间 | 结束时间 | 耗时 | 结果 |
|------|------|----------|----------|------|------|
| 1 | 模拟主库宕机 (kill -9) | 10:00:00 | 10:00:05 | 5s | 成功 |
| 2 | Sentinel 检测故障 | 10:00:05 | 10:00:15 | 10s | 自动检测 |
| 3 | 自动故障转移 | 10:00:15 | 10:00:35 | 20s | 成功 |
| 4 | 应用重连验证 | 10:00:35 | 10:01:00 | 25s | 成功 |
| 5 | 业务验证 (下单/查询) | 10:01:00 | 10:05:00 | 4m | 成功 |

## 3. 实际 RTO/RPO
- RTO 实际: 1 分钟 5 秒 (目标 < 5 分钟) ✅
- RPO 实际: 0 秒 (GTID 同步) ✅

## 4. 发现问题与改进
| 问题 | 影响 | 改进措施 | 负责人 | 截止日期 |
|------|------|----------|--------|----------|
| VIP 切换脚本耗时 10s | 延长 RTO | 优化脚本并行化 | 张三 | 2026-10-15 |
| 监控大盘未自动切换 | 观测盲区 | 增加 VIP 变更事件触发刷新 | 李四 | 2026-10-10 |

## 5. 结论
- 演练结果: ✅ 通过
- 实际 RTO: 1分05秒 < 5分钟目标
- 实际 RPO: 0秒 < 1分钟目标
- 签字确认: 张三 (DBA)、李四 (运维)
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
│    │  (北京/华北)  │   MySQL GTID + Redis Cluster    │  (上海/华东) │   │
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
| Phase 1 | 备份异地化 | 对象存储跨区域复制、Binlog 实时同步 | 1 个月 |
| Phase 2 | 备站就绪 | 备站 MySQL/Redis 部署、单向同步验证 | 2 个月 |
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
| 增量备份延迟 | Binlog 同步进度 | < 1 分钟 | > 5 分钟 | P1 |
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
```sql
-- MySQL 备份专用账号
CREATE USER 'backup_user'@'%' IDENTIFIED BY 'complex_password';
GRANT SELECT, RELOAD, SHOW DATABASES, LOCK TABLES, REPLICATION CLIENT, PROCESS
ON *.* TO 'backup_user'@'%';
FLUSH PRIVILEGES;

-- Redis 备份专用账号 (ACL)
ACL SETUSER backup_user on >complex_password ~* +bgsave +lastsave +config|get|set +info +client|list +memory +keyspace
```

### 9.2 对象存储生命周期策略
```json
{
  "Rules": [
    {
      "ID": "mysql-full-lifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "mysql/full/"},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"},
        {"Days": 365, "StorageClass": "DEEP_ARCHIVE"}
      ],
      "Expiration": {"Days": 2555}
    },
    {
      "ID": "mysql-binlog-lifecycle",
      "Status": "Enabled",
      "Filter": {"Prefix": "mysql/binlog/"},
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
| MySQL 恢复 | DBA 张三 | 138-xxxx-xxxx | @张三 | 主 DBA |
| MySQL 恢复备选 | DBA 李四 | 139-xxxx-xxxx | @李四 | 备选 DBA |
| Redis 恢复 | 运维 王五 | 137-xxxx-xxxx | @王五 | 运维主力 |
| 对象存储/权限 | 云平台支持 | 400-xxx-xxxx | - | 提交 P0 工单 |
| 网络/专线 | 网络团队 | 136-xxxx-xxxx | @网络组长 | 专线故障联系 |
| 管理层升级 | CTO | 135-xxxx-xxxx | @CTO | 重大灾难决策 |
EOF