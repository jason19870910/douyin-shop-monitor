from services.fetcher import cache, CACHE_KEYS
print('auth:', cache.get(CACHE_KEYS['auth']))