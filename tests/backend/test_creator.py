#!/usr/bin/env python3
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('CREATOR_URL', 'https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard')
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/json',
    'cookie': os.getenv('CREATOR_COOKIE'),
    'origin': 'https://creator.douyin.com',
    'priority': 'u=1, i',
    'referer': 'https://creator.douyin.com/creator-micro/data-center/operation',
    'sec-ch-ua': '"Not A(Brand)";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': 'Windows',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    'x-secsdk-csrf-token': os.getenv('CREATOR_CSRF_TOKEN')
}
try:
    r = requests.post(url, headers=headers, json={'recent_days': 1}, timeout=15)
    print('Status:', r.status_code)
    print('Response headers:', dict(r.headers))
    try:
        data = r.json()
        print('Response json:')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print('Raw text:', r.text[:2000])
        print('JSON parse error:', e)
except Exception as e:
    print('Error:', e)
