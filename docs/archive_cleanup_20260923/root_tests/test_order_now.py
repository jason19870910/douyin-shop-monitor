from services.fetcher import _fetch_orders_from_api
try:
    orders = _fetch_orders_from_api()
    print('orders count', len(orders))
    print(orders[:1])
except Exception as e:
    print('error', e)
