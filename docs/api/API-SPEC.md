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
{ "code": 0, "message": "success", "data": { } }
```

### 错误响应
```json
{ "code": 40001, "message": "错误描述", "data": null }
```

---

## 2. 通用认证 & 请求头

### 2.1 认证方式
- 通过 **Cookie** 维持会话
- 查询字符串需携带动态签名参数：`__token`、`msToken`、`a_bogus`、`verifyFp`、`fp`

### 2.2 常用请求头（节选）
| Header | 必填 | 示例值 |
|--------|------|--------|
| Accept | 是 | `application/json, text/plain, */*` |
| User-Agent | 是 | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| Cookie | 是 | 完整的域名 Cookie |

> ⚠️ 完整 Cookie 请在实际抓包时获取，缺失会导致 `40101` 或 `40301`。

---

## 3. 接口总览

### 3.1 外部抖音电商后台 API（直接调用）
| # | 接口名称 | 方法 | 路径 | 域名 | 说明 |
|---|----------|------|------|------|------|
| 1 | 商品统计 | GET | `/product/tproduct/aggsProductCount` | fxg.jinritemai.com | 商品聚合统计 |
| 2 | 商品列表 | GET | `/product/tproduct/list` | fxg.jinritemai.com | 商品分页列表 |
| 3 | 订单统计 | GET | `/api/order/tabcnt` | fxg.jinritemai.com | 订单状态汇总 |
| 4 | 订单列表 | GET | `/api/order/searchlist` | fxg.jinritemai.com | 订单明细列表 |
| 5 | 创作者概览 | POST | `/janus/douyin/creator/data/overview/dashboard` | creator.douyin.com | 创作者仪表盘 |
| 6 | 抖店罗盘 | GET | `/api/shop/compass` | fxg.jinritemai.com | 运营指标（URL 待补） |

### 3.2 内部转发接口（供前端调用）
| # | 内部路径 | 代理目标 | 说明 |
|---|----------|----------|------|
| A | `/api/products/stats` | `/product/tproduct/aggsProductCount` | 商品统计转发 |
| B | `/api/products/external` | `/product/tproduct/list` | 商品列表转发 |
| C | `/api/orders/stats` | `/api/order/tabcnt` | 订单统计转发 |
| D | `/api/creator/dashboard` | `/janus/douyin/creator/data/overview/dashboard` | 创作者概览转发 |

---

## 4. 详细接口规范 — 外部 API

详细参数、请求头、响应示例请参考 **EXTERNAL-API-SPEC.md**。

---

## 5. 内部转发接口规范（供前端调用）

响应结构统一：
```json
{ "success": true, "data": { /* 外部 API data */ }, "message": "fetched from external service" }
```

| 内部路径 | 代理目标 | 方法 | 说明 |
|----------|----------|------|------|
| `/api/products/stats` | `/product/tproduct/aggsProductCount` | GET | 商品统计转发 |
| `/api/products/external` | `/product/tproduct/list` | GET | 商品列表转发 |
| `/api/orders/stats` | `/api/order/tabcnt` | GET | 订单统计转发 |
| `/api/creator/dashboard` | `/janus/douyin/creator/data/overview/dashboard` | POST | 创作者概览转发 |

---

## 6. 错误码统一说明
| code | HTTP | 含义 |
|------|------|------|
| 0 | 200 | 成功 |
| 40001 | 400 | 参数错误或缺失 |
| 40101 | 401 | 未授权 |
| 40301 | 403 | 防爬虫签名错误 |
| 429 | 429 | 频率限流 |
| 500 | 500 | 服务器错误 |

---

## 7. 调用示例（Python）
```python
import requests, os
HEADERS = {"Accept":"application/json, text/plain, */*","User-Agent":"Mozilla/5.0"}
def call(url, params, cookies):
    r=requests.get(url, params=params, headers=HEADERS, cookies=cookies, timeout=30)
    r.raise_for_status()
    return r.json()
# 示例订单列表
url="https://fxg.jinritemai.com/api/order/searchlist"
params={"page":0,"pageSize":10,"compact_time[select]":"create_time_start,create_time_end","order_by":"create_time","order":"desc","tab":"all","appid":1,"__token":os.getenv("__TOKEN"),"_bid":"ffa_order","aid":4272,"_lid":104476165896,"msToken":os.getenv("MS_TOKEN"),"a_bogus":os.getenv("a_bogus"),"verifyFp":os.getenv("verifyFp"),"fp":os.getenv("fp")}
cookies={"passport_csrf_token":"..."}  # 完整 Cookie
print(call(url, params, cookies))
```

---

## 8. 环境变量映射（.env）
| 变量 | 用途 |
|------|------|
| `FXG_BASE_URL` | 抖店基础 URL |
| `CREATOR_BASE_URL` | 创作者中心基础 URL |
| `__TOKEN` | 会话 token |
| `MS_TOKEN` | 动态安全令牌 |
| `a_bogus` | 防爬虫签名 |
| `verifyFp` / `fp` | 指纹 token |
| `FXG_COOKIES` | 抖店 Cookie |
| `CREATOR_COOKIES` | 创作者 Cookie |

---

## 9. 动态参数获取策略
- `a_bogus`/`msToken`：从前端 `window.__INIT_DATA__` 或加密脚本实时生成。
- `verifyFp`/`fp`：页面渲染时注入。
- `__TOKEN`：登录后 Cookie `passport_csrf_token`。
- Cookie：浏览器抓包导出完整域名 Cookie。

---

## 10. 版本变更记录
| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-08-12 | 初始版本：整理 6 外部 API 与 4 内部转发接口 |