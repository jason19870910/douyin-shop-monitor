import sys
sys.path.insert(0, '/app')
import os
from services.fetcher import Config
import requests
import json
endpoint = Config.CREATOR_WORK_LIST_URL
params = {'status':'0','count':'12','max_cursor':'0','scene':'star_atlas','device_platform':'android','aid':Config.CREATOR_WORK_AID}
cookie_str = os.getenv('CREATOR_COOKIES','')
headers={'User-Agent':Config.USER_AGENT,'Referer':'https://creator.douyin.com/creator-micro/content/manage','Cookie':cookie_str}
resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
result = resp.json()
print(json.dumps(result, ensure_ascii=False)[:2000])
