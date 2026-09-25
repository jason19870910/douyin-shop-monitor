import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("HOMEPAGE_URL")
cookie = os.getenv("COOKIE")
headers = {
    "accept": "application/json",
    "cookie": cookie,
    "referer": "https://fxg.jinritemai.com/ffa/mshop/homepage/index",
    "user-agent": "Mozilla/5.0"
}
r = requests.get(url, headers=headers, timeout=10)
j = r.json()
cards = j['data']['lay_out_data'][1]['cards']
print("cards at index 1:")
print(json.dumps(cards, indent=2, ensure_ascii=False))
