import sys
sys.path.insert(0, '/app')
from services.fetcher import _fetch_creators_from_api
import json
data = _fetch_creators_from_api()
print(json.dumps(data, ensure_ascii=False)[:500])
