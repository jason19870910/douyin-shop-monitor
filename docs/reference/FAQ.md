---
title: 常见问题解答 (FAQ)
version: 1.1.0
status: Published
last_updated: 2026-10-16
owner: PM
reviewers: [Tech Lead, 运维负责人, 业务分析师]
approvers: [PM]
classification: Public
doc_id: DOC-REF-002
tags: [参考, FAQ, 常见问题, 答疑, 故障自助]
related_docs: [DOC-REF-003, DOC-OPS-001, DOC-OPS-003, DOC-DEV-001]
changelog: |
  v1.1.0 (2026-10-16): 同步架构变更 - 移除 Celery/MySQL/JWT 引用，改为内置调度器 + Redis + API Key 认证 - PM
  v1.0.0 (2026-09-26): 初版创建 - PM
---

# 常见问题解答 (FAQ)

## 目录
1. [环境搭建与部署](#1-环境搭建与部署)
2. [开发规范与工具](#2-开发规范与工具)
3. [数据同步与外部 API](#3-数据同步与外部-api)
4. [权限与认证](#4-权限与认证)
5. [性能优化](#5-性能优化)
6. [监控告警](#6-监控告警)
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
# 编辑 .env 填写 Redis/API_KEY/FXG/Creator/好货 Cookie 凭证

# 3. 启动全栈服务
docker-compose up -d

# 4. 验证服务
curl http://localhost/api/health  # 应返回 {"status":"ok"}
```

### Q1.2: 首次启动报 Redis 连接失败怎么办？
**A:** 检查以下几点：
1. Redis 连接配置正确：`REDIS_HOST=redis`、`REDIS_PORT=6379`（docker-compose 内默认服务名 `redis`）
2. Redis 容器已健康：`docker-compose ps redis` 状态为 `Up`，`docker-compose logs redis` 无异常
3. 网络连通：`docker-compose exec app redis-cli -h redis -p 6379 ping` 应返回 `PONG`
4. 如启用了密码/ACL：确认 `REDIS_PASSWORD` 与 Redis 服务端一致（`redis-cli -a $REDIS_PASSWORD ping`）

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
- Mock 外部依赖（Redis/外部 API）

### Q2.4: 如何本地调试同步任务（内置调度器）？
**A:**
```bash
# 方式 1: 查看内置调度器日志 (确认周期触发与执行结果)
docker-compose logs app | grep -E "sync_cycle|SYNC|scheduler"

# 方式 2: 手动触发一次完整同步周期 (阻塞执行，便于断点调试)
curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"

# 方式 3: 本地直接执行同步逻辑 (不依赖容器)
cd src/backend
python -c "from services.fetcher import scheduled_job; scheduled_job()"
```

---

## 3. 数据同步与外部 API

### Q3.1: FXG API 返回 429 Too Many Requests 怎么办？
**A:** 平台已内置限流保护：
- **客户端限流**: Token Bucket 20 QPS/店铺 (见 `services/fetcher.py`)
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
- [ ] 调度器线程存活：`docker-compose logs app | grep -E "scheduler|sync_cycle"`，应有 `Sync scheduler started` 及周期日志
- [ ] 同步锁未僵死：`docker-compose exec redis redis-cli GET douyin:monitor:sync:lock`（长时间占用且无进度日志说明上次同步卡住）
- [ ] 外部 API 响应：`curl -v https://fxg.jinritemai.com/api/health`
- [ ] app 容器资源：`docker stats app` 看 CPU/内存是否打满
- [ ] app 日志：`docker-compose logs app -f`

**常见原因:**
- 外部 API 响应慢/限流 → 检查 429 与超时，适当调整 `SCHEDULE_INTERVAL_MINUTES`
- 数据量大 → 分批处理、游标分页
- 同步锁未释放 → `docker-compose exec redis redis-cli DEL douyin:monitor:sync:lock` 释放后手动触发同步验证

### Q3.3: 同步数据不一致/丢单怎么办？
**A:** 自查步骤：
1. 对比 FXG 后台订单数 vs 看板订单数（前端数据来自 Redis/文件缓存）
2. 查看同步历史：`curl http://localhost/api/v1/sync/history -H "Authorization: Bearer $API_KEY"`，确认最近周期状态与耗时
3. 检查最近成功周期时间：`docker-compose logs app | grep "Sync cycle completed"`
4. 手动触发补偿同步：`curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"`
5. 检查 FXG API 返回数据是否包含 `is_deleted` 标记（软删除处理）

### Q3.4: FXG Cookie 失效/Token 过期如何处理？
**A:** 定时同步依赖各平台站点 Cookie，过期后外部 API 返回未登录/权限错误，同步周期标记失败：
- **Cookie**: 有效期通常 2h-7 天，需定期通过浏览器 F12（开发者工具）复制更新
- **同步检测**: 同步过程中检测到 `COOKIE_EXPIRED`/`AUTH_ERROR` 会记录告警日志并标记该周期状态
- **涉及站点**: 抖店 `fxg.jinritemai.com`、创作者中心 `creator.douyin.com`、指南针 `compass.jinritemai.com`、好货 `haohuo.jinritemai.com`

**应急手动操作:**
```bash
# 1. 浏览器登录对应平台，F12 复制新 Cookie
# 2. 更新 .env 中对应环境变量（FXG_COOKIES / CREATOR_COOKIES / HAOHUO_COOKIES）并重启 app 生效
docker-compose restart app

# 3. 手动触发一次同步验证
curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"

# 4. 查看认证相关日志
docker-compose logs app | grep -E "cookie|auth|COOKIE|AUTH"
```

---

## 4. 权限与认证

### Q4.1: 用户登录后提示“权限不足”？
**A:** 检查权限矩阵：
1. 确认用户角色：按 `docs/reference/PERMISSION.md` 权限矩阵核对目标角色是否具备该操作权限
2. 确认店铺授权：核对 `.env` 中该用户 API Key 对应的店铺与角色绑定关系
3. 检查 RBAC 策略：`docs/reference/PERMISSION.md` 权限矩阵
4. 后端日志搜索：`grep "permission_denied" logs/app.log`

### Q4.2: 调用 API 返回 401 Unauthorized 怎么办？
**A:** 平台采用 API Key 双 Header 认证，任一通过即可，无登录态/刷新机制：
- **Authorization**: `Authorization: Bearer <API_KEY>`
- **X-API-Key**: `X-API-Key: <API_KEY>`
- **公共端点白名单**（无需认证）: health、health/external、auth/login、auth/callback、auth/qr-code、auth/status

**常见原因**: Header 缺失/拼写错误（`Bearer ` 后需有空格）、`API_KEY` 与服务端环境变量不一致、访问了非白名单端点但未携带凭证。

**调试:**
```bash
# 1. 带凭证请求对比验证
curl -i http://localhost/api/v1/products -H "Authorization: Bearer $API_KEY"

# 2. 查看认证失败日志
docker-compose logs app | grep -E "401|auth"

# 3. 确认服务端已配置 API_KEY（未配置时全部业务端点返回 401）
docker-compose exec app env | grep API_KEY

# 4. 本地开发可临时设置 SKIP_AUTH=true 跳过认证（仅限开发环境）
```

### Q4.3: 如何临时授予用户临时权限？
**A:** 平台无本地用户库，访问控制基于 API Key + RBAC 权限矩阵（`docs/reference/PERMISSION.md`）：
```bash
# 1. 核对目标角色当前权限
grep "shop_admin" docs/reference/PERMISSION.md

# 2. 为该用户在 .env 颁发独立 API Key（便于审计与回收）
#    需与权限矩阵中角色一一对应

# 3. 权限到期后轮换/回收该 API Key 并同步更新权限矩阵
```

---

## 5. 性能优化

### Q5.1: 接口响应慢 (P99 > 1s) 如何排查？
**A:** 诊断步骤：
1. **Grafana 查看**: `http_request_duration_seconds` P99 趋势
2. **性能剖析**: `py-spy top --pid <pid>` 实时看热点函数，`py-spy dump --pid <pid>` 抓取当前调用栈
3. **外部调用耗时**: 检查 FXG/创作者中心等外部 API 响应时间与重试次数
4. **缓存命中**: `docker-compose exec redis redis-cli INFO stats` 看 `keyspace_hits/misses`，关注缓存穿透
5. **容器资源**: `docker stats app` 看 CPU/内存是否受限

**常见优化:**
- 缓存热点数据：看板统计结果缓存 TTL 60s，减少重复计算
- 游标分页替代 OFFSET：`WHERE id > last_id ORDER BY id LIMIT 20`
- 减少外部调用：合并/批量请求，避免循环内逐个调用外部 API
- 按需返回字段：接口只返回必要字段，避免全量冗余数据传输

### Q5.2: app 容器 CPU/内存飙高怎么办？
**A:** 紧急缓解：
```bash
# 1. 定位热点函数/线程
APP_PID=$(docker inspect -f '{{.State.Pid}}' douyin_app)
py-spy top --pid $APP_PID

# 2. 临时拉长同步间隔、降低外部请求并发
#    修改 .env 中 SCHEDULE_INTERVAL_MINUTES 并重启容器
docker-compose restart app

# 3. 通过同步周期日志识别异常任务
docker-compose logs app | grep -E "sync_cycle|SYNC"
```

**根因排查:**
- 外部 API 响应慢 → 检查 FXG/创作者中心响应时间与重试次数
- 签名计算密集 → `a_bogus` 的 V8 实时计算 CPU 开销（仅 FXG 域名）
- 连接异常 → 检查 Redis 连接池复用情况
- 缓存值过大 → Redis 大 Key 触发序列化/传输开销

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
2. **识别根因**: 查看告警共同标签，定位共同根因（如 Redis 故障触发所有服务告警）
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

### Q7.1: `redis.exceptions.ConnectionError` 连接 Redis 失败/被断开
**A:** 原因：Redis 服务重启、网络中断或连接空闲超时导致连接断开。
**解决:**
```bash
# 1. 确认 Redis 容器存活与连通
docker-compose ps redis
docker-compose exec app redis-cli -h redis -p 6379 ping   # 应返回 PONG

# 2. 查看 Redis 日志，排查重启/OOM 原因
docker-compose logs redis --tail=100

# 3. 重启 app 容器重新建立连接
docker-compose restart app
```

### Q7.2: 同步周期失败（日志出现 `Sync cycle failed` 或 `Sync skipped`）
**A:** 同步由 app 容器内置调度器驱动，先区分"失败"与"被跳过"：
```bash
# 1. 查看最近同步周期日志（failed / skipped / completed）
docker-compose logs app | grep -E "Sync cycle|Sync skipped|Sync scheduler"

# 2. 检查同步锁是否僵死（长期占用会导致后续同步被跳过）
docker-compose exec redis redis-cli GET douyin:monitor:sync:lock
# 确认无同步进行后释放：
docker-compose exec redis redis-cli DEL douyin:monitor:sync:lock

# 3. 检查 Redis 连通性（连接失败时降级文件缓存并记录告警）
docker-compose exec app redis-cli -h redis -p 6379 PING

# 4. 检查外部 API / Cookie 是否失效
docker-compose logs app | grep -E "COOKIE|AUTH|429|timeout" | tail -20
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

### Q7.4: 日志提示 `Sync skipped: another sync already in progress`
**A:** 本次同步被跳过——分布式锁已被占用（上次同步未完成或锁未释放）。
**处理:** 同步为幂等设计，跳过不会造成数据错误，但需确认：
1. 上一次同步周期是否卡住：`docker-compose logs app | grep "Sync cycle"`
2. 锁是否僵死：`docker-compose exec redis redis-cli GET douyin:monitor:sync:lock`，确认无同步进行后 `DEL` 释放
3. 同步频率是否过高：调整 `SCHEDULE_INTERVAL_MINUTES`，避免周期重叠

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
docker-compose pull app:v1.2.0
docker-compose up -d app

# 方案 2: Git 回滚 + 重新部署
git checkout main
git revert <bad-commit-hash>  # 或 git reset --hard v1.2.0
git push origin main --force-with-lease  # 需谨慎
# 触发 CI/CD 重新部署

# 方案 3: 数据侧恢复 - 旧版本无数据库迁移，触发全量同步重建缓存
curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"
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

*文档版本: v1.1.0 | 维护责任: PM/Tech Lead | 更新周期: 按需补充 | 反馈渠道: GitHub Issues / 企业微信群*