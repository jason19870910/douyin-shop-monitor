"""Main application entry point with Flask blueprints."""
import os
import json
import logging
import logging.config
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, urlparse

import yaml
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from config import Config
from services.fetcher import (
    cache,
    CACHE_KEYS,
    fetch_and_store_products,
    fetch_and_store_orders,
    fetch_and_store_creators,
    fetch_and_store_creator_works,
    fetch_and_store_videos,
    check_alerts,
    fetch_and_check_compliance,
    _acquire_sync_lock,
    _release_sync_lock,
    _check_and_log_auth_errors,
    _calculate_overall_status,
    _extract_status,
    _save_sync_history,
    load_all_data,
    save_all_data,
    _init_default_compliance_rules,
)
from blueprints import (
    products_bp,
    orders_bp,
    creators_bp,
    auth_bp,
    videos_bp,
    accounts_bp,
    compliance_bp,
    media_bp,
    alerts_bp,
    dashboard_bp,
    sync_bp,
    frontend_bp,
)
from utils.responses import unauthorized_response
from middleware.health import health


def setup_logging():
    """Load logging configuration from YAML file."""
    log_config_path = Path(__file__).parent / 'logging.yaml'
    if log_config_path.exists():
        with open(log_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        for handler in config.get('handlers', {}).values():
            filename = handler.get('filename')
            if filename:
                log_path = Path(filename)
                if not log_path.is_absolute():
                    log_path = (Path(__file__).parent / log_path).resolve()
                log_path.parent.mkdir(parents=True, exist_ok=True)
                handler['filename'] = str(log_path)
        try:
            logging.config.dictConfig(config)
            return
        except Exception as exc:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logging.getLogger(__name__).warning(
                "Failed to apply logging.yaml (%s); using basicConfig", exc
            )
            return
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


setup_logging()
logger = logging.getLogger(__name__)

SKIP_AUTH = os.getenv('SKIP_AUTH', 'false').lower() == 'true'

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    }
})


def parse_cookie(cookie_value: Optional[str]) -> str:
    """兼容旧版接口：将 Cookie 字符串或 Cookie 文件转换为标准字符串。"""
    if cookie_value is None:
        return ""

    cookie_value = str(cookie_value).strip()
    if not cookie_value:
        return ""

    cookie_path = Path(cookie_value)
    if cookie_path.exists() and cookie_path.is_file():
        try:
            text = cookie_path.read_text(encoding='utf-8')
        except OSError:
            return cookie_value
        if '\t' in text:
            cookies = []
            for line in text.splitlines():
                parts = [part.strip() for part in line.split('\t')]
                if len(parts) >= 7 and parts[5] and parts[6]:
                    cookies.append(f"{parts[5]}={parts[6]}")
            return '; '.join(cookies)
        return text.strip()

    if '\n' in cookie_value and '\t' in cookie_value:
        cookies = []
        for line in cookie_value.splitlines():
            parts = [part.strip() for part in line.split('\t')]
            if len(parts) >= 7 and parts[5] and parts[6]:
                cookies.append(f"{parts[5]}={parts[6]}")
        return '; '.join(cookies)

    return cookie_value


def extract_csrf_token(url: str) -> str:
    """从 URL 中提取 __token / token 参数。"""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        for key in ('__token', 'token', 'csrf_token'):
            values = params.get(key)
            if values:
                return values[0]
    except Exception:
        return ""
    return ""


def build_product_headers(url: str) -> Dict[str, str]:
    """构建抖店请求头，兼容旧代码和测试。"""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "https://fxg.jinritemai.com"
    referer = f"{origin}/" if origin else "https://fxg.jinritemai.com/"
    cookie = os.getenv('COOKIE', '')
    token = extract_csrf_token(url) or os.getenv('CREATOR_CSRF_TOKEN', '')

    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': cookie,
        'origin': origin,
        'referer': referer,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'x-csrf-token': token,
        'x-secsdk-csrf-token': token,
        'x-requested-with': 'XMLHttpRequest',
    }


# Flasgger / Swagger UI（可选，未安装时跳过）
try:
    from flasgger import Swagger
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Douyin Monitor API",
            "description": "抖音电商数据监控平台 API 文档",
            "version": "1.0.0",
            "contact": {
                "name": "Douyin Monitor Team"
            }
        },
        "basePath": "/api/v1",
        "schemes": ["http", "https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        }
    })
except ImportError:
    swagger = None
    logger.warning("flasgger not installed, Swagger UI disabled")


# Only unauthenticated bootstrap / OAuth / probe endpoints.
# Business data (dashboard, sync, mock status) requires Bearer API key.
PUBLIC_ENDPOINTS = {
    '/api/v1/health',
    '/api/v1/health/external',
    '/api/v1/auth/login',
    '/api/v1/auth/callback',
    '/api/v1/auth/qr-code',
    '/api/v1/auth/status',
}


@app.before_request
def check_auth():
    """Check authentication for all API requests."""
    if SKIP_AUTH:
        return

    if request.method == 'OPTIONS':
        return

    if request.path in PUBLIC_ENDPOINTS:
        return

    if request.path.startswith('/static/') or request.path == '/' or request.path.startswith('/favicon'):
        return

    if request.path.startswith('/api/v1/'):
        auth_header = request.headers.get('Authorization', '')
        api_key_header = request.headers.get('X-API-Key', '')

        from config import Config
        api_key = (Config.API_KEY or '').strip()
        if not api_key:
            return unauthorized_response('Server API key is not configured')
        print(f"[AUTH DEBUG] API_KEY from Config: {repr(api_key)}", flush=True)
        print(f"[AUTH DEBUG] auth_header: {repr(auth_header)}", flush=True)
        print(f"[AUTH DEBUG] X-API-Key: {repr(api_key_header)}", flush=True)
        
        # Verify Authorization: Bearer token
        bearer_valid = auth_header.startswith('Bearer ') and auth_header[7:] == api_key

        # Verify X-API-Key header
        api_key_valid = api_key_header == api_key and api_key != ''

        print(f"[AUTH DEBUG] bearer_valid: {bearer_valid}", flush=True)
        print(f"[AUTH DEBUG] api_key_valid: {api_key_valid}", flush=True)
        print(f"[AUTH DEBUG] result: {bearer_valid or api_key_valid}", flush=True)

        # Accept if either validation passes (both headers should carry same key)
        if not (bearer_valid or api_key_valid):
            return unauthorized_response('Missing or invalid Authorization header or X-API-Key')


app.register_blueprint(products_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(creators_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(videos_bp)
app.register_blueprint(accounts_bp)
app.register_blueprint(compliance_bp)
app.register_blueprint(media_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(sync_bp)
app.register_blueprint(frontend_bp)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return health()

load_all_data()
_init_default_compliance_rules()
logger.info("Application started with embedded sync scheduler")


# ==================== Sync Scheduler ====================

SYNC_INTERVAL_MINUTES = int(os.getenv('SCHEDULE_INTERVAL_MINUTES', '60'))


def _run_sync_cycle():
    """Run one complete data sync cycle with distributed lock."""
    if not _acquire_sync_lock():
        logger.warning("Sync skipped: another sync already in progress")
        return
    
    try:
        logger.info("Starting scheduled sync cycle...")
        start_time = datetime.now()
        
        # Initialize default compliance rules if none exist
        _init_default_compliance_rules()
        
        results = {}
        results['products'] = fetch_and_store_products()
        results['orders'] = fetch_and_store_orders()
        results['creators'] = fetch_and_store_creators()
        results['creator_works'] = fetch_and_store_creator_works()
        results['videos'] = fetch_and_store_videos()
        results['compliance'] = fetch_and_check_compliance()
        results['alerts'] = check_alerts()
        
        # Check for auth errors and log (Way 2: log-only, most conservative)
        _check_and_log_auth_errors(results)
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Calculate overall status
        overall_status = _calculate_overall_status(results)
        
        # Record sync history
        _save_sync_history({
            'timestamp': end_time.isoformat(),
            'duration_ms': duration_ms,
            'status': overall_status,
            'trigger': 'scheduled',
            'details': {
                'products': _extract_status(results.get('products')),
                'orders': _extract_status(results.get('orders')),
                'creators': _extract_status(results.get('creators')),
                'creator_works': _extract_status(results.get('creator_works')),
                'compliance': _extract_status(results.get('compliance')),
                'alerts': _extract_status(results.get('alerts')),
            },
        })
        
        logger.info("Sync cycle completed in %dms with status: %s", duration_ms, overall_status)
    except Exception as e:
        logger.error("Sync cycle failed: %s", e, exc_info=True)
    finally:
        _release_sync_lock()


def _sync_scheduler_loop():
    """Background thread that runs scheduled sync tasks."""
    import schedule
    
    # Schedule sync every SYNC_INTERVAL_MINUTES minutes
    schedule.every(SYNC_INTERVAL_MINUTES).minutes.do(_run_sync_cycle)
    
    # Also run immediately on startup
    _run_sync_cycle()
    
    # Keep the thread running
    logger.info("Sync scheduler started, interval: %d minutes", SYNC_INTERVAL_MINUTES)
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except Exception as e:
            logger.warning("Scheduler error: %s", e)
            time.sleep(5)


# Start the scheduler thread daemon
scheduler_thread = threading.Thread(target=_sync_scheduler_loop, daemon=True)
scheduler_thread.start()


def create_app() -> Flask:
    """Application factory."""
    return app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)