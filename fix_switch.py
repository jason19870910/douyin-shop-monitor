with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "r") as f:
    content = f.read()

# Add Switch to the antd imports
content = content.replace(
    "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions } from 'antd';",
    "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions, Switch } from 'antd';"
)

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "w") as f:
    f.write(content)
print("Fixed Switch import")