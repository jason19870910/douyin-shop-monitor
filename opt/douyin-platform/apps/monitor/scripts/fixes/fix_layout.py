import re
with open("/opt/douyin-platform/apps/monitor/frontend/src/Layout/Layout.jsx", "r") as f:
    content = f.read()

# Add ShoppingCartOutlined to imports
content = content.replace("UsergroupAddOutlined,", "UsergroupAddOutlined,\n  ShoppingCartOutlined,")

with open("/opt/douyin-platform/apps/monitor/frontend/src/Layout/Layout.jsx", "w") as f:
    f.write(content)
print("Fixed Layout.jsx")