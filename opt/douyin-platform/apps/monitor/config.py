import os
from pathlib import Path
from datetime import datetime


def _read_secret(secret_name: str, env_var: str = None, default: str = '') -> str:
    """Read secret from Docker secret file, then environment variable, then default.
    
    Docker secrets are mounted at /run/secrets/<secret_name>
    """
    # Try Docker secret file first
    secret_path = Path(f'/run/secrets/{secret_name}')
    if secret_path.exists():
        try:
            return secret_path.read_text().strip()
        except Exception:
            pass
    
    # Fall back to environment variable
    if env_var:
        return os.getenv(env_var, default)
    
    return default


def _read_secret_int(secret_name: str, env_var: str = None, default: int = 0) -> int:
    """Read integer secret from Docker secret file or environment variable."""
    val = _read_secret(secret_name, env_var, str(default))
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# Minimal Config class for API usage
class Config:
    """Compatibility wrapper exposing expected attributes for Flask app."""
    DOUYIN_APP_ID = _read_secret('douyin_app_id', 'DOUYIN_APP_ID')
    DOUYIN_APP_SECRET = _read_secret('douyin_app_secret', 'DOUYIN_APP_SECRET')
    DOUYIN_ACCESS_TOKEN = _read_secret('douyin_access_token', 'DOUYIN_ACCESS_TOKEN')
    SCHEDULE_INTERVAL_MINUTES = _read_secret_int('schedule_interval_minutes', 'SCHEDULE_INTERVAL_MINUTES', 60)
    ALERT_EMAIL = _read_secret('alert_email', 'ALERT_EMAIL')
    DATA_DIR = os.getenv('DATA_DIR', str(Path(__file__).parent / 'data'))
    EXTERNAL_DATA_BASE_URL = os.getenv('EXTERNAL_DATA_BASE_URL', 'https://example.com/monitor')
    API_AUTH_TOKEN = _read_secret('api_auth_token', 'API_AUTH_TOKEN')
    # 双域名基础 URL
    FXG_BASE_URL = os.getenv('FXG_BASE_URL', 'https://fxg.jinritemai.com')
    CREATOR_BASE_URL = os.getenv('CREATOR_BASE_URL', 'https://creator.douyin.com')
    # 创作者中心内容管理 API
    CREATOR_WORK_LIST_URL = os.getenv('CREATOR_WORK_LIST_URL', 'https://creator.douyin.com/janus/douyin/creator/pc/work_list')
    # 公共请求头中的 User-Agent（顶层属性供 sign_request 使用）
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')
    # 公共请求头模板（可根据需求覆盖）
    COMMON_HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Priority": "u=1, i",
        "User-Agent": USER_AGENT
    }
    # 双域名 Cookie 变量（从 Docker secrets 读取）
    FXG_COOKIES = _read_secret('fxg_cookies', 'FXG_COOKIES')
    CREATOR_COOKIES = _read_secret('creator_cookies', 'CREATOR_COOKIES')
    # 抖店 Shop ID 与 Log ID（多店铺场景需配置）
    FXG_SHOP_ID = _read_secret_int('fxg_shop_id', 'FXG_SHOP_ID', 4272)
    FXG_LOG_ID = _read_secret('fxg_log_id', 'FXG_LOG_ID', '104476165896')
    # 认证与签名参数
    TOKEN = _read_secret('token', '__TOKEN')
    MS_TOKEN = _read_secret('ms_token', 'MS_TOKEN')
    a_bogus = _read_secret('a_bogus', 'a_bogus')
    verifyFp = _read_secret('verify_fp', 'verifyFp')
    fp = _read_secret('fp', 'fp')
    # Add any other attributes referenced in app.py
    KEEP_ALIVE_TIMEOUT = _read_secret_int('keep_alive_timeout', 'KEEP_ALIVE_TIMEOUT', 30)
    TIMEOUT = _read_secret_int('timeout', 'TIMEOUT', 30)
    API_KEY = _read_secret('api_key', 'API_KEY')

# placeholder