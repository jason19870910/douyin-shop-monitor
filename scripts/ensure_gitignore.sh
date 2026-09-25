#!/usr/bin/env bash
# 确保 .env 被 .gitignore 忽略，并从 Git 历史中移除（如果已跟踪）
# 用法: ./scripts/ensure_gitignore.sh /path/to/project

set -euo pipefail

PROJECT_ROOT="${1:-.}"
GIT_DIR="$PROJECT_ROOT/.git"

if [ ! -d "$GIT_DIR" ]; then
  echo "⚠️  目录不是 Git 仓库: $PROJECT_ROOT"
  exit 0
fi

cd "$PROJECT_ROOT"

# 1. 检查 .gitignore 是否包含 .env
if grep -q '^\.env$' .gitignore 2>/dev/null; then
  echo "✅ .gitignore 已包含 .env"
else
  echo "➕ 向 .gitignore 添加 .env"
  echo ".env" >> .gitignore
fi

# 2. 检查 .env 是否已被跟踪
if git ls-files --error-unmatch .env 2>/dev/null; then
  echo "⚠️  .env 已被 Git 跟踪，从历史中移除..."
  git rm --cached .env
  echo "✅ 已从索引移除 .env（提交以永久删除）"
else
  echo "✅ .env 未被跟踪"
fi

echo "完成。请运行: git add .gitignore && git commit -m \"chore: ignore .env\""