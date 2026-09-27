from services.fetcher import Config, _read_secret, get_fxg_cookies
from douyin_sign import sign_request
import requests
endpoint = f'{Config.FXG_BASE_URL}/product/tproduct/list'
base_params = {
    'page': 0,
    'pageSize': 20,
    'draft_status': 0,
    'comment_percent': '',
    'group_id': '',
    'sku_type': '',
    'tab': 'onSale',
    'business_type': 4,
    'is_online': 1,
    'not_for_sale_search_type': 1,
    'from_mng': 1,
    'check_status': 3,
    'status': 0,
    'supply_status': '',
    'need_auto_rectify_info': 'true',
    'need_pay_no_stock_skus': 'true',
    'order_field': 'audit_time',
    'sort': 'desc',
    'appid': 1,
    '_bid': 'ffa_goods',
    'aid': Config.FXG_SHOP_ID,
    '_lid': '829906029528',
}
existing_tokens = {
    '__token': _read_secret('token','__TOKEN'),
    'msToken': _read_secret('ms_token','MS_TOKEN'),
    'verifyFp': _read_secret('verify_fp','verifyFp'),
    'fp': _read_secret('fp','fp'),
}
sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
params = {**base_params, **sign_params}
cookies = get_fxg_cookies()
print('URL', endpoint)
print('COOKIES keys', list(cookies.keys())[:10])
resp = requests.get(endpoint, headers=Config.COMMON_HEADERS, params=params, cookies=cookies, timeout=30)
print('STATUS', resp.status_code)
print('TEXT', resp.text[:2000])
