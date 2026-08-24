<# 
.SYNOPSIS
    Deploy script: sync local code to server 122.51.208.138
.DESCRIPTION
    Supports frontend build, backend code sync, Docker service restart
.PARAMETER Environment
    Target environment: production (default) | staging
.PARAMETER SkipBuild
    Skip frontend build step
.PARAMETER OnlyFrontend
    Deploy frontend only
.PARAMETER OnlyBackend
    Deploy backend only
.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -Environment production
    .\deploy.ps1 -SkipBuild
    .\deploy.ps1 -OnlyFrontend
#>

param(
    [ValidateSet('production', 'staging')]
    [string]$Environment = 'production',
    
    [switch]$SkipBuild,
    
    [switch]$OnlyFrontend,
    
    [switch]$OnlyBackend
)

# Configuration
$SSH_HOST = "122.51.208.138"
$SSH_USER = "root"
$SSH_KEY = "C:\Users\Administrator\.ssh\id_rsa"
$REMOTE_BASE = "/opt/douyin-platform"
$LOCAL_PROJECT_ROOT = "C:\Users\Administrator\Documents\trae_projects\douyin\opt\douyin-platform"
$FRONTEND_DIR = "$LOCAL_PROJECT_ROOT\apps\monitor\frontend"
$BACKEND_DIR = "$LOCAL_PROJECT_ROOT\apps\monitor"

function Write-Step($message) { Write-Host "========== $message ==========" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Error($message) { Write-Host "[ERR] $message" -ForegroundColor Red }
function Write-Info($message) { Write-Host "  -> $message" -ForegroundColor Yellow }

function Test-SSHConnection {
    Write-Step "Testing SSH connection..."
    $result = ssh -i $SSH_KEY -o ConnectTimeout=10 -o BatchMode=yes $SSH_USER@$SSH_HOST "echo 'SSH OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "SSH connection OK"
        return $true
    } else {
        Write-Error "SSH connection failed: $result"
        return $false
    }
}

function Build-Frontend {
    if ($SkipBuild) {
        Write-Info "Skipping frontend build (--SkipBuild)"
        return $true
    }
    
    Write-Step "Building frontend..."
    Set-Location $FRONTEND_DIR
    
    Write-Info "Installing dependencies..."
    npm ci
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm ci failed"
        return $false
    }
    
    Write-Info "Running build..."
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend build failed"
        return $false
    }
    
    Write-Success "Frontend build completed: $FRONTEND_DIR\build"
    return $true
}

function Sync-ToServer {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$Description
    )
    
    Write-Step "Syncing $Description..."
    Write-Info "Local: $LocalPath"
    $remoteTarget = "${SSH_USER}@${SSH_HOST}:${RemotePath}"
    Write-Info "Remote: $remoteTarget"
    
    # Ensure remote directory exists
    $mkdirCmd = "ssh -i $SSH_KEY $SSH_USER@$SSH_HOST 'mkdir -p $RemotePath'"
    Write-Info "Creating remote directory: $mkdirCmd"
    Invoke-Expression $mkdirCmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create remote directory"
        return $false
    }
    
    # Use scp for Windows compatibility (rsync not available)
    # Create a temporary directory with filtered content, then scp
    $excludeDirs = @(
        "node_modules"
        ".git"
        "__pycache__"
        ".pytest_cache"
        "build"
    )
    $excludeFiles = @(
        ".gitignore"
        "*.log"
        "*.pyc"
        "*.map"
        ".env*.local"
    )
    
    # Create a temp directory and copy filtered content
    $tempDir = [System.IO.Path]::GetTempPath() + "deploy_sync_" + [System.Guid]::NewGuid().ToString("N")
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    # Copy with exclusions using robocopy (Windows built-in)
    $robocopyDirExcludes = $excludeDirs -join " "
    $robocopyFileExcludes = $excludeFiles -join " "
    $robocopyCmd = "robocopy '$LocalPath' '$tempDir\$([System.IO.Path]::GetFileName($LocalPath))' /E /XD $robocopyDirExcludes /XF $robocopyFileExcludes /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP"
    
    Write-Info "Copying to temp directory with exclusions..."
    Write-Info "Command: $robocopyCmd"
    $robocopyOutput = Invoke-Expression $robocopyCmd 2>&1
    Write-Host $robocopyOutput
    # robocopy returns exit codes 0-7 for success, 8+ for errors
    if ($LASTEXITCODE -ge 8) {
        Write-Error "Robocopy failed"
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        return $false
    }
    
    # Use scp to copy to remote
    $scpCmd = "scp -i $SSH_KEY -o StrictHostKeyChecking=no -r '$tempDir\$([System.IO.Path]::GetFileName($LocalPath))' '${remoteTarget}'"
    Write-Info "Command: $scpCmd"
    $scpOutput = Invoke-Expression $scpCmd 2>&1
    Write-Host $scpOutput
    
    # Cleanup temp directory
    Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$Description sync completed"
        return $true
    } else {
        Write-Error "$Description sync failed"
        return $false
    }
}

function Restart-Services {
    Write-Step "Restarting server services..."
    
    $commands = @()
    
    if (-not $OnlyFrontend) {
        $commands += "cd $REMOTE_BASE/apps/monitor && docker compose down && docker compose up -d --build"
    }
    
    if (-not $OnlyBackend) {
        $commands += "cd $REMOTE_BASE/apps/monitor/frontend && docker compose down && docker compose up -d --build"
    }
    
    $commands += "nginx -t && nginx -s reload"
    
    $fullCmd = $commands -join " && "
    Write-Info "Executing: $fullCmd"
    
    $sshCmd = "ssh -i $SSH_KEY $SSH_USER@$SSH_HOST '$fullCmd'"
    Invoke-Expression $sshCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services restarted"
        return $true
    } else {
        Write-Error "Service restart failed"
        return $false
    }
}

function Verify-Deployment {
    Write-Step "Verifying deployment..."
    
    $healthUrl = "https://wlkj-tech.cn/health"
    Write-Info "Checking health endpoint: $healthUrl"
    
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Success "Health check passed"
            return $true
        }
    } catch {
        Write-Error "Health check failed: $($_.Exception.Message)"
    }
    
    $frontendUrl = "https://wlkj-tech.cn"
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend accessible"
            return $true
        }
    } catch {
        Write-Error "Frontend access failed: $($_.Exception.Message)"
    }
    
    return $false
}

# Main
Write-Host "Starting deployment to $Environment environment" -ForegroundColor Magenta
Write-Host "Target server: $SSH_HOST" -ForegroundColor Gray
Write-Host "Local project: $LOCAL_PROJECT_ROOT" -ForegroundColor Gray
Write-Host ""

$success = $true

# 1. Test SSH
if (-not (Test-SSHConnection)) {
    exit 1
}

# 2. Build frontend
if (-not $OnlyBackend) {
    if (-not (Build-Frontend)) {
        $success = $false
    }
}

if (-not $success) {
    Write-Error "Build failed, aborting deployment"
    exit 1
}

# 3. Sync backend
if (-not $OnlyFrontend) {
    if (-not (Sync-ToServer -LocalPath $BACKEND_DIR -RemotePath "$REMOTE_BASE/apps/monitor" -Description "Backend code")) {
        $success = $false
    }
}

# 4. Sync frontend build
if (-not $OnlyBackend) {
    $frontendBuildDir = "$FRONTEND_DIR\build"
    if (-not (Sync-ToServer -LocalPath $frontendBuildDir -RemotePath "$REMOTE_BASE/apps/monitor/frontend/build" -Description "Frontend build")) {
        $success = $false
    }
}

if (-not $success) {
    Write-Error "Sync failed, aborting deployment"
    exit 1
}

# 5. Restart services
if (-not (Restart-Services)) {
    Write-Error "Service restart failed"
    exit 1
}

# 6. Verify
Start-Sleep -Seconds 5
if (Verify-Deployment) {
    Write-Host "Deployment successful!" -ForegroundColor Green
} else {
    Write-Error "Deployment may have issues, please check manually"
    exit 1
}