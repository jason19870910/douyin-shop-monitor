import os

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "r") as f:
    content = f.read()

# The columns are defined at module level (lines 11-85) but reference handlers defined inside component
# Need to move columns inside the component

# Find the columns definition and the component start
# Move columns from module level to inside the component

# First, extract the columns definition
columns_start = content.find("const columns = [")
columns_end = content.find("];", columns_start) + 2
columns_code = content[columns_start:columns_end]

# Remove columns from module level
content = content[:columns_start] + content[columns_end:]

# Now insert columns inside the component, right after "const Compliance = () => {"
component_start = content.find("const Compliance = () => {")
insert_pos = content.find("\n", component_start) + 1

# Add columns inside component with proper indentation
indented_columns = "\n".join("  " + line for line in columns_code.split("\n"))
content = content[:insert_pos] + indented_columns + "\n\n" + content[insert_pos:]

with open("/opt/douyin-platform/apps/monitor/frontend/src/pages/Compliance.js", "w") as f:
    f.write(content)

print("Fixed: moved columns inside component")