from services.fetcher import cache, CACHE_KEYS
auth = cache.get(CACHE_KEYS['auth'])
print(auth)