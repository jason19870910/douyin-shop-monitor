import requests
original_get = requests.get

def debug_get(url, params=None, headers=None, cookies=None, timeout=None):
    resp = original_get(url, params=params, headers=headers, cookies=cookies, timeout=timeout)
    print("=== REQUEST ===")
    print("URL:", url)
    print("PARAMS:", params)
    print("STATUS:", resp.status_code)
    try:
        text = resp.text
    except Exception:
        text = "<no text>"
    print("TEXT_HEAD:", text[:2000])
    try:
        j = resp.json()
        print("JSON:", j)
    except Exception as e:
        print("JSON parse error:", e)
    return resp

requests.get = debug_get

from services.fetcher import _fetch_products_from_api
try:
    d = _fetch_products_from_api()
    print("COUNT", len(d))
except Exception as e:
    print("EXCEPTION", e)
