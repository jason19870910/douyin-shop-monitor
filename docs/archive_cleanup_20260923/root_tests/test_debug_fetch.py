import sys
sys.path.insert(0, '/app')
import os
from services.fetcher import Config
import requests
import json

endpoint = f"{Config.FXG_BASE_URL}/product/tproduct/list"
params = {'page':0,'pageSize':1}
cookie_str = os.getenv('FXG_COOKIES','')
print('cookie_len', len(cookie_str))
headers = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/product/tproduct/list',
    'Cookie': cookie_str,
}
resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
print('status', resp.status_code)
result = resp.json()
print('keys', result.keys())
data_block = result.get('data')
print('data_block type', type(data_block))
print('data_block len' if isinstance(data_block, list) else 'not list')
if isinstance(data_block, list):
    print('first item keys', list(data_block[0].keys())[:5] if data_block else 'empty')
