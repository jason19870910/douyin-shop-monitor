#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

filepath = r"c:\Users\Administrator\Documents\trae_projects\douyin\docs\architecture\FRONTEND_DESIGN.md"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the /dian/version route from the sidebar routing table
# Find and remove the line "| `/dian/version` | VersionControl | dian | 版本控制 |"
old_line = "| `/dian/version` | VersionControl | dian | 版本控制 |"
# Remove this line (it might have a newline before or after)
lines = content.split('\n')
new_lines = []
for line in lines:
    if line.strip() == old_line.strip():
        print(f"Removing line: {line.strip()}")
        continue
    new_lines.append(line)

content = '\n'.join(new_lines)

# 2. Add system tools section after /dian/account and before /alerts
# Find the position after "| /dian/account | Account | dian | 账号管理 |"
# and before "| /alerts |重定向 → /alerts/douyin| alerts | 告警设置入口 |"
# Insert new system tools section

# First, let's find where to insert
# We'll add after the dian/account line
account_line = "| `/dian/account` | Account | dian | 账号管理 |"
alerts_line = "| `/alerts` | 重定向 → `/alerts/douyin` | alerts | 告警设置入口 |"

# Insert system tools version control after account line
version_route = "| `/version` | VersionControl | system | 版本控制 |"

# Insert the version route line after the account line
if account_line in content:
    # Find the account line and insert after it
    lines = content.split('\n')
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line == account_line and not inserted:
            # Insert version route after this line, but before the next line
            # We need to be careful about the structure
            inserted = True
            # Just add the version route on a new line after account
            # Actually, let's insert it and then handle the structure
            new_lines.append(version_route)
    content = '\n'.join(new_lines)
    print("Added version route after dian/account")
else:
    print("Could not find dian/account line")

# Now we need to also remove the version route from its current position if it exists elsewhere,
# or just leave the structure. Let's check the current state and rebuild properly.

# Actually, let's do a cleaner approach: rebuild the routing table section
# Find the routing table section and rebuild it

print("Current content length:", len(content))

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ FRONTEND_DESIGN.md 初步更新完成")