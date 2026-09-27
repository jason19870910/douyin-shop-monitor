# API 规范文档

> Douyin 监控平台统一 API 规范，包含内部后端 RESTful 接口与外部抖音电商后台接口。

**版本**: 1.2.1
**最后更新**: 2026-09-26
**维护**: 项目核心团队

---

## 目录

1. [公共返回结构](#公共返回结构)
2. [内部 API 概览](#内部-api-概览)
3. [内部 API 详细](#内部-api-详细)
4. [外部 API 概览](#外部-api-概览)
5. [外部 API 详细](#外部-api-详细)
6. [认证与请求头](#认证与请求头)
7. [错误码](#错误码)

---

## 公共返回结构

### 内部 API 成功

```json
{ "success": true, "data": {}, "message": "可选" }
```

### 内部 API 错误

```json
{ "success": false, "error": "错误描述", "code": 400 }
```

### 外部 API 成功

```json
{ "code": 0, "message": "success", "data": {} }
```

### 外部 API 错误

```json
{ "code": 40001, "message": "错误描述", "data": null }
```

---

## 内部 API 概览

Base URL: `http://localhost:5000/api/v1` 开发 / 生产域名 `/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/dashboard/stats` | 仪表盘聚合统计 |
| GET | `/api/v1/products` | 商品列表缓存 |
| GET | `/api/v1/products/stats` | 商品统计转发 |
| GET | `/api/v1/products/external` | 外部商品列表透传 |
| GET | `/api/v1/products/:id` | 商品详情 |
| GET | `/api/v1/orders` | 订单列表 |
| GET | `/api/v1/orders/stats` | 订单统计转发 |
| GET | `/api/v1/creators` | 创作者列表 |
| GET | `/api/v1/creators/works` | 创作者作品缓存 |
| GET | `/api/v1/creators/works/external` | 外部创作者作品透传 |
| GET | `/api/v1/creators/overview` | **创作者概览转发**（已统一为 GET） |
| GET | `/api/v1/compliance` | 合规列表 |
| GET | `/api/v1/compliance/stats` | 合规统计 |
| GET | `/api/v1/compliance/rules` | 合规规则列表 |
| POST | `/api/v1/compliance/rules` | 创建合规规则 |
| PUT | `/api/v1/compliance/rules/:id` | 更新合规规则 |
| DELETE | `/api/v1/compliance/rules/:id` | 删除合规规则 |
| POST | `/api/v1/compliance/check` | 触发合规检测 |
| GET | `/api/v1/compliance/export` | 导出合规报告 |
| GET | `/api/v1/alerts/config` | 获取通用告警配置 |
| POST | `/api/v1/alerts/config` | 更新通用告警配置 |
| GET | `/api/v1/alerts/history` | 获取告警历史（支持分页、类型过滤） |
| DELETE | `/api/v1/alerts/history` | 清空告警历史 |
| GET | `/api/v1/alerts/history/stats` | 获取告警统计汇总 |
| GET | `/api/v1/alerts/dian/config` | 获取抖店告警配置 |
| POST | `/api/v1/alerts/dian/config` | 更新抖店告警配置 |
| GET | `/api/v1/alerts/douyin/config` | 获取抖音告警配置 |
| POST | `/api/v1/alerts/douyin/config` | 更新抖音告警配置 |
| POST | `/api/v1/sync` | 手动触发同步（支持 `?async=true` 异步模式） |
| GET | `/api/v1/sync/history` | 同步历史 |
| GET | `/api/v1/mock/status` | Mock 状态 |
| GET | `/api/v1/videos` | 视频列表 |
| GET | `/api/v1/videos/:id` | 视频详情 |
| POST | `/api/v1/videos` | 创建视频 |
| PUT | `/api/v1/videos/:id` | 更新视频 |
| DELETE | `/api/v1/videos/:id` | 删除视频 |
| GET | `/api/v1/auth/qr-code` | 获取二维码 |
| GET | `/api/v1/auth/login` | 登录 |
| POST | `/api/v1/auth/logout` | 登出 |
| GET | `/api/v1/auth/status` | 授权状态 |
| GET | `/api/v1/accounts` | 账号列表 |
| GET | `/api/v1/accounts/:id` | 账号详情 |
| POST | `/api/v1/accounts` | 创建账号 |
| PUT | `/api/v1/accounts/:id` | 更新账号 |
| DELETE | `/api/v1/accounts/:id` | 删除账号 |
| GET | `/api/v1/media/video-edit` | 视频编辑列表 |
| GET | `/api/v1/media/image-edit` | 图片编辑列表 |

---

## 首页数据需求

| 区块 | 使用的 API | 说明 |
|------|------------|------|
| 整体概览（今日销售额、今日订单数、今日收入、转化率） | `GET /api/v1/dashboard/stats` | 提供 total_sales_today/yesterday, total_revenue_today/yesterday, total_orders_today/yesterday, avg_conversion_rate, sales_trend, top_products |
| 商品统计（在售/库存/违规） | `GET /api/v1/products/stats?tab=...` | 根据 tab 返回对应统计指标（销量、库存、违规数等） |
| 订单统计（全部/支付/取消） | `GET /api/v1/orders/stats` | 返回 all/pay/cancel 的 count 和 amount |
| 创作者中心概览 | `GET /api/v1/creators/overview?recent_days=7` | 返回 total_followers, total_videos, recent_view, recent_like |
| 系统健康 | `GET /api/v1/health` | 返回 status、last_update、timestamp；数据来源从 dashboard/stats 的 data_source 字段获取 |
| 立即同步触发 | `POST /api/v1/sync` | 手动触发同步（支持 `?async=true` 异步模式），成功后刷新健康状态 |
| 合规告警（可选） | `GET /api/v1/compliance/stats` + `GET /api/v1/compliance?status=pending&size=5` | 未处理高危违规数量与最近 5 条记录 |
| 告警配置开关 | `GET /api/v1/alerts/config`、`GET /api/v1/alerts/dian/config`、`GET /api/v1/alerts/douyin/config` | 是否启用各类预警 |
| Mock / 降级开关 | `GET /api/v1/mock/status` | 前端根据此决定是否展示占位数据 |
## 内部 API 详细

### 健康检查

`GET /api/v1/health`

**无需认证**（在 `PUBLIC_ENDPOINTS` 白名单中）。

```json
{ "status": "healthy", "timestamp": "...", "last_update": "..." }
```

- `status`: 固定为 `healthy`
- `timestamp`: 当前服务器时间（ISO 8601）
- `last_update`: 最近一次定时同步完成时间（来自 Redis `last_update` 键）

### 仪表盘统计

`GET /api/v1/dashboard/stats`

返回：`total_sales_today/yesterday`、`total_revenue_today/yesterday`、`total_orders_today/yesterday`、`avg_conversion_rate`、`sales_trend`、`top_products`。

### 商品列表

`GET /api/v1/products?page=1&size=20&keyword=`

分页返回商品缓存数据。

### 商品统计

`GET /api/v1/products/stats?tab=onSale&appid=1`

转发至外部 `fxg.jinritemai.com/product/tproduct/aggsProductCount`，自动注入 Cookie 与签名。

**参数**：
- `tab`: `onSale` (在售) / `stock` (库存) / `violation` (违规)
- `appid`: 应用 ID

**返回字段**（外部透传）：
- `total_count`: 总数
- `on_sale_count`: 在售数
- `stock_count`: 库存预警数
- `violation_count`: 违规数

### 外部商品列表

`GET /api/v1/products/external`

透传所有查询参数至外部 `/product/tproduct/list`。

**返回字段**（`data.list`）：
- `product_id` / `product_name` / `name`
- `sales_today` / `sales_yesterday`
- `conversion_rate` / `conversion_rate_yesterday`
- `inventory` / `status`
- `market_price` / `discount_price` / `price`
- `img` / `product_url`
- `shop_id`

### 订单统计

`GET /api/v1/orders/stats`

转发至外部 `fxg.jinritemai.com/api/order/tabcnt`。

**返回字段**（外部透传）：
```json
{
  "all": { "count": 100, "amount": 50000 },
  "pay": { "count": 80, "amount": 45000 },
  "cancel": { "count": 20, "amount": 5000 }
}
```

### 创作者概览

`GET /api/v1/creators/overview?recent_days=7`

**内部已统一为 GET**（外部为 `POST /janus/douyin/creator/data/overview/dashboard`）。

转发至外部创作者中心，自动注入 Cookie 与签名。

**返回字段**：
- `total_followers`: 总粉丝数
- `total_videos`: 总视频数
- `recent_view`: 近期播放量
- `recent_like`: 近期点赞数

### 创作者作品外部列表

`GET /api/v1/creators/works/external`

透传至外部 `/janus/douyin/creator/pc/work_list`，前端做字段归一化映射。

**归一化映射**：
| 前端字段 | 外部字段回退 |
|---------|-------------|
| `title` | `title` → `name` |
| `creator_name` | `creator_name` → `author_name` → `nickname` → `user_nickname` |
| `cover_url` | `cover_url` → `cover` → `cover_img` |
| `play_count` | `play_count` → `play` |
| `like_count` | `like_count` → `favorite_count` |
| `comment_count` | `comment_count` → `comment` |
| `share_count` | `share_count` → `share` |

---

### 手动触发同步

`POST /api/v1/sync`

**查询参数**：
- `async` (可选): `true` / `false` - 是否异步执行（默认 `false`）

**同步模式返回**：
```json
{
  "status": "completed",
  "mode": "sync",
  "last_update": "2026-09-23T10:00:00",
  "results": {
    "products": "success",
    "orders": "success",
    "creators": "success",
    "creator_works": "success",
    "compliance": "success",
    "alerts": "success"
  }
}
```

**异步模式返回**：
```json
{
  "status": "started",
  "mode": "async",
  "task_id": "celery-task-id",
  "message": "Full sync task queued"
}
```

---

## 外部 API 概览

域名: `fxg.jinritemai.com`, `creator.douyin.com`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 商品统计 | GET | `/product/tproduct/aggsProductCount` | 商品聚合计数 |
| 商品列表 | GET | `/product/tproduct/list` | 商品分页列表 |
| 订单统计 | GET | `/api/order/tabcnt` | 订单状态汇总 |
| 订单列表 | GET | `/api/order/searchlist` | 订单明细 |
| 创作者概览 | POST | `/janus/douyin/creator/data/overview/dashboard` | 创作者仪表盘 |
| 创作者作品 | GET/POST | `/janus/douyin/creator/pc/work_list` | 作品列表 |

---

## 外部 API 详细

### 商品列表 `/product/tproduct/list`

**参数示例**：`page`, `pageSize`, `tab`, `appid`, `__token`, `msToken`, `a_bogus`, `verifyFp`, `fp`, `_bid`, `aid`, `_lid`

**返回**：`data.list` 包含 `product_id`, `name`, `product_name`, `sales_today`, `market_price`, `discount_price`, `img`, `product_url`, `shop_id`.

### 订单列表 `/api/order/searchlist`

**参数**：`page`, `pageSize`, `compact_time[select]`, `order_by`, `order`, `tab`, `appid`, `__token`, `msToken`, `a_bogus`, `verifyFp`, `fp`, `_bid`, `aid`, `_lid`

**返回**：`data.list` 包含 `order_id`, `buyer_name`, `product_name`, `amount`, `status`.

### 创作者作品 `/janus/douyin/creator/pc/work_list`

**参数**：`cursor`, `count`, `creator_id`, `__token`, `msToken`, `a_bogus`, `verifyFp`, `fp`

**返回**：`data.list` 包含 `work_id`, `title`, `cover_url`, `play_count`, `like_count`, `creator_name`.

详见归档历史文档 `archive_cleanup_20260923/legacy_docs/api_old/`.

---

### 通用告警配置

`GET /api/v1/alerts/config` / `POST /api/v1/alerts/config`

**GET 返回字段**：
```json
{
  "sales_drop_threshold": 0.3,
  "conversion_drop_threshold": 0.2,
  "inventory_low_threshold": 10,
  "notification_email": "admin@example.com",
  "enabled": true
}
```

**POST 请求体**（所有字段可选）：
```json
{
  "sales_drop_threshold": 0.3,
  "conversion_drop_threshold": 0.2,
  "inventory_low_threshold": 10,
  "notification_email": "admin@example.com",
  "enabled": true
}
```

---

### 抖店告警配置

`GET /api/v1/alerts/dian/config` / `POST /api/v1/alerts/dian/config`

**GET 返回字段**：
```json
{
  "product_sales_drop_threshold": 0.3,
  "order_refund_rate_threshold": 0.15,
  "compliance_risk_threshold": "medium",
  "notification_email": "admin@example.com",
  "enabled": true
}
```

**POST 请求体**（所有字段可选）：
```json
{
  "product_sales_drop_threshold": 0.3,
  "order_refund_rate_threshold": 0.15,
  "compliance_risk_threshold": "medium",
  "notification_email": "admin@example.com",
  "enabled": true
}
```

---

### 抖音告警配置

`GET /api/v1/alerts/douyin/config` / `POST /api/v1/alerts/douyin/config`

**GET 返回字段**：
```json
{
  "video_view_drop_threshold": 0.3,
  "video_like_drop_threshold": 0.2,
  "creator_follower_drop_threshold": 0.1,
  "notification_email": "admin@example.com",
  "enabled": true
}
```

**POST 请求体**（所有字段可选）：
```json
{
  "video_view_drop_threshold": 0.3,
  "video_like_drop_threshold": 0.2,
  "creator_follower_drop_threshold": 0.1,
  "notification_email": "admin@example.com",
  "enabled": true
}
```

---

### 告警历史

`GET /api/v1/alerts/history`

**查询参数**：
- `limit` (可选): 每页数量，默认 50，最大 200
- `offset` (可选): 偏移量，默认 0
- `type` (可选): 告警类型过滤（`sales_drop`、`low_inventory`、`conversion_drop`）

**返回**：
```json
{
  "list": [
    {
      "type": "sales_drop",
      "product_id": "xxx",
      "product_name": "商品名",
      "message": "Product xxx sales dropped by 50%",
      "drop_rate": 0.5,
      "threshold": 0.3,
      "timestamp": "2026-09-23T10:00:00"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

`DELETE /api/v1/alerts/history`

**返回**：
```json
{
  "cleared": 100
}
```

---

### 告警统计汇总

`GET /api/v1/alerts/history/stats`

**返回**：
```json
{
  "total": 100,
  "by_type": {
    "sales_drop": 50,
    "low_inventory": 30,
    "conversion_drop": 20
  }
}
```

---

## 认证与请求头

### 内部 API 认证

- **Header**：`Authorization: Bearer <API_KEY>` + `X-API-Key: <API_KEY>`
- **健康检查** `/api/v1/health` 与 **OAuth 回调** 除外
- 前后端统一 `Config.API_KEY` 与 `VITE_API_KEY`

### 外部 API 认证

- Cookie 维持会话，需完整 `fxg.jinritemai.com` / `creator.douyin.com` Cookie
- 动态签名参数：`__token`, `msToken`, `a_bogus`, `verifyFp`, `fp`
- 常用头：`Accept`, `User-Agent`, `Cookie`, `Referer`
- 由后端 `services.fetcher._request` 统一注入

---

## 错误码

### 内部 API

| 码 | 说明 |
|----|------|
| 400 | 请求参数错误 |
| 401 | 未授权 / API_KEY 无效 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 502 | 上游服务异常 |
| 503 | 服务不可用（熔断/限流） |

### 外部 API (抖店/创作者中心)

- `40101` / `40301`：Cookie 失效或缺失
- `10008`：登录失效
- `10001010A`：订单风控

---

## 变更记录

- **2026-09-26 v1.2.1**：
  - 修正同步 API：`POST /api/v1/sync` 支持 `?async=true` 异步模式（Celery 任务队列）
  - 新增通用告警配置端点：`GET/POST /api/v1/alerts/config`
  - 修正告警历史与统计端点：`GET/DELETE /api/v1/alerts/history`、`GET /api/v1/alerts/history/stats`
  - 明确健康检查端点无需认证（`PUBLIC_ENDPOINTS` 白名单）
  - 补充告警配置、告警历史、同步 API 的详细请求/返回字段文档

- **2026-09-23 v1.2.0**：
  - 内部 API 前缀统一为 `/api/v1`
  - `GET /api/v1/creators/overview` 替代原 `POST /creators/overview/dashboard`
  - 所有相对路径不带前导 `/`，配合 `baseURL: '/api/v1'`
  - 前端鉴权头同时发送 `Authorization: Bearer` + `X-API-Key`

*历史版本已归档至 `archive_cleanup_20260923/legacy_docs/api_old/`*