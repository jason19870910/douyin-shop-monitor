#!/usr/bin/env bash
# 通用部署脚本
# 用法: ./deploy.sh [--dry-run] [--skip-tests] [--host <ssh host>] [--user <ssh user>] [--path <remote path>]

set -euo pipefail

DRY_RUN=0
SKIP_TESTS=0
HOST="122.51.208.138"
USER="root"
REMOTE_PATH="/opt/app"
LOCAL_PATH="."

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    --host) HOST="$2"; shift ;;
    --user) USER="$2"; shift ;;
    --path) REMOTE_PATH="$2"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

echo "🚀 部署到 $USER@$HOST:$REMOTE_PATH"

# 1. 运行本地测试（除非跳过）
if [ $SKIP_TESTS -eq 0 ]; then
  echo "🧪 本地测试..."
  if [ -f "package.json" ]; then
    npm test || true
  elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    pytest || true
  fi
fi

# 2. 传输文件（rsync）
echo "📦 同步文件..."
RSYNC_OPTS="-avz --delete --exclude '.env' --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' --exclude 'logs/' --exclude 'coverage/' --exclude 'dist/' --exclude 'uploads/'"

if [ $DRY_RUN -eq 1 ]; then
  echo "DRY RUN: rsync $RSYNC_OPTS $LOCAL_PATH/ $USER@$HOST:$REMOTE_PATH/"
else
  rsync $RSYNC_OPTS $LOCAL_PATH/ $USER@$HOST:$REMOTE_PATH/
fi

# 3. 远程安装依赖并重启服务
echo "🔧 远程操作..."
REMOTE_CMD="cd $REMOTE_PATH && "

if [ -f "$REMOTE_PATH/package.json" ]; then
  REMOTE_CMD+="npm ci && "
elif [ -f "$REMOTE_PATH/requirements.lock.txt" ]; then
  REMOTE_CMD+="python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.lock.txt && "
fi

# 重启策略：优先 systemd，其次 PM2
if ssh $USER@$HOST "systemctl list-units --type=service --state=running | grep -q doudian_monitor"; then
  REMOTE_CMD+="systemctl restart doudian_monitor && systemctl status doudian_monitor --no-pager -l"
elif ssh $USER@$HOST "command -v pm2" >/dev/null; then
  REMOTE_CMD+="pm2 restart all && pm2 list"
else
  REMOTE_CMD+="echo 'No service manager found (systemd/pm2)' && exit 1"
fi

if [ $DRY_RUN -eq 1 ]; then
  echo "DRY RUN: ssh $USER@$HOST \"$REMOTE_CMD\""
else
  ssh $USER@$HOST "$REMOTE_CMD"
fi

echo "✅ 部署完成"