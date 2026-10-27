#!/usr/bin/env python3
import sys
import re

cookie_file = sys.argv[1]
env_path = '/opt/douyin-platform/config/.env'

with open(cookie_file, 'r', encoding='utf-8') as f:
    new_cookie = f.read().strip()

with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = re.sub(
    r'^FXG_COOKIES=.*$',
    f'FXG_COOKIES={new_cookie}',
    content,
    flags=re.MULTILINE
)

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("FXG_COOKIES updated successfully")
