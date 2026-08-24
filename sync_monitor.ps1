# Sync monitor directory to server 122.51.208.138
$ErrorActionPreference = "Stop"

# Config
$localMonitorPath = "C:\Users\Administrator\Documents\trae_projects\douyin\opt\douyin-platform\apps\monitor"
$remoteHost = "122.51.208.138"
$remoteUser = "root"
$sshKey = "C:\Users\Administrator\.ssh\id_rsa"
$remoteBase = "/opt/douyin-platform/apps"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveName = "monitor_sync_$timestamp.tar.gz"
$localArchive = Join-Path $env:TEMP $archiveName
$remoteArchive = "/tmp/$archiveName"

Write-Host "=== 1. Pack local monitor directory ===" -ForegroundColor Cyan
$parent = Split-Path $localMonitorPath -Parent
$leaf = Split-Path $localMonitorPath -Leaf
# Use Windows built-in tar.exe (requires Windows 10 17063+)
tar.exe --exclude="__pycache__" --exclude="logs" --exclude="data" --exclude=".git" `
        --exclude="*.log" --exclude="*.pid" --exclude="node_modules" `
        -czf $localArchive -C $parent $leaf

if (-not (Test-Path $localArchive)) {
    Throw "Packing failed: $localArchive not created"
}
$sizeMB = [math]::Round((Get-Item $localArchive).Length / 1MB, 2)
Write-Host "Created $localArchive ($sizeMB MB)" -ForegroundColor Green

Write-Host "=== 2. Upload to server ===" -ForegroundColor Cyan
scp -i $sshKey $localArchive "${remoteUser}@${remoteHost}:${remoteArchive}"
Write-Host "Upload completed" -ForegroundColor Green

Write-Host "=== 3. Server extract and set permissions ===" -ForegroundColor Cyan
$sshCmd = @"
set -e
cd $remoteBase
tar -xzf $remoteArchive
chown -R monitor:project_admins monitor
chmod 600 monitor/.env
echo 'Extract done, file count:'
find monitor -type f | wc -l
"@
ssh -i $sshKey ${remoteUser}@${remoteHost} $sshCmd
Write-Host "Server extract completed" -ForegroundColor Green

Write-Host "=== 4. Restart Docker services ===" -ForegroundColor Cyan
$restartCmd = @"
cd $remoteBase/monitor
docker compose down --remove-orphans
docker compose up -d --build
docker compose ps
"@
ssh -i $sshKey ${remoteUser}@${remoteHost} $restartCmd
Write-Host "Services restarted" -ForegroundColor Green

# Cleanup local temp archive
Remove-Item -Force $localArchive -ErrorAction SilentlyContinue
Write-Host "=== Sync completed ===" -ForegroundColor Magenta