# 后端 API 文档 (Backend API Documentation)

## 基础信息
- **Base URL**：`http://localhost:5000/api` (开发) / `https://your-domain.com/api` (生产)
- **认证方式**：无需认证（内部服务），外部 API 由后端代理注入 Cookie
- **数据格式**：JSON

## API 端点列表

### 1. 健康检查
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 服务健康状态检查 |

**响应示例**：
```json
{
  "status": "healthy",
  "timestamp": "2026-08-16T00:38:40.687316",
  "last_update": null
}
```

### 2. 仪表盘统计
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/dashboard/stats` | 获取仪表盘聚合统计数据 |

**响应示例**：
```json
{
  "data": {
    "total_sales_today": 1234,
    "total_sales_yesterday": 1100,
    "total_revenue_today": 56789.00,
    "total_revenue_yesterday": 52000.00,
    "total_orders_today": 456,
    "total_orders_yesterday": 420,
    "avg_conversion_rate": 0.032,
    "avg_conversion_rate_yesterday": 0.028,
    "sales_trend": [
      {"date": "2026-08-10", "sales": 100},
      {"date": "2026-08-11", "sales": 120}
    ],
    "top_products": [
      {"product_id": "123", "product_name": "商品A", "sales_today": 50}
    ]
  }
}
```

### 3. 商品管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/products` | 获取商品列表（内部缓存，分页） |
| GET | `/api/products/stats` | 获取商品统计（转发外部 API） |
| GET | `/api/products/external` | 外部商品列表透传（完整参数转发） |
| GET | `/api/products/:id` | 获取单个商品详情 |

#### 3.1 获取商品列表 (`GET /api/products`)
**查询参数**：
- `page` (int, 默认 1)
- `size` (int, 默认 20)
- `keyword` (string, 可选，搜索关键词)

#### 3.2 获取商品统计 (`GET /api/products/stats`)
**查询参数**：
- `tab` (string, 默认 'onSale')
- `appid` (string, 默认 '1')
**说明**：转发至外部 API `https://fxg.jinritemai.com/product/tproduct/aggsProductCount`，自动注入 Cookie 和动态签名参数。返回 `onsale/audit/draft` 等计数。

#### 3.4 外部商品总数统计 `GET /api/products/count`
**说明**：调用 `https://fxg.jinritemai.com/product/tproduct/aggsProductCount`，参数：`tab=onSale&appid=1&_bid=ffa_goods&_lid=638198341795`，返回 `data.onsale` 等计数。
**响应示例**：
```json
{
  "code": 0,
  "data": {
    "audit": 0,
    "draft": 0,
    "forbidden": 0,
    "onsale": 9,
    "sell_out_new": 0,
    "unpass": 0,
    "unpass_new": 0
  }
}
```

#### 3.3 外部商品列表透传 (`GET /api/products/external`)
**查询参数**：完整透传至外部 API `https://fxg.jinritemai.com/product/tproduct/list`  
**说明**：自动生成动态签名参数，复用 `.env` 中的长效 Token。当前生产参数：`page=0&pageSize=20&draft_status=0&tab=onSale&business_type=4&is_online=1&appid=1&_bid=ffa_goods&aid=257675707&_lid=829906029528`

### 4. 订单管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/orders` | 获取订单列表（内部缓存，分页） |
| GET | `/api/orders/stats` | 获取订单统计（转发外部 API） |

#### 4.1 获取订单列表 (`GET /api/orders`)
**查询参数**：
- `page` (int, 默认 1)
- `size` (int, 默认 20)
- `keyword` (string, 可选)
- `start_date` (string, 可选，YYYY-MM-DD)
- `end_date` (string, 可选，YYYY-MM-DD)
- `status` (string, 可选：completed/pending/cancelled/refunded)

#### 4.2 获取订单统计 (`GET /api/orders/stats`)
**查询参数**：
- `start_time` (int, 时间戳)
- `end_time` (int, 时间戳)
**说明**：转发至外部 API `https://fxg.jinritemai.com/api/order/searchlist`，自动注入 Cookie 和动态签名参数。生产参数：`page=0&pageSize=10&order_by=create_time&order=desc&tab=all&appid=1&_bid=ffa_order&aid=4272&_lid=843863276461`。当前受风控拦截 `code 10001010A`，临时使用 Mock 兜底。
**响应示例（正常）**：
```json
{
  "code": 0,
  "data": {
    "orders": [...],
    "total": 123
  }
}
```
**响应示例（风控）**：
```json
{
  "code": "10001010A",
  "msg": "当前环境存在风险，请稍后重试"
}
```

### 5. 创作者管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/creators` | 获取创作者列表（内部缓存） |
| GET | `/api/creators/:id` | 获取创作者详情 |
| GET | `/api/creators/works` | 获取创作者作品列表 |

#### 5.1 创作者作品列表
**说明**：调用 `https://creator.douyin.com/janus/douyin/creator/pc/work_list`，参数：`status=0&count=12&max_cursor=0&scene=star_atlas&device_platform=android&aid=1128`，使用最新 `CREATOR_COOKIES`，Referer: `https://creator.douyin.com/creator-micro/content/manage`
**响应示例**：
```json
{
  "status_code": 0,
  "data": {
    "works": [
      {
        "work_id": "123456",
        "title": "作品标题",
        "cover_url": "...",
        "play_count": 1000
      }
    ],
    "max_cursor": "0"
  }
}
```

### 6. 告警配置
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/alerts/config` | 获取告警配置 |
| POST | `/api/alerts/config` | 更新告警配置 |

### 7. 数据同步
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/sync` | 手动触发全量数据同步 |

**响应示例**：
```json
{
  "last_update": "2026-08-16T00:38:40.687316",
  "message": "Sync completed"
}
```
**说明**：同步流程：获取商品 → 获取订单 → 获取创作者 → 检查告警

### 8. 外部 API 签名机制
所有转发至抖店/创作者中心的请求，后端自动完成：
1. 动态生成 `a_bogus`（使用 `py_mini_racer` V8 实时计算）
2. 复用长效 Token：优先读取 Docker Secrets `/run/secrets/ms_token`、`verify_fp`、`fp`、`token`，次选 `.env`
3. 自动注入 Cookie：从 Docker Secrets `/opt/douyin-platform/secrets/fxg_cookies.txt` / `creator_cookies.txt`
4. 添加必要参数：`_bid`、`aid`、`_lid`、`_t` (时间戳)
5. 请求头补充：`Referer`、`Origin`、`X-Requested-With` 匹配抓包

**Docker Secrets 优先级**：`/run/secrets/*` > `.env`。凭证文件位于 `/opt/douyin-platform/secrets/`，由 Cron 每 15 分钟热更新。

**.env / Secrets 必需字段**：
```env
FXG_BASE_URL=https://fxg.jinritemai.com
CREATOR_BASE_URL=https://creator.douyin.com
__TOKEN=xxx
MS_TOKEN=xxx
verifyFp=xxx
fp=xxx
FXG_COOKIES=xxx
CREATOR_COOKIES=xxx
USER_AGENT=Mozilla/5.0...
```

---
*文档最后更新：2026-09-22*