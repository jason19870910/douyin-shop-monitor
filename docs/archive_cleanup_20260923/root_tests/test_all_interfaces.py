import sys
sys.path.insert(0, '/app')
from services.fetcher import _fetch_products_from_api, _fetch_orders_from_api, _fetch_creator_works_from_api, _fetch_creators_from_api

print('products', len(_fetch_products_from_api()))
print('orders', len(_fetch_orders_from_api()))
print('creator_works', len(_fetch_creator_works_from_api()))
data = _fetch_creators_from_api()
print('creators keys', list(data.keys()) if isinstance(data, dict) else data)
