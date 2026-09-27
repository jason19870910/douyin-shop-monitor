# 抖音电商数据监控平台 - 文档总索引

> 精简后的专业文档体系，仅保留真实存在的文档。按功能域组织，覆盖全生命周期。

---

## API 文档
- [api/INTERNAL-API-SPEC.md](./api/INTERNAL-API-SPEC.md) – 内部 RESTful API 详细规范
- [api/EXTERNAL-API-SPEC.md](./api/EXTERNAL-API-SPEC.md) – 外部抖音电商后台 API 详细规范
- [api/API-SPEC.md](./api/API-SPEC.md) – API 规范概览（内部转发 + 外部接口）
- [api/API_DOC.md](./api/API_DOC.md) – 后端 API 文档（端点、参数、示例）

## 治理文档
- [PROJECT_CHARTER.md](./PROJECT_CHARTER.md) – 项目章程
- [REQUIREMENTS.md](./REQUIREMENTS.md) – 需求规格
- [ISSUE_ANALYSIS.md](./ISSUE_ANALYSIS.md) – 问题分析报告
- [QUALITY_PLAN.md](./QUALITY_PLAN.md) – 质量计划
- [RISK_REGISTER.md](./RISK_REGISTER.md) – 风险登记册

## 其他现有文档
- [README.md](./README.md) – 项目总览
- [CHANGELOG.md](./CHANGELOG.md) – 变更日志
- [CONTRIBUTING.md](./CONTRIBUTING.md) – 贡献指南
- [PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md) – 项目分析
- [FRONTEND_DESIGN.md](./FRONTEND_DESIGN.md) – 前端设计文档
- [DESIGN.md](./DESIGN.md) – 系统设计文档
- [ARCHITECTURE.md](./ARCHITECTURE.md) – 架构文档

## 归档
- [archive/](./archive/) – 已废弃或历史版本文档

---

### 维护规范
1. **新增文档** → 放入对应类别目录（`api/`），或置于 docs 根目录，并在本索引追加条目。
2. **版本变更** → 更新文档头部版本号、更新日期、作者。
3. **废弃文档** → 移动到 `archive_cleanup_20260923/legacy_docs/`，并在本索引标注“已归档”。
4. **链接检查** → CI 中运行 `markdown-link-check docs/**/*.md`。

*最后更新：2026-09-21*  
*维护者：项目核心团队*