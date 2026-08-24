$dest = 'c:\Users\Administrator\Documents\trae_projects\douyin_backup_' + (Get-Date -Format 'yyyyMMdd_HHmm')
Write-Host "Backup destination: $dest"
# Exclude the backup folder itself to avoid recursive self-copy
$exclude = @("douyin_backup_*")
$items = Get-ChildItem -Path . | Where-Object { $_.Name -notmatch '^douyin_backup_\d{8}_\d{4}$' }
foreach ($item in $items) {
    Copy-Item -Path $item.FullName -Destination $dest -Recurse -Force
}