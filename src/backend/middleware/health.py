import datetime
import json
import psutil
from pathlib import Path
from flask import current_app
from utils.responses import success_response, internal_error_response
from services.fetcher import cache, DATA_DIR

# CST 时区 (UTC+8)
CST = datetime.timezone(datetime.timedelta(hours=8))

def health():
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 获取最后数据同步时间：优先 Redis，回退到本地文件
        last_update = cache.get('last_update')
        if last_update is None:
            last_update_file = DATA_DIR / 'last_update.json'
            if last_update_file.exists():
                try:
                    with open(last_update_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        last_update = data.get('last_update')
                except Exception:
                    pass
        
        return success_response({
            "status": "healthy",
            "last_update": last_update,
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
                "used": mem.used,
            },
            "cpu_percent": cpu_percent,
            "timestamp": datetime.datetime.now(CST).isoformat()
        })
    except Exception as e:
        return internal_error_response(str(e))