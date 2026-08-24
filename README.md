# 抖音电商数据监控平台

## 1. 项目概述
> 详细设计文档请查阅 [docs/DESIGN.md](docs/DESIGN.md)

- **背景**：抖音电商店铺缺乏统一的数据监控与告警手段，导致运营决策滞后、异常难以及时发现。
- **核心目标**：构建一套稳健、可维护的抖音店铺监控系统，提供商品、订单、创作者等数据的实时查询、可视化与异常告警，支持每日自动抓取。
- **目标受众**：抖音店铺运营人员、业务分析师、技术运维团队。

## 2. 目录结构

```
douyin/
├── .github/workflows/       # CI/CD 工作流（GitHub Actions）
├── docs/                     # 项目文档（架构、设计、规范等）
├── nginx/                    # Nginx 反向代理配置
│   ├── nginx.conf
│   └── conf.d/wlkj-tech.cn.conf
├── opt/douyin-platform/apps/monitor/   # 后端服务（Flask + Celery）
│   ├── blueprints/          # API 路由模块
│   ├── services/            # 业务服务（数据抓取、规则引擎）
│   ├── migrations/          # 数据库迁移
│   ├── scripts/             # 运维脚本
│   │   └── fixes/           # 历史修复脚本
│   ├── tests/               # 测试用例
│   ├── tools/               # 辅助工具
│   ├── secrets/             # 敏感配置（不入 git）
│   ├── app.py               # Flask 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # 前端项目（React + Vite，独立 git 仓库）
├── scripts/                  # 项目级脚本（PowerShell）
├── docker-compose.yml        # 统一服务编排
├── Makefile                  # 构建/部署入口
└── .gitignore
```

## 3. 技术架构概览
```
+-------------------+      +-------------------+      +-------------------+
|   Frontend React  | <----|   Nginx (反向代理)| <----|   外部用户        |
+-------------------+      +-------------------+      +-------------------+
       ^   ^                     ^   ^
       |   |                     |   |
       |   +--- /api/* ----->+-------------------+
       |                       |   Flask API      |
       |                       |   (monitor)      |
       |                       +-------------------+
       |                              ^   ^
       |                              |   |
       |                              |   +--- Celery Beat + Workers
       |                              +--- Redis 共享缓存
       |
       +--- Docker Compose 编排所有服务
```

### 核心技术栈
| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **前端** | React + Vite | 18 / 5.x | TypeScript 严格模式，深色主题 |
| **UI 库** | Ant Design | 5.x | 全量组件深色样式覆盖 |
| **图表** | Recharts | 2.x | 趋势图、饼图、迷你图 |
| **后端** | Flask | 2.x | RESTful API |
| **异步任务** | Celery + Redis | 5.x / 7.x | Beat + Worker 4 服务编排 |
| **缓存** | Redis | 7.x | 共享缓存、Lua 原子操作 |
| **部署** | Docker + Nginx | - | 容器化、反向代理、SSL |

## 4. 服务编排（docker-compose.yml）

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| `monitor` | douyin_monitor | 5000 | Flask API + Gunicorn |
| `celery_worker` | douyin_celery_worker | - | Celery 异步任务执行 |
| `celery_beat` | douyin_celery_beat | - | Celery 定时任务调度 |
| `redis` | douyin_redis | 6379 | 共享缓存 + Celery Broker |
| `frontend` | douyin_frontend | 3000 | React 静态资源 + Nginx |
| `nginx` | douyin_nginx | 80/443 | 反向代理 + SSL 终端 |

## 5. 快速开始

### 5.1 环境准备
```bash
# 克隆代码
git clone <repo-url>
cd douyin

# 配置后端环境变量
cp opt/douyin-platform/apps/monitor/.env.example opt/douyin-platform/apps/monitor/.env
# 编辑 .env 填写真实值（Cookie、API 地址、告警邮箱等）

# 配置敏感信息（secrets）
# 将各 secret 文件放入 opt/douyin-platform/apps/monitor/secrets/
```

### 5.2 启动服务（推荐）
```bash
# 使用 Makefile（推荐）
make up

# 或直接使用 docker compose
docker compose up -d

# 查看服务状态
make ps
make health
```

### 5.3 本地开发
```bash
# 后端
cd opt/douyin-platform/apps/monitor
pip install -r requirements.txt
python app.py

# 前端
cd frontend
npm install
npm run dev
```

### 5.4 访问地址
- **生产**：https://wlkj-tech.cn
- **本地 Docker**：http://localhost:3000（前端）、http://localhost:5000/api/v1（API）
- **健康检查**：https://wlkj-tech.cn/health

## 6. 环境变量与密钥管理

### 6.1 环境变量
完整配置项见 [opt/douyin-platform/apps/monitor/.env.example](opt/douyin-platform/apps/monitor/.env.example)

### 6.2 敏感信息（Secrets）
通过 `docker-compose.yml` 的 `secrets:` 部分加载，文件存放于：
```
opt/douyin-platform/apps/monitor/secrets/
├── douyin_app_id.txt
├── douyin_app_secret.txt
├── douyin_access_token.txt
├── fxg_cookies.txt
├── creator_cookies.txt
├── token.txt
├── ms_token.txt
├── a_bogus.txt
├── verify_fp.txt
├── fp.txt
├── fxg_shop_id.txt
├── fxg_log_id.txt
└── api_key.txt
```

> **注意**：secrets 目录已加入 `.gitignore`，不会提交到 git。生产环境通过部署脚本分发。

## 7. 构建与部署

### 7.1 使用 Makefile（推荐）
```bash
make build          # 构建所有镜像
make up             # 启动服务
make deploy         # 生产部署（构建+启动）
make deploy-dev     # 开发环境部署
make ssl-init       # 初始化 SSL 证书
make ssl-renew      # 续期 SSL 证书
```

### 7.2 常用命令
```bash
make logs              # 查看所有服务日志
make logs-monitor      # 查看 monitor 日志
make test              # 运行所有测试
make test-monitor      # 运行后端测试
make test-frontend     # 运行前端测试
make lint              # 代码检查
make format            # 代码格式化
make backup            # 备份项目
make health            # 健康检查
make status           # 服务状态
```

### 7.3 SSL 证书管理
```bash
# 初始化（首次）
make ssl-init

# 续期（定期执行，建议加入 cron）
make ssl-renew
```

## 8. API 接口

### 核心接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/dashboard/stats` | GET | 仪表盘聚合统计 |
| `/api/v1/products` | GET | 商品分页列表 |
| `/api/v1/orders` | GET | 订单分页列表 |
| `/api/v1/creators` | GET | 创作者列表 |
| `/api/v1/compliance` | GET | 合规列表 |
| `/api/v1/compliance/rules` | GET/POST/PUT/DELETE | 合规规则 CRUD |
| `/api/v1/alerts/dian/config` | GET/POST | 抖店告警配置 |
| `/api/v1/sync` | POST | 手动触发全量同步 |

> 完整 API 规范见 [opt/douyin-platform/apps/monitor/INTERNAL-API-SPEC.md](opt/douyin-platform/apps/monitor/INTERNAL-API-SPEC.md)

## 9. 测试与质量

```bash
# 后端测试
make test-monitor
# cd opt/douyin-platform/apps/monitor && python -m pytest tests/ -v --cov=app

# 前端测试
make test-frontend
# cd frontend && npm test -- --watchAll=false --ci

# 代码检查
make lint

# 代码格式化
make format
```

## 10. 文档索引

### 核心文档
| 文档 | 说明 |
|------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构概览 |
| [docs/DESIGN.md](docs/DESIGN.md) | 详细设计文档 |
| [docs/FRONTEND_DESIGN.md](docs/FRONTEND_DESIGN.md) | 前端设计文档 |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | 需求规格 |
| [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) | 项目章程 |

### 运维文档
| 文档 | 说明 |
|------|------|
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | 运维手册 |
| [docs/SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md) | 安全加固指南 |
| [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) | 测试策略 |
| [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md) | 风险登记册 |

### API 规范
| 文档 | 说明 |
|------|------|
| [opt/.../INTERNAL-API-SPEC.md](opt/douyin-platform/apps/monitor/INTERNAL-API-SPEC.md) | 内部 RESTful API 规范 |
| [opt/.../EXTERNAL-API-SPEC.md](opt/douyin-platform/apps/monitor/EXTERNAL-API-SPEC.md) | 外部 API 详细规范 |

### 后端文档
| 文档 | 说明 |
|------|------|
| [opt/.../monitor/README.md](opt/douyin-platform/apps/monitor/README.md) | 后端服务详细文档 |
| [opt/.../monitor/CHANGELOG.md](opt/douyin-platform/apps/monitor/CHANGELOG.md) | 版本变更记录 |

## 11. CI/CD

GitHub Actions 工作流定义于 [.github/workflows/ci.yml](.github/workflows/ci.yml)，包含：
1. **Cleanup & Lint**：清理备份文件、Python/Node 代码检查
2. **Test**：运行后端 pytest 和前端 Jest 测试，上传覆盖率
3. **Build**：构建 Docker 镜像并推送至 ghcr.io
4. **Deploy**：生产环境部署（需配置 SSH secrets）
5. **Notify Failure**：失败通知

## 12. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 前端 403 Forbidden | 文件权限不正确 | `chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 ...` |
| 前端路由刷新 404 | Nginx 未配置 fallback | `try_files $uri $uri/ /index.html;` |
| 修改 .env 不生效 | 进程未重启 | `docker compose restart` |
| 抓取数据全为 0 | 外部 API 字段缺失 | 检查外部服务返回字段 |
| Celery 任务未执行 | Redis 未就绪 | `docker compose logs redis` 检查 |
| SSL 证书过期 | 未续期 | `make ssl-renew` |

## 13. 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feat/xxx`
3. 提交变更：`git commit -m "feat: xxx"`
4. 推送分支：`git push origin feat/xxx`
5. 发起 Pull Request

---

**维护团队**：抖音电商数据监控平台项目组
**联系方式**：通过企业微信联系项目负责人
**License**：内部私有项目，禁止外泄
