import sys
sys.path.insert(0, "/app")
from config import Config
from services.fetcher import _read_secret, parse_cookies, _request
import requests
import json

# ========== 1. 商品统计 ==========
fxg_cookie_str = _read_secret('fxg_cookies', 'FXG_COOKIES')
fxg_cookies = parse_cookies(fxg_cookie_str)
fxg_headers = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/product/tproduct/list',
    'Accept': 'application/json, text/plain, */*',
}
endpoint = f'{Config.FXG_BASE_URL}/product/tproduct/aggsProductCount'
params = {'tab': 'onSale', 'appid': 1, '_bid': 'ffa_product', 'aid': Config.FXG_SHOP_ID}
r = requests.get(endpoint, params=params, headers=fxg_headers, cookies=fxg_cookies, timeout=30)
print("=" * 60)
print("1. 商品统计 /product/tproduct/aggsProductCount")
print("=" * 60)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))

# ========== 2. 商品列表 ==========
endpoint = f'{Config.FXG_BASE_URL}/product/tproduct/list'
params = {'page': 1, 'pageSize': 20, 'tab': 'onSale', 'appid': 1, '_bid': 'ffa_product', 'aid': Config.FXG_SHOP_ID, '_lid': Config.FXG_PRODUCT_LID}
r = requests.get(endpoint, params=params, headers=fxg_headers, cookies=fxg_cookies, timeout=30)
print("\n" + "=" * 60)
print("2. 商品列表 /product/tproduct/list")
print("=" * 60)
data = r.json()
print(f"Code: {data.get('code')}")
# 响应结构：data 是列表
if isinstance(data.get('data'), list):
    print(f"List count: {len(data['data'])}")
    if data['data']:
        print("First item keys:", list(data['data'][0].keys()))
else:
    print(f"Total: {data.get('data', {}).get('total')}")
    print(f"List count: {len(data.get('data', {}).get('list', []))}")
    if data.get('data', {}).get('list'):
        print("First item keys:", list(data['data']['list'][0].keys()))

# ========== 3. 订单统计 ==========
fxg_headers_order = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/ffa/morder/order/list',
    'Accept': 'application/json, text/plain, */*',
}
endpoint = f'{Config.FXG_BASE_URL}/api/order/tabcnt'
params = {'tabcnt_version': 'v1', 'tab': 'all', 'appid': 1, '_bid': 'ffa_order', 'aid': Config.FXG_ORDER_AID, '_lid': Config.FXG_ORDER_LID}
r = requests.get(endpoint, params=params, headers=fxg_headers_order, cookies=fxg_cookies, timeout=30)
print("\n" + "=" * 60)
print("3. 订单统计 /api/order/tabcnt")
print("=" * 60)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))

# ========== 4. 订单列表 (skip_sign) ==========
fxg_headers_order_list = {
    'User-Agent': Config.USER_AGENT,
    'Referer': 'https://fxg.jinritemai.com/ffa/order',
    'Accept': 'application/json, text/plain, */*',
}
endpoint = f'{Config.FXG_BASE_URL}/api/order/searchlist'
params = {'page': 0, 'pageSize': 10, 'order_by': 'create_time', 'order': 'desc', 'tab': 'all', 'appid': 1, '_bid': 'ffa_order', 'aid': Config.FXG_ORDER_AID, '_lid': '606316310312'}
# 手动加上长效参数
params['__token'] = Config.TOKEN
params['verifyFp'] = Config.VERIFY_FP
params['fp'] = Config.FP
result = _request(endpoint, params=params, headers=fxg_headers_order_list, cookies=fxg_cookies, skip_sign=True)
print("\n" + "=" * 60)
print("4. 订单列表 /api/order/searchlist (skip_sign=True)")
print("=" * 60)
if isinstance(result, dict) and result.get('code') == 0:
    data = result.get('data', [])
    print(f"Orders count: {len(data)}")
    if data:
        print("First order keys:", list(data[0].keys()))
        print(json.dumps(data[0], ensure_ascii=False, indent=2)[:2000])
else:
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])

# ========== 5. 创作者概览 ==========
creator_cookie_str = _read_secret('creator_cookies', 'CREATOR_COOKIES')
creator_cookies = parse_cookies(creator_cookie_str)
creator_headers = {'User-Agent': Config.USER_AGENT, 'Referer': 'https://creator.douyin.com/', 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json'}
endpoint = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
r = requests.post(endpoint, headers=creator_headers, json={'recent_days': 7}, cookies=creator_cookies, timeout=15)
print("\n" + "=" * 60)
print("5. 创作者概览 /janus/douyin/creator/data/overview/dashboard")
print("=" * 60)
data = r.json()
print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])

# ========== 6. 创作者作品 ==========
endpoint = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/pc/work_list'
params = {'status': '0', 'count': '12', 'max_cursor': '0', 'scene': 'star_atlas', 'device_platform': 'android', 'aid': Config.CREATOR_WORK_AID}
r = requests.get(endpoint, params=params, headers=creator_headers, cookies=creator_cookies, timeout=15)
print("\n" + "=" * 60)
print("6. 创作者作品 /janus/douyin/creator/pc/work_list")
print("=" * 60)
data = r.json()
print(f"Code: {data.get('status_code')}")
print(f"Total: {data.get('total')}")
aweme_list = data.get('aweme_list', [])
print(f"Works count: {len(aweme_list)}")
if aweme_list:
    print("First work keys:", list(aweme_list[0].keys()))
    print("Statistics keys:", list(aweme_list[0].get('statistics', {}).keys()))
    print("Video keys:", list(aweme_list[0].get('video', {}).keys()))
    print("Author keys:", list(aweme_list[0].get('author', {}).keys()))