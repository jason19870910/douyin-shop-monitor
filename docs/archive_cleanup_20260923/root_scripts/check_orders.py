from services.fetcher import _fetch_orders_from_api
import json
d = _fetch_orders_from_api()
print("COUNT", len(d))
print(json.dumps(d[:2], ensure_ascii=False))
