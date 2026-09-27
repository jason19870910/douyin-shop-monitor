"""Auth blueprint."""
from flask import Blueprint, request, current_app, make_response
from services.fetcher import cache, CACHE_KEYS, get_config, set_config, DEFAULT_AUTH_CONFIG
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import base64
import requests
import logging
import os
from pathlib import Path
from utils.responses import success_response, bad_request_response, internal_error_response as server_error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1')

logger = logging.getLogger(__name__)

DOUYIN_TOKEN_URL = "https://open.douyin.com/oauth/access_token/"
DOUYIN_REFRESH_URL = "https://open.douyin.com/oauth/refresh_token/"


def _read_auth_secret(secret_name: str, env_var: str = None, default: str = '') -> str:
    """Read secret from Docker secret file, then environment variable, then default."""
    secret_path = Path(f'/run/secrets/{secret_name}')
    if secret_path.exists():
        try:
            return secret_path.read_text().strip()
        except Exception:
            pass
    if env_var:
        return os.getenv(env_var, default)
    return default


def _get_auth_config_with_secrets() -> dict:
    """Get auth config with secrets filled in from Docker secrets."""
    auth_config = get_config('auth_config').copy()
    
    # Fill in app_id and app_secret from secrets if not in config
    if not auth_config.get('douyin_app_id'):
        auth_config['douyin_app_id'] = _read_auth_secret('douyin_app_id', 'DOUYIN_APP_ID')
    if not auth_config.get('douyin_app_secret'):
        auth_config['douyin_app_secret'] = _read_auth_secret('douyin_app_secret', 'DOUYIN_APP_SECRET')
    # Always use the value from secrets or environment variable for redirect_uri
    auth_config['redirect_uri'] = _read_auth_secret('redirect_uri', 'OAUTH_REDIRECT_URI', 'https://wlkj-tech.cn/api/v1/auth/callback')
    
    return auth_config


# ----------------------------------------------------------------------
# Helper: generate a URL-safe state token (max 32 alphanum chars)
# ----------------------------------------------------------------------
def _gen_state_token() -> str:
    """
    Generate an alphanumeric token <= 32 characters.
    Douyin requires state to be alphanumeric (A-Z, a-z, 0-9) and <= 32 chars.
    """
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


# ----------------------------------------------------------------------
# Helper: build the OAuth URL with all mandatory parameters properly encoded
# ----------------------------------------------------------------------
def _build_oauth_url(auth_config: dict) -> tuple[str, str]:
    """
    Construct a Douyin OAuth "connect" URL that satisfies the platform requirements:
    
    https://open.douyin.com/platform/oauth/connect/?client_key=...
        &response_type=code
        &redirect_uri=<ENCODED_REDIRECT>
        &scope=<ENCODED_SCOPE>
        &state=<ENCODED_STATE>
    
    Returns tuple of (oauth_url, state_token)
    """
    base_url = "https://open.douyin.com/platform/oauth/connect/"
    
    client_key = auth_config.get('douyin_app_id', '')
    redirect_uri = auth_config.get('redirect_uri')
    if not client_key or not redirect_uri:
        raise ValueError("Missing douyin_app_id or redirect_uri in auth config")
    
    # Encode redirect_uri because it may contain "/", "?" or other reserved chars
    encoded_redirect = quote_plus(redirect_uri)
    
    # Scope - read from environment variable DOUYIN_SCOPE
    # Falls back to hardcoded scope with valid Douyin OAuth scopes
    scope = os.getenv('DOUYIN_SCOPE', '')
    if not scope:
        logger.warning(
            "DOUYIN_SCOPE environment variable not set. "
            "Using fallback scope with valid Douyin OAuth scopes. "
            "Please set DOUYIN_SCOPE in .env to match Douyin console Authorized Scope."
        )
        # Valid Douyin OAuth scope code (not internal capability names from PERMISSION.md)
        # Only user_info is confirmed valid for OAuth authorization
        # Additional scopes require separate approval in Douyin Open Platform console
        scope = "user_info"
    
    # State - generate a short URL-safe token
    state = _gen_state_token()
    
    # Response type - Douyin expects "code"
    response_type = "code"
    
    # Assemble the final URL with all parameters properly encoded
    oauth_url = (
        f"{base_url}"
        f"?client_key={quote_plus(client_key)}"
        f"&response_type={response_type}"
        f"&redirect_uri={encoded_redirect}"
        f"&scope={quote_plus(scope)}"
        f"&state={state}"
    )
    return oauth_url, state


def _exchange_code_for_token(code: str, auth_config: dict) -> dict:
    """Exchange authorization code for access token."""
    data = {
        'client_key': auth_config.get('douyin_app_id', ''),
        'client_secret': auth_config.get('douyin_app_secret', ''),
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        resp = requests.post(DOUYIN_TOKEN_URL, data=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        if result.get('data'):
            return {'success': True, 'data': result['data']}
        else:
            logger.error(f"Token exchange failed: {result}")
            return {'success': False, 'error': result.get('message', 'Unknown error'), 'detail': result}
            
    except requests.RequestException as e:
        logger.error(f"Token exchange request failed: {e}")
        return {'success': False, 'error': f'Request failed: {str(e)}'}


def _refresh_access_token(refresh_token: str, auth_config: dict) -> dict:
    """Refresh access token using refresh token."""
    data = {
        'client_key': auth_config.get('douyin_app_id', ''),
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    try:
        resp = requests.post(DOUYIN_REFRESH_URL, data=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        if result.get('data'):
            return {'success': True, 'data': result['data']}
        else:
            logger.error(f"Token refresh failed: {result}")
            return {'success': False, 'error': result.get('message', 'Unknown error'), 'detail': result}
            
    except requests.RequestException as e:
        logger.error(f"Token refresh request failed: {e}")
        return {'success': False, 'error': f'Request failed: {str(e)}'}


@auth_bp.route('/auth/status', methods=['GET'])
def get_auth_status():
    """Get authorization status."""
    auth_config = get_config('auth_config')
    
    # Check if token is expired
    expires_at = auth_config.get('expires_at', 0)
    is_expired = expires_at > 0 and datetime.now().timestamp() >= expires_at
    
    return success_response({
        **auth_config,
        'is_expired': is_expired,
        'expires_in': max(0, int(expires_at - datetime.now().timestamp())) if expires_at > 0 else 0
    })


@auth_bp.route('/auth/login', methods=['GET'])
def auth_login():
    """Initiate OAuth login - redirect to Douyin auth page."""
    auth_config = _get_auth_config_with_secrets()

    # Validate required config
    if not auth_config.get('douyin_app_id') or not auth_config.get('douyin_app_secret'):
        return bad_request_response('Missing douyin_app_id or douyin_app_secret in config')

    if not auth_config.get('redirect_uri'):
        return bad_request_response('Missing redirect_uri in config')

    # Build the correct OAuth URL with proper encoding
    try:
        auth_url, state = _build_oauth_url(auth_config)
    except ValueError as ve:
        logger.error(f"Auth config validation error: {ve}")
        return bad_request_response(str(ve))

    # Persist the generated state before redirecting; otherwise callback validation fails
    cache.set(f"oauth_state:{state}", "pending", ttl=600)
    logger.info(
        "OAuth login initiated: redirect_uri=%s state=%s state_key=%s",
        auth_config.get('redirect_uri'),
        state,
        f"oauth_state:{state}",
    )

    return success_response({
        'auth_url': auth_url
    }, 'Redirect to Douyin OAuth')


@auth_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """OAuth callback handler - exchange code for access token."""
    code = request.args.get('code')
    error = request.args.get('error')
    state = request.args.get('state')

    logger.info(
        "OAuth callback received: has_code=%s has_state=%s error=%s redirect_uri=%s",
        bool(code),
        bool(state),
        error,
        _get_auth_config_with_secrets().get('redirect_uri'),
    )

    if error:
        logger.warning(f"OAuth error: {error}")
        return _frontend_redirect('error', error)

    if not code:
        logger.warning("OAuth callback missing code parameter")
        return _frontend_redirect('error', 'Missing authorization code')

    # Validate state parameter (CSRF protection)
    if not state:
        logger.warning("OAuth callback missing state parameter")
        return _frontend_redirect('error', 'Missing state parameter')

    state_key = f"oauth_state:{state}"
    stored_state = cache.get(state_key)
    if not stored_state:
        logger.warning(
            "OAuth state validation failed: state=%s state_key=%s cache_value=%s redirect_uri=%s",
            state,
            state_key,
            stored_state,
            _get_auth_config_with_secrets().get('redirect_uri'),
        )
        return _frontend_redirect('error', 'Invalid or expired state parameter')

    # Delete state after use (one-time use)
    cache.delete(state_key)

    auth_config = _get_auth_config_with_secrets()

    # Validate required config
    if not auth_config.get('douyin_app_id') or not auth_config.get('douyin_app_secret'):
        return server_error_response('Server config missing: douyin_app_id or douyin_app_secret')

    # Exchange code for token
    token_result = _exchange_code_for_token(code, auth_config)

    if not token_result['success']:
        logger.error(f"Failed to exchange code for token: {token_result['error']}")
        return server_error_response(f'Token exchange failed: {token_result["error"]}')

    token_data = token_result['data']

    # Update auth config with real tokens
    expires_in = token_data.get('expires_in', 86400)  # Default 24 hours
    refresh_expires_in = token_data.get('refresh_expires_in', 2592000)  # Default 30 days

    auth_config.update({
        'authorized': True,
        'access_token': token_data.get('access_token', ''),
        'refresh_token': token_data.get('refresh_token', ''),
        'open_id': token_data.get('open_id', ''),
        'expires_at': int((datetime.now() + timedelta(seconds=expires_in)).timestamp()),
        'refresh_expires_at': int((datetime.now() + timedelta(seconds=refresh_expires_in)).timestamp()),
        'scope': token_data.get('scope', 'user_info').split(','),
        'last_updated': datetime.now().isoformat()
    })

    set_config('auth_config', auth_config)
    cache.set(CACHE_KEYS['auth'], auth_config)

    logger.info(f"OAuth authorization successful for open_id: {token_data.get('open_id', 'unknown')}")

    return success_response(auth_config, 'Authorization successful')


@auth_bp.route('/auth/refresh', methods=['POST'])
def auth_refresh():
    """Refresh access token using refresh token."""
    auth_config = get_config('auth_config')
    
    if not auth_config.get('authorized'):
        return bad_request_response('Not authorized')
    
    # Fill in secrets if missing
    if not auth_config.get('douyin_app_id'):
        auth_config['douyin_app_id'] = _read_auth_secret('douyin_app_id', 'DOUYIN_APP_ID')
    if not auth_config.get('douyin_app_secret'):
        auth_config['douyin_app_secret'] = _read_auth_secret('douyin_app_secret', 'DOUYIN_APP_SECRET')
    
    refresh_token = auth_config.get('refresh_token')
    if not refresh_token:
        return bad_request_response('No refresh token available')
    
    # Check if refresh token is expired
    refresh_expires_at = auth_config.get('refresh_expires_at', 0)
    if refresh_expires_at > 0 and datetime.now().timestamp() >= refresh_expires_at:
        # Refresh token expired, need full re-authorization
        auth_config.update({
            'authorized': False,
            'access_token': '',
            'refresh_token': '',
            'expires_at': 0,
            'refresh_expires_at': 0
        })
        set_config('auth_config', auth_config)
        cache.set(CACHE_KEYS['auth'], auth_config)
        return bad_request_response('Refresh token expired, please re-authorize')
    
    # Refresh the token
    token_result = _refresh_access_token(refresh_token, auth_config)
    
    if not token_result['success']:
        logger.error(f"Failed to refresh token: {token_result['error']}")
        return server_error_response(f'Token refresh failed: {token_result["error"]}')
    
    token_data = token_result['data']
    
    expires_in = token_data.get('expires_in', 86400)
    refresh_expires_in = token_data.get('refresh_expires_in', 2592000)
    
    auth_config.update({
        'access_token': token_data.get('access_token', ''),
        'refresh_token': token_data.get('refresh_token', ''),
        'expires_at': int((datetime.now() + timedelta(seconds=expires_in)).timestamp()),
        'refresh_expires_at': int((datetime.now() + timedelta(seconds=refresh_expires_in)).timestamp()),
        'scope': token_data.get('scope', 'user_info').split(','),
        'last_updated': datetime.now().isoformat()
    })
    
    set_config('auth_config', auth_config)
    cache.set(CACHE_KEYS['auth'], auth_config)
    
    logger.info("Access token refreshed successfully")
    
    return success_response(auth_config, 'Token refreshed successfully')


@auth_bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    """Revoke authorization."""
    auth_config = get_config('auth_config')
    auth_config.update({
        'authorized': False,
        'access_token': '',
        'refresh_token': '',
        'expires_at': 0,
        'refresh_expires_at': 0,
        'scope': []
    })
    set_config('auth_config', auth_config)
    cache.set(CACHE_KEYS['auth'], auth_config)
    return success_response(None, 'Authorization revoked')


@auth_bp.route('/auth/qr-code', methods=['GET'])
def get_auth_qr_code():
    """Get QR code data for authorization - returns the OAuth URL to encode in QR code."""
    auth_config = _get_auth_config_with_secrets()
    
    # Validate required config
    if not auth_config.get('douyin_app_id') or not auth_config.get('douyin_app_secret'):
        return bad_request_response('Missing douyin_app_id or douyin_app_secret in config')
    
    if not auth_config.get('redirect_uri'):
        return bad_request_response('Missing redirect_uri in config')
    
    # Build the correct OAuth URL with proper encoding
    try:
        oauth_url, state = _build_oauth_url(auth_config)
    except ValueError as ve:
        logger.error(f"Auth config validation error: {ve}")
        return bad_request_response(str(ve))
    
    # Store state in cache with TTL (10 minutes) for CSRF validation in callback
    cache.set(f"oauth_state:{state}", "pending", ttl=600)
    
    # Return the URL (the front-end will turn it into a QR code)
    return success_response({
        "auth_url": oauth_url
    }, 'QR code data generated')


def _frontend_redirect(status: str, message: str = '') -> object:
    """Redirect browser-based OAuth callback results back to the frontend auth page."""
    frontend_origin = os.getenv('FRONTEND_URL', 'https://wlkj-tech.cn')
    target = (
        f"{frontend_origin.rstrip('/')}/auth?oauth={quote_plus(status, safe='')}"
        f"&msg={quote_plus(message or status, safe='')}"
    )
    html = f"""
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <meta http-equiv="refresh" content="0; url={target}" />
        <title>Douyin OAuth</title>
      </head>
      <body style="font-family: sans-serif; text-align: center; padding: 32px;">
        <p>授权处理中，请稍候...</p>
        <script>
          window.location.replace({target!r});
        </script>
      </body>
    </html>
    """
    return make_response(html, 200)
