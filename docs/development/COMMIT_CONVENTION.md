---
title: 提交信息规范
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: Tech Lead
reviewers: [资深工程师, 架构师, DevOps Lead]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-DEV-005
tags: [开发, Git, Commit Message, Conventional Commits, 版本管理, 规范]
related_docs: [DOC-DEV-001, DOC-DEV-002, DOC-DEV-003, DOC-DEV-004]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - Tech Lead
---

# 提交信息规范

## 1. 概述
本文档基于 **Conventional Commits 1.0.0** 规范，结合项目实际定义提交信息格式，旨在实现：
- **语义化版本自动化**：通过提交类型自动判断版本号升级
- **变更日志自动生成**：CHANGELOG 自动化、发布说明自动化
- **变更可追溯**：每个提交可追溯到 Issue/PR、便于审计与回溯
- **团队协作效率**：统一格式降低认知负担、便于 Code Review

---

## 2. 提交格式

### 2.1 标准格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

| 部分 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | 提交类型，决定语义化版本影响 |
| `scope` | ⭕ | 影响模块/范围，便于过滤和归类 |
| `subject` | ✅ | 简短摘要，祈使语气，首字母小写，无句号 |
| `body` | ⭕ | 详细说明：动机、设计决策、破坏性变更 |
| `footer` | ⭕ | 关联 Issue、Breaking Change 声明、Co-author |

### 2.2 完整示例
```
feat(order): add bulk export API with CSV/Excel support

- Add new endpoint POST /api/v1/orders/export
- Support CSV and Excel format with configurable columns
- Add async job processing with progress tracking
- Implement permission check for export operation

Closes #123
Breaking Change: Response structure changed from direct file to job ID
Co-authored-by: Zhang San <zhangsan@example.com>
```

---

## 3. Type 类型规范

### 3.1 标准类型 (Conventional Commits 核心)
| type | 语义化版本影响 | 说明 | 示例 |
|------|---------------|------|------|
| `feat` | **MINOR** (次版本) | 新增用户可见功能 | `feat(order): add bulk export API` |
| `fix` | **PATCH** (补丁版本) | 修复 Bug | `fix(order): handle null status in export` |
| `perf` | **PATCH** | 性能优化 (不改变行为) | `perf(order): add index for status query` |
| `refactor` | 无 (或 PATCH) | 重构 (非功能/非修复) | `refactor(order): extract export logic to service` |
| `style` | 无 | 代码风格 (格式化、分号、空格) | `style: format order service with ruff` |
| `docs` | 无 | 文档更新 (README/CHANGELOG/API/注释) | `docs(order): update export API doc` |
| `test` | 无 | 测试相关 (新增/修改/重构测试) | `test(order): add export edge case tests` |
| `chore` | 无 | 构建/工具/依赖/配置/维护 | `chore: upgrade ruff to 0.4.0` |
| `revert` | 视情况 | 回滚之前的提交 | `revert: feat(order): add bulk export API` |

### 3.2 扩展类型 (项目扩展)
| type | 版本影响 | 说明 | 示例 |
|------|----------|------|------|
| `build` | 无 | 构建系统/外部依赖/打包配置 | `build: add docker multi-stage build` |
| `ci` | 无 | CI/CD 配置/脚本/流水线 | `ci: add security scan stage` |
| `security` | **PATCH** (或 MINOR) | 安全加固/漏洞修复/合规 | `security: upgrade vulnerable dependency` |
| `release` | **MAJOR/MINOR/PATCH** | 发布准备/版本号/CHANGELOG | `release: prepare v1.3.0` |
| `wip` | 无 | 工作进行中 (仅限本地/草稿 PR) | `wip: drafting export service` |

> **规则**：`wip` 类型**严禁**出现在合并到保护分支的历史中，仅限本地开发或 Draft PR。

---

## 4. Scope 范围规范

### 4.1 标准 Scope 列表
| scope | 覆盖模块 | 示例 |
|-------|----------|------|
| `order` | 订单模块 (列表/详情/导出/状态) | `feat(order): add bulk export` |
| `product` | 商品模块 (列表/详情/SKU/分类) | `fix(product): fix sku price calc` |
| `auth` | 认证授权 (登录/OAuth/Token/JWT/RBAC) | `feat(auth): add OAuth2 refresh token` |
| `user` | 用户/账号/个人中心 | `feat(user): add avatar upload` |
| `product` | 商品/商品详情/SKU | `fix(product): sku stock sync` |
| `compliance` | 合规/风控/规则引擎 | `feat(compliance): add keyword rule` |
| `alert` | 告警/通知/渠道 | `fix(alert): fix wecom notification` |
| `sync` | 数据同步/定时任务/Celery | `perf(sync): optimize batch insert` |
| `api` | 通用 API 基础设施 (中间件/异常/文档) | `refactor(api): unify error response` |
| `ui` | 前端 UI 组件/页面/样式 | `feat(ui): add dark theme toggle` |
| `infra` | 基础设施/部署/配置/监控/日志 | `chore(infra): add prometheus alerts` |
| `deps` | 依赖升级/锁文件 | `chore(deps): upgrade ruff to 0.4.0` |
| `release` | 发布相关 | `release: prepare v1.3.0` |
| `security` | 安全加固/漏洞修复 | `security: fix CVE-2024-xxxx` |

> **原则**：Scope 应与代码仓库目录结构/业务领域对应，团队内统一维护列表。

### 4.2 多 Scope 写法
```
feat(order,product): add cross-module search API
# 或
feat(order/product): add cross-module search API
```

---

## 5. Subject 主题规范

### 5.1 书写规则
| 规则 | 正例 | 反例 |
|------|------|------|
| **祈使语气** | `add export API` | `added export API` / `adds export API` |
| **首字母小写** | `add export API` | `Add export API` |
| **无末尾句号** | `add export API` | `add export API.` |
| **简洁明了** | `add bulk export API` | `add a new feature to export orders in bulk` |
| **< 50 字符** | `add bulk export API` | `add bulk export API with CSV and Excel support and progress tracking` |

### 5.2 常用动词词汇表
| 意图 | 推荐动词 | 示例 |
|------|----------|------|
| 新增 | `add`, `introduce`, `implement`, `support` | `add export`, `support dark mode` |
| 修复 | `fix`, `resolve`, `correct`, `handle` | `fix null pointer`, `handle edge case` |
| 移除 | `remove`, `drop`, `drop`, `eliminate` | `remove deprecated API` |
| 修改/调整 | `update`, `adjust`, `modify`, `tweak` | `update timeout config` |
| 重构 | `refactor`, `restructure`, `extract`, `simplify` | `extract service layer` |
| 优化 | `optimize`, `improve`, `enhance`, `speed up` | `optimize query performance` |
| 文档 | `document`, `add docs`, `clarify` | `document API changes` |
| 测试 | `add test`, `cover`, `extend test` | `add edge case tests` |
| 配置 | `configure`, `set up`, `enable`, `disable` | `configure rate limiter` |
| 升级 | `upgrade`, `bump`, `migrate to` | `upgrade ruff to 0.4.0` |
| 回滚 | `revert`, `roll back` | `revert: feat(xxx)` |

---

## 6. Body 正文规范

### 6.1 何时需要 Body
| 场景 | 是否必须 | 说明 |
|------|----------|------|
| 复杂功能/重构 | ✅ 必须 | 说明设计动机、技术方案、替代方案对比 |
| 破坏性变更 | ✅ 必须 | 说明影响范围、迁移指南、时间表 |
| 复杂 Bug 修复 | ✅ 推荐 | 说明根因、复现步骤、修复思路、测试验证 |
| 简单修复/文档/依赖升级 | 可选 | 简述即可，Subject 已足够 |

### 4.2 Body 结构模板
```
# 动机/背景
说明为什么要做这个变更，关联 Issue/需求背景。

# 解决方案
核心实现思路、关键设计决策、考虑的替代方案及放弃理由。

# 实现细节
关键代码变更点、新增/修改的关键类/函数、数据流变化。

# 破坏性变更 (如有)
## 影响范围
- API: ...
- 数据库: ...
- 配置: ...

## 迁移指南
1. 步骤一...
2. 步骤二...

## 时间表
- v1.3: 新版本发布，旧字段标记废弃
- v1.4: 移除旧字段

# 测试验证
- 单元测试: 新增/修改 X 个测试用例
- 集成测试: 覆盖核心链路 X 条
- 手动验证: 已在测试环境验证导出功能
- 性能测试: P99 延迟从 500ms 降至 200ms
```

### 6.3 Body 示例
```
Fix intermittent timeout in order sync when FXG API returns 429.

Root cause: Sync task didn't respect FXG rate limit (20 QPS), causing
cascading retries that exhausted Celery worker pool.

Solution:
- Add token bucket rate limiter (20 req/s) per shop in sync service
- Add exponential backoff retry with max 3 attempts
- Add circuit breaker to fail fast when rate limit exceeded
- Add metrics: sync_rate_limit_hits, sync_retry_count

Testing:
- Unit tests: rate limiter logic, backoff calculation
- Integration test: mock 429 responses, verify backoff behavior
- Load test: 100 concurrent shops, 0 sync failures

Closes #456
Co-authored-by: Li Si <lisi@example.com>
```

---

## 7. Footer 页脚规范

### 7.1 关联 Issue
| 关键词 | 含义 | 示例 |
|--------|------|------|
| `Closes` | 关闭 Issue (合并后自动关闭) | `Closes #123` |
| `Fixes` | 修复 Issue (同 `Closes`) | `Fixes #456` |
| `Resolves` | 解决 Issue (同 `Closes`) | `Resolves #789` |
| `Refs` | 关联但不关闭 | `Refs #111, #222` |
| `See also` | 参考相关 | `See also: #333` |

> 多个 Issue 用逗号或换行分隔：`Closes #123, #456`

### 7.2 Breaking Change 声明
```text
BREAKING CHANGE: API response structure changed from direct file download to async job pattern.

Impact:
- Old: GET /api/v1/orders/export → 200 OK (file stream)
- New: POST /api/v1/orders/export → 202 Accepted { job_id }
         GET /api/v1/export/jobs/{job_id} → 200 OK (file stream)

Migration:
1. Update client to call POST then poll job status
2. Update timeout handling (async may take 30s+)
3. Old endpoint deprecated, will be removed in v1.4.0

Migration guide: docs/migration/v1.3-export-api.md
```

### 7.3 Co-authored-by (协作者)
```text
Co-authored-by: Zhang San <zhangsan@example.com>
Co-authored-by: Li Si <lisi@example.com>
```

### 7.4 完整 Footer 示例
```
Closes #123
Refs #456, #789

BREAKING CHANGE: Export API changed from sync to async pattern.
See migration guide: docs/migration/v1.3-export-api.md

Co-authored-by: Zhang San <zhangsan@example.com>
Co-authored-by: Li Si <lisi@example.com>
```

---

## 6. 完整提交示例库

### 6.1 功能新增
```
feat(order): add bulk export API with CSV/Excel support

- Add new endpoint POST /api/v1/orders/export
- Support CSV and Excel format with configurable columns
- Add async job processing with progress tracking (Redis + Celery)
- Implement permission check for export operation
- Add rate limiting (20 req/s per shop) to respect FXG API quota

Closes #123
Breaking Change: Response changed from direct file to async job pattern.
Migration guide: docs/migration/v1.3-export-api.md
```

### 6.2 Bug 修复
```
fix(order): handle null status in bulk export CSV writer

Root cause: Order.status can be None for legacy orders, causing
AttributeError when CSV writer calls str(status.value).

Fix: Add null check, default to 'UNKNOWN' status for display.
Add regression test in test_export.py::test_export_null_status.

Fixes #456
```

### 6.3 性能优化
```
perf(order): optimize order list query with composite index

Before: P99 latency 1.2s (full table scan on 500k rows)
After: P99 latency 45ms (index seek)

Changes:
- Add composite index (shop_id, status, created_at)
- Refactor query to use index seek instead of scan
- Update query plan verification in CI

Performance impact:
- P50: 120ms → 15ms
- P99: 1200ms → 45ms
- Rows examined: 500k → 50

Closes #789
```

### 6.4 重构
```
refactor(order): extract export logic to dedicated service

Motivation: Export logic was mixed in controller, hard to test and reuse.
Extract to OrderExportService with clear interface.

Changes:
- New: OrderExportService (CSV/Excel generation, job management)
- New: ExportJob entity (progress tracking, result storage)
- Modified: OrderController -> delegate to service
- Tests: Add service unit tests, update controller tests

Ref: #789 (performance optimization depends on this)
```

### 6.5 依赖升级
```
chore(deps): upgrade ruff from 0.3.0 to 0.4.0

Changes:
- Update pyproject.toml ruff version
- Fix new lint warnings: RUF012 (mutable default argument)
- Update pre-commit hook rev

Test: CI passes, no functional changes.

Ref: https://github.com/astral-sh/ruff/releases/tag/0.4.0
```

### 6.6 破坏性变更
```
feat(api): unify error response format across all endpoints

BREAKING CHANGE: Error response structure standardized.

Old format:
{ "error": "message", "code": 400 }

New format (RFC 7807 Problem Details):
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Invalid input",
  "instance": "/api/v1/orders",
  "errors": { "field": ["message"] }
}

Migration:
1. Update all clients to parse new structure
2. Update error handling middleware
3. Old format supported until v2.0.0 (deprecation header)

Migration guide: docs/migration/v2.0-error-format.md
Closes #999
```

### 6.7 Revert 回滚
```
revert: feat(order): add bulk export API

This reverts commit abc1234 (PR #123).

Reason: Export API causes memory leak under high concurrency.
Root cause: Job results not cleaned up, Redis OOM.

Plan: Fix memory leak in separate PR, then re-apply.
Ref: #1001 (tracking memory leak fix)

Closes #1000
```

---

## 7. 规范执行与工具链

### 7.1 提交信息校验
```yaml
# .github/workflows/commit-lint.yml
name: Commit Lint
on: [push, pull_request]
jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@v5
        with:
          configFile: .commitlintrc.yaml
```

### 7.2 commitlint 配置
```yaml
# .commitlintrc.yaml
extends: ['@commitlint/config-conventional']
rules:
  type-enum:
    - 2
    - always
    - [feat, fix, perf, refactor, style, docs, test, chore, build, ci, security, release, revert]
  type-case:
    - 2
    - always
    - lower-case
  type-empty:
    - 2
    - never
  scope-case:
    - 2
    - always
    - lower-case
  subject-case:
    - 2
    - never
    - [sentence-case, start-case, pascal-case, upper-case]
  subject-empty:
    - 2
    - never
  subject-full-stop:
    - 2
    - never
    - .
  header-max-length:
    - 2
    - always
    - 72
  body-max-line-length:
    - 2
    - always
    - 100
  footer-leading-blank:
    - 1
    - always
```

### 7.3 Git Hooks 集成
```bash
# .git/hooks/commit-msg (由 commitlint 安装)
#!/bin/sh
npx --no-install commitlint --edit "$1"

# 或使用 husky + commitlint
# npm install --save-dev husky @commitlint/cli @commitlint/config-conventional
# npx husky install
# npx husky add .husky/commit-msg 'npx --no-install commitlint --edit "$1"'
```

### 7.4 Git Commit Template
```bash
# ~/.gitmessage.txt (配置 git config commit.template ~/.gitmessage.txt)
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
# Closes #ISSUE
# BREAKING CHANGE: ...
# Co-authored-by: Name <email>
#
# Type: feat|fix|perf|refactor|style|docs|test|chore|build|ci|security|release|revert
# Scope: order|product|auth|user|compliance|alert|sync|api|ui|infra|deps|release|security
# Subject: <imperative, lower case, no period, <50 chars>
```

---

## 8. 常见错误与修正

| 常见错误 | 问题 | 修正示例 |
|----------|------|----------|
| `Fixed bug in order export` | 类型错误、主语错误、无 Scope | `fix(order): handle null status in export` |
| `Add new feature for export` | 类型模糊、无 Scope、主语错误 | `feat(order): add bulk export API` |
| `Update code` | 无信息量、无类型/范围 | `refactor(order): extract export logic to service` |
| `Fix bug` | 无具体信息、无关联 Issue | `fix(order): handle null status in export (Fixes #456)` |
| `WIP: working on export` | `wip` 类型进入主分支历史 | 仅限本地/Draft PR，合并前必须重写 |
| `Merge branch 'develop'` | 合并提交污染历史 (非 --no-ff) | 使用 Squash Merge 或 --no-ff 显式合并 |
| `fix: add export` | Scope 缺失、动词错误 | `feat(order): add bulk export API` |
| `feat: add export.` | Subject 末尾有句号 | `feat(order): add bulk export API` |

---

## 9. 版本发布自动化

### 9.1 语义化版本映射
| Commit Type | 版本号变化 | 示例 |
|-------------|-----------|------|
| `feat` | `MINOR` +1 | `v1.2.0` → `v1.3.0` |
| `fix` / `perf` / `security` | `PATCH` +1 | `v1.2.0` → `v1.2.1` |
| `BREAKING CHANGE` (footer) | `MAJOR` +1 | `v1.2.0` → `v2.0.0` |
| `release` | 显式指定 | `release: v2.0.0` |
| 其他 (`docs`/`style`/`chore`/`refactor`/`test`/`build`/`ci`) | **无变化** | - |

### 9.2 自动化发布流水线
```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Generate changelog
        uses: conventional-changelog/conventional-changelog-action@v4
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          version-file: package.json
          tag-prefix: 'v'
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

---

## 10. 团队培训与执行

### 10.1 培训要点
| 培训内容 | 目标受众 | 频次 |
|----------|----------|------|
| Commit Message 规范实操 | 全员开发 | 入职培训 + 季度复训 |
| Conventional Commits 语义化版本原理 | Tech Lead / 核心开发 | 半年 |
| Commitlint 配置与 CI 集成 | DevOps / Tech Lead | 按需 |
| 常见错误案例分析 | 全员 | 月度 Code Review 复盘 |

### 10.2 执行考核
| 指标 | 目标 | 统计方式 |
|------|------|----------|
| 提交规范通过率 | 100% (CI 拦截) | CI 统计 |
| 规范违规率 (人工 Review 发现) | < 5% | Code Review 统计 |
| 规范培训覆盖率 | 100% 新入职 | HR 记录 |
| 规范文档更新及时性 | 版本发布前同步 | 文档版本对比 |

---

## 11. 附录

### 11.1 快速参考卡
```
# 类型速查
feat     → MINOR    新功能
fix      → PATCH    修复Bug
perf     → PATCH    性能优化
refactor → (无)     重构
docs     → 无       文档
test     → 无       测试
chore    → 无       杂项
revert   → 视情况   回滚

# Scope 常用
order | product | auth | user | compliance | alert | sync | api | ui | infra | deps | security

# Subject 口诀
祈使语气、首字母小写、无句点、<50字符

# Footer 关键字
Closes #123 | BREAKING CHANGE: ... | Co-authored-by: Name <email>
```

### 11.2 常用别名
```bash
# ~/.gitconfig
[alias]
  cm = commit -m
  cam = commit -am
  amend = commit --amend --no-edit
  amendm = commit --amend -m
  fixup = commit --fixup
  squash = commit --squash
  log1 = log --oneline --graph --decorate -20
  lg = log --oneline --graph --decorate --all
  fix = "!f() { git commit -m \"fix($1): $2\"; }; f"
  feat = "!f() { git commit -m \"feat($1): $2\"; }; f"
  perf = "!f() { git commit -m \"perf($1): $2\"; }; f"
```

---

*文档版本: v1.0.0 | 维护者: Tech Lead | 更新周期: 季度 | 遵循标准: Conventional Commits 1.0.0*
EOF