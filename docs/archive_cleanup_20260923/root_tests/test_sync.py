import sys
sys.path.insert(0, '/app')
from services.fetcher import fetch_and_store_products
res = fetch_and_store_products()
print(res)
