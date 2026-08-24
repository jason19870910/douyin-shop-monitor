"""Main application entry point with Flask blueprints."""
import os
import json
import logging
import logging.config
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from flask import Flask, request
from flask_cors import CORS

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import config
from config import Config

# Import services
from services.fetcher import (
    load_all_data, 
    save_all_data, 
    scheduled_job,
    cache,
    CACHE_KEYS,
)

# Import blueprints
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
    frontend_bp,
)

# Import response helpers
from utils.responses import unauthorized_response

# Configure logging from YAML file
def setup_logging():
    """Load logging configuration from YAML file."""
    log_config_path = Path(__file__).parent / 'logging.yaml'
    if log_config_path.exists():
        with open(log_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Fallback to basic config if YAML not found
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend/build/static', static_url_path='/static')
CORS(app)

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


# Authentication middleware
PUBLIC_ENDPOINTS = {
    '/api/v1/health',
    '/api/v1/sync',
    '/api/v1/auth/login',
    '/api/v1/auth/callback',
    '/api/v1/auth/qr-code',
    '/api/v1/auth/status',  # Allow checking auth status without auth
}


@app.before_request
def check_auth():
    """Check authentication for all API requests."""
    # Skip for OPTIONS (CORS preflight)
    if request.method == 'OPTIONS':
        return
    
    # Skip for public endpoints
    if request.path in PUBLIC_ENDPOINTS:
        return
    
    # Skip for static files and frontend
    if request.path.startswith('/static/') or request.path == '/' or request.path.startswith('/favicon'):
        return
    
    # Only check auth for /api/v1/ paths
    if request.path.startswith('/api/v1/'):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return unauthorized_response('Missing or invalid Authorization header')
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        if token != Config.API_KEY:
            return unauthorized_response('Invalid API key')


# Register blueprints
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
app.register_blueprint(frontend_bp)

# Load data at module level so it runs with gunicorn
load_all_data()
logger.info("Application started (Celery Beat handles scheduling)")


def create_app() -> Flask:
    """Application factory."""
    return app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)