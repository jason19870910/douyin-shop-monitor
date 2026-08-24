from services.fetcher import load_all_data, cache, CACHE_KEYS
load_all_data()
auth = cache.get(CACHE_KEYS['auth'])
print('auth after load:', auth)