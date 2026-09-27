from services.fetcher import cache
print("products:", cache.get("products"))
print("creators:", cache.get("creators"))
print("orders:", cache.get("orders"))
print("videos:", cache.get("videos"))