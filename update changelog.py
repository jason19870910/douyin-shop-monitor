#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

filepath = r"c:\Users\Administrator\Documents\trae_projects\douyin\docs\architecture\FRONTEND_DESIGN.md"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and update the change log entry
# Look for the 2026-10-11 entry and add the 2026-10-12 entry
old_entry = "- **2026-10-11（晚）**：合规管理页面完整实现：接入 compliance 全部 10 端点"
new_entries = """- **2026-10-11（晚）**：合规管理页面完整实现：接入 compliance 全部 10 端点
- **2026-10-12（上午）**：版本控制作为独立顶级菜单实现：路由 `/version` 加入侧边栏（type: system），后端 4 个 API endpoint 保持不变（`/version`, `/changes`, `/status`, `/env`），前端 `VersionControl` 页面（4 个标签页：当前版本/最近变更/部署状态/环境配置）重新布局至系统工具板块"""

# Replace the old entry
if old_entry in content:
    content = content.replace(old_entry, new_entries)
    print("✅ Updated change log with version control entry")
else:
    print("Could not find old entry, trying alternative...")
    # Try to find any 2026-10-11 entry
    import re
    match = re.search(r'-\*\*2026-10-11.*?\n', content, re.DOTALL)
    if match:
        content = content.replace(match.group(), new_entries)
        print("✅ Updated change log with alternative match")
    else:
        print("Could not find change log entry point")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ FRONTEND_DESIGN.md 变更记录更新完成")