import sys
sys.path.insert(0, '/app')
import os
from services.fetcher import Config
import requests
import json

endpoint = f"{Config.FXG_BASE_URL}/product/tproduct/list"
params = {'page':0,'pageSize':1}
cookie_str = os.getenv('FXG_COOKIES','')
headers = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/product/tproduct/list',
    'Cookie': cookie_str,
}
resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
print('status', resp.status_code)
print('headers', resp.headers.get('content-type'))
try:
    result = resp.json()
    print('result keys', list(result.keys())[:10])
    print('result', json.dumps(result, ensure_ascii=False)[:1000])
except Exception as e:
    print('json error', e)
    print(resp.text[:500])
