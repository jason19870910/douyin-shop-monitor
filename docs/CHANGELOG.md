# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **首页重构**：路由 `path="/"` 切换为 HomePage，实现 4 模块竖向布局（商品统计、订单统计、创作者概览、系统健康），左侧栏保持不变
- **Home.tsx 新建**：按外部 API 字段做字段回退映射与加载态统一，使用 `Spin` 加载、`Empty` 空态
- **核心外部 API 对接**：
  - 商品统计：`GET /api/v1/products/stats` → 外部 `GET /product/tproduct/aggsProductCount` (tab=onSale/stock/violation)
  - 订单统计：`GET /api/v1/orders/stats` → 外部 `GET /api/order/tabcnt` (all/pay/cancel)
  - 创作者概览：`GET /api/v1/creators/overview` → 外部 `POST /janus/douyin/creator/data/overview/dashboard`（内部已统一为 GET）
- **前端鉴权统一**：`apiClient` 拦截器同时发送 `Authorization: Bearer <API_KEY>` + `X-API-Key: <API_KEY>`
- **Docker 部署流程文档化**：`npm run build` → `scp` → `docker cp` → `nginx -s reload`

### Changed

- **API 路径前缀统一**：`baseURL` 设为 `/api/v1`，所有相对路径不带前导 `/`（如 `/creators/overview`、`/products/stats`、`/orders/stats`、`/health`）
- **creatorApi.getCreatorOverview**：从 `POST /janus/.../dashboard` 改为 `GET /creators/overview`，参数 `recent_days`
- **路由入口**：`App.tsx` 中 `path="/"` 由 `DashboardPage` 切换为 `HomePage`
- **前端部署方式**：从 `scp` 到宿主机改为 `docker cp` 到容器 `eb6af2f375fe:/usr/share/nginx/html`

### Fixed

- **前端静态资源 403 Forbidden**：容器内文件属主为 root，Nginx 以 nginx 用户运行 → `chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755`
- **部署路径误用**：曾将构建产物 scp 到宿主机 `/usr/share/nginx/html`，实际服务由 Docker 容器 `eb6af2f375fe` 提供 → 改为 `docker cp` 到容器内
- **401 Unauthorized**：前后端 API_KEY 不一致，鉴权头缺失 → 统一 `Config.API_KEY` 与 `VITE_API_KEY`，拦截器同时发送双头
- **405 Method Not Allowed**：创作者概览调用 `POST /creators/overview/dashboard` → 改为 `GET /creators/overview` 并停止重试
- **404 Not Found**：路径拼接错误 `GET /api/v1/janus/douyin/creator/data/overview/dashboard` → 修正 baseURL 为 `/api/v1` + 相对路径 `/creators/overview`
- **资源取消加载/浏览器缓存旧构建**：强制刷新 + 重新构建部署

---

## [1.2.0] - 2026-09-23

### Added

- 首页重构：4 模块竖向布局（商品统计、订单统计、创作者概览、系统健康）
- 统一 API 路径前缀 `/api/v1` 与相对路径规范
- 前端鉴权双头（`Authorization: Bearer` + `X-API-Key`）
- Docker 前端部署标准流程文档

### Changed

- `creatorApi.getCreatorOverview` 从 POST 改为 GET
- `apiClient.baseURL` 统一为 `/api/v1`
- 首页路由由 Dashboard 切换为 Home

### Fixed

- 403 静态资源权限
- 401 鉴权失败
- 405 方法不允许
- 404 路径错误
- 部署路径错误（宿主机 vs 容器）

---

## [1.1.0] - 2026-08-22

### Added

- 统一深色主题设计系统
- Design Tokens 体系 (颜色、间距、圆角、阴影、字体、断点、动画、Z-index、布局)
- 语义化颜色分类：Primary/Success/Warning/Error/Neutral/Status/Sider/Trend
- 状态色深色适配：成功 `#95de64`、警告 `#ffd666`、错误 `#ff7875`、主色 `#69b1ff`

### Changed

- 前端全站背景色统一为 `#001529`（与侧边栏一致）
- 卡片/容器背景 `#001d3a`，表头/悬浮层 `#002751`
- 文字色：主 `#ffffff`、次 `rgba(255,255,255,0.65)`、三级 `rgba(255,255,255,0.45)`
- 边框色：半透明白色 `rgba(255,255,255,0.06/0.1/0.15)`
- 阴影增强适配深色背景（`rgba(0,0,0,0.3-0.6)`）

### Fixed

- Ant Design 组件默认浅色样式在深色背景下不可见问题
- 输入框、下拉框、模态框、抽屉、提示框等组件背景色/文字色
- 分页器、标签、面包屑、标签页、工具提示、气泡卡片等组件
- 滚动条、焦点环、文本选择样式深色适配

---

## [1.0.0] - 2026-08-12

### Added

- 外部 API 集成重构：双域名基础 URL (`FXG_BASE_URL`、`CREATOR_BASE_URL`)
- 统一请求函数 `_request`：URL 拼接、Header 注入、签名生成、指数退避重试
- Celery 4 服务编排：monitor、celery_worker、celery_beat、redis
- `doudian_monitor.service` Systemd 服务文件
- Nginx 反向代理配置（HTTPS、静态资源、API 代理、Gzip）
- `.env.example` 环境变量模板（含双域名、签名参数、Cookie、Celery 配置）
- Docker 多阶段构建优化
- GitHub Actions CI/CD 流水线
- 综合文档体系：README、DESIGN、ARCHITECTURE、FRONTEND_DESIGN、API-SPEC 等

### Changed

- 从抖音官方 API 迁移至可配置外部数据服务
- 配置管理：`config.py` 新增双域名、公共头部、Cookie 常量
- 数据同步：`fetch_and_store_*` 统一使用 `_request` 调用外部服务
- 缓存层：迁移至 Redis 共享缓存 (`redis_cache.RedisCache`)，支持 Lua 原子操作
- 告警系统：阈值可配置、支持邮件通知

### Fixed

- 多 Worker 下缓存不一致（Redis 共享缓存 + Lua 脚本）
- 外部 API 字段缺失导致前端显示 0（字段标准化默认值补全）
- 环境变量修改不生效（文档说明需重启服务）

---

## [0.1.0] - 2024-06-15

### Added

- Basic data fetching from Douyin/Doudian APIs
- Configuration management via .env
- Systemd service file for production deployment
- APScheduler for periodic data fetching (0,6,12,18 UTC)
- Email alert system via SMTP
- Docker support with multi-stage build
- GitHub Actions CI pipeline
- Pre-commit hooks (black, flake8, mypy)
- Comprehensive documentation

### Fixed

- Improved cookie parsing to support Netscape format
- Enhanced error handling with fallback to mock data

---

[Unreleased]: https://github.com/yourusername/doudian_monitor/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v1.2.0
[1.1.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v1.1.0
[1.0.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v1.0.0
[0.1.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v0.1.0