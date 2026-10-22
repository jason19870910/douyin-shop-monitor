# 安全加固指南

> **版本**: 1.1.0  
> **更新日期**: 2026-10-16  
> **适用范围**: 开发、测试、Staging、生产环境  
> **合规基线**: 等保 2.0 三级、GDPR 最小权限原则、OWASP Top 10

---

## 1. 密钥与凭证管理

### 1.1 原则
| 原则 | 实施要求 |
|------|---------|
| **零硬编码** | 代码/镜像/日志/配置文件中绝不出现明文密钥 |
| **最小权限** | 每个密钥仅授予完成任务所需的最小权限集 |
| **定期轮换** | 关键密钥 ≤ 90 天轮换，泄露立即轮换 |
| **分环境隔离** | 开发/测试/生产环境使用完全不同的密钥体系 |
| **审计追踪** | 所有密钥访问/变更留存审计日志 ≥ 1 年 |

### 1.2 密钥分级与轮换周期
| 密钥类型 | 示例 | 轮换周期 | 存储位置 | 泄露响应 SLA |
|---------|------|---------|---------|-------------|
| **L0 核心根密钥** | CA 根证书、KMS 主密钥 | 1 年 | 硬件安全模块 (HSM) / 云 KMS | 1 小时内 |
| **L1 服务身份** | API 签名密钥 (`a_bogus` 密钥对)、API Gateway 密钥 | 90 天 | 云 Secret Manager / Vault | 4 小时内 |
| **L2 应用凭证** | Redis 密码、外部 API Key (`API_KEY`) | 90 天 | `.env` (生产由 Secret Manager 注入) | 4 小时内 |
| **L3 运营凭证** | 抖音 Cookie、动态签名参数 (`a_bogus`、`msToken` 等) | 失效即更新 (通常 2h-7 天) | `.env` + 运维手动维护 | 发现即更新 |
| **L4 临时/一次性** | CI/CD 部署 Token、调试 Token | 单次/24 小时 | CI 变量 / 临时文件 | 自动失效 |

### 1.3 存储规范
```bash
# ✅ 正确：生产环境使用 Secret Manager 注入
# docker-compose.yml
services:
  app:
    environment:
      - FXG_COOKIES=${FXG_COOKIES}  # 由 CI/CD 从 Secret Manager 获取注入
      - CREATOR_COOKIES=${CREATOR_COOKIES}

# ❌ 错误：直接写在代码/镜像/公共配置中
# FXG_COOKIES=xxx  # 禁止提交到 Git
```

### 1.4 泄露应急响应
```bash
# 1. 立即轮换
#   - 更新 Secret Manager 中的密钥
#   - 触发 CI/CD 重新部署 (自动拉取新密钥)

# 2. 撤销旧凭证
#   - 外部 API: 在上游控制台 Revoke 旧 Token/Cookie
#   - API Key: 轮换 .env 中 API_KEY 并重新部署

# 3. 审计
#   - 检查近 30 天访问日志: grep "old_key" /var/log/*.log
#   - 确认无异常数据访问/篡改

# 4. 复盘记录
#   - 填写 Security Incident Report
#   - 更新威胁模型
```

---

## 2. 网络与传输安全

### 2.1 TLS 配置基线 (Nginx)
```nginx
# /etc/nginx/conf.d/ssl-base.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS (生产环境开启)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 1.1.1.1 valid=300s;
resolver_timeout 5s;
```

### 2.2 安全响应头
```nginx
# /etc/nginx/conf.d/security-headers.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://wlkj-tech.cn;" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### 2.3 网络分段
```
                    Internet
                       │
              ┌────────▼────────┐
              │  WAF / CDN      │  ← DDoS 防护、Bot 管理、IP 信誉
              └────────┬────────┘
                       │ HTTPS (443)
              ┌────────▼────────┐
              │  Nginx (DMZ)    │  ← TLS 终止、速率限制、IP 白名单
              └────────┬────────┘
                       │ HTTP (内网)
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │ Flask   │   │ 调度器   │   │  Redis   │  ← 内网 VPC，安全组仅允许必要端口
   │ :5000   │   │ (内置)   │   │  :6379   │
   └─────────┘   └──────────┘   └──────────┘
```

### 2.4 速率限制
```nginx
# /etc/nginx/conf.d/rate-limit.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=conn:10m;

server {
    location /api/ {
        limit_req zone=api burst=200 nodelay;
        limit_conn conn 50;
    }
    location /api/auth/login {
        limit_req zone=login burst=3 nodelay;
    }
}
```

---

## 3. 应用层安全

### 3.1 输入验证与输出编码
| 层面 | 要求 |
|------|------|
| **查询参数** | Pydantic/FastAPI/Flask-RESTX 模型验证，拒绝额外字段 |
| **请求 Body** | JSON Schema 验证，大小限制 ≤ 1MB |
| **文件上传** | 仅允许白名单 MIME/扩展名，病毒扫描，存储对象存储非本地磁盘 |
| **SQL** | 仅使用参数化查询 / ORM，禁止原生 SQL 拼接 |
| **Shell** | 禁止 `os.system`/`subprocess` 直接拼接用户输入，使用 `shlex.quote` |
| **XSS 防护** | 模板引擎自动转义，CSP 头，`HttpOnly`/`Secure` Cookie 标志 |
| **CSRF** | 状态改变接口要求 `X-CSRF-Token` 或 SameSite=Strict Cookie |

### 3.2 认证与授权

系统采用 **双 Header 认证** 机制，所有 `/api/v1/*` 请求（公共端点除外）需同时携带以下两个 Header 中任一有效值：

| Header | 说明 | 示例 |
|--------|------|------|
| `Authorization` | Bearer 令牌 | `Authorization: Bearer <API_KEY>` |
| `X-API-Key` | API 密钥 | `X-API-Key: <API_KEY>` |

两个 Header 传入相同的 API_KEY，任一校验通过即视为认证成功。

**公共端点（无需认证）**：
- `/api/v1/health` - 基础健康检查
- `/api/v1/health/external` - 外部 API 健康检查
- `/api/v1/auth/login` - OAuth 登录
- `/api/v1/auth/callback` - OAuth 回调
- `/api/v1/auth/qr-code` - 二维码登录
- `/api/v1/auth/status` - 登录状态查询

**中间件实现**（`src/backend/app.py` `check_auth`）：
```python
@app.before_request
def check_auth():
    if SKIP_AUTH:
        return
    if request.method == 'OPTIONS':
        return
    if request.path in PUBLIC_ENDPOINTS:
        return
    if request.path.startswith('/api/v1/'):
        auth_header = request.headers.get('Authorization', '')
        api_key_header = request.headers.get('X-API-Key', '')
        api_key = (Config.API_KEY or '').strip()
        bearer_valid = auth_header.startswith('Bearer ') and auth_header[7:] == api_key
        api_key_valid = api_key_header == api_key and api_key != ''
        if not (bearer_valid or api_key_valid):
            return unauthorized_response('Missing or invalid Authorization header or X-API-Key')
```

### 3.3 敏感数据保护
| 数据类型 | 处理方式 |
|---------|---------|
| **PII (手机/邮箱/身份证)** | 存储前脱敏/加密，日志仅显示掩码 (`138****1234`) |
| **密码** | 仅存 `bcrypt`/`argon2` 哈希，不可逆 |
| **API Key/Token** | 仅存前缀 + 哈希 (`sk_live_abc...` + `sha256(full_key)`)，验证时比对哈希 |
| **Cookie/Session** | `HttpOnly`、`Secure`、`SameSite=Strict`、`Domain` 限制 |
| **日志脱敏** | 统一日志过滤器自动替换：`password=xxx` → `password=***` |

---

## 4. 依赖与供应链安全

### 4.1 依赖管理基线
```bash
# Python
pip-audit --desc --format=json  # CI 每次运行
pip install --require-hashes -r requirements.txt  # 固定哈希

# Node.js
npm audit --audit-level=high  # CI 每次运行
npm ci --package-lock-only  # 锁定版本
```

### 4.2 依赖审查清单 (新增/升级依赖时)
- [ ] 来源可信：官方仓库 / 知名组织维护
- [ ] 维护活跃：近 6 个月有提交，Issue 响应及时
- [ ] 无已知高危漏洞：`CVE` 扫描通过
- [ ] 许可证兼容：MIT/Apache-2.0/BSD 等宽松协议
- [ ] 体积合理：无异常大的依赖树
- [ ] 固定版本：`requirements.txt` / `package-lock.json` 锁定精确版本

### 4.3 容器镜像安全
```dockerfile
# Dockerfile 安全基线
FROM python:3.11-slim  # 精简基础镜像，定期更新

# 非 root 用户运行
RUN useradd -m -u 1000 appuser
USER appuser

# 多阶段构建：构建阶段与运行阶段分离
# 最终镜像不含编译工具、源码、测试文件

# 镜像签名与验证
# cosign sign --key cosign.key yourdockerhubuser/douyin_monitor:latest
# cosign verify --key cosign.pub yourdockerhubuser/douyin_monitor:latest
```

### 4.4 SBOM (Software Bill of Materials)
```bash
# 生成 SBOM (CI 集成)
syft yourdockerhubuser/douyin_monitor:latest -o spdx-json > sbom.spdx.json

# 漏洞扫描
grype yourdockerhubuser/douyin_monitor:latest
trivy image yourdockerhubuser/douyin_monitor:latest
```

---

## 5. 运行时安全

### 5.1 进程与文件系统加固
```yaml
# docker-compose.yml 安全选项
services:
  app:
    security_opt:
      - no-new-privileges:true
    read_only: true  # 根文件系统只读
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/run:noexec,nosuid,size=10m
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # 仅必要能力
```

### 5.2 运行时监控
```bash
# Falco 规则示例：检测异常进程/文件访问
# - rule: Suspicious Process in Container
#   condition: container.id != host and proc.name in (nc, ncat, netcat, socat, wget, curl, bash, sh)
#   output: "Suspicious process in container (user=%user.name cmd=%proc.cmdline)"
#   priority: WARNING

# 文件完整性监控 (AIDE/Tripwire)
# 每日对比 /app/src/backend 关键文件哈希
```

### 5.3 审计日志
```python
# 结构化审计日志 (JSON 格式，发送至 Loki/ELK)
import logging
import json
from datetime import datetime

audit_logger = logging.getLogger('audit')

def audit_log(event: str, user: str, resource: str, action: str, result: str, **extra):
    audit_logger.info(json.dumps({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'event': event,
        'user': user,
        'resource': resource,
        'action': action,
        'result': result,  # success/failed/denied
        **extra
    }))

# 使用示例 (认证由 check_auth 中间件统一处理，端点内直接记录审计)
def delete_product(product_id):
    audit_log('product_delete', request.headers.get('X-API-Key', ''), f'product:{product_id}', 'DELETE', 'success')
    ...
```

---

## 6. 漏洞管理与应急响应

### 6.1 漏洞分级与 SLA
| 严重度 | CVSS 分值 | 修复 SLA | 示例 |
|--------|----------|---------|------|
| **Critical** | 9.0-10.0 | 24 小时 | RCE、未授权访问、SQLi 导致数据泄露 |
| **High** | 7.0-8.9 | 72 小时 | 认证绕过、权限提升、敏感信息泄露 |
| **Medium** | 4.0-6.9 | 30 天 | XSS、CSRF、信息泄露(非敏感) |
| **Low** | 0.1-3.9 | 90 天 | 信息泄露(版本号)、配置不当 |

### 6.2 应急响应流程
```
发现漏洞
    │
    ├─► 评估严重度 (CVSS + 业务影响)
    │
    ├─► Critical/High: 启动应急响应小组
    │       ├─► 1 小时内: 临时缓解 (WAF 规则、下线受影响接口、IP 封禁)
    │       ├─► 4 小时内: 根因分析 + 修复代码
    │       ├─► 24 小时内: 灰度发布验证 + 全量发布
    │       └─► 48 小时内: 事后复盘报告
    │
    └─► Medium/Low: 纳入下个迭代计划
            ├─► 创建 Issue + 打标签 severity/medium
            └─► Sprint Planning 排期修复
```

### 6.3 关键漏洞类型专项防护
| 漏洞类型 | 防护措施 |
|---------|---------|
| **Log4Shell 类 (RCE)** | 禁止不可信输入进入日志格式化，升级日志库，WAF 拦截 `${jndi:` 模式 |
| **反序列化** | 禁用 `pickle`/`yaml.load`/`eval`，使用 JSON/Protobuf |
| **SSRF** | 外部请求白名单域名/IP，禁止访问内网元数据服务 (169.254.169.254) |
| **路径遍历** | 规范化路径 `os.path.normpath`，校验在允许目录内 |
| **依赖混淆** | 私有包使用 scoped 名称 (`@company/pkg`)，配置 npm/pip 仅从私有源拉取 |

---

## 7. 合规与审计

### 7.1 等保 2.0 三级关键控制点映射
| 控制点 | 实施状态 | 证据 |
|--------|---------|------|
| 身份鉴别 (强密码、MFA、锁定) | ✅ | API Key 认证 + 双 Header 校验 |
| 访问控制 (最小权限、RBAC) | ✅ | 基于角色的接口授权 |
| 安全审计 (全量日志、防篡改) | ✅ | 结构化日志 + Loki 集中存储 |
| 入侵防范 (WAF、速率限制、异常检测) | ✅ | Nginx + Falco + 速率限制 |
| 恶意代码防范 (依赖扫描、镜像签名) | ✅ | CI 集成 Trivy/Gripe + Cosign |
| 数据完整性/机密性 (加密传输/存储) | ✅ | TLS 1.2+、敏感字段加密 |
| 备份恢复 (定期备份、演练) | ✅ | 每日备份 + 季度恢复演练 |

### 7.2 审计日志保留
| 日志类型 | 保留期限 | 存储位置 |
|---------|---------|---------|
| 访问日志 (Nginx) | 1 年 | Loki + 对象存储归档 |
| 应用审计日志 | 3 年 | Loki + 合规存储桶 (WORM) |
| 安全事件日志 | 永久 | 专用 SIEM / 归档桶 |
| 调度器同步日志 | 3 年 | Loki + 合规存储桶 (WORM) |

---

## 8. 安全培训与文化

### 8.1 必修培训 (全员/年)
| 主题 | 形式 | 频率 |
|------|------|------|
| 安全编码规范 (OWASP Top 10) | 线上课程 + 考试 | 入职 + 年度复训 |
| 密钥管理与泄露应急 | 实战演练 | 半年一次 |
| 社会工程学/钓鱼识别 | 模拟钓鱼邮件 | 季度 |
| 数据保护与隐私合规 | 线上课程 | 年度 |

### 8.2 安全文化建设
- **Security Champions**：每团队指定 1 名安全联络人，参与威胁建模评审
- **Bug Bounty / 内部漏洞奖励**：发现并负责任披露漏洞给予奖励
- **事后复盘公开透明**：无责文化，关注系统性改进而非追责个人

---

## 9. 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.1.0 | 2026-10-16 | 同步架构变更：认证改为双 Header (Authorization + X-API-Key)，移除 JWT/MySQL 引用，更新服务名为 app | - |
| 1.0.0 | 2026-08-18 | 初始版本：密钥管理、网络传输、应用层、依赖供应链、运行时、漏洞管理、合规审计 | Auto |

---

> **执行检查清单 (每季度自检)**：
> - [ ] 所有密钥轮换记录完整，无过期未轮换
> - [ ] TLS 证书有效期 > 30 天，自动续期正常
> - [ ] 依赖漏洞扫描 0 Critical/High
> - [ ] 容器镜像签名验证通过
> - [ ] WAF/速率限制规则生效，近 30 天无异常流量
> - [ ] 审计日志完整、可查、防篡改
> - [ ] 备份恢复演练通过 (本季度)
> - [ ] 应急响应演练完成 (本季度)
> - [ ] 全员安全培训完成率 100%