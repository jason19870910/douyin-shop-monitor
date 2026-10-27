import os, json, glob, subprocess

print("=== which python/gunicorn ===")
for cmd in [['which','python3'], ['which','gunicorn']]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  {' '.join(cmd)}: {r.stdout.strip()} | {r.stderr.strip()}")

print("=== /usr/local/bin/python* ===")
for p in glob.glob('/usr/local/bin/python*'):
    print("  ", p)

print("=== gunicorn master environ (FXG/redis-related) ===")
try:
    with open('/proc/1643689/environ', 'rb') as f:
        envblock = f.read()
    env = {}
    for part in envblock.split(b'\x00'):
        if not part:
            continue
        try:
            k, v = part.decode('utf-8', 'replace').split('=', 1)
            env[k] = v
        except ValueError:
            pass
    for k in sorted(env):
        kl = k.lower()
        if any(s in kl for s in ['fxg','token','cookie','verify','redis','debug','skip','data','schedule','celery']):
            print(f"  {k}={env[k][:100]}")
    if not any(any(s in k.lower() for s in ['fxg','token','cookie','verify','redis']) for k in env):
        print("  (no FXG/redis env vars in gunicorn master)")
except Exception as e:
    print("  environ read failed:", e)

print("=== sync_history.json (last 3) ===")
try:
    d = json.load(open('/data/sync_history.json', encoding='utf-8'))
    for entry in d[-3:]:
        print(json.dumps(entry, indent=2, ensure_ascii=False)[:800])
        print("  ---")
except Exception as e:
    print("  read failed:", e)

print("=== Try importing app modules via subprocess (system python3) ===")
code = '''
import sys
sys.path.insert(0, "/root/douyin_new")
try:
    import settings
    print("settings OK")
    c = settings.Config
    print("FXG_BASE_URL:", c.FXG_BASE_URL)
    print("TOKEN:", repr(c.TOKEN)[:40])
    print("VERIFY_FP:", repr(c.VERIFY_FP)[:40])
    print("FP:", repr(c.FP)[:40])
    print("FXG_COOKIES:", repr(c.FXG_COOKIES)[:60])
    print("FXG_ORDER_LID:", c.FXG_ORDER_LID)
    print("FXG_ORDER_AID:", c.FXG_ORDER_AID)
except Exception as e:
    print("settings import FAIL:", repr(e))
'''
r = subprocess.run(['python3', '-c', code], capture_output=True, text=True, cwd='/root/douyin_new')
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)

print("=== Find flask installation ===")
r = subprocess.run(['python3', '-m', 'pip', 'list'], capture_output=True, text=True)
for line in r.stdout.splitlines():
    if any(name in line.lower() for name in ['flask','redis','celery','pydantic','schedule','python-dotenv','gunicorn','requests']):
        print("  ", line)
