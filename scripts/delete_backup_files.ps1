# Delete all backup files except in the new backup folder
$newBackupFolder = 'douyin_backup_20260824_1851'

$files = Get-ChildItem -Recurse | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -and 
    $_.FullName -notmatch $newBackupFolder
}

$files | Select-Object FullName, LastWriteTime

if ($files.Count -gt 0) {
    Write-Host "Deleting $($files.Count) backup files..."
    $files | Remove-Item -Force
    Write-Host "Done."
} else {
    Write-Host "No backup files to delete."
}