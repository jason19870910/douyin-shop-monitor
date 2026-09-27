import sys
sys.path.insert(0, '/app')
from services.fetcher import _fetch_products_from_api
data = _fetch_products_from_api()
print('count', len(data))
