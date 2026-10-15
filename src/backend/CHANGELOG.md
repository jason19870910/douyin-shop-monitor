# 后端服务变更日志

## [未发布] - 2026-10-15

### 添加
- **独立统计端点**：新增三个聚合统计 API，读取本地同步缓存而非调用外部 API
  - `GET /api/v1/products/stats` → 返回 `{total, onsale, stock, violation}` 商品统计
  - `GET /api/v1/orders/stats` → 返回 `{all: {count, amount}, pay: {...}, cancel: {...}, sub_tab_count_map: {...}}` 订单统计
  - `GET /api/v1/creators/overview?recent_days=7` → 返回 `{total, total_followers, total_videos, total_views, ...}` 创作者概览
- 兼容外部 API 多种字段名：`total_count`/`count`/`total`、`all_amount`/`total_amount`/`amount`
- **新增好货商品在线预览 API**：`POST /api/v1/external/haohuo/product/preview`
  - `services/fetcher.py` 新增 `fetch_haohuo_product_preview(promotion_id)` 函数
  - `blueprints/compliance.py` 新增端点 `/api/v1/external/haohuo/product/preview`
  - 支持详情图片、规格信息、价格/销量/协议配置、跳转链接等完整预览数据
  - 需配置 `HAOHUO_COOKIES` 环境变量

### 修复
- **stats 端点数据源错误**：原逻辑直接调用外部 FXG API（受限/返回空），现改为读取 Redis/文件缓存的同步数据本地聚合
  - `blueprints/products.py`：循环查询 onSale/stock/violation 三个 tab 聚合
  - `blueprints/orders.py`：兼容 tabs 结构和扁平结构，标准化返回格式匹配前端 OrderStatsData 类型
- 同步任务缓存键一致性：确保 stats 端点读取的缓存键与同步任务写入一致

## [未发布]