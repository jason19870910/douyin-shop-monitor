# API 规范文档

> Douyin 监控平台统一 API 规范，包含内部后端 RESTful 接口与外部抖音电商后台接口。
> **版本**: 2.4.1
> **最后更新**: 2026-10-17
> **维护**: 项目核心团队

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
| POST | `/api/v1/compliance/:id/ignore` | 忽略合规问题 |
| POST | `/api/v1/compliance/:id/take-down` | 下架合规问题内容 |
| POST | `/api/v1/compliance/:id/restore` | 恢复已下架内容（2026-10-11 新增） |
| GET | `/api/v1/compliance/rules` | 合规规则列表 |
| POST | `/api/v1/compliance/rules` | 创建合规规则 |
| PUT | `/api/v1/compliance/rules/:id` | 更新合规规则 |
| DELETE | `/api/v1/compliance/rules/:id` | 删除合规规则 |
| GET | `/api/v1/compliance/rules/:id/history` | 规则检查历史 |
| POST | `/api/v1/compliance/check` | 触发合规检测（全量） |
| POST | `/api/v1/compliance/check/products` | **触发商品合规检测**（按 `applicable_to` 含 `product` 过滤规则，自动合并好货预览数据） |
| POST | `/api/v1/compliance/check/works` | **触发作品合规检测**（按 `applicable_to` 含 `work` 过滤规则） |
| GET | `/api/v1/compliance/export` | 导出合规报告 |
| POST | `/api/v1/external/haohuo/product/preview` | **好货商品在线预览**（返回详情图片、规格、价格/销量/协议配置、跳转链接） |
| GET | `/api/v1/version` | 版本信息 | 返回当前应用版本、git commit、构建时间和 API Key 内联状态 |
| GET | `/api/v1/changes` | 获取最近变更 | 返回最近 10 条 git commit 变更记录 |
| GET | `/api/v1/status` | 容器健康状态 | 检查 App/Redis/Frontend 三容器的健康状态 |
| GET | `/api/v1/env` | 环境变量配置 | 返回 VITE_API_KEY, VITE_DEV_MODE 等环境变量配置 |
| GET | `/api/v1/health/external` | **外部 API 状态检查（新增）** | 9 个外部 API（4 FXG + 2 Creator + 2 Creator收益 + 1 Compass）健康状态、响应时间、HTTP 状态码 |
| GET | `/api/v1/alerts/config` | 获取通用告警配置 |
| POST | `/api/v1/alerts/config` | 更新通用告警配置 |
| GET | `/api/v1/alerts/history` | 获取告警历史（支持分页、类型过滤） |
| DELETE | `/api/v1/alerts/history` | 清空告警历史 |
| GET | `/api/v1/alerts/history/stats` | 获取告警统计汇总 |
| GET | `/api/v1/alerts/dian/config` | 获取抖店告警配置 |
| POST | `/api/v1/alerts/dian/config` | 更新抖店告警配置 |
| GET | `/api/v1/alerts/douyin/config` | 获取抖音告警配置 |
| POST | `/api/v1/alerts/douyin/config` | 更新抖音告警配置 |
| POST | `/api/v1/sync/manual` | 手动触发同步（同步执行） |
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
| GET | `/api/v1/auth/profile` | 获取用户资料（需授权） |
| GET | `/api/v1/accounts` | 账号列表 |
| GET | `/api/v1/accounts/:id` | 账号详情 |
| POST | `/api/v1/accounts` | 创建账号 |
| PUT | `/api/v1/accounts/:id` | 更新账号 |
| DELETE | `/api/v1/accounts/:id` | 删除账号 |
| GET | `/api/v1/media/video-edit` | 视频编辑列表 |
| GET | `/api/v1/media/image-edit` | 图片编辑列表 |

---

## 首页数据需求（2026-10-15 更新：KPI 用独立统计端点，趋势/TOP 用聚合端点）

| 区块 | 使用的 API | 说明 |
|------|------------|------|
| **KPI：今日销售额、今日订单数** | `GET /api/v1/orders/stats` | 返回 `{all: {count, amount}, pay: {...}, cancel: {...}, sub_tab_count_map: {...}}`，单位**元** |
| **KPI：商品概览（总数/在售/库存/违规）** | `GET /api/v1/products/stats` | 返回 `{total, onsale, stock, violation}` 扁平格式 |
| **KPI：创作者与视频（达人/粉丝/视频/播放）** | `GET /api/v1/creators/overview?recent_days=7` | 返回 `{total_followers, total_videos, total_views, total_likes, ...}`，`data_source: "cache"` |
| **趋势图：销售趋势 (近7天)** | `GET /api/v1/dashboard/stats` | 返回 `sales_trend` 数组（[{date, amount}]） |
| **TOP 5：热销商品** | `GET /api/v1/dashboard/stats` | 返回 `top_products` 数组（含 `product_name`、`price_lower`(分)、`sales_today`） |
| 系统健康 | `GET /api/v1/health` | 返回 status、last_update、timestamp；数据来源从 dashboard/stats 的 data_source 字段获取 |
| 立即同步触发 | `POST /api/v1/sync/manual` | 手动触发同步（同步执行），成功后刷新健康状态 |
| 合规告警（可选） | `GET /api/v1/compliance/stats` + `GET /api/v1/compliance?status=pending&size=5` | 未处理高危违规数量与最近 5 条记录 |
| 告警配置开关 | `GET /api/v1/alerts/config`、`GET /api/v1/alerts/dian/config`、`GET /api/v1/alerts/douyin/config` | 是否启用各类预警 |
| Mock / 降级开关 | `GET /api/v1/mock/status` | 前端根据此决定是否展示占位数据 |
| 外部 API 健康状态 | `GET /api/v1/health/external` | **9 个外部 API**（4 FXG + 2 Creator + 2 Creator收益 + 1 Compass）健康标签、响应延迟、HTTP 状态码 |

> **架构说明**：KPI 类数据（销售额、订单数、商品数、创作者统计）使用**独立统计端点**，读取本地同步缓存聚合，响应快且不受外部 API 限流影响。趋势和 TOP 数据继续使用**聚合端点** `/dashboard/stats`，保持向后兼容。
## 内部 API 详细

### 健康检查

`GET /api/v1/health`

**无需认证**（在 `PUBLIC_ENDPOINTS` 白名单中）。

```json
{ "status": "healthy", "timestamp": "2026-10-14T18:25:31.050112+08:00", "last_update": "2026-10-14T18:24:47.450773+08:00" }
```

- `status`: 固定为 `healthy`
- `timestamp`: 当前服务器时间（ISO 8601，CST 时区 +08:00）
- `last_update`: 最近一次定时同步完成时间（来自 Redis `last_update` 键，ISO 8601，CST 时区 +08:00）

### 外部 API 状态检查

`GET /api/v1/health/external`

**无需认证**（在 `PUBLIC_ENDPOINTS` 白名单中）。

```json
{
  "data": {
    "endpoints": [
      {
        "name": "FXG-商品列表",
        "status": "healthy",
        "response_time_ms": 327,
        "status_code": 200,
        "url": "https://fxg.jinritemai.com/product/tproduct/list"
      },
      {
        "name": "FXG-商品统计",
        "status": "healthy",
        "response_time_ms": 233,
        "status_code": 200,
        "url": "https://fxg.jinritemai.com/product/tproduct/aggsProductCount"
      },
      {
        "name": "FXG-订单搜索",
        "status": "healthy",
        "response_time_ms": 111,
        "status_code": 200,
        "url": "https://fxg.jinritemai.com/api/order/searchlist"
      },
      {
        "name": "FXG-订单统计",
        "status": "healthy",
        "response_time_ms": 175,
        "status_code": 200,
        "url": "https://fxg.jinritemai.com/api/order/tabcnt"
      },
      {
        "name": "创作者中心-概览",
        "status": "healthy",
        "response_time_ms": 166,
        "status_code": 200,
        "url": "https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard"
      },
      {
        "name": "创作者中心-作品列表",
        "status": "healthy",
        "response_time_ms": 670,
        "status_code": 200,
        "url": "https://creator.douyin.com/janus/douyin/creator/pc/work_list"
      },
      {
        "name": "创作者中心-收益汇总",
        "status": "healthy",
        "response_time_ms": 156,
        "status_code": 200,
        "url": "https://creator.douyin.com/aweme/v1/creator/income/category/summary/"
      },
      {
        "name": "创作者中心-收益明细",
        "status": "healthy",
        "response_time_ms": 234,
        "status_code": 200,
        "url": "https://creator.douyin.com/aweme/v1/creator/income/category/detail/"
      },
      {
        "name": "指南针-店铺核心指标",
        "status": "healthy",
        "response_time_ms": 116,
        "status_code": 200,
        "url": "https://compass.jinritemai.com/compass_api/shop/common/homepage/core_index_v3"
      }
    ],
    "healthy_count": 9,
    "overall_status": "healthy",
    "total_count": 9
  },
  "error": null,
  "success": true
}
```

- `endpoints`: 9 个外部 API 的健康检查结果数组，每项包含：
  - `name`: 接口名称（中文描述）
  - `status`: 健康状态（`healthy`/`unhealthy`/`timeout`/`connection_error`/`error`）
  - `response_time_ms`: 响应延迟（毫秒）
  - `status_code`: HTTP 状态码
  - `url`: 实际访问的外部 API URL
- `healthy_count`: 健康接口计数
- `overall_status`: 总体状态（`healthy` 表示全部健康，`degraded` 表示部分不健康，`unhealthy` 表示全部不健康）
- `total_count`: 总检查接口数（当前为 9）

**使用示例**：

```typescript
// 前端使用
const { data: externalHealth, isLoading } = useExternalApiHealth({});
// externalHealth.data.endpoints[i].status 显示健康标签
// externalHealth.data.endpoints[i].response_time_ms 显示响应时间
// externalHealth.data.overall_status 显示总体状态
```

### 用户资料

`GET /api/v1/auth/profile`

**需认证**：需要有效的 `X-API-Key` 或 `Authorization: Bearer <API_KEY>`。

**返回**：用户资料对象（基于 OAuth 授权配置构建）。

```json
{
  "user_id": "user_12345678",
  "username": "douyin_user_abcd1234",
  "email": "",
  "phone": "",
  "role": "authorized_user",
  "create_time": "2026-10-11T03:14:02.732991",
  "last_login": "2026-10-11T03:14:02.732991",
  "open_id": "openid_xxx",
  "authorized": true,
  "scope": ["user_info"],
  "expires_in": 3600,
  "is_expired": false
}
```

**字段说明**：
- `user_id`: 基于 open_id 生成的用户标识
- `username`: 从 open_id 派生的用户名
- `role`: `user`（未授权）、`authorized_user`（有 user_info scope）、`admin`（管理员 scope）
- `open_id`: 抖音 OAuth 返回的 open_id
- `authorized`: 是否已完成 OAuth 授权
- `scope`: 授权范围数组
- `expires_in`: Token 剩余有效期（秒），0 表示永不过期或未设置
- `is_expired`: Token 是否已过期

### 仪表盘统计

`GET /api/v1/dashboard/stats`

返回：`total_sales_today/yesterday`、`total_revenue_today/yesterday`、`total_orders_today/yesterday`、`avg_conversion_rate`、`sales_trend`、`top_products`。

### 商品列表

`GET /api/v1/products?page=1&size=20&keyword=`

分页返回商品缓存数据。

### 商品统计（2026-10-15 重构：读取本地同步缓存聚合，不再直接调用外部 API）

`GET /api/v1/products/stats`

**数据源**：本地 Redis/文件缓存（由定时同步任务从外部 `/product/tproduct/list` 获取并写入），后端本地聚合统计三个标签页。

**返回字段**（标准化扁平格式）：
```json
{
  "total": 9,
  "onsale": 6,
  "stock": 3,
  "violation": 0
}
```

**字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `total` | int | 商品总数 | 9 |
| `onsale` | int | 在售商品数 | 6 |
| `stock` | int | 库存预警商品数 | 3 |
| `violation` | int | 违规/禁售商品数 | 0 |

> **重要变更（2026-10-15）**：原逻辑按 `tab` 参数单次查询外部 API 并透传返回，现改为无参数一次性聚合三个标签页（onSale/stock/violation）的本地缓存数据，返回扁平格式。前端 `ProductStatsData` 类型已同步更新。

### 外部商品列表

`GET /api/v1/products/external`

透传所有查询参数至外部 `/product/tproduct/list`。

**外部 API 实际参数**（从 `/product/tproduct/list` 映射而来）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | `0` | 0-based 页码索引 |
| `pageSize` | int | `20` | 每页数量，建议 10-20 |

**参数说明**：
- `page`: 从 0 开始，`page=0` 为第一页
- `pageSize`: 每页返回的产品数，当前默认 20（实际 API 返回可能因数据量而异，测试中 `pageSize=10` 返回 9 条，`pageSize=1` 返回 1 条）

**返回字段**（`data.list`）：
- `product_id` / `product_name` / `name`
- `sales_today` / `sales_yesterday`
- `conversion_rate` / `conversion_rate_yesterday`
- `inventory` / `status`
- `market_price` / `discount_price` / `price`
- `img` / `product_url`
- `shop_id`

> **已修复问题**：原代码使用 `pageSize=1` 导致每次仅获取 1 个产品，现已改为 `pageSize=20` 以获取完整列表。页码使用 0-based 索引，`page=0` 为第一页。

### 订单统计（2026-10-15 重构：读取本地同步缓存聚合，不再直接调用外部 API）

`GET /api/v1/orders/stats`

**数据源**：本地 Redis/文件缓存（由定时同步任务从外部 `/api/order/searchlist` 获取并写入），后端本地聚合统计。

**返回字段**（标准化格式，单位：**元 yuan**）：
```json
{
  "all": { "count": 1, "amount": 62.02 },
  "pay": { "count": 1, "amount": 62.02 },
  "cancel": { "count": 0, "amount": 0 },
  "sub_tab_count_map": {
    "closed": { "count": 1, "amount": 62.02 },
    "cancel": { "count": 0, "amount": 0 },
    "exp_ship": { "count": 0, "amount": 0 },
    ...
  }
}
```

**字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `all.count` | int | 总订单数 | 1 |
| `all.amount` | float | 总订单金额（元） | 62.02 |
| `pay.count` | int | 已支付订单数 | 1 |
| `pay.amount` | float | 已支付订单金额（元） | 62.02 |
| `cancel.count` | int | 已取消订单数 | 0 |
| `cancel.amount` | float | 已取消订单金额（元） | 0 |
| `sub_tab_count_map` | object | 子标签详细统计（count+amount） | 见上方示例 |

> **重要变更（2026-10-15）**：外部 API 返回金额单位为**分**（如 `pay_amount: 6202`），内部 stats 端点已修正为 `/ 100` 转为**元**返回。前端 `formatCurrency` 可直接使用，无需额外除以 100。

### 创作者概览（2026-10-15 重构：读取本地同步缓存聚合，不再直接调用外部 API）

`GET /api/v1/creators/overview?recent_days=7`

**数据源**：本地 Redis/文件缓存（由定时同步任务从外部 `/janus/douyin/creator/data/overview/dashboard` 和 `/janus/douyin/creator/pc/work_list` 获取并写入），后端本地聚合统计。

**返回字段**（标准化格式）：
```json
{
  "recent_days": 7,
  "total_followers": 1160,
  "total_videos": 14,
  "total_views": 188,
  "total_likes": 12,
  "total_comments": 3,
  "total_shares": 1,
  "recent_followers_gain": 5,
  "recent_view": 188,
  "recent_like": 12,
  "data_source": "cache"
}
```

**字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `recent_days` | int | 统计天数 | 7 |
| `total_followers` | int | 总粉丝数 | 1160 |
| `total_videos` | int | 总视频数 | 14 |
| `total_views` | int | 总播放量 | 188 |
| `total_likes` | int | 总点赞数 | 12 |
| `total_comments` | int | 总评论数 | 3 |
| `total_shares` | int | 总分享数 | 1 |
| `recent_followers_gain` | int | 近期净增粉 | 5 |
| `recent_view` | int | 近期播放量 | 188 |
| `recent_like` | int | 近期点赞数 | 12 |
| `data_source` | string | 数据来源标识 | `cache` |

> **重要变更（2026-10-15）**：原逻辑直接调用外部 API 并解析 `metrics` 数组，现改为读取本地缓存聚合作品列表统计（粉丝数取概览缓存，视频/播放/点赞/评论/分享累加作品列表）。返回格式新增 `data_source: "cache"` 标识。

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

**执行方式**：手动触发同步由 app 容器**同步执行**，无独立任务队列；定时同步由 app 容器内置调度器（schedule + threading）按 `SCHEDULE_INTERVAL_MINUTES`（默认 60 分钟）触发。原 `?async=true` 异步模式（Celery 任务队列）已随 3 容器架构精简移除。

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
| 收益概览 | GET | `/api/v1/external/creator/income/summary` | 创作者平台收益汇总（分类汇总：day1/7/30，系统级接口） |
| 收益趋势 | GET | `/api/v1/external/creator/income/detail` | 创作者平台收益趋势/明细（chart坐标 + 每日收入列表，history_day_count=7） |
|  compass 经营概况 | GET | `/api/v1/external/compass/shop/core-index` | compass店铺首页核心指标（系统级接口，15核心营业数据） |
| 好货商品预览 | POST | `/api/v1/external/haohuo/product/preview` | 好货平台商品在线预览（详情图片、规格、价格/销量/协议配置、跳转链接，系统级接口） |

---

## 外部 API 详细

### 商品统计 `/product/tproduct/aggsProductCount`

**方法**：GET

**完整 URL**：`https://fxg.jinritemai.com/product/tproduct/aggsProductCount`

**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `tab` | string | 是 | `onSale` | 筛选标签：`onSale`(在售)/`draft`(草稿)/`audit`(审核中)/`violation`(违规) |
| `appid` | int | 是 | `1` | 应用 ID |

**签名参数**（自动注入，需有效）：
- `__token` (TOKEN)
- `msToken` (MS_TOKEN)
- `a_bogus` (实时计算)
- `verifyFp` (VERIFY_FP)
- `fp` (FP)

**固定参数**：
- `_bid=ffa_product`
- `aid=FXG_SHOP_ID` (4272)

**请求头**：
```
User-Agent: Config.USER_AGENT
Referer: https://fxg.jinritemai.com/product/tproduct/list
Origin: https://fxg.jinritemai.com
Cookie: FXG_COOKIES
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
X-Requested-With: XMLHttpRequest
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Cache-Control: no-cache
Pragma: no-cache
Priority: u=1, i
Sec-Ch-Ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
```

**返回示例**：
```json
{
  "code": 0,
  "data": {
    "audit": 0,
    "draft": 0,
    "forbidden": 0,
    "onsale": 6,
    "sell_out_new": 0,
    "unpass": 0,
    "unpass_new": 0
  }
}
```

**字段详细说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `code` | int | 成功标识，0 表示成功 | 0 |
| `data.audit` | int | 审核中商品数 | 0 |
| `data.draft` | int | 草稿箱商品数 | 0 |
| `data.forbidden` | int | 违规/禁售商品数 | 0 |
| `data.onsale` | int | **在售商品数（核心指标）** | 6 |
| `data.sell_out_new` | int | 售罄商品数 | 0 |
| `data.unpass` | int | 审核不通过数 | 0 |
| `data.unpass_new` | int | 新版审核不通过数 | 0 |

---

### 商品列表 `/product/tproduct/list`

**方法**：GET

**完整 URL**：`https://fxg.jinritemai.com/product/tproduct/list`

**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `page` | int | 是 | `1` | 页码 |
| `pageSize` | int | 是 | `20` | 每页数量 |
| `tab` | string | 是 | `onSale` | 筛选标签 |
| `appid` | int | 是 | `1` | 应用 ID |

**签名参数**（自动注入，需有效）：
- `__token` (TOKEN)
- `msToken` (MS_TOKEN)
- `a_bogus` (实时计算)
- `verifyFp` (VERIFY_FP)
- `fp` (FP)

**固定参数**：
- `_bid=ffa_product`
- `aid=FXG_ORDER_AID` (4272)
- `_lid=FXG_PRODUCT_LID` (829906029528)

**请求头**：同上（商品统计）

**返回示例**：
```json
{
  "code": 0,
  "data": []
}
```

**⚠️ 实际结构差异（2026-10-08 验证）**：
- 响应顶层 `data` 直接是**数组**，而非旧文档的对象 `{ list: [], total: 0 }`
- 当前无商品数据，返回空数组 `[]`

**预期商品对象字段（基于接口规范）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `product_id` | string | 商品 ID |
| `name` / `product_name` | string | 商品名称 |
| `sales_today` | int | 今日销量 |
| `market_price` | float | 市场价（元） |
| `discount_price` | float | 折扣价/售价（元） |
| `img` | string | 主图 URL |
| `product_url` | string | 商品详情页 URL |
| `shop_id` | string | 店铺 ID |
| `status` | int | 商品状态 |
| `create_time` | int | 创建时间戳 |

**分页信息**：当前响应无 `page`、`size`、`total` 字段，需通过 `pageSize` 和返回数组长度推断

---

### 订单统计 `/api/order/tabcnt`

**方法**：GET

**完整 URL**：`https://fxg.jinritemai.com/api/order/tabcnt`

**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `tabcnt_version` | string | 是 | `v1` | 版本参数 |
| `tab` | string | 是 | `all` | 标签：`all`/`pay`/`cancel` 等 |
| `appid` | int | 是 | `1` | 应用 ID |

**签名参数**（自动注入，需有效）：
- `__token` (TOKEN)
- `msToken` (MS_TOKEN)
- `a_bogus` (实时计算)
- `verifyFp` (VERIFY_FP)
- `fp` (FP)

**固定参数**：
- `_bid=ffa_order`
- `aid=FXG_ORDER_AID` (4272)
- `_lid=FXG_ORDER_LID` (550078945638)

**请求头**：
```
User-Agent: Config.USER_AGENT
Referer: https://fxg.jinritemai.com/ffa/morder/order/list
Origin: https://fxg.jinritemai.com
Cookie: FXG_COOKIES
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
X-Requested-With: XMLHttpRequest
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Cache-Control: no-cache
Pragma: no-cache
Priority: u=1, i
Sec-Ch-Ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
```

**返回示例**：
```json
{
  "code": 0,
  "data": {
    "all": 1,
    "closed": 1,
    "unpaid": 0,
    "on_delivery": 0,
    "received": 0,
    "handling": 0,
    "stock_up": 0,
    "exp_ship": 0,
    "ship_delay": 0,
    "in_aftersale": 0,
    "have_aftersale": 0,
    "cnt_report": {
      "warning": "0",
      "ship_exception": "0"
    },
    "sub_tab_count_map": {
      "all": {"count": "1", "text": "全部"},
      "exp_ship": {"count": "0", "text": "待发货"},
      "ship_delay": {"count": "0", "text": "发货延迟"},
      "handling": {"count": "0", "text": "处理中"},
      "stock_up": {"count": "0", "text": "备货中"},
      "on_delivery": {"count": "0", "text": "配送中"},
      "received": {"count": "0", "text": "已收货"},
      "unpaid": {"count": "0", "text": "待付款"},
      "closed": {"count": "1", "text": "已完成"},
      "cancel": {"count": "0", "text": "已取消"},
      "refund": {"count": "0", "text": "退款中"},
      "aftersale": {"count": "0", "text": "售后中"}
    }
  }
}
```

**字段详细说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `code` | int | 成功标识 | 0 |
| `data.all` | int | **全部订单总数（核心指标）** | 1 |
| `data.closed` | int | 已完成/关闭订单数 | 1 |
| `data.unpaid` | int | 待付款订单数 | 0 |
| `data.on_delivery` | int | 配送中订单数 | 0 |
| `data.received` | int | 已收货订单数 | 0 |
| `data.handling` | int | 处理中订单数 | 0 |
| `data.stock_up` | int | 备货中订单数 | 0 |
| `data.exp_ship` | int | 待发货订单数 | 0 |
| `data.ship_delay` | int | 发货延迟订单数 | 0 |
| `data.in_aftersale` | int | 售后中订单数 | 0 |
| `data.have_aftersale` | int | 有售后记录的订单数 | 0 |
| `data.cnt_report.warning` | string | 预警单数 | "0" |
| `data.cnt_report.ship_exception` | string | 物流异常单数 | "0" |
| `data.sub_tab_count_map` | object | 子标签详细计数映射（含 count 文本） | 见上方示例 |

---

### 订单列表 `/api/order/searchlist` ⚠️ **关键修复**

**方法**：GET

**完整 URL**：`https://fxg.jinritemai.com/api/order/searchlist`

**⚠️ 重要发现**：该端点**不需要** `a_bogus`、`msToken` 签名参数！仅需 Cookie 认证即可。
- **带过期签名请求** → 返回 `10001010A` (SIGNATURE_ERROR)
- **去掉 a_bogus/msToken** → 返回 `code: 0` 成功
- **代码实现**：`_request()` 新增 `skip_sign: bool = False` 参数，`_fetch_orders_from_api()` 调用时传 `skip_sign=True`

**Query 参数（仅保留有效参数）**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `page` | int | 是 | `0` | 页码（从 0 开始） |
| `pageSize` | int | 是 | `10` | 每页数量 |
| `order_by` | string | 是 | `create_time` | 排序字段 |
| `order` | string | 是 | `desc` | 排序方向 |
| `tab` | string | 是 | `all` | 订单标签 |
| `appid` | int | 是 | `1` | 应用 ID |
| `__token` | string | 是 | `3b2d8e84e606...` | 稳定 Token (TOKEN，长效) |
| `verifyFp` | string | 是 | `verify_muxpd4sm_...` | 设备指纹 (VERIFY_FP，长效) |
| `fp` | string | 是 | `verify_muxpd4sm_...` | 设备指纹 (FP，长效) |
| `compact_time[select]` | string | 否 | `create_time_start,create_time_end` | 时间筛选模式 |
| `create_time_start` | int | 否 | `1788763712` | 开始时间戳 |
| `create_time_end` | int | 否 | `1791355712` | 结束时间戳 |

**固定参数**：
- `_bid=ffa_order`
- `aid=FXG_ORDER_AID` (4272)
- `_lid=606316310312` （实测有效值，不同于配置默认值 550078945638）

**参数策略说明**：
- **长效参数（显式传递）**：`__token`、`verifyFp`、`fp` —— 从配置读取，有效期长（天级），直接加入请求
- **强时效参数（跳过注入）**：`msToken`、`a_bogus` —— 有效期极短（分钟级），通过 `skip_sign=True` 禁止 `_request` 自动注入，避免导致 `10001010A` 签名错误
- **实测有效 `_lid`**：使用 `606316310312`（用户浏览器抓包值），而非配置默认值

**❌ 不需要的参数**（会导致失败）：
- `msToken` (MS_TOKEN) — 时效性极强，几分钟失效
- `a_bogus` (A_BOGUS) — 时效性极强，几分钟失效

**优化后请求头（2026-10-07 更新，模拟浏览器指纹以获取丰富数据）**：
```
Accept: application/json, text/plain, /*
Accept-Language: zh-CN,zh;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
Priority: u=1, i
User-Agent: Config.USER_AGENT (Chrome 150)
Referer: https://fxg.jinritemai.com/ffa/order
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Sec-Ch-Ua: "Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Cache-Control: no-cache
Pragma: no-cache
Cookie: FXG_COOKIES
```

**关键差异说明**：
- `Referer` 指向具体订单页面 (`/ffa/order`) 而非首页
- 完整的 `Sec-Fetch-*` 与 `Sec-Ch-Ua-*` 指纹头，通过浏览器反爬检测
- `Priority: u=1, i` 表示高优先级资源请求
- `Accept-Encoding` 包含 `zstd` 支持现代压缩

**返回示例（浏览器实测返回丰富字段）**：
```json
{
  "st": 0,
  "code": 0,
  "msg": "",
  "data": [
    {
      "shop_order_id": "6952528259545240685",
      "order_status": 3,
      "create_time": 1744624277862,
      "update_time": 1744624277862,
      "pay_time": 1744624277862,
      "product_item": [
        {
          "product_id": "123456",
          "product_name": "海盐嘭润保湿沐浴露",
          "spec_name": "默认规格",
          "count": 1,
          "price": 29.9,
          "img": "https://..."
        }
      ],
      "receiver_info": {
        "name": "张三",
        "phone": "138****8888",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "address": "科技园路1号",
        "full_address": "广东省深圳市南山区科技园路1号"
      },
      "operation_actions": [
        {"name": "发货", "action_id": "ship"},
        {"name": "退款", "action_id": "refund"}
      ],
      "total_amount": 29.9,
      "pay_amount": 29.9,
      "freight_amount": 0,
      "buyer_memo": "",
      "shop_id": "257675707"
    }
  ],
  "page": 0,
  "size": 10,
  "total": 1,
  "order": "desc",
  "order_by": "create_time"
}
```

**⚠️ 实测完整字段列表（97 字段，2026-10-08 验证）**：
单个订单对象包含以下关键字段分组：

**基础标识与状态**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `shop_order_id` | string | 店铺订单号（主键，如 `"6952528259545240685"`） |
| `order_id` | string | 平台订单号（有时为空字符串） |
| `order_status` | int | 订单状态码（3=待发货，4=已完成等） |
| `order_status_info` | object | 状态描述对象（含文本、颜色等 UI 信息） |
| `order_status_desc` | string | 状态文本描述 |

**金额信息（单位：分）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `pay_amount` | int | 实付金额（如 `6202` = ¥62.02） |
| `actual_receive_amount` | string | 商家实收金额（格式化，如 `"¥62.02"`） |
| `actual_receive_amount_int` | int | 商家实收金额（分） |
| `total_post_amount` | int | 邮费 |
| `promotion_amount` | int | 优惠金额 |
| `total_amount` | float | 订单总金额（元） |
| `product_amount` | float | 商品金额（元） |

**时间戳（毫秒/秒混合）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `create_time` | int | 下单时间（毫秒，如 `1777760073000`） |
| `pay_time` | int | 支付时间 |
| `update_time` | int | 更新时间 |
| `exp_ship_time` | int | 预期发货时间 |
| `create_time_str` | string | 格式化下单时间 |
| `pay_time_str` | string | 格式化支付时间 |

**商品明细**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `product_item` | array | **核心：商品列表数组** |
| `product_count` | int | 商品种类数 |
| `product_item[].product_id` | string | 商品 ID |
| `product_item[].product_name` | string | 商品名称 |
| `product_item[].spec_name` | string | 规格名称 |
| `product_item[].count` | int | 购买数量 |
| `product_item[].price` | float | 单价（元） |
| `product_item[].img` | string | 商品主图 URL |

**买家信息**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `user_nickname` | string | 脱敏买家昵称（如 `"东*"`） |
| `user_id` | string | 脱敏用户 ID |
| `buyer_memo` | string | 买家备注 |
| `buyer_words` | string | 买家留言 |

**收货信息（详细）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `receiver_info` | object | **详细收货人信息对象** |
| `receiver_info.post_receiver` | string | 收货人姓名（脱敏，如 `"郭*"`） |
| `receiver_info.post_tel` | string | 电话（脱敏，如 `"1**********"`） |
| `receiver_info.post_addr` | object | 省/市/区/街道完整地址对象 |
| `receiver_info.post_addr.province_name` | string | 省份 |
| `receiver_info.post_addr.city_name` | string | 城市 |
| `receiver_info.post_addr.district_name` | string | 区县 |
| `receiver_info.post_addr.street_name` | string | 街道 |
| `receiver_info.post_addr.detail` | string | 详细地址 |

**操作动作（后台可用操作）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `operation_actions` | array | 可用操作列表（发货、退款、改价等） |
| `operation_actions[].name` | string | 操作名称（如 "发货"、"退款"） |
| `operation_actions[].action_id` | string | 操作标识（如 "ship"、"refund"） |
| `action_map` | object | 操作映射表（联系买家、备注、修改地址等） |

**物流信息**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `way_bill_url` | string | 运单链接 |
| `latest_logistic_info` | object | 最新物流轨迹对象 |
| `logistics_company` | string | 物流公司名称 |
| `tracking_no` | string | 快递单号 |

**其他**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `remark` | string | 商家备注 |
| `shop_id` | string | 店铺 ID |
| `service_info` | object | 售后服务信息 |
| `promotion_info` | array | 优惠详情数组 |

**分页信息（顶层）**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `page` | int | 当前页码（从 0 开始） |
| `size` | int | 每页数量 |
| `total` | int | 总记录数 |
| `order` | string | 排序方向 (`desc`/`asc`) |
| `order_by` | string | 排序字段 (`create_time`) |

---

### 创作者概览 `/janus/douyin/creator/data/overview/dashboard`

**方法**：POST

**完整 URL**：`https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard`

**Body 参数 (JSON)**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `recent_days` | int | 是 | `7` | 统计天数 |

**签名参数**：创作者中心暂**不自动注入签名**，依赖 Cookie 中的 `x_tt_token` 等字段。

**请求头**：
```
User-Agent: Config.USER_AGENT
Referer: https://creator.douyin.com/
Cookie: CREATOR_COOKIES (字符串)
Accept: application/json, text/plain, */*
Content-Type: application/json
```

**⚠️ 实际返回格式（2026-10-08 验证）**：`metrics` 数组，非旧文档的 `data` 对象。每个 metric 含 `trends` 字段（7 天每日趋势数据）。

**返回示例**：
```json
{
  "status_code": 0,
  "metrics": [
    {"english_metric_name": "total_fans_cnt", "metric_value": 1166, "metric_name": "粉丝", "trends": [...]},
    {"english_metric_name": "publish_cnt", "metric_value": 0, "metric_name": "投稿量", "trends": [...]},
    {"english_metric_name": "play_cnt", "metric_value": 47, "metric_name": "播放量", "trends": [...]},
    {"english_metric_name": "digg_cnt", "metric_value": 2, "metric_name": "作品点赞", "trends": [...]},
    {"english_metric_name": "share_count", "metric_value": 0, "metric_name": "作品分享", "trends": [...]},
    {"english_metric_name": "comment_cnt", "metric_value": 0, "metric_name": "作品评论", "trends": [...]},
    {"english_metric_name": "net_fans_cnt", "metric_value": -3, "metric_name": "净增粉丝", "trends": [...]},
    {"english_metric_name": "cancel_fans_cnt", "metric_value": 3, "metric_name": "取关粉丝", "trends": [...]},
    {"english_metric_name": "homepage_view_cnt", "metric_value": 10, "metric_name": "主页访问", "trends": [...]},
    {"english_metric_name": "avg_view_second", "metric_value": 3.23, "metric_name": "平均播放时长", "trends": [...]},
    {"english_metric_name": "completion_rate_5s", "metric_value": 0.1, "metric_name": "5秒完播率", "trends": [...]},
    {"english_metric_name": "bounce_rate_2s", "metric_value": 0.67, "metric_name": "2秒跳出率", "trends": [...]},
    {"english_metric_name": "cover_click_ratio", "metric_value": null, "metric_name": "封面点击率", "trends": [...]}
  ],
  "status_msg": ""
}
```

**Metrics 完整字段表（13 项）**：
| # | `english_metric_name` | `metric_name` | `metric_value` | 类型 | 说明 |
|---|----------------------|---------------|----------------|------|------|
| 1 | `total_fans_cnt` | 粉丝 | **1166** | int | **总粉丝数（核心指标）** |
| 2 | `publish_cnt` | 投稿量 | **0** | int | 总视频/投稿数 |
| 3 | `play_cnt` | 播放量 | **47** | int | 总播放量 |
| 4 | `digg_cnt` | 作品点赞 | **2** | int | 总点赞数 |
| 5 | `share_count` | 作品分享 | **0** | int | 总分享数 |
| 6 | `comment_cnt` | 作品评论 | **0** | int | 总评论数 |
| 7 | `net_fans_cnt` | 净增粉丝 | **-3** | int | 近期净增粉（负数=掉粉） |
| 8 | `cancel_fans_cnt` | 取关粉丝 | **3** | int | 取关数 |
| 9 | `homepage_view_cnt` | 主页访问 | **10** | int | 主页访问量 |
| 10 | `avg_view_second` | 平均播放时长 | **3.23** | float | 平均播放秒数 |
| 11 | `completion_rate_5s` | 5秒完播率 | **0.1** | float | 10%（0-1 之间） |
| 12 | `bounce_rate_2s` | 2秒跳出率 | **0.67** | float | 67%（0-1 之间） |
| 13 | `cover_click_ratio` | 封面点击率 | `null` | float/null | 无数据时为 null |

**Trends 每日趋势结构**（每个 metric 含 7 天数据）：
| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期 (YYYY-MM-DD) |
| `douyin_value` | int/float | 抖音端数值 |
| `xigua_value` | int/float | 西瓜视频端数值 |
| `yumme_value` | int/float | 火山/皮皮虾端数值 |
| `change_rate` | float | 环比变化率 |
| `change_value` | int/float | 环比变化绝对值 |

**字段映射（内部 `_fetch_creator_overview_from_api()` 实现）**：
| 内部标准字段 | 外部 `english_metric_name` | 备注 |
|-------------|---------------------------|------|
| `total_followers` | `total_fans_cnt` | 兼容旧 `follow_cnt` |
| `total_videos` | `publish_cnt` | 兼容旧 `aweme_cnt` |
| `total_views` | `play_cnt` | 新增字段 |
| `total_likes` | `digg_cnt` | 兼容旧 `like_cnt` |
| `total_comments` | `comment_cnt` | 新增字段 |
| `total_shares` | `share_count` | 兼容旧 `share_cnt` |
| `recent_followers_gain` | `net_fans_cnt` | 兼容旧 `net_followers_gain` |
| `recent_view` | `play_cnt` | 兼容旧字段名 |
| `recent_like` | `digg_cnt` | 兼容旧字段名 |

---

### 创作者作品 `/janus/douyin/creator/pc/work_list`

**方法**：GET

**完整 URL**：`https://creator.douyin.com/janus/douyin/creator/pc/work_list`

**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `status` | string | 是 | `0` | 状态：`0`(全部)/`1`(已发布) |
| `count` | string | 是 | `12` | 每页数量 |
| `max_cursor` | string | 是 | `0` | 分页游标 |
| `scene` | string | 是 | `star_atlas` | 场景 |
| `device_platform` | string | 是 | `android` | 设备平台 |
| `aid` | int | 是 | `1128` | 应用 ID (CREATOR_WORK_AID) |

**签名参数**：暂不自动注入，依赖 Cookie。

**请求头**：
```
User-Agent: Config.USER_AGENT
Referer: https://creator.douyin.com/creator-micro/content/manage
Accept: application/json, text/plain, */*
Cookie: CREATOR_COOKIES (字符串)
```

**⚠️ 关键差异**：创作者中心作品列表**必须使用 `cookies` 参数传递字典**（`requests` 的 `cookies=`），而非 `Cookie` Header 字符串。

**⚠️ 实际返回格式（2026-10-08 验证）**：`aweme_list` 数组，包含完整的视频详情（`statistics`、`video`、`author`、`create_time` 等）。

**返回示例**：
```json
{
  "status_code": 0,
  "aweme_list": [
    {
      "aweme_id": "7622892105911864616",
      "desc": "",
      "statistics": {"play_count": 283, "digg_count": 20, "comment_count": 2, "share_count": 0},
      "author": {"uid": "...", "nickname": "创作者名"},
      "create_time": 1791355712,
      "video": {"cover": {"url_list": ["https://..."]}, "play_addr": {"url_list": ["https://..."]}}
    }
  ],
  "total": 12
}
```

**⚠️ 实测完整字段列表（aweme_list 单元素 40+ 字段，2026-10-08 验证）**：
| 分组 | 关键字段 | 类型/示例 | 说明 |
|------|----------|-----------|------|
| **基础标识** | `aweme_id` | string | 作品唯一 ID |
| | `item_id` | string | 同 aweme_id |
| | `group_id` | string | 分组 ID |
| | `desc` | string | 视频标题/描述 |
| | `create_time` | int | 发布时间戳（秒） |
| | `duration` | int | 时长（毫秒，如 `4064`） |
| **统计数据** | `statistics.play_count` | int | 播放数（如 `283`） |
| | `statistics.digg_count` | int | 点赞数（如 `20`） |
| | `statistics.comment_count` | int | 评论数（如 `2`） |
| | `statistics.share_count` | int | 分享数（如 `0`） |
| | `statistics.collect_count` | int | 收藏数 |
| | `statistics.forward_count` | int | 转发数 |
| **作者信息** | `author.nickname` | string | 创作者昵称 |
| | `author.uid` | string | 用户 ID |
| | `author.follower_count` | int | 粉丝数 |
| | `author.aweme_count` | int | 总作品数 |
| **视频详情** | `video.cover.url_list` | array | 封面图 URL 列表 |
| | `video.play_addr.url_list` | array | 播放地址 URL 列表 |
| | `video.width/height` | int | 分辨率（1280×720） |
| | `video.duration` | int | 时长毫秒 |
| | `video.has_watermark` | bool | 是否有水印 |
| | `video.ratio` | string | 清晰度标识（如 `"720p"`） |
| | `video.bit_rate` | int | 码率 |
| **状态与权限** | `status_value` | int | 状态值（如 `102`） |
| | `status.allow_comment` | bool | 允许评论 |
| | `status.is_private` | bool | 是否私密 |
| | `status.is_delete` | bool | 是否删除 |
| **风控/标签** | `risk_infos` | array | 风控提示（如 `"作品含 AI 生成内容"`） |
| | `video_labels` | array | 视频标签 |
| | `commerce_info` | object | 电商带货信息（如有） |
| **其他** | `region` | string | 地区标识 |
| | `music_info` | object | 背景音乐信息 |
| | `challenge_info_list` | array | 话题挑战信息 |
|
### 收益概览 `/api/v1/external/creator/income/summary`
**
**方法**：GET
**
**完整 URL**：`https://creator.douyin.com/aweme/v1/creator/income/category/summary/`
**
**概述**：从抖音创作者平台获取收益分类汇总数据，返回 day1/7/30 日の收入概览以及 total_balance 和 category_list 分类明细。这是一个**系统级接口**，用于前端版本控制页面的 "环境配置" 标签页和 "系统工具" 板块。
**
**请求头**：
```
User-Agent: Config.USER_AGENT (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36)
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Pragma: no-cache
Referer: https://creator.douyin.com/creator-micro/revenue/center?type=1
Cookie: CREATOR_COOKIES (完整域名 Cookie 字符串)
```
**
**返回示例**：
```json
{
  "status_code": 0,
  "status_msg": "",
  "data_update_status": 2,
  "day1_income_summary": {
    "category_list": [
      {"category_id": "ecom_merchant", "name": "开店收入", "today_total_income": 0, "yesterday_total_income": 62404}
    ],
    "data_update_status": 2,
    "has_link_relative": true,
    "history_total_income": 63146,
    "link_relative": 0
  },
  "day7_income_summary": {
    "category_list": [
      {"category_id": "business_task", "name": "商单任务", "today_total_income": 0, "yesterday_total_income": 742}
    ],
    "data_update_status": 2,
    "has_link_relative": true,
    "history_total_income": 63146,
    "link_relative": 0
  },
  "day30_income_summary": {
    "category_list": [],
    "data_update_status": 2,
    "has_link_relative": true,
    "history_total_income": 63146,
    "link_relative": 0
  },
  "extra": {"now": 1791855089000},
  "has_today_total_income": false,
  "today_total_income": 0,
  "total_balance": 71,
  "total_income_summary": {
    "category_list": [
      {"category_id": "ecom_merchant", "data_update_desc": "每天24点前更新昨日收益", "data_update_status": 2, "has_link_relative": true, "has_today_total_income": false, "icon": "", "light_color_icon": "", "link_relative": 0, "name": "开店收入", "today_total_income": 0, "yesterday_total_income": 62404},
      {"category_id": "business_task", "data_update_desc": "每天12点前更新昨日收益", "data_update_status": 2, "has_link_relative": true, "has_today_total_income": false, "icon": "https://p3.douyinpic.com/aweme-server-static-resource/first_business_task.png~tplv-noop.image", "light_color_icon": "https://p3.douyinpic.com/aweme-server-static-resource/second_business_task.png~tplv-noop.image", "link_relative": 0, "name": "商单任务", "today_total_income": 0, "yesterday_total_income": 742}
    ],
    "data_update_status": 2,
    "fail_reason": null,
    "history_total_income": 63146,
    "link_relative": 0
  },
  "fail_reason": null
}
```
**
**返回字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `status_code` | int | 成功标识，0 表示成功 | 0 |
| `status_msg` | string | 状态消息 | "" |
| `data_update_status` | int | 数据更新状态（0=未更新，2=已更新） | 2 |
| `day1_income_summary.category_list` | array | day1（今日）收入分类列表 | `[{"category_id":"ecom_merchant","name":"开店收入","today_total_income":0,"yesterday_total_income":62404}]` |
| `day1_income_summary.history_total_income` | int | day1 历史总收入 | 63146 |
| `day1_income_summary.link_relative` | int | day1 环比链接相对值 | 0 |
| `day7_income_summary.category_list` | array | day7（近7天）收入分类列表 | `[{"category_id":"business_task","name":"商单任务","today_total_income":0,"yesterday_total_income":742}]` |
| `day7_income_summary.history_total_income` | int | day7 历史总收入 | 63146 |
| `day30_income_summary.category_list` | array | day30（近30天）收入分类列表 | `[]` (无数据) |
| `extra.now` | int | 服务器时间戳（毫秒） | 1791855089000 |
| `has_today_total_income` | bool | 是否有今日总收入 | false |
| `today_total_income` | number | 今日总收入 | 0 |
| `total_balance` | int | 账户余额 | 71 |
| `total_income_summary.category_list` | array | 收益总计分类列表 | 2 项：开店收入、商单任务 |
| `total_income_summary.history_total_income` | int | 总历史收入 | 63146 |
| `total_income_summary.link_relative` | int | 总环比链接相对值 | 0 |
| `fail_reason` | string | 失败原因（无错误时为 null） | null |
**
**使用示例**：
```typescript
// 前端 useApi hook 调用
const { data: incomeSummary, isLoading } = useApi('/api/v1/external/creator/income/summary');
// 通过 incomeSummary.data.total_income_summary 获取总收益
// 通过 incomeSummary.data.day7_income_summary 获取近7天概览
```
**
**异常处理**：
- `status_code: -1` - 连接错误（无法抓取 Creator 平台）
- `status_code: -2` - 请求超时
- `status_code: -3` - 请求参数/格式错误
- `status_code: -99` - 未知异常

---
### 收益趋势 `/api/v1/external/creator/income/detail`
**
**方法**：GET
**
**完整 URL**：`https://creator.douyin.com/aweme/v1/creator/income/category/detail/`
**
**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `history_day_count` | int | 是 | `7` | 获取最近 N 天的收入数据（目前固定为 7） |
**
**概述**：从抖音创作者平台获取收益明细和趋势图数据，返回 `chart_coordinate_list`（用于绘制趋势图）和 `income_item_list`（每日收入明细 [{amount, name, timestamp}]）。这是一个**系统级接口**，用于前端版本控制页面的 "收益趋势" 标签页。
**
**请求头**：
```
User-Agent: Config.USER_AGENT (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36)
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Pragma: no-cache
Referer: https://creator.douyin.com/creator-micro/revenue/center?type=1
Cookie: CREATOR_COOKIES (完整域名 Cookie 字符串)
```
**
**返回示例**：
```json
{
  "status_code": 0,
  "status_msg": "",
  "chart_coordinate_list": [
    {"x": "2026-10-05", "y": 1240},
    {"x": "2026-10-04", "y": 1080},
    {"x": "2026-10-03", "y": 950},
    {"x": "2026-10-02", "y": 870},
    {"x": "2026-10-01", "y": 760},
    {"x": "2026-09-30", "y": 650},
    {"x": "2026-09-29", "y": 580}
  ],
  "income_item_list": [
    {"amount": 1240, "name": "2026-10-05", "timestamp": 1791302400},
    {"amount": 1080, "name": "2026-10-04", "timestamp": 1791216000},
    {"amount": 950, "name": "2026-10-03", "timestamp": 1791139200},
    {"amount": 870, "name": "2026-10-02", "timestamp": 1791052800},
    {"amount": 760, "name": "2026-10-01", "timestamp": 1790966400},
    {"amount": 650, "name": "2026-09-30", "timestamp": 1790880000},
    {"amount": 580, "name": "2026-09-29", "timestamp": 1790793600}
  ],
  "extra": {"now": 1791855089000}
}
```
**
**返回字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `status_code` | int | 成功标识，0 表示成功 | 0 |
| `status_msg` | string | 状态消息 | "" |
| `chart_coordinate_list` | array | 趋势图坐标点数组 [{x, y}]，用于 ECharts/图表绘制 | `[{"x":"2026-10-05","y":1240}, ...]` |
| `income_item_list` | array | 收入明细列表 [{amount, name, timestamp}]，每日收入记录 | `[{"amount":1240,"name":"2026-10-05","timestamp":1791302400}, ...]` |
| `extra.now` | int | 服务器时间戳（毫秒） | 1791855089000 |
**
**使用示例**：
```typescript
// 前端 useApi hook 调用
const { data: incomeDetail, isLoading } = useApi('/api/v1/external/creator/income/detail?history_day_count=7');
// 通过 incomeDetail.data.chart_coordinate_list 绘制收益趋势图
// 通过 incomeDetail.data.income_item_list 显示每日收入明细
```
**
**异常处理**：
- `status_code: -1` - 连接错误（无法抓取 Creator 平台）
- `status_code: -2` - 请求超时
- `status_code: -3` - 请求参数/格式错误
- `status_code: -99` - 未知异常

---
**⚠️ 关键备注**：
- 两个接口均为**系统级接口**（标记 "— 系统级接口"），需要有效的 `CREATOR_COOKIES` 环境变量支持
- Cookie 有效期通常为 2h-7 天，需定期手动更新（通过浏览器 F12 抓取）
- 接口响应格式与 `summary`（汇总数据）和 `detail`（明细/趋势）相匹配，便于前端统一封装
- 前端 `VersionControl.tsx` 已准备好通过 `useApi` hook 调用这两个端点
---
### Compass 店铺经营概况 `/api/v1/external/compass/shop/core-index`
**
**方法**：GET
**
**完整 URL**：`https://compass.jinritemai.com/compass_api/shop/common/homepage/core_index_v3`
**
**概述**：从compass店铺后台获取核心经营指标数据，返回 15 个核心指标的当日数据（income_amt, pay_amt, settlement_amt_pay_time, pay_cnt, product_show_ucnt, product_click_ucnt, per_usr_pay_amt, pay_ucnt, rfndsuc_amt, rfndsuc_amt_pay_time, refund_amt_rate, refund_amt, refund_order_cnt, refund_order_cnt_pay_time, product_show_click_ucnt_ratio, product_click_pay_ucnt_ratio）。这是一个**系统级接口**，用于店铺经营数据大盘和监控平台。
**
**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `begin_date` | string | 是 | `2026/10/13+00:00:00` | 开始日期（格式：YYYY/MM/DD+HH:MM:SS） |
| `end_date` | string | 是 | `2026/10/13+00:00:00` | 结束日期（格式：YYYY/MM/DD+HH:MM:SS） |
| `date_type` | int | 是 | `1` | 日期类型（1=单日） |
| `activity_id` | string | 否 | (empty) | 活动 ID |
| `index_selected` | string | 是 | `income_amt,pay_amt,settlement_amt_pay_time,pay_cnt,product_show_ucnt,product_click_ucnt,per_usr_pay_amt,pay_ucnt,rfndsuc_amt,rfndsuc_amt_pay_time,refund_amt_rate,refund_amt,refund_order_cnt,refund_order_cnt_pay_time,product_show_click_ucnt_ratio,product_click_pay_ucnt_ratio` | 要查询的指标列表（逗号分隔，见下方说明） |
| `operate_type` | int | 是 | `0` | 操作类型 |
| `_lid` | string | 是 | `579006128205` | 页面层级ID |
| `msToken` | string | 是 | `9JANHxTPoFvsQ-ZnSrRuJEW8xzKRQAlAsmS3mXE42j-JM7RegLn8QzsNkhsuRB7YW3CBXNXNwWnSIWILzKpxX5Rcq1rEAoKTE-gSjKAFJS9PfuDwmM8s9Wja8LAEstIrmluEb1iiHomWF2TiKXqcjZYGwuLppBGWQ9QC6oFpuVyWM8aCigQJ0A=D===` | MS Token（时效性参数） |
| `a_bogus` | string | 是 | `Yysfhw6yxxmcKpCt8Ck87leUYALlNsWyBeixbeaN7KOqLXFbVe3X4NbuaowQmnkrVWpENK-HUd4MbfnbqUTwpZ2pzmpkSNzy6s29VtfoMZrsTGig7qDKCbSEuiPYUATYm=AUE/f56s0F2dQW9q9hAdB7q/UxmbjdFN-XV/znT9usUCujho2Ca-YkFhll` | 加密参数（时效性参数） |
| `verifyFp` | string | 是 | `verify_mv5wpr56_0PeqEgqG_K4aj_4lyS_AWMt_D80uU6fJOfSr` | 验证指纹参数 |
| `fp` | string | 是 | `verify_mv5wpr56_0PeqEgqG_K4aj_4lyS_AWMt_D80uU6fJOfSr` | 指纹参数 |
**
**请求头**：```
User-Agent: Config.USER_AGENT (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36)
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Pragma: no-cache
Referer: https://compass.jinritemai.com/shop?btm_ppre=a0.b0.c0.d0&btm_pre=..c0.d0
sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36
x-e2e-platform: compass
Cookie: COMPASS_COOKIES (完整域名 Cookie 字符串)
```**
**返回示例**：```json
{
  "data": {
    "module_data": {
      "homepage_core_index": {
        "compass_general_multi_index_card_value": {
          "basic_meta": [
            {"index_name":"income_amt"},
            {"index_name":"pay_amt"},
            {"index_name":"settlement_amt_pay_time"},
            {"index_name":"pay_cnt"},
            {"index_name":"product_show_ucnt"},
            {"index_name":"product_click_ucnt"},
            {"index_name":"per_usr_pay_amt"},
            {"index_name":"pay_ucnt"},
            {"index_name":"rfndsuc_amt"},
            {"index_name":"rfndsuc_amt_pay_time"},
            {"index_name":"refund_amt_rate"},
            {"index_name":"refund_amt"},
            {"index_name":"refund_order_cnt"},
            {"index_name":"refund_order_cnt_pay_time"},
            {"index_name":"product_show_click_ucnt_ratio"},
            {"index_name":"product_click_pay_ucnt_ratio"}
          ],
          "data": [
            {
              "income_amt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6},
                    "pay_qc_plat_coupon_amt_ratio":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "pay_amt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6},
                    "new_usr_pay_amt":{"unit":6},
                    "new_usr_pay_amt_ratio":{"unit":6},
                    "old_usr_pay_amt":{"unit":6},
                    "old_usr_pay_amt_ratio":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "pay_cnt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "pay_ucnt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "per_usr_pay_amt": {
                "index_value": {
                  "extra_value":{"benchmark_type":{"unit":6}}
                },
                "value":{"unit":6}
              },
              "product_click_pay_ucnt_ratio": {
                "index_value": {
                  "extra_value":{"benchmark_type":{"unit":6}}
                },
                "value":{"unit":6}
              },
              "product_click_ucnt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "product_show_click_ucnt_ratio": {
                "index_value": {
                  "extra_value":{"benchmark_type":{"unit":6}}
                },
                "value":{"unit":6}
              },
              "product_show_ucnt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "refund_amt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "refund_amt_rate": {
                "index_value": {
                  "extra_value":{"benchmark_type":{"unit":6}}
                  },
                  "value":{"unit":6}
                }
              },
              "refund_order_cnt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "refund_order_cnt_pay_time": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "rfndsuc_amt": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "rfndsuc_amt_pay_time": {
                "index_value": {
                  "extra_value": {
                    "benchmark_type":{"unit":6},
                    "delivery_proportion":{"unit":6}
                  },
                  "value":{"unit":6}
                }
              },
              "settlement_amt_pay_time": {
                "index_value": {
                  "extra_value":{"benchmark_type":{"unit":6}}
                },
                "value":{"unit":6}
              }
            }
          ],
          "meta": []
        }
      }
    },
    "msg": "",
    "st": 0
  }
}
```
**
**返回字段说明**：| 字段 | 类型 | 说明 | 示例值 | |------|------|------|--------| | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.basic_meta` | array | 15个指标名称列表 | `[{"index_name":"income_amt"}, ..., {"index_name":"product_click_pay_ucnt_ratio"}]` | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data` | array | 15个指标的数值对象数组 | 见上方返回示例的 data 数组 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].income_amt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].pay_amt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].settlement_amt_pay_time.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].pay_cnt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].product_show_ucnt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].product_click_ucnt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].per_usr_pay_amt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].pay_ucnt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].rfndsuc_amt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].rfndsuc_amt_pay_time.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].refund_amt_rate.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].refund_amt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].refund_order_cnt.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].refund_order_cnt_pay_time.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].product_show_click_ucnt_ratio.index_value.value.unit` | int | 数值单位系数 | 6 | | `data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[].product_click_pay_ucnt_ratio.index_value.value.unit` | int | 数值单位系数 | 6 | | `st` | int | 状态码（0表示成功） | 0 | | `msg` | string | 状态消息 | "" | |
**指标说明 (index_selected 包含的 15 个核心指标)**| 指标名称 | 类型 | 说明 | |------|------|------|--------| | `income_amt` | 收益金额 | 当日总收益 | | `pay_amt` | 支付金额 | 当日总支付金额 | | `settlement_amt_pay_time` | 结算金额/支付时间 | 结算相关金额和时间 | | `pay_cnt` | 支付笔数 | 当日支付订单总笔数 | | `product_show_ucnt` | 产品展示量 | 产品展示总次数 | | `product_click_ucnt` | 产品点击量 | 产品点击总次数 | | `per_usr_pay_amt` | 人均支付金额 | 每用户平均支付金额 | | `pay_ucnt` | 支付用户数 | 当日支付的独家用户数 | | `rfndsuc_amt` | 退款成功金额 | 成功退款的总金额 | | `rfndsuc_amt_pay_time` | 退款成功支付时间 | 退款成功的支付时间戳 | | `refund_amt_rate` | 退款率 | 退款率（比例） | | `refund_amt` | 退款金额 | 退款总金额 | | `refund_order_cnt` | 退款订单数 | 退款订单总数 | | `refund_order_cnt_pay_time` | 退款订单支付时间 | 退款订单的支付时间戳 | | `product_show_click_ucnt_ratio` | 产品展示点击比例 | 产品展示被点击的比例 | | `product_click_pay_ucnt_ratio` | 产品点击支付比例 | 产品点击后支付的比例 | |
**使用示例**：```typescript// 前端 useApi hook 调用
const { data: compassData, isLoading } = useApi('/api/v1/external/compass/shop/core-index?begin_date=2026/10/13+00:00:00&end_date=2026/10/13+00:00:00&index_selected=income_amt,pay_cnt');// 通过 compassData.data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[0].income_amt 获取收益金额// 通过 compassData.data.module_data.homepage_core_index.compass_general_multi_index_card_value.data[0].pay_cnt 获取支付笔数```**异常处理**：- `st: 0` - 成功- `st: !== 0` - 失败（配合 msg 字段查看具体错误信息）- Cookie 失效时返回相应错误状态
---
**⚠️ 关键备注**：
- 该接口为**系统级接口**（标记 "— 系统级接口"），需要有效的 `COMPASS_COOKIES` 环境变量支持
- Cookie 有效期通常为 2h-7 天，需定期手动更新（通过浏览器 F12 抓取）
- `index_selected` 参数决定返回哪些指标，默认包含 15 个核心指标
- 接口响应数据结构包含 `basic_meta`（指标名称列表）和 `data`（具体数值），便于前端统一按名称映射展示
- 前端可根据需要动态构建 `index_selected` 参数，只请求需要的指标
---

### 好货商品在线预览 `/api/v1/external/haohuo/product/preview`

**方法**：POST

**完整 URL**：`https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/`

**概述**：从好货平台获取商品在线预览数据，返回商品详情图片、规格信息、价格/销量/协议配置、跳转链接等完整预览数据。这是一个**系统级接口**，用于商品详情页预览和商品管理。

**Query 参数**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `is_h5` | string | 是 | `1` | H5 模式标识 |
| `origin_type` | string | 是 | `doudian_product_management` | 来源类型 |
| `msToken` | string | 否 | (动态生成) | MS Token（时效性参数，建议从 Cookie/页面获取） |
| `a_bogus` | string | 否 | (动态生成) | 加密参数（时效性参数，建议从 Cookie/页面获取） |

**请求体**：
| 参数 | 类型 | 必填 | 示例值 | 说明 |
|------|------|------|--------|------|
| `promotion_id` | string | 是 | `3832031939804659866` | 商品推广ID（即商品ID） |
| `enter_from` | string | 否 | (empty) | 进入来源 |
| `meta_param` | string | 否 | (empty) | 元参数 |
| `is_h5` | string | 是 | `1` | H5 模式标识 |

**请求头**：
```
User-Agent: Config.USER_AGENT (Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36)
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
Origin: https://haohuo.jinritemai.com
Referer: https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id={promotion_id}&origin_type=doudian_product_management
sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Cookie: HAOHUO_COOKIES (完整域名 Cookie 字符串)
```

**返回示例**：```json
{
  "status_code": 0,
  "detail_info": {
    "detail_imgs": [
      {
        "uri": "ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800",
        "url_list": [
          "https://p3-item.ecombdimg.com/img/ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800~tplv-5mmsx3fupr-resize:790:800.jpeg",
          "https://p26-item.ecombdimg.com/img/ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800~tplv-5mmsx3fupr-resize:790:800.jpeg"
        ],
        "width": 790,
        "height": 800
      }
    ],
    "product_format": [
      {
        "format": [
          {"name": "规格", "message": [{"desc": "1瓶装"}], "pic_urls": null, "property_id": "93"},
          {"name": "产地", "message": [{"desc": "中国大陆"}], "pic_urls": null, "property_id": "1880"},
          {"name": "材质", "message": [{"desc": "低温丝"}], "pic_urls": null, "property_id": "3127"}
        ],
        "media_elements": null
      }
    ],
    "detail_config": [
      {
        "main_content": [
          {
            "content": [
              "售卖价，由商家依照《价格法》规定的定价原则及定价依据通过商家后台页面自主填写...",
              "如商品通过商家后台参加促销活动（如优惠券、满减、秒杀、拼团等）...",
              "到手价，指商品使用各种优惠券、参与满减等促销活动后，消费者实际支付的价格...",
              "商品价格由商家自主决定，如商家及/或达人对商品价格有特别说明的...",
              "抖音电商平台价格标签说明"
            ],
            "type": 0,
            "title": "价格说明",
            "links": [{"key": "抖音电商平台价格标签说明", "link": "https://school.jinritemai.com/doudian/web/article/aHzox7KpPT94"}],
            "default_show": false
          },
          {
            "main_content": [
              {
                "content": [
                  "\"已售\"，指该店铺在抖音电商平台内，销售该款商品的数量。",
                  "\"同款热销\"，系同型号同规格的同款商品，在抖音电商平台内多店铺历史销量汇总统计所得..."
                ],
                "type": 0,
                "title": "销量说明",
                "links": [],
                "default_show": false
              },
              {
                "main_content": [
                  "小店平台用户服务协议",
                  "小店隐私政策"
                ],
                "type": 0,
                "title": "协议",
                "links": [
                  {"key": "小店平台用户服务协议", "link": "https://school.jinritemai.com/doudian/web/article/104868?rank=1&fromPage=search_result&searchInfo=10700604816031273580%3A1%3A0&query=%E5%B0%8F%E5%BA%97%E7%94%A8%E6%88%B7%E5%8D%8F%E8%AE%AE"},
                  {"key": "小店隐私政策", "link": "https://school.jinritemai.com/doudian/web/article/aHJfD81heWcT"}
                ],
                "default_show": false
              }
            ],
            "main_title": "",
            "main_type": 0
          }
        ],
        "main_title": "",
        "main_type": 0
      }
    ],
    "detail_imgs_new": [
      {
        "image": {
          "uri": "ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800",
          "url_list": [
            "https://p3-item.ecombdimg.com/img/ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800~tplv-5mmsx3fupr-resize:790:800.jpeg",
            "https://p26-item.ecombdimg.com/img/ecom-shop-material/jpeg_m_3e12dbbc077c033f177ca9fd02893c16_sx_178065_www790-800~tplv-5mmsx3fupr-resize:790:800.jpeg"
          ],
          "width": 790,
          "height": 800
        },
        "pic_type": "pic"
      }
    ],
    "title_image": {
      "uri": "tos-cn-i-5mmsx3fupr/product_detail_head.png",
      "url_list": ["http://p26-item.ecombdimg.com/tos-cn-i-5mmsx3fupr/product_detail_head.png~tplv-5mmsx3fupr-origin-png.png"],
      "width": 149,
      "height": 21
    },
    "ai_question": null,
    "tag_card": null,
    "jump_url": "sslocal://webcast_lynxview?type=popup&url=https%3A%2F%2Flf-webcast-sourcecdn-tos.bytegecko.com%2Fobj%2Fbyte-gurd-source%2F10181%2Fgecko%2Fresource%2Fecommerce_extensions_aweme%2Fextensions%2Fspecifications%2Ftemplate.js&gravity=bottom&height_percent=73&top_level=1&mask_alpha=0.56&add_safe_area_height=0&use_real_screen_height=1&feature_page_source=changmiao&screen_size_adaptation=1"
  },
  "extra": {
    "logid": "20261015104241F1CD0CA2197F56844711",
    "now": 1792032161000,
    "fatal_item_ids": []
  },
  "log_pb": {
    "impr_id": "20261015104241F1CD0CA2197F56844711"
  }
}
```

**返回字段说明**：
| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `status_code` | int | 状态码（0表示成功） | 0 |
| `detail_info.detail_imgs` | array | 详情图片列表（含 url_list、width、height） | `[{uri, url_list: [...], width: 790, height: 800}, ...]` |
| `detail_info.product_format` | array | 商品规格信息（格式、属性） | `[{format: [{name: "规格", message: [{desc: "1瓶装"}], property_id: "93"}, ...]}]` |
| `detail_info.detail_config` | array | 详情配置（价格说明、销量说明、协议等） | `[{main_content: [...]}]` |
| `detail_info.detail_imgs_new` | array | 新格式详情图片（含 pic_type 字段） | `[{image: {...}, pic_type: "pic"}, ...]` |
| `detail_info.title_image` | object | 标题图片 | `{uri, url_list: [...], width: 149, height: 21}` |
| `detail_info.jump_url` | string | 跳转链接（直播间/lynxview schema） | `sslocal://webcast_lynxview?type=popup&url=...` |
| `detail_info.ai_question` | unknown | AI 问答相关 | null |
| `detail_info.tag_card` | unknown | 标签卡片 | null |
| `extra.logid` | string | 日志ID | `20261015104241F1CD0CA2197F56844711` |
| `extra.now` | int | 当前时间戳（毫秒） | 1792032161000 |
| `extra.fatal_item_ids` | array | 致命错误商品ID列表 | `[]` |
| `log_pb.impr_id` | string | 曝光ID | `20261015104241F1CD0CA2197F56844711` |

**使用示例**：
```typescript
// 前端调用
const { data: preview } = await haohuoApi.getProductPreview('3832031939804659866');

// 获取详情图片
const images = preview?.detail_info?.detail_imgs?.map(img => img.url_list[0]) || [];

// 获取商品规格
const specs = preview?.detail_info?.product_format?.[0]?.format || [];

// 获取价格/销量/协议说明
const configs = preview?.detail_info?.detail_config || [];

// 获取跳转链接
const jumpUrl = preview?.detail_info?.jump_url;
```

**异常处理**：
- `status_code: 0` - 成功
- `status_code: -1` - 连接错误
- `status_code: -2` - 请求超时
- `status_code: -3` - 请求失败
- `status_code: -99` - 未知异常

---
**⚠️ 关键备注**：
- 该接口为**系统级接口**，需要有效的 `HAOHUO_COOKIES` 环境变量支持
- Cookie 有效期通常为 2h-7 天，需定期手动更新（通过浏览器 F12 抓取）
- `msToken` 和 `a_bogus` 是动态签名参数，通常需要从页面 JS 计算或从 Cookie 中提取，当前实现不传递这两个参数，服务端可能仅依靠 Cookie 校验
- `jump_url` 为抖音小程序/直播间跳转 schema，需在抖音 App 内打开
- 前端 `haohuoApi.getProductPreview(promotionId)` 已封装好调用
---
| 字段 | 类型 | 说明 |
|------|------|------|
| `status_code` | int | 成功标识 (0) |
| `total` | int | 总作品数（如 42） |
| `aweme_list` | array | 当前页作品列表（默认 12 条） |
| `has_more` | bool | 是否有更多 |
| `max_cursor` | string | 下一页游标 |

---

## 外部 API 字段跨接口映射速查表（内部标准化字段对照）

| 内部标准字段 | 抖店商品统计 | 抖店商品列表 | 抖店订单统计 | 抖店订单列表 | 创作者概览 | 创作者作品 |
|-------------|-------------|-------------|-------------|-------------|-----------|-----------|
| **总数/计数** | `data.onsale` | `len(data)` | `data.all` | `data[].product_count` | `total_fans_cnt` (粉丝) | `total` (总作品数) |
| **金额(分)** | - | `discount_price`*100 | - | `pay_amount` | - | - |
| **播放量** | - | - | - | - | `play_cnt` | `statistics.play_count` |
| **点赞数** | - | - | - | - | `digg_cnt` | `statistics.digg_count` |
| **评论数** | - | - | - | - | `comment_cnt` | `statistics.comment_count` |
| **分享数** | - | - | - | - | `share_count` | `statistics.share_count` |
| **粉丝数** | - | - | - | - | `total_fans_cnt` | `author.follower_count` |
| **作品数** | - | - | - | - | `publish_cnt` | `author.aweme_count` |
| **收货信息** | - | - | - | `receiver_info` | - | - |
| **商品明细** | - | `data[]` | - | `product_item[]` | - | `aweme_list[]` |
| **操作动作** | - | - | - | `operation_actions` | - | - |

> `*` 商品列表价格字段为元单位，内部转换为分存储

---

### 单位换算速查表（2026-10-15 新增）

| 数据类型 | 典型字段 | 外部 API 单位 | 内部 stats 端点返回单位 | 前端 formatCurrency 调用方式 |
|---------|---------|-------------|---------------------|--------------------------|
| **商品价格** | `price_lower`、`price_higher`、`market_price`、`discount_price`、`price` | **分 (fen)** | **分** (透传) | `formatCurrency(value / 100)` |
| **订单金额** | `pay_amount`、`total_price`、`total_amount`、`actual_receive_amount_int` | **分 (fen)** | **元 (yuan)** (已 `/ 100`) | `formatCurrency(value)` |
| **统计聚合金额** | `/orders/stats.all.amount`、`/orders/stats.pay.amount`、`/dashboard/stats.total_revenue_today` | **分 (fen)** | **元 (yuan)** (已 `/ 100`) | `formatCurrency(value)` |
| **创作者收益** | `today_total_income`、`yesterday_total_income`、`history_total_income` | **分 (fen)** | **分** (透传) | `formatCurrency(value / 100)` |

> **核心原则**：
> - **商品价格类**字段（Products、Dashboard.top_products）：外部 API 返回**分**，内部 stats 端点透传**分**，前端显示时 `/ 100` 转元
> - **订单金额类**字段（Orders、Dashboard.recent_orders、/orders/stats）：外部 API 返回**分**，内部 stats 端点聚合时已 `/ 100` 转**元**，前端直接用
> - **创作者收益类**字段：外部 API 返回**分**，内部透传**分**，前端显示时 `/ 100` 转元

---

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

## 关键修复记录（2026-10-07/08 验证）

### 1. 订单列表签名策略修复 (`/api/order/searchlist`)

**问题**：带过期签名请求返回 `10001010A` (SIGNATURE_ERROR/RISK_CONTROL)

**根因**：该端点**不需要** `a_bogus`、`msToken` 时效性签名参数。仅需长效 Cookie 认证（`__token`、`verifyFp`、`fp`）。

**修复**：
- `_request()` 新增 `skip_sign: bool = False` 参数
- `_fetch_orders_from_api()` 调用时显式传 `skip_sign=True`
- 仅保留长效参数：`__token`、`verifyFp`、`fp`、`_lid=606316310312`（实测有效值）

**参数策略**：
| 类型 | 参数 | 处理方式 |
|------|------|----------|
| 长效 | `__token`、`verifyFp`、`fp` | 显式传递（配置读取） |
| 强时效 | `msToken`、`a_bogus` | `skip_sign=True` 禁止自动注入 |
| 固定 | `_lid` | 使用实测值 `606316310312` |

### 2. Redis 缓存共享问题

**现象**：单 app 容器 (`douyin_app`) 在 Redis 连接失败时若回退到进程内内存字典，会导致同步任务写入 Redis 但读取方读到旧缓存。（历史案例：5 容器时代 Flask (`douyin_monitor`) 与 Celery Worker (`douyin_celery_worker`) 各自持有独立内存缓存；2026-10-16 起单 app 容器共享缓存，且 `redis_cache.py` 已移除内存 fallback，连接失败直接抛错，此问题不再复现，此处保留作为 Redis 连接异常排障参考）

**解决**：
- 重启 app 容器确保 Redis 连接建立：`docker restart douyin_app`
- 验证：`docker exec douyin_redis redis-cli GET 'douyin:monitor:creators'`

### 3. 创作者概览字段解析修复

**问题**：外部 API 返回 `metrics` 数组，内部代码按旧格式 `data.creators`/`data.total_followers` 解析，导致全 0。

**修复**：`_fetch_creator_overview_from_api()` 和 `_fetch_creators_from_api()` 兼容解析 `metrics` 数组，按 `english_metric_name` 映射标准字段。

### 4. 内部 API 验证结果（2026-10-08 同步后）

| 接口 | 状态 | data_source | 关键字段 |
|------|------|-------------|----------|
| `GET /api/v1/creators/overview` | ✅ | external | total_followers: 1166, total_views: 47, recent_like: 2 |
| `GET /api/v1/creators/works` | ✅ | external | 12 个作品完整详情 |
| `GET /api/v1/creators` | ✅ | real | 1 个创作者聚合统计 |
| `GET /api/v1/orders/stats` | ✅ | real | all: 1 单 62.02元 |
| `GET /api/v1/orders` | ✅ | real | 1 个订单完整详情 |
| `GET /api/v1/products` | ✅ | real | 商品列表 |
| `POST /api/v1/sync` | ✅ | - | 6/6 任务全成功 |

---

## 认证与请求头

### 内部 API 认证（Flask + axios）

**后端鉴权中间件**（`app.py:check_auth`）：
- **Header 校验**：同时检查 `Authorization: Bearer <API_KEY>` 和 `X-API-Key: <API_KEY>`
- **通过条件**：任一 Header 校验通过即可（建议前后端双发）
- **白名单端点**（`PUBLIC_ENDPOINTS`）：
  - `/api/v1/health` - 健康检查
  - `/api/v1/auth/login` - OAuth 登录入口
  - `/api/v1/auth/callback` - OAuth 回调
  - `/api/v1/auth/qr-code` - 获取登录二维码
  - `/api/v1/auth/status` - 授权状态查询
  - `/api/v1/auth/profile` - 获取用户资料（需内部 API_KEY，非白名单）
- **API_KEY 来源**：`Config.API_KEY`（优先读取 Docker secret `api_key`，回退环境变量 `API_KEY`）
- **默认值**：`wlkj_douyin_api_20260921_abc123`
- **SKIP_AUTH 开关**：`SKIP_AUTH=true` 环境变量可完全跳过鉴权（调试用）

**前端 axios 封装**（`src/frontend/src/utils/apiClient.ts`）：
```typescript
// 同时发送双 Header
instance.defaults.headers.common['X-API-Key'] = token
instance.defaults.headers.common['Authorization'] = `Bearer ${token}`

// Token 来源优先级：VITE_API_KEY > localStorage.authToken
```
- 401 响应时自动清空 token，由调用方决定是否跳转登录
- 非 401 错误自动弹出 `message.error` 提示

### 外部 API 认证（抖店/创作者中心）

**统一请求转发器**（`services.fetcher._request`）：

| 项目 | 抖店 (`fxg.jinritemai.com`) | 创作者中心 (`creator.douyin.com`) |
|------|---------------------------|-------------------------------|
| **Base URL** | `Config.FXG_BASE_URL` | `Config.CREATOR_BASE_URL` |
| **Cookie 来源** | `FXG_COOKIES` (完整域名 Cookie 字符串) | `CREATOR_COOKIES` (完整域名 Cookie 字符串) |
| **Cookie 传递方式** | `headers['Cookie']` 字符串 | `cookies=` 字典参数（`requests` 的 `cookies=`） |
| **Cookie 预处理** | 直接使用字符串 | `parse_cookies(cookie_str)` 转字典 |
| **动态签名** | `a_bogus`, `msToken`, `verifyFp`, `fp`, `__TOKEN` | 同上（仅 fxg 域名由 `_request` 自动签名） |
| **固定参数** | `_bid=ffa_product`, `aid=FXG_SHOP_ID`, `_lid=FXG_PRODUCT_LID` | `aid=CREATOR_WORK_AID` (无 `_bid`/`_lid`) |
| **Referer** | `https://fxg.jinritemai.com/` | `https://creator.douyin.com/creator-micro/content/manage` |
| **User-Agent** | `Config.USER_AGENT` (Chrome 150) | 同上 |
| **签名实现** | `douyin_sign.sign_request` (V8 实时计算 `a_bogus`) | 同上（仅 fxg 域名触发） |
| **典型端点** | `/product/tproduct/list`, `/api/order/searchlist` | `/janus/douyin/creator/pc/work_list` |

**Cookie 传递差异**（关键点，已在 fetcher.py 实现）：
- **抖店接口**：通过 `headers['Cookie']` 传递字符串
- **创作者中心作品列表** (`/janus/douyin/creator/pc/work_list`)：**必须**使用 `cookies` 参数传递字典（`requests` 库的 `cookies=`），而非 `Cookie` Header

**请求参数差异**：
- **抖店商品/订单**：需 `_bid`、`aid`、`_lid`、`_token` 等签名参数（由 `_request` 自动注入）
- **创作者作品列表**：`status=0`, `count=12`, `max_cursor=0`, `scene=star_atlas`, `device_platform=android`, `aid=CREATOR_WORK_AID`（无签名参数自动注入）

**错误码分类与指引**（`_classify_external_error` + `_get_auth_error_guidance`）：
| 类别 | 包含码 | 处理指引 |
|------|--------|----------|
| `COOKIE_EXPIRED` | `40101`, `10008` | 重新登录抓取完整 Cookie 更新 `.env` |
| `SIGNATURE_ERROR` | `40301` | 重新抓取 `a_bogus`/`msToken`/`verifyFp`/`fp`/`__token` |
| `RATE_LIMITED` | `429` | 降低频率、增加间隔、稍后重试 |
| `RISK_CONTROL` | `10001010A` | 检查账号状态，降低请求频率 |
| `HTTP_ERROR` | 非 2xx 状态码 | 检查网络/目标服务状态 |
| `TIMEOUT` | 请求超时 | 检查网络或增加超时 |
| `CONNECTION_ERROR` | 连接失败 | 检查域名可达性 |
| `EXCEPTION` | 其他异常 | 查看详细日志 |

---

## 环境变量配置（基于 `config/settings.py` Settings 类）

后端配置优先级：**Docker Secret (`/run/secrets/...`) > 环境变量 > `.env` > 默认值**。

```env
# =========================================================================
# 基础配置
# =========================================================================
DATA_DIR=./data                    # 数据存储目录（容器内映射为 /data）
SCHEDULE_INTERVAL_MINUTES=60       # 定时任务间隔（分钟）
ALERT_EMAIL=                       # 告警通知邮箱
API_AUTH_TOKEN=                    # API 认证 Token（内部服务间调用，可选）
API_KEY=wlkj_douyin_api_20260921_abc123  # API 密钥（前后端统一，也可通过 secret `api_key` 注入）
KEEP_ALIVE_TIMEOUT=30              # Keep-alive 超时（秒）
TIMEOUT=30                         # 请求超时（秒）
EXTERNAL_DATA_BASE_URL=            # 外部数据服务基础 URL（预留扩展）

# =========================================================================
# 抖音开放平台 OAuth 2.0（如需）
# =========================================================================
DOUYIN_APP_ID=                     # 抖音开放平台 App ID
DOUYIN_APP_SECRET=                 # 抖音开放平台 App Secret
DOUYIN_ACCESS_TOKEN=               # 抖音访问令牌

# =========================================================================
# 双域名基础 URL
# =========================================================================
FXG_BASE_URL=https://fxg.jinritemai.com
CREATOR_BASE_URL=https://creator.douyin.com

# =========================================================================
# 公共请求头
# =========================================================================
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36

# =========================================================================
# 认证与签名参数（强时效性，需定期手动更新，通常 2h-7 天失效）
# 获取方式：浏览器登录目标网站 -> F12 Network -> 任意请求 -> Request Headers
# =========================================================================
# 抖店签名参数
TOKEN=                             # 抖店 __TOKEN 参数
MS_TOKEN=                          # 抖店 MS_TOKEN 参数
A_BOGUS=                           # 抖店 a_bogus 参数
VERIFY_FP=                         # 抖店 verifyFp 参数
FP=                                # 抖店 fp 参数

# =========================================================================
# Cookie 配置（完整 Cookie 字符串，分号分隔）
# 获取方法：浏览器登录 -> F12 -> Network -> 任意请求 -> Request Headers -> Cookie
# =========================================================================
FXG_COOKIES=                       # 抖店 Cookie (fxg.jinritemai.com)
CREATOR_COOKIES=                   # 创作者中心 Cookie (creator.douyin.com)
COMPASS_COOKIES=                   # 指南针 Cookie (compass.jinritemai.com)，/external/compass/shop/core-index 必填
HAOHUO_COOKIES=                    # 好货平台 Cookie (haohuo.jinritemai.com)，/external/haohuo/product/preview 必填

# =========================================================================
# 抖店 Shop ID 与 Log ID（多店铺场景需配置）
# =========================================================================
FXG_SHOP_ID=4272                   # 抖店 Shop ID
FXG_LOG_ID=104476165896            # 抖店 Log ID
FXG_PRODUCT_LID=829906029528       # 抖店商品列表 _lid
FXG_ORDER_LID=646601599070         # 抖店订单列表 _lid
FXG_ORDER_AID=4272                 # 抖店订单列表 aid
CREATOR_WORK_AID=1128              # 创作者作品列表 aid

# =========================================================================
# Redis 配置（缓存 / 分布式锁，3 容器架构：app / redis / frontend）
# =========================================================================
REDIS_HOST=redis
REDIS_PORT=6379

# 定时同步间隔（分钟，app 容器内置调度器 schedule + threading）
SCHEDULE_INTERVAL_MINUTES=60

# =========================================================================
# 创作者中心内容管理 API
# =========================================================================
CREATOR_WORK_LIST_URL=https://creator.douyin.com/janus/douyin/creator/pc/work_list

# =========================================================================
# 告警配置
# =========================================================================
ALERT_WECOM_WEBHOOK=               # 企业微信告警 Webhook
ALERT_DINGTALK_WEBHOOK=            # 钉钉告警 Webhook
ALERT_SMTP_HOST=                   # SMTP 服务器地址
ALERT_SMTP_PORT=587                # SMTP 端口
ALERT_SMTP_USER=                   # SMTP 用户名
ALERT_SMTP_PASSWORD=               # SMTP 密码
ALERT_SMTP_FROM=                   # SMTP 发件人邮箱

# =========================================================================
# 日志配置
# =========================================================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760             # 10MB
LOG_BACKUP_COUNT=5

# =========================================================================
# 监控配置
# =========================================================================
ENABLE_METRICS=true
METRICS_PORT=9090

# =========================================================================
# Docker Secrets 对应关系（用于生产环境）
# =========================================================================
# /run/secrets/api_key              -> API_KEY
# /run/secrets/douyin_app_id        -> DOUYIN_APP_ID
# /run/secrets/douyin_app_secret    -> DOUYIN_APP_SECRET
# /run/secrets/douyin_access_token  -> DOUYIN_ACCESS_TOKEN
# /run/secrets/fxg_cookies          -> FXG_COOKIES
# /run/secrets/creator_cookies      -> CREATOR_COOKIES
# /run/secrets/token                -> TOKEN (__TOKEN)
# /run/secrets/ms_token             -> MS_TOKEN
# /run/secrets/a_bogus              -> A_BOGUS
# /run/secrets/verify_fp            -> VERIFY_FP
# /run/secrets/fp                   -> FP
# /run/secrets/fxg_shop_id          -> FXG_SHOP_ID
# /run/secrets/fxg_log_id           -> FXG_LOG_ID
# /run/secrets/compass_cookies      -> COMPASS_COOKIES
# /run/secrets/haohuo_cookies       -> HAOHUO_COOKIES
```

**前端环境变量**（`.env` 或 `.env.production`）：
```env
VITE_API_KEY=wlkj_douyin_api_20260921_abc123  # 必须与后端 API_KEY 一致
VITE_API_BASE_URL=http://localhost:5000       # 开发环境后端地址
```

---

## 签名机制

所有转发至抖店/创作者中心的请求，后端 `services.fetcher._request` 自动完成（仅对 `fxg.jinritemai.com` 域名）：

1. **读取长效参数**：从 `Config` 读取 `TOKEN`、`MS_TOKEN`、`A_BOGUS`、`VERIFY_FP`、`FP`（优先 Docker Secret，回退环境变量）
2. **动态生成 `a_bogus`**：调用 `douyin_sign.sign_request(endpoint, params, existing_tokens, USER_AGENT)`，使用 `py_mini_racer` (V8) 实时计算
3. **合并参数**：将签名参数合并到请求 `params` 中
4. **注入 Cookie**：抖店用 `headers['Cookie']`，创作者中心作品列表用 `cookies=` 字典参数
5. **统一请求头**：`User-Agent` 使用 `Config.USER_AGENT`，`Accept: application/json, text/plain, */*`

**签名实现细节**（`douyin_sign.py`）：
- 加载本地 JS 签名算法文件（通常为混淆后的字节码）
- 通过 V8 运行时执行签名函数，输入：URL、参数、现有 Token、User-Agent
- 输出：更新后的 `a_bogus`、`msToken` 等动态参数
- 失败时记录警告并继续发送无签名请求（由外部 API 返回错误码触发重试/告警）

**动态参数获取来源**：
| 参数 | 获取方式 | 更新频率 |
|------|----------|----------|
| `a_bogus` | V8 实时计算 (`douyin_sign`) | 每次请求 |
| `msToken` | 浏览器页面 `window.__INIT_DATA__` 或 Cookie | 定期手动更新 |
| `verifyFp` / `fp` | 页面加载时的指纹参数 | 定期手动更新 |
| `__TOKEN` | 登录后 Cookie `passport_csrf_token` 或请求头 | 定期手动更新 |
| Cookie | 浏览器插件/开发者工具导出完整域名 Cookie | 定期手动更新（通常 2h-7 天失效） |

**生产环境建议**：
- 使用 Docker Secrets 管理所有敏感参数（`/run/secrets/...`）
- 配置监控告警：外部 API 返回 `COOKIE_EXPIRED`/`SIGNATURE_ERROR` 时自动通知
- 定期轮换 Cookie 和长效 Token（建议每日或每半日）

---

## 外部 API 概览

域名：`fxg.jinritemai.com`、`creator.douyin.com`

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 商品统计 | GET | `/product/tproduct/aggsProductCount` | 商品聚合计数 |
| 商品列表 | GET | `/product/tproduct/list` | 商品分页列表 |
| 订单统计 | GET | `/api/order/tabcnt` | 订单状态汇总 |
| 订单列表 | GET | `/api/order/searchlist` | 订单明细 |
| 创作者概览 | POST | `/janus/douyin/creator/data/overview/dashboard` | 创作者仪表盘 |
| 创作者作品 | GET/POST | `/janus/douyin/creator/pc/work_list` | 作品列表 |

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

- **2026-10-17 v2.4.1**：
  - 环境变量清单补登新增外部 API 依赖的两个 Cookie 变量：`COMPASS_COOKIES`（指南针店铺核心指标接口 `/api/v1/external/compass/shop/core-index`）与 `HAOHUO_COOKIES`（好货商品预览接口 `/api/v1/external/haohuo/product/preview`）；此前两个变量仅在正文出现，未登记在「环境变量配置」章节及 Docker Secrets 映射表中
  - 同步更新 `config/.env.example` 与 `src/backend/.env.example` 模板

- **2026-10-16 v2.4.0**：
  - 文档同步更新：根据代码实际状态更新 API_SPEC.md、ARCHITECTURE.md 和 RUNBOOK.md
  - 新增端点详细文档：/api/v1/health/external (9个外部API健康检查)、/api/v1/compliance/check/products、/api/v1/compliance/check/works、/api/v1/external/haohuo/product/preview、/api/v1/external/creator/income/summary、/api/v1/external/creator/income/detail、/api/v1/external/compass/shop/core-index
  - 修正现有端点字段描述：/api/v1/products/stats (扁平格式)、/api/v1/orders/stats (金额单位元)、/api/v1/creators/overview (data_source: "cache")
  - 补充认证机制：双 Header 验证 (Authorization: Bearer + X-API-Key)、PUBLIC_ENDPOINTS 白名单完整列表
  - 补充分布式锁机制：Redis SET NX EX 5分钟 TTL 保护同步任务
  - 补充签名策略：skip_sign 参数使用场景、长效参数显式传递、强时效参数跳过注入
  - 更新架构和运维文档以反映 3容器简化架构和内置调度器实现

- **2026-10-08 v2.2.0**：
  - 全面更新 6 个外部 API 实测返回字段完整文档（基于 2026-10-08 容器环境实测）：
    - 商品统计：7 个字段详细表（`onsale`、`audit`、`draft`、`forbidden`、`sell_out_new`、`unpass`、`unpass_new`）
    - 商品列表：修正响应结构为数组 `data[]`，列出预期商品对象 10 字段
    - 订单统计：完整 15 字段表，含 `cnt_report`、`sub_tab_count_map` 13 子标签映射
    - 订单列表：新增 97 字段完整分组表（基础标识、金额、时间、商品明细、买家、收货、操作、物流、分页）
    - 创作者概览：13 项 metrics 完整表 + trends 每日趋势结构 + 9 字段内部映射表
    - 创作者作品：aweme_list 40+ 字段分组表（基础、统计、作者、视频、状态、风控、其他）+ 顶层 5 字段
  - 新增「外部 API 字段跨接口映射速查表」：6 接口核心字段对照，便于内部标准化字段开发
  - **修复前端 API 认证 401 错误**：(1) 在 docker-compose.yml 中为 frontend service 添加 `env_file: - ./src/frontend/.env` 确保 VITE_API_KEY 环境变量加载到容器；(2) 在 src/frontend/nginx.conf 中添加 `proxy_set_header X-API-Key $VITE_API_KEY` 确保 X-API-Key header 正确转发至后端 Flask app。现 API 调用均返回 200 OK，不再出现 401 UNAUTHORIZED。
- **2026-10-08 v2.1.0**：
  - 修复创作者概览字段解析：外部 API 实际返回 `metrics` 数组，内部 `_fetch_creator_overview_from_api()` / `_fetch_creators_from_api()` 兼容解析并按 `english_metric_name` 映射标准字段（新增字段映射表）
  - 修复订单列表签名策略：`_request()` 新增 `skip_sign` 参数，`_fetch_orders_from_api()` 显式传 `skip_sign=True`，仅保留长效参数（`__token`/`verifyFp`/`fp`），禁止过期 `msToken`/`a_bogus` 注入
  - 解决 Redis 缓存共享问题：Flask 与 Celery Worker 需重启建立 Redis 连接，避免内存 fallback 导致数据不一致
  - 更新创作者概览/作品外部 API 实际返回格式文档（`metrics` 数组、`aweme_list` 完整结构）
  - 补充内部 API 验证结果表（7 个接口全部通过）
- **2026-10-07 v2.0.2**：
  - 优化 `searchlist` 订单列表请求头：补充完整浏览器指纹头（`Sec-Fetch-*`、`Sec-Ch-Ua-*`、`Priority`、`Accept-Encoding: zstd`、`Referer: /ffa/order`），配合 `skip_sign=True` 跳过过期签名注入，复现浏览器丰富响应字段（`product_item`、`receiver_info`、`operation_actions` 等）
  - `_request()` 新增 `skip_sign` 参数，`_fetch_orders_from_api()` 显式传 `skip_sign=True`
- **2026-10-07 v2.0.1**：根据实际代码完善「认证与请求头」「环境变量配置」「签名机制」三节，补充：
  - 内部 API 双 Header 鉴权细节、白名单端点、SKIP_AUTH 开关、前端 axios 拦截器行为
  - 外部 API 双域名认证差异、Cookie 传递方式差异、错误码分类与修复指引表
  - 环境变量完整清单（基于 `config/settings.py` Settings 类，含 Docker Secrets 映射）
  - 签名机制实现细节（V8 实时计算 `a_bogus`、参数来源表、生产环境建议）
- **2026-10-07 v1.2.2**：
  - 更新 FXG_COOKIES / CREATOR_COOKIES：修复抖店 Cookie 过期 (10008) 导致的 `/api/v1/products/stats`、`/api/v1/orders/stats` 返回空数据
  - 修复前端 nginx 502 Bad Gateway：重启 douyin_frontend 清理 upstream 缓存的旧 monitor 容器 IP
  - 统一环境变量配置源：建立 `/opt/douyin-platform/.env -> config/.env` 软链接，docker-compose.yml 读取 `./config/.env`

- **2026-10-15 v2.3.0**：
  - **首页 KPI 数据流重构**：三大统计端点改为读取本地同步缓存聚合，不再直接调用外部 API
    - `GET /api/v1/products/stats`：返回扁平格式 `{total, onsale, stock, violation}`，聚合三个标签页
    - `GET /api/v1/orders/stats`：返回标准化格式 `{all: {count, amount}, pay: {...}, cancel: {...}, sub_tab_count_map: {...}}`，金额单位**元**（外部分除以 100 转换）
    - `GET /api/v1/creators/overview`：返回聚合统计 `{total_followers, total_videos, total_views, total_likes, ...}`，`data_source: "cache"`
  - **价格/金额单位统一修复**：
    - 商品价格类（`/products`、`/dashboard/stats.top_products`）：API 返回**分**，前端显示 `/ 100` 转元（Products、Dashboard、Home、Orders 多处修复）
    - 订单金额类（`/orders`、`/dashboard/stats.recent_orders`、`/orders/stats`）：API 返回**元**，前端直接用
  - **首页趋势/TOP 数据恢复**：Home.tsx 复用 `/dashboard/stats` 获取 `sales_trend` 和 `top_products`，KPI 用独立端点
  - **前端类型同步**：`ProductStatsData` 从嵌套对象改为扁平格式，`OrderStatsData` 匹配新标准化格式
  - **TypeScript 构建修复**：`OrderStatusItem` 导入修正、DataTable pagination 属性移除、未使用变量清理

- **2026-10-08 v2.3.0**（3容器架构精简版）:
  - 精简架构：从 5 容器（monitor + celery_worker + celery_beat + redis + frontend）降至 3 容器（app + redis + frontend）
  - 合并职责：`app` 容器同时包含 Flask REST API + 嵌入式 sync scheduler（使用 `schedule` + `threading`），不再需要独立 `celery_worker` 和 `celery_beat` 进程
  - 分布式锁：在 `app.py` 中实现 Redis `SET NX EX`（5分钟 TTL），防止并发同步任务重复执行
  - 强制 Redis 连接：`redis_cache.py` P0 修复，移除内存 fallback，启动时若 Redis 不可用将直接报错退出
  - creator works 语法修复：`blueprints/creators.py` 添加缺失的 `get_creator_works()` 函数，修复原 `GET /creators/works/external` 500 错误
  - Dockerfile 权限修复：使用 `CMD` 直接运行 gunicorn 替代 `ENTRYPOINT`，避免 `entrypoint.sh` 权限被拦截问题
  - 数据流验证：所有 6 个外部 API 抓取正常，同步间隔配置为 60 分钟（可通过 `SCHEDULE_INTERVAL_MINUTES` 环境变量配置）

- **2026-10-12 v1.2.2**：
  - 新增版本控制 API：`GET /api/v1/version`、`GET /api/v1/changes`、`GET /api/v1/status`、`GET /api/v1/env`
  - 前端版本控制页面实现：`VersionControl` 页面（4 个标签页），路由 `/dian/version`
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