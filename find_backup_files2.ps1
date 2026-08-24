# Check all files including hidden ones
$files = Get-ChildItem -Recurse -File -Force | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -or 
    $_.Name -match '~$' -or
    $_.Name -match '\.bak-'
}
$files | Select-Object FullName, LastWriteTime