<# 
.SYNOPSIS
    简化同步脚本：使用 scp/rsync 将本地文件同步到服务器
.DESCRIPTION
    支持 rsync (Linux/macOS/WSL) 和 scp (Windows 原生 OpenSSH)
    适用于：快速同步代码、配置文件、前端构建产物
.PARAMETER Target
    同步目标: all (默认) | frontend | backend | config
.PARAMETER DryRun
    试运行模式，不实际传输文件 (仅 rsync 支持)
.PARAMETER Delete
    删除远程多余文件 (--delete, 仅 rsync 支持)
.PARAMETER UseScp
    强制使用 scp 而非 rsync
.EXAMPLE
    .\sync.ps1
    .\sync.ps1 -Target frontend
    .\sync.ps1 -Target config -DryRun
    .\sync.ps1 -Target all -Delete
    .\sync.ps1 -UseScp
#>

param(
    [ValidateSet('all', 'frontend', 'backend', 'config')]
    [string]$Target = 'all',
    
    [switch]$DryRun,
    
    [switch]$Delete,
    
    [switch]$UseScp
)

# 配置
$SSH_HOST = "122.51.208.138"
$SSH_USER = "root"
$SSH_KEY = "C:\Users\Administrator\.ssh\id_rsa"
$REMOTE_BASE = "/opt/douyin-platform"
$LOCAL_BASE = "C:\Users\Administrator\Documents\trae_projects\douyin\opt\douyin-platform"

function Write-Step($msg) { Write-Host "========== $msg ==========" -ForegroundColor Cyan }
function Write-OK($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "  -> $msg" -ForegroundColor Yellow }

# Detect available sync tool
function Get-SyncTool {
    if ($UseScp) {
        return "scp"
    }
    
    # Check if rsync is available
    $rsyncTest = & rsync --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        return "rsync"
    }
    
    # Check if scp is available
    $scpTest = & scp 2>$null
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {  # scp returns 1 when no args
        return "scp"
    }
    
    Write-Err "Neither rsync nor scp found. Please install one:"
    Write-Err "  - rsync: choco install rsync / scoop install rsync / Git for Windows"
    Write-Err "  - scp: Windows 10+ built-in OpenSSH Client"
    exit 1
}

$SYNC_TOOL = Get-SyncTool
Write-Info "Using sync tool: $SYNC_TOOL"

# 通用排除模式 (仅 rsync 使用)
$CommonExcludes = @(
    "--exclude=node_modules"
    "--exclude=.git"
    "--exclude=.gitignore"
    "--exclude=*.log"
    "--exclude=__pycache__"
    "--exclude=.pytest_cache"
    "--exclude=*.pyc"
    "--exclude=.env*.local"
    "--exclude=*.map"
    "--exclude=build"
    "--exclude=dist"
    "--exclude=.vite"
)

function Sync-Directory {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$Label,
        [string[]]$ExtraExcludes = @()
    )
    
    if (-not (Test-Path $LocalPath)) {
        Write-Err "Local path not found: $LocalPath"
        return $false
    }
    
    Write-Step "Sync $Label"
    Write-Info "Local: $LocalPath"
    $remoteTarget = "${SSH_USER}@${SSH_HOST}:${RemotePath}"
    Write-Info "Remote: $remoteTarget"
    
    $success = $false
    
    if ($SYNC_TOOL -eq "rsync") {
        $excludes = $CommonExcludes + $ExtraExcludes
        $deleteFlag = if ($Delete) { "--delete" } else { "" }
        $dryRunFlag = if ($DryRun) { "--dry-run" } else { "" }
        
        $cmd = "rsync -avz $dryRunFlag $deleteFlag -e 'ssh -i $SSH_KEY -o StrictHostKeyChecking=no' $($excludes -join ' ') '$LocalPath/' '${remoteTarget}/'"
        
        Write-Info "Command: $cmd"
        Invoke-Expression $cmd
        $success = ($LASTEXITCODE -eq 0)
    }
    else {
        # 使用 scp 递归复制
        if ($DryRun) {
            Write-Info "Dry-run not supported with scp, skipping"
            return $true
        }
        
        # scp 不支持排除模式，先创建临时目录复制文件
        $tempDir = [System.IO.Path]::GetTempFileName()
        Remove-Item $tempDir
        New-Item -ItemType Directory -Path $tempDir | Out-Null
        
        # 复制文件到临时目录（排除不需要的）
        $excludeDirs = @("node_modules", ".git", "__pycache__", ".pytest_cache", "build", "dist", ".vite")
        $excludeFiles = @("*.log", "*.pyc", "*.map", ".env*.local")
        
        Get-ChildItem -Path $LocalPath -Recurse -Force | Where-Object {
            $relative = $_.FullName.Substring($LocalPath.Length + 1)
            $parts = $relative.Split('\')
            $shouldExclude = $false
            foreach ($part in $parts) {
                if ($excludeDirs -contains $part) { $shouldExclude = $true; break }
                foreach ($pattern in $excludeFiles) {
                    if ($part -like $pattern) { $shouldExclude = $true; break }
                }
            }
            return -not $shouldExclude
        } | ForEach-Object {
            $dest = Join-Path $tempDir $_.FullName.Substring($LocalPath.Length + 1)
            if ($_.PSIsContainer) {
                New-Item -ItemType Directory -Path $dest -Force | Out-Null
            } else {
                $destDir = Split-Path $dest -Parent
                if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
                Copy-Item $_.FullName -Destination $dest -Force
            }
        }
        
        # 使用 scp 上传
        $scpCmd = "scp -i $SSH_KEY -o StrictHostKeyChecking=no -r '$tempDir/' '${remoteTarget}/'"
        Write-Info "Command: $scpCmd"
        Invoke-Expression $scpCmd
        $success = ($LASTEXITCODE -eq 0)
        
        # 清理临时目录
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    if ($success) {
        Write-OK "$Label sync completed"
        return $true
    } else {
        Write-Err "$Label sync failed"
        return $false
    }
}

$success = $true

# 同步后端代码
function Sync-Backend {
    param([bool]$CurrentSuccess)
    $result = Sync-Directory `
        -LocalPath "$LOCAL_BASE\apps\monitor" `
        -RemotePath "$REMOTE_BASE/apps/monitor" `
        -Label "Backend code" `
        -ExtraExcludes @("--exclude=frontend")
    return $CurrentSuccess -and $result
}

# 同步前端源码
function Sync-FrontendSource {
    param([bool]$CurrentSuccess)
    $result = Sync-Directory `
        -LocalPath "$LOCAL_BASE\apps\monitor\frontend" `
        -RemotePath "$REMOTE_BASE/apps/monitor/frontend" `
        -Label "Frontend source"
    return $CurrentSuccess -and $result
}

# 同步前端构建产物
function Sync-FrontendBuild {
    param([bool]$CurrentSuccess)
    if (-not (Test-Path "$LOCAL_BASE\apps\monitor\frontend\build")) {
        Write-Info "Frontend build not found, skipping"
        return $CurrentSuccess
    }
    $result = Sync-Directory `
        -LocalPath "$LOCAL_BASE\apps\monitor\frontend\build" `
        -RemotePath "$REMOTE_BASE/apps/monitor/frontend/build" `
        -Label "Frontend build"
    return $CurrentSuccess -and $result
}

# 同步配置文件
function Sync-Config {
    param([bool]$CurrentSuccess)
    $configFiles = @(
        "$LOCAL_BASE\apps\monitor\.env"
        "$LOCAL_BASE\apps\monitor\docker-compose.yml"
        "$LOCAL_BASE\apps\monitor\nginx.conf"
        "$LOCAL_BASE\apps\monitor\frontend\.env"
        "$LOCAL_BASE\apps\monitor\frontend\nginx.conf"
        "$LOCAL_BASE\apps\monitor\frontend\docker-compose.yml"
        "$LOCAL_BASE\apps\monitor\frontend\Dockerfile"
    )
    
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            $relPath = $file.Replace("$LOCAL_BASE\", "")
            $remoteDir = Split-Path "$REMOTE_BASE/$relPath"
            $result = Sync-Directory `
                -LocalPath (Split-Path $file) `
                -RemotePath $remoteDir `
                -Label "Config: $relPath" `
                -ExtraExcludes @("--exclude=*")
            $CurrentSuccess = $CurrentSuccess -and $result
        }
    }
    return $CurrentSuccess
}

# 执行同步逻辑
if ($Target -eq 'all' -or $Target -eq 'backend') {
    $success = Sync-Backend -CurrentSuccess $success
}

if ($Target -eq 'all' -or $Target -eq 'frontend') {
    $success = Sync-FrontendSource -CurrentSuccess $success
    $success = Sync-FrontendBuild -CurrentSuccess $success
}

if ($Target -eq 'config') {
    $success = Sync-Config -CurrentSuccess $success
}

if ($DryRun -and $SYNC_TOOL -eq "scp") {
    Write-Host ""
    Write-Info "Dry-run not supported with scp. Install rsync for dry-run support."
} elseif ($DryRun) {
    Write-Host ""
    Write-Info "Dry-run completed. Remove -DryRun to execute actual sync."
} elseif ($success) {
    Write-Host ""
    Write-OK "Sync completed successfully!"
} else {
    Write-Host ""
    Write-Err "Sync failed with errors"
    exit 1
}