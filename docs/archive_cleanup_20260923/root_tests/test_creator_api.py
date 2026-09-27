from services.fetcher import Config, get_creator_cookies
import requests
url = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
headers = Config.COMMON_HEADERS.copy()
headers['Content-Type'] = 'application/json'
cookies = get_creator_cookies()
payload = {"recent_days":7}
resp = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=30)
print('STATUS', resp.status_code)
try:
    print(resp.json())
except:
    print(resp.text[:500])
