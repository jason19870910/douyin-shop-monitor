# API 规范文档（内部 API Specification）

## 版本说明
- **文档版本**: v1.0.0
- **最后更新**: 2026-08-12
- **作者**: 自动化助手

## 目的
本文件记录 Douyin Monitor 后端提供的内部 RESTful 接口规范，供前端、第三方系统或调试使用。

本文件详细说明 **Douyin Monitor** 后端提供的所有 RESTful 接口、请求方式、参数、响应示例及错误码，供前端、第三方系统或调试使用。

---

## 公共返回结构
所有成功响应均使用 JSON 对象，统一返回字段：

```json
{
  "success": true,
  "data": <实际业务数据>,
  "message": "可选的附加信息"
}
```

错误响应（`success": false`）示例：

```json
{
  "success": false,
  "error": "错误描述",
  "code": 400
}
```

---

## 1. 健康检查
- **路径**：`/api/health`
- **方法**：`GET`
- **描述**：返回服务状态、当前时间以及最近一次数据同步时间。
- **请求参数**：无
- **响应示例**：
```json
{
  "status": "healthy",
  "timestamp": "2026-08-12T10:38:48.819000",
  "last_update": "2026-08-12T10:38:29.296731"
}
```

---

## 2. 商品接口
### 2.1 获取商品列表
- **路径**：`/api/products`
- **方法**：`GET`
- **查询参数**：
  - `page` (int, optional, 默认 1) – 页码
  - `size` (int, optional, 默认 20) – 每页数量
  - `keyword` (string, optional) – 商品名称关键字模糊搜索
- **响应结构**：
```json
{
  "data": [
    {
      "product_id": "p123",
      "product_name": "商品A",
      "sales_today": 120,
      "sales_yesterday": 100,
      "inventory": 30,
      "conversion_rate": 0.12,
      "conversion_rate_today": 0.12,
      "conversion_rate_yesterday": 0.10,
      "fetched_at": "2026-08-12T10:38:30.123456"
    }
  ],
  "total": 57,
  "page": 1,
  "size": 20
}
```

### 2.2 获取单个商品详情
- **路径**：`/api/products/<product_id>`
- **方法**：`GET`
- **路径参数**：`product_id` – 商品唯一标识
- **响应示例**：同列表中单条记录的对象放在 `data` 字段。

---

## 3. 订单接口
### 3.1 获取订单列表
- **路径**：`/api/orders`
- **方法**：`GET`
- **查询参数**：
  - `page` (int, 默认 1)
  - `size` (int, 默认 20)
  - `start_date` (YYYY-MM-DD, 可选) – 起始日期过滤
  - `end_date` (YYYY-MM-DD, 可选) – 结束日期过滤
  - `status` (string, 可选) – 订单状态过滤
- **响应结构**：
```json
{
  "success": true,
  "data": {
    "abnormal": {"amount": 0, "count": 0},
    "after_sale": {"amount": 0, "count": 0},
    "all": {"amount": 12345, "count": 57}
  },
  "list": [
    {
      "order_id": "o987",
      "amount": 199,
      "status": "completed",
      "create_time": "2026-08-11",
      "fetched_at": "2026-08-12T10:38:31.456789"
    }
  ],
  "total": 57,
  "page": 1,
  "size": 20
}
```

### 3.2 手动同步订单（内部使用）
- **路径**：`/api/sync`
- **方法**：`POST`
- **描述**：触发一次完整的数据抓取（商品、订单、创作者）并更新缓存。
- **请求体**：无
- **响应示例**：
```json
{
  "message": "Sync completed",
  "last_update": "2026-08-12T10:38:35.789012"
}
```

## 4. 创作者接口
### 4.1 获取创作者列表
- **路径**：`/api/creators`
- **方法**：`GET`
- **响应结构**：
```json
{
  "data": [
    {
      "creator_id": "c001",
      "name": "创作者A",
      "followers": 5000,
      "total_sales": 300,
      "avg_conversion_rate": 0.15,
      "fetched_at": "2026-08-12T10:38:32.987654"
    }
  ],
  "total": 3
}
```

### 4.2 获取单个创作者详情
- **路径**：`/api/creators/<creator_id>`
- **方法**：`GET`
- **路径参数**：`creator_id`
- **响应**：同列表中单条记录的对象放在 `data` 字段。

---

## 5. 仪表盘统计接口
- **路径**：`/api/dashboard/stats`
- **方法**：`GET`
- **描述**：返回业务关键统计数据及最近 7 天趋势、TOP5 商品列表。
- **响应结构**：
```json
{
  "data": {
    "total_sales_today": 1200,
    "total_sales_yesterday": 1150,
    "total_revenue_today": 35000,
    "total_revenue_yesterday": 34000,
    "total_orders_today": 58,
    "total_orders_yesterday": 55,
    "avg_conversion_rate": 0.1243,
    "avg_conversion_rate_yesterday": 0.1187,
    "sales_trend": [
      {"date": "2026-08-06", "sales": 1100}
    ],
    "top_products": [
      {"product_id": "p5", "product_name": "商品E", "sales_today": 200}
    ]
  }
}
```

---

## 6. 告警配置接口
### 6.1 查询告警配置
- **路径**：`/api/alerts/config`
- **方法**：`GET`
- **响应**：
```json
{
  "data": {
    "sales_drop_threshold": 0.3,
    "conversion_drop_threshold": 0.2,
    "inventory_low_threshold": 10,
    "notification_email": "alert@example.com",
    "enabled": true
  }
}
```

### 6.2 更新告警配置
- **路径**：`/api/alerts/config`
- **方法**：`POST`
- **请求体（JSON）**：仅包含需要更新的字段，示例：
```json
{
  "sales_drop_threshold": 0.25,
  "notification_email": "ops@example.com",
  "enabled": false
}
```
- **响应**：返回更新后的完整配置。

---

## 7. 错误码说明
| HTTP 状态码 | 含义 | 说明 |
|---|---|---|
| 200 | OK | 请求成功，返回 `success: true`（或健康检查不含 `success`） |
| 400 | Bad Request | 参数缺失或格式错误，例如分页参数非整数 |
| 401 | Unauthorized | 需要授权但未提供或 Token 无效（未来可扩展） |
| 404 | Not Found | 请求的资源（如商品 ID）不存在 |
| 500 | Internal Server Error | 服务器内部异常，日志中会记录详细堆栈 |

---

## 8. 版本说明
- **当前版本**：v1.0.0（2026‑08‑12）
- **变更日志**：请参阅 `CHANGELOG.md` 获取历史版本更新记录。

---

> 本规范文档随代码同步更新，任何接口变更请同步更新此文件并在 `CHANGELOG.md` 中记录。