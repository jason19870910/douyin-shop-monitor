import requests
original = requests.get
def dbg(url, params=None, **kw):
    print('URL', url)
    print('PARAMS', params)
    r = original(url, params=params, **kw)
    print('STATUS', r.status_code)
    j = r.json()
    print('code', j.get('code'), 'data keys', j.get('data', {}).keys())
    print('orders count', len(j.get('data', {}).get('orders', [])))
    return r
requests.get = dbg
from services.fetcher import _fetch_orders_from_api
orders = _fetch_orders_from_api()
print('Fetched', len(orders))
