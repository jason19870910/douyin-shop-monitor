from services.fetcher import Config, get_creator_cookies
import requests
url = Config.CREATOR_WORK_LIST_URL
headers = Config.COMMON_HEADERS.copy()
headers['Referer']='https://creator.douyin.com/creator-micro/content/manage'
params = {'max_cursor':'0','scene':'star_atlas','device_platform':'android','aid':'1128'}
r = requests.get(url, headers=headers, params=params, cookies=get_creator_cookies(), timeout=30)
print(r.status_code)
print(r.json().get('status_code'))
