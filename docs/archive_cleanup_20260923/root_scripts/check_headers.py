import os
import requests
from config.settings import Config
from services.fetcher import get_fxg_cookies

e = f"{Config.FXG_BASE_URL}/product/tproduct/list"
p = {"page":0,"pageSize":1}
h = {"User-Agent":Config.USER_AGENT,"Referer":"https://fxg.jinritemai.com/product/tproduct/list"}
r = requests.get(e,params=p,headers=h,cookies=get_fxg_cookies(),timeout=10)
print(r.status_code)
print(dict(r.headers))
print(r.json().get('code'), r.json().get('st'))
