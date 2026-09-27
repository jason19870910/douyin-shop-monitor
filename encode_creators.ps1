$content = Get-Content 'c:\Users\Administrator\Documents\trae_projects\douyin\src\backend\blueprints\creators.py' -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$encoded = [Convert]::ToBase64String($bytes)
$encoded | Set-Content 'c:\Users\Administrator\Documents\trae_projects\douyin\creators_b64.txt' -NoNewline