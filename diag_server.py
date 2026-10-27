import os, sys, importlib, glob

print("=== Python ===")
print(sys.version)
print("sys.path:", sys.path[:5])

print("\n=== Module availability ===")
for m in ['redis', 'flask', 'celery', 'schedule', 'yaml', 'dotenv', 'pydantic', 'requests']:
    try:
        mod = importlib.import_module(m)
        print(f"  {m}: OK {getattr(mod, '__version__', '')}")
    except Exception as e:
        print(f"  {m}: MISSING ({e})")

print("\n=== Locate fetcher.py / config.py / services dir ===")
for pat in ['**/fetcher.py', '**/config.py', '**/services/__init__.py']:
    matches = glob.glob(f'/root/douyin_new/{pat}', recursive=True)
    print(f"  {pat}: {matches[:5]}")

print("\n=== Environment variables (FXG/RELATED) ===")
for k in sorted(os.environ.keys()):
    kl = k.lower()
    if any(s in kl for s in ['fxg', 'token', 'cookie', 'verify', 'aid', 'lid', 'redis', 'debug', 'skip_auth', 'schedule', 'data_dir']):
        print(f"  {k}={os.environ[k][:80]}")

print("\n=== /data contents ===")
for f in glob.glob('/data/*'):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read(200)
        print(f"  {f}: {content!r}")
    except Exception as e:
        print(f"  {f}: (binary/error {e})")

print("\n=== Try importing app modules ===")
os.chdir('/root/douyin_new')
sys.path.insert(0, '/root/douyin_new')
try:
    from config import Config
    print("  config.Config OK")
    print("    FXG_BASE_URL:", Config.FXG_BASE_URL)
    print("    TOKEN:", repr(Config.TOKEN)[:60])
    print("    VERIFY_FP:", repr(Config.VERIFY_FP)[:60])
    print("    FP:", repr(Config.FP)[:60])
    print("    FXG_COOKIES:", repr(Config.FXG_COOKIES)[:80])
    print("    FXG_ORDER_LID:", Config.FXG_ORDER_LID)
    print("    FXG_ORDER_AID:", Config.FXG_ORDER_AID)
except Exception as e:
    print("  config.Config FAIL:", repr(e))

try:
    from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_ORDERS
    print("  services.fetcher OK")
    print("  CACHE_KEYS['orders']:", CACHE_KEYS.get('orders'))
    data, source = get_data_with_fallback('orders', MOCK_ORDERS)
    print("  get_data_with_fallback('orders'): len=", len(data), "source=", source)
except Exception as e:
    print("  services.fetcher FAIL:", repr(e))
