import os

# Fix Compliance.js - move handlers inside component
with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "r") as f:
    content = f.read()

# The issue: handleIgnore, handleTakeDown, handleRestore are defined outside the component
# They need to be moved inside the component after handleTableChange and before "if (loading"

# First, remove any external definitions (they might not exist after our local fix)
# Find the pattern where handlers are defined before the component
old_pattern = """  };

const handleIgnore = async (record) => {
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

const handleTakeDown = async (record) => {
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

const handleRestore = async (record) => {
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

new_pattern = """  };

const Compliance = () => {"""

content = content.replace(old_pattern, new_pattern)

# Now add handlers inside the component after handleTableChange
old_inside = """  const handleTableChange = (pagination) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  if (loading && !data) {"""

new_inside = """  const handleTableChange = (pagination) => {
    if (pagination) {
      setPage(pagination.current);
      setPageSize(pagination.pageSize);
    }
  };

  const handleIgnore = async (record) => {
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

  const handleTakeDown = async (record) => {
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

  const handleRestore = async (record) => {
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

  if (loading && !data) {"""

content = content.replace(old_inside, new_inside)

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "w") as f:
    f.write(content)

print("Fixed Compliance.js")