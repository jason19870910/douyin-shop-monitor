import os, requests
from config.settings import get_settings
s = get_settings()
cookies = s.FXG_COOKIES.split('; ')
# Convert to dict
cookie_dict = {}
for c in cookies:
    if '=' in c:
        k,v = c.split('=',1)
        cookie_dict[k]=v
url = f"{s.FXG_BASE_URL}/product/tproduct/list?shop_id={s.FXG_SHOP_ID}&page=1&size=10"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://fxg.jinritemai.com/',
}
try:
    r = requests.get(url, cookies=cookie_dict, headers=headers, timeout=10)
    print('STATUS', r.status_code)
    print('HEADERS', dict(r.headers))
    print('TEXT[:500]', r.text[:500])
except Exception as e:
    print('ERROR', e)
