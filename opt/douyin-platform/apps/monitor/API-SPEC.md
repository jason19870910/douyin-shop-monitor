# API 规范文档 (Douyin 监控平台 - 外部接口)

> 本文档统一记录项目中调用的 **外部抖音电商后台 API** 与 **内部转发接口** 规范，作为代码实现、联调、测试以及运维的唯一事实源。

---

## 版本说明
| 项目 | 说明 |
|------|------|
| 文档版本 | 1.0.0 |
| 最后更新 | 2026-08-12 |
| 作者 | 自动化助手 |

---

## 1. 公共返回结构

### 成功响应
```json
{
  "code": 0,
  "message": "success",
  "data": { }
}
```

### 错误响应
```json
{
  "code": 40001,
  "message": "错误描述",
  "data": null
}
```

---

## 2. 通用认证 & 请求头

### 2.1 认证方式
- 通过 **Cookie** 维持会话
- 查询字符串中需携带动态签名参数：
  - `__token`、`msToken`、`a_bogus`、`verifyFp`、`fp`

### 2.2 常用请求头
| Header | 必填 | 示例值 |
|--------|------|--------|
| Accept | 是 | `application/json, text/plain, */*` |
| Accept-Language | 否 | `zh-CN,zh;q=0.9` |
| Cache-Control | 是 | `no-cache` |
| Pragma | 是 | `no-cache` |
| Priority | 是 | `u=1, i` |
| Referer | 是 | 触发请求的业务页面 URL |
| Sec-CH-UA | 是 | `"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"` |
| Sec-CH-UA-Mobile | 是 | `?0` |
| Sec-CH-UA-Platform | 是 | `"Windows"` |
| Sec-Fetch-Dest | 是 | `empty` |
| Sec-Fetch-Mode | 是 | `cors` |
| Sec-Fetch-Site | 是 | `same-origin` |
| User-Agent | 是 | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36` |

### 2.3 通用 Cookie 字段清单（抖店 / 创作者中心需分别维护）
| 域名 | 关键 Cookie 字段（节选） |
|------|---------------------------|
| `fxg.jinritemai.com` | `passport_csrf_token`, `__security_mc_1_s_sdk_crypt_sdk`, `bd_ticket_guard_client_data`, `ecom_gray_shop_id`, `csrf_session_id`, `uid_tt`, `sid_tt`, `sessionid`, `PHPSESSID`, `ecom_us_lt`, `ttwid`, `msToken` … |
| `creator.douyin.com` | `passport_csrf_token`, `__security_mc_1_s_sdk_crypt_sdk`, `bd_ticket_guard_client_data`, `csrf_session_id`, `uid_tt`, `sessionid`, `ttwid`, `msToken`, `odin_tt` … |

> ⚠️ **完整 Cookie 请在实际抓包时获取**，缺失关键字段会导致 `40101`（未授权）或 `40301`（防爬虫签名错误）。

---

## 3. 接口总览

### 3.1 外部抖音电商后台 API（直接调用）
| # | 接口名称 | HTTP 方法 | 路径 | 域名 | 说明 |
|---|----------|-----------|------|------|------|
| 1 | 商品统计 | GET | `/product/tproduct/aggsProductCount` | fxg.jinritemai.com | 查询商品聚合统计数据 |
| 2 | 商品列表 | GET | `/product/tproduct/list` | fxg.jinritemai.com | 获取商品分页列表 |
| 3 | 订单统计 | GET | `/api/order/tabcnt` | fxg.jinritemai.com | 订单状态汇总统计 |
| 4 | 订单列表 | GET | `/api/order/searchlist` | fxg.jinritemai.com | 查询订单明细列表 |
| 5 | 创作者中心概览 | POST | `/janus/douyin/creator/data/overview/dashboard` | creator.douyin.com | 获取创作者仪表盘数据 |
| 6 | 抖店罗盘 | GET | `/api/shop/compass` | fxg.jinritemai.com | 店铺运营罗盘指标（URL 待补） |

### 3.2 内部转发接口（供前端调用，由本服务代理转发）
| # | 内部路径 | 代理目标 | 说明 |
|---|----------|----------|------|
| A | `/api/products/stats` | `/product/tproduct/aggsProductCount` | 商品统计转发 |
| B | `/api/products/external` | `/product/tproduct/list` | 商品列表转发 |
| C | `/api/orders/stats` | `/api/order/tabcnt` | 订单统计转发 |
| D | `/api/creator/dashboard` | `/janus/douyin/creator/data/overview/dashboard` | 创作者概览转发 |

---

## 4. 详细接口规范 — 外部 API

### 4.1 商品统计 — `/product/tproduct/aggsProductCount`
- **域名**: `fxg.jinritemai.com`
- **方法**: `GET`
- **查询参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `appid` | 是 | integer | 应用 ID |
| `__token` | 是 | string | 会话签名 token（短时有效） |
| `_bid` | 是 | string | 业务标识 `ffa_product` |
| `aid` | 是 | integer | 店铺 ID |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌 |
| `a_bogus` | 是 | string | 防爬虫签名 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |

- **响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_products": 57,
    "sales_today": 1200,
    "sales_yesterday": 1150,
    "inventory_total": 3400,
    "conversion_rate": 0.1243
  }
}
```

---

### 4.2 商品列表 — `/product/tproduct/list`
- **域名**: `fxg.jinritemai.com`
- **方法**: `GET`
- **查询参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `page` | 是 | integer | 页码（从 1 开始） |
| `pageSize` | 是 | integer | 每页记录数 |
| `keyword` | 否 | string | 商品名称关键字搜索 |
| 其余同上（`appid`、`__token`、`_bid`、`aid`、`_lid`、`msToken`、`a_bogus`、`verifyFp`、`fp`） | | | |

- **响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "products": [
      { "product_id": "p123", "product_name": "商品A", "sales_today": 120, "inventory": 30, "conversion_rate": 0.12 }
    ],
    "total": 57,
    "page": 1,
    "size": 20
  }
}
```

---

### 4.3 订单统计 — `/api/order/tabcnt`
- **域名**: `fxg.jinritemai.com`
- **方法**: `GET`
- **查询参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `tabcnt_version` | 是 | string | 版本标识，如 `v1` |
| `tab` | 是 | string | 统计标签：`all`、`pay`、`cancel` 等 |
| `appid` | 是 | integer | 应用 ID |
| `__token` | 是 | string | 会话签名 token |
| `_bid` | 是 | string | 业务标识 `ffa_order` |
| `aid` | 是 | integer | 店铺 ID |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |
| `a_bogus` | 是 | string | 防爬虫签名 |

- **响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 123,
    "tabs": {
      "all": { "order_count": 100, "amount": 50000 },
      "pay": { "order_count": 80, "amount": 40000 }
    }
  }
}
```

---

### 4.4 订单列表 — `/api/order/searchlist`
- **域名**: `fxg.jinritemai.com`
- **方法**: `GET`
- **完整请求示例**:
```
https://fxg.jinritemai.com/api/order/searchlist?
  page=0&pageSize=10&
  compact_time[select]=create_time_start,create_time_end&
  order_by=create_time&order=desc&tab=all&
  appid=1&__token=xxx&_bid=ffa_order&aid=4272&_lid=104476165896&
  msToken=xxx&a_bogus=xxx&verifyFp=xxx&fp=xxx
```

- **查询参数**:

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `page` | 是 | integer | 页码（从 0 开始） |
| `pageSize` | 是 | integer | 每页记录数 |
| `compact_time[select]` | 是 | string | 时间维度，如 `create_time_start,create_time_end` |
| `order_by` | 否 | string | 排序字段，默认 `create_time` |
| `order` | 否 | string | `asc` / `desc`，默认 `desc` |
| `tab` | 否 | string | 标签过滤，`all` 为全部 |
| `appid` | 否 | integer | 应用 ID，示例 `1` |
| `__token` | 是 | string | 会话签名 token |
| `_bid` | 是 | string | 固定 `ffa_order` |
| `aid` | 是 | integer | 店铺 ID |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌 |
| `a_bogus` | 是 | string | 防爬虫签名 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |

> **说明**: `compact_time[select]` 实际传输时为 `compact_time%5Bselect%5D`，请保持方括号原样。

- **响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 123,
    "list": [
      {
        "order_id": "1234567890",
        "create_time": "2026-10-11 04:43:05",
        "status": "PAID",
        "amount": 1999,
        "buyer": { "uid": "111222333", "nickname": "用户A" }
      }
    ]
  }
}
```

---

### 4.5 创作者中心概览 — `/janus/douyin/creator/data/overview/dashboard`
- **域名**: `creator.douyin.com`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求体**:
```json
{ "recent_days": 7 }
```
- **响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_followers": 5000,
    "total_videos": 120,
    "recent_view": 3400,
    "recent_like": 800
  }
}
```

---

### 4.6 抖店罗盘 — `/api/shop/compass`（URL 待补）
- **域名**: `fxg.jinritemai.com`
- **方法**: `GET`
- **查询参数**:
  - `shop_id` (integer, 必填) – 店铺 ID
  - `date_range` (string, 可选) – 如 `last7`, `last30`，默认 `last7`
  - 其余安全签名参数透传

---

## 5. 内部转发接口规范（供前端调用）

> 以下接口由本服务代理转发到上述外部 API，保持查询参数透传，响应结构统一为：
```json
{
  "success": true,
  "data": { /* 外部 API 返回的 data 字段 */ },
  "message": "xxx fetched from external service"
}
```

| 内部路径 | 代理目标 | 方法 | 说明 |
|----------|----------|------|------|
| `/api/products/stats` | `/product/tproduct/aggsProductCount` | GET | 商品统计转发，支持 `tab`、`appid` |
| `/api/products/external` | `/product/tproduct/list` | GET | 商品列表转发，全参数透传 |
| `/api/orders/stats` | `/api/order/tabcnt` | GET | 订单统计转发，全参数透传 |
| `/api/creator/dashboard` | `/janus/douyin/creator/data/overview/dashboard` | POST | 创作者概览转发 |

---

## 6. 错误码统一说明

| code | HTTP 状态 | 含义 |
|------|-----------|------|
| 0 | 200 | 成功 |
| 40001 | 400 | 参数错误或缺失 |
| 40101 | 401 | 未授权（Cookie/Token 失效） |
| 40301 | 403 | 防爬虫签名错误（`a_bogus`/`msToken` 不匹配） |
| 429 | 429 | 请求频率过高（触发限流） |
| 500 | 500 | 服务器内部错误 |

---

## 7. 调用示例（Python）

```python
import requests

# 统一请求头模板
COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def call_external(url: str, params: dict, cookies: dict) -> dict:
    resp = requests.get(url, params=params, headers=COMMON_HEADERS, cookies=cookies, timeout=30)
    resp.raise_for_status()
    return resp.json()

# 示例：订单列表
url = "https://fxg.jinritemai.com/api/order/searchlist"
params = {
    "page": 0,
    "pageSize": 10,
    "compact_time[select]": "create_time_start,create_time_end",
    "order_by": "create_time",
    "order": "desc",
    "tab": "all",
    "appid": 1,
    "__token": os.getenv("__TOKEN"),
    "_bid": "ffa_order",
    "aid": 4272,
    "_lid": 104476165896,
    "msToken": os.getenv("MS_TOKEN"),
    "a_bogus": os.getenv("a_bogus"),
    "verifyFp": os.getenv("verifyFp"),
    "fp": os.getenv("fp"),
}
cookies = {"passport_csrf_token": "..."}  # 完整 Cookie
result = call_external(url, params, cookies)
print(result)
```

---

## 8. 环境变量映射（.env）

| 变量名 | 用途 | 示例 |
|--------|------|------|
| `FXG_BASE_URL` | 抖店域名基础 URL | `https://fxg.jinritemai.com` |
| `CREATOR_BASE_URL` | 创作者中心域名基础 URL | `https://creator.douyin.com` |
| `__TOKEN` | 会话签名 token | 从 Cookie/页面获取 |
| `MS_TOKEN` | 动态安全令牌 | 从页面脚本获取 |
| `a_bogus` | 防爬虫签名 | 实时生成 |
| `verifyFp` / `fp` | 防刷指纹 Token | 从页面获取 |
| `FXG_COOKIES` | 抖店完整 Cookie 字符串 | `k1=v1; k2=v2; ...` |
| `CREATOR_COOKIES` | 创作者中心完整 Cookie 字符串 | `k1=v1; k2=v2; ...` |

---

## 9. 动态参数获取策略

| 参数 | 来源 | 更新频率 | 备注 |
|------|------|----------|------|
| `a_bogus` / `msToken` | 前端页面 `window.__INIT_DATA__` 或加密脚本 | 每次请求前 | 需实时生成 |
| `verifyFp` / `fp` | 页面渲染时注入 | 每次请求前 | 同上 |
| `__TOKEN` | 登录后 Cookie `passport_csrf_token` 或 `Authorization` | 短时有效 | 失效需重新登录 |
| Cookie | 浏览器开发者工具抓包 | 会话级 | 过期需重新抓取 |

---

## 10. 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-08-12 | 初始版本：整理 6 个外部 API 与 4 个内部转发接口规范 |

---