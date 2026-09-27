#!/usr/bin/env python3
"""
修复文档 Frontmatter 中的 version 格式 (1.0 -> 1.0.0)
"""

import re
from pathlib import Path

def fix_version(filepath: Path) -> bool:
    """修复单个文件的 version 格式"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"  ❌ 编码错误: {filepath}")
        return False
    
    # 查找并替换 version: 1.0 -> version: 1.0.0
    new_content = re.sub(
        r'^version:\s*1\.0\s*$',
        'version: 1.0.0',
        content,
        flags=re.MULTILINE
    )
    
    if new_content != content:
        try:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 修复 version: {filepath}")
            return True
        except Exception as e:
            print(f"  ❌ 写入失败: {filepath} - {e}")
            return False
    else:
        print(f"  ⏭️ 无需修复: {filepath}")
        return True

def main():
    docs_root = Path(__file__).parent.parent
    
    # 查找所有 md 文件
    md_files = list(docs_root.rglob('*.md'))
    exclude_patterns = ['archive', 'templates', '.vitepress', 'node_modules']
    md_files = [
        f for f in md_files
        if not any(p in str(f) for p in exclude_patterns)
    ]
    
    print("修复 version 格式 (1.0 -> 1.0.0)...")
    print("=" * 60)
    
    success = 0
    for md_file in md_files:
        if fix_version(md_file):
            success += 1
    
    print("=" * 60)
    print(f"完成: 处理 {success} 个文件")

if __name__ == '__main__':
    main()
EOF