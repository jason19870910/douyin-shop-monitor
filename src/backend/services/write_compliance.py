import os
content = open('c:/Users/Administrator/Documents/trae_projects/douyin/src/backend/services/fetcher.py', 'r', encoding='utf-8').read()
old = content[content.find('Compliance Fetching'):content.find('Alert Checking')]
print('OLD LEN:', len(old))