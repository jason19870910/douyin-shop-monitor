from services.fetcher import Config, get_creator_cookies
import requests
url = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
headers = Config.COMMON_HEADERS.copy()
headers['Content-Type']='application/json'
r = requests.post(url, headers=headers, json={"recent_days":7}, cookies=get_creator_cookies(), timeout=30)
print(r.status_code)
print(r.json().get('status_code'))
