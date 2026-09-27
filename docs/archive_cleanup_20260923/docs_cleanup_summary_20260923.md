# docs 目录整合与清理摘要 - 第二阶段

日期：2026-09-23
阶段：进一步整合统一

## 本次操作
1. 模板文件归档
   - README.template.md、CHANGELOG.template.md 移至 `archive_cleanup_20260923/legacy_docs/root_files/`
   - 根目录移除模板文件

2. API 规范合并
   - 原 4 份文档归档：`API-SPEC.md` `API_DOC.md` `EXTERNAL-API-SPEC.md` `INTERNAL-API-SPEC.md` → `archive_cleanup_20260923/legacy_docs/api_old/`
   - 生成统一规范 `docs/api/API_SPEC.md`，涵盖内部 API 概览/详细、外部 API 概览/详细、认证、错误码
   - 历史版本保留可追溯

3. 根目录冗余清理
   - `PROJECT_TECH_DOCS.md` 归档至 `legacy_docs/root_files/`
   - `INDEX.md` 部署项更新为 `NGINX_WLJKDOC.md`，移除对已归档文件的引用
   - 保留核心文档：`ARCHITECTURE.md` `DESIGN.md` `FRONTEND_DESIGN.md` `PROJECT_ANALYSIS.md` `PROJECT_CHARTER.md` `REQUIREMENTS.md` `ISSUE_ANALYSIS.md` `CHANGELOG.md` `QUALITY_PLAN.md` `RISK_REGISTER.md` `COMMUNICATION_PLAN.md` `CONTRIBUTING.md` `TEST_STRATEGY.md` `SECURITY_HARDENING.md` `RUNBOOK.md` `INCIDENTS.md` `permission.md` `NGINX_WLJKDOC.md`

## 当前结构
docs/
- api/API_SPEC.md [统一]
- ARCHITECTURE.md DESIGN.md FRONTEND_DESIGN.md
- PROJECT_ANALYSIS.md PROJECT_CHARTER.md REQUIREMENTS.md ISSUE_ANALYSIS.md
- CHANGELOG.md QUALITY_PLAN.md RISK_REGISTER.md COMMUNICATION_PLAN.md CONTRIBUTING.md TEST_STRATEGY.md
- SECURITY_HARDENING.md RUNBOOK.md INCIDENTS.md permission.md NGINX_WLJKDOC.md
- INDEX.md MASTER_INDEX.md README.md
- archive/ archive_cleanup_20260923/

## 建议
- 新增文档直接写入根目录或 api/
- 废弃文档一律归档至 archive_cleanup_20260923/legacy_docs/
- 定期更新 INDEX.md 与 MASTER_INDEX.md
