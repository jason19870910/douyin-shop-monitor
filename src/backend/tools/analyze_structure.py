import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

HOMEPAGE_URL = os.getenv("HOMEPAGE_URL")
PRODUCT_URL = os.getenv("PRODUCT_URL")
COOKIE = os.getenv("COOKIE")

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cookie": COOKIE,
    "priority": "u=1, i",
    "referer": "https://fxg.jinritemai.com/ffa/mshop/homepage/index",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}

def show_structure(url, name):
    print(f"\n=== {name} ===")
    r = requests.get(url, headers=HEADERS, timeout=10)
    j = r.json()
    print("top keys:", list(j.keys()))
    if 'data' in j:
        d = j['data']
        if isinstance(d, dict):
            print("data keys:", list(d.keys()))
            # show todo_list path?
            if 'lay_out_data' in d:
                print(f"lay_out_data length: {len(d['lay_out_data'])}")
                for idx, item in enumerate(d['lay_out_data']):
                    cards = item.get('cards', [])
                    print(f"  index {idx}: layout_id={item.get('layout_id')}, cards count={len(cards)}")
                    for c in cards:
                        print(f"    card_type={c.get('card_type')}, card_name={c.get('card_name')}")
        else:
            print("data is not dict:", type(d))

show_structure(HOMEPAGE_URL, "HOMEPAGE_URL")
show_structure(PRODUCT_URL, "PRODUCT_URL")
