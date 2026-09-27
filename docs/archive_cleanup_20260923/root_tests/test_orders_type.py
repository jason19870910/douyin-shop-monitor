import sys
sys.path.insert(0, '/app')
import os
from services.fetcher import Config
import requests
endpoint = f'{Config.FXG_BASE_URL}/api/order/searchlist'
params = {'page':0,'pageSize':10,'order_by':'create_time','order':'desc','tab':'all','appid':1,'_bid':'ffa_order','aid':Config.FXG_ORDER_AID,'_lid':Config.FXG_ORDER_LID}
cookie_str = os.getenv('FXG_COOKIES','')
headers={'User-Agent':Config.USER_AGENT,'Referer':'https://fxg.jinritemai.com/','Cookie':cookie_str}
resp = requests.get(endpoint, headers=headers, params=params, timeout=30)
result = resp.json()
print(type(result))
print(isinstance(result, list))
print(isinstance(result, dict))
