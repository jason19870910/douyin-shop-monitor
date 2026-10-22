---
title: 故障排查指南
version: 1.0.2
status: Published
last_updated: 2026-10-17
owner: DevOps Lead
reviewers: [Tech Lead, 运维工程师, Backend Lead]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-REF-003
tags: [参考, 故障排查, 故障处理, 运维, SRE, 自助诊断]
related_docs: [DOC-OPS-001, DOC-OPS-003, DOC-OPS-005, DOC-REF-002]
changelog: |
  v1.0.2 (2026-10-17): 新增第 2.9 节合规检测返回 checked: 0 / 商品数据为空的排查步骤（FXG_COOKIES 过期/Redis 缓存空/上游 API code 10008） - DevOps Lead
  v1.0.1 (2026-10-16): 同步架构变更 - 移除 Celery/MySQL 引用，改为内置调度器排查命令 - DevOps Lead
  v1.0.0 (2026-09-26): 初版创建 - DevOps Lead
---

# 故障排查指南

## 使用说明
- **适用场景**: 线上故障自助诊断、新人入职培训、应急演练参考
- **排查原则**: 从基础设施 → 应用层 → 业务层，由简入繁、快速定位
- **记录要求**: 每次排查记录现象、操作、结论，沉淀到知识库
- **升级路径**: P0 故障 15min 无进展 → 升级至 Tech Lead/架构师

---

## 1. 快速诊断清单 (前 5 分钟)

| 检查项 | 命令/操作 | 正常标准 | 异常处理 |
|--------|----------|----------|----------|
| **服务存活** | `docker-compose ps` | 所有容器 Up | 重启异常容器 |
| **健康检查** | `curl -s http://localhost/api/health` | `{"status":"ok"}` | 查看后端日志 |
| **Redis** | `docker-compose exec redis redis-cli ping` | `PONG` | 检查内存/连接数 |
| **同步调度器** | `docker-compose logs app | grep -E "sync|schedule"` | 同步周期日志正常 | 检查调度器线程状态 |
| **外部 API** | `curl -s http://localhost/api/health/external` | 返回 `{"status":"ok"}` | 检查 Cookie/签名/网络 |
| **Nginx** | `curl -I https://wlkj-tech.cn` | `200 OK` | 检查配置/证书 |
| **磁盘空间** | `df -h /` | 使用率 < 80% | 清理日志/备份 |
| **内存使用** | `free -h` | 可用 > 20% | 排查泄漏/重启 |
| **CPU 负载** | `uptime` | load < CPU 核心数 | 排查进程/限流 |

---

## 2. 常见故障场景排查树

### 2.1 服务完全不可访问
```
现象: 浏览器/客户端无法访问，curl 超时或连接拒绝
├── 检查 Nginx 是否运行
│   └── systemctl status nginx / docker-compose ps nginx
├── 检查端口监听
│   └── netstat -tlnp | grep :80 :443 :5000
├── 检查防火墙/安全组
│   └── 云控制台/iptables -L -n | grep 80/443
├── 检查域名解析
│   └── dig wlkj-tech.cn / nslookup
└── 检查 SSL 证书
    └── curl -vI https://wlkj-tech.cn | grep -A5 "SSL certificate"
```

### 2.2 API 返回 5xx / 超时
```
现象: 接口报 500/502/503/504，或响应时间 > 10s
├── 查看后端日志
│   └── docker-compose logs app -f --tail=100
├── 检查 Redis 连接
│   └── INFO clients / 连接池配置
├── 检查外部 API 依赖
│   └── FXG/Creator API 响应时间/错误率
├── 检查内置调度器线程
│   └── 日志含 schedule/sync 关键字 / 线程是否存活
└── 检查资源限制
    └── docker stats / cgroup 限制 / OOM Killer
```

### 2.3 数据同步失败/延迟
```
现象: 同步任务失败、数据不一致、同步耗时异常
├── 查看调度器执行状态
│   └── docker-compose logs app | grep -E "sync_cycle|SYNC" 查看最近同步结果
├── 检查同步锁状态
│   └── docker-compose exec redis redis-cli GET douyin:monitor:sync:lock
├── 检查外部 API 响应
│   └── FXG/Creator API: 429/5xx/超时/签名错误
├── 检查限流/熔断状态
│   └── Redis: sync:rate_limit:* / sync:circuit_breaker:*
├── 检查缓存数据新鲜度
│   └── Redis: GET douyin:last_sync_timestamp / 文件缓存时间戳
└── 手动触发补偿同步
    └── curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"
```

### 2.4 前端页面白屏/报错
```
现象: 页面空白、JS 报错、资源加载失败
├── 浏览器控制台
│   └── F12 Console / Network 看红色报错
├── 检查构建产物
│   └── dist/ 目录文件完整 / hash 文件名匹配
├── 检查 Nginx 静态资源代理
│   └── location /assets/ / location / 配置 try_files
├── 检查 API 请求
│   └── Network 看 /api/* 请求状态/响应
├── 检查环境变量注入
│   └── window.__ENV__ / Vite define 配置
└── 清理缓存重试
    └── Ctrl+Shift+R / 无痕模式 / CDN 刷新
```

### 2.5 价格/金额显示异常 (新增 2026-10-15)
```
现象: 商品价格显示 100 倍 (如 ¥825 应为 ¥8.25)、订单金额为 0 或字段缺失
├── 检查 API 返回单位
│   └── /products、/dashboard/stats.top_products 返回 price_lower/price_higher/market_price → 单位为 **分 (fen)**
│   └── /orders、/dashboard/stats.recent_orders、/orders/stats 返回 pay_amount/total_price → 单位为 **元 (yuan)**
├── 检查前端 formatCurrency 调用
│   └── 商品价格类字段：render 中需 `(value / 100)` 后传入 formatCurrency
│   └── 订单金额类字段：直接传入 formatCurrency (已是元)
├── 检查字段名映射
│   └── 订单列表：API 返回 pay_amount/total_price，前端需用正确字段名
│   └── 热销商品：API 返回 price_lower/price_higher，前端需用 price_lower
├── 检查导出 CSV
│   └── exportConfig.columns 中添加 render 函数做单位转换
└── 验证修复
    └── 访问 /#/dian/products、/#/dashboard、/#/orders、/#/ 确认价格/金额显示正确
```

### 2.6 首页 KPI 数据全为 0 / 趋势图空白 (新增 2026-10-15)
```
现象: 首页 今日销售额 0、今日订单数 0、商品概览在售 0、销售趋势/热销商品显示占位提示
├── 检查后端统计端点数据源
│   └── /products/stats、/orders/stats、/creators/overview 是否读取本地缓存聚合
│   └── 修复前：直接调用外部 FXG API 返回空/受限
│   └── 修复后：读取 Redis/文件缓存的同步数据本地统计
├── 检查前端 Hook 调用
│   └── Home.tsx: useProductsStats、useOrdersStats、useCreatorsOverview (KPI 用)
│   └── Home.tsx: useDashboardStats (趋势/TOP 数据用)
├── 检查同步任务状态
│   └── 定时任务是否成功写入缓存 (Redis/文件)
│   └── 手动触发同步验证: 点击首页"手动同步"按钮
└── 验证修复
    └── 首页 KPI 卡片显示真实数据
    └── 销售趋势图表显示 7 天折线
    └── 热销商品 TOP 5 表格显示数据
```

### 2.7 好货商品预览 API 失败/无数据 (新增 2026-10-15)
```
现象: /api/v1/external/haohuo/product/preview 返回错误、status_code != 0、detail_info 为空
├── 检查 HAOHUO_COOKIES 环境变量
│   └── 服务器 .env 或 docker-compose.yml 是否配置有效的 HAOHUO_COOKIES
│   └── Cookie 有效期通常 2h-7 天，需定期通过浏览器 F12 更新
├── 检查请求参数
│   └── POST body 必须包含 promotion_id (商品ID)
│   └── Query params: is_h5=1, origin_type=doudian_product_management
├── 检查动态签名参数
│   └── msToken、a_bogus 为时效性参数，当前实现不传递
│   └── 服务端可能仅依靠 Cookie 校验，若失败需从页面 JS 计算或 Cookie 提取
├── 检查网络/防火墙
│   └── 服务器是否能访问 haohuo.jinritemai.com (端口 443)
│   └── curl -v "https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/" 测试
├── 检查后端日志
│   └── docker-compose logs app -f | grep haohuo
│   └── 查看 status_code: -1=连接错误, -2=超时, -3=请求失败, -99=未知异常
└── 验证修复
    └── 返回 status_code: 0
    └── detail_info.detail_imgs 数组非空 (商品详情图片)
    └── detail_info.product_format 非空 (商品规格)
    └── detail_info.detail_config 非空 (价格/销量/协议说明)
    └── detail_info.jump_url 非空 (直播间/lynxview 跳转链接)
```

### 2.8 权限/认证异常
```
现象: 401/403、凭证失效、无限跳转登录
├── 检查认证 Header
│   └── Authorization: Bearer <token> 与 X-API-Key 任一有效即可通过
├── 确认端点是否在公共白名单
│   └── health、health/external、auth/login、auth/callback、auth/qr-code、auth/status
├── 检查后端认证中间件日志
│   └── docker-compose logs app | grep -E "auth|401|403"
├── 检查 RBAC 策略配置
│   └── docs/reference/PERMISSION.md 矩阵核对
└── 检查时钟同步
    └─► date / ntpdate -q pool.ntp.org (偏差 > 1min 会影响有效期判断)
```

### 2.9 合规检测返回 checked: 0 / 商品数据为空 (新增 2026-10-17)
```
现象: 合规检测接口 `/api/v1/compliance/check/products` 返回 `checked: 0`，商品列表为空，无法进行合规检测

├─► 检查 Redis 商品缓存键
│   └─► docker exec douyin_redis redis-cli GET douyin:monitor:products
│   返回 `[]` 或为空 → 上游商品抓取未写入缓存，进入下一步

├─► 检查 app 容器日志中的业务错误
│   └─► docker logs douyin_app --tail 100 | grep -i "FXG API 业务错误"
│   如出现 `code=10008` → FXG Cookie 已过期（API 返回 HTTP 200，但业务码 10008 "登录信息已失效，请重新登录"）

├─► 检查 .env 中 Cookie 变量
│   └─► grep FXG_COOKIES /opt/douyin-platform/config/.env
│   值为空或已过期 → 按 RUNBOOK 第 5.2 节流程更新 FXG_COOKIES

├─► 更新 Cookie 并重建容器（restart 不会重读 .env）
│   └─► cd /opt/douyin-platform
│   └─► docker compose up -d --force-recreate app
│   └─► docker restart douyin_frontend   # 刷新前端 upstream 缓存

├─► 验证恢复
│   └─► docker exec douyin_redis redis-cli GET douyin:monitor:products   # 应非空
│   └─► curl -H "X-API-Key: wlkj_douyin_api_20260921_abc123" http://localhost:5000/api/v1/compliance/check/products
│   返回 `checked > 0` 即恢复正常

> **根因**: FXG API 在 Cookie 过期时仍返回 HTTP 200，但响应体中 `code=10008`。fetcher.py 原先仅校验 HTTP 状态码，导致业务错误被静默吞掉，products 为空列表，合规检测返回 `checked: 0`。现已在 fetcher.py 增加业务错误码校验，Cookie 过期时会抛出 HTTPError 并记录明确 ERROR 日志，后续可直接通过 `docker logs douyin_app | grep "FXG API 业务错误"` 定位。
```

---

## 3. 关键日志位置与查询命令

| 组件 | 日志路径/命令 | 关键词过滤示例 |
|------|--------------|---------------|
| **Nginx** | `/var/log/nginx/access.log` `/var/log/nginx/error.log` | `grep " 5[0-9][0-9] " /var/log/nginx/access.log` |
| **Backend (Flask)** | `docker-compose logs app -f` | `grep -E "ERROR|CRITICAL|traceback" logs/app.log` |
| **内置调度器** | `docker-compose logs app -f` (同 App 容器) | `grep -E "sync_cycle|SCHEDULER|SYNC" logs/app.log` |
| **Redis** | `docker-compose logs redis -f` | `redis-cli MONITOR | grep -E "OOM|maxmemory"` |
| **应用结构化日志** | ELK/Loki 查询 | `{service="backend"} | level="ERROR" | json` |

---

## 4. 性能问题快速定位

| 症状 | 定位命令/工具 | 常见原因 | 解决方向 |
|------|--------------|----------|----------|
| **API P99 > 1s** | Grafana `http_request_duration_seconds` | 单线程 GIL 争用/Rabbit 慢/缓存穿透 | 缓存/异步/减少外部调用 |
| **后端 CPU 100%** | `docker stats` `py-spy dump` | 同步请求阻塞/签名计算密集 | 检查外部 API 超时/签名性能 |
| **Redis OOM** | `redis-cli INFO memory` `redis-cli --bigkeys` | 大 Key/无 TTL/内存碎片 | 缩短 TTL/压缩值/Cluster 分片 |
| **同步周期超时** | `docker-compose logs app | grep sync_cycle` | 外部 API 慢/网络抖动/限流 | 调整 SCHEDULE_INTERVAL_MINUTES/熔断降级 |
| **前端加载慢** | Lighthouse / Chrome DevTools Performance | Bundle 过大/无代码分割/无缓存 | 代码分割/预加载/CDN/压缩 |

---

## 5. 应急操作速查卡

### 5.1 服务重启 (按依赖顺序)
```bash
# 1. 最小影响重启 (仅应用层，内置调度器随容器重启)
docker-compose restart backend

# 2. 中等影响 (含缓存)
docker-compose restart redis backend

# 3. 完全重启 (需谨慎!)
docker-compose down && docker-compose up -d

# 4. 仅重载 Nginx (配置变更后)
docker-compose exec nginx nginx -s reload
```

### 5.2 调度器/同步紧急操作
```bash
# 查看同步锁状态
docker-compose exec redis redis-cli GET douyin:monitor:sync:lock

# 手动释放同步锁 (僵死时)
docker-compose exec redis redis-cli DEL douyin:monitor:sync:lock

# 手动触发同步
curl -X POST http://localhost/api/v1/sync -H "Authorization: Bearer $API_KEY"

# 查看同步周期日志
docker-compose logs app | grep -E "sync_cycle|SYNC"
```

### 5.3 Redis 紧急操作
```bash
# 查看内存
redis-cli INFO memory | grep used_memory_human

# 临时调整淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 删除大 Key (谨慎!)
redis-cli --scan --pattern "cache:*" | head -100 | xargs redis-cli DEL

# 连接数清理
redis-cli CLIENT LIST | awk '$5 > 300 {print $2}' | xargs -I{} redis-cli CLIENT KILL {}
```

### 5.4 证书紧急续期
```bash
# 手动续期
certbot renew --force-renewal --nginx

# 检查证书状态
certbot certificates

# 重载 Nginx
docker-compose exec nginx nginx -s reload
```

---

## 6. 常用诊断脚本 (建议收藏为别名)

```bash
# ~/.bashrc 或 ~/.zshrc 追加
alias dps='docker-compose ps'
alias dlogs='docker-compose logs -f --tail=100'
alias dlogb='docker-compose logs app -f --tail=100'
alias dlogr='docker-compose logs redis -f --tail=100'
alias dexec='docker-compose exec'
alias rediscli='docker-compose exec redis redis-cli'
alias synclog='docker-compose logs app | grep -E "sync_cycle|SCHEDULER"'
alias health='curl -s http://localhost/api/health | jq .'
alias healthext='curl -s http://localhost/api/health/external | jq .'
alias healthredis='docker-compose exec redis redis-cli ping'
alias synclock='docker-compose exec redis redis-cli GET douyin:monitor:sync:lock'
alias syncunlock='docker-compose exec redis redis-cli DEL douyin:monitor:sync:lock'
alias dfh='df -h /'
alias mem='free -h'
alias cpu='uptime'
alias ports='netstat -tlnp | grep -E ":80|:443|:5000|:6379"'
alias disks='docker system df -v'
```

---

## 7. 故障等级判定与升级标准

| 等级 | 判定标准 | 响应时限 | 通知范围 | 典型场景 |
|------|----------|----------|----------|----------|
| **P0** | 核心业务全不可用/数据丢失/安全事件 | 15 min | 全响应组+管理层 | Redis 主库挂/数据泄露/全站 5xx |
| **P1** | 核心功能严重受损/大量用户受影响 | 1 小时 | IC+TL+Ops+Comms | 同步全失败/API 错误率>10%/Redis 集群故障 |
| **P2** | 部分功能异常/性能显著下降 | 4 小时 | IC+TL+Ops | 单接口慢/调度器线程异常/磁盘告警 |
| **P3** | 非核心功能/体验问题/观测盲区 | 1 工作日 | Owner | 报表失败/日志采集断/UI 样式错乱 |

---

## 8. 故障复盘模板 (PIR)

```markdown
# PIR-INC-YYYYMMDD-XXX: {故障标题}

## 1. 基本信息
- 发生时间: YYYY-MM-DD HH:MM - HH:MM
- 持续时长: XX 分钟
- 严重等级: P0/P1/P2
- 影响范围: {受影响店铺/用户/功能}
- 事件指挥官: 姓名

## 2. 时间线
| 时间 | 事件 | 操作人 | 备注 |
|------|------|--------|------|
| 10:30 | 告警触发 | 监控系统 | - |
| 10:32 | IC 确认 P1 | 张三 | - |
| 10:35 | TL 定位根因 | 李四 | FXG API 返回 429 |
| 10:40 | 实施降级 | 王五 | 启用缓存读模式 |
| 10:45 | 业务验证通过 | 赵六 | - |

## 3. 根因分析 (5Why)
1. Why? 订单同步周期连续失败
2. Why? FXG API 返回 429 Too Many Requests
3. Why? 并发请求数超过平台限制 (20 QPS)
4. Why? 增量同步并发未做限流，突发流量触发限流
5. Why? 代码未实现令牌桶限流，同步周期并发配置分散

**根因**: 同步任务缺乏客户端限流机制，配置管理不一致

## 4. 影响评估
- 数据同步延迟: 2 小时
- 受影响店铺: 12 家
- 用户投诉: 3 单
- 收入影响: 无直接损失

## 5. 改进行动项
| 编号 | 改进措施 | 负责人 | 截止日期 | 状态 | 验收标准 |
|------|---------|--------|----------|------|----------|
| ACT-001 | 实现客户端令牌桶限流 (20 QPS) | 李四 | 2026-10-10 | 进行中 | 压测验证 100 并发不触发 429 |
| ACT-002 | 统一同步配置到 .env / docker-compose.yml | 王五 | 2026-10-05 | 待开始 | 服务读取统一环境变量 |
| ACT-003 | 增加限流指标监控告警 | 张三 | 2026-10-08 | 待开始 | Grafana 有限流仪表盘 |

## 6. 经验教训
- 配置分散导致行为不一致，需集中化管理
- 缺乏压测验证上游限流阈值
- 降级开关生效验证不足
```

---

## 9. 联系人速查 (内部)

| 角色 | 姓名 | 电话 | 企业微信 | 备注 |
|------|------|------|----------|------|
| IC (主) | | | | DevOps Lead |
| IC (备) | | | | 运维资深 |
| TL (主) | | | | Backend Lead |
| TL (备) | | | | 架构师 |
| Ops (主) | | | | 运维工程师 |
| Ops (备) | | | | 运维工程师 |
| 安全负责人 | | | | 安全团队 |
| 云厂商支持 | - | 400-xxx-xxxx | - | 工单优先级 P0 |

---

*文档版本: v1.0.1 | 维护责任: DevOps Lead | 更新周期: 季度或重大故障后*