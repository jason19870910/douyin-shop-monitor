---
title: 数据流设计文档
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: Tech Lead
reviewers: [架构师, Backend Lead, Data Engineer]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-TECH-004
tags: [架构, 数据流, 设计文档, ETL, 同步]
related_docs: [DOC-TECH-001, DOC-TECH-002, DOC-API-001, DOC-API-002]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - Tech Lead
---

# 数据流设计文档

## 1. 概述
本文档描述抖音电商数据监控平台的核心数据流向，包括外部数据拉取、内部处理、存储、查询及告警触发的完整链路。

---

## 2. 总体数据流架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  外部数据源  │────▶│  同步服务    │────▶│  数据清洗/   │────▶│  存储层      │
│  (FXG/Creator)│     │  (Celery)   │     │  转换层      │     │  (MySQL/Redis)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                    │                    │
                           ▼                    ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │  任务调度    │     │  校验/告警   │     │  查询服务    │
                    │  (Celery Beat)│     │  引擎        │     │  (Flask API) │
                    └─────────────┘     └─────────────┘     └─────────────┘
                           │                    │                    │
                           ▼                    ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │  监控/日志   │     │  通知推送    │     │  前端展示    │
                    │  (Prometheus)│     │  (WeCom/Email)│     │  (React)     │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 3. 外部数据源接入

### 3.1 抖店 (FXG) API
| 维度 | 说明 |
|------|------|
| Base URL | `https://fxg.jinritemai.com` |
| 认证方式 | Cookie + `__TOKEN` + `a_bogus` 签名 |
| 核心接口 | `/api/goods/list`、`/api/order/list`、`/api/compliance/list` |
| 限流策略 | 20 QPS，指数退避重试 |
| 分页方式 | `page` + `size` (max 100) |

### 3.2 抖音创作者 API
| 维度 | 说明 |
|------|------|
| Base URL | `https://creator.douyin.com` |
| 认证方式 | OAuth 2.0 + `access_token` 刷新 |
| 核心接口 | `/api/creator/info`、`/api/video/list`、`/api/fans/trend` |
| 限流策略 | 50 QPS，令牌桶算法 |

---

## 4. 同步任务设计

### 4.1 任务分类
| 任务类型 | 调度方式 | 优先级队列 | 典型耗时 | 重试策略 |
|---------|---------|-----------|---------|---------|
| 全量同步 | Celery Beat (每日 02:00) | `sync` (高) | 15-30 min | 3 次，指数退避 |
| 增量同步 | Celery Beat (每小时) | `sync` (高) | 2-5 min | 3 次，指数退避 |
| 单商品补录 | 手动触发 / API | `sync` (高) | < 30s | 2 次 |
| 报表生成 | Celery Beat (每日 03:00) | `report` (低) | 5-10 min | 2 次 |
| 告警检查 | Celery Beat (每 5 分钟) | `alert` (高) | < 1 min | 1 次 |
| 合规检测 | 手动触发 / 定时 | `default` | 3-10 min | 2 次 |

### 4.2 任务幂等性设计
```python
# 任务键设计：防止重复执行
TASK_KEYS = {
    "full_sync": "sync:full:{date:%Y%m%d}",
    "incremental_sync": "sync:incr:{shop_id}:{timestamp:%Y%m%d%H}",
    "report_daily": "report:daily:{date:%Y%m%d}",
    "alert_check": "alert:check:{rule_id}:{window_start:%Y%m%d%H%M}",
}

# Redis SETNX 实现分布式锁
def acquire_task_lock(key: str, ttl: int = 3600) -> bool:
    return redis.set(key, "1", nx=True, ex=ttl)
```

---

## 5. 数据清洗与转换层

### 5.1 清洗规则
| 源字段 | 目标字段 | 转换逻辑 | 异常处理 |
|--------|---------|---------|---------|
| `goods_id` (str) | `product_id` (int) | `int(goods_id)` | 非数字记录错误日志，跳过 |
| `price` (str, 分) | `price_yuan` (Decimal) | `Decimal(price) / 100` | 负数设为 0 |
| `create_time` (ms) | `created_at` (DateTime) | `datetime.fromtimestamp(ms/1000, tz=UTC)` | 未来时间截断为 now |
| `status` (int) | `status_enum` (Enum) | 映射表转换 | 未知值标记为 `UNKNOWN` |
| `sku_list` (list) | `skus` (JSON) | 保留原始结构，校验必填字段 | 空列表存 `[]` |

### 5.2 数据模型映射
```python
# 外部 -> 内部统一模型
class ProductSyncDTO:
    product_id: int
    shop_id: int
    name: str
    price_yuan: Decimal
    stock: int
    sales_7d: int
    status: ProductStatus  # ON_SALE / OFF_SALE / VIOLATION
    category_path: str
    images: List[str]
    created_at: datetime
    updated_at: datetime
    raw_data: dict  # 保留原始字段供审计
```

---

## 6. 存储设计

### 6.1 MySQL 核心表
| 表名 | 用途 | 分区策略 | 索引策略 | 保留周期 |
|------|------|---------|---------|---------|
| `products` | 商品主表 | 无 (单表 < 50w) | idx_shop_status, idx_updated_at | 永久 |
| `orders` | 订单主表 | 按月分区 | idx_shop_status_time, idx_buyer | 3 年 |
| `order_items` | 订单明细 | 按月分区 | idx_order_id, idx_product_id | 3 年 |
| `creators` | 创作者表 | 无 | idx_shop_fans | 永久 |
| `videos` | 视频表 | 按月分区 | idx_creator_time, idx_status | 2 年 |
| `compliance_records` | 合规记录 | 按月分区 | idx_shop_risk_time, idx_rule_id | 2 年 |
| `alert_history` | 告警历史 | 按月分区 | idx_shop_metric_time, idx_status | 1 年 |
| `sync_tasks` | 同步任务记录 | 按月分区 | idx_type_status_time, idx_shop | 6 个月 |

### 6.2 Redis 缓存设计
| Key 模式 | 数据类型 | TTL | 用途 |
|---------|---------|-----|------|
| `cache:dashboard:stats:{shop_id}` | Hash | 60s | 仪表盘聚合指标 |
| `cache:products:list:{shop_id}:{page}:{size}:{filters_hash}` | String(JSON) | 120s | 商品列表分页 |
| `cache:orders:list:{shop_id}:{page}:{size}:{filters_hash}` | String(JSON) | 60s | 订单列表分页 |
| `cache:creators:list:{shop_id}` | String(JSON) | 300s | 创作者列表 |
| `lock:sync:{task_key}` | String | 3600s | 分布式任务锁 |
| `rate_limit:api:{endpoint}:{ip}` | String | 60s | API 限流计数 |
| `session:{user_id}` | Hash | 86400s | 用户会话 |
| `celery:broker` | List/Stream | 永久 | Celery 消息队列 |

---

## 7. 查询服务数据流

### 7.1 API 查询路径
```
Client (React)
    │
    ▼
Nginx (反向代理, 静态资源, 限流)
    │
    ▼
Flask API (Gunicorn Workers)
    │
    ├── /api/health          ──▶ Redis Ping + DB Ping
    ├── /api/dashboard/stats ──▶ Redis Cache → MySQL (聚合查询)
    ├── /api/products        ──▶ Redis Cache → MySQL (分页 + 筛选)
    ├── /api/orders          ──▶ Redis Cache → MySQL (分页 + 筛选)
    ├── /api/creators        ──▶ Redis Cache → MySQL
    ├── /api/compliance      ──▶ MySQL (实时性要求高，不缓存)
    └── /api/sync            ──▶ Celery 异步任务提交
```

### 7.2 缓存策略
| 场景 | 策略 | 失效机制 |
|------|------|----------|
| 仪表盘聚合 | Cache-Aside | 同步任务完成主动删 key |
| 列表分页 | Cache-Aside | 筛选条件变化自然失效 |
| 详情页 | Cache-Aside | 更新操作主动删 key |
| 合规/告警 | 不缓存 | 强一致性要求 |

---

## 8. 告警触发数据流

```
定时触发 (Celery Beat, 5min)
    │
    ▼
告警检查 Task (worker_alert)
    │
    ├── 读取告警规则 (MySQL: alert_rules)
    │
    ├── 查询当前指标值
    │     ├── 销量/收入/订单 ──▶ Redis Cache (dashboard:stats)
    │     ├── 退款率 ──▶ MySQL 实时聚合
    │     ├── 合规风险 ──▶ MySQL (compliance_records 近 1h)
    │     └── 播放量/互动 ──▶ Redis Cache (creators)
    │
    ├── 规则引擎评估
    │     ├── 条件：值 > 阈值 / 值 < 阈值 / 波动率 > 阈值
    │     ├── 静默期检查
    │     └── 去重：同规则同实体 30min 内不重复告警
    │
    ├── 生成告警记录 (MySQL: alert_history)
    │
    └── 异步推送通知 (Celery: worker_default)
          ├── 企业微信机器人 (Markdown 卡片)
          ├── 邮件 (HTML 模板)
          └── 短信 (紧急级别)
```

---

## 9. 数据血缘与追踪

### 9.1 关键字段血缘
```
外部 API 响应
    │ (原始 JSON 存 raw_data)
    ▼
清洗转换 (tasks/transformers.py)
    │ (字段映射、类型转换、异常标记)
    ▼
入库 (MySQL 核心表)
    │ (事务保证一致性)
    ▼
缓存更新 (Redis)
    │ (异步，最终一致性)
    ▼
API 查询返回
    │ (序列化、脱敏)
    ▼
前端渲染 (React Components)
```

### 9.2 追踪字段
每条核心记录包含：
- `trace_id`: 链路追踪 ID (贯穿同步任务 → 入库 → 缓存 → 查询)
- `source`: 数据来源 (`fxg` / `creator` / `manual`)
- `sync_batch_id`: 同步批次 ID (关联同步任务记录)
- `raw_data`: 原始 API 响应 (审计、回溯、重处理)

---

## 10. 异常处理与补偿

| 异常场景 | 检测方式 | 补偿措施 |
|---------|---------|---------|
| 外部 API 返回错误码 | HTTP 状态码 + 业务 code | 指数退避重试 3 次，记录失败任务供人工重跑 |
| 外部 API 限流 | 429 / 频控错误码 | 动态调整并发度，启用令牌桶限流 |
| 数据清洗失败 | Python 异常捕获 | 记录错误样本，入库 `sync_errors` 表，告警通知 |
| MySQL 主从延迟 | 读写分离路由检测 | 强制走主库，或等待追上 |
| Redis 缓存穿透 | 空值缓存 + 布隆过滤器 | 空值缓存 30s，布隆过滤器拦截非法 key |
| 任务积压 | Flower 监控队列长度 | 自动扩容 Worker，或降级非核心任务 |

---

## 11. 性能优化点

1. **批量入库**: `executemany` / `LOAD DATA` 批量插入，减少 Round-trip
2. **异步流水线**: 生产者-消费者模式，同步任务不阻塞 API
3. **读写分离**: 查询走从库，同步写主库
4. **缓存预热**: 定时任务完成后主动预热热点缓存
5. **索引优化**: 覆盖索引避免回表，联合索引顺序匹配查询模式
6. **分页优化**: 游标分页替代 Offset 大偏移
EOF