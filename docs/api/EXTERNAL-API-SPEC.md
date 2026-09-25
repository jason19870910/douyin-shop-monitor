# 外部 API 规范文档（EXTERNAL API Specification）

> 本文档统一记录项目中调用的外部抖音电商后台 API 接口细节，包括请求路径、请求方法、请求参数、请求头、Cookie、认证方式、示例请求与响应以及错误码说明。

## 目录
1. [订单列表](#订单列表)
2. [订单统计](#订单统计)
3. [商品统计](#商品统计)
4. [商品列表](#商品列表)
5. [创作者中心概览](#创作者中心概览)
6. [抖店罗盘（待补）](#抖店罗盘)

---

## 订单列表 `/api/order/searchlist`
### 接口概述
- **功能**：根据时间范围、分页、排序等条件查询店铺的订单列表。
- **HTTP 方法**：`GET`
- **完整请求 URL 示例**：
```
https://fxg.jinritemai.com/api/order/searchlist?
  page=0&
  pageSize=10&
  compact_time[select]=create_time_start,create_time_end&
  order_by=create_time&
  order=desc&
  tab=all&
  appid=1&
  __token=YOUR_TOKEN&
  _bid=ffa_order&
  aid=4272&
  _lid=104476165896&
  msToken=YOUR_MS_TOKEN&
  a_bogus=YOUR_ABOGUS&
  verifyFp=YOUR_VERIFYFP&
  fp=YOUR_FP
```

### 查询参数
| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `page` | 是 | integer | 页码（从 0 开始） |
| `pageSize` | 是 | integer | 每页记录数 |
| `compact_time[select]` | 是 | string | 时间维度选择，逗号分隔，如 `create_time_start,create_time_end` |
| `order_by` | 否 | string | 排序字段，默认 `create_time` |
| `order` | 否 | string (`asc`/`desc`) | 排序方式，默认 `desc` |
| `tab` | 否 | string | 订单标签过滤，`all` 为全部 |
| `appid` | 否 | integer | 应用 ID，示例 `1` |
| `__token` | 是 | string | 会话签名 token（短时有效） |
| `_bid` | 是 | string | 业务标识，固定 `ffa_order` |
| `aid` | 是 | integer | 业务 ID（店铺 ID） |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌，需实时获取 |
| `a_bogus` | 是 | string | 防爬虫签名，需实时生成 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |

### 请求头 (Headers)
| Header | 必填 | 说明 |
|---|---|---|
| `Accept` | 是 | `application/json, text/plain, */*` |
| `User-Agent` | 是 | 浏览器标识，示例见下方 |
| `Cookie` | 是 | 必须携带完整的 `fxg.jinritemai.com` 域名 Cookie（见下方） |

### Cookie (示例)
> 以下示例仅用于演示，请在实际请求时使用最新捕获的完整 Cookie。
```
passport_csrf_token=...; passport_csrf_token_default=...; s_v_web_id=...; __security_mc_1_s_sdk_crypt_sdk=...; bd_ticket_guard_client_data=...; bd_ticket_guard_client_web_domain=2; uid_tt=...; sid_tt=...; sessionid=...; PHPSESSID=...; ecom_us_lt=...; ucas_c0=...; ttwid=...; ...（共 100+ 字段）
```

### 响应结构（示例）
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
        "buyer": {
          "uid": "111222333",
          "nickname": "用户A"
        }
      }
    ]
  }
}
```

### 错误码说明
| `code` | 含义 |
|---|---|
| `0` | 成功 |
| `40001` | 参数错误或缺失 |
| `40101` | 未授权（Cookie 或 token 失效） |
| `40301` | 防爬虫签名错误 (`a_bogus`、`msToken` 不匹配) |
| `429` | 请求频率过高（触发限流） |
| `500` | 服务器内部错误 |

---
## 订单统计 `/api/order/tabcnt`
### 接口概述
- **功能**：获取订单统计聚合数据（按标签、时间等），常用于仪表盘统计。
- **HTTP 方法**：`GET`
- **完整请求 URL 示例**：
```
https://fxg.jinritemai.com/api/order/tabcnt?
  tabcnt_version=v1&
  tab=all&
  appid=1&
  __token=YOUR_TOKEN&
  _bid=ffa_order&
  aid=4272&
  _lid=104476165896&
  msToken=YOUR_MS_TOKEN&
  verifyFp=YOUR_VERIFYFP&
  fp=YOUR_FP&
  a_bogus=YOUR_ABOGUS
```

### 查询参数
| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `tabcnt_version` | 是 | string | 版本标识，例如 `v1` |
| `tab` | 是 | string | 统计标签，如 `all`、`pay`、`cancel` 等 |
| `appid` | 是 | integer | 应用 ID |
| `__token` | 是 | string | 会话签名 token |
| `_bid` | 是 | string | 业务标识 `ffa_order` |
| `aid` | 是 | integer | 店铺 ID |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |
| `a_bogus` | 是 | string | 防爬虫签名 |

### 请求头 & Cookie
同 **订单列表**（使用 `fxg.jinritemai.com` Cookie）。

### 响应结构（示例）
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "all": {"amount": 12345, "count": 57},
    "pay": {"amount": 11000, "count": 50},
    "cancel": {"amount": 1345, "count": 7}
  }
}
```

### 错误码
同 **订单列表**。

---

## 商品统计 `/product/tproduct/aggsProductCount`
### 接口概述
- **功能**：获取商品聚合统计数据（在售、仓库、违规等）。
- **HTTP 方法**：`GET`
- **完整请求 URL 示例**：
```
https://fxg.jinritemai.com/product/tproduct/aggsProductCount?
  tab=onSale&
  appid=1&
  __token=YOUR_TOKEN&
  _bid=ffa_product&
  aid=4272&
  _lid=104476165896&
  msToken=YOUR_MS_TOKEN&
  a_bogus=YOUR_ABOGUS&
  verifyFp=YOUR_VERIFYFP&
  fp=YOUR_FP
```

### 查询参数
| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `tab` | 是 | string | 统计分类，如 `onSale`、`stock`、`violation` |
| `appid` | 是 | integer | 应用 ID |
| `__token` | 是 | string | 会话签名 token |
| `_bid` | 是 | string | 业务标识 `ffa_product` |
| `aid` | 是 | integer | 店铺 ID |
| `_lid` | 是 | integer | 业务日志 ID |
| `msToken` | 是 | string | 动态安全令牌 |
| `a_bogus` | 是 | string | 防爬虫签名 |
| `verifyFp` | 是 | string | 防刷指纹 Token |
| `fp` | 是 | string | 同上 |

### 请求头 & Cookie
同 **订单列表**（使用 `fxg.jinritemai.com` Cookie）。

### 响应结构（示例）
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "onSale": 120,
    "stock": 30,
    "violation": 2
  }
}
```

### 错误码
同 **订单列表**。

---

## 商品列表 `/product/tproduct/list`
### 接口概述
- **功能**：获取商品分页列表，支持关键词搜索。
- **HTTP 方法**：`GET`
- **完整请求 URL 示例**：
```
https://fxg.jinritemai.com/product/tproduct/list?
  page=1&
  pageSize=20&
  keyword=手机&
  appid=1&
  __token=YOUR_TOKEN&
  _bid=ffa_product&
  aid=4272&
  _lid=104476165896&
  msToken=YOUR_MS_TOKEN&
  a_bogus=YOUR_ABOGUS&
  verifyFp=YOUR_VERIFYFP&
  fp=YOUR_FP
```

### 查询参数
| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `page` | 是 | integer | 页码（从 1 开始） |
| `pageSize` | 是 | integer | 每页记录数 |
| `keyword` | 否 | string | 商品名称关键字搜索 |
| 其余同 **商品统计**（`appid`、`__token`、`_bid`、`aid`、`_lid`、`msToken`、`a_bogus`、`verifyFp`、`fp`） |

### 请求头 & Cookie
同 **订单列表**（使用 `fxg.jinritemai.com` Cookie）。

### 响应结构（示例）
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "products": [
      {
        "product_id": "p123",
        "product_name": "商品A",
        "sales_today": 120,
        "inventory": 30,
        "conversion_rate": 0.12
      }
    ],
    "total": 57,
    "page": 1,
    "size": 20
  }
}
```

### 错误码
同 **订单列表**。

---

## 创作者中心概览 `/janus/douyin/creator/data/overview/dashboard`
### 接口概述
- **功能**：获取创作者中心仪表盘概览数据（粉丝、视频、最近浏览等）。
- **HTTP 方法**：`POST`
- **完整请求 URL 示例**：
```
https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard
```

### 请求体 (JSON)
```json
{
  "recent_days": 7
}
```
> `recent_days` 为可选字段，默认 7 天。

### 请求头 & Cookie
| Header | 必填 | 说明 |
|---|---|---|
| `Accept` | 是 | `application/json, text/plain, */*` |
| `Content-Type` | 是 | `application/json` |
| `User-Agent` | 是 | 同 **订单列表** |
| `Cookie` | 是 | 完整的 `creator.douyin.com` 域名 Cookie（见下方示例） |

### Cookie 示例（creator.douyin.com）
```
passport_csrf_token=...; passport_csrf_token_default=...; s_v_web_id=...; __security_mc_1_s_sdk_crypt_sdk=...; bd_ticket_guard_client_data=...; bd_ticket_guard_client_web_domain=2; uid_tt=...; sid_tt=...; sessionid=...; PHPSESSID=...; ecom_us_lt=...; ucas_c0=...; ttwid=...; ...（共 100+ 字段）
```

### 响应结构（示例）
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

### 错误码
同 **订单列表**（`code` 为 0 表示成功，其他值参照抖音统一错误码）。

---

## 抖店罗盘（URL 待补）
> 该接口因业务方暂未提供具体 URL，后续请在 `EXTERNAL_DATA_BASE_URL` 中配置相应路径并在此处补全文档。

---

## 通用错误码说明
| `code` | 含义 |
|---|---|
| `0` | 成功 |
| `40001` | 参数错误或缺失 |
| `40101` | 未授权（Cookie/Token 失效） |
| `40301` | 防爬虫签名错误 |
| `429` | 请求频率过高 |
| `500` | 服务器内部错误 |

---

## 环境变量映射
| 环境变量 | 用途 |
|---|---|
| `FXG_BASE_URL` | `fxg.jinritemai.com` 域名基础 URL |
| `CREATOR_BASE_URL` | `creator.douyin.com` 域名基础 URL |
| `__TOKEN` | 会话签名 token |
| `MS_TOKEN` | 动态安全令牌 |
| `a_bogus` | 防爬虫签名 |
| `verifyFp` / `fp` | 防刷指纹 token |
| `FXG_COOKIES` | `fxg.jinritemai.com` 完整 Cookie |
| `CREATOR_COOKIES` | `creator.douyin.com` 完整 Cookie |

---

## 动态参数获取策略
- **`a_bogus` / `msToken`**：请在前端页面的 `window.__INIT_DATA__` 或对应的加密脚本中捕获，或通过官方提供的 JavaScript 加密函数实时生成。
- **`verifyFp` / `fp`**：同上，依据页面渲染的 `verifyFp` 参数获取。
- **`__TOKEN`**：登录后通过 Cookie 中的 `passport_csrf_token` 或请求头 `Authorization` 获取短时 token。
- **Cookie**：使用浏览器插件或抓包工具导出完整 `fxg.jinritemai.com` 与 `creator.douyin.com` 域名的 Cookie，确保包含所有 100+ 字段。

---

> **备注**：所有接口均需在请求头中加入 `User-Agent`，推荐使用 `Config.USER_AGENT` 环境变量统一管理。