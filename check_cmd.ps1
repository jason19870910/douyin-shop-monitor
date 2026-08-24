# Use cmd dir command to check
$output = cmd /c "dir /s /b *.bak *.old *~ *.dist *.backup 2>nul"
$output