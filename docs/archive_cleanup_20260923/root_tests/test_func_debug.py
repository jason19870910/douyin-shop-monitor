import sys
sys.path.insert(0, '/app')
from services.fetcher import Config
import os
import requests

endpoint = f"{Config.FXG_BASE_URL}/product/tproduct/list"
params = {'page':0,'pageSize':1}
cookie_str = os.getenv('FXG_COOKIES','')
headers = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/product/tproduct/list',
    'Cookie': cookie_str,
}
resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
result = resp.json()
print('result data type', type(result.get('data')))
import json
print(json.dumps(result.get('data')[0], ensure_ascii=False)[:200])
