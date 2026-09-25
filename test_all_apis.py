from services.fetcher import Config, _read_secret, get_fxg_cookies, get_creator_cookies
from douyin_sign import sign_request
import requests
import json

def test_fxg(endpoint, base_params, cookies, name):
    existing_tokens = {
        '__token': _read_secret('token','__TOKEN'),
        'msToken': _read_secret('ms_token','MS_TOKEN'),
        'verifyFp': _read_secret('verify_fp','verifyFp'),
        'fp': _read_secret('fp','fp'),
    }
    sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
    params = {**base_params, **sign_params}
    headers = Config.COMMON_HEADERS.copy()
    try:
        resp = requests.get(endpoint, headers=headers, params=params, cookies=cookies, timeout=30)
        txt = resp.text[:500]
        try:
            data = resp.json()
            code = data.get('code') or data.get('st')
        except:
            code = None
        print(name, resp.status_code, code, txt[:200])
    except Exception as e:
        print(name, 'ERR', e)

cookies = get_fxg_cookies()
# product
test_fxg(f'{Config.FXG_BASE_URL}/product/tproduct/list', {
    'page':0,'pageSize':20,'draft_status':0,'tab':'onSale','business_type':4,'is_online':1,'appid':1,'_bid':'ffa_goods','aid':Config.FXG_SHOP_ID,'_lid':'829906029528'
}, cookies, 'product')

# orders
test_fxg(f'{Config.FXG_BASE_URL}/api/order/searchlist', {
    'page':0,'pageSize':10,'order_by':'create_time','order':'desc','tab':'all','appid':1,'_bid':'ffa_order','aid':'4272','_lid':'843863276461'
}, cookies, 'orders')
