from services.fetcher import Config, _read_secret, get_fxg_cookies
from douyin_sign import sign_request
import requests
endpoint = f'{Config.FXG_BASE_URL}/products/stats'
base_params = {'appid':1,'_bid':'ffa_goods','aid':Config.FXG_SHOP_ID}
existing_tokens = {'__token': _read_secret('token','__TOKEN'),'msToken': _read_secret('ms_token','MS_TOKEN'),'verifyFp': _read_secret('verify_fp','verifyFp'),'fp': _read_secret('fp','fp')}
sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
params = {**base_params, **sign_params}
headers = Config.COMMON_HEADERS.copy()
headers['Referer']='https://fxg.jinritemai.com/'
headers['Origin']='https://fxg.jinritemai.com'
r = requests.get(endpoint, headers=headers, params=params, cookies=get_fxg_cookies(), timeout=30)
print(r.status_code)
print(r.text[:300])
