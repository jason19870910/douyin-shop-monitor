# 步骤 1：删除 monitor 目录中的 11 个完全重复文件
$monitorDir = 'C:\Users\Administrator\Documents\trae_projects\douyin\opt\douyin-platform\apps\monitor'

Write-Host "=== 删除 monitor 目录中的重复文件 ==="
Remove-Item (Join-Path $monitorDir 'app.py') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: app.py"
Remove-Item (Join-Path $monitorDir 'config.py') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: config.py"
Remove-Item (Join-Path $monitorDir 'requirements.txt') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: requirements.txt"
Remove-Item (Join-Path $monitorDir 'ARCHITECTURE.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: ARCHITECTURE.md"
Remove-Item (Join-Path $monitorDir 'DESIGN.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: DESIGN.md"
Remove-Item (Join-Path $monitorDir 'FRONTEND_DESIGN.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: FRONTEND_DESIGN.md"
Remove-Item (Join-Path $monitorDir 'COMMUNICATION_PLAN.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: COMMUNICATION_PLAN.md"
Remove-Item (Join-Path $monitorDir 'QUALITY_PLAN.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: QUALITY_PLAN.md"
Remove-Item (Join-Path $monitorDir 'RISK_REGISTER.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: RISK_REGISTER.md"
Remove-Item (Join-Path $monitorDir 'REQUIREMENTS.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: REQUIREMENTS.md"
Remove-Item (Join-Path $monitorDir 'PROJECT_CHARTER.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: PROJECT_CHARTER.md"
Remove-Item (Join-Path $monitorDir 'ISSUE_ANALYSIS.md') -Force -ErrorAction SilentlyContinue; Write-Host "已删除: ISSUE_ANALYSIS.md"
Write-Host "=== 步骤 1 完成 ==="