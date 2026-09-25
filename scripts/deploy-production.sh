#!/usr/bin/env bash
# Production Deployment Script
# Usage: ./scripts/deploy-production.sh [latest|<tag>]

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-douyin}"
TAG="${1:-latest}"
DEPLOY_PATH="/opt/douyin-platform"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required environment variables
check_env() {
    local required_vars=(
        "ALERT_EMAIL"
        "API_AUTH_TOKEN"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check secret files
    local secrets=(
        "douyin_app_id"
        "douyin_app_secret"
        "douyin_access_token"
        "fxg_cookies"
        "creator_cookies"
        "token"
        "ms_token"
        "a_bogus"
        "verify_fp"
        "fp"
        "fxg_shop_id"
        "fxg_log_id"
        "api_key"
    )
    
    for secret in "${secrets[@]}"; do
        if [[ ! -f "./opt/douyin-platform/apps/monitor/secrets/${secret}.txt" ]]; then
            log_warn "Secret file ./opt/douyin-platform/apps/monitor/secrets/${secret}.txt not found"
        fi
    done
}

# Pull latest images
pull_images() {
    log_info "Pulling Docker images with tag: $TAG"
    
    export REGISTRY IMAGE_NAME TAG
    docker compose $COMPOSE_FILES pull
}

# Deploy with zero-downtime
deploy() {
    log_info "Starting deployment..."
    
    export REGISTRY IMAGE_NAME TAG
    docker compose $COMPOSE_FILES up -d --remove-orphans
    
    log_info "Waiting for services to stabilize..."
    sleep 30
}

# Verify health checks
verify_health() {
    log_info "Verifying service health..."
    
    local max_attempts=10
    local attempt=1
    
    # Check monitor API
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf http://localhost:5000/api/v1/health > /dev/null; then
            log_info "Monitor API: HEALTHY"
            break
        fi
        log_warn "Waiting for monitor API... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Monitor API health check failed"
        return 1
    fi
    
    # Check frontend
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf http://localhost/health > /dev/null; then
            log_info "Frontend: HEALTHY"
            break
        fi
        log_warn "Waiting for frontend... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Check HTTPS
    if curl -sf https://wlkj-tech.cn/health > /dev/null; then
        log_info "HTTPS: HEALTHY"
    else
        log_warn "HTTPS check failed (may be expected if certs not configured)"
    fi
    
    return 0
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    docker builder prune -f
}

# Rollback function
rollback() {
    log_warn "Rolling back to previous version..."
    
    local prev_monitor=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep monitor | head -2 | tail -1)
    local prev_frontend=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep frontend | head -2 | tail -1)
    
    if [[ -n "$prev_monitor" && -n "$prev_frontend" ]]; then
        log_info "Rolling back to: $prev_monitor and $prev_frontend"
        docker tag "$prev_monitor" "${REGISTRY}/${IMAGE_NAME}/monitor:latest"
        docker tag "$prev_frontend" "${REGISTRY}/${IMAGE_NAME}/frontend:latest"
        docker compose $COMPOSE_FILES up -d --remove-orphans
        sleep 20
        verify_health
    else
        log_error "No previous images found for rollback"
        return 1
    fi
}

# Main deployment flow
main() {
    log_info "Starting production deployment (tag: $TAG)"
    
    cd "$DEPLOY_PATH" || {
        log_error "Deployment path $DEPLOY_PATH not found"
        exit 1
    }
    
    check_env
    pull_images
    
    if deploy && verify_health; then
        cleanup
        log_info "Deployment completed successfully!"
    else
        log_error "Deployment failed, attempting rollback..."
        if rollback; then
            log_warn "Rollback completed"
            exit 1
        else
            log_error "Rollback failed! Manual intervention required."
            exit 1
        fi
    fi
}

main "$@"