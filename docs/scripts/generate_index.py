#!/usr/bin/env python3
"""生成文档索引 - 自动扫描目录结构生成 INDEX.md"""
import os
import yaml
from datetime import datetime
from pathlib import Path

DOCS_ROOT = Path(__file__).parent.parent

CATEGORY_ORDER = [
    ("governance", "项目治理"),
    ("requirements", "需求规格"),
    ("architecture", "架构设计"),
    ("api", "API 设计"),
    ("operations", "运维手册"),
    ("quality", "质量保证"),
    ("risk", "风险管理"),
    ("development", "开发规范"),
    ("reference", "参考资料"),
    ("adr", "架构决策记录"),
    ("meetings", "会议记录"),
]

STATUS_ICONS = {"Draft": "🟡", "UnderReview": "🔵", "Approved": "🟢", "Deprecated": "🔴", "Published": "🟢", "Archived": "⚫", "Obsolete": "⚫", "Proposed": "🔵", "Accepted": "🟢", "Superseded": "🔴"}
CLASSIFICATION_ICONS = {"Public": "🌐", "Internal": "🔒", "Confidential": "🔐", "Restricted": "🚫"}

def scan_documents():
    docs = []
    for md_file in DOCS_ROOT.rglob("*.md"):
        if md_file.name == "INDEX.md":
            continue
        rel_path = md_file.relative_to(DOCS_ROOT)
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1])
                    if fm:
                        fm["path"] = str(rel_path)
                        fm["depth"] = len(rel_path.parts)
                        docs.append(fm)
        except Exception:
            pass
    return docs

def get_category_key(path_str):
    first_dir = path_str.split("/")[0] if "/" in path_str else "reference"
    for key, _ in CATEGORY_ORDER:
        if key == first_dir:
            return key
    return "reference"

def generate_index(docs):
    by_category = {}
    for d in docs:
        cat = get_category_key(d["path"])
        by_category.setdefault(cat, []).append(d)
    
    total = len(docs)
    by_status = {}
    by_class = {}
    for d in docs:
        by_status[d.get("status", "draft")] = by_status.get(d.get("status", "draft"), 0) + 1
        by_class[d.get("classification", "internal")] = by_class.get(d.get("classification", "internal"), 0) + 1
    
    lines = []
    lines.append("---")
    lines.append("doc_id: INDEX")
    lines.append("title: 项目文档总索引")
    lines.append("version: 1.0.0")
    lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"last_updated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("author: Documentation Team")
    lines.append("owner: PMO")
    lines.append("approvers: [Tech Lead, Architect]")
    lines.append("reviewers: [Tech Lead, Architect]")
    lines.append("classification: Internal")
    lines.append("status: Approved")
    lines.append("changelog: []")
    lines.append("tags: [index, navigation, master]")
    lines.append("---")
    lines.append("")
    lines.append("# 项目文档总索引")
    lines.append("")
    lines.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 共 **{total}** 份文档")
    lines.append("")
    
    lines.append("## 文档统计")
    lines.append("")
    lines.append("| 维度 | 分布 |")
    lines.append("|------|------|")
    lines.append(f"| **总计** | {total} 份 |")
    for status, count in sorted(by_status.items()):
        lines.append(f"| {STATUS_ICONS.get(status, '⚪')} {status.capitalize()} | {count} 份 |")
    for cls, count in sorted(by_class.items()):
        lines.append(f"| {CLASSIFICATION_ICONS.get(cls, '⚪')} {cls.capitalize()} | {count} 份 |")
    lines.append("")
    
    for cat_key, cat_name in CATEGORY_ORDER:
        cat_docs = by_category.get(cat_key, [])
        if not cat_docs:
            continue
        lines.append(f"## {cat_name} ({len(cat_docs)})")
        lines.append("")
        lines.append("| 文档 | 版本 | 状态 | 密级 | 更新时间 |")
        lines.append("|------|------|------|------|----------|")
        for d in sorted(cat_docs, key=lambda x: x["path"]):
            status_icon = STATUS_ICONS.get(d.get("status", "draft"), "⚪")
            class_icon = CLASSIFICATION_ICONS.get(d.get("classification", "internal"), "⚪")
            rel_path = d["path"]
            title = d.get("title", Path(rel_path).stem)
            version = d.get("version", "1.0.0")
            status = d.get("status", "draft")
            classification = d.get("classification", "internal")
            date = d.get("date", "")
            lines.append(f"| [{title}]({rel_path}) | {version} | {status_icon} {status} | {class_icon} {classification} | {date} |")
        lines.append("")
    
    return "\n".join(lines)

def main():
    print(f"扫描文档目录: {DOCS_ROOT}")
    docs = scan_documents()
    print(f"发现 {len(docs)} 个有效文档")
    index_content = generate_index(docs)
    index_path = DOCS_ROOT / "INDEX.md"
    index_path.write_text(index_content, encoding="utf-8")
    print(f"索引已生成: {index_path}")

if __name__ == "__main__":
    main()