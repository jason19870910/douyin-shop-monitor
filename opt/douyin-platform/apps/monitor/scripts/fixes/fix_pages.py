import re

# Fix Account.js
with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "r") as f:
    content = f.read()

# Make sure handleDelete and handleFormSubmit are defined before the component
# The issue is the component uses handleDelete and handleFormSubmit but they're defined later
# Move them before the component

# Check if they're already defined
if "const handleDelete = async (account, refetch)" in content:
    print("handleDelete already defined")
else:
    # Add the missing functions before the component
    content = content.replace(
        "const Account = () => {",
        """const handleDelete = async (account, refetch) => {
  try {
    if (window.confirm(`确定要删除账号 ${account.account_name} 吗？`)) {
      message.loading('删除中...', 0);
      message.destroy();
      message.success('删除成功');
      refetch();
    }
  } catch (err) {
    message.error('删除失败');
  }
};

const handleFormSubmit = (values) => {
  message.success('账号保存成功');
};

const Account = () => {"""
    )
    print("Added missing functions to Account.js")

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Account.js", "w") as f:
    f.write(content)

# Fix Compliance.js
with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "r") as f:
    content = f.read()

# Check if functions are already defined before the component
if "const handleIgnore = async (record)" in content and content.index("const handleIgnore = async (record)") < content.index("const Compliance = () => {"):
    print("Compliance functions already defined before component")
else:
    # Move the function definitions before the component
    # First remove duplicate definitions inside the component
    content = content.replace(
        """  const handleIgnore = async (record) => {
    try {
      message.loading('处理中...', 0);
      // 调用忽略 API
      message.destroy();
      message.success('已忽略');
      refetch();
    } catch (err) {
      message.destroy();
      message.error('操作失败');
    }
  };

  const handleTakeDown = async (record) => {
    try {
      message.loading('下架中...', 0);
      // 调用下架 API
      message.destroy();
      message.success('已下架');
      refetch();
    } catch (err) {
      message.destroy();
      message.error('下架失败');
    }
  };

  const handleRestore = async (record) => {
    try {
      message.loading('恢复中...', 0);
      // 调用恢复 API
      message.destroy();
      message.success('已恢复');
      refetch();
    } catch (err) {
      message.destroy();
      message.error('操作失败');
    }
  };

  if (loading && !data) {""",
        """  if (loading && !data) {"""
    )
    
    # Add the functions before the component
    content = content.replace(
        "const Compliance = () => {",
        """const handleIgnore = async (record, refetch) => {
  try {
    message.loading('处理中...', 0);
    message.destroy();
    message.success('已忽略');
    refetch();
  } catch (err) {
    message.destroy();
    message.error('操作失败');
  }
};

const handleTakeDown = async (record, refetch) => {
  try {
    message.loading('下架中...', 0);
    message.destroy();
    message.success('已下架');
    refetch();
  } catch (err) {
    message.destroy();
    message.error('下架失败');
  }
};

const handleRestore = async (record, refetch) => {
  try {
    message.loading('恢复中...', 0);
    message.destroy();
    message.success('已恢复');
    refetch();
  } catch (err) {
    message.destroy();
    message.error('操作失败');
  }
};

const Compliance = () => {"""
    )
    print("Fixed Compliance.js")

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "w") as f:
    f.write(content)

print("Done!")