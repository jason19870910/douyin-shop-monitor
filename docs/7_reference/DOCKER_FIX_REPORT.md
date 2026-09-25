# Docker 构建修复与部署验证报告

> **修复日期**: 2026-08-19  
> **服务器**: 122.51.208.138  
> **项目**: `/opt/douyin-platform/apps/monitor`

---

## 1. 问题背景

### 1.1 现象
- `docker compose build` 因 Debian 镜像源下载系统依赖极慢（`apt-get update` 阶段卡顿 10+ 分钟），导致构建超时失败
- 即使构建成功，容器启动时抛出 `ModuleNotFoundError: No module named 'flasgger'`，Gunicorn worker 启动失败，健康检查不通过，容器无限重启

### 1.2 根因
| 原因 | 说明 |
|------|------|
| **网络环境** | 服务器访问 `deb.debian.org` 速度极慢（~13 KB/s），安装 77 个系统包需 20+ 分钟 |
| **依赖缺失** | `requirements.txt` 虽含 `flasgger==0.9.7.1`，但构建中断导致未安装 |
| **代码强依赖** | 早期 `app.py` 直接 `from flasgger import Swagger`，缺包即崩溃 |

---

## 2. 修复方案

### 2.1 代码层：可选导入 `flasgger` (已完成)
**文件**: `app.py` 第 35-63 行

```python
# Flasgger / Swagger UI（可选，未安装时跳过）
try:
    from flasgger import Swagger
    swagger = Swagger(app, template={ ... })
except ImportError:
    swagger = None
    logger.warning("flasgger not installed, Swagger UI disabled")
```
- **效果**: 缺包时仅记录警告，核心 API 正常启动

### 2.2 部署层：利用卷映射热加载 (规避重新构建)
**文件**: `docker-compose.yml` 第 37 行

```yaml
volumes:
  - ./data:/data
  - ~/.cache:/root/.cache
  - ./app.py:/app/app.py    # ← 关键：宿主机代码直接映射进容器
```

**操作流程**:
```bash
# 1. 本地修改 app.py 后同步到服务器
scp -i ~/.ssh/id_rsa app.py root@122.51.208.138:/opt/douyin-platform/apps/monitor/app.py

# 2. 秒级重启生效（无需 build）
ssh root@122.51.208.138 "cd /opt/douyin-platform/apps/monitor && docker compose restart monitor"
```

- **优势**: 绕过 `apt-get`/`pip install` 全流程，修改生效 < 10 秒

### 2.3 长期建议（非紧急）
- 网络条件允许时重新构建镜像：`docker compose build --no-cache monitor`
- 或预构建含 `flasgger` 的基础镜像推送至私有仓库

---

## 3. 部署验证结果

### 3.1 服务状态
```bash
$ docker ps | grep douyin_monitor
f4100e8daaec   monitor-monitor   "gunicorn app:app --…"   Up 2 minutes (healthy)   0.0.0.0:5000->5000/tcp   douyin_monitor
```
- 容器状态: **Up (healthy)**
- 健康检查: `curl -f http://localhost:5000/api/health` 通过

### 3.2 日志确认
```
[2026-08-19 02:03:34] [INFO] Starting gunicorn 21.2.0
[2026-08-19 02:03:34] [INFO] Listening at: http://0.0.0.0:5000
[2026-08-19 02:03:35] [WARNING] flasgger not installed, Swagger UI disabled
[2026-08-19 02:03:35] [INFO] APScheduler started
```
- Gunicorn 4 workers 正常启动
- `flasgger` 警告仅影响 Swagger UI，不影响业务

### 3.3 API 端点验证 (全部 200)

| 端点 | 状态码 | 说明 |
|------|--------|------|
| `GET /api/health` | **200** | 健康检查 |
| `GET /api/stats?period=7d` | **200** | 仪表盘统计别名 |
| `GET /api/dashboard/stats?period=7d` | **200** | 仪表盘统计标准端点 |
| `GET /api/products` | **200** | 商品列表 |
| `GET /api/orders` | **200** | 订单列表 |
| `GET /api/videos` | **200** | 视频列表 |
| `GET /api/auth/status` | **200** | 授权状态 |
| `GET /api/alerts/douyin/config` | **200** | 抖音告警配置 |
| `GET /api/alerts/dian/config` | **200** | 抖店告警配置 |

### 3.4 前端静态资源
- `https://wlkj-tech.cn/` → **200** (HTML)
- `https://wlkj-tech.cn/assets/index-*.js` → **200** (JS)
- `https://wlkj-tech.cn/assets/index-*.css` → **200** (CSS)
- 权限已修复 (`chown -R nginx:nginx /opt/.../build && chmod -R 755 assets`)

---

## 4. 运维操作速查表

| 场景 | 命令 | 耗时 |
|------|------|------|
| **代码热更新** | `scp app.py root@server:/opt/.../ && docker compose restart monitor` | ~5 秒 |
| **查看日志** | `docker logs douyin_monitor -f --tail 100` | 实时 |
| **健康检查** | `curl -s https://wlkj-tech.cn/api/health \| jq .` | < 1 秒 |
| **完整重启栈** | `docker compose restart` | ~15 秒 |
| **重新构建镜像** | `docker compose build --no-cache monitor` | 10-30 分钟 (视网络) |

---

## 5. 结论

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 服务可用性 | ❌ 容器循环重启 | ✅ 稳定运行 (healthy) |
| 部署周期 | 20+ 分钟 (含构建) | **< 10 秒** (热加载) |
| 核心 API | 502/503 | **全部 200** |
| Swagger UI | 报错崩溃 | ⚠️ 禁用 (仅文档受影响) |

**核心结论**: 通过**代码容错 + 卷映射热加载**，在不改善网络环境前提下彻底解决了 Docker 构建慢与依赖缺失导致的服务不可用问题。后续迭代仅需 `scp + restart` 即可秒级发布。

---

## 附录：当前生产环境关键信息

```text
服务器: 122.51.208.138
部署路径: /opt/douyin-platform/apps/monitor
镜像版本: monitor-monitor:latest (db1845af64e2)
容器名称: douyin_monitor / douyin_celery_worker / douyin_celery_beat / douyin_redis
Nginx 配置: /etc/nginx/conf.d/wlkj-tech.cn.conf + douyin-monitor.conf
SSL 证书: Let's Encrypt (wlkj-tech.cn-0001)
数据目录: /opt/douyin-platform/apps/monitor/data (JSON 文件)
```