from services.fetcher import Config, _read_secret, get_fxg_cookies
from douyin_sign import sign_request
import requests
endpoint = f'{Config.FXG_BASE_URL}/product/tproduct/list'
base_params = {'page':0,'pageSize':20,'draft_status':0,'tab':'onSale','business_type':4,'is_online':1,'appid':1,'_bid':'ffa_goods','aid':Config.FXG_SHOP_ID,'_lid':'829906029528'}
existing_tokens = {'__token': _read_secret('token','__TOKEN'),'msToken': _read_secret('ms_token','MS_TOKEN'),'verifyFp': _read_secret('verify_fp','verifyFp'),'fp': _read_secret('fp','fp')}
sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
params = {**base_params, **sign_params}
r = requests.get(endpoint, headers=Config.COMMON_HEADERS, params=params, cookies=get_fxg_cookies(), timeout=30)
print(r.status_code)
import json
try:
    j = r.json()
    print(j.get('code'), j.get('total'))
except:
    print(r.text[:200])
