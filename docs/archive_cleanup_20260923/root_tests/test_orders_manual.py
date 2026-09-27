import sys
sys.path.insert(0, '/app')
import os
from services.fetcher import Config
import requests
endpoint = f"{Config.FXG_BASE_URL}/api/order/searchlist"
params = {'page':0,'pageSize':10}
cookie_str = os.getenv('FXG_COOKIES','')
headers = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/',
    'Cookie': cookie_str,
}
resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
print('status', resp.status_code)
try:
    result = resp.json()
    print('code', result.get('code'))
    print('keys', list(result.keys()))
    data = result.get('data', {})
    print('data keys', data.keys() if isinstance(data, dict) else 'not dict')
except Exception as e:
    print('error', e)
