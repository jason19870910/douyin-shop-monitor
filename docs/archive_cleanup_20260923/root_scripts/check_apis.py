from services.fetcher import _fetch_products_from_api, _fetch_creators_from_api, _fetch_creator_works_from_api, _fetch_orders_from_api
print('products', len(_fetch_products_from_api()))
print('creators', len(_fetch_creators_from_api()))
print('works', len(_fetch_creator_works_from_api()))
try:
    o = _fetch_orders_from_api()
    print('orders', len(o))
except Exception as e:
    print('orders error', e)
