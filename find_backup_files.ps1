# Use Get-ChildItem with filter for the extensions
$files = Get-ChildItem -Recurse -File | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -or 
    $_.Name -match '~$'
}
$files | Select-Object FullName, LastWriteTime