import requests
from services.fetcher import Config, _read_secret
# reuse fetcher logic to build params
def get_secret(name, env_name, default):
    import os
    if os.path.exists(f'/run/secrets/{name}'):
        return open(f'/run/secrets/{name}').read().strip()
    return os.getenv(env_name, default)

__token = get_secret('token','__TOKEN','')
msToken = get_secret('ms_token','MS_TOKEN','')
verifyFp = get_secret('verify_fp','verifyFp','')
fp = get_secret('fp','fp','')
params = {
    'page':1,
    'pageSize':100,
    'appid':1,
    '_bid':'ffa_product',
    'aid':Config.FXG_SHOP_ID,
    '_lid':Config.FXG_LOG_ID,
    '__token':__token,
    'msToken':msToken,
    'verifyFp':verifyFp,
    'fp':fp,
}
url = f"{Config.FXG_BASE_URL}/product/tproduct/listBanner"
r = requests.get(url, params=params, timeout=15, cookies={'cookie':'test'})
print('STATUS', r.status_code)
print(r.json()[:500])
