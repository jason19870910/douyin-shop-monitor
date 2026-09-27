#!/usr/bin/env python3
"""
为所有文档自动添加标准 Frontmatter
"""

import os
import re
from pathlib import Path
from datetime import datetime

# 文档配置映射
DOC_CONFIG = {
    'README.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-001',
        'title': '项目总览',
        'owner': 'PM',
        'reviewers': ['Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Public',
        'tags': ['概览', 'README'],
    },
    'governance/PROJECT_CHARTER.md': {
        'category': 'governance',
        'doc_id': 'DOC-GOV-001',
        'title': '项目章程',
        'owner': 'PM',
        'reviewers': ['Tech Lead', '架构师'],
        'approvers': ['执行发起人'],
        'classification': 'Internal',
        'tags': ['治理', '章程'],
    },
    'governance/COMMUNICATION_PLAN.md': {
        'category': 'governance',
        'doc_id': 'DOC-GOV-002',
        'title': '沟通计划',
        'owner': 'PM',
        'reviewers': ['Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Internal',
        'tags': ['治理', '沟通'],
    },
    'requirements/REQUIREMENTS.md': {
        'category': 'requirements',
        'doc_id': 'DOC-REQ-001',
        'title': '需求规格说明书',
        'owner': 'PM',
        'reviewers': ['业务分析师', 'Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Internal',
        'tags': ['需求', '规格'],
    },
    'architecture/ARCHITECTURE.md': {
        'category': 'architecture',
        'doc_id': 'DOC-TECH-001',
        'title': '系统架构总览',
        'owner': 'Tech Lead',
        'reviewers': ['架构师', '资深工程师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['架构', '总览'],
    },
    'architecture/DESIGN.md': {
        'category': 'architecture',
        'doc_id': 'DOC-TECH-002',
        'title': '详细设计文档',
        'owner': 'Tech Lead',
        'reviewers': ['架构师', '资深工程师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['架构', '设计'],
    },
    'architecture/FRONTEND_DESIGN.md': {
        'category': 'architecture',
        'doc_id': 'DOC-TECH-003',
        'title': '前端设计文档',
        'owner': 'Frontend Lead',
        'reviewers': ['Tech Lead', 'UI/UX 设计师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['架构', '前端', '设计'],
    },
    'api/INTERNAL-API-SPEC.md': {
        'category': 'api',
        'doc_id': 'DOC-API-001',
        'title': '内部 API 规范',
        'owner': 'Backend Lead',
        'reviewers': ['Frontend Lead', 'Tech Lead'],
        'approvers': ['Backend Lead', 'Frontend Lead'],
        'classification': 'Internal',
        'tags': ['API', '内部接口'],
    },
    'api/EXTERNAL-API-SPEC.md': {
        'category': 'api',
        'doc_id': 'DOC-API-002',
        'title': '外部 API 规范',
        'owner': 'Backend Lead',
        'reviewers': ['Frontend Lead', 'Tech Lead'],
        'approvers': ['Backend Lead', 'Frontend Lead'],
        'classification': 'Internal',
        'tags': ['API', '外部接口'],
    },
    'api/API_SPEC.md': {
        'category': 'api',
        'doc_id': 'DOC-API-003',
        'title': 'API 规范概览',
        'owner': 'Backend Lead',
        'reviewers': ['Frontend Lead'],
        'approvers': ['Backend Lead'],
        'classification': 'Internal',
        'tags': ['API', '概览'],
    },
    'api/API_DOC.md': {
        'category': 'api',
        'doc_id': 'DOC-API-004',
        'title': 'API 文档补充',
        'owner': 'Backend Lead',
        'reviewers': ['Frontend Lead'],
        'approvers': ['Backend Lead'],
        'classification': 'Internal',
        'tags': ['API', '文档'],
    },
    'operations/RUNBOOK.md': {
        'category': 'operations',
        'doc_id': 'DOC-OPS-001',
        'title': '运维手册',
        'owner': 'DevOps Lead',
        'reviewers': ['运维工程师', 'Tech Lead'],
        'approvers': ['DevOps Lead'],
        'classification': 'Confidential',
        'tags': ['运维', '手册'],
    },
    'operations/SECURITY_HARDENING.md': {
        'category': 'operations',
        'doc_id': 'DOC-OPS-002',
        'title': '安全加固指南',
        'owner': 'DevOps Lead',
        'reviewers': ['安全负责人', 'Tech Lead'],
        'approvers': ['DevOps Lead'],
        'classification': 'Confidential',
        'tags': ['运维', '安全'],
    },
    'quality/TEST_STRATEGY.md': {
        'category': 'quality',
        'doc_id': 'DOC-QA-001',
        'title': '测试策略',
        'owner': 'QA Lead',
        'reviewers': ['测试工程师', 'Tech Lead', 'PM'],
        'approvers': ['QA Lead'],
        'classification': 'Internal',
        'tags': ['质量', '测试', '策略'],
    },
    'quality/QUALITY_PLAN.md': {
        'category': 'quality',
        'doc_id': 'DOC-QA-002',
        'title': '质量计划',
        'owner': 'QA Lead',
        'reviewers': ['测试工程师', 'Tech Lead', 'PM'],
        'approvers': ['QA Lead'],
        'classification': 'Internal',
        'tags': ['质量', '计划'],
    },
    'risk/RISK_REGISTER.md': {
        'category': 'risk',
        'doc_id': 'DOC-RISK-001',
        'title': '风险登记册',
        'owner': 'PM',
        'reviewers': ['Tech Lead', '安全负责人', '业务方'],
        'approvers': ['PM'],
        'classification': 'Confidential',
        'tags': ['风险', '登记册'],
    },
    'risk/CHANGE_REQUEST_TEMPLATE.md': {
        'category': 'risk',
        'doc_id': 'DOC-RISK-002',
        'title': '变更请求模板',
        'owner': 'PM',
        'reviewers': ['Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Internal',
        'tags': ['风险', '变更', '模板'],
    },
    'risk/INCIDENTS.md': {
        'category': 'risk',
        'doc_id': 'DOC-RISK-003',
        'title': '事故记录',
        'owner': 'PM',
        'reviewers': ['DevOps Lead', 'Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Confidential',
        'tags': ['风险', '事故'],
    },
    'risk/ISSUE_ANALYSIS.md': {
        'category': 'risk',
        'doc_id': 'DOC-RISK-004',
        'title': '问题分析报告',
        'owner': 'PM',
        'reviewers': ['Tech Lead', '相关 Owner'],
        'approvers': ['PM'],
        'classification': 'Internal',
        'tags': ['风险', '问题分析'],
    },
    'development/CONTRIBUTING.md': {
        'category': 'development',
        'doc_id': 'DOC-DEV-001',
        'title': '贡献指南',
        'owner': 'Tech Lead',
        'reviewers': ['资深工程师'],
        'approvers': ['Tech Lead'],
        'classification': 'Public',
        'tags': ['开发', '贡献指南'],
    },
    'reference/CHANGELOG.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-002',
        'title': '版本变更记录',
        'owner': 'PM',
        'reviewers': ['Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Public',
        'tags': ['参考', '变更日志'],
    },
    'reference/CHANGELOG.template.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-003',
        'title': '变更日志模板',
        'owner': 'PM',
        'reviewers': ['Tech Lead'],
        'approvers': ['PM'],
        'classification': 'Public',
        'tags': ['参考', '模板'],
    },
    'reference/AST.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-004',
        'title': '抽象语法树参考',
        'owner': 'Tech Lead',
        'reviewers': ['资深工程师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['参考', 'AST'],
    },
    'reference/DOCKER_FIX_REPORT.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-005',
        'title': 'Docker 修复报告',
        'owner': 'DevOps Lead',
        'reviewers': ['Tech Lead'],
        'approvers': ['DevOps Lead'],
        'classification': 'Internal',
        'tags': ['参考', 'Docker', '故障'],
    },
    'reference/EXAMPLES.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-006',
        'title': '示例代码',
        'owner': 'Tech Lead',
        'reviewers': ['资深工程师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['参考', '示例'],
    },
    'reference/GITHUB_SECRETS.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-007',
        'title': 'GitHub Secrets 配置',
        'owner': 'DevOps Lead',
        'reviewers': ['Tech Lead'],
        'approvers': ['DevOps Lead'],
        'classification': 'Restricted',
        'tags': ['参考', 'Secrets', 'CI/CD'],
    },
    'reference/MIGRATION_GUIDE.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-008',
        'title': '迁移指南',
        'owner': 'Tech Lead',
        'reviewers': ['架构师'],
        'approvers': ['Tech Lead'],
        'classification': 'Internal',
        'tags': ['参考', '迁移'],
    },
    'reference/permission.md': {
        'category': 'reference',
        'doc_id': 'DOC-REF-009',
        'title': '权限矩阵',
        'owner': 'PM',
        'reviewers': ['Tech Lead', '安全负责人'],
        'approvers': ['PM'],
        'classification': 'Confidential',
        'tags': ['参考', '权限'],
    },
}

def add_frontmatter(filepath: Path, config: dict) -> bool:
    """为文件添加 Frontmatter"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"  ❌ 编码错误: {filepath}")
        return False
    
    # 检查是否已有 Frontmatter
    if content.startswith('---'):
        print(f"  ⏭️ 已有 Frontmatter: {filepath}")
        return True
    
    # 构建 Frontmatter
    today = datetime.now().strftime('%Y-%m-%d')
    
    fm_lines = [
        '---',
        f"title: {config['title']}",
        f"version: 1.0.0",
        f"status: Published",
        f"last_updated: {today}",
        f"owner: {config['owner']}",
        f"reviewers: {config['reviewers']}",
        f"approvers: {config['approvers']}",
        f"classification: {config['classification']}",
        f"doc_id: {config['doc_id']}",
        f"tags: {config['tags']}",
        f"related_docs: []",
        f"changelog: |",
        f"  v1.0 ({today}): 初版创建 - {config['owner']}",
        f"---",
        f"",
    ]
    
    fm_content = '\n'.join(fm_lines)
    new_content = fm_content + content
    
    try:
        filepath.write_text(new_content, encoding='utf-8')
        print(f"  ✅ 添加 Frontmatter: {filepath}")
        return True
    except Exception as e:
        print(f"  ❌ 写入失败: {filepath} - {e}")
        return False

def main():
    docs_root = Path(__file__).parent.parent
    success = 0
    failed = 0
    
    print("开始为文档添加 Frontmatter...")
    print("=" * 60)
    
    for rel_path, config in DOC_CONFIG.items():
        filepath = docs_root / rel_path
        if filepath.exists():
            if add_frontmatter(filepath, config):
                success += 1
            else:
                failed += 1
        else:
            print(f"  ⚠️ 文件不存在: {rel_path}")
    
    print("=" * 60)
    print(f"完成: 成功 {success} 个, 失败 {failed} 个")

if __name__ == '__main__':
    main()
EOF