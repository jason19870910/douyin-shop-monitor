# 抖音电商数据监控平台

面向抖店（FXG）与抖音创作者中心的数据采集、看板、合规与告警一体化监控平台。

## 1. 项目简介

- **数据采集**：app 容器内置调度器（schedule + threading）定时拉取商品、订单、创作者与作品数据，默认 60 分钟间隔（`SCHEDULE_INTERVAL_MINUTES`）
- **看板与业务页**：Dashboard、商品/订单、视频/创作者、账号、合规、告警
- **授权**：抖音开放平台 OAuth（登录 / 回调 / Token 刷新）
- **合规引擎**：关键词 / 规则检查与日志
- **告警**：销量、转化、库存、视频互动等阈值告警（邮件通知）
- **部署**：Docker Compose 3 容器（app / redis / frontend）+ 宿主机 systemd Nginx

## 2. 技术架构

```
                         ┌──────────────────────────────────────────┐
                         │        宿主机 (122.51.208.138)            │
                         │  systemd Nginx :443 (wlkj-tech.cn)        │
                         └───────────────┬──────────────────────────┘
                                         │
                    ┌────────────────────┼──────────────────┐
                    ▼                    ▼                  ▼
          ┌──────────────────┐  ┌───────────────┐  ┌────────────────┐
          │ frontend 容器    │  │ app 容器      │  │ redis 容器     │
          │ Nginx :3000→:80  │→ │ Flask :5000   │→│ 缓存/分布式锁  │
          │ React 静态资源   │  │ + 内置调度器  │  │                │
          └──────────────────┘  └───────┬───────┘  └────────────────┘
                                        │
                                        ▼
                        抖店 FXG / 抖音创作者中心 外部 API
```

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | React 18 + Vite 5 + TypeScript | Ant Design 5 深色主题，Recharts 图表 |
| 后端 | Flask 2.x | RESTful API，前缀 `/api/v1` |
| 定时任务 | 内置调度器（schedule + threading） | app 容器后台线程，60 分钟间隔 |
| 缓存 | Redis 7 | 共享缓存、Lua 原子操作、分布式锁 |
| 认证 | API Key 双 Header | `Authorization: Bearer <API_KEY>` 或 `X-API-Key: <API_KEY>`，任一通过即可 |

## 3. 快速开始

### 本地开发

```bash
# 后端
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r src/backend/requirements-dev.txt
pytest -c pytest.ini

# 前端
cd src/frontend
npm ci
npm run dev
```

### Docker 部署（生产形态）

```bash
cp config/.env.example config/.env      # 编辑填写真实值
docker compose up -d --build

# 访问
#   前台  https://wlkj-tech.cn
#   API   https://wlkj-tech.cn/api/v1/health
```

> 生产服务器（122.51.208.138）为宿主机 systemd Nginx（443）→ `frontend` 容器（3000）→ app 容器（5000），详见 [运维手册](operations/RUNBOOK.md)。

## 4. 文档地图

| 分类 | 文档 | 内容 |
|------|------|------|
| 项目治理 | [项目章程](governance/PROJECT_CHARTER.md) | 目标、范围、组织、验收标准 |
| 架构设计 | [系统架构](architecture/ARCHITECTURE.md)、[详细设计](architecture/DESIGN.md)、[前端设计](architecture/FRONTEND_DESIGN.md) | 组件、数据流、网络拓扑、前端规范 |
| API 规范 | [API 规范](api/API_SPEC.md) | 端点、认证、错误码、请求/响应示例 |
| 需求 | [需求规格](requirements/REQUIREMENTS.md)、[用户故事](requirements/USER_STORIES.md)、[验收标准](requirements/ACCEPTANCE_CRITERIA.md) | 需求追溯体系 |
| 运维 | [运维手册](operations/RUNBOOK.md)、[备份恢复](operations/BACKUP_RECOVERY.md)、[安全加固](operations/SECURITY_HARDENING.md)、[事件响应](operations/INCIDENT_RESPONSE.md)、[监控告警](operations/MONITORING_ALERTING.md) | 日常巡检、发布回滚、应急预案 |
| 质量 | [测试策略](quality/TESTING.md) | 分层测试、覆盖率要求 |
| 开发规范 | [编码规范](development/CODING_STANDARDS.md)、[Git 工作流](development/GIT_WORKFLOW.md)、[贡献指南](development/CONTRIBUTING.md) | 分支、提交、评审约定 |
| 风险 | [风险登记册](risk/RISK_REGISTER.md) | 风险识别、评估、跟踪 |
| 参考资料 | [术语表](reference/GLOSSARY.md)、[FAQ](reference/FAQ.md)、[故障排查](reference/TROUBLESHOOTING.md)、[权限矩阵](reference/PERMISSION.md) | 术语、答疑、排障速查 |
| 架构决策 | [ADR](adr/DECISIONS.md) | 重要架构决策记录 |

## 5. 常用端点速查

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查（免认证） |
| `/api/v1/health/external` | GET | 外部 API 连通性检查 |
| `/api/v1/dashboard/stats` | GET | 仪表盘聚合统计 |
| `/api/v1/sync/manual` | POST | 手动触发同步（需 API Key） |
| `/api/v1/sync/history` | GET | 同步历史（需 API Key） |

## 6. 维护信息

- **许可证**：内部私有项目，禁止外泄
- **联系方式**：通过企业微信联系项目负责人
- **变更记录**：见仓库根目录 `CHANGELOG.md`
