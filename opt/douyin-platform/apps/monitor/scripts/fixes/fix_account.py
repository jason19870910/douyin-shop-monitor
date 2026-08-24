import re

# Fix Account.js - add Switch import
with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "r") as f:
    content = f.read()

# Check if Switch is already imported from antd
if "Switch" not in content.split("from 'antd'")[0] and "Switch" not in content.split("from \"antd\"")[0]:
    # Add Switch to the antd imports
    content = content.replace(
        "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions, Switch } from 'antd';",
        "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions, Switch } from 'antd';"
    )
    # If Switch not in the import, add it
    if "Switch" not in content:
        content = content.replace(
            "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions } from 'antd';",
            "import { Card, Table, Input, Button, Select, Space, Spin, Form, message, Tag, Avatar, Modal, Descriptions, Switch } from 'antd';"
        )
    print("Added Switch import to Account.js")

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "w") as f:
    f.write(content)

print("Done!")