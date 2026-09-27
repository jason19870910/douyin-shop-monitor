#!/usr/bin/env python3
"""
文档 Frontmatter 验证脚本
检查所有 Markdown 文档是否包含标准 Frontmatter 字段
"""

import os
import sys
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_FIELDS = [
    'title', 'version', 'status', 'last_updated', 'owner',
    'reviewers', 'approvers', 'classification', 'doc_id', 'tags', 'changelog'
]

VALID_STATUSES = ['Draft', 'UnderReview', 'Approved', 'Published', 'Archived', 'Obsolete', 'Proposed', 'Accepted', 'Superseded', 'Deprecated']
VALID_CLASSIFICATIONS = ['Public', 'Internal', 'Confidential', 'Restricted']

DOC_ID_PATTERNS = {
    'governance': r'^DOC-GOV-\d{3}$',
    'requirements': r'^DOC-REQ-\d{3}$',
    'architecture': r'^DOC-TECH-\d{3}$',
    'api': r'^DOC-API-\d{3}$',
    'operations': r'^DOC-OPS-\d{3}$',
    'quality': r'^DOC-QA-\d{3}$',
    'risk': r'^DOC-RISK-\d{3}$',
    'development': r'^DOC-DEV-\d{3}$',
    'reference': r'^DOC-REF-\d{3}$',
    'adr': r'^ADR-\d{3}$',
    'meeting': r'^MEETING-\d{3}$',
    'retro': r'^RETRO-\d{3}$',
}

def get_category_from_path(filepath: Path) -> str:
    """从文件路径推断文档类别"""
    parts = filepath.parts
    for part in parts:
        if part in DOC_ID_PATTERNS:
            return part
    return 'unknown'

def validate_frontmatter(filepath: Path) -> Tuple[bool, List[str]]:
    """验证单个文件的 Frontmatter"""
    errors = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        errors.append(f"编码错误: 无法以 UTF-8 读取")
        return False, errors
    
    # 提取 Frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        errors.append("缺少 Frontmatter (--- 分隔符)")
        return False, errors
    
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as e:
        errors.append(f"Frontmatter YAML 解析错误: {e}")
        return False, errors
    
    if not fm:
        errors.append("Frontmatter 为空")
        return False, errors
    
    # 检查必填字段
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"缺少必填字段: {field}")
        elif fm[field] is None or (isinstance(fm[field], str) and not fm[field].strip()):
            errors.append(f"字段为空: {field}")
    
    # 验证 status
    if 'status' in fm and fm['status'] not in VALID_STATUSES:
        errors.append(f"无效的 status: {fm['status']}, 可选值: {VALID_STATUSES}")
    
    # 验证 classification
    if 'classification' in fm and fm['classification'] not in VALID_CLASSIFICATIONS:
        errors.append(f"无效的 classification: {fm['classification']}, 可选值: {VALID_CLASSIFICATIONS}")
    
    # 验证 doc_id 格式
    if 'doc_id' in fm:
        category = get_category_from_path(filepath)
        pattern = DOC_ID_PATTERNS.get(category)
        if pattern and not re.match(pattern, fm['doc_id']):
            errors.append(f"doc_id 格式不符合规范: {fm['doc_id']}, 期望模式: {pattern}")
    
    # 验证 last_updated 格式 (YYYY-MM-DD)
    if 'last_updated' in fm:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(fm['last_updated'])):
            errors.append(f"last_updated 格式错误: {fm['last_updated']}, 期望 YYYY-MM-DD")
    
    # 验证 version 格式 (SemVer)
    if 'version' in fm:
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$', str(fm['version'])):
            errors.append(f"version 格式错误: {fm['version']}, 期望 SemVer 如 1.0.0 或 1.0.0-draft")
    
    # 验证 reviewers 和 approvers 是否为列表
    for list_field in ['reviewers', 'approvers', 'tags', 'related_docs']:
        if list_field in fm and not isinstance(fm[list_field], list):
            errors.append(f"{list_field} 必须是列表格式")
    
    return len(errors) == 0, errors

def main():
    docs_root = Path(__file__).parent.parent
    md_files = list(docs_root.rglob('*.md'))
    
    # 排除不需要检查的文件
    exclude_patterns = [
        'archive',
        'templates',
        '.vitepress',
        'node_modules',
        'CHANGELOG.template.md',
        'README.template.md',
    ]
    
    md_files = [
        f for f in md_files
        if not any(p in str(f) for p in exclude_patterns)
    ]
    
    print(f"检查 {len(md_files)} 个 Markdown 文件...")
    print("=" * 60)
    
    total_errors = 0
    files_with_errors = 0
    
    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(docs_root)
        valid, errors = validate_frontmatter(md_file)
        
        if valid:
            print(f"✅ {rel_path}")
        else:
            print(f"❌ {rel_path}")
            for err in errors:
                print(f"   - {err}")
            total_errors += len(errors)
            files_with_errors += 1
    
    print("=" * 60)
    print(f"总计: {len(md_files)} 个文件, {files_with_errors} 个有错误, {total_errors} 个错误项")
    
    if total_errors > 0:
        sys.exit(1)
    else:
        print("✅ 所有文档 Frontmatter 验证通过")
        sys.exit(0)

if __name__ == '__main__':
    main()
EOF