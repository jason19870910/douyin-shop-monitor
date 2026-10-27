#!/usr/bin/env python3
"""Diagnostic script for orders data issue on server."""
import os
import json
from pathlib import Path

print("=== Environment Variables ===")
for key in ['__TOKEN', 'TOKEN', 'VERIFY_FP', 'verifyFp', 'FP', 'fp', 'FXG_COOKIES', 'DEBUG', 'REDIS_HOST', 'DATA_DIR', 'FXG_BASE_URL', 'FXG_ORDER_AID', 'FXG_ORDER_LID', 'FXG_SHOP_ID']:
    val = os.getenv(key, '')
    if 'TOKEN' in key or 'COOKIE' in key or 'SECRET' in key or 'FP' in key:
        val = '[REDACTED]' if val else '(empty)'
    print(f"  {key} = {val}")

print("\n=== Data Files ===")
data_dir = Path(os.getenv('DATA_DIR', '/data'))
for fname in ['orders.json', 'sync_history.json', 'products.json', 'creators.json']:
    fpath = data_dir / fname
    if fpath.exists():
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"  {fname}: list with {len(data)} items")
            elif isinstance(data, dict):
                print(f"  {fname}: dict with keys {list(data.keys())[:10]}")
            else:
                print(f"  {fname}: {type(data).__name__}")
        except Exception as e:
            print(f"  {fname}: ERROR reading - {e}")
    else:
        print(f"  {fname}: NOT FOUND")

print("\n=== Redis Connectivity ===")
try:
    import redis
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)
    r.ping()
    orders = r.get('orders')
    print(f"  Redis connected. orders key: {'exists' if orders else 'missing'}")
    if orders:
        print(f"  orders data length: {len(orders)}")
except ImportError:
    print("  redis module not available")
except Exception as e:
    print(f"  Redis connection failed: {e}")

print("\n=== FXG API Test ===")
import requests
try:
    fxg_base = os.getenv('FXG_BASE_URL', 'https://fxg.jinritemai.com')
    token = os.getenv('__TOKEN', '') or os.getenv('TOKEN', '')
    verify_fp = os.getenv('verifyFp', '') or os.getenv('VERIFY_FP', '')
    fp = os.getenv('fp', '') or os.getenv('FP', '')

    params = {
        'page': 0,
        'pageSize': 10,
        'order_by': 'create_time',
        'order': 'desc',
        'tab': 'all',
        'appid': 1,
        '_bid': 'ffa_order',
        'aid': os.getenv('FXG_ORDER_AID', '4272'),
        '_lid': '606316310312',
    }
    if token:
        params['__token'] = token
    if verify_fp:
        params['verifyFp'] = verify_fp
    if fp:
        params['fp'] = fp

    cookie_str = os.getenv('FXG_COOKIES', '')
    cookies = {}
    if cookie_str:
        for pair in cookie_str.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://fxg.jinritemai.com/ffa/order',
        'Accept': 'application/json, text/plain, */*',
    }

    resp = requests.get(f'{fxg_base}/api/order/searchlist', params=params, headers=headers, cookies=cookies, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  URL: {resp.url[:200]}...")
    result = resp.json()
    data_block = result.get('data')
    if isinstance(data_block, list):
        print(f"  Orders count: {len(data_block)}")
    elif isinstance(data_block, dict):
        print(f"  Orders count: {len(data_block.get('orders', []))}")
    else:
        print(f"  Response preview: {str(result)[:500]}")
except Exception as e:
    print(f"  API call failed: {type(e).__name__}: {e}")
