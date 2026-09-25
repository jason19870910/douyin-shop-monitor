#!/bin/bash
# ============================================================
# 5S 自动清理脚本 (5S Cleanup Script)
# 项目: 抖音电商数据监控平台
# 用途: 定期执行 5S 整理/清扫，保持服务器项目目录整洁
# 频率: 每周一次（建议通过 cron 调度）
# ============================================================
# 5S 原则:
#   Seiri (整理): 清除不必要文件
#   Seiton (整顿): 保持有序结构
#   Seiso (清扫): 清理缓存/日志
#   Seiketsu (标准化): 维护标准
#   Shitsuke (素养): 持续改进
# ============================================================

set -euo pipefail

PROJECT_ROOT="/opt/douyin-platform"
LOG_FILE="/var/log/5s-cleanup.log"
RETENTION_DAYS=7  # 日志保留天数
MAX_DANGLING_IMAGES=10

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============== 1. 整理 (Seiri) ==============
seiri() {
    log "=== 1. 整理 (Seiri): 清除不必要文件 ==="

    # 1.1 清除临时 tar.gz 包
    local tar_files
    tar_files=$(find "$PROJECT_ROOT" -maxdepth 2 -name '*.tar.gz' -not -path '*/node_modules/*' 2>/dev/null || true)
    if [ -n "$tar_files" ]; then
        echo "$tar_files" | while read -r f; do
            rm -f "$f"
            log "  删除临时包: $f"
        done
    fi

    # 1.2 清除备份文件
    find "$PROJECT_ROOT" -type f \( -name '*.bak' -o -name '*.bak.*' -o -name '*.old' -o -name '*.orig' -o -name '*~' -o -name '*.dist' -o -name '*.backup' \) \
        -not -path '*/node_modules/*' -not -path '*/.git/*' -delete 2>/dev/null || true
    log "  备份文件已清理"

    # 1.3 清除 Python 缓存
    find "$PROJECT_ROOT" -type d -name '__pycache__' -not -path '*/node_modules/*' -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name '*.pyc' -not -path '*/node_modules/*' -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -type d -name '.pytest_cache' -not -path '*/node_modules/*' -exec rm -rf {} + 2>/dev/null || true
    log "  Python 缓存已清理"

    # 1.4 清除空目录
    find "$PROJECT_ROOT" -type d -empty -not -path '*/node_modules/*' -not -path '*/.git/*' -delete 2>/dev/null || true
    log "  空目录已清理"

    # 1.5 清除 Windows 系统文件污染
    find "$PROJECT_ROOT" -name 'desktop.ini' -o -name 'ehthumbs.db' -o -name 'pagefile.sys' \
        -o -name 'hiberfil.sys' -o -name 'swapfile.sys' -o -name 'Thumbs.db' \
        -not -path '*/node_modules/*' -delete 2>/dev/null || true
    log "  Windows 系统文件污染已清理"
}

# ============== 2. 整顿 (Seiton) ==============
seiton() {
    log "=== 2. 整顿 (Seiton): 检查目录结构 ==="

    # 2.1 检查是否有嵌套 opt/douyin-platform 目录
    if [ -d "$PROJECT_ROOT/opt/douyin-platform" ]; then
        log "  警告: 发现嵌套目录 $PROJECT_ROOT/opt/douyin-platform - 请检查是否为污染"
    fi

    # 2.2 检查根目录是否有遗留脚本
    local legacy_files
    legacy_files=$(find "$PROJECT_ROOT" -maxdepth 1 -name 'test-*.js' -o -name 'test-*.ps1' -o -name 'app-legacy.py' 2>/dev/null || true)
    if [ -n "$legacy_files" ]; then
        log "  警告: 发现遗留测试脚本 - 请检查是否可删除"
    fi

    # 2.3 检查 backup_ 目录
    find "$PROJECT_ROOT" -maxdepth 1 -name 'backup_*' -type d 2>/dev/null | while read -r d; do
        log "  警告: 发现 backup 目录 $d - 请确认是否可删除"
    done
}

# ============== 3. 清扫 (Seiso) ==============
seiso() {
    log "=== 3. 清扫 (Seiso): 清理日志和缓存 ==="

    # 3.1 清理旧日志文件（保留最近 N 天）
    find "$PROJECT_ROOT" -name '*.log.*' -mtime +${RETENTION_DAYS} -not -path '*/node_modules/*' -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name '*.log' -mtime +${RETENTION_DAYS} -size +50M -not -path '*/node_modules/*' -exec truncate -s 0 {} \; 2>/dev/null || true
    log "  旧日志已清理（保留 ${RETENTION_DAYS} 天）"

    # 3.2 清理 Docker 构建缓存
    if command -v docker &> /dev/null; then
        docker builder prune -f --filter "until=48h" &> /dev/null || true
        log "  Docker 构建缓存已清理"

        # 3.3 清理悬挂镜像
        local dangling_count
        dangling_count=$(docker images -f 'dangling=true' -q 2>/dev/null | wc -l)
        if [ "$dangling_count" -gt 0 ]; then
            docker image prune -f &> /dev/null || true
            log "  清理 $dangling_count 个悬挂镜像"
        fi

        # 3.4 清理未使用的镜像（48小时前）
        docker image prune -a -f --filter 'until=48h' &> /dev/null || true
        log "  未使用镜像已清理"
    fi

    # 3.5 清理前端构建缓存
    find "$PROJECT_ROOT/apps/monitor/frontend" -type d -name '.vite' -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT/apps/monitor/frontend" -type d -name '.cache' -exec rm -rf {} + 2>/dev/null || true
    log "  前端构建缓存已清理"
}

# ============== 4. 标准化 (Seiketsu) ==============
seiketsu() {
    log "=== 4. 标准化 (Seiketsu): 维护标准 ==="

    # 4.1 验证关键服务健康状态
    if command -v docker &> /dev/null; then
        local unhealthy
        unhealthy=$(docker compose -f "$PROJECT_ROOT/docker-compose.yml" ps --format json 2>/dev/null | grep -v '"healthy"' | grep -v '"Status":"exited"' | wc -l || echo "0")
        if [ "$unhealthy" -gt 0 ]; then
            log "  警告: 发现 $unhealthy 个非健康服务，请检查"
        else
            log "  所有服务运行正常"
        fi
    fi

    # 4.2 检查磁盘使用率
    local disk_usage
    disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print int($5)}')
    if [ "$disk_usage" -gt 80 ]; then
        log "  警告: 磁盘使用率 ${disk_usage}% - 超过 80% 阈值"
    else
        log "  磁盘使用率 ${disk_usage}% - 正常"
    fi
}

# ============== 5. 素养 (Shitsuke) ==============
shitsuke() {
    log "=== 5. 素养 (Shitsuke): 持续改进 ==="

    # 5.1 统计清理成果
    local total_size
    total_size=$(du -sh "$PROJECT_ROOT" 2>/dev/null | awk '{print $1}')
    log "  项目目录总大小: $total_size"

    # 5.2 记录文件数量
    local file_count
    file_count=$(find "$PROJECT_ROOT" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null | wc -l)
    log "  文件总数: $file_count"

    log "=== 5S 清理完成 ==="
    log ""
}

# ============== 主流程 ==============
main() {
    log "========================================"
    log "5S 清理任务开始"
    log "项目: $PROJECT_ROOT"
    log "========================================"

    seiri
    seiton
    seiso
    seiketsu
    shitsuke
}

main "$@"
