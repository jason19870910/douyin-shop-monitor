from services.fetcher import _fetch_orders_from_api
import json
o=_fetch_orders_from_api()
print('count', len(o))
print(json.dumps(o[:2], ensure_ascii=False)[:800])
