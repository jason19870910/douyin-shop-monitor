---
title: 常见问题解答 (FAQ)
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: PM
reviewers: [Tech Lead, 运维负责人, 业务分析师]
approvers: [PM]
classification: Public
doc_id: DOC-REF-002
tags: [参考, FAQ, 常见问题, 答疑, 故障自助]
related_docs: [DOC-REF-003, DOC-OPS-001, DOC-OPS-003, DOC-DEV-001]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - PM
---

# 常见问题解答 (FAQ)

## 目录
1. [环境搭建与部署](#1-环境搭建与部署)
2. [开发规范与工具](#2-开发规范与工具)
3. [数据同步与外部 API](#3-数据同步与外部-api)
4. [权限与认证](#4-权限与认证)
5. [性能优化](#5-性能优化)
5. [监控告警](#6-监控告警)
7. [常见报错与解决](#7-常见报错与解决)
8. [发布与版本管理](#8-发布与版本管理)

---

## 1. 环境搭建与部署

### Q1.1: 本地开发环境如何快速启动？
**A:** 使用 Docker Compose 一键启动完整栈：
```bash
# 1. 克隆代码
git clone https://github.com/your-org/douyin-monitor.git
cd douyin-monitor

# 2. 复制环境变量模板并填写真实值
cp config/.env.example .env
# 编辑 .env 填写数据库/Redis/FXG/CREATOR 凭证

# 3. 启动全栈服务
docker-compose up -d

# 4. 验证服务
curl http://localhost/api/health  # 应返回 {"status":"ok"}
```

### Q1.2: 首次启动报数据库连接失败怎么办？
**A:** 检查以下几点：
1. `.env` 中 `DATABASE_URL` 格式正确：`mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4`
2. MySQL 容器已健康：`docker-compose logs mysql | grep "ready for connections"`
3. 网络连通：`docker-compose exec backend ping mysql`
4. 权限正确：数据库用户有 `SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER` 权限

### Q1.3: 前端开发服务器热更新不生效？
**A:**
1. 确认 `frontend/vite.config.ts` 中 `server.hmr` 配置正确
2. 检查文件监听限制：`echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p`
3. 使用 `docker-compose exec frontend npm run dev` 而非宿主机直接运行
4. 确保卷挂载正确：`volumes: - ./src/frontend:/app` 在 docker-compose.yml 中

### Q1.4: 生产环境部署后无法访问？
**A:** 排查清单：
- [ ] Nginx 配置正确（`nginx/conf.d/wlkj-tech.cn.conf`）
- [ ] SSL 证书有效（`certbot certificates` 查看）
- [ ] 域名解析正确（`dig wlkj-tech.cn`）
- [ ] 安全组/防火墙放行 80/443 端口
- [ ] 后端健康检查通过（`curl http://localhost:5000/api/health`）
- [ ] 前端静态资源 Nginx 代理正确（`try_files $uri $uri/ /index.html`）

---

## 2. 开发规范与工具

### Q2.1: 代码提交被 CI 拦截，提示 lint/type-check 失败？
**A:** 本地先跑完整检查：
```bash
# 后端
cd src/backend
ruff check . --fix
ruff format .
mypy .

# 前端
cd src/frontend
npm run lint
npm run type-check
npm run format
```
推送前建议运行 `pre-commit run --all-files`。

### Q2.2: 提交信息被 commitlint 拦截？
**A:** 按规范格式提交：
```bash
# 正确格式
git commit -m "feat(order): add bulk export API"
# 或交互式修正
git commit --amend
# 参考: docs/development/COMMIT_CONVENTION.md
```

### Q2.3: 如何在 PR 中添加测试覆盖率要求？
**A:** CI 已集成覆盖率检查（`pytest --cov=src --cov-fail-under=80`）。新增代码需：
- 核心业务逻辑：≥ 80% 覆盖
- 边界/异常分支：必须有测试用例
- Mock 外部依赖（数据库/Redis/外部 API）

### Q2.4: 如何本地调试 Celery 任务？
**A:**
```bash
# 方式 1: 同步执行 (阻塞调试)
celery -A celery_app worker --loglevel=INFO --concurrency=1 -Q sync

# 方式 2: 使用 Flower 监控
pip install flower
celery -A celery_app flower --port=5555
# 浏览器访问 http://localhost:5555

# 方式 3: 同步执行单个任务 (用于调试)
python -c "from tasks import sync_all_data; sync_all_data.delay().get(timeout=60)"
```

---

## 3. 数据同步与外部 API

### Q3.1: FXG API 返回 429 Too Many Requests 怎么办？
**A:** 平台已内置限流保护：
- **客户端限流**: Token Bucket 20 QPS/店铺 (见 `tasks/sync_service.py`)
- **指数退避重试**: 最大 3 次，间隔 1s/2s/4s
- **熔断器**: 连续 5 次 429 触发熔断 60s
- **监控告警**: `sync_rate_limit_hits` 指标触发 P1 告警

**排查步骤:**
1. 检查 `sync_rate_limit_hits` 指标是否激增
2. 确认店铺数量未超预期（每店铺 20 QPS）
3. 检查 FXG 侧是否调整配额（联系平台技术支持）
4. 临时降低并发：修改 `RATE_LIMIT_QPS` 环境变量

### Q3.2: 同步任务长时间卡住/超时怎么办？
**A:** 排查清单：
- [ ] Celery Worker 存活：`celery -A celery_app inspect ping`
- [ ] 队列积压：`celery -A celery_app inspect active_queues`
- [ ] 数据库连接池：`SHOW PROCESSLIST` 是否有大量 `Sleep` 连接
- [ ] 外部 API 响应：`curl -v https://fxg.jinritemai.com/api/health`
- [ ] Worker 日志：`docker-compose logs celery_worker_sync -f`

**常见原因:**
- 外部 API 响应慢 → 调整 `SYNC_TIMEOUT` 环境变量
- 数据量大 → 分批处理、游标分页、异步分批入库
- 死锁 → 检查数据库死锁日志，调整事务隔离级别/索引

### Q3.3: 同步数据不一致/丢单怎么办？
**A:** 自查步骤：
1. 对比 FXG 后台订单数 vs 本地订单数
2. 检查 `sync_tasks` 表最近执行记录（成功/失败/耗时）
3. 检查 `orders` 表 `updated_at` 最近更新时间
4. 手动触发增量同步：`celery -A celery_app call tasks.sync_incremental`
5. 检查 FXG API 返回数据是否包含 `is_deleted` 标记（软删除处理）

### Q3.4: FXG Cookie 失效/Token 过期如何处理？
**A:** 平台已实现自动刷新机制：
- **Access Token**: 有效期 2h，提前 10min 自动刷新（见 `tasks/auth.py`）
- **Cookie**: 有效期 7-30 天，过期前 24h 告警提醒（`alert_cookie_expiry`）
- **手动刷新**: 管理后台 → 授权管理 → 点击“刷新 Token”

**应急手动操作:**
```bash
# 1. 获取新 Cookie/Token (浏览器开发者工具复制)
# 2. 更新 Vault/环境变量
docker-compose exec backend python -c "
from tasks.auth import refresh_fxg_token
refresh_fxg_token(shop_id=123)
"
# 3. 重启同步 Worker 生效
docker-compose restart celery_worker_sync
```

---

## 4. 权限与认证

### Q4.1: 用户登录后提示“权限不足”？
**A:** 检查权限矩阵：
1. 确认用户角色：`SELECT * FROM users WHERE id=xxx;`
2. 确认店铺授权：`SELECT * FROM shop_authorizations WHERE user_id=xxx AND shop_id=yyy;`
3. 检查 RBAC 策略：`docs/reference/PERMISSION.md` 权限矩阵
4. 后端日志搜索：`grep "permission_denied" logs/backend.log`

### Q4.2: JWT Token 过期/刷新失败怎么办？
**A:**
- **Access Token**: 30min 过期，前端自动携带 Refresh Token 调用 `/api/auth/refresh`
- **Refresh Token**: 7天过期，过期需重新登录
- **常见原因**: 时钟不同步（检查服务器 NTP）、Refresh Token 被撤销/过期、并发刷新导致竞争

**调试:**
```bash
# 解码 JWT 查看过期时间
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | jq -R 'split(".")[1] | @base64d | fromjson'
```

### Q4.3: 如何临时授予用户临时权限？
**A:**
```sql
-- 临时授予店铺管理员权限 (24小时后自动过期)
INSERT INTO user_permissions (user_id, shop_id, permission, expires_at)
VALUES (123, 456, 'shop_admin', NOW() + INTERVAL '24 HOUR');

-- 或通过管理后台：用户管理 → 权限分配 → 设置过期时间
```

---

## 5. 性能优化

### Q5.1: 接口响应慢 (P99 > 1s) 如何排查？
**A:** 诊断步骤：
1. **Grafana 查看**: `http_request_duration_seconds` P99 趋势
2. **慢查询日志**: `mysqldumpslow -s t /var/log/mysql/slow.log`
3. **EXPLAIN 分析**: `EXPLAIN ANALYZE SELECT ...` 看是否全表扫描
4. **索引检查**: `SHOW INDEX FROM orders;` 确认组合索引覆盖
5. **N+1 排查**: Django Debug Toolbar / SQLAlchemy `echo=True` 看查询数

**常见优化:**
- 加组合索引：`CREATE INDEX idx_shop_status_time ON orders(shop_id, status, created_at);`
- 游标分页替代 OFFSET：`WHERE id > last_id ORDER BY id LIMIT 20`
- 缓存热点数据：`cache:dashboard:stats:{shop_id}` TTL 60s
- 只查需要字段：`SELECT id, status, amount FROM ...` 避免 `SELECT *`

### Q5.2: 数据库 CPU/内存飙高怎么办？
**A:** 紧急缓解：
```sql
-- 1. 杀掉长时间运行查询
KILL QUERY <thread_id>;

-- 2. 临时降低同步并发
-- 修改环境变量 SYNC_CONCURRENCY=2 并重启 Worker

-- 3. 临时禁用非核心同步任务
UPDATE sync_tasks SET enabled=0 WHERE task_name IN ('non_core_task');
```

**根因排查:**
- 慢查询 → 加索引/改写 SQL/分页优化
- 连接泄漏 → 检查连接池配置 `pool_size`/`max_overflow`/`pool_recycle`
- 大事务 → 拆分事务、异步补偿、乐观锁
- 统计信息过期 → `ANALYZE TABLE orders;`

### Q5.3: Redis 内存不足 (OOM) 怎么办？
**A:** 紧急缓解：
```bash
# 1. 查看内存使用
redis-cli INFO memory

# 2. 找出大 Key
redis-cli --bigkeys

# 3. 设置淘汰策略 (临时)
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 4. 清理过期 Key
redis-cli SCAN 0 MATCH "cache:*" COUNT 1000 | xargs redis-cli DEL
```

**长期优化:**
- 缩短 TTL：非核心缓存 5min → 1min
- 压缩值：大对象 gzip/zstd 压缩存储
- 分片集群：Redis Cluster 横向扩展
- 监控告警：`redis_memory_used_bytes / redis_memory_max_bytes > 0.85` 告警

---

## 6. 监控告警

### Q6.1: 告警风暴（短时间大量告警）如何处理？
**A:** 紧急处理：
1. **静默告警**: Alertmanager Web UI → Silences → 新建静默 (匹配告警标签)
2. **识别根因**: 查看告警共同标签，定位共同根因（如数据库宕机触发所有服务告警）
3. **分级处理**: 先恢复核心服务，再处理派生告警
4. **事后优化**: 增加抑制规则、调整阈值、增加分组间隔

### Q6.2: 告警不触发/延迟触发怎么办？
**A:** 自查清单：
- [ ] Prometheus 规则加载正常：`curl http://prometheus:9090/api/v1/rules`
- [ ] Alertmanager 路由匹配：`curl http://alertmanager:9093/api/v2/status`
- [ ] 告警抑制规则是否过度抑制
- [ ] 通知渠道通畅：企业微信 Webhook 测试 `curl -X POST ...`
- [ ] 指标采集正常：`curl http://target:port/metrics | grep metric_name`

### Q6.3: 如何新增/修改告警规则？
**A:**
```yaml
# prometheus/rules/custom.yml
groups:
- name: custom-alerts
  rules:
  - alert: Custom_OrderSyncFailureRateHigh
    expr: |
      sum(rate(sync_task_failed_total[5m])) by (shop_id)
      /
      sum(rate(sync_task_total[5m])) by (shop_id)
      > 0.1
    for: 5m
    labels:
      severity: warning
      team: backend
      component: sync
    annotations:
      summary: "店铺 {{ \$labels.shop_id }} 同步失败率 {{ \$value | humanizePercentage }}"
      runbook_url: "https://wiki.example.com/runbook/sync-failure"
```
部署后 `promtool check rules` 验证，`prometheus reload` 热加载。

---

## 7. 常见报错与解决

### Q7.1: `sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2006, 'MySQL server has gone away')`
**A:** 原因：连接超时被 MySQL 主动断开。
**解决:**
```python
# SQLAlchemy 配置加上连接池预检
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # 关键：获取连接前先 ping
    pool_recycle=3600,           # 1小时强制回收 (小于 MySQL wait_timeout)
    pool_size=20,
    max_overflow=10,
)
```

### Q7.2: `celery.exceptions.OperationalError: Connection refused to Redis`
**A:** 检查 Redis 连通性：
```bash
# 1. Redis 容器状态
docker-compose ps redis

# 2. 网络连通
docker-compose exec backend redis-cli -h redis -p 6379 PING

# 3. 密码/ACL
redis-cli -h redis -a $REDIS_PASSWORD PING

# 4. 连接池耗尽
redis-cli INFO clients | grep connected_clients
```

### Q7.3: `pydantic.ValidationError: 1 validation error for OrderDTO status Input should be 'pending'|'paid'|...`
**A:** 外部 API 返回了未定义的枚举值。
**修复:**
```python
# 1. 枚举类添加兜底
class OrderStatus(str, Enum):
    UNKNOWN = "unknown"
    # ...

# 2. Pydantic 模型宽容模式
class OrderDTO(BaseModel):
    status: OrderStatus = Field(default=OrderStatus.UNKNOWN)
    model_config = ConfigDict(use_enum_values=True)
```

### Q7.4: `celery.exceptions.TaskRevokedError: Task was revoked`
**A:** 任务被主动撤销（部署重启/手动撤销/Worker 关闭）。
**处理:** 幂等设计保证重试安全，监控 `celery_task_revoked_total` 指标。

### Q7.5: `redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'`
**A:** 参见 Q5.3 Redis OOM 处理。

---

## 8. 发布与版本管理

### Q8.1: 如何发布新版本？
**A:** 标准发布流程：
```bash
# 1. 创建发布分支
git checkout develop && git pull
git switch -c release/v1.3

# 2. 版本号更新 + CHANGELOG
npm version minor  # 或手动修改版本号
# 编辑 CHANGELOG.md
git add . && git commit -m "chore(release): prepare v1.3.0"

# 3. 推送发布分支，触发预发布部署
git push -u origin release/v1.3

# 4. 预发布验证通过后，合并到 main 打 Tag
git checkout main && git pull
git merge --no-ff release/v1.3 -m "chore(release): merge release v1.3.0"
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin main --tags

# 4. 同步回 develop
git checkout develop
git merge --no-ff release/v1.3
git push origin develop
```

### Q8.2: 如何回滚生产环境？
**A:** 快速回滚方案：
```bash
# 方案 1: Docker 镜像回滚 (推荐，秒级)
docker-compose pull backend:v1.2.0
docker-compose up -d backend

# 方案 2: Git 回滚 + 重新部署
git checkout main
git revert <bad-commit-hash>  # 或 git reset --hard v1.2.0
git push origin main --force-with-lease  # 需谨慎
# 触发 CI/CD 重新部署

# 方案 3: 数据库回滚 (如有迁移)
./scripts/rollback_migration.sh v1.2.0
```

### Q8.3: 如何查看当前生产环境版本？
```bash
# 1. 查看部署镜像标签
docker-compose ps --format "table {{.Service}}\t{{.Image}}"

# 2. 查看 Git Tag
git tag --sort=-v:refname | head -5

# 3. 查看应用内置版本
curl http://localhost:5000/api/version
# 返回: {"version": "1.3.0", "commit": "abc1234", "build_time": "2026-09-26T10:00:00Z"}
```

---

## 9. 贡献指南快速入门

### Q9.1: 新人第一天如何开始贡献？
```bash
# 1. 环境搭建 (参考 Q1.1)
# 2. 阅读核心文档
- docs/development/CODING_STANDARDS.md
- docs/development/GIT_WORKFLOW.md
- docs/development/CODE_REVIEW_GUIDE.md

# 3. 认领一个 Good First Issue
# GitHub Issues 标签: good-first-issue

# 3. 提交第一个 PR
git checkout -b feature/good-first-issue-xxx
# ... 开发 ...
git commit -m "fix(typo): correct typo in README"
git push origin feature/good-first-issue-xxx
# 创建 PR，等待 Review
```

### Q9.2: 如何申请 Code Reviewer 权限？
**A:** 满足条件后向 Tech Lead 申请：
- 通过 Code Review 考核（完成 5+ 次高质量 Review）
- 熟悉核心模块代码架构
- 熟悉编码规范、Review 清单、安全规范
- 通过安全编码考核

---

*文档版本: v1.0.0 | 维护责任: PM/Tech Lead | 更新周期: 按需补充 | 反馈渠道: GitHub Issues / 企业微信群*
EOF