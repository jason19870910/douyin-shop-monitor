---
title: 贡献指南
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: Tech Lead
reviewers: ['资深工程师']
approvers: ['Tech Lead']
classification: Public
doc_id: DOC-DEV-001
tags: ['开发', '贡献指南']
related_docs: []
changelog: |
  v1.0 (2026-09-26): 初版创建 - Tech Lead
---
# 贡献指南

感谢关注 DouDian Monitor 项目！

## 开发流程

1. Fork 本仓库
2. 克隆到本地：
   ```bash
   git clone https://github.com/yourusername/doudian_monitor.git
   cd doudian_monitor
   ```
3. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows
   pip install -r requirements-dev.txt
   ```
4. 配置 pre-commit hooks：
   ```bash
   pre-commit install
   ```
5. 创建特性分支：
   ```bash
   git checkout -b feature/amazing-feature
   ```
6. 修改代码，确保：
   - 通过 `black` 格式化
   - 通过 `flake8` 检查
   - 通过 `mypy` 类型检查（类型注解）
   - 通过 `pytest` 测试
7. 提交更改：
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```
8. 推送分支：
   ```bash
   git push origin feature/amazing-feature
   ```
9. 创建 Pull Request，描述变更内容

## 代码规范

- Python 类型注解（PEP 484）
- 遵循 PEP 8（black 自动格式化）
- 函数/变量命名清晰，添加 docstring
- 单元测试覆盖率达 80%+

## 提交信息格式

```
type: short description

optional longer description

Types:
- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes (no code change)
- refactor: code restructuring
- test: adding or updating tests
- chore: maintenance tasks
```

示例：
```
feat: add product list pagination support

- Support page and page_size query parameters
- Add total count in response headers
- Update frontend to use paginated API
```

## CI/CD

所有 PR 和 Push 都会触发 GitHub Actions：
- 测试（Python 3.11, 3.12）
- 代码检查（flake8, black, mypy）
- Docker 构建
- 安全扫描（Trivy）

确保 CI 状态全部通过才能合并。

## 发布流程

1. 更新版本号（app.py 或 config.py）
2. 更新 CHANGELOG.md
3. 创建 Git tag：
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```
4. GitHub Actions 自动构建并推送 Docker 镜像

## PR Review Checklist (代码审查清单)

### 🔒 安全性
- [ ] **无硬编码密钥**：API Key、Token、密码、Cookie 未提交到代码库（使用 `.env` / Secret Manager）
- [ ] **输入验证**：所有外部输入（查询参数、Body、Header）均有类型/格式/长度校验
- [ ] **SQL/命令注入防护**：使用参数化查询，避免字符串拼接 SQL/Shell 命令
- [ ] **敏感日志脱敏**：日志中不打印完整 Cookie、Token、手机号、身份证等 PII 信息
- [ ] **依赖安全**：新增依赖通过 `pip-audit` / `npm audit` 扫描，无 High/Critical 漏洞
- [ ] **权限最小化**：新增 API/数据库操作遵循最小权限原则

### ⚡ 性能
- [ ] **无 N+1 查询**：列表接口使用批量查询或 JOIN，避免循环中查询 DB/外部 API
- [ ] **合理缓存**：高频只读数据（配置、字典、统计）使用 Redis/内存缓存，设置 TTL
- [ ] **分页限制**：列表接口强制 `size ≤ 100`，防止全量导出内存溢出
- [ ] **异步处理**：耗时操作（外部 API 调用、文件生成、邮件发送）交由后台线程 / 内置调度器（schedule + threading）执行
- [ ] **连接池配置**：HTTP 客户端/Redis/DB 连接池大小匹配并发预期

### 🏷️ 类型与代码质量
- [ ] **类型注解完整**：公共函数/类/接口均有类型提示（Python: PEP 484 / TS: strict 模式）
- [ ] **无 `any` / `Any` 滥用**：仅在动态场景最小范围使用，并添加类型忽略注释说明理由
- [ ] **Mypy/Pyright 通过**：`mypy .` / `npx tsc --noEmit` 无报错
- [ ] **Lint 通过**：`flake8` / `eslint` 无警告（或已在配置中豁免并说明）
- [ ] **命名规范**：变量/函数/类遵循 PEP 8 / TypeScript Standard，语义清晰
- [ ] **Docstring/注释**：公共接口、复杂算法、业务规则有文档字符串或行内注释

### 🧪 测试
- [ ] **单测覆盖新增/变更逻辑**：核心分支 ≥ 90%，整体 ≥ 85%
- [ ] **边界场景覆盖**：空值、异常输入、极值、并发、幂等性
- [ ] **集成测试通过**：涉及外部依赖的变更补充集成测试
- [ ] **契约测试同步**：API 变更同步更新 OpenAPI 规范 / Pact 契约
- [ ] **E2E 核心路径**：关键用户旅程（登录、同步、告警配置）有 Playwright 用例

### 📚 文档同步
- [ ] **README/架构图更新**：架构变更、新增服务/端口/环境变量同步至 README、ARCHITECTURE.md
- [ ] **API 文档同步**：新增/变更接口同步更新 `INTERNAL-API-SPEC.md` / OpenAPI Spec
- [ ] **CHANGELOG 记录**：遵循 Conventional Commits，自动生成或手动补充
- [ ] **环境变量文档**：新增 `.env` 变量同步至 `.env.example` 并运行 `scripts/check_env.py`
- [ ] **运维文档**：部署/扩容/备份/证书轮换流程变更同步至 Runbook

### 🔄 向后兼容与迁移
- [ ] **API 兼容性**：不破坏现有字段/枚举/错误码；新增字段默认可选
- [ ] **数据库迁移**：如有 Schema 变更，提供向前/向后兼容的迁移脚本
- [ ] **配置迁移**：新增必填配置项提供默认值或启动校验友好报错
- [ ] **废弃标记**：即将移除的接口/字段添加 `Deprecated` 标注并给出迁移指引

---

## 问题反馈

- Bug: 请提供复现步骤、环境信息、日志
- Feature: 请描述使用场景和预期行为

谢谢！