import datetime
import psutil
from flask import jsonify
from utils.responses import success_response, internal_error_response

def health():
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return success_response({
            "status": "ok",
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
                "used": mem.used,
            },
            "cpu_percent": cpu_percent,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return internal_error_response(str(e))