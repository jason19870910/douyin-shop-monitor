import datetime
import psutil
from flask import current_app
from utils.responses import success_response, internal_error_response
from services.fetcher import cache

# CST 时区 (UTC+8)
CST = datetime.timezone(datetime.timedelta(hours=8))

def health():
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 获取最后数据同步时间
        last_update = cache.get('last_update')
        
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