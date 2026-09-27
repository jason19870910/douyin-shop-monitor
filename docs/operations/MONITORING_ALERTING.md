---
title: 监控告警规范
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: DevOps Lead
reviewers: [SRE Lead, Backend Lead, 架构师]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-OPS-005
tags: [运维, 监控, 告警, Prometheus, Grafana, SRE, 可观测性]
related_docs: [DOC-OPS-001, DOC-OPS-003, DOC-TECH-006]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - DevOps Lead
---

# 监控告警规范

## 1. 概述
本文档定义抖音电商数据监控平台的监控体系、指标体系、告警规则、大盘设计及运维操作规范，遵循 **USE/RED/四大黄金信号** 方法论，实现全栈可观测。

---

## 2. 监控架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        监控架构 (Prometheus 生态)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │  数据采集层    │   │  存储/查询层   │   │  告警/通知层   │   │  可视化层    │ │
│  │              │   │              │   │              │   │              │ │
│  │ • Node Exp.  │──▶│ • Prometheus │──▶│ • Alertmanager│──▶│ • Grafana    │ │
│  │ • cAdvisor   │   │   (TSDB)     │   │   (路由/抑制) │   │   (仪表盘)   │ │
│  │ • App Metrics│   │ • Thanos     │   │ • WeCom/PagerD│   │ • 内嵌面板    │ │
│  │ • Blackbox   │   │   (长期存储)  │   │   (On-Call)   │   │ • 业务看板    │ │
│  │ • Log Exporter│  │   (下游)      │   │               │   │              │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
│         │                   │                   │                   │       │
│         └───────────────────┼───────────────────┼───────────────────┘       │
│                             ▼                                               │
│                    ┌─────────────────────┐                                  │
│                    │    元数据/服务发现     │                                  │
│                    │  • Consul / k8s SD   │                                  │
│                    │  • 静态文件配置       │                                  │
│                    └─────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 组件版本
| 组件 | 版本 | 部署方式 | 高可用 |
|------|------|---------|--------|
| Prometheus | 2.47+ | Docker/二进制 | 双副本 + Thanos Sidecar |
| Alertmanager | 0.26+ | Docker | 3 节点集群 (HA) |
| Grafana | 10.1+ | Docker | 双副本 + SQLite/PostgreSQL |
| Node Exporter | 1.7+ | DaemonSet/主机 | 全节点部署 |
| cAdvisor | 0.47+ | DaemonSet | 全节点部署 |
| Pushgateway | 1.6+ | 单实例 | 短生命周期任务推送 |
| Blackbox Exporter | 0.24+ | Deployment | 双副本 |
| Loki | 2.9+ | 单实例/集群 | 单实例 (规划集群) |

---

## 3. 指标体系设计

### 3.1 四大黄金信号 (Google SRE)
| 信号 | 定义 | 关键指标 | 告警阈值 |
|------|------|---------|---------|
| **延迟** | 请求处理时间 | `http_request_duration_seconds` (P50/P95/P99) | P99 > 1s (P1)、> 3s (P0) |
| **流量** | 请求速率 | `http_requests_total` (QPS) | 突降 > 50% (P1)、突增 > 200% (P2) |
| **错误** | 失败率 | `http_requests_total{status=~"5.."}` / `http_requests_total` | > 1% (P1)、> 5% (P0) |
| **饱和度** | 资源利用率 | CPU/内存/磁盘/网络/连接池/队列 | > 80% (P2)、> 90% (P1) |

### 3.2 USE 方法 (资源指标)
| 资源 | Utilization (使用率) | Saturation (饱和度) | Errors (错误) |
|------|---------------------|---------------------|--------------|
| CPU | `node_cpu_seconds_total{mode="idle"}` | `node_load1 / cpu_cores` | `node_cpu_seconds_total{mode="iowait"}` |
| 内存 | `node_memory_Active_bytes / node_memory_MemTotal_bytes` | `node_memory_Available_bytes < 10%` | OOM Kill 事件 |
| 磁盘 | `node_filesystem_avail_bytes / node_filesystem_size_bytes` | `node_disk_io_time_seconds_total` 增长 | `node_filesystem_readonly` |
| 网络 | `node_network_receive_bytes_total / bandwidth` | `node_network_tcp_retrans_total` | `node_network_err_total` |
| 连接池 | `active_connections / max_connections` | `waiting_requests` | `connection_errors_total` |

### 3.3 RED 方法 (服务指标)
| 维度 | Rate (请求率) | Errors (错误率) | Duration (延迟) |
|------|--------------|----------------|----------------|
| **API 网关** | `http_requests_total` | `http_requests_total{status=~"5.."}` | `http_request_duration_seconds` |
| **业务接口** | `business_request_total` | `business_request_total{status="failed"}` | `business_request_duration_seconds` |
| **数据库** | `mysql_queries_total` | `mysql_errors_total` | `mysql_query_duration_seconds` |
| **缓存** | `redis_commands_total` | `redis_keyspace_misses / redis_keyspace_hits` | `redis_command_duration_seconds` |
| **消息队列** | `celery_tasks_total` | `celery_tasks_failed_total` | `celery_task_duration_seconds` |

### 3.4 业务指标 (North Star Metrics)
| 指标名 | 定义 | 采集来源 | 告警阈值 | 归属团队 |
|--------|------|---------|---------|---------|
| `douyin_sync_success_rate` | 同步任务成功率 | Celery 任务结果 | < 99.5% (P1) | 后端 |
| `douyin_sync_latency_seconds` | 同步任务端到端耗时 | Celery 任务耗时 | P99 > 30min (P1) | 后端 |
| `douyin_api_availability` | 核心 API 可用性 | Blackbox 探测 | < 99.9% (P0) | 运维 |
| `douyin_data_freshness_hours` | 数据新鲜度 (最晚同步时间) | MySQL `updated_at` | > 4 小时 (P1) | 后端 |
| `douyin_alert_noise_ratio` | 告警噪音比 (无效告警/总告警) | Alertmanager | > 20% (P2) | 运维 |
| `douyin_user_active_daily` | 日活用户数 | 业务埋点 | 环比下降 > 30% (P1) | 产品/运营 |

---

## 4. 告警规则规范

### 4.1 告警命名规范
```yaml
# 格式: <严重级>_<组件>_<信号>_<条件>
# 示例:
- alert: P0_MySQL_Down                    # 组件不可用
- alert: P1_MySQL_ReplicationLag_High     # 延迟过高
- alert: P2_Node_CPU_Utilization_High     # 资源使用率高
- alert: P1_API_ErrorRate_High            # 服务错误率
- alert: P2_Node_Disk_Space_Low           # 资源即将耗尽
```

### 4.2 告警标签规范
```yaml
labels:
  severity: "critical|warning|info"     # 必填: critical/warning/info
  team: "backend|ops|frontend|platform" # 必填: 负责团队
  component: "mysql|redis|nginx|api"    # 必填: 组件
  environment: "prod|staging|dev"       # 必填: 环境
  runbook: "https://wiki/runbook/xxx"   # 推荐: 对应 Runbook 链接
  owner: "zhangsan"                     # 推荐: 直接负责人
```

### 4.3 告警注解规范
```yaml
annotations:
  summary: "MySQL 主库不可用 (实例: {{ $labels.instance }})"
  description: |
    **故障详情**: MySQL 主库 {{ $labels.instance }} 连接失败，已持续 {{ $value | humanizeDuration }}。
    **影响范围**: 所有写入业务、同步任务、依赖主库的只读查询。
    **建议动作**:
    1. 检查实例进程/端口/磁盘/内存
    2. 执行主从切换 (参考 Runbook: DOC-OPS-001)
    3. 通知业务方只读降级
  runbook_url: "https://wiki.douyin.com/runbook/mysql-failover"
  dashboard_url: "https://grafana.douyin.com/d/mysql-overview"
```

### 4.4 告警抑制与分组
```yaml
# 抑制规则示例
inhibit_rules:
# 主库挂了，抑制从库复制延迟告警
- source_match:
    alertname: "P0_MySQL_Down"
  target_match:
    alertname: "P1_MySQL_ReplicationLag_High"
  equal: ["instance", "cluster"]

# 网络不通抑制所有上层应用告警
- source_match:
    alertname: "P0_Blackbox_Probe_Failed"
  target_match_re:
    alertname: "P1_API_.*"
  equal: ["instance"]

# 分组路由
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
  - match:
      severity: 'critical'
    receiver: 'pagerduty-critical'
    continue: true
  - match:
      team: 'backend'
    receiver: 'wecom-backend'
  - match:
      team: 'ops'
    receiver: 'wecom-ops'
```

---

## 5. 核心告警规则库

### 5.1 基础设施层
```yaml
groups:
- name: infrastructure
  interval: 30s
  rules:
  # 节点存活
  - alert: P0_Node_Down
    expr: up{job="node-exporter"} == 0
    for: 1m
    labels:
      severity: critical
      team: ops
      component: node
    annotations:
      summary: "节点 {{ $labels.instance }} 不可达"
      description: "节点 {{ $labels.instance }} 已失联 {{ $value | humanizeDuration }}"

  # CPU 使用率
  - alert: P1_Node_CPU_Utilization_High
    expr: (1 - avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))) > 0.85
    for: 10m
    labels:
      severity: warning
      team: ops
      component: node
    annotations:
      summary: "节点 {{ $labels.instance }} CPU 使用率过高"
      description: "CPU 使用率 {{ $value | humanizePercentage }} 持续 10 分钟"

  # 内存可用率
  - alert: P1_Node_Memory_Available_Low
    expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
    for: 5m
    labels:
      severity: warning
      team: ops
      component: node
    annotations:
      summary: "节点 {{ $labels.instance }} 可用内存不足 10%"
      description: "可用内存 {{ $value | humanizePercentage }}"

  # 磁盘空间
  - alert: P1_Node_Disk_Space_Low
    expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
    for: 5m
    labels:
      severity: warning
      team: ops
      component: node
    annotations:
      summary: "节点 {{ $labels.instance }} 根分区剩余空间 < 15%"
      description: "剩余空间 {{ $value | humanizePercentage }}"

  # 证书过期
  - alert: P1_SSL_Cert_Expiring_Soon
    expr: ssl_cert_not_after_timestamp_seconds - time() < 86400 * 30
    for: 1h
    labels:
      severity: warning
      team: ops
      component: nginx
    annotations:
      summary: "SSL 证书即将过期: {{ $labels.domain }}"
      description: "证书将在 {{ $value | humanizeDuration }} 后过期"
```

### 5.2 数据库层
```yaml
- name: mysql
  interval: 30s
  rules:
  # MySQL 存活
  - alert: P0_MySQL_Down
    expr: mysql_up == 0
    for: 30s
    labels:
      severity: critical
      team: ops
      component: mysql
    annotations:
      summary: "MySQL 实例 {{ $labels.instance }} 不可用"
      runbook_url: "https://wiki.douyin.com/runbook/mysql-failover"

  # 复制延迟
  - alert: P1_MySQL_ReplicationLag_High
    expr: mysql_slave_seconds_behind_master > 30
    for: 5m
    labels:
      severity: warning
      team: ops
      component: mysql
    annotations:
      summary: "MySQL 从库 {{ $labels.instance }} 复制延迟 {{ $value | humanizeDuration }}"

  # 连接数
  - alert: P2_MySQL_Connections_High
    expr: (mysql_global_status_threads_connected / mysql_global_variables_max_connections) > 0.8
    for: 10m
    labels:
      severity: warning
      team: ops
      component: mysql
    annotations:
      summary: "MySQL {{ $labels.instance }} 连接数使用率 {{ $value | humanizePercentage }}"

  # 慢查询
  - alert: P2_MySQL_Slow_Queries_High
    expr: rate(mysql_global_status_slow_queries[5m]) > 10
    for: 5m
    labels:
      severity: warning
      team: backend
      component: mysql
    annotations:
      summary: "MySQL {{ $labels.instance }} 慢查询频率过高: {{ $value }}/s"
```

### 5.3 Redis 层
```yaml
- name: redis
  interval: 30s
  rules:
  - alert: P0_Redis_Down
    expr: redis_up == 0
    for: 30s
    labels:
      severity: critical
      team: ops
      component: redis
    annotations:
      summary: "Redis 实例 {{ $labels.instance }} 不可用"

  - alert: P1_Redis_Memory_High
    expr: (redis_memory_used_bytes / redis_memory_max_bytes) > 0.85
    for: 5m
    labels:
      severity: warning
      team: ops
      component: redis
    annotations:
      summary: "Redis {{ $labels.instance }} 内存使用率 {{ $value | humanizePercentage }}"

  - alert: P2_Redis_Connected_Clients_High
    expr: (redis_connected_clients / redis_config_maxclients) > 0.8
    for: 10m
    labels:
      severity: warning
      team: ops
      component: redis
    annotations:
      summary: "Redis {{ $labels.instance }} 连接数使用率 {{ $value | humanizePercentage }}"
```

### 5.4 应用服务层
```yaml
- name: application
  interval: 30s
  rules:
  # API 可用性 (Blackbox)
  - alert: P0_API_Down
    expr: probe_success{job="blackbox-http"} == 0
    for: 1m
    labels:
      severity: critical
      team: backend
      component: api
    annotations:
      summary: "API 接口 {{ $labels.instance }} 探测失败"
      description: "端点: {{ $labels.__param_target }}"

  # API 错误率
  - alert: P1_API_ErrorRate_High
    expr: |
      sum(rate(http_requests_total{status=~"5.."}[5m])) by (service, instance)
      /
      sum(rate(http_requests_total[5m])) by (service, instance)
      > 0.05
    for: 3m
    labels:
      severity: warning
      team: backend
      component: api
    annotations:
      summary: "服务 {{ $labels.service }} 实例 {{ $labels.instance }} 5xx 错误率 {{ $value | humanizePercentage }}"

  # API 延迟 P99
  - alert: P1_API_Latency_P99_High
    expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service, instance)) > 1
    for: 5m
    labels:
      severity: warning
      team: backend
      component: api
    annotations:
      summary: "服务 {{ $labels.service }} P99 延迟 {{ $value | humanizeDuration }}"

  # 业务同步成功率
  - alert: P1_Sync_SuccessRate_Low
    expr: |
      sum(rate(celery_task_success_total[30m])) by (task_name)
      /
      sum(rate(celery_task_total[30m])) by (task_name)
      < 0.995
    for: 10m
    labels:
      severity: warning
      team: backend
      component: celery
    annotations:
      summary: "同步任务 {{ $labels.task_name }} 成功率 {{ $value | humanizePercentage }}"
```

### 5.5 业务指标层
```yaml
- name: business
  interval: 5m
  rules:
  - alert: P1_Data_Freshness_Stale
    expr: (time() - douyin_last_sync_timestamp_seconds) > 14400  # 4 小时
    for: 10m
    labels:
      severity: warning
      team: backend
      component: sync
    annotations:
      summary: "数据新鲜度异常，最后同步 {{ $value | humanizeDuration }} 前"

  - alert: P1_Alert_Noise_Ratio_High
    expr: |
      sum(rate(alertmanager_notifications_total{alertname=~"P3_.*"}[1h]))
      /
      sum(rate(alertmanager_notifications_total[1h]))
      > 0.2
    for: 1h
    labels:
      severity: warning
      team: ops
      component: alerting
    annotations:
      summary: "告警噪音比过高: {{ $value | humanizePercentage }}"
```

---

## 6. Grafana 大盘设计规范

### 6.1 大盘分类与命名
| 大盘分类 | 命名前缀 | 示例 | 更新频率 | 受众 |
|---------|---------|------|---------|------|
| 概览/总览 | `Overview -` | `Overview - System` | 30s | 全员/管理层 |
| 基础设施 | `Infra -` | `Infra - Node Exporter` | 30s | 运维 |
| 数据库 | `DB -` | `DB - MySQL Overview` | 30s | DBA/运维 |
| 缓存 | `Cache -` | `Cache - Redis Cluster` | 30s | 运维 |
| 应用服务 | `App -` | `App - API Gateway` | 30s | 后端/运维 |
| 业务指标 | `Biz -` | `Biz - Sync Monitoring` | 1m | 产品/后端/运营 |
| 告警/事件 | `Alert -` | `Alert - Alertmanager` | 实时 | 运维/On-Call |
| 链路追踪 | `Trace -` | `Trace - Service Map` | 实时 | 后端/架构师 |

### 6.2 大盘设计原则
1. **单屏原则**: 关键大盘单屏展示，避免滚动
2. **红绿分明**: 正常绿色、警告黄色、严重红色、正常蓝色
3. **TOP-N 展示**: 列表类面板默认展示 Top 10
3. **时间范围**: 默认 1 小时，提供 5m/1h/6h/24h/7d 快捷切换
4. **变量化**: 环境/集群/实例/服务作为顶部变量下拉框
5. **链接跳转**: 关键指标面板点击跳转到详细大盘或日志查询

### 6.3 标准大盘模板结构
```json
{
  "title": "App - API Gateway",
  "tags": ["api", "gateway", "backend"],
  "timezone": "Asia/Shanghai",
  "refresh": "30s",
  "time": {"from": "now-1h", "to": "now"},
  "templating": {
    "list": [
      {"name": "environment", "type": "query", "query": "label_values(up, environment)"},
      {"name": "service", "type": "query", "query": "label_values(http_requests_total, service)"},
      {"name": "instance", "type": "query", "query": "label_values(http_requests_total{service=~\"$service\"}, instance)"}
    ]
  },
  "panels": [
    {"title": "QPS", "type": "timeseries", "targets": [{"expr": "sum(rate(http_requests_total[5m])) by (service)"}]},
    {"title": "Error Rate", "type": "timeseries", "targets": [{"expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)"}]},
    {"title": "Latency P50/P95/P99", "type": "timeseries", "targets": [{"expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))"}, {"expr": "histogram_quantile(0.95, ...")}, {"expr": "histogram_quantile(0.99, ...")}]},
    {"title": "Top 10 Slow Endpoints", "type": "table", "targets": [{"expr": "topk(10, histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)))"}]}
  ]
}
```

---

## 7. 日志监控规范

### 7.1 日志采集架构
```
应用容器 (stdout/stderr)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Loki / ELK 采集管道                          │
│  Promtail / Filebeat ──▶ Loki / Logstash ──▶ Loki / ES       │
│       │                      │                    │           │
│       ▼                      ▼                    ▼           │
│  标签化 (service, pod,      解析 (JSON/Logfmt/       索引/存储  │
│  namespace, container)       正则/多行)              (TSDB)     │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Grafana / Kibana 查询                        │
│  • LogQL / Lucene 查询                                       │
│  • 关联 Trace ID (trace_id)                                   │
│  • 告警规则 (LogQL)                                           │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 结构化日志格式 (JSON)
```json
{
  "timestamp": "2026-09-26T10:30:00.123Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "abc-123-def-456",
  "span_id": "span-789",
  "user_id": "user_001",
  "shop_id": "shop_123",
  "action": "order.sync",
  "duration_ms": 1250,
  "status": "success",
  "message": "Order sync completed",
  "context": {
    "orders_synced": 150,
    "duration_seconds": 1.25
  }
}
```

### 7.3 关键日志告警规则
```yaml
- alert: P1_App_Error_Log_Spike
  expr: |
    sum by (service) (rate({service=~".+"} |= "ERROR" [5m])) > 10
  for: 3m
  labels:
    severity: warning
    team: backend
  annotations:
    summary: "服务 {{ $labels.service }} ERROR 日志激增: {{ $value }}/s"

- alert: P0_App_Panic_Crash
  expr: |
    sum by (service) (rate({service=~".+"} |= "panic" or |= "fatal" or |= "Segmentation fault" [5m])) > 0
  for: 1m
  labels:
    severity: critical
    team: backend
  annotations:
    summary: "服务 {{ $labels.service }} 发生崩溃/panic"
```

---

## 8. 链路追踪规范

### 8.1 追踪采样策略
| 场景 | 采样率 | 说明 |
|------|--------|------|
| 正常请求 | 10% (1/10) | 统计延迟分布 |
| 错误请求 (5xx) | 100% | 全量采集错误链路 |
| 慢请求 (P99+) | 100% | 全量采集慢请求 |
| 关键业务链路 | 100% | 同步任务、支付、核心写入 |

### 8.2 Span 标准属性
```go
// OpenTelemetry 语义约定
span.SetAttributes(
    attribute.String("http.method", "GET"),
    attribute.String("http.target", "/api/orders"),
    attribute.Int("http.status_code", 200),
    attribute.String("http.route", "/api/orders"),
    attribute.String("net.peer.ip", "10.0.1.50"),
    attribute.String("db.system", "mysql"),
    attribute.String("db.name", "douyin"),
    attribute.String("db.operation", "SELECT"),
    attribute.String("db.statement", "SELECT * FROM orders WHERE shop_id=?"),
    attribute.Int64("db.rows_affected", 150),
    attribute.String("messaging.system", "celery"),
    attribute.String("messaging.destination", "sync_queue"),
    attribute.String("messaging.operation", "publish"),
    attribute.Int64("messaging.message_size", 1024),
)
```

---

## 9. On-Call 倒班与响应

### 9.1 倒班职责
| 角色 | 职责 | 响应时限 | 升级路径 |
|------|------|---------|---------|
| **Primary On-Call** | 首响应、初步诊断、实施标准恢复、状态同步 | ACK 5min、定位 15min | 无法解决 → Secondary |
| **Secondary On-Call** | 复杂故障支持、架构决策、跨团队协调 | 接手后 10min 响应 | 仍无法解决 → Tech Lead/Manager |
| **Manager On-Call** | 重大决策、资源调度、对外沟通、事后复盘推进 | 接手后 30min | - |

### 9.2 倒班交接清单
```markdown
# On-Call 交接单 - YYYY-MM-DD

## 交接人: 张三 → 接班人: 李四
## 交接时间: 2026-09-26 18:00

### 进行中告警
| 告警 | 级别 | 当前状态 | 已执行动作 | 下一步计划 | 预计解决 |
|------|------|----------|------------|------------|----------|
| P1_MySQL_ReplicationLag | Warning | 监控中 | 已检查无长事务 | 观察 30min | 19:00 |

### 待办变更
| 变更单 | 风险 | 窗口 | 状态 | 备注 |
|--------|------|------|------|------|
| CHG-20260926-001 | 低 | 22:00-23:00 | 待审批 | Nginx 配置优化 |

### 关注点
- 今日新发布 v1.2.3，关注错误率波动
- FXG API 近期偶发 429，已配置降级

### 文档链接
- 当前待办: https://jira.douyin.com/filter/oncall-open
- Runbook: https://wiki.douyin.com/runbook
- 监控大盘: https://grafana.douyin.com/d/overview
```

---

## 10. 告警治理与优化

### 9.1 告警生命周期管理
| 阶段 | 动作 | 负责人 | 频率 |
|------|------|--------|------|
| **新增** | 设计评审、Runbook 关联、测试验证 | 申请人 + 运维 Review | 按需 |
| **调优** | 阈值调整、抑制规则、分组优化 | 运维 + 相关 Owner | 月度 |
| **清理** | 失效/冗余/噪音告警下线 | 运维 | 季度 |
| **演练** | 告警触发验证、流程演练 | On-Call | 季度 |

### 9.2 告警质量指标 (目标)
| 指标 | 目标 | 当前 | 改进方向 |
|------|------|------|---------|
| 告警噪音比 (无效/总) | < 10% | ~25% | 清理 P3、合并相关告警、抑制规则 |
| 平均响应时间 (MTTA) | < 5 min (P0) | ~8 min | 优化 Runbook、自动化诊断 |
| 平均恢复时间 (MTTR) | < 30 min (P0) | ~45 min | 自动化恢复、预案演练 |
| 告警覆盖率 (关键路径) | 100% | ~85% | 补全业务指标监控 |
| 重复告警率 | < 5% | ~15% | 分组抑制、智能降噪 |

---

## 10. 附录

### 10.1 Prometheus 规则单元测试
```yaml
# tests/rules_test.yml
groups:
- name: test_mysql_rules
  interval: 1m
  rules:
  - alert: Test_MySQL_Down
    expr: mysql_up == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "Test alert"

# 运行测试
promtool test rules tests/rules_test.yml
```

### 10.2 常用 PromQL 片段
```promql
# 实例级 CPU 使用率 (排除 idle)
1 - avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

# 服务级 QPS
sum(rate(http_requests_total[5m])) by (service)

# 服务级错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)

# P99 延迟
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))

# 磁盘使用率
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes

# 网络带宽利用率
rate(node_network_transmit_bytes_total[5m]) / (node_network_speed_bytes / 8)

# 容器重启次数
increase(container_start_time_seconds[1h])

# 证书剩余天数
(ssl_cert_not_after_timestamp_seconds - time()) / 86400
```

### 10.3 Grafana 仪表盘导入 API
```bash
# 通过 API 批量导入大盘
curl -X POST "https://grafana.douyin.com/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @dashboard.json
```
EOF