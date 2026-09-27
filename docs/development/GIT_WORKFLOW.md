---
title: Git 工作流规范
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: Tech Lead
reviewers: [资深工程师, 架构师, DevOps Lead]
approvers: [Tech Lead]
classification: Internal
doc_id: DOC-DEV-002
tags: [开发, Git, 工作流, 分支策略, CI/CD, 版本管理]
related_docs: [DOC-DEV-001, DOC-DEV-003, DOC-DEV-005, DOC-QA-004]
changelog: |
  v1.0.0 (2026-09-26): 初版创建 - Tech Lead
---

# Git 工作流规范

## 1. 概述
本文档定义抖音电商数据监控平台的 Git 工作流，基于 **GitHub Flow** 与 **GitFlow** 的混合模式，适应持续交付与定期发布的双重需求。

---

## 2. 分支策略

### 2.1 分支层级
```
                    ┌─────────────────────┐
                    │     main (保护)      │ ◄── 生产环境镜像，仅接受 PR 合并
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ release/v1.2│  │ release/v1.3│  │ release/v1.4│ ◄── 发布分支，仅修复发布相关 Bug
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │     develop (保护)   │ ◄── 集成分支，日常开发合并目标
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ feature/xxx │  │ bugfix/xxx  │  │ hotfix/xxx  │ ◄── 短生命周期工作分支
       └─────────────┘  └─────────────┘  └─────────────┘
```

### 2.2 分支命名规范
| 分支类型 | 命名模式 | 示例 | 生命周期 | 合并目标 |
|----------|----------|------|----------|----------|
| 主分支 | `main` | `main` | 永久 | - |
| 集成分支 | `develop` | `develop` | 永久 | `main` (发布时) |
| 发布分支 | `release/v{MAJOR}.{MINOR}` | `release/v1.2` | 发布周期 | `main`、`develop` |
| 功能分支 | `feature/{issue-id}-{short-desc}` | `feature/123-add-export-api` | 天~周 | `develop` |
| 缺陷分支 | `bugfix/{issue-id}-{short-desc}` | `bugfix/456-fix-export-null` | 天 | `develop` |
| 紧急修复 | `hotfix/{issue-id}-{short-desc}` | `hotfix/789-fix-payment-crash` | 小时~天 | `main`、`develop`、`release/*` |
| 实验分支 | `experiment/{desc}` | `experiment/new-cache-strategy` | 短期 | `develop` 或废弃 |

### 2.3 分支保护规则
| 分支 | 保护规则 | 说明 |
|------|----------|------|
| `main` | ✅ Required PR review (2) ✅ Status checks ✅ Linear history ✅ No force push ✅ No deletion ✅ Signed commits | 生产镜像，最高保护 |
| `develop` | ✅ Required PR review (1) ✅ Status checks ✅ No force push ✅ No deletion | 集成分支，需 Code Review |
| `release/*` | ✅ Required PR review (1) ✅ Status checks ✅ No force push | 发布分支，仅修复发布 Bug |
| `feature/*` `bugfix/*` | ❌ 无强制保护，建议开启 Status checks | 短生命周期，由作者自管 |
| `hotfix/*` | ✅ Required PR review (1) ✅ Status checks | 紧急修复，需快速 Review |

---

## 3. 工作流程

### 3.1 日常功能开发流程
```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/123-add-export-api

# 2. 本地开发，遵循提交规范
git add .
git commit -m "feat(export): add bulk export API
Closes #123"

# 3. 定期同步 develop (避免大冲突)
git fetch origin
git rebase origin/develop

# 4. 推送并创建 PR
git push origin feature/123-add-export-api
# GitHub/GitLab 创建 PR: feature/123-add-export-api → develop

# 5. Code Review 通过后，Squash and Merge
# 删除远程分支，本地清理
git checkout develop
git pull origin develop
git branch -d feature/123-add-export-api
```

### 3.2 缺陷修复流程
```bash
# 1. 从 develop 创建 bugfix 分支
git checkout develop
git pull origin develop
git checkout -b bugfix/456-fix-export-null

# 2. 修复并编写回归测试
git commit -m "fix(export): handle null status in bulk export
Root cause: status field not validated before CSV writer
Test: add null status test case in test_export.py
Fixes #456"

# 3. PR → develop，Review 通过后 Merge
```

### 3.3 紧急热修复流程
```bash
# 场景: 生产环境 P0 故障，需立即修复
# 1. 从 main 创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/789-fix-payment-crash

# 2. 修复、测试、构建验证
git commit -m "fix(payment): prevent null pointer in callback handler
Root cause: callback data missing required field
Test: add mock callback test with missing fields
Fixes #789"

# 4. 同时向 main 和 develop 发起 PR (或 cherry-pick)
# PR 1: hotfix/789-fix-payment-crash → main (优先部署)
# PR 2: hotfix/789-fix-payment-crash → develop (同步修复)

# 5. 如有活跃 release 分支，同步修复
git checkout release/v1.2
git cherry-pick <hotfix-commit-hash>
git push origin release/v1.2
```

### 3.4 发布流程
```bash
# 1. 发布准备: 从 develop 创建 release 分支
git checkout develop
git pull origin develop
git checkout -b release/v1.2
# 版本号更新、CHANGELOG 生成、版本号提交
git commit -m "chore(release): bump version to v1.2.0
Update CHANGELOG.md
Bump package.json version"

# 2. 发布分支仅接受 bugfix，不接受新功能
git checkout -b bugfix/release-v1.2-fix-export
# 修复发布阻断性 Bug...
git push origin bugfix/release-v1.2-fix-export
# PR → release/v1.2

# 3. 发布验证通过后，合并到 main 并打 Tag
git checkout main
git pull origin main
git merge --no-ff release/v1.2 -m "chore(release): merge release v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 4. 同步回 develop
git checkout develop
git merge --no-ff release/v1.2 -m "chore(release): sync release v1.2.0 to develop"
git push origin develop

# 5. 清理 release 分支 (可选保留)
git branch -d release/v1.2
git push origin --delete release/v1.2
```

---

## 4. 提交规范
详见 `COMMIT_CONVENTION.md` 和 `CODING_STANDARDS.md`

---

## 5. PR 流程规范

### 5.1 PR 创建检查清单
- [ ] 分支命名符合规范
- [ ] Commit Message 符合 Conventional Commits
- [ ] 代码通过 Lint、Type Check、Test
- [ ] 单元测试覆盖新增/修改逻辑 (核心模块 ≥ 80%)
- [ ] 更新相关文档 (README/CHANGELOG/API 文档/注释)
- [ ] 无明显性能退化、安全隐患
- [ ] PR 描述清晰：What/Why/How、关联 Issue、测试步骤、截图/录屏

### 5.2 PR 模板
```markdown
## 变更类型
- [ ] feat: 新功能
- [ ] fix: Bug 修复
- [ ] refactor: 重构
- [ ] perf: 性能优化
- [ ] docs: 文档更新
- [ ] test: 测试相关
- [ ] chore: 构建/工具/依赖

## 变更描述
**What**: 简述做了什么
**Why**: 为什么要做 (关联 Issue #123)
**How**: 核心实现思路、关键设计决策

## 变更影响
- 影响模块: [order, product, auth...]
- 破坏性变更: [无 / 有，详见下方]
- 数据库变更: [无 / 有迁移脚本]
- 配置变更: [无 / 新增环境变量 XXX]

## 测试验证
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动验证步骤:
  1. 登录系统
  2. 进入订单导出页
  3. 点击导出，验证 CSV 格式正确
- [ ] 性能测试: [无 / 通过基线对比]

## 破坏性变更 (如有)
- API 变更: `/api/v1/orders/export` 响应结构调整
- 迁移指南: 见 `docs/migration/v1.2-export-api.md`
- 废弃时间表: v1.3 移除旧字段

## 相关链接
- Issue: #123
- 设计文档: https://wiki.xxx.com/design/export-api
- 部署清单: https://wiki.xxx.com/deploy/checklist
```

### 5.3 Review 规则
| 场景 | 最少 Reviewer | 要求 |
|------|--------------|------|
| 普通功能/修复 | 1 | 代码质量、测试、文档 |
| 核心模块/架构变更 | 2 | 包含 Tech Lead/架构师 |
| 安全/性能/数据库 Schema 变更 | 2 | 包含安全负责人/DBA |
| 紧急热修复 | 1 | 可事后补全详细 Review |

### 5.3 Merge 策略
| 分支合并 | 策略 | 说明 |
|----------|------|------|
| `feature/*` → `develop` | **Squash and Merge** | 保持历史整洁，单次提交 |
| `bugfix/*` → `develop` | **Squash and Merge** | 同理 |
| `hotfix/*` → `main` | **Squash and Merge** | 快速合并，保持 main 简洁 |
| `release/*` → `main` | **Merge Commit (--no-ff)** | 保留发布分支历史、便于回溯 |
| `release/*` → `develop` | **Merge Commit (--no-ff)** | 同步发布修复回 develop |

---

## 6. 版本发布规范

### 6.1 语义化版本
```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

MAJOR: 不兼容的 API 变更、重大架构调整
MINOR: 向后兼容的功能新增
PATCH: 向后兼容的 Bug 修复
PRERELEASE: alpha/beta/rc (如 v1.2.0-rc.1)
BUILD: Git Commit Hash (如 +abc1234)
```

### 6.2 发布节奏
| 发布类型 | 频率 | 分支 | 发布内容 |
|----------|------|------|----------|
| **主版本** | 半年/年 | `release/v{M+1}.0` | 重大架构、不兼容变更 |
| **次版本** | 月度/双周 | `release/v{M}.{m+1}` | 新功能、改进、兼容修复 |
| **补丁版本** | 周度/按需 | `release/v{M}.{m}.{p+1}` / `hotfix/*` | Bug 修复、安全补丁 |
| **预发布** | 按需 | `release/v{M}.{m}.{p}-rc.{n}` | 内测、灰度验证 |

### 6.3 发布清单
| 步骤 | 责任人 | 验收标准 |
|------|--------|----------|
| 版本号确认、CHANGELOG 生成 | PM/Tech Lead | 版本号语义正确、变更完整 |
| 发布分支创建、版本号提交 | Tech Lead | CI 通过、版本号一致 |
| 发布分支验证 (测试/预发布/灰度) | QA/运维/业务 | 核心流程通过、无 P0/P1 缺陷 |
| 生产部署、冒烟测试 | 运维/Tech Lead | 核心接口可用、监控正常 |
| Tag 打标、合并回 develop | Tech Lead | Tag 规范、合并无冲突 |
| 发布通知、文档归档 | PM | 发布公告、归档制品 |

---

## 7. 常用 Git 命令速查

### 7.1 分支操作
```bash
# 查看分支
git branch -a -vv          # 显示所有分支及上游
git log --oneline --graph --all -20  # 可视化历史

# 创建/切换
git switch -c feature/xxx  # 创建并切换 (Git 2.23+)
git switch develop         # 切换分支

# 同步上游
git fetch origin           # 仅获取
git pull --rebase          # 变基拉取 (功能分支推荐)
git pull                   # 合并拉取 (主分支推荐)

# 删除分支
git branch -d feature/xxx  # 本地删除 (已合并)
git branch -D feature/xxx  # 强制删除
git push origin --delete feature/xxx  # 远程删除
```

### 7.2 提交与重写
```bash
# 修正最近一次提交
git commit --amend --no-edit      # 仅修正内容，保留 message
git commit --amend -m "new msg"   # 修改 message

# 交互式变基 (整理提交历史)
git rebase -i HEAD~3              # 最近 3 个提交
# pick/squash/drop/edit/reword

# 撤销操作
git reset --soft HEAD~1           # 保留改动在暂存区
git reset --mixed HEAD~1          # 保留改动在工作区 (默认)
git reset --hard HEAD~1           # 彻底丢弃 (慎用!)

# 恢复丢失提交
git reflog                        # 查看操作历史
git checkout <commit-hash>        # 恢复到该提交
```

### 7.3 冲突解决
```bash
# 变基时冲突
git rebase origin/develop
# 冲突文件会标记 <<<<<<< ======= >>>>>>>
# 手动解决后
git add <resolved-files>
git rebase --continue

# 合并时冲突
git merge feature/xxx
# 解决后
git add <resolved-files>
git commit -m "resolve conflict: merge feature/xxx"
```

### 7.4 远程操作
```bash
# 设置上游
git push -u origin feature/xxx    # 首次推送设置上游

# 强制推送 (仅限个人分支、变基后)
git push --force-with-lease origin feature/xxx  # 更安全

# 标签操作
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
git push origin --tags            # 推送所有标签

# 清理远程已删除分支的本地跟踪
git fetch -p                      # prune
```

### 7.5 搜索与诊断
```bash
# 搜索代码
git grep "TODO" -- "*.py"         # 搜索特定模式
git log --all --grep="JIRA-123"   # 搜索提交信息
git log -p --follow -- <file>     # 文件完整修改历史

# 统计贡献
git shortlog -sn                  # 按提交数排序
git shortlog -sn --since="2026-01-01"

# 大文件查找
git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k3 -n | tail -10 | awk '{print $1}')"
```

---

## 8. Git Hooks 规范

### 8.1 客户端 Hooks (本地强制)
```bash
# .git/hooks/pre-commit (由 pre-commit 框架管理)
# 安装: pre-commit install

# .pre-commit-config.yaml
repos:
-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
    -   id: ruff
        args: [--fix, --exit-non-zero-on-fix]
    -   id: ruff-format

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
    -   id: mypy
        args: [--strict]

-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-json
    -   id: check-merge-conflict
    -   id: detect-private-key
    -   id: check-added-large-files
```

### 8.2 服务端 Hooks (CI/CD 强制)
- `pre-receive`: 拒绝未签名提交、拒绝未通过 CI 的提交
- `update`: 保护分支命名规范、提交 message 规范
- `post-receive`: 触发 CI/CD、通知系统

---

## 8. 常见问题与最佳实践

| 场景 | 推荐做法 | 避坑指南 |
|------|----------|----------|
| 长期功能分支 | 定期 `rebase develop`、小步提交、及时 PR | 避免大冲突、避免分支腐烂 |
| 多人协作同一功能 | 共享功能分支、约定 commit message 前缀 | 避免 force push 覆盖他人工作 |
| 代码审查发现大改动 | 拆分小 PR、或在 PR 中分多次 commit | 避免单次 PR 过大 (>500 行) |
| 生产热修复同步 develop | `cherry-pick` 或合并 hotfix 分支 | 避免遗漏同步导致回归 |
| 大文件误提交 | `git filter-repo` / BFG Repo-Cleaner 清理历史 | 预提交钩子拦截大文件 |
| 敏感信息泄露 | 立即轮换密钥、`git filter-repo` 清理、通知安全团队 | 预提交钩子检测密钥 |

---

## 9. 迁移与遗留分支清理

### 9.1 遗留分支识别
```bash
# 查找已合并的远程分支
git branch -r --merged main | grep -v "main\|develop\|release/" | xargs -n 1 git push origin --delete

# 查找超过 90 天无活动的分支
git for-each-ref --format='%(refname:short) %(committerdate:iso8601) %(authorname)' refs/remotes/origin | \
  awk '$2 < "'$(date -d '90 days ago' +%Y-%m-%d)'" {print $1}' | \
  xargs -n 1 git push origin --delete
```

### 9.2 归档策略
| 分支状态 | 处理方式 |
|----------|----------|
| 已合并、无活动 > 30 天 | 删除远程分支，本地可保留 |
| 未合并、无活动 > 90 天 | 确认废弃后删除，或转为 `archive/` 前缀 |
| 实验性/调研分支 | 前缀 `experiment/`，定期清理 |

---

*文档版本: v1.0.0 | 维护者: Tech Lead | 更新周期: 季度*
EOF