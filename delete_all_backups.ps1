# Delete all backup files including those with hyphenated names like .bak-YYYYMMDD-HHMMSS
$files = Get-ChildItem -Recurse -File -Force | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -or 
    $_.Name -match '~$' -or
    $_.Name -match '\.bak-' -or
    $_.Name -match '\.old-' -or
    $_.Name -match '\.backup-' -or
    $_.Name -match '\.dist-'
}

$files | Select-Object FullName

if ($files.Count -gt 0) {
    Write-Host "Deleting $($files.Count) backup files..."
    $files | Remove-Item -Force
    Write-Host "Done."
} else {
    Write-Host "No backup files to delete."
}