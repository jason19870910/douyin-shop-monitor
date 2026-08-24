# 抖音电商数据监控平台

## 1. 项目概述
> 详细设计文档请查阅 [DESIGN.md](DESIGN.md)

- **背景**：抖音电商店铺缺乏统一的数据监控与告警手段，导致运营决策滞后、异常难以及时发现。
- **核心目标**：构建一套稳健、可维护的抖音店铺监控系统，提供商品、订单、创作者等数据的实时查询、可视化与异常告警，支持每日自动抓取。
- **目标受众**：抖音店铺运营人员、业务分析师、技术运维团队。

## 2. 技术架构概览
```
+-------------------+      +-------------------+      +-------------------+
|   Frontend React  | <--->|   Flask API（app）| <--->| External Data API |
+-------------------+      +-------------------+      +-------------------+
       ^   ^                     ^   ^                     ^   ^
       |   |                     |   |                     |   |
       |   |                     |   |                     |   +--- HTTP GET (JSON)
       |   |                     |   +--- Celery Beat + Workers
       |   +--- Nginx 反向代理   +--- Docker / Docker‑Compose
       +--- Systemd service (doudian_monitor.service)
       |                                 |
       |                                 v
       |                         +-------------------+
       +------------------------->|   共享缓存        |
                                  |   (Redis)         |
                                  +-------------------+
```

### 核心技术栈
| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **前端** | React + Vite | 18 / 5.x | TypeScript 严格模式，深色主题 |
| **UI 库** | Ant Design | 5.x | 全量组件深色样式覆盖 |
| **状态管理** | React Hooks + Context | - | `useApi` 统一数据获取 |
| **图表** | Recharts | 2.x | 趋势图、饼图、迷你图 |
| **样式** | CSS Modules + CSS Variables | - | Design Tokens 体系 |
| **后端** | Flask | 2.x | RESTful API |
| **异步任务** | Celery + Redis | 5.x / 7.x | Beat + Worker 4 服务编排 |
| **缓存** | Redis | 7.x | 共享缓存、Lua 原子操作 |
| **部署** | Docker + Nginx + Systemd | - | 容器化、反向代理、进程管理 |

## 3. 项目里程碑
| 里程碑 | 完成日期 | 产出 |
|--------|---------|------|
| 需求梳理 | 2026‑07‑01 | 需求文档 |
| 架构设计 | 2026‑07‑05 | 架构图、技术选型 |
| 核心功能实现 | 2026‑08‑01 | API、前端页面 |
| 外部 API 重构 | 2026‑08‑12 | 双域名、Celery 编排 |
| **统一深色主题** | **2026‑08‑22** | **Design Tokens、全量组件覆盖** |
| 自动化测试 & CI/CD | 2026‑08‑25 | 测试覆盖、GitHub Actions |
| Docker 化 & 部署 | 2026‑08‑28 | 镜像、systemd、Nginx 配置 |
| 项目验收 | 2026‑09‑01 | 交付物检查、验收报告 |

## 4. 功能模块

### 4.1 仪表盘 (`/dashboard`)
- **核心指标**：总销量、总收入、订单数、转化率、商品总数、创作者粉丝
- **趋势图表**：销量/收入/订单/转化率 4 维度趋势 (Recharts)
- **热销商品 TOP 10**：增长率、库存预警、转化率
- **订单看板**：状态分布饼图、趋势迷你图、最新订单列表
- **创作者数据**：粉丝总数、今日新增、互动率、增长趋势
- **数据源状态**：实时/模拟数据标识、健康检查、告警提示

### 4.2 抖店管理 (`/dian/*`)
| 页面 | 路由 | 功能 |
|------|------|------|
| 商品管理 | `/dian/products` | 分页、搜索、详情抽屉、导出 CSV |
| 数据中心 | `/dian/orders` | 分页、多维筛选、金额格式化、导出 CSV |
| 合规管理 | `/dian/compliance` | 风险分布图表、违规列表、规则增删改查、一键检测 |
| 视频编辑 | `/dian/video-edit` | 占位页 |
| 图片编辑 | `/dian/image-edit` | 占位页 |
| 账号管理 | `/dian/account` | 账号列表管理 |

### 4.3 抖音管理 (`/douyin/*`)
| 页面 | 路由 | 功能 |
|------|------|------|
| 视频管理 | `/douyin/videos` | 视频列表 |
| 创作者中心 | `/douyin/creator` | 创作者列表、详情 |
| 授权管理 | `/auth` | OAuth 授权流程 |

### 4.4 告警设置 (`/alerts/*`)
| 页面 | 路由 | 功能 |
|------|------|------|
| 抖店告警 | `/alerts/dian` | 销量下跌、退款率上升、合规风险阈值 |
| 抖音告警 | `/alerts/douyin` | 播放量下跌、点赞下跌、粉丝流失阈值 |

### 4.5 个人中心 (`/profile`)
- 用户信息、偏好设置

## 5. API 接口规范
详见 [INTERNAL-API-SPEC.md](INTERNAL-API-SPEC.md) 和 [EXTERNAL-API-SPEC.md](EXTERNAL-API-SPEC.md)

### 核心内部接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/dashboard/stats` | GET | 仪表盘聚合统计 |
| `/api/products` | GET | 商品分页列表 |
| `/api/orders` | GET | 订单分页列表 |
| `/api/creators` | GET | 创作者列表 |
| `/api/compliance` | GET | 合规列表 |
| `/api/compliance/stats` | GET | 合规统计 |
| `/api/compliance/rules` | GET/POST/PUT/DELETE | 合规规则 CRUD |
| `/api/compliance/check` | POST | 触发合规检测 |
| `/api/alerts/dian/config` | GET/POST | 抖店告警配置 |
| `/api/alerts/douyin/config` | GET/POST | 抖音告警配置 |
| `/api/sync` | POST | 手动触发全量同步 |

## 6. 环境配置
> 完整配置项见 [.env.example](.env.example)

### 必填关键变量
```bash
# 双域名基础 URL
FXG_BASE_URL=https://api.fxg.example.com
CREATOR_BASE_URL=https://api.creator.example.com

# 认证签名参数
__TOKEN=xxx
MS_TOKEN=xxx
a_bogus=xxx
verifyFp=xxx
fp=xxx

# 完整 Cookie（从浏览器开发者工具复制）
FXG_COOKIES="sessionid=xxx; csrftoken=xxx;"
CREATOR_COOKIES="sessionid=xxx; csrftoken=xxx;"

# Celery Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 可选：告警邮件
ALERT_EMAIL=alert@example.com
```

## 7. 部署指南

### 7.1 Docker 部署（推荐生产）
```bash
cd apps/monitor
cp .env.example .env
# 编辑 .env 填写真实值
docker-compose build
docker-compose up -d
```
服务端口：`monitor:5000` (Flask API + 静态前端)、`redis:6379`

### 7.2 前端独立构建部署
```bash
cd apps/monitor/frontend
npm install
npm run build
# 同步至服务器
scp -r build/* root@server:/opt/douyin-platform/apps/monitor/frontend/build/
# 修复权限（关键！避免 403 Forbidden）
ssh root@server "chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 /opt/douyin-platform/apps/monitor/frontend/build"
```

### 7.3 Nginx 反向代理
```nginx
server {
    listen 443 ssl http2;
    server_name wlkj-tech.cn;

    ssl_certificate /etc/letsencrypt/live/wlkj-tech.cn-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wlkj-tech.cn-0001/privkey.pem;

    root /opt/douyin-platform/apps/monitor/frontend/build;
    index index.html;

    location /assets/ {
        alias /opt/douyin-platform/apps/monitor/frontend/build/assets/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ^~ /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 200M;
    }
}
```

### 7.4 Systemd 服务
```bash
sudo cp doudian_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now doudian_monitor
```

## 8. 快速开始
```bash
# 1. 克隆代码
git clone <repo-url>
cd douyin-platform/apps/monitor

# 2. 配置环境
cp .env.example .env
# 编辑 .env 填写 Cookie、API 地址等

# 3. 启动服务
docker-compose up -d

# 4. 访问前端
# https://wlkj-tech.cn (生产) 或 http://localhost:5000 (本地 Docker)

# 5. 手动同步数据
curl -X POST https://wlkj-tech.cn/api/sync

# 6. 配置告警阈值
# 访问 https://wlkj-tech.cn/alerts/dian 或 /alerts/douyin
```

## 9. 质量保障
- **单元测试**：`pytest -q`，覆盖率 ≥ 80%
- **代码风格**：`flake8`、`black`、`mypy` (Python)；`eslint`、`tsc` (TypeScript)
- **CI/CD**：GitHub Actions 自动执行 lint、test、docker build
- **部署流水线**：推送镜像至 Docker Hub，生产服务器滚动升级

## 10. 文档索引

### 核心文档
| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目总览（本文档） |
| [DESIGN.md](DESIGN.md) | 详细设计文档（架构、数据流、部署、前端设计） |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构概览（组件、数据流、网络拓扑、扩展性） |
| [FRONTEND_DESIGN.md](FRONTEND_DESIGN.md) | 前端设计文档（技术栈、主题、组件、API、代码组织） |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

### 配置与环境
| 文档 | 说明 |
|------|------|
| [.env.example](.env.example) | 环境变量示例文件 |
| [config.py](config.py) | 环境变量封装类 |

### 后端代码
| 文档 | 说明 |
|------|------|
| [app.py](app.py) | Flask 应用入口 |
| [requirements.txt](requirements.txt) | Python 依赖列表 |
| [celery_config.py](celery_config.py) | Celery 配置与调度 |
| [tasks.py](tasks.py) | Celery 任务实现 |
| [services/fetcher.py](services/fetcher.py) | 外部 API 数据抓取 |
| [services/rule_engine.py](services/rule_engine.py) | 合规规则引擎 |

### 部署运维
| 文档 | 说明 |
|------|------|
| [Dockerfile](Dockerfile) | 镜像构建文件 |
| [docker-compose.yml](docker-compose.yml) | Docker-Compose 编排（4 服务） |
| [doudian_monitor.service](doudian_monitor.service) | Systemd 服务文件 |
| [nginx.conf](nginx.conf) | Nginx 反向代理配置 |

### CI/CD
| 文档 | 说明 |
|------|------|
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | GitHub Actions 工作流 |

### API 规范
| 文档 | 说明 |
|------|------|
| [INTERNAL-API-SPEC.md](INTERNAL-API-SPEC.md) | 内部 RESTful API 规范 |
| [EXTERNAL-API-SPEC.md](EXTERNAL-API-SPEC.md) | 外部 API 详细规范 |
| [API-SPEC.md](API-SPEC.md) | API 规范概览 |
| [API_DOC.md](API_DOC.md) | API 文档补充 |

### 项目治理
| 文档 | 说明 |
|------|------|
| [PROJECT_CHARTER.md](PROJECT_CHARTER.md) | 项目章程 |
| [REQUIREMENTS.md](REQUIREMENTS.md) | 需求规格 |
| [QUALITY_PLAN.md](QUALITY_PLAN.md) | 质量计划 |
| [RISK_REGISTER.md](RISK_REGISTER.md) | 风险登记册 |
| [COMMUNICATION_PLAN.md](COMMUNICATION_PLAN.md) | 沟通计划 |
| [SECURITY_HARDENING.md](SECURITY_HARDENING.md) | 安全加固指南 |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | 测试策略 |
| [RUNBOOK.md](RUNBOOK.md) | 运维手册 |
| [ISSUE_ANALYSIS.md](ISSUE_ANALYSIS.md) | 问题分析报告 |

## 11. 当前任务执行状态

| 编号 | 任务 | 状态 | 优先级 | 备注 |
|------|------|------|--------|------|
| 1 | 统一深色主题设计系统 | ✅ 已完成 | 🔴 高 | Design Tokens、全量 Ant Design 覆盖 |
| 2 | 前端框架升级 (CRA → Vite) | ✅ 已完成 | 🔴 高 | TypeScript 严格模式 |
| 3 | 外部 API 集成重构 | ✅ 已完成 | 🔴 高 | 双域名、_request 统一请求 |
| 4 | Celery 4 服务编排 | ✅ 已完成 | 🔴 高 | monitor/worker/beat/redis |
| 5 | Redis 共享缓存层 | ✅ 已完成 | 🔴 高 | Lua 原子操作、防击穿 |
| 6 | Nginx 反向代理 + HTTPS | ✅ 已完成 | 🔴 高 | 静态资源、API 代理、Gzip |
| 7 | Systemd 服务管理 | ✅ 已完成 | 🟡 中 | 开机自启、日志集成 |
| 8 | 文档体系完善 | ✅ 已完成 | 🟡 中 | 12+ 核心文档 |
| 9 | CI/CD 流水线 | 🟡 进行中 | 🟡 中 | GitHub Actions |
| 10 | 单元测试覆盖率 ≥ 80% | 🟡 进行中 | 🟢 低 | pytest + Jest |

> **更新时间**: 2026-08-22  
> **当前版本**: v1.1.0 (深色主题版本)  
> **当前阶段**: 核心功能完成，进入测试验收与文档完善阶段

---

## 12. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 前端 403 Forbidden | 文件权限不正确 | `chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 ...` |
| 前端路由刷新 404 | Nginx 未配置 fallback | `try_files $uri $uri/ /index.html;` |
| 修改 .env 不生效 | 进程未重启 | `docker-compose restart` 或 `systemctl restart doudian_monitor` |
| 抓取数据全为 0 | 外部 API 字段缺失 | 检查外部服务返回 `sales_today`、`sales_yesterday` 等字段 |
| 多 Worker 缓存不一致 | 未使用共享缓存 | 已迁移至 Redis + Lua 原子操作 |
| Ant Design 组件样式异常 | 深色主题未覆盖 | 已在 `src/index.css` 全量覆盖 20+ 组件 |

---

## 13. 贡献指南
1. Fork 项目
2. 创建特性分支：`git checkout -b feat/xxx`
3. 提交变更：`git commit -m "feat: xxx"`
4. 推送分支：`git push origin feat/xxx`
5. 发起 Pull Request

---

**维护团队**：抖音电商数据监控平台项目组  
**联系方式**：通过企业微信/钉钉联系项目负责人  
**License**：内部私有项目，禁止外泄