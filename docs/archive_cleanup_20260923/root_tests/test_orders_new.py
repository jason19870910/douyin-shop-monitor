import sys
sys.path.insert(0, '/app')
from services.fetcher import _fetch_orders_from_api
data = _fetch_orders_from_api()
print('count', len(data))
if data:
    print(data[0].keys())
