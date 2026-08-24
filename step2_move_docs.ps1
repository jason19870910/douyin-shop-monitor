# 步骤 2：将根目录通用文档移入 docs/ 目录
$rootDir = 'C:\Users\Administrator\Documents\trae_projects\douyin'
$docsDir = 'C:\Users\Administrator\Documents\trae_projects\douyin\docs'

# 创建 docs 目录
if (-not (Test-Path $docsDir)) {
    New-Item -ItemType Directory -Path $docsDir -Force | Out-Null
    Write-Host "已创建目录: docs/"
}

$docFiles = @(
    'ARCHITECTURE.md',
    'DESIGN.md',
    'FRONTEND_DESIGN.md',
    'COMMUNICATION_PLAN.md',
    'QUALITY_PLAN.md',
    'RISK_REGISTER.md',
    'REQUIREMENTS.md',
    'PROJECT_CHARTER.md',
    'ISSUE_ANALYSIS.md',
    'SECURITY_HARDENING.md',
    'TEST_STRATEGY.md',
    'RUNBOOK.md'
)

Write-Host "=== 移动文档到 docs/ 目录 ==="
foreach ($file in $docFiles) {
    $src = Join-Path $rootDir $file
    $dst = Join-Path $docsDir $file
    if (Test-Path $src) {
        Move-Item $src $dst -Force
        Write-Host "已移动: $file -> docs/"
    } else {
        Write-Host "不存在 (跳过): $file"
    }
}
Write-Host "=== 步骤 2 完成 ==="