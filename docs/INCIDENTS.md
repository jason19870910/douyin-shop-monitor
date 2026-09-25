# 事故复盘记录 (Incident Postmortems)

> **维护原则**：每次生产事故必须在 24 小时内完成复盘记录，包含时间线、根因、修复、改进措施
> **模板参考**：[Google Postmortem Culture](https://cloud.google.com/blog/products/devops-sre/how-write-incident-postmortem)

---

## INC-20260822-001: scp 部署导致前端静态资源 403 Forbidden

### 基本信息
| 项目 | 详情 |
|------|------|
| **事故编号** | INC-20260822-001 |
| **发生时间** | 2026-08-22 20:05 (UTC+8) |
| **发现时间** | 2026-08-22 20:10 (UTC+8) |
| **解决时间** | 2026-08-22 20:15 (UTC+8) |
| **持续时长** | ~10 分钟 |
| **严重级别** | P1 (High) - 前端全站白屏，核心业务不可用 |
| **影响范围** | 所有前端页面 (https://wlkj-tech.cn) |
| **报告人** | 运维值班 |
| **复盘完成** | 2026-08-22 21:00 |

---

### 时间线

| 时间 | 事件 | 备注 |
|------|------|------|
| 20:05 | 执行 `scp -r build/* root@server:/opt/.../build/` 部署前端新版本 | 例行发布流程 |
| 20:06 | 执行 `nginx -s reload` | 配置未变更 |
| 20:10 | 访问 https://wlkj-tech.cn 发现页面白屏，浏览器控制台报 `net::ERR_ABORTED 403 (Forbidden)` | CSS/JS 均 403 |
| 20:11 | 排查：`curl -I https://wlkj-tech.cn/assets/index-xxx.css` 返回 `HTTP/2 403` | 确认是权限问题 |
| 20:12 | 检查服务器文件权限：`ls -la /opt/.../build/assets/` 显示所有者为 `root:root` | Nginx worker 以 `nginx` 用户运行 |
| 20:13 | 执行权限修复：`chown -R monitor:project_admins /opt/.../build && chmod -R 755 ...` | 标准运维操作 |
| 20:14 | 验证：`curl -I` 返回 `HTTP/2 200`，页面恢复正常 | 故障解除 |
| 20:15 | 记录 CHANGELOG、同步文档 | 事后处理 |

---

### 根因分析 (5 Why)

| 层级 | 问题 | 答案 |
|------|------|------|
| **1** | 为什么前端资源返回 403？ | Nginx worker 进程 (`nginx` 用户) 无法读取 `/opt/.../build/assets/` 下的文件 |
| **2** | 为什么 Nginx 无法读取文件？ | 文件所有者为 `root:root`，权限 `rw-r--r--` (644)，缺乏 `other` 读取权限或组权限 |
| **3** | 为什么文件所有者是 root？ | 使用 `scp` 以 `root` 用户上传，文件保留了上传者的所有权 |
| **4** | 为什么 scp 部署没有自动修复权限？ | 部署脚本/流程中缺少权限修复步骤，依赖人工执行 |
| **5** | 为什么流程中没有权限修复步骤？ | 历史发布多为 Docker 镜像部署 (镜像内已设置用户)，前端独立 scp 部署是新增场景，未纳入标准化运维清单 |

**根因**：**前端独立构建+scp 部署流程缺少自动化权限修复步骤**，导致文件以 root 所有者落盘，Nginx 无权读取。

---

### 修复措施

#### 即时修复 (已完成)
```bash
# 修复文件所有权与权限
chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build
chmod -R 755 /opt/douyin-platform/apps/monitor/frontend/build

# 验证
curl -I https://wlkj-tech.cn/assets/index-xxx.css  # 应返回 200
```

#### 临时规避 (如再次发生)
```bash
# 一键修复别名 (可加入 ~/.bashrc)
alias fix-frontend-perm='chown -R monitor:project_admins /opt/douyin-platform/apps/monitor/frontend/build && chmod -R 755 /opt/douyin-platform/apps/monitor/frontend/build'
```

---

### 改进措施 (防止复发)

| 编号 | 措施 | 优先级 | 负责人 | 目标完成时间 | 状态 |
|------|------|--------|--------|--------------|------|
| **IMP-001** | 在部署脚本中强制添加权限修复步骤 | P0 | 运维 | 2026-08-25 | ✅ 已完成（5s-cleanup.sh 含权限标准化检查） |
| **IMP-002** | 编写标准化前端部署脚本 `deploy-frontend.sh`，内含构建、scp、权限修复、Nginx reload | P0 | 运维 | 2026-08-25 | ⏳ 待落地（脚本草案见附录） |
| **IMP-003** | 评估改用 Docker 镜像部署前端 (构建时指定 USER)，避免 scp 权限问题 | P1 | 架构师 | 2026-09-01 | ✅ 已完成（已全面采用 Docker 镜像部署） |
| **IMP-004** | 在 Nginx 配置中添加 `server` 级别 `access_log` 记录 403 详情，便于快速定位 | P2 | 运维 | 2026-08-30 | ⏳ 计划中 |
| **IMP-005** | 增加部署后自动健康检查：`curl -f https://wlkj-tech.cn/assets/index.css` 失败则报警回滚 | P1 | 运维 | 2026-08-28 | ⏳ 计划中 |

---

### 经验教训

1. **任何文件落盘操作都必须显式处理权限**，不要假设目标环境用户一致
2. **新增部署方式必须纳入标准化运维清单**，包含：构建 → 传输 → 权限修复 → 验证 → 回滚预案
3. **权限问题表现为 403 而非 404**，易误判为路径配置错误，需建立快速排查卡片
4. **监控告警应覆盖静态资源可用性**，而非仅依赖 API 健康检查

---

### 相关文档更新

| 文档 | 更新内容 |
|------|----------|
| `CHANGELOG.md` | [Unreleased] Fixed 新增 2026-08-22 问题记录 |
| `README.md` | 常见问题排查表新增 "前端 403 Forbidden" 条目 |
| `RUNBOOK.md` | 故障排查决策树 6.1 新增权限检查步骤 |
| `docs/RUNBOOK.md` | 4.1 症状分支新增 "检查文件所有者/权限" |

---

## 附录：标准化前端部署脚本 (草案)

```bash
#!/bin/bash
# deploy-frontend.sh - 标准化前端部署
# 用法: ./deploy-frontend.sh [server_ip] [target_dir]

set -euo pipefail

SERVER="${1:-122.51.208.138}"
TARGET_DIR="${2:-/opt/douyin-platform/apps/monitor/frontend/build}"
LOCAL_BUILD_DIR="./frontend/build"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 开始前端部署流程..."

# 1. 本地构建
echo "📦 步骤 1/5: 本地构建生产包"
cd frontend
npm ci
npm run build
cd ..

# 2. 同步文件
echo "📤 步骤 2/5: 同步构建产物至服务器"
scp -i "$SSH_KEY" -r "$LOCAL_BUILD_DIR"/* "root@$SERVER:$TARGET_DIR/"

# 3. 远程修复权限 (关键步骤)
echo "🔐 步骤 3/5: 修复服务器文件权限"
ssh -i "$SSH_KEY" "root@$SERVER" "
  chown -R monitor:project_admins '$TARGET_DIR'
  chmod -R 755 '$TARGET_DIR'
"

# 4. 重载 Nginx
echo "🔄 步骤 4/5: 重载 Nginx 配置"
ssh -i "$SSH_KEY" "root@$SERVER" "nginx -t && nginx -s reload"

# 5. 部署后健康检查
echo "✅ 步骤 5/5: 部署后健康检查"
sleep 2
CSS_URL=$(ssh -i "$SSH_KEY" "root@$SERVER" "ls $TARGET_DIR/assets/index-*.css | head -1 | xargs basename")
if curl -f -s "https://wlkj-tech.cn/assets/$CSS_URL" > /dev/null; then
  echo "✅ 部署成功: 静态资源可访问"
else
  echo "❌ 部署失败: 静态资源不可访问，请检查权限或 Nginx 配置"
  exit 1
fi

echo "🎉 前端部署完成!"
```

---

## INC-20260824-001: Docker 重建后前端 assets 权限丢失 + CSP 阻止 Google Fonts

### 基本信息
| 项目 | 详情 |
|------|------|
| **事故编号** | INC-20260824-001 |
| **发生时间** | 2026-08-24 21:48 (UTC+8) |
| **发现时间** | 2026-08-24 21:50 (UTC+8) |
| **解决时间** | 2026-08-24 21:55 (UTC+8) |
| **持续时长** | ~7 分钟 |
| **严重级别** | P1 (High) - 前端全站白屏，核心业务不可用 |
| **影响范围** | 所有前端页面 (https://wlkj-tech.cn) |
| **报告人** | 用户反馈 |
| **复盘完成** | 2026-08-24 22:10 |

---

### 时间线

| 时间 | 事件 | 备注 |
|------|------|------|
| 21:40 | 执行 `docker compose build --no-cache` + `docker compose up -d` 重建镜像部署 | 项目结构整理后同步至服务器 |
| 21:48 | 6 个容器启动成功，API/前端/Nginx 健康检查通过 | 容器级健康检查正常 |
| 21:50 | 用户访问 https://wlkj-tech.cn 发现页面空白 | 控制台报错 |
| 21:50 | 控制台报错 1：`Refused to load stylesheet 'https://fonts.googleapis.com/...' because it violates Content-Security-Policy directive "style-src 'self' 'unsafe-inline'"` | CSP 策略阻止 Google Fonts |
| 21:50 | 控制台报错 2：`Failed to load resource: 403 (index-DAmdn99Y.js)` | JS 主模块 403 |
| 21:50 | 控制台报错 3：`Uncaught TypeError: Failed to fetch dynamically imported module` + `重试 30 次仍未找到 window.__APP_MOUNT__` | JS 加载失败的连锁反应 |
| 21:52 | 排查：`docker exec douyin_frontend ls -la /usr/share/nginx/html/` 发现 `assets` 目录权限为 `drwx------` (700) | 根因 1 定位 |
| 21:53 | 排查：`grep Content-Security-Policy nginx/conf.d/wlkj-tech.cn.conf` 发现 CSP 未包含 `fonts.googleapis.com` | 根因 2 定位 |
| 21:54 | 修复 1：`docker exec douyin_frontend chmod -R 755 /usr/share/nginx/html/assets` | 权限修复 |
| 21:54 | 修复 2：更新 CSP `style-src` 添加 `https://fonts.googleapis.com`，`font-src` 添加 `https://fonts.gstatic.com` | CSP 策略更新 |
| 21:55 | 重启 nginx，验证 JS/CSS/前端均返回 HTTP 200 | 故障解除 |

---

### 根因分析 (5 Why)

**问题 1：JS 403 错误**

| 层级 | 问题 | 答案 |
|------|------|------|
| **1** | 为什么 JS 文件返回 403？ | nginx worker 进程无法读取 `/usr/share/nginx/html/assets/` 下的文件 |
| **2** | 为什么 nginx 无法读取文件？ | `assets` 目录权限为 `drwx------` (700)，仅 root 可读 |
| **3** | 为什么 assets 权限是 700？ | Docker 构建过程中 `COPY --from=builder /app/build /usr/share/nginx/html` 保留了构建阶段的权限，而构建阶段未显式设置 |
| **4** | 为什么构建阶段未设置权限？ | 前端 `Dockerfile` 在 `COPY --from=builder` 后未添加 `RUN chmod -R 755` 步骤 |
| **5** | 为什么本次部署才暴露？ | 之前使用 `scp` 直接部署到宿主机，权限由部署脚本控制；本次改用 Docker 镜像构建，镜像内权限未处理 |

**根因 1**：**前端 Dockerfile 构建阶段未设置 assets 目录权限**，导致镜像内文件权限为 700，nginx worker 无法读取。

**问题 2：CSP 阻止 Google Fonts**

| 层级 | 问题 | 答案 |
|------|------|------|
| **1** | 为什么 Google Fonts 被阻止？ | CSP `style-src 'self' 'unsafe-inline'` 未包含 `https://fonts.googleapis.com` |
| **2** | 为什么 CSP 未包含 Google Fonts？ | nginx 配置 `wlkj-tech.cn.conf` 的 CSP 策略过于严格 |
| **3** | 为什么之前未暴露？ | 之前 `index.html` 可能未引用 Google Fonts，或本次项目结构调整引入了新的字体引用 |
| **4** | 为什么 CSP 策略未随业务变化更新？ | CSP 策略维护流程缺失，未在引入新外部资源时同步更新 CSP 白名单 |

**根因 2**：**CSP 策略维护流程缺失**，引入 Google Fonts 后未同步更新白名单。

---

### 修复措施

#### 即时修复 (已完成)
```bash
# 1. 修复 assets 目录权限
docker exec douyin_frontend chmod -R 755 /usr/share/nginx/html/assets
docker exec douyin_frontend chmod 755 /usr/share/nginx/html

# 2. 更新 CSP 策略 (nginx/conf.d/wlkj-tech.cn.conf)
# 修改前: style-src 'self' 'unsafe-inline'; font-src 'self' data:;
# 修改后: style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' data: https://fonts.gstatic.com;

# 3. 重启 nginx
docker restart douyin_nginx
```

#### 永久修复 (需落地)
1. 在 [frontend/Dockerfile](file:///c:/Users/Administrator/Documents/trae_projects/douyin/frontend/Dockerfile) 中添加权限修复步骤
2. 将 CSP 策略白名单同步至本地 [nginx/conf.d/wlkj-tech.cn.conf](file:///c:/Users/Administrator/Documents/trae_projects/douyin/nginx/conf.d/wlkj-tech.cn.conf)

---

### 改进措施 (防止复发)

| 编号 | 措施 | 优先级 | 负责人 | 目标完成时间 | 状态 |
|------|------|--------|--------|--------------|------|
| **IMP-006** | 前端 Dockerfile 在 `COPY --from=builder` 后添加 `RUN chmod -R 755 /usr/share/nginx/html` | P0 | 开发 | 立即 | ✅ 已完成（Dockerfile 第 8 行已添加 chmod，镜像已重建验证） |
| **IMP-007** | 同步更新本地 nginx CSP 配置，添加 `fonts.googleapis.com` 和 `fonts.gstatic.com` | P0 | 开发 | 立即 | ✅ 已完成（服务器已验证） |
| **IMP-008** | 建立 CSP 白名单维护流程：引入新外部资源时必须同步更新 CSP | P1 | 架构师 | 2026-08-28 | ⏳ 计划中 |
| **IMP-009** | 部署后健康检查增加 JS/CSS 资源访问验证，而非仅检查 HTTP 200 | P1 | 运维 | 2026-08-28 | ⏳ 计划中 |
| **IMP-010** | Docker 镜像构建后自动验证关键文件权限，失败则阻止部署 | P2 | 运维 | 2026-09-01 | ⏳ 计划中 |

---

### 经验教训

1. **Docker 构建的权限陷阱**：`COPY` 指令保留源文件权限，构建阶段必须显式设置运行时权限
2. **容器健康检查的盲区**：容器级 `HEALTHCHECK` 只检查 HTTP 状态码，无法发现静态资源 403
3. **CSP 策略与业务同步**：引入新外部资源时必须同步更新 CSP 白名单
4. **白屏问题的快速定位**：浏览器控制台报错是定位前端故障的第一手信息，需建立"控制台报错 → 根因"映射表
5. **与 INC-20260822-001 的关联**：两次均为前端 403 权限问题，但根因不同（scp 部署 vs Docker 构建），需分别防护

---

### 与历史事故的关联分析

| 事故编号 | 现象 | 根因 | 本次关联 |
|----------|------|------|----------|
| INC-20260822-001 | 前端 403 白屏 | scp 部署未修复宿主机文件权限 | 根因不同，但现象相同，均需在部署流程中处理权限 |
| INC-20260824-001 | 前端 403 白屏 + CSP | Docker 构建未设置镜像内文件权限 + CSP 策略未同步 | 本次新增 CSP 问题 |

**防护建议**：统一在 Dockerfile 和部署脚本中添加权限修复步骤，建立"前端部署权限检查清单"。

---

## 附录：前端 Dockerfile 权限修复补丁

```dockerfile
# frontend/Dockerfile 修复补丁
# 在 COPY --from=builder 后添加权限修复

# Production stage
FROM docker.1ms.run/nginx:alpine AS production

# Copy built assets
COPY --from=builder /app/build /usr/share/nginx/html

# Fix permissions (关键修复：确保 nginx worker 可读)
RUN chmod -R 755 /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ... 其余配置不变
```

---

## INC-20260824-002: 容器内残留 Windows 路径污染（潜在 Bug 排查发现）

### 基本信息
| 项目 | 详情 |
|------|------|
| **事故编号** | INC-20260824-002 |
| **发现时间** | 2026-08-24 22:20 (UTC+8)（INC-20260824-001 排查过程中发现） |
| **解决时间** | 2026-08-24 22:16 (UTC+8)（celery 容器最终清理完成） |
| **严重级别** | P2 (Medium) - 当前未影响业务，但存在潜在风险 |
| **影响范围** | `douyin_frontend`、`douyin_monitor`、`douyin_celery_worker`、`douyin_celery_beat` 容器 |
| **发现人** | 运维排查 |
| **状态** | **已修复** |

---

### 问题描述

在排查 INC-20260824-001 时，通过 `find` 命令发现容器内存在 Windows 路径污染：

**前端容器 (`douyin_frontend`)**：
```
/usr/share/nginx/html/C:/$RECYCLE.BIN
/usr/share/nginx/html/C:/$WinREAgent
/usr/share/nginx/html/C:/$Windows.~WS
/usr/share/nginx/html/C:/6096779bb084295792
```

**Monitor 容器 (`douyin_monitor`)**：
```
/app/C:/$RECYCLE.BIN
/app/C:/$WinREAgent
/app/C:/$Windows.~WS
/app/C:/6096779bb084295792
```

**Celery 容器 (`douyin_celery_worker` / `douyin_celery_beat`)** — 2026-08-24 22:10 复查发现：
```
/app/C:/$RECYCLE.BIN/S-1-5-18/desktop.ini
/app/C:/$RECYCLE.BIN/S-1-5-21-475528884-1138294492-2197336103-500/desktop.ini
```
- 污染体积：497MB / 容器
- 原因：celery 镜像构建于 21:43，早于 `.dockerignore` 更新时间 (22:01)，未应用 Windows 排除规则

这些是 Windows 系统的隐藏目录（回收站、Windows 恢复环境、Windows 升级临时文件），被错误地打包进 Docker 构建上下文。

---

### 根因分析

| 层级 | 问题 | 答案 |
|------|------|------|
| **1** | 为什么容器内有 `C:` 目录？ | Docker 构建上下文包含了 Windows 系统的隐藏目录 |
| **2** | 为什么构建上下文包含这些目录？ | `.dockerignore` 未排除 `C:`、`$RECYCLE.BIN`、`$WinREAgent` 等 Windows 特定路径 |
| **3** | 为什么 `.dockerignore` 未排除？ | `.dockerignore` 主要针对 `node_modules`、`.git` 等，未考虑 Windows 系统文件 |
| **4** | 为什么本地存在 `C:` 目录？ | Windows 系统或某些工具（如 Docker Desktop、WSL）创建了这些目录 |

**根因**：`.dockerignore` 未排除 Windows 系统隐藏目录，导致它们被打包进 Docker 镜像。

---

### 潜在风险

1. **镜像体积膨胀**：`C:` 目录可能包含大量 Windows 临时文件
2. **安全风险**：`$RECYCLE.BIN` 可能包含已删除的敏感文件
3. **路径混淆**：`C:` 目录在 Linux 容器内是合法路径，可能被误访问
4. **构建上下文过大**：每次构建都会传输这些无用文件

---

### 其他发现的问题

| 编号 | 问题 | 严重级别 | 状态 |
|------|------|--------|------|
| **ISS-001** | 前端容器 `/usr/share/nginx/html/build/` 目录冗余 | P3 | 待清理 |
| **ISS-002** | nginx 日志显示 `.git/HEAD`、`.git/config` 被扫描（返回 404，正常防护） | P3 | 监控中 |
| **ISS-003** | `favicon.ico` 返回 404 | P3 | 待修复 |
| **ISS-004** | 根路径 `/` 在某些情况下返回 404 | P3 | 待排查 |

---

### 改进措施

| 编号 | 措施 | 优先级 | 负责人 | 目标完成时间 | 状态 |
|------|------|--------|--------|--------------|------|
| **IMP-011** | 更新 `.dockerignore` 添加 Windows 系统文件排除规则（根目录、monitor、frontend） | P0 | 开发 | 立即 | ✅ 已完成 |
| **IMP-012** | 清理所有容器内 `C:` 目录（frontend、monitor、celery_worker、celery_beat） | P1 | 运维 | 立即 | ✅ 已完成 |
| **IMP-015** | 重新构建 celery 镜像并清理旧镜像（1.51GB→750MB） | P1 | 运维 | 立即 | ✅ 已完成 |
| **IMP-013** | 添加 `favicon.ico` 文件 | P3 | 开发 | 2026-08-28 | 计划中 |
| **IMP-014** | 排查根路径 `/` 返回 404 的问题 | P3 | 开发 | 2026-08-28 | 计划中 |

---

### `.dockerignore` 修复补丁

```dockerignore
# Windows system files (critical!)
C:
$RECYCLE.BIN
$WinREAgent
$Windows.~WS
desktop.ini
Thumbs.db
ehthumbs.db
```

---

## 附录：本次排查发现的 Bug 清单

| 编号 | 类型 | 描述 | 当前状态 |
|------|------|------|----------|
| INC-20260824-001 | 已发生事故 | Docker 重建后前端 assets 权限丢失 + CSP 阻止 Google Fonts | ✅ 已修复（权限 755 + CSP 白名单已验证） |
| INC-20260824-002 | 潜在 Bug | 容器内残留 Windows 路径污染 | ✅ 已修复（容器内无 C: 目录） |
| ISS-001 | 潜在 Bug | 前端容器 build 目录冗余 | ✅ 已修复（容器内无 build 目录） |
| ISS-002 | 安全监控 | `.git/` 目录被扫描（已防护） | ✅ 已修复（容器内无 .git 目录） |
| ISS-003 | 小问题 | favicon.ico 404 | ❌ 待修复（favicon.ico 不存在） |
| ISS-004 | 潜在 Bug | 根路径 `/` 偶发 404 | ✅ 已修复（返回 HTTP 200） |

---

## 2026-08-25 复审记录

### 验证结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 前端容器 assets 目录权限 | ✅ drwxr-xr-x (755) | nginx worker 可读 |
| 容器内 Windows 污染 (C: 目录) | ✅ 无污染 | frontend/monitor 容器均干净 |
| CSP Google Fonts 白名单 | ✅ 已包含 | fonts.googleapis.com + fonts.gstatic.com |
| .dockerignore Windows 排除规则 | ✅ 3 个文件均含 | 根/monitor/frontend |
| 根路径 / 返回状态 | ✅ HTTP 200 | 正常 |
| 前端容器 build 目录冗余 | ✅ 已清理 | 不存在 |
| 前端容器 .git 目录 | ✅ 已清理 | 不存在 |
| favicon.ico | ❌ 仍缺失 | IMP-013 待落地 |
| Dockerfile chmod 修复 | ✅ 已完成 | IMP-006 已落地（第 8 行 RUN chmod -R 755） |

### 仍需落地的改进措施

| 编号 | 措施 | 优先级 | 状态 |
|------|------|--------|------|
| IMP-006 | Dockerfile 添加 `RUN chmod -R 755` | P0 | ✅ 已完成 |
| IMP-013 | 添加 favicon.ico | P3 | ⏳ 计划中 |
| IMP-002 | 标准化 deploy-frontend.sh 脚本 | P0 | ⏳ 待落地 |
| IMP-005 | 部署后自动健康检查 | P1 | ⏳ 计划中 |
| IMP-008 | CSP 白名单维护流程 | P1 | ⏳ 计划中 |
| IMP-009 | JS/CSS 资源访问验证 | P1 | ⏳ 计划中 |
| IMP-010 | 镜像构建权限自动验证 | P2 | ⏳ 计划中 |
| IMP-004 | Nginx access_log 403 详情 | P2 | ⏳ 计划中 |

---

*下次审查: 2026-09-22*
*维护者: 运维团队*
*最近复审: 2026-08-25*

---
## INC-20260921-001: Nginx 502 Bad Gateway 与 API 401 Unauthorized 连发

### 基本信息
| 项目 | 详情 |
|------|------|
| **事故编号** | INC-20260921-001 |
| **发生时间** | 2026-09-21 13:42 UTC+8 |
| **发现时间** | 2026-09-21 13:45 UTC+8 |
| **解决时间** | 2026-09-21 14:10 UTC+8 |
| **持续时长** | ~28 分钟 |
| **严重级别** | P1 |
| **影响范围** | https://wlkj-tech.cn 前端全站 + API /api/v1/products/creators/orders |
| **报告人** | 前端监控 |
| **复盘完成** | 2026-09-21 15:00 |

### 时间线
| 时间 | 事件 |
|------|------|
| 13:42 | Nginx 返回 502 Bad Gateway，error.log 显示 `connect() failed (111: Connection refused) while connecting to upstream http://127.0.0.1:3000` |
| 13:43 | 检查 docker，douyin_frontend / douyin_monitor 均健康，端口 3000/5000 监听正常 |
| 13:45 | 发现 /etc/nginx/conf.d/cci-monitor.conf proxy_set_header 语法错误导致 nginx reload 失败，历史配置残留 |
| 13:50 | 修复 cci-monitor.conf，nginx -t 通过，reload 成功，502 恢复 |
| 13:55 | 前端 API 请求仍 401 Unauthorized，日志显示 `Missing or invalid Authorization header` |
| 14:00 | 定位后端 app.py check_auth 要求 Bearer API_KEY，后端 API_KEY=your_api_key，frontend/.env VITE_API_KEY 未配置 |
| 14:05 | 统一 API_KEY 为 wlkj_douyin_api_20260921_abc123，frontend/.env 设置 VITE_API_KEY，执行 vite build |
| 14:08 | 部署前端构建产物至 douyin_frontend，nginx reload |
| 14:10 | API 返回 200，401 解除 |

### 根因
1. Nginx 配置 cci-monitor.conf proxy_set_header 语法错误导致 reload 失败，502。
2. API 鉴权未统一：后端强制 Bearer API_KEY，前端未配置 VITE_API_KEY，且历史上使用 SKIP_AUTH 临时绕过，导致密钥不一致。

### 修复措施
- 修复 /etc/nginx/conf.d/cci-monitor.conf 变量转义，nginx -t 通过 reload。
- 后端 /opt/douyin-platform/config/.env 设置 `API_KEY=wlkj_douyin_api_20260921_abc123`，移除 SKIP_AUTH。
- 前端 `src/frontend/.env` 设置 `VITE_API_KEY=wlkj_douyin_api_20260921_abc123`，vite build 后 scp 部署。

### 改进措施
| 编号 | 措施 |
|------|------|
| IMP-021 | Nginx 配置变更前强制 `nginx -t` CI 校验 |
| IMP-022 | API_KEY 与 VITE_API_KEY 纳入统一密钥管理，文档化 |
| IMP-023 | 前端构建流水线自动注入 VITE_*，避免手动修改 .env |

### 相关文档更新
| 文档 | 更新内容 |
|------|----------|
| CHANGELOG.md | [Unreleased] Fixed 新增 2026-09-21 502/401 记录 |
| docs/INCIDENTS.md | 新增 INC-20260921-001 |
| docs/2_api/API_DOCUMENTATION.md | API 鉴权说明更新