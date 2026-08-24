# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 统一深色主题设计系统 (Design Tokens)
- 前端 CSS Variables 设计令牌体系 (200+ 变量)
- 全量 Ant Design 5.x 组件样式覆盖 (`src/index.css`)
- TypeScript 设计令牌定义 (`src/theme/tokens.ts`)
- 组件级 CSS Modules 样式隔离
- Recharts 图表集成（趋势图、饼图、迷你图）
- 动态侧边栏菜单（home/douyin/dian/alerts 四套菜单）
- `useApi` Hook 统一数据获取（加载、错误、重试、轮询）
- `axios` 实例封装（拦截器、错误归一化、取消令牌）
- 格式化工具库 (`formatters.ts`)

### Changed
- **前端框架升级**：Create React App → Vite 5.x
- **语言升级**：JavaScript → TypeScript 严格模式
- **主题重构**：浅色主题 → 统一深色主题 (`#001529`)，与侧边栏色调一致
- **样式架构**：内联样式/零散 CSS → Design Tokens + CSS Modules + 全局覆盖
- **构建工具**：react-scripts → Vite，构建速度提升 3x+
- **API 客户端**：统一错误处理、自动重试（指数退避）、请求取消
- **路由结构**：扁平化 → 嵌套动态侧边栏路由
- **部署流程**：新增前端构建部署脚本、权限修复步骤

### Fixed
- Nginx 静态资源 403 Forbidden（权限修复：`chown -R monitor:project_admins`）
  - **2026-08-22 问题记录**：使用 `scp` 部署前端构建产物时，文件以 `root` 所有者复制到服务器，而 Nginx worker 进程以 `nginx` 用户运行，无法读取文件导致 403 Forbidden。解决：`chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 ...`。后续部署需在脚本中自动修复权限。
- Ant Design 组件深色模式样式不兼容（全量覆盖 20+ 组件）
- 表格空状态 "暂无数据" 背景色异常
- CSS Variables 在 Vite 构建中未生成（修正 `@import` 路径）
- TypeScript 类型错误（InputNumber step prop、dayjs 导入、reduce 类型推断）
- 前端路由刷新 404（Nginx `try_files $uri $uri/ /index.html`）

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

[Unreleased]: https://github.com/yourusername/doudian_monitor/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v1.1.0
[1.0.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v1.0.0
[0.1.0]: https://github.com/yourusername/doudian_monitor/releases/tag/v0.1.0