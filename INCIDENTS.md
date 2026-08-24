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
| **IMP-001** | 在部署脚本中强制添加权限修复步骤 | P0 | 运维 | 2026-08-25 | 计划中 |
| **IMP-002** | 编写标准化前端部署脚本 `deploy-frontend.sh`，内含构建、scp、权限修复、Nginx reload | P0 | 运维 | 2026-08-25 | 计划中 |
| **IMP-003** | 评估改用 Docker 镜像部署前端 (构建时指定 USER)，避免 scp 权限问题 | P1 | 架构师 | 2026-09-01 | 评估中 |
| **IMP-004** | 在 Nginx 配置中添加 `server` 级别 `access_log` 记录 403 详情，便于快速定位 | P2 | 运维 | 2026-08-30 | 计划中 |
| **IMP-005** | 增加部署后自动健康检查：`curl -f https://wlkj-tech.cn/assets/index.css` 失败则报警回滚 | P1 | 运维 | 2026-08-28 | 计划中 |

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

*下次审查: 2026-09-22*  
*维护者: 运维团队*