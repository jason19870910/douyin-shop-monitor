import requests
original = requests.get
def dbg(url, params=None, **kw):
    print("URL", url)
    print("PARAMS", params)
    r = original(url, params=params, **kw)
    print("STATUS", r.status_code)
    j = r.json()
    print("code", j.get('code'), "total", j.get('total'), "data len", len(j.get('data', [])))
    return r
requests.get = dbg
from services.fetcher import Config
# manually build params
base_params = {
    'page':1,
    'pageSize':20,
    'appid':1,
    '_bid':'ffa_product',
    'aid':Config.FXG_SHOP_ID,
    '_lid':Config.FXG_LOG_ID,
    '__token':'fc3986f3634aaa8aded2fa0d220ebd31',
    'msToken':'TqwZjJB-WtRNFBJhj5Q30jdXHm85xicJcWt9qdfm7hrzbmmQBv76Yy_Z_TJiNlqcP6t0w0dLKnrlxIQptbchLtcYuczC3PyRHT3xPkZmEFfrzFk3mouwC4eZgm_EYNMpJeGFH1IMW-6aN11e9PVUahSlY9hTMtbaKMc_gcWZe0Il4Q==',
    'verifyFp':'verify_muawvz3s_IQqihHkB_Mb9i_4kMg_9cIv_IUimkTcWsWmw',
    'fp':'verify_muawvz3s_IQqihHkB_Mb9i_4kMg_9cIv_IUimkTcWsWmw',
}
url = f"{Config.FXG_BASE_URL}/product/tproduct/list"
requests.get(url, params=base_params, timeout=15)
