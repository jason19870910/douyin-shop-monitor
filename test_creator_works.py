from services.fetcher import Config, get_creator_cookies
import requests
url = f'{Config.CREATOR_WORK_LIST_URL}'
headers = Config.COMMON_HEADERS.copy()
headers['Referer'] = 'https://creator.douyin.com/creator-micro/content/manage'
cookies = get_creator_cookies()
params = {'max_cursor':'0','scene':'star_atlas','device_platform':'android','aid':'1128'}
resp = requests.get(url, headers=headers, params=params, cookies=cookies, timeout=30)
print('STATUS', resp.status_code)
try:
    j = resp.json()
    print('code', j.get('code'), 'data keys', list(j.get('data',{}).keys()))
except:
    print(resp.text[:500])
