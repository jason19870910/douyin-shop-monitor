"""System blueprint for version, health, and environment info."""
import json
import os
from pathlib import Path
from flask import Blueprint, request

from utils.responses import success_response

system_bp = Blueprint('system', __name__, url_prefix='/api/v1')


@system_bp.route('/version', methods=['GET'])
def get_version():
    """Get current application version and build info."""
    # Read version info from generated file (in /data to survive volume mount)
    version_file = Path('/data/version_info.json')
    version = 'dev'
    commit = 'unknown'
    built_at = ''

    if version_file.exists():
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                version = version_data.get('version', 'dev')
                commit = version_data.get('commit', 'unknown')
                built_at = version_data.get('builtAt', '')
        except Exception:
            pass

    from config.settings import get_settings
    settings = get_settings()

    # apiKeyInlined: 前端构建时是否已内联 API Key
    # 运行时无法准确判断，默认按环境区分：生产环境通常内联
    api_key_inlined = not getattr(settings, 'DEBUG', False)

    return success_response({
        'version': version,
        'commit': commit,
        'builtAt': built_at,
        'apiKeyInlined': api_key_inlined,
        'environment': 'production' if not getattr(settings, 'DEBUG', False) else 'development',
    })


@system_bp.route('/changes', methods=['GET'])
def get_recent_changes():
    """Get recent git changes from generated file."""
    changes_file = Path('/data/changes_info.json')
    if changes_file.exists():
        try:
            with open(changes_file, 'r', encoding='utf-8') as f:
                changes = json.load(f)
                return success_response(changes)
        except Exception:
            pass

    return success_response([], 'Git history not available in container')


@system_bp.route('/status', methods=['GET'])
def get_status():
    """Get deployment and service health status."""
    import redis

    redis_healthy = False
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=0,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        redis_healthy = redis_client.ping()
    except Exception:
        pass

    # 读取最后部署时间（可从文件或环境变量获取）
    last_deploy = os.getenv('LAST_DEPLOY_TIME', '')

    return success_response({
        'appHealthy': True,  # 能响应说明 app 正常
        'redisHealthy': redis_healthy,
        'frontendHealthy': True,  # 前端由 nginx 独立服务，这里默认 true
        'lastDeploy': last_deploy,
    })


@system_bp.route('/env', methods=['GET'])
def get_env():
    """Get frontend environment config (non-sensitive)."""
    return success_response({
        'VITE_API_KEY': os.getenv('VITE_API_KEY', ''),
        'VITE_DEV_MODE': os.getenv('VITE_DEV_MODE', 'false').lower() == 'true',
        'VITE_ENABLE_MOCK_FALLBACK': os.getenv('VITE_ENABLE_MOCK_FALLBACK', 'false').lower() == 'true',
    })