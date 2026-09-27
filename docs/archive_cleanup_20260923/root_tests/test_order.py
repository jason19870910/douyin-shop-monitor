from services.fetcher import _fetch_orders_from_api
o = _fetch_orders_from_api()
print('count', len(o))
