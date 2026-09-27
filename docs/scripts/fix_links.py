#!/usr/bin/env python3
"""
修复文档内部链接路径
将相对路径链接修正为新目录结构下的正确路径
"""

import re
from pathlib import Path

# 链接映射：旧链接 -> 新链接
LINK_MAPPINGS = {
    # 根目录文件 -> 新位置
    'DESIGN.md': 'architecture/DESIGN.md',
    'ARCHITECTURE.md': 'architecture/ARCHITECTURE.md',
    'FRONTEND_DESIGN.md': 'architecture/FRONTEND_DESIGN.md',
    'CHANGELOG.md': 'reference/CHANGELOG.md',
    'PROJECT_CHARTER.md': 'governance/PROJECT_CHARTER.md',
    'REQUIREMENTS.md': 'requirements/REQUIREMENTS.md',
    'QUALITY_PLAN.md': 'quality/QUALITY_PLAN.md',
    'RISK_REGISTER.md': 'risk/RISK_REGISTER.md',
    'COMMUNICATION_PLAN.md': 'governance/COMMUNICATION_PLAN.md',
    'SECURITY_HARDENING.md': 'operations/SECURITY_HARDENING.md',
    'TEST_STRATEGY.md': 'quality/TEST_STRATEGY.md',
    'RUNBOOK.md': 'operations/RUNBOOK.md',
    'ISSUE_ANALYSIS.md': 'risk/ISSUE_ANALYSIS.md',
    'INTERNAL-API-SPEC.md': 'api/INTERNAL-API-SPEC.md',
    'EXTERNAL-API-SPEC.md': 'api/EXTERNAL-API-SPEC.md',
    'API-SPEC.md': 'api/API-SPEC.md',
    'API_DOC.md': 'api/API_DOC.md',
    'API_SPEC.md': 'api/API_SPEC.md',
    'CHANGE_REQUEST_TEMPLATE.md': 'risk/CHANGE_REQUEST_TEMPLATE.md',
    'INCIDENTS.md': 'risk/INCIDENTS.md',
    'THREAT_MODEL.md': 'risk/THREAT_MODEL.md',
    'DOCKER_FIX_REPORT.md': 'reference/DOCKER_FIX_REPORT.md',
    'GITHUB_SECRETS.md': 'reference/GITHUB_SECRETS.md',
    'EXAMPLES.md': 'reference/EXAMPLES.md',
    'AST.md': 'reference/AST.md',
    'MIGRATION_GUIDE.md': 'reference/MIGRATION_GUIDE.md',
    'permission.md': 'reference/permission.md',
    'README.template.md': 'reference/README.template.md',
    'CHANGELOG.template.md': 'reference/CHANGELOG.template.md',
    'CONTRIBUTING.md': 'development/CONTRIBUTING.md',
    
    # 旧目录结构引用
    '6_docs/PROJECT_CHARTER.md': 'governance/PROJECT_CHARTER.md',
    '6_docs/REQUIREMENTS.md': 'requirements/REQUIREMENTS.md',
    '6_docs/QUALITY_PLAN.md': 'quality/QUALITY_PLAN.md',
    '6_docs/RISK_REGISTER.md': 'risk/RISK_REGISTER.md',
    '6_docs/COMMUNICATION_PLAN.md': 'governance/COMMUNICATION_PLAN.md',
    '6_docs/SECURITY_HARDENING.md': 'operations/SECURITY_HARDENING.md',
    '6_docs/TEST_STRATEGY.md': 'quality/TEST_STRATEGY.md',
    '6_docs/RUNBOOK.md': 'operations/RUNBOOK.md',
    '6_docs/ISSUE_ANALYSIS.md': 'risk/ISSUE_ANALYSIS.md',
    '7_reference/AST.md': 'reference/AST.md',
    '7_reference/CHANGELOG.md': 'reference/CHANGELOG.md',
    '7_reference/CHANGELOG.template.md': 'reference/CHANGELOG.template.md',
    '7_reference/CHANGE_REQUEST_TEMPLATE.md': 'risk/CHANGE_REQUEST_TEMPLATE.md',
    '7_reference/CONTRIBUTING.md': 'development/CONTRIBUTING.md',
    '7_reference/DOCKER_FIX_REPORT.md': 'reference/DOCKER_FIX_REPORT.md',
    '7_reference/GITHUB_SECRETS.md': 'reference/GITHUB_SECRETS.md',
    '7_reference/EXAMPLES.md': 'reference/EXAMPLES.md',
    '7_reference/MIGRATION_GUIDE.md': 'reference/MIGRATION_GUIDE.md',
    '7_reference/README.template.md': 'reference/README.template.md',
    '4_guides/COMMUNICATION_PLAN.md': 'governance/COMMUNICATION_PLAN.md',
    '4_guides/PERMISSION.md': 'reference/permission.md',
    '4_guides/QUALITY_PLAN.md': 'quality/QUALITY_PLAN.md',
    '4_guides/RISK_REGISTER.md': 'risk/RISK_REGISTER.md',
    '4_guides/TEST_STRATEGY.md': 'quality/TEST_STRATEGY.md',
    '3_deployment/DEPLOY_GUIDE.md': 'operations/DEPLOY_GUIDE.md',
    '3_deployment/RUNBOOK.md': 'operations/RUNBOOK.md',
    '3_deployment/SECURITY_HARDENING.md': 'operations/SECURITY_HARDENING.md',
    '2_api/api-reference.md': 'api/API_SPEC.md',
    '2_api/API_DOCUMENTATION.md': 'api/API_DOC.md',
    '1_architecture/ARCHITECTURE.md': 'architecture/ARCHITECTURE.md',
    '1_architecture/DESIGN.md': 'architecture/DESIGN.md',
    '1_architecture/FRONTEND_DESIGN.md': 'architecture/FRONTEND_DESIGN.md',
    '0_overview/INDEX.md': 'INDEX.md',
    '0_overview/README.md': 'README.md',
    '5_testing/TEST_PLAN.md': 'quality/TEST_PLAN.md',
    '5_testing/TEST_STRATEGY.md': 'quality/TEST_STRATEGY.md',
    
    # GitHub 模板
    '.github/ISSUE_TEMPLATE/change-request.md': '.github/ISSUE_TEMPLATE/change-request.md',
    '.github/ISSUE_TEMPLATE/emergency-change.md': '.github/ISSUE_TEMPLATE/emergency-change.md',
    '.github/ISSUE_TEMPLATE/post-implementation-review.md': '.github/ISSUE_TEMPLATE/post-implementation-review.md',
}

# 需要处理的文件
TARGET_FILES = [
    'README.md',
    'governance/PROJECT_CHARTER.md',
    'governance/COMMUNICATION_PLAN.md',
    'requirements/REQUIREMENTS.md',
    'architecture/ARCHITECTURE.md',
    'architecture/DESIGN.md',
    'architecture/FRONTEND_DESIGN.md',
    'api/INTERNAL-API-SPEC.md',
    'api/EXTERNAL-API-SPEC.md',
    'api/API_SPEC.md',
    'api/API_DOC.md',
    'api/API-SPEC.md',
    'operations/RUNBOOK.md',
    'operations/SECURITY_HARDENING.md',
    'quality/TEST_STRATEGY.md',
    'quality/QUALITY_PLAN.md',
    'risk/RISK_REGISTER.md',
    'risk/CHANGE_REQUEST_TEMPLATE.md',
    'risk/INCIDENTS.md',
    'risk/ISSUE_ANALYSIS.md',
    'development/CONTRIBUTING.md',
    'reference/CHANGELOG.md',
    'reference/CHANGELOG.template.md',
    'reference/AST.md',
    'reference/DOCKER_FIX_REPORT.md',
    'reference/EXAMPLES.md',
    'reference/GITHUB_SECRETS.md',
    'reference/MIGRATION_GUIDE.md',
    'reference/permission.md',
]

# 相对路径修正：从特定目录出发的相对链接
RELATIVE_FIXES = {
    'governance/COMMUNICATION_PLAN.md': {
        'risk/RISK_REGISTER.md': '../risk/RISK_REGISTER.md',
        'operations/RUNBOOK.md': '../operations/RUNBOOK.md',
        'quality/QUALITY_PLAN.md': '../quality/QUALITY_PLAN.md',
        'architecture/ARCHITECTURE.md': '../architecture/ARCHITECTURE.md',
        'architecture/DESIGN.md': '../architecture/DESIGN.md',
        'RISK_REGISTER.md': '../risk/RISK_REGISTER.md',
        'RUNBOOK.md': '../operations/RUNBOOK.md',
        'QUALITY_PLAN.md': '../quality/QUALITY_PLAN.md',
        'ARCHITECTURE.md': '../architecture/ARCHITECTURE.md',
        'DESIGN.md': '../architecture/DESIGN.md',
    },
    'risk/CHANGE_REQUEST_TEMPLATE.md': {
        'governance/PROJECT_CHARTER.md': '../governance/PROJECT_CHARTER.md',
        'governance/COMMUNICATION_PLAN.md': '../governance/COMMUNICATION_PLAN.md',
        'risk/RISK_REGISTER.md': '../risk/RISK_REGISTER.md',
        'PROJECT_CHARTER.md': '../governance/PROJECT_CHARTER.md',
        'COMMUNICATION_PLAN.md': '../governance/COMMUNICATION_PLAN.md',
        'RISK_REGISTER.md': '../risk/RISK_REGISTER.md',
        '.github/ISSUE_TEMPLATE/change-request.md': '../../.github/ISSUE_TEMPLATE/change-request.md',
        '.github/ISSUE_TEMPLATE/emergency-change.md': '../../.github/ISSUE_TEMPLATE/emergency-change.md',
        '.github/ISSUE_TEMPLATE/post-implementation-review.md': '../../.github/ISSUE_TEMPLATE/post-implementation-review.md',
    },
    'README.md': {
        '.env.example': '../.env.example',  # 这个文件不在 docs 里，标记为外部引用
        '../src/backend/tasks.py': '../../src/backend/tasks.py',  # 源码引用
    },
}

def fix_links_in_file(filepath: Path, docs_root: Path) -> int:
    """修复单个文件中的链接"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"  ❌ 编码错误: {filepath}")
        return 0
    
    original_content = content
    fixed_count = 0
    rel_path = filepath.relative_to(docs_root)
    rel_path_str = str(rel_path)
    
    # 获取当前文件的相对路径修正规则
    relative_fixes = RELATIVE_FIXES.get(rel_path_str, {})
    
    # 计算当前文件相对于 docs 根目录的深度
    current_depth = len(rel_path.parents) - 1  # 减去 docs 根目录
    
    # 匹配 [text](link) 格式的链接
    def replace_link(match):
        nonlocal fixed_count
        text = match.group(1)
        link = match.group(2)
        
        # 跳过外部链接、锚点链接、mailto
        if link.startswith('http://') or link.startswith('https://') or link.startswith('mailto:') or link.startswith('#'):
            return match.group(0)
        
        # 1. 优先使用当前文件的相对路径修正
        if link in relative_fixes:
            new_link = relative_fixes[link]
            fixed_count += 1
            print(f"    {link} -> {new_link} (relative)")
            return f'[{text}]({new_link})'
        
        # 2. 使用全局映射（针对无路径前缀的简单文件名）
        if link in LINK_MAPPINGS:
            # 计算从当前文件到目标文件的相对路径
            target_path = LINK_MAPPINGS[link]
            # 如果当前文件在根目录，直接使用目标路径
            if current_depth == 0:
                new_link = target_path
            else:
                # 需要添加 ../ 前缀
                new_link = '../' * current_depth + target_path
            fixed_count += 1
            print(f"    {link} -> {new_link}")
            return f'[{text}]({new_link})'
        
        # 3. 处理已带路径前缀的链接（如 risk/RISK_REGISTER.md）
        # 检查是否是已知的目标路径但相对于当前文件位置不对
        for simple_name, target_path in LINK_MAPPINGS.items():
            # 如果链接以 target_path 结尾，但不是正确的相对路径
            if link.endswith(target_path) and link != target_path:
                # 计算正确的相对路径
                if current_depth == 0:
                    new_link = target_path
                else:
                    new_link = '../' * current_depth + target_path
                if link != new_link:
                    fixed_count += 1
                    print(f"    {link} -> {new_link} (fix relative)")
                    return f'[{text}]({new_link})'
        
        # 4. 处理 ../ 相对路径
        if link.startswith('../'):
            # 简单处理：去掉 ../ 尝试映射
            simple_link = link.replace('../', '')
            if simple_link in LINK_MAPPINGS:
                target_path = LINK_MAPPINGS[simple_link]
                new_link = '../' * (current_depth + 1) + target_path
                fixed_count += 1
                print(f"    {link} -> {new_link}")
                return f'[{text}]({new_link})'
        
        # 5. 处理 .env.example 和源码引用 - 标记为外部引用不修复
        if link in ['.env.example', '../src/backend/tasks.py']:
            # 这些是合理的外部引用，不修复
            return match.group(0)
        
        return match.group(0)
    
    # 替换链接
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, content)
    
    # 处理裸链接（不在 [] 中的 URL）
    # 这里不处理，因为容易误伤
    
    if content != original_content:
        filepath.write_text(content, encoding='utf-8')
        print(f"  ✅ 修复 {fixed_count} 个链接: {filepath}")
    else:
        print(f"  ⏭️ 无需修复: {filepath}")
    
    return fixed_count

def main():
    docs_root = Path(__file__).parent.parent
    total_fixed = 0
    
    print("开始修复内部链接...")
    print("=" * 60)
    
    for rel_path in TARGET_FILES:
        filepath = docs_root / rel_path
        if filepath.exists():
            total_fixed += fix_links_in_file(filepath, docs_root)
        else:
            print(f"  ⚠️ 文件不存在: {rel_path}")
    
    print("=" * 60)
    print(f"完成: 共修复 {total_fixed} 个链接")

if __name__ == '__main__':
    main()
EOF