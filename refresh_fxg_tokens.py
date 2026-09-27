#!/usr/bin/env python3
import os, re
import requests

SECRETS_DIR = '/opt/douyin-platform/secrets'
COOKIE_FILE = os.path.join(SECRETS_DIR, 'fxg_cookies.txt')
TOKEN_FILE = os.path.join(SECRETS_DIR, 'token.txt')

def read_cookies():
    if os.path.exists(COOKIE_FILE):
        return open(COOKIE_FILE).read().strip()
    return ''

def save_token(tok):
    open(TOKEN_FILE,'w').write(tok)

def fetch_token():
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36',
        'Referer':'https://fxg.jinritemai.com/',
    }
    try:
        r = requests.get('https://fxg.jinritemai.com/', headers=headers, timeout=15)
        m = re.search(r"__token['\"]\s*:\s*['\"]([^'\"]+)", r.text)
        if m:
            return m.group(1)
    except Exception as e:
        print('fetch error', e)
    return None

if __name__ == '__main__':
    new_cookies = os.getenv('FXG_NEW_COOKIES')
    if new_cookies:
        open(COOKIE_FILE,'w').write(new_cookies)
        print('updated cookies')
    tok = fetch_token()
    if tok:
        save_token(tok)
        print('updated token')
    else:
        print('token unchanged')
