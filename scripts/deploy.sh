#!/bin/bash
# 抖音平台服务器端一键部署脚本（在 /opt/douyin-platform 目录下运行）
#
# 用法:
#   bash deploy.sh            部署（写部署时间 -> 构建 -> 启动 -> 健康检查，失败自动回滚）
#   bash deploy.sh --rollback 手动回滚到上一次部署的镜像
#
# 前置条件:
#   1) 代码已通过 scp / git 同步到服务器（app 为 bind mount，backend 改动即时生效）
#   2) data/version_info.json 已由本地 scripts/generate_version_info.py 生成后同步到 data/
#      （服务器无 .git，无法本地生成；缺失时版本页面显示 dev/unknown 并打印警告）
set -euo pipefail
cd "$(dirname "$0")"

PROJECT=$(docker compose config --format json 2>/dev/null | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
[ -z "$PROJECT" ] && PROJECT=douyin-platform
echo "[deploy] compose 项目名: $PROJECT"
APP_HEALTH=http://127.0.0.1:5000/api/v1/health
FRONTEND_HEALTH=http://127.0.0.1:3000/health

health_ok () {
  curl -sf "$APP_HEALTH" >/dev/null 2>&1 && curl -sf "$FRONTEND_HEALTH" >/dev/null 2>&1
}

rollback () {
  echo "[rollback] 回滚到上一次部署的镜像 ..."
  if docker image inspect "$PROJECT-app:prev" >/dev/null 2>&1 \
     && docker image inspect "$PROJECT-frontend:prev" >/dev/null 2>&1; then
    docker tag "$PROJECT-app:prev" "$PROJECT-app:latest"
    docker tag "$PROJECT-frontend:prev" "$PROJECT-frontend:latest"
    # 恢复宿主机源码快照：app 容器 bind mount ./src/backend，宿主机源码变更即时生效
    # 且不随镜像回退，不回退则"旧镜像 + 未回退的新代码"组合继续运行、故障依旧存在。
    # 快照由 CI 的 Sync 步在覆盖源码前创建（src_backend_prev.tar），手动回滚同样有效。
    if [ -f src_backend_prev.tar ]; then
      echo "[rollback] 恢复源码快照：src/backend <- src_backend_prev.tar"
      mkdir -p src/backend
      if tar -xf src_backend_prev.tar -C src/backend; then
        echo "[rollback] 源码快照恢复完成"
      else
        echo "[rollback] 源码快照恢复失败，继续回滚镜像层"
      fi
    else
      echo "[rollback] 未找到源码快照 src_backend_prev.tar，仅回滚镜像层"
    fi
    docker compose up -d --no-build
    # 确定性重建前端：:prev tag 与运行镜像一致时 compose 会判定无变化导致回滚空转
    docker compose up -d --no-build --force-recreate --no-deps frontend
    sleep 5
    if health_ok; then
      echo "[rollback] 回滚成功"
    else
      echo "[rollback] 回滚后健康检查仍未通过，请人工介入"
      exit 1
    fi
  else
    echo "[rollback] 未找到 prev 镜像，无法自动回滚"
    exit 1
  fi
}

if [ "${1:-}" = "--rollback" ]; then
  rollback
  exit 0
fi

# 1) 版本信息检查（bind mount 会遮蔽镜像内 /data 副本，只认宿主 data/）
if [ ! -f data/version_info.json ]; then
  echo "[warn] data/version_info.json 不存在：请在本地运行 scripts/generate_version_info.py 并同步到 data/"
fi

# 2) 备份当前镜像为 prev（供回滚）
docker tag "$PROJECT-app:latest" "$PROJECT-app:prev" 2>/dev/null || echo "[info] 无旧 app 镜像可备份"
docker tag "$PROJECT-frontend:latest" "$PROJECT-frontend:prev" 2>/dev/null || echo "[info] 无旧 frontend 镜像可备份"

# 3) 写入部署时间到 .env（docker compose 插值）并导出
DEPLOY_TIME=$(date -Iseconds)
touch .env
if grep -q '^LAST_DEPLOY_TIME=' .env; then
  sed -i "s|^LAST_DEPLOY_TIME=.*|LAST_DEPLOY_TIME=$DEPLOY_TIME|" .env
else
  echo "LAST_DEPLOY_TIME=$DEPLOY_TIME" >> .env
fi
export LAST_DEPLOY_TIME="$DEPLOY_TIME"
echo "[deploy] LAST_DEPLOY_TIME=$DEPLOY_TIME"

# 4) 构建并启动（--build 保证 frontend dist 最新；app bind mount 改动即时生效）
echo "[deploy] 构建镜像 ..."
docker compose build app frontend
echo "[deploy] 启动容器 ..."
docker compose up -d

# 5) 健康检查（最多等待 60 秒），失败自动回滚
DEPLOY_OK=0
for i in $(seq 1 12); do
  if health_ok; then DEPLOY_OK=1; break; fi
  echo "[deploy] 等待服务就绪 ... ($i/12)"
  sleep 5
done
if [ "$DEPLOY_OK" = "1" ]; then
  echo "[deploy] 部署成功（版本页面「最后部署」已更新）"
else
  echo "[deploy] 健康检查失败，自动回滚"
  rollback
fi
