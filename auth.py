"""Auth blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_config, set_config, DEFAULT_AUTH_CONFIG
from datetime import datetime, timedelta
import base64
from utils.responses import success_response, bad_request_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1')


@auth_bp.route('/auth/status', methods=['GET'])
def get_auth_status():
    """Get authorization status."""
    return success_response(get_config('auth_config'))


@auth_bp.route('/auth/login', methods=['GET'])
def auth_login():
    """Initiate OAuth login - redirect to Douyin auth page."""
    auth_config = get_config('auth_config')
    auth_url = f"https://open.douyin.com/platform/oauth/connect/?client_key={auth_config.get('douyin_app_id', '')}&response_type=code&redirect_uri={auth_config.get('redirect_uri', '')}&scope=video.list,video.create,creator.info"
    return success_response({
        'auth_url': auth_url
    }, 'Redirect to Douyin OAuth')


@auth_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """OAuth callback handler."""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return bad_request_response(error)
    
    if not code:
        return bad_request_response('Missing authorization code')
    
    # In production, exchange code for access token
    # For now, simulate successful auth
    auth_config = get_config('auth_config')
    auth_config.update({
        'authorized': True,
        'access_token': f"access_token_{int(datetime.now().timestamp())}",
        'refresh_token': f"refresh_token_{int(datetime.now().timestamp())}",
        'expires_at': int((datetime.now() + timedelta(days=30)).timestamp()),
        'scope': ['video.list', 'video.create', 'creator.info']
    })
    set_config('auth_config', auth_config)
    cache.set(CACHE_KEYS['auth'], auth_config)
    
    return success_response(auth_config, 'Authorization successful')


@auth_bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    """Revoke authorization."""
    auth_config = get_config('auth_config')
    auth_config.update({
        'authorized': False,
        'access_token': '',
        'refresh_token': '',
        'expires_at': 0,
        'scope': []
    })
    set_config('auth_config', auth_config)
    cache.set(CACHE_KEYS['auth'], auth_config)
    return success_response(None, 'Authorization revoked')


@auth_bp.route('/auth/qr-code', methods=['GET'])
def get_auth_qr_code():
    """Get QR code for authorization."""
    auth_config = get_config('auth_config')
    qr_data = f"douyin_oauth:{auth_config.get('douyin_app_id', '')}:{int(datetime.now().timestamp())}"
    qr_base64 = base64.b64encode(qr_data.encode()).decode()
    return success_response({
        'qr_code': f"data:image/png;base64,{qr_base64}"
    }, 'Scan with Douyin app')