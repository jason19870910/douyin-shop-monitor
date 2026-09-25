import requests
original_get = requests.get
def debug_get(url, params=None, headers=None, cookies=None, timeout=None):
    print("URL", url)
    print("PARAMS", params)
    resp = original_get(url, params=params, headers=headers, cookies=cookies, timeout=timeout)
    print("STATUS", resp.status_code)
    try:
        j = resp.json()
        print("JSON", j)
    except Exception as e:
        print("JSON error", e)
    return resp
requests.get = debug_get

from services.fetcher import Config
from services.fetcher import _read_secret
# manually call
url = f"{Config.FXG_BASE_URL}/product/tproduct/listBanner"
params = {
    'page':1,'pageSize':100,'appid':1,'_bid':'ffa_product','aid':Config.FXG_SHOP_ID,'_lid':Config.FXG_LOG_ID
}
# copy other params from fetcher
# simplified
print("Testing banner")
