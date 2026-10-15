# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **2026-10-15**：
  - 首页 KPI 数据流修复：后端统计端点改为读取本地同步缓存聚合，解决首页数据全为 0 问题
  - 独立统计端点：新增 `/products/stats`（商品总数/在售/库存/违规）、`/orders/stats`（订单数/金额/状态分布）、`/creators/overview`（达人/粉丝/视频/播放）
  - 价格单位统一处理：API 返回分，前端显示自动除以 100（Products、Dashboard、Orders、Home 多处修复）
  - 首页趋势和 TOP 数据恢复：复用 `/dashboard/stats` 端点提供 `sales_trend` 和 `top_products`
  - 导出 CSV 价格字段同步修正（分转元）
  - **新增好货商品在线预览 API**：`/api/v1/external/haohuo/product/preview`（POST），支持商品详情图片、规格、价格/销量/协议配置、跳转链接获取，基于 `haohuo.jinritemai.com` 外部接口

### Fixed
- 2026-10-15 **首页 KPI 全为 0**：后端 stats 端点直接调用外部 API 而非读取本地缓存，改为聚合本地同步数据
- 2026-10-15 **商品价格显示 100 倍**：Products、Dashboard、Orders、Home 多处 `formatCurrency` 未除以 100
- 2026-10-15 **订单金额字段缺失**：Dashboard、Orders 使用 `amount` 字段，实际 API 返回 `pay_amount`/`total_price`（元单位）
- 2026-10-15 **首页销售趋势/热销商品显示占位**：Home.tsx 仅用独立端点缺失趋势和 TOP 数据，复用 dashboard/stats 恢复
- 2026-10-15 **TypeScript 构建错误**：OrderStatusItem 导入方式修正、DataTable pagination 属性移除、未使用变量清理

- 2026-10-14 Fixed health check response format: status="healthy", added last_update, CST timezone
- 2026-10-14 Extended external health check to 9 endpoints (added creator income summary/detail + compass)
- 2026-10-14 Fixed manual sync last_update timing (now reads after scheduled_job completes)
- 2026-10-14 Fixed Google Fonts timeout by switching to domestic CDN mirror
- 2026-10-14 Fixed Nginx caching and auth header forwarding
- 2026-10-14 **Fixed Nginx DNS cache causing proxy failures**: added runtime resolver with 10s TTL, backend restarts no longer require frontend restart

## [v1.0.0] - 2026-09-05
### Added
- First formal version release