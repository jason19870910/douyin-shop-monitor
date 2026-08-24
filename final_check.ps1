Get-ChildItem -Recurse -File | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -or 
    $_.Name -match '~$' -or
    $_.Name -match '\.bak-' -or
    $_.Name -match '\.old-' -or
    $_.Name -match '\.backup-' -or
    $_.Name -match '\.dist-'
} | Select-Object FullName