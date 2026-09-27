#!/usr/bin/env python3
"""Fix frontmatter issues in documentation files."""

from pathlib import Path
import yaml

def fix_adr_titles(docs_root: Path):
    """Fix ADR titles that contain colons causing YAML parse errors."""
    adr_files = [
        "adr/001-use-react-vite.md",
        "adr/002-adopt-celery-redis.md",
        "adr/003-dark-theme-design-tokens.md",
    ]
    
    for rel_path in adr_files:
        filepath = docs_root / rel_path
        if filepath.exists():
            content = filepath.read_text(encoding='utf-8')
            # Fix title line - wrap in quotes if it contains colon after ADR-XXX:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('title: ADR-') and ':' in line.split('title:')[1]:
                    # Already has colon in title, need to quote
                    if not line.startswith("title: '"):
                        lines[i] = line.replace('title: ', "title: '") + "'"
            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"Fixed: {rel_path}")

def fix_index_frontmatter(docs_root: Path):
    """Add frontmatter to INDEX.md if missing."""
    index_path = docs_root / "INDEX.md"
    if index_path.exists():
        content = index_path.read_text(encoding='utf-8')
        if not content.startswith('---'):
            fm = """---
title: 文档总索引
version: 1.0.0
status: Published
last_updated: 2026-09-26
owner: PM
reviewers: [Tech Lead]
approvers: [PM]
classification: Public
doc_id: DOC-REF-000
tags: [索引, 文档目录, 总览]
related_docs: []
changelog: |
  v1.0.0 (2026-09-26): 初版生成 - 自动化脚本
---
"""
            index_path.write_text(fm + content, encoding='utf-8')
            print("Fixed: INDEX.md frontmatter added")

def main():
    docs_root = Path(__file__).parent.parent
    fix_adr_titles(docs_root)
    fix_index_frontmatter(docs_root)
    print("All fixes applied!")

if __name__ == '__main__':
    main()
