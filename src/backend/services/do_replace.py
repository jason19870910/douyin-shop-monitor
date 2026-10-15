import os
content = open('c:/Users/Administrator/Documents/trae_projects/douyin/src/backend/services/fetcher.py', 'r', encoding='utf-8').read()
old = content[content.find('Compliance Fetching'):content.find('Alert Checking')]
print('OLD LEN:', len(old))
print('OLD:', repr(old))

new = open('c:/Users/Administrator/Documents/trae_projects/douyin/src/backend/services/new_code.txt', 'r', encoding='utf-8').read()
print('NEW LEN:', len(new))

if old in content:
    content = content.replace(old, new)
    with open('c:/Users/Administrator/Documents/trae_projects/douyin/src/backend/services/fetcher.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Replaced fetch_and_check_compliance function')
else:
    print('ERROR: Old code not found')