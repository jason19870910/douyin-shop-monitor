import sys
sys.path.insert(0, '/app')
from services.fetcher import _fetch_orders_from_api
try:
    data = _fetch_orders_from_api()
    print('count', len(data))
    print(data[:1])
except Exception as e:
    print('error', e)
