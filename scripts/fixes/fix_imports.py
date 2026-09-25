import os
import re

# Fix Layout.jsx
layout_path = "/opt/douyin-platform/apps/monitor/frontend/src/Layout/Layout.jsx"
with open(layout_path, "r") as f:
    content = f.read()

content = content.replace("from './api'", "from '@api'")
content = content.replace("from './hooks/useApi'", "from '@hooks/useApi'")
content = content.replace("from './utils/formatters'", "from '@utils/formatters'")

with open(layout_path, "w") as f:
    f.write(content)
print("Fixed Layout.jsx")

# Fix page files
pages_dir = "/opt/douyin-platform/apps/monitor/frontend/src/pages"
for filename in os.listdir(pages_dir):
    if filename.endswith(".js"):
        filepath = os.path.join(pages_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        content = content.replace("from '../../api'", "from '@api'")
        content = content.replace("from '../../hooks/useApi'", "from '@hooks/useApi'")
        content = content.replace("from '../../utils/formatters'", "from '@utils/formatters'")
        
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Fixed: {filename}")

print("Done!")