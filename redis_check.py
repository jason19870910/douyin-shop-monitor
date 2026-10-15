import redis
import sys

r = redis.Redis(host='redis', port=6379, decode_responses=True)

keys_to_check = [
    'douyin:monitor:products',
    'douyin:monitor:orders', 
    'douyin:monitor:creators',
    'douyin:monitor:creator_works',
    'douyin:monitor:last_update'
]

print("=== Redis Data Check ===")
for key in keys_to_check:
    val = r.get(key)
    if val:
        if isinstance(val, list):
            print(f"{key}: list({len(val)} items)")
            if val:
                print(f"  first item keys: {list(val[0].keys())}")
        else:
            print(f"{key}: {type(val).__name__} = {str(val)[:100]}")
    else:
        print(f"{key}: EMPTY")

print()
print("=== Sync History ===")
sync_hist = r.lrange('douyin:monitor:sync_history', 0, 2)
for entry in sync_hist or []:
    print(f"  {entry.get('timestamp', '?')}: {entry.get('status', '?')}, duration={entry.get('duration_ms', '?')}ms")

print()
print("=== Last Update ===")
last_update = r.get('douyin:monitor:last_update')
print(f"  {last_update}")