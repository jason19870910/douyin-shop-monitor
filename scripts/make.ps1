<#>
.SYNOPSIS
    Douyin Project - Unified Build & Deployment Commands (PowerShell)

.DESCRIPTION
    Provides unified commands for building, testing, deploying, and maintaining the Douyin project.
    Usage: .\scripts\make.ps1 <target>
    Example: .\scripts\make.ps1 help

.NOTES
    Requires: Docker, Docker Compose, PowerShell 5.1+
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Target = "help",

    [Parameter(Mandatory=$false)]
    [switch]$NoCache
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  Douyin Project - Available Commands" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🐳 Docker Compose:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 up           - Start all services (detached)"
    Write-Host "  .\scripts\make.ps1 up-logs      - Start all services with logs"
    Write-Host "  .\scripts\make.ps1 down         - Stop and remove all containers"
    Write-Host "  .\scripts\make.ps1 restart      - Restart all services"
    Write-Host "  .\scripts\make.ps1 ps           - List running containers"
    Write-Host "  .\scripts\make.ps1 logs         - Follow logs for all services"
    Write-Host "  .\scripts\make.ps1 logs-monitor - Follow monitor service logs"
    Write-Host "  .\scripts\make.ps1 logs-frontend- Follow frontend service logs"
    Write-Host "  .\scripts\make.ps1 logs-celery  - Follow celery service logs"
    Write-Host ""
    Write-Host "🔨 Build:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 build        - Build all service images"
    Write-Host "  .\scripts\make.ps1 build-monitor- Build monitor service image"
    Write-Host "  .\scripts\make.ps1 build-frontend- Build frontend service image"
    Write-Host "  .\scripts\make.ps1 rebuild      - Rebuild all images (no cache)"
    Write-Host ""
    Write-Host "🧪 Testing & Quality:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 test         - Run all tests"
    Write-Host "  .\scripts\make.ps1 test-monitor - Run monitor service tests"
    Write-Host "  .\scripts\make.ps1 test-frontend- Run frontend tests"
    Write-Host "  .\scripts\make.ps1 lint         - Run all linters"
    Write-Host "  .\scripts\make.ps1 lint-monitor - Run monitor linter (ruff)"
    Write-Host "  .\scripts\make.ps1 lint-frontend- Run frontend linter (eslint)"
    Write-Host "  .\scripts\make.ps1 format       - Format code (black + prettier)"
    Write-Host ""
    Write-Host "🧹 Maintenance:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 clean        - Remove stopped containers, unused images, volumes"
    Write-Host "  .\scripts\make.ps1 clean-all    - Deep clean (includes volumes)"
    Write-Host "  .\scripts\make.ps1 prune        - Docker system prune"
    Write-Host "  .\scripts\make.ps1 backup       - Backup project (exclude node_modules, .git, etc.)"
    Write-Host ""
    Write-Host "🚀 Deployment:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 deploy       - Deploy to production (with SSL)"
    Write-Host "  .\scripts\make.ps1 deploy-dev   - Deploy to development"
    Write-Host "  .\scripts\make.ps1 ssl-init     - Initialize SSL certificates (Let's Encrypt)"
    Write-Host "  .\scripts\make.ps1 ssl-renew    - Renew SSL certificates"
    Write-Host ""
    Write-Host "📦 Database:" -ForegroundColor Green
    Write-Host "  .\scripts\make.ps1 migrate      - Run database migrations"
    Write-Host "  .\scripts\make.ps1 migrate-create- Create new migration"
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Invoke-DockerCompose {
    param([string[]]$Args)
    docker compose -f docker-compose.yml @Args
}

function Invoke-CommandInDir {
    param([string]$Dir, [string]$Command)
    Push-Location $Dir
    try {
        Invoke-Expression $Command
    } finally {
        Pop-Location
    }
}

switch ($Target) {
    "help" { Show-Help }

    # Docker Compose
    "up" { Invoke-DockerCompose up -d }
    "up-logs" { Invoke-DockerCompose up }
    "down" { Invoke-DockerCompose down }
    "restart" { Invoke-DockerCompose restart }
    "ps" { Invoke-DockerCompose ps }
    "logs" { Invoke-DockerCompose logs -f }
    "logs-monitor" { Invoke-DockerCompose logs -f monitor }
    "logs-frontend" { Invoke-DockerCompose logs -f frontend }
    "logs-celery" { Invoke-DockerCompose logs -f celery_worker, celery_beat }
    "logs-nginx" { Invoke-DockerCompose logs -f nginx }
    "logs-redis" { Invoke-DockerCompose logs -f redis }

    # Build
    "build" { Invoke-DockerCompose build }
    "build-monitor" { Invoke-DockerCompose build monitor }
    "build-frontend" { Invoke-DockerCompose build frontend }
    "build-nginx" { Invoke-DockerCompose build nginx }
    "rebuild" { Invoke-DockerCompose build --no-cache }

    # Test
    "test" { 
        Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "python -m pytest tests/ -v --cov=app --cov-report=term-missing"
        Invoke-CommandInDir "frontend" "npm test -- --watchAll=false --ci"
    }
    "test-monitor" { Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "python -m pytest tests/ -v --cov=app --cov-report=term-missing" }
    "test-frontend" { Invoke-CommandInDir "frontend" "npm test -- --watchAll=false --ci" }

    # Lint
    "lint" {
        Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "ruff check . && ruff format --check ."
        Invoke-CommandInDir "frontend" "npm run lint"
    }
    "lint-monitor" { Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "ruff check . && ruff format --check ." }
    "lint-frontend" { Invoke-CommandInDir "frontend" "npm run lint" }

    # Format
    "format" {
        Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "ruff format ."
        Invoke-CommandInDir "frontend" "npx prettier --write \"src/**/*.{js,jsx,ts,tsx,json,css,md}\""
    }
    "format-monitor" { Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "ruff format ." }
    "format-frontend" { Invoke-CommandInDir "frontend" "npx prettier --write \"src/**/*.{js,jsx,ts,tsx,json,css,md}\"" }

    # Maintenance
    "clean" {
        Invoke-DockerCompose down -v --remove-orphans
        docker container prune -f
        docker image prune -f
    }
    "clean-all" {
        Invoke-DockerCompose down -v --remove-orphans
        docker system prune -af --volumes
    }
    "prune" { docker system prune -af --volumes }

    "backup" {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupName = "douyin_backup_$timestamp"
        Write-Host "Creating backup: $backupName" -ForegroundColor Yellow
        tar --exclude='node_modules' `
            --exclude='.git' `
            --exclude='__pycache__' `
            --exclude='*.pyc' `
            --exclude='*.log' `
            --exclude='*.tar.gz' `
            --exclude='*.zip' `
            --exclude='douyin_backup_*' `
            --exclude='frontend/build' `
            --exclude='opt/douyin-platform/apps/monitor/logs' `
            --exclude='.venv' `
            --exclude='venv' `
            -czf "$backupName.tar.gz" .
        Write-Host "Backup created: $backupName.tar.gz" -ForegroundColor Green
    }

    # Deployment
    "deploy" {
        Invoke-DockerCompose build
        Invoke-DockerCompose up -d
        Write-Host "✅ Production deployment complete!" -ForegroundColor Green
        Write-Host "   Frontend: https://wlkj-tech.cn"
        Write-Host "   API:      https://wlkj-tech.cn/api/v1"
        Write-Host "   Health:   https://wlkj-tech.cn/health"
    }
    "deploy-dev" {
        Invoke-DockerCompose up -d --build
        Write-Host "✅ Development deployment complete!" -ForegroundColor Green
        Write-Host "   Frontend: http://localhost:3000"
        Write-Host "   API:      http://localhost:5000/api/v1"
        Write-Host "   Health:   http://localhost/health"
    }

    "ssl-init" {
        Write-Host "Initializing SSL certificates..." -ForegroundColor Yellow
        docker run -it --rm `
            -v ${PWD}/certbot/conf:/etc/letsencrypt `
            -v ${PWD}/certbot/www:/var/www/certbot `
            certbot/certbot certonly --webroot `
            -w /var/www/certbot `
            -d wlkj-tech.cn -d www.wlkj-tech.cn `
            --email admin@wlkj-tech.cn --agree-tos --no-eff-email
    }

    "ssl-renew" {
        Write-Host "Renewing SSL certificates..." -ForegroundColor Yellow
        docker run -it --rm `
            -v ${PWD}/certbot/conf:/etc/letsencrypt `
            -v ${PWD}/certbot/www:/var/www/certbot `
            certbot/certbot renew --webroot -w /var/www/certbot
        Invoke-DockerCompose exec nginx nginx -s reload
    }

    # Database
    "migrate" { Invoke-DockerCompose exec monitor python -m alembic upgrade head }
    "migrate-create" {
        $msg = Read-Host "Migration message"
        Invoke-DockerCompose exec monitor python -m alembic revision --autogenerate -m $msg
    }

    # Shell access
    "shell-monitor" { Invoke-DockerCompose exec monitor sh }
    "shell-frontend" { Invoke-DockerCompose exec frontend sh }
    "shell-redis" { Invoke-DockerCompose exec redis redis-cli }
    "shell-nginx" { Invoke-DockerCompose exec nginx sh }

    # Install
    "install-monitor" { Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "pip install -r requirements.txt" }
    "install-frontend" { Invoke-CommandInDir "frontend" "npm install" }
    "install-all" {
        Invoke-CommandInDir "opt/douyin-platform/apps/monitor" "pip install -r requirements.txt"
        Invoke-CommandInDir "frontend" "npm install"
    }

    # Health check
    "health" {
        Write-Host "Checking service health..." -ForegroundColor Yellow
        try { Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing; Write-Host "✅ Nginx/Health OK" -ForegroundColor Green } catch { Write-Host "❌ Nginx/Health FAILED" -ForegroundColor Red }
        try { Invoke-WebRequest -Uri "http://localhost:5000/api/v1/health" -UseBasicParsing; Write-Host "✅ Monitor API OK" -ForegroundColor Green } catch { Write-Host "❌ Monitor API FAILED" -ForegroundColor Red }
        try { Invoke-WebRequest -Uri "http://localhost:3000/health" -UseBasicParsing; Write-Host "✅ Frontend OK" -ForegroundColor Green } catch { Write-Host "❌ Frontend FAILED" -ForegroundColor Red }
    }

    "status" {
        Invoke-DockerCompose ps
        Write-Host ""
        .\scripts\make.ps1 health
    }

    default {
        Write-Host "Unknown target: $Target" -ForegroundColor Red
        Show-Help
        exit 1
    }
}