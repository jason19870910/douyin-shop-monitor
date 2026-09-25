from services.fetcher import _fetch_products_from_api
import json, traceback
try:
    d = _fetch_products_from_api()
    print("COUNT", len(d))
    print(json.dumps(d[:2], ensure_ascii=False))
except Exception as e:
    print("ERROR", e)
    traceback.print_exc()
