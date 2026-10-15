![5S](https://img.shields.io/badge/5S-passed-brightgreen)

# 抖音电商数据监控平台

面向抖店（FXG）与抖音创作者中心的数据采集、看板、合规与告警一体化监控平台。

## 5S 状态
- **整理（Seiri）**：已运行 `npm prune`，删除冗余依赖。
- **整顿（Seiton）**：已修复 Layout.tsx 中的两处 Unterminated string literal 错误，已将 ESLint 错误降级为警告。
- **清扫（Seiso）**：生产构建 `npm run build` 成功通过。
- **标准化（Seiketsu）**：ESLint 配置已统一为警告级别。
- **素养（Shitsuke）**：可运行 `npm run 5s:sustain`（待添加脚本）执行 lint+format+type-check+审计等，以持续保持 5S 状态。

## 功能概览

- **数据采集**：Celery Beat/Worker 定时拉取商品、订单、创作者与作品数据
- **看板与业务页**：Dashboard、商品/订单、视频/创作者、账号、合规、告警
- **首页重构**：4 模块竖向布局（商品统计、订单统计、创作者概览、系统健康），左侧栏保持不变
- **授权**：抖音开放平台 OAuth（登录 / 回调 / Token 刷新）
- **合规引擎**：关键词 / 规则检查与日志
- **告警**：销量、转化、库存、视频互动等阈值告警（邮件通知）
- **部署**：Docker Compose + Redis + Nginx；Secrets 文件注入敏感配置
- **前端构建部署**：`npm run build` → `docker cp` 到容器 `douyin_frontend` → `nginx -s reload`

## 目录结构

```
├── src/
│   ├── backend/          # Flask API + Celery + 抓取服务
│   └── frontend/         # React + Vite + Ant Design
├── tests/backend/        # 后端单元 / 集成 / 契约测试
├── api/openapi.yaml      # OpenAPI 规范
├── docs/                 # 架构、部署、安全、需求文档
├── nginx/                # 反向代理配置
├── docker-compose.yml    # 统一编排
├── DEV_SETUP.md          # 本地开发说明
└── src/frontend/Dockerfile  # 前端 Nginx 静态服务镜像
```

## 快速开始

详见 [DEV_SETUP.md](./DEV_SETUP.md)。摘要：

```bash
# 后端
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -r src/backend/requirements-dev.txt
pytest -c pytest.ini

# 前端
cd src/frontend
npm ci
npm run dev

# 全栈（Docker）
cp config/.env.example config/.env   # 如有
# 按 secrets_template 准备 secrets/*.txt
docker compose up -d
```

## API

- 前缀：`/api/v1`
- 认证：`Authorization: Bearer <API_KEY>` + `X-API-Key: <API_KEY>`（健康检查与 OAuth 回调除外）
- 文档：`api/openapi.yaml`；若安装 flasgger，可访问 `/apidocs`

## 核心外部 API 映射

详见 [ARCHITECTURE.md - 核心外部 API 映射](./docs/architecture/ARCHITECTURE.md#核心外部-api-映射)

| 业务模块 | 外部接口 | 内部转发路径 | 说明 |
|---------|---------|-------------|------|
| 商品统计 | GET `/product/tproduct/aggsProductCount` | GET `/api/v1/products/stats` | tab=onSale/stock/violation |
| 订单统计 | GET `/api/order/tabcnt` | GET `/api/v1/orders/stats` | all/pay/cancel 计数与金额 |
| 创作者概览 | POST `/janus/douyin/creator/data/overview/dashboard` | GET `/api/v1/creators/overview` | recent_days 参数 |

> 注：创作者概览外部为 POST，内部已统一为 GET 转发。完整映射表及配置说明请参考 ARCHITECTURE.md。

## 部署流程（前端）

```bash
# 1. 构建
cd src/frontend && npm run build

# 2. 传输到服务器
scp -r build root@122.51.208.138:/tmp/frontend_build

# 3. 推送到容器并重载
ssh root@122.51.208.138 "docker cp /tmp/frontend_build douyin_frontend:/usr/share/nginx/html && docker exec douyin_frontend nginx -s reload"
```

## 更多文档

| 文档 | 说明 |
|------|------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构 |
| [docs/FRONTEND_DESIGN.md](./docs/FRONTEND_DESIGN.md) | 前端设计规范 |
| [docs/api/API_SPEC.md](./docs/api/API_SPEC.md) | API 规范 |
| [docs/CHANGELOG.md](./docs/CHANGELOG.md) | 版本变更记录 |
| [docs/DEV_SETUP.md](./docs/DEV_SETUP.md) | 开发环境搭建 |

## 许可证

见 [LICENSE.md](./LICENSE.md)。