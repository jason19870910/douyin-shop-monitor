Get-ChildItem 'C:\Users\Administrator\Documents\trae_projects\douyin' -File -Recurse | Where-Object { 
    $_.Extension -match '\.(bak|old|~|dist|backup)$' -or 
    $_.Name -match '~$' -or
    $_.Name -match '\.bak-' -or
    $_.Name -match '\.old-' -or
    $_.Name -match '\.backup-' -or
    $_.Name -match '\.dist-'
} | Select-Object FullName