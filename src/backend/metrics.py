"""
监控指标模块 - 提供 /metrics 端点
依赖：仅标准库，无需额外安装
"""

import time
from threading import Lock
from flask import jsonify, current_app

# 全局指标（线程安全）
_metrics_lock = Lock()
_metrics = {
    'start_time': time.time(),
    'tasks_total': 0,
    'tasks_success': 0,
    'tasks_failed': 0,
    'last_run_timestamp': None,
    'last_run_success': None,
    'api_calls': 0,
    'api_errors': 0
}

def record_task(success: bool):
    with _metrics_lock:
        _metrics['tasks_total'] += 1
        if success:
            _metrics['tasks_success'] += 1
        else:
            _metrics['tasks_failed'] += 1
        _metrics['last_run_timestamp'] = time.time()
        _metrics['last_run_success'] = success

def record_api_call(success: bool):
    with _metrics_lock:
        _metrics['api_calls'] += 1
        if not success:
            _metrics['api_errors'] += 1

def get_metrics():
    """返回指标字典"""
    with _metrics_lock:
        uptime = time.time() - _metrics['start_time']
        data = _metrics.copy()
        data['uptime_seconds'] = round(uptime, 2)
        data['success_rate'] = (
            round(data['tasks_success'] / data['tasks_total'], 4)
            if data['tasks_total'] > 0 else None
        )
        return data

def register_monitor_routes(app):
    """向 Flask app 注册监控路由"""
    @app.route('/metrics')
    def metrics_endpoint():
        return jsonify(get_metrics())

    # 注意：/health 由 app.py 原生提供，此处不再重复注册以避免冲突