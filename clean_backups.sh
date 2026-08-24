#!/usr/bin/env bash
# 清理历史环境变量备份文件，防止密钥泄露
# 用法: ./scripts/clean_backups.sh /path/to/project

set -euo pipefail

PROJECT_ROOT="${1:-.}"

echo "🔍 扫描项目: $PROJECT_ROOT"

# 查找并删除 .env.backup* 和类似的备份文件
mapfile -t backups < <(find "$PROJECT_ROOT" -maxdepth 1 -type f -name ".env.backup*" -o -name "*.env.*" -o -name "*.bak" -o -name ".env_*" 2>/dev/null || true)

if [ ${#backups[@]} -eq 0 ]; then
  echo "✅ 未发现备份文件"
else
  echo "🗑️  发现 ${#backups[@]} 个备份文件，将删除："
  printf '%s\n' "${backups[@]}"
  rm -f "${backups[@]}"
  echo "✅ 已删除"
fi