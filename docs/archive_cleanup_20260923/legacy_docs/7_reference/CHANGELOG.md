# Changelog

All notable changes to the Douyin Monitor Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.0] - 2026-08-29

### 🎉 Major Architecture Overhaul

#### Added
- **统一 Docker Compose 编排**: 根目录 `docker-compose.yml` 管理所有服务，支持 `docker-compose.prod.yml` 生产环境覆盖
- **Docker 网络隔离**: 自定义 bridge 网络 `douyin-network`，服务间通过容器名通信
- **容器化 Nginx (`douyin_nginx`)**: 统一管理所有子域名路由、SSL 终止、反向代理、安全头、速率限制
- **Docker DNS Resolver**: nginx.conf 配置 `resolver 127.0.0.11` 实现运行时 upstream 动态解析，解决容器重启后 IP 变更问题
- **前端容器化部署 (`douyin_frontend`)**: 内部 Nginx 处理 SPA 路由 fallback、静态资源长期缓存、健康检查端点
- **14 个 Docker Secrets**: 敏感信息完全通过 Docker Secrets 管理，优先级高于环境变量
- **OAuth 2.0 完整流程**: `/auth/qr-code` → 二维码 → 扫码授权 → `/auth/callback` 换 token → `localStorage.authToken`
- **skipAuth 机制**: apiClient 支持 `config.skipAuth === true` 跳过 Authorization 头注入，解决登录前/登出后 401 问题

#### Changed
- **Nginx 部署模式**: 从宿主机 systemd Nginx 迁移到 Docker 容器，停用 `systemctl stop nginx`
- **前端部署模式**: 从 scp 同步构建产物到宿主机，改为前端源码同步 + 容器内构建/服务
- **子域名管理**: 从 `/etc/nginx/sites-enabled/` 迁移到 Docker nginx `conf.d/` 统一管理
- **OAuth Scope 扩展**: 从 7 个权限扩展到 15 个权限，与 PERMISSION.md "已获得权限列表" 完全一致
- **配置管理**: 迁移到 pydantic-settings (`config/settings.py`)，支持 Docker Secrets、环境变量、.env 分层优先级
- **数据目录**: 统一为容器内 `/data`，宿主机对应 `/opt/douyin-platform/data/`
- **API 基础路径**: 统一为 `/api/v1/` 前缀，预留版本化空间

#### Fixed
- **host not found in upstream**: Docker DNS resolver 解决容器重启后 upstream 解析失败
- **前端 401 循环**: 统一 token key 为 `authToken`，authApi 使用 `skipAuth: true`
- **nginx 端口冲突**: 停用宿主机 nginx 释放 80/443 端口给 Docker nginx
- **data_source 返回时间戳**: `manual_sync` 使用 `get_mock_status()` 正确计算整体数据源
- **redirect_uri secret 缺失**: 新增 `redirect_uri.txt` secret 并挂载到 monitor 容器

#### Security
- 所有敏感信息 (Cookie、Token、签名参数、OAuth 凭证) 通过 Docker Secrets 注入，不再写入镜像或 .env
- Nginx 安全头完善: HSTS、X-Frame-Options、X-Content-Type-Options、CSP、Referrer-Policy
- 速率限制: API 10r/s 突发 20，登录 5r/m 突发 5

---

## [v1.5.0] - 2026-08-26

### Added
- OpenAPI 3.0 规范 (`api/openapi.yaml`) 作为单一事实源
- CI 自动化 pipeline (`.github/workflows/api-docs.yml`): OpenAPI 验证、TS 类型生成、契约测试、文档同步检查
- API 文档归档: 4 个重复文档移至 `docs/archive/2_api/`
- PERMISSION.md 权限能力文档，记录已获得/未获得权限列表

### Changed
- API_DOCUMENTATION.md 重构: 明确区分三层架构 (前端内部 API、后端代理转发 API、外部原始 API)
- 认证方式对照表: 明确前端→后端 (Bearer token) 与 后端→外部 (Cookie+签名) 两套完全不同的认证机制

### Fixed
- 修复 apiClient VITE_API_KEY 回退逻辑导致的未授权请求
- 修复 Sidebar 标题不显示 (token key 不一致: `token` vs `authToken`)

---

## [v1.4.0] - 2026-08-22

### Added
- 手动同步接口 `POST /api/v1/sync` 返回 `data_source: "real"|"mock"|"empty"`
- `get_mock_status()` 函数检测各数据源真实/模拟/空状态
- 企业微信告警 Webhook 集成
- 数据抓取熔断器设计 (待实现)

### Changed
- 后端配置迁移: 删除旧 `config.py`，统一使用 `config/settings.py` (pydantic-settings)
- 定时任务间隔可配置: `SCHEDULE_INTERVAL_MINUTES` 环境变量

### Fixed
- 修复 `/data` 目录在容器中不存在导致的写入失败 (`DATA_DIR.mkdir(parents=True, exist_ok=True)`)
- 修复 Celery Worker 内存泄漏风险 (添加 `--max-tasks-per-child=100` 建议)

---

## [v1.3.0] - 2026-08-15

### Added
- 动态签名生成 (`douyin_sign.py`): V8 执行 JS 算法实时计算 `a_bogus`
- 统一数据抓取服务 (`services/fetcher.py`): 重试机制、签名注入、缓存策略
- 6 个外部 API 代理转发端点
- 合规管理模块: 规则引擎、检测任务、导出功能

### Changed
- 外部 API 调用统一通过 `fetcher._request()` 处理 Cookie、签名、参数注入
- 请求头统一管理: `Config.COMMON_HEADERS` 计算属性

---

## [v1.2.0] - 2026-08-01

### Added
- 前端 Design Tokens 系统: 200+ CSS Variables、TypeScript 令牌、全量组件覆盖
- React Query 风格 `useApi` Hook: 加载/错误/重试/轮询统一处理
- 深色主题完整适配 Ant Design 5.x 组件

### Changed
- 样式方案: 从 styled-components 迁移到 CSS Modules + CSS Variables
- 状态管理: 从 Redux 迁移到 React Hooks + Context

---

## [v1.1.0] - 2026-07-15

### Added
- Celery 分布式任务队列: Worker + Beat 架构
- Redis 缓存层: 解决多进程数据一致性
- 定时数据抓取: 商品、订单、创作者数据
- 告警系统: 阈值检测、邮件通知

---

## [v1.0.0] - 2026-07-01

### Added
- 初始版本: React + Flask + Redis 基础架构
- 商品/订单/创作者基础 CRUD API
- 简单的定时任务 (APScheduler)
- 基础前端页面: 仪表盘、列表、详情

---

## 版本说明

| 版本类型 | 说明 | 示例 |
|----------|------|------|
| **Major (vX.0.0)** | 架构重大变更、不兼容 API 变更 | v2.0.0: Docker 化、Nginx 容器化 |
| **Minor (vX.Y.0)** | 新增功能、向后兼容 | v1.5.0: OpenAPI、CI 自动化 |
| **Patch (vX.Y.Z)** | Bug 修复、小幅优化 | v1.4.1: 修复 data_source 返回格式 |

---

## 升级指南

### v1.x → v2.0.0 (破坏性变更)

**必须操作**:
1. 服务器执行 `systemctl stop nginx` 停用宿主机 nginx
2. 配置所有 14 个 Docker Secrets (见 DEPLOY_GUIDE.md)
3. 更新 `.env` 中的 `DOUYIN_SCOPE` 为抖音开放平台控制台实际授权的 OAuth scope 代码（当前仅 `user_info`）
4. 运行 `docker compose up -d --build` 重新构建所有服务
5. 验证 `https://wlkj-tech.cn/` 和 `https://api.wlkj-tech.cn/` 均可访问

**配置迁移**:
- 旧 `/opt/douyin-platform/apps/monitor/.env` → 新 `/opt/douyin-platform/config/.env`
- 旧宿主机 nginx 配置 → 新 `/opt/douyin-platform/nginx/conf.d/*.conf`
- 旧前端构建产物目录 → 新前端源码目录 (`src/frontend/`)

---

*最后更新：2026-08-29*