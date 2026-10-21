"""System blueprint for version, health, and environment info."""
import json
import os
from pathlib import Path
from flask import Blueprint, request

from utils.responses import success_response

system_bp = Blueprint('system', __name__, url_prefix='/api/v1')


def _frontend_healthy() -> bool:
    """Actually probe the frontend container's nginx /health endpoint."""
    try:
        import urllib.request
        with urllib.request.urlopen('http://frontend/health', timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _frontend_api_key_inlined() -> bool:
    """Detect whether the API key was inlined into the frontend bundle at build time.

    构建时 vite define 替换成功 => 产物 JS 中不存在 VITE_API_KEY 占位符，
    且包含鉴权 header 逻辑。app 与 frontend 在同一 compose 网络，可用服务名直连。
    """
    try:
        import re
        import urllib.request
        with urllib.request.urlopen('http://frontend/', timeout=2) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        match = re.search(r'/assets/index-[^"\']+\.js', html)
        if not match:
            return False
        with urllib.request.urlopen('http://frontend' + match.group(0), timeout=5) as resp:
            bundle = resp.read().decode('utf-8', errors='ignore')
        return (
            'X-API-Key' in bundle
            and 'VITE_API_KEY' not in bundle
            and '%VITE_API_KEY%' not in bundle
        )
    except Exception:
        return False


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

    # 运行镜像 ID 由 CI 部署成功后写入 /data/image_info.json。
    # version_info.json 是 bind mount 的宿主机文件、不随镜像回退，仅看它无法分辨
    # "回滚后跑旧镜像但版本号显示新提交"；imageId 反映真实运行的镜像。
    image_info = {}
    image_file = Path('/data/image_info.json')
    try:
        if image_file.exists():
            with open(image_file, 'r', encoding='utf-8') as f:
                image_info = json.load(f)
    except Exception:
        pass

    image_id = image_info.get('imageId') or None

    # apiKeyInlined: 前端构建产物中是否已内联 API Key（真实探测 bundle）
    api_key_inlined = _frontend_api_key_inlined()

    return success_response({
        'version': version,
        'commit': commit,
        'builtAt': built_at,
        'apiKeyInlined': api_key_inlined,
        'environment': 'production' if not getattr(settings, 'DEBUG', False) else 'development',
        'imageId': image_id,
        'imageIdShort': image_id.replace('sha256:', '')[:12] if image_id else None,
        'imageRecordedAt': image_info.get('recordedAt')
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

    # 读取最后部署时间（部署脚本 / CI 写入项目根 .env 的 LAST_DEPLOY_TIME）
    last_deploy = os.getenv('LAST_DEPLOY_TIME', '')

    return success_response({
        'appHealthy': True,  # 能响应说明 app 正常
        'redisHealthy': redis_healthy,
        'frontendHealthy': _frontend_healthy(),  # 实际探测 frontend 容器 /health
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