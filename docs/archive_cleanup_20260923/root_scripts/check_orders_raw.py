from services.fetcher import Config, _read_secret
from douyin_sign import sign_request
import requests
endpoint = f'{Config.FXG_BASE_URL}/api/order/searchlist'
base_params = {
    'page': 0,
    'pageSize': 10,
    'order_by': 'create_time',
    'order': 'desc',
    'tab': 'all',
    'appid': 1,
    '_bid': 'ffa_order',
    'aid': '4272',
    '_lid': '843863276461',
}
existing_tokens = {
    '__token': _read_secret('token', '__TOKEN'),
    'msToken': _read_secret('ms_token', 'MS_TOKEN'),
    'verifyFp': _read_secret('verify_fp', 'verifyFp'),
    'fp': _read_secret('fp', 'fp'),
}
sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
params = {**base_params, **sign_params}
print('URL', endpoint)
print('PARAMS', params)
resp = requests.get(endpoint, headers=Config.COMMON_HEADERS, params=params, timeout=30)
print('STATUS', resp.status_code)
print('TEXT', resp.text[:2000])
