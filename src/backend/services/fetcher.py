"""Shared data fetching service layer for both Celery tasks and Flask app."""
import json
import logging
import os
import random
import requests
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from functools import wraps
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import config
from config import Config

# Import Redis cache - lazy initialization to avoid connection at module load
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Lazy cache getter - only initializes Redis connection when first accessed
_cache_instance = None
_redis_available = None  # Track Redis availability

def _get_cache():
    """Get cache instance with lazy initialization."""
    global _cache_instance, _redis_available
    if _cache_instance is None:
        try:
            from redis_cache import get_cache
            _cache_instance = get_cache()
            _redis_available = True
        except ConnectionError as e:
            logger.warning(f"Redis unavailable, falling back to file-only mode: {e}")
            _cache_instance = None
            _redis_available = False
    return _cache_instance

def is_redis_available() -> bool:
    """Check if Redis is available."""
    global _redis_available
    if _redis_available is None:
        _get_cache()  # This will set _redis_available
    return _redis_available

# For backwards compatibility - property-like access with graceful degradation
class _CacheProxy:
    def __getattr__(self, name):
        cache_instance = _get_cache()
        if cache_instance is None:
            # Return a no-op function for common methods
            def noop(*args, **kwargs):
                logger.debug(f"Cache operation '{name}' skipped (Redis unavailable)")
                return None
            # Handle special methods
            if name in ('get', 'set', 'delete', 'exists'):
                return noop
            return noop
        return getattr(cache_instance, name)

cache = _CacheProxy()

# Cache keys
CACHE_KEYS = {
    'products': 'products',
    'orders': 'orders',
    'creators': 'creators',
    'videos': 'videos',
    'accounts': 'accounts',
    'compliance_rules': 'compliance_rules',
    'compliance_logs': 'compliance_logs',
    'media': 'media',
    'auth': 'auth',
    'creator_works': 'creator_works',
    'alert_config': 'alert_config',
    'alert_douyin_config': 'alert_douyin_config',
    'alert_dian_config': 'alert_dian_config',
    'alert_history': 'alert_history',
    'sync_history': 'sync_history',
    'auth_config': 'auth_config',
    'audit_log': 'audit_log',
}

# 映射文档API_SPEC.md中列出的典型 english_metric_name 到实际 API 返回的可能字段名
# 用于兼容不同版本的外部返回格式
METRIC_ALIASES = {
    'total_followers': ('total_fans_cnt', 'followers', 'fans_cnt'),
    'total_videos'  : ('publish_cnt', 'video_cnt', 'videos_cnt'),
    'total_views'   : ('play_cnt', 'total_views', 'view_cnt'),
    'total_likes'   : ('digg_cnt', 'likes', 'likes_cnt'),
    'total_comments': ('comment_cnt', 'comments', 'comment_count'),
    'total_shares'  : ('share_count', 'shares', 'share_cnt'),
    'recent_followers_gain': ('net_fans_cnt', 'follower_gain', 'new_fans'),
    # 创作者中心概览额外字段
    'recent_share': ('share_count', 'shares', 'share_cnt'),
    'recent_comment': ('comment_cnt', 'comments', 'comment_count'),
    'recent_homepage_view': ('homepage_view_cnt', 'home_views', 'profile_view_cnt'),
    'cover_click_ratio': ('cover_click_rate', 'cover_ctr', 'click_ratio'),
    'cancel_followers': ('unfollow_cnt', 'cancel_fans', 'lost_fans'),
    'completion_rate_5s': ('completion_5s_rate', 'play_5s_rate', 'finish_rate_5s'),
    'bounce_rate_2s': ('bounce_2s_rate', 'drop_2s_rate', 'leave_rate_2s'),
    'avg_view_second': ('avg_play_duration', 'avg_watch_time', 'avg_view_sec'),
}

def _metric_value(metric_map: Dict[str, int], key: str) -> int:
    """根据英文名称从 metric_map 中查找对应的数值。
    
    先尝试精确匹配，再依据 METRIC_ALIASES 别名列表回退。
    若未找到则返回 0 并记录警告，便于排查。
    """
    # 1) 精确匹配
    if key in metric_map:
        return metric_map[key]
    # 2) 别名回退
    for alias in METRIC_ALIASES.get(key, (key,)):
        if alias in metric_map:
            return metric_map[alias]
    # 3) 未找到
    logger.warning(f"Creator overview metric '{key}' not found in API response, returning 0")
    return 0

# Data storage paths
DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))
# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_FILE = DATA_DIR / 'products.json'
ORDERS_FILE = DATA_DIR / 'orders.json'
CREATORS_FILE = DATA_DIR / 'creators.json'
VIDEOS_FILE = DATA_DIR / 'videos.json'
ACCOUNTS_FILE = DATA_DIR / 'accounts.json'
COMPLIANCE_FILE = DATA_DIR / 'compliance.json'  # 合规日志
COMPLIANCE_RULES_FILE = DATA_DIR / 'compliance_rules.json'  # 合规规则（权威源）
MEDIA_FILE = DATA_DIR / 'media.json'
AUTH_FILE = DATA_DIR / 'auth.json'
CREATOR_WORKS_FILE = DATA_DIR / 'creator_works.json'
ALERT_CONFIG_FILE = DATA_DIR / 'alert_config.json'
ALERT_DOUYIN_CONFIG_FILE = DATA_DIR / 'alert_douyin_config.json'
ALERT_DIAN_CONFIG_FILE = DATA_DIR / 'alert_dian_config.json'

# Default configurations
DEFAULT_ALERT_CONFIG = {
    'sales_drop_threshold': 0.3,
    'conversion_drop_threshold': 0.2,
    'inventory_low_threshold': 10,
    'notification_email': os.getenv('ALERT_EMAIL', ''),
    'enabled': True
}

DEFAULT_ALERT_DOUYIN_CONFIG = {
    'video_view_drop_threshold': 0.3,
    'video_like_drop_threshold': 0.2,
    'creator_follower_drop_threshold': 0.1,
    'notification_email': os.getenv('ALERT_EMAIL', ''),
    'enabled': True
}

DEFAULT_ALERT_DIAN_CONFIG = {
    'product_sales_drop_threshold': 0.3,
    'order_refund_rate_threshold': 0.15,
    'compliance_risk_threshold': 'medium',
    'notification_email': os.getenv('ALERT_EMAIL', ''),
    'enabled': True
}

DEFAULT_AUTH_CONFIG = {
    'douyin_app_id': '',
    'douyin_app_secret': '',
    'redirect_uri': '',
    'authorized': False,
    'access_token': '',
    'refresh_token': '',
    'expires_at': 0,
    'scope': []
}

DEFAULT_VIDEOS = []
DEFAULT_ACCOUNTS = []
DEFAULT_COMPLIANCE = []
DEFAULT_MEDIA = []


def _read_secret(secret_name: str, env_var: str = None, default: str = '') -> str:
    """Read secret from environment variable first, then Docker secret file, then default."""
    if env_var:
        env_val = os.getenv(env_var)
        if env_val is not None and env_val != '':
            return env_val
    secret_path = Path(f'/run/secrets/{secret_name}')
    if secret_path.exists():
        try:
            return secret_path.read_text().strip()
        except Exception:
            pass
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


# HTTP 请求重试装饰器（指数退避 + 抖动）
def _http_retry(max_retries=3, base_delay=1.0, max_delay=10.0, timeout=30):
    """HTTP 请求重试装饰器（指数退避 + 抖动）"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.ConnectionError, requests.Timeout, requests.RequestException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        logger.warning(f"HTTP 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}, {delay:.2f}s 后重试")
                        time.sleep(delay)
                    else:
                        logger.error(f"HTTP 请求最终失败 (已重试 {max_retries} 次): {e}")
            raise last_exception
        return wrapper
    return decorator


def parse_cookies(cookie_str: str) -> dict:
    """Parse cookie string to dict."""
    cookies = {}
    if not cookie_str:
        return cookies
    for pair in cookie_str.split(';'):
        pair = pair.strip()
        if '=' in pair:
            k, v = pair.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies


def get_fxg_cookies() -> dict:
    """Get fxg.jinritemai.com cookies."""
    cookie_str = _read_secret('fxg_cookies', 'FXG_COOKIES')
    return parse_cookies(cookie_str)


def get_creator_cookies() -> dict:
    """Get creator.douyin.com cookies."""
    cookie_str = _read_secret('creator_cookies', 'CREATOR_COOKIES')
    return parse_cookies(cookie_str)


def save_json_file(file_path: Path, data: Any) -> None:
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")


def load_json_file(
    file_path: Path, 
    default: Any = None, 
    model_type: Optional[str] = None
) -> Any:
    """Load JSON file with optional Pydantic validation, return default if not exists.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or validation fails
        model_type: Optional model type key from MODEL_MAP for validation
        
    Returns:
        Parsed and validated data, or default
    """
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Apply Pydantic validation if model_type provided
            if model_type:
                from models import validate_data, validate_single, MODEL_MAP
                if isinstance(data, list) and model_type in MODEL_MAP:
                    return validate_data(data, model_type)
                elif isinstance(data, dict) and model_type in MODEL_MAP:
                    return validate_single(data, model_type)
            
            return data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from {file_path}")
            return default
        except Exception as e:
            logger.error(f"Validation failed for {file_path} (model_type={model_type}): {e}")
            return default
    return default


# ==================== Product Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_products_from_api() -> List[Dict[str, Any]]:
    """Fetch products from external FXG API."""
    logger.info("Fetching products from external FXG API...")
    
    endpoint = f"{Config.FXG_BASE_URL}/product/tproduct/list"
    base_params = {
        'page': 0,
        'pageSize': 20,
    }
    
    params = base_params
    
    cookie_str = os.getenv('FXG_COOKIES', '')
    headers = {
        'User-Agent': Config.USER_AGENT,
        'Referer': 'https://fxg.jinritemai.com/product/tproduct/list',
        'Cookie': cookie_str,
    }
    
    resp = requests.get(endpoint, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    # 外部 API 实际返回格式：{ st, msg, code, data: [...], page, size, total }
    # data 是直接的产品列表，不是包含 products 键的字典
    data_block = result.get('data')
    if isinstance(data_block, list):
        products = data_block
    elif isinstance(data_block, dict):
        products = data_block.get('products', [])
    else:
        products = []
    
    # 确保每个产品都有合规检查所需的关键字段
    for product in products:
        # 基础字段转换和默认值
        product.setdefault('product_id', product.get('id', ''))
        product.setdefault('product_name', product.get('name', product.get('product_name', 'Unknown')))
        product.setdefault('sales_today', product.get('sales_today', product.get('today_sales', 0)))
        product.setdefault('sales_yesterday', product.get('sales_yesterday', product.get('yesterday_sales', 0)))
        product.setdefault('inventory', product.get('inventory', product.get('stock', 0)))
        product.setdefault('conversion_rate', product.get('conversion_rate', product.get('convert_rate', 0.0)))
        product.setdefault('conversion_rate_today', product.get('conversion_rate_today', product.get('today_convert_rate', 0.0)))
        product.setdefault('conversion_rate_yesterday', product.get('conversion_rate_yesterday', product.get('yesterday_convert_rate', 0.0)))
        # Ensure numeric types
        try:
            product['sales_today'] = int(product['sales_today'])
        except (ValueError, TypeError):
            product['sales_today'] = 0
        try:
            product['sales_yesterday'] = int(product['sales_yesterday'])
        except (ValueError, TypeError):
            product['sales_yesterday'] = 0
        try:
            product['inventory'] = int(product['inventory'])
        except (ValueError, TypeError):
            product['inventory'] = 0
        try:
            product['conversion_rate'] = float(product['conversion_rate'])
        except (ValueError, TypeError):
            product['conversion_rate'] = 0.0
        try:
            product['conversion_rate_today'] = float(product['conversion_rate_today'])
        except (ValueError, TypeError):
            product['conversion_rate_today'] = 0.0
        try:
            product['conversion_rate_yesterday'] = float(product['conversion_rate_yesterday'])
        except (ValueError, TypeError):
            product['conversion_rate_yesterday'] = 0.0
    
    logger.info(f"Fetched {len(products)} products from API (page={params['page']}, pageSize={params['pageSize']}, total={result.get('total', 'unknown')})")
    return products


def _classify_error(error: Exception) -> Dict[str, str]:
    """将异常分类为标准错误类型，便于监控和告警。
    
    Returns:
        Dict with 'error_type' and 'error_code' keys
    """
    error_msg = str(error).lower()
    
    # 外部 API 错误码分类（参考 API_SPEC.md）
    if any(code in error_msg for code in ['40101', '10008', 'cookie expired', 'cookie 过期', 'login required']):
        return {'error_type': 'COOKIE_EXPIRED', 'error_code': '40101'}
    if any(code in error_msg for code in ['40301', 'signature', '签名', 'sign error', 'a_bogus', 'msToken']):
        return {'error_type': 'SIGNATURE_ERROR', 'error_code': '40301'}
    if any(code in error_msg for code in ['429', 'rate limit', '限流', 'too many requests']):
        return {'error_type': 'RATE_LIMITED', 'error_code': '429'}
    if any(code in error_msg for code in ['10001010A', 'risk control', '风控']):
        return {'error_type': 'RISK_CONTROL', 'error_code': '10001010A'}
    if isinstance(error, requests.ConnectionError):
        return {'error_type': 'CONNECTION_ERROR', 'error_code': 'CONN_ERR'}
    if isinstance(error, requests.Timeout):
        return {'error_type': 'TIMEOUT', 'error_code': 'TIMEOUT'}
    if isinstance(error, requests.HTTPError):
        return {'error_type': 'HTTP_ERROR', 'error_code': str(error.response.status_code) if error.response else 'HTTP_ERR'}
    if isinstance(error, requests.RequestException):
        return {'error_type': 'EXTERNAL_API_ERROR', 'error_code': 'EXT_API_ERR'}
    
    return {'error_type': 'EXCEPTION', 'error_code': 'UNKNOWN'}


def fetch_and_store_products() -> Dict[str, Any]:
    """Fetch products from API and store in Redis + JSON file."""
    try:
        products = _fetch_products_from_api()
        
        # Transform and store
        for product in products:
            product['fetched_at'] = datetime.now().isoformat()
            product['sales_today'] = product.get('sales_today', 0)
            product['sales_yesterday'] = product.get('sales_yesterday', 0)
            product['inventory'] = product.get('inventory', 0)
            product['conversion_rate'] = product.get('conversion_rate', 0.0)
            product['conversion_rate_today'] = product.get('conversion_rate_today', 0.0)
            product['conversion_rate_yesterday'] = product.get('conversion_rate_yesterday', 0.0)
        
        # Store in Redis cache
        cache.set(CACHE_KEYS['products'], products)
        # Also save to JSON file for persistence
        save_json_file(PRODUCTS_FILE, products)
        logger.info(f"Fetched and stored {len(products)} products")
        
        return {'status': 'success', 'count': len(products)}
        
    except Exception as e:
        error_info = _classify_error(e)
        logger.error(f"Failed to fetch products: {e}", extra=error_info)
        return {
            'status': 'error', 
            'message': str(e),
            'error_type': error_info['error_type'],
            'error_code': error_info['error_code']
        }


# ==================== Order Fetching ====================

@_http_retry(max_retries=3, base_delay=5.0, max_delay=30.0)
def _fetch_orders_from_api() -> List[Dict[str, Any]]:
    """Fetch orders from external FXG API using _request with skip_sign=True.
    
    Per API spec: searchlist does NOT need a_bogus/msToken (short-lived, minutes).
    Only needs long-lived params: __token, verifyFp, fp.
    Uses skip_sign=True to prevent auto-injection of expired msToken/a_bogus.
    """
    logger.info("Fetching orders from external FXG API...")
    
    endpoint = f'{Config.FXG_BASE_URL}/api/order/searchlist'
    
    # 稳定签名参数（从配置读取，不随请求变化，不易过期）
    # __token、verifyFp、fp 为长效参数，直接加入请求参数
    # msToken、a_bogus 为强时效参数（几分钟失效），通过 skip_sign=True 跳过自动注入
    token = _read_secret('token', '__TOKEN')
    verify_fp = _read_secret('verify_fp', 'verifyFp')
    fp = _read_secret('fp', 'fp')
    
    base_params = {
        'page': 0,
        'pageSize': 10,
        'order_by': 'create_time',
        'order': 'desc',
        'tab': 'all',
        'appid': 1,
        '_bid': 'ffa_order',
        'aid': Config.FXG_ORDER_AID,
        '_lid': '606316310312',  # 使用实测有效的 _lid 值（用户浏览器抓包值）
    }
    # 追加稳定签名参数（仅当配置存在时）
    if token:
        base_params['__token'] = token
    if verify_fp:
        base_params['verifyFp'] = verify_fp
    if fp:
        base_params['fp'] = fp
    
    cookie_str = os.getenv('FXG_COOKIES', '')
    cookies = {}
    if cookie_str:
        for pair in cookie_str.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    
    # 使用完整的浏览器指纹头部，模拟真实浏览器请求以获取丰富数据
    # 参考浏览器抓包：包含 Sec-Fetch-*, Sec-Ch-Ua*, Priority, 详细 Referer 等
    headers = {
        **Config.COMMON_HEADERS,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://fxg.jinritemai.com/ffa/order',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Ch-Ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    
    # 使用 _request 并设置 skip_sign=True，避免自动注入过期的 msToken/a_bogus
    # 这是按 API 规范要求的：searchlist 不需要动态签名
    result = _request(
        endpoint=endpoint,
        params=base_params,
        headers=headers,
        cookies=cookies,
        method='GET',
        skip_sign=True  # 关键：跳过 a_bogus/msToken 自动注入
    )
    
    # _request 失败时返回 {'data': {}, 'error': ...}，需检查
    if isinstance(result, dict) and result.get('error'):
        raise requests.RequestException(f"External API error: {result.get('error')}")
    
    # 兼容不同的返回结构
    if isinstance(result, list):
        orders = result
    elif isinstance(result, dict):
        data_block = result.get('data')
        if isinstance(data_block, list):
            orders = data_block
        elif isinstance(data_block, dict):
            orders = data_block.get('orders', [])
        else:
            orders = result.get('orders', [])
    else:
        orders = []
    return orders


def fetch_and_store_orders() -> Dict[str, Any]:
    """Fetch orders from API and store in Redis + JSON file."""
    try:
        orders = _fetch_orders_from_api()
        
        # Transform and store
        for order in orders:
            order['fetched_at'] = datetime.now().isoformat()
        
        # Store in Redis cache
        cache.set(CACHE_KEYS['orders'], orders)
        # Also save to JSON file for persistence
        save_json_file(ORDERS_FILE, orders)
        logger.info(f"Fetched and stored {len(orders)} orders")
        
        return {'status': 'success', 'count': len(orders)}
        
    except Exception as e:
        error_info = _classify_error(e)
        logger.error(f"Failed to fetch orders: {e}", extra=error_info)
        return {
            'status': 'error', 
            'message': str(e),
            'error_type': error_info['error_type'],
            'error_code': error_info['error_code']
        }


# ==================== Creator Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_creators_from_api() -> List[Dict[str, Any]]:
    """Fetch creators from external Creator API.
    
    Per API spec: Creator center MUST use cookies dict parameter (requests cookies=),
    NOT Cookie header string. Parse cookie string to dict first.
    """
    logger.info("Fetching creators from external Creator API...")
    
    url = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
    payload = {"recent_days": 7}
    cookie_str = os.getenv('CREATOR_COOKIES', '')
    
    # Parse cookie string to dict (required for creator.douyin.com endpoints)
    cookies = {}
    if cookie_str:
        for pair in cookie_str.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    
    headers = {
        'User-Agent': Config.USER_AGENT,
        'Referer': 'https://creator.douyin.com/',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }
    
    response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    # 外部 API 返回 metrics 数组，需解析映射到 creators 列表格式
    # 兼容旧格式：data.creators 以及新格式：metrics 数组
    if 'creators' in result.get('data', {}):
        return result['data']['creators']
    
    metrics = result.get('metrics') or result.get('data', {}).get('metrics', [])
    if not metrics:
        return []
    
    # 将 metrics 数组转换为单个 creator 信息 dict
    metric_map = {m.get('english_metric_name'): m.get('metric_value', 0) for m in metrics}
    creator_info = {
        'total_followers'    : _metric_value(metric_map, 'total_followers'),
        'total_videos'       : _metric_value(metric_map, 'total_videos'),
        'total_views'        : _metric_value(metric_map, 'total_views'),
        'total_likes'        : _metric_value(metric_map, 'total_likes'),
        'total_comments'     : _metric_value(metric_map, 'total_comments'),
        'total_shares'       : _metric_value(metric_map, 'total_shares'),
        'recent_followers_gain': _metric_value(metric_map, 'recent_followers_gain'),
    }
    return [creator_info]


@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_creator_overview_from_api(recent_days: int = 7) -> Dict[str, Any]:
    """Fetch creator overview from external Creator API.
    
    Per API spec: Creator center MUST use cookies dict parameter (requests cookies=),
    NOT Cookie header string. Parse cookie string to dict first.
    """
    logger.info(f"Fetching creator overview from external Creator API (recent_days={recent_days})...")

    url = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
    payload = {"recent_days": recent_days}
    cookie_str = os.getenv('CREATOR_COOKIES', '')
    
    # Parse cookie string to dict (required for creator.douyin.com endpoints)
    cookies = {}
    if cookie_str:
        for pair in cookie_str.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v

    headers = {
        'User-Agent': Config.USER_AGENT,
        'Referer': 'https://creator.douyin.com/',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=30)
    response.raise_for_status()
    result = response.json()

    # 外部 API 实际返回格式：{ metrics: [{english_metric_name, metric_name, metric_value, trends}, ...] }
    # 兼容旧格式：{ code: 0, data: { total_followers, total_videos, recent_view, recent_like } }
    if 'total_followers' in result.get('data', {}):
        data = result.get('data', {})
        return {
            'total_followers': data.get('total_followers', 0),
            'total_videos': data.get('total_videos', 0),
            'recent_view': data.get('recent_view', 0),
            'recent_like': data.get('recent_like', 0),
            'recent_share': data.get('recent_share', 0),
            'recent_comment': data.get('recent_comment', 0),
            'recent_homepage_view': data.get('recent_homepage_view', 0),
            'cover_click_ratio': data.get('cover_click_ratio', 0),
            'net_followers_gain': data.get('net_followers_gain', 0),
            'cancel_followers': data.get('cancel_followers', 0),
            'completion_rate_5s': data.get('completion_rate_5s', 0),
            'bounce_rate_2s': data.get('bounce_rate_2s', 0),
            'avg_view_second': data.get('avg_view_second', 0),
            'total_views': data.get('total_views', 0),
            'total_likes': data.get('total_likes', 0),
            'total_comments': data.get('total_comments', 0),
            'total_shares': data.get('total_shares', 0),
        }
    
    metrics = result.get('metrics') or result.get('data', {}).get('metrics', [])
    if not metrics:
        return {
            'total_followers': 0,
            'total_videos': 0,
            'recent_view': 0,
            'recent_like': 0,
            'recent_share': 0,
            'recent_comment': 0,
            'recent_homepage_view': 0,
            'cover_click_ratio': 0,
            'net_followers_gain': 0,
            'cancel_followers': 0,
            'completion_rate_5s': 0,
            'bounce_rate_2s': 0,
            'avg_view_second': 0,
            'total_views': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_shares': 0,
        }
    
    # 将 metrics 数组转换为 dict，使用 _metric_value 进行别名回退
    metric_map = {m.get('english_metric_name'): m.get('metric_value', 0) for m in metrics}
    return {
        'total_followers': _metric_value(metric_map, 'total_followers'),
        'total_videos': _metric_value(metric_map, 'total_videos'),
        'total_views': _metric_value(metric_map, 'total_views'),
        'total_likes': _metric_value(metric_map, 'total_likes'),
        'total_comments': _metric_value(metric_map, 'total_comments'),
        'total_shares': _metric_value(metric_map, 'total_shares'),
        'recent_view': _metric_value(metric_map, 'total_views'),  # 兼容旧字段名
        'recent_like': _metric_value(metric_map, 'total_likes'),  # 兼容旧字段名
        'recent_share': _metric_value(metric_map, 'recent_share'),
        'recent_comment': _metric_value(metric_map, 'recent_comment'),
        'recent_homepage_view': _metric_value(metric_map, 'recent_homepage_view'),
        'cover_click_ratio': _metric_value(metric_map, 'cover_click_ratio'),
        'net_followers_gain': _metric_value(metric_map, 'recent_followers_gain'),
        'cancel_followers': _metric_value(metric_map, 'cancel_followers'),
        'completion_rate_5s': _metric_value(metric_map, 'completion_rate_5s'),
        'bounce_rate_2s': _metric_value(metric_map, 'bounce_rate_2s'),
        'avg_view_second': _metric_value(metric_map, 'avg_view_second'),
    }


def fetch_and_store_creators() -> Dict[str, Any]:
    """Fetch creators from API and store in Redis + JSON file."""
    try:
        creators = _fetch_creators_from_api()
        
        # Ensure each creator has fetched_at timestamp
        for creator in creators:
            creator['fetched_at'] = datetime.now().isoformat()
        
        # Store in Redis cache
        cache.set(CACHE_KEYS['creators'], creators)
        # Also save to JSON file for persistence
        save_json_file(CREATORS_FILE, creators)
        logger.info(f"Fetched and stored {len(creators)} creators")
        
        return {'status': 'success', 'count': len(creators)}
        
    except Exception as e:
        error_info = _classify_error(e)
        logger.error(f"Failed to fetch creators: {e}", extra=error_info)
        return {
            'status': 'error', 
            'message': str(e),
            'error_type': error_info['error_type'],
            'error_code': error_info['error_code']
        }


# ==================== Creator Works Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_creator_works_from_api(recent_days: int = None) -> List[Dict[str, Any]]:
    """Fetch creator works from external Creator API.

    Per API spec: Creator center works list MUST use cookies dict parameter (requests cookies=),
    NOT Cookie header string. Parse cookie string to dict first.

    Args:
        recent_days: 可选，仅保留最近 N 天内发布的作品（按 create_time unix 时间戳过滤）
    """
    logger.info("Fetching creator works from external Creator API...")
    
    endpoint = Config.CREATOR_WORK_LIST_URL
    params = {
        'status': '0',
        'count': '12',
        'max_cursor': '0',
        'scene': 'star_atlas',
        'device_platform': 'android',
        'aid': Config.CREATOR_WORK_AID,
    }
    cookie_str = os.getenv('CREATOR_COOKIES', '')
    
    # Parse cookie string to dict (required for creator.douyin.com endpoints)
    cookies = {}
    if cookie_str:
        for pair in cookie_str.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    
    headers = {
        'User-Agent': Config.USER_AGENT,
        'Referer': 'https://creator.douyin.com/creator-micro/content/manage',
        'Accept': 'application/json, text/plain, */*',
    }
    
    resp = requests.get(endpoint, params=params, headers=headers, cookies=cookies, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    # 兼容不同的返回结构：aweme_list / data / works
    works = result.get('aweme_list') or result.get('items') or []
    if isinstance(works, dict):
        works = works.get('works', [])

    # 按 recent_days 过滤（create_time 为 unix 秒时间戳）
    if recent_days:
        cutoff = datetime.now().timestamp() - recent_days * 86400
        filtered = []
        for w in works:
            ct = w.get('create_time')
            if isinstance(ct, (int, float)) and ct >= cutoff:
                filtered.append(w)
        works = filtered
    return works


def fetch_and_store_creator_works() -> Dict[str, Any]:
    """Fetch creator works from API and store in Redis + JSON file."""
    try:
        works = _fetch_creator_works_from_api()
        
        # Transform and store
        for work in works:
            work['fetched_at'] = datetime.now().isoformat()
        
        # Store in Redis cache
        cache.set(CACHE_KEYS['creator_works'], works)
        # Also save to JSON file for persistence
        save_json_file(CREATOR_WORKS_FILE, works)
        logger.info(f"Fetched and stored {len(works)} creator works")
        
        return {'status': 'success', 'count': len(works)}
        
    except Exception as e:
        error_info = _classify_error(e)
        logger.error(f"Failed to fetch creator works: {e}", extra=error_info)
        return {
            'status': 'error', 
            'message': str(e),
            'error_type': error_info['error_type'],
            'error_code': error_info['error_code']
        }


# ==================== Videos Fetching ====================

def _transform_work_to_video(work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """将创作者作品 API 的原始 aweme 结构转换为前端 Videos 页面期望的扁平结构。

    映射关系（基于 creator_works.json 真实样本验证）：
      video_id      <- aweme_id
      title         <- desc
      creator_name  <- author.nickname
      play_count    <- statistics.play_count
      like_count    <- statistics.digg_count
      comment_count <- statistics.comment_count
      share_count   <- statistics.share_count
      duration      <- duration（毫秒 -> 秒）
      create_time   <- create_time（unix 秒 -> ISO8601）
      status        <- 'published'（作品列表 status=0 即已发布）
      cover_url     <- video.cover.url_list[0]（回退顶层 Cover）
      video_url     <- video.play_addr.url_list[0]
    """
    aweme_id = work.get('aweme_id')
    if not aweme_id:
        return None

    stats = work.get('statistics') or {}
    author = work.get('author') or {}
    video_info = work.get('video') or {}

    def _first_url(obj: Any) -> str:
        if isinstance(obj, dict):
            url_list = obj.get('url_list')
            if isinstance(url_list, list) and url_list:
                return str(url_list[0])
        return ''

    raw_duration = work.get('duration') or video_info.get('duration') or 0
    # 抖音 duration 为毫秒；>1000 视为毫秒转秒，否则原样保留
    duration = int(raw_duration) // 1000 if isinstance(raw_duration, (int, float)) and raw_duration > 1000 else int(raw_duration or 0)

    create_time = ''
    ct = work.get('create_time')
    if isinstance(ct, (int, float)):
        try:
            create_time = datetime.fromtimestamp(ct).isoformat()
        except (ValueError, OSError, OverflowError):
            create_time = ''

    cover_url = _first_url(video_info.get('cover')) or _first_url(work.get('Cover'))
    video_url = _first_url(video_info.get('play_addr'))

    return {
        'video_id': str(aweme_id),
        'title': work.get('desc') or work.get('caption') or '',
        'creator_name': author.get('nickname') or author.get('unique_id') or '',
        'play_count': int(stats.get('play_count') or 0),
        'like_count': int(stats.get('digg_count') or 0),
        'comment_count': int(stats.get('comment_count') or 0),
        'share_count': int(stats.get('share_count') or 0),
        'duration': duration,
        'create_time': create_time,
        'status': 'published',
        'cover_url': cover_url,
        'video_url': video_url,
    }


def _load_videos_from_file() -> List[Dict[str, Any]]:
    """兜底：从本地 videos.json 加载历史数据（不再生成假数据）。"""
    videos_file = DATA_DIR / 'videos.json'
    if videos_file.exists():
        try:
            with open(videos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} videos from data file (fallback)")
                return data
        except Exception as e:
            logger.warning(f"Failed to load videos from file: {e}")
    return []


def fetch_and_store_videos() -> Dict[str, Any]:
    """Fetch videos from Creator works API, transform to flat schema, store in Redis + JSON file.

    数据源优先级：
      1. 创作者作品 API（真实数据，经 _transform_work_to_video 转换）
      2. API 失败或返回空时：保留现有缓存/历史文件不动，不生成假数据
    """
    try:
        works = _fetch_creator_works_from_api()
        videos = [v for v in (_transform_work_to_video(w) for w in works) if v]

        if not videos:
            raise ValueError('Creator works API returned no transformable videos')

        now_iso = datetime.now().isoformat()
        for video in videos:
            video['fetched_at'] = now_iso

        cache.set(CACHE_KEYS['videos'], videos)
        save_json_file(DATA_DIR / 'videos.json', videos)
        logger.info(f"Fetched and stored {len(videos)} videos from creator works API")

        return {'status': 'success', 'count': len(videos), 'data_source': 'external'}

    except Exception as e:
        error_info = _classify_error(e)
        logger.error(f"Failed to fetch videos from creator works API: {e}", extra=error_info)
        # 兜底：保留现有缓存/文件，避免 API 故障期间清空前端数据
        existing = cache.get(CACHE_KEYS['videos'], None) or _load_videos_from_file()
        return {
            'status': 'error',
            'message': str(e),
            'error_type': error_info['error_type'],
            'error_code': error_info['error_code'],
            'fallback_count': len(existing),
        }


# ==================== Compliance Fetching ====================

def fetch_and_check_compliance() -> Dict[str, Any]:
    """Fetch products and run compliance checks against them using rule engine."""
    logger.info("Running compliance checks on real products...")
    
    try:
        products = cache.get(CACHE_KEYS['products'], [])
        if not products:
            logger.info("No products in cache, fetching from API...")
            products = _fetch_products_from_api()
            if products:
                for product in products:
                    product['fetched_at'] = datetime.now().isoformat()
                cache.set(CACHE_KEYS['products'], products)
                save_json_file(PRODUCTS_FILE, products)
        
        if not products:
            logger.warning("No products available for compliance check")
            return {
                'status': 'success',
                'message': 'No products to check',
                'checked': 0,
                'pass': 0,
                'fail': 0,
                'warning': 0,
                'details': []
            }
        
        rules = cache.get(CACHE_KEYS['compliance_rules'], [])
        enabled_rules = [r for r in rules if r.get('enabled', True)]
        
        if not enabled_rules:
            logger.warning("No enabled compliance rules found")
            return {
                'status': 'success',
                'message': 'No enabled rules to check',
                'checked': 0,
                'pass': 0,
                'fail': 0,
                'warning': 0,
                'details': []
            }
        
        logger.info("Running compliance check on {} products with {} rules".format(len(products), len(enabled_rules)))
        
        from services.rule_engine import run_compliance_check, CheckResult
        
        all_results = []
        total_checked = 0
        total_pass = 0
        total_fail = 0
        total_warning = 0
        
        for product in products:
            product_id = str(product.get('product_id') or product.get('id') or '')
            product_name = product.get('product_name', 'Unknown Product')
            
            if not product_id:
                logger.warning("Skipping product without ID: {}".format(product_name))
                continue
            
            total_checked += 1
            
            outcomes = run_compliance_check(
                target_data=product,
                target_type='product',
                target_id=product_id,
                rules=enabled_rules
            )
            
            product_results = {
                'product_id': product_id,
                'product_name': product_name,
                'checked_at': datetime.now().isoformat(),
                'rule_results': []
            }
            
            product_pass = 0
            product_fail = 0
            product_warning = 0
            
            for outcome in outcomes:
                if outcome.status == CheckResult.FAIL:
                    product_fail += 1
                elif outcome.status == CheckResult.WARNING:
                    product_warning += 1
                elif outcome.status == CheckResult.PASS:
                    product_pass += 1
                
                log_entry = {
                    'id': "log_" + str(int(datetime.now().timestamp())) + "_" + str(outcome.rule_id),
                    'rule_id': outcome.rule_id,
                    'rule_name': outcome.rule_name,
                    'rule_type': outcome.rule_type.value if hasattr(outcome.rule_type, 'value') else str(outcome.rule_type),
                    'target_type': 'product',
                    'target_id': product_id,
                    'target_name': product_name,
                    'status': outcome.status.value if hasattr(outcome.status, 'value') else str(outcome.status),
                    'details': outcome.details,
                    'matched_content': outcome.matched_content,
                    'checked_at': outcome.checked_at,
                    'execution_time_ms': outcome.execution_time_ms
                }
                
                product_results['rule_results'].append({
                    'rule_id': outcome.rule_id,
                    'rule_name': outcome.rule_name,
                    'rule_type': outcome.rule_type.value if hasattr(outcome.rule_type, 'value') else str(outcome.rule_type),
                    'status': outcome.status.value if hasattr(outcome.status, 'value') else str(outcome.status),
                    'message': outcome.message,
                    'details': outcome.details,
                    'matched_content': outcome.matched_content,
                    'execution_time_ms': outcome.execution_time_ms
                })
                
                all_results.append(log_entry)
            
            if product_fail > 0:
                product_results['overall_status'] = 'fail'
                total_fail += 1
            elif product_warning > 0:
                product_results['overall_status'] = 'warning'
                total_warning += 1
            else:
                product_results['overall_status'] = 'pass'
                total_pass += 1
            
            _append_compliance_log(product_results)
        
        logger.info("Compliance check completed: checked={}, pass={}, fail={}, warning={}".format(total_checked, total_pass, total_fail, total_warning))
        
        return {
            'status': 'success',
            'message': "Checked {} products".format(total_checked),
            'checked': total_checked,
            'pass': total_pass,
            'fail': total_fail,
            'warning': total_warning,
            'details': all_results
        }
        
    except Exception as e:
        logger.error("Compliance check failed: {}".format(e))
        return {
            'status': 'error',
            'message': "Compliance check failed: {}".format(str(e)),
            'checked': 0,
            'pass': 0,
            'fail': 0,
            'warning': 0,
            'details': []
        }


def _append_compliance_log(log_entry):
    """Append a compliance check result to the logs cache and file."""
    try:
        existing_logs = cache.get(CACHE_KEYS['compliance_logs'], [])
        if not isinstance(existing_logs, list):
            existing_logs = []
        
        if 'rule_results' in log_entry:
            for rule_result in log_entry['rule_results']:
                entry = {
                    # 毫秒时间戳 + uuid 后缀，确保每条记录 ID 唯一（rowKey 冲突会导致表格渲染错乱）
                    'id': "log_" + str(int(datetime.now().timestamp() * 1000)) + "_" + str(rule_result['rule_id']) + "_" + uuid.uuid4().hex[:6],
                    'rule_id': rule_result['rule_id'],
                    'rule_name': rule_result['rule_name'],
                    'rule_type': rule_result['rule_type'],
                    'target_type': 'product',
                    'target_id': log_entry['product_id'],
                    'target_name': log_entry['product_name'],
                    'status': rule_result['status'],
                    'details': rule_result['details'],
                    'matched_content': rule_result.get('matched_content'),
                    'checked_at': log_entry['checked_at'],
                    # 前端"处理时间"列读取 created_at/updated_at，与 checked_at 保持一致
                    'created_at': log_entry.get('checked_at'),
                    'updated_at': log_entry.get('checked_at'),
                    'execution_time_ms': rule_result.get('execution_time_ms', 0)
                }
                existing_logs.insert(0, entry)
        else:
            existing_logs.insert(0, log_entry)
        
        if len(existing_logs) > 10000:
            existing_logs = existing_logs[:10000]
        
        cache.set(CACHE_KEYS['compliance_logs'], existing_logs)
        save_json_file(COMPLIANCE_FILE, existing_logs)
        
    except Exception as e:
        logger.error("Failed to append compliance log: {}".format(e))


# ==================== Compliance Rule Initialization ====================

def _init_default_compliance_rules() -> Dict[str, Any]:
    """Initialize compliance rules from JSON file at startup (force reload).
    
    启动时强制从 compliance_rules.json 文件加载规则，确保跨容器重启始终使用最新规则。
    仅当文件不存在或为空时，才回退到缓存或创建默认规则。
    
    Returns:
        Dict with initialization result status
    """
    from services.fetcher import cache, CACHE_KEYS
    from pathlib import Path
    import json
    
    rules_file = Path(__file__).parent.parent / 'data' / 'compliance_rules.json'
    
    # ✅ 方案1：启动时强制从 JSON 文件加载（优先级最高，确保跨重启一致性）
    if rules_file.exists():
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                loaded_rules = json.load(f)
            # 验证规则结构基本合法
            if isinstance(loaded_rules, list) and len(loaded_rules) > 0:
                logger.info(f"Loaded {len(loaded_rules)} compliance rules from file (startup forced)")
                # 始终同步到缓存
                cache.set(CACHE_KEYS['compliance_rules'], loaded_rules)
                # 确保文件持久化（防止手动修改丢失）
                try:
                    with open(rules_file, 'w', encoding='utf-8') as f:
                        json.dump(loaded_rules, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass  # 文件已存在且已读取成功
                return {'status': 'loaded_from_file', 'count': len(loaded_rules)}
            else:
                logger.warning("compliance_rules.json is empty, falling back to cache/fallback")
        except Exception as e:
            logger.warning(f"Failed to load compliance rules from file: {e}, falling back to cache/fallback")
    
    # ✅ 回退：检查缓存是否有规则
    rules = cache.get(CACHE_KEYS['compliance_rules'], None)
    if rules is not None and len(rules) > 0:
        logger.info(f"Using {len(rules)} compliance rules from cache (file empty/missing)")
        return {'status': 'used_from_cache', 'count': len(rules)}
    
    # ✅ 最后才回退：创建最小默认规则（不再生成大量 mock 数据）
    # 创建仅 1 条基础规则，确保系统可用而非充满模拟数据
    default_rules = [
        {
            'id': f"rule_{int(datetime.now().timestamp())}_base",
            'rule_name': '基础合规检测',
            'rule_type': 'KEYWORD',
            'rule_content': {
                'keywords': [],
                'fields': ['product_name', 'description'],
                'case_sensitive': False,
                'match_all': False
            },
            'severity': 'LOW',
            'category': '基础合规',
            'enabled': True
        }
    ]
    
    # 存储规则到缓存和文件
    cache.set(CACHE_KEYS['compliance_rules'], default_rules)
    
    # 持久化到 JSON 文件（确保下次启动能读取）
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(default_rules, f, ensure_ascii=False, indent=2)
        logger.info("Created 1 default compliance rule and persisted to file")
    except Exception as e:
        logger.warning(f"Failed to persist default rules to file: {e}")
    
    logger.info(f"Initialized {len(default_rules)} default compliance rule (fallback)")
    return {
        'status': 'initialized',
        'message': f'Initialized {len(default_rules)} default compliance rule (fallback)',
        'count': len(default_rules),
        'rules': [{'id': r['id'], 'rule_name': r['rule_name'], 'rule_type': r['rule_type'], 'enabled': r['enabled']} for r in default_rules]
    }


# Ensure default rules are initialized when module is imported (optional)
# This can be triggered manually via API or scheduled task

def get_alert_config() -> Dict[str, Any]:
    """Get current alert configuration from Redis cache."""
    config = cache.get(CACHE_KEYS['alert_config'])
    if config is None:
        return DEFAULT_ALERT_CONFIG
    return config


def check_alerts() -> Dict[str, Any]:
    """Check alert conditions and send notifications if needed."""
    alert_config = get_alert_config()
    
    if not alert_config.get('enabled', True):
        return {'status': 'skipped', 'reason': 'alerts disabled'}
    
    logger.info("Checking alert conditions...")
    
    products = cache.get(CACHE_KEYS['products'], [])
    alerts_triggered = []
    
    for product in products:
        product_name = product.get('product_name', 'Unknown')
        product_id = product.get('product_id', '')
        
        # Check sales drop
        sales_today = product.get('sales_today', 0)
        sales_yesterday = product.get('sales_yesterday', 0)
        
        if sales_yesterday > 0:
            drop_rate = (sales_yesterday - sales_today) / sales_yesterday
            if drop_rate >= alert_config['sales_drop_threshold']:
                alert = {
                    'type': 'sales_drop',
                    'product_id': product_id,
                    'product_name': product_name,
                    'message': f"Product {product_name} sales dropped by {drop_rate:.1%}",
                    'drop_rate': drop_rate,
                    'threshold': alert_config['sales_drop_threshold'],
                    'timestamp': datetime.now().isoformat()
                }
                alerts_triggered.append(alert)
                save_alert_to_history(alert)
                send_alert_notification(alert)

        # Check inventory
        inventory = product.get('inventory', 0)
        if inventory <= alert_config['inventory_low_threshold']:
            alert = {
                'type': 'low_inventory',
                'product_id': product_id,
                'product_name': product_name,
                'message': f"Product {product_name} inventory low: {inventory}",
                'inventory': inventory,
                'threshold': alert_config['inventory_low_threshold'],
                'timestamp': datetime.now().isoformat()
            }
            alerts_triggered.append(alert)
            save_alert_to_history(alert)
            send_alert_notification(alert)

        # Check conversion rate drop
        conv_today = product.get('conversion_rate_today', 0)
        conv_yesterday = product.get('conversion_rate_yesterday', 0)

        if conv_yesterday > 0:
            drop_rate = (conv_yesterday - conv_today) / conv_yesterday
            if drop_rate >= alert_config['conversion_drop_threshold']:
                alert = {
                    'type': 'conversion_drop',
                    'product_id': product_id,
                    'product_name': product_name,
                    'message': f"Product {product_name} conversion rate dropped by {drop_rate:.1%}",
                    'drop_rate': drop_rate,
                    'threshold': alert_config['conversion_drop_threshold'],
                    'timestamp': datetime.now().isoformat()
                }
                alerts_triggered.append(alert)
                save_alert_to_history(alert)
                send_alert_notification(alert)
    
    logger.info(f"Alert check completed. Triggered {len(alerts_triggered)} alerts")
    return {'status': 'success', 'alerts_triggered': len(alerts_triggered)}


def send_alert_notification(alert: Dict[str, Any]) -> None:
    """Send alert notification via WeChat Work webhook and email."""
    from utils.notifications import send_alert_notification as _send

    alert_config = get_alert_config()
    email = alert_config.get('notification_email')

    try:
        _send(alert, email=email)
    except Exception as e:
        logger.error(f"Failed to send alert notification: {e}")


# ==================== Alert History ====================

def save_alert_to_history(alert: Dict[str, Any]) -> None:
    """Persist triggered alert to history list in Redis cache."""
    history = cache.get(CACHE_KEYS['alert_history'], [])
    if not isinstance(history, list):
        history = []
    # Prepend new alert (most recent first)
    history.insert(0, alert)
    # Keep only last 500 alerts to avoid memory bloat
    if len(history) > 500:
        history = history[:500]
    cache.set(CACHE_KEYS['alert_history'], history)


def get_alert_history(
    limit: int = 50,
    offset: int = 0,
    alert_type: str = None,
) -> Dict[str, Any]:
    """Get paginated alert history with optional type filter."""
    history = cache.get(CACHE_KEYS['alert_history'], [])
    if not isinstance(history, list):
        history = []

    # Filter by type if specified
    if alert_type:
        history = [a for a in history if a.get('type') == alert_type]

    total = len(history)
    # Paginate
    paginated = history[offset:offset + limit]

    return {
        'list': paginated,
        'total': total,
        'limit': limit,
        'offset': offset,
    }


def clear_alert_history() -> int:
    """Clear all alert history. Returns count of cleared alerts."""
    history = cache.get(CACHE_KEYS['alert_history'], [])
    count = len(history) if isinstance(history, list) else 0
    cache.set(CACHE_KEYS['alert_history'], [])
    return count


# ==================== Data Initialization ====================

def init_compliance_data() -> None:
    """Initialize compliance data from JSON files (force reload at startup).
    
    启动时强制从 JSON 文件加载合规数据，确保跨容器重启始终使用最新规则和日志。
    仅当文件不存在或为空时，才回退到创建最小默认数据。
    """
    from pathlib import Path
    import json
    from services.fetcher import cache, CACHE_KEYS, COMPLIANCE_RULES_FILE, COMPLIANCE_FILE
    from models import validate_data
    
    # ✅ 方案1：启动时强制从 JSON 文件加载规则（优先级最高）
    rules_file = Path(__file__).parent.parent / 'data' / 'compliance_rules.json'
    if rules_file.exists():
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                loaded_rules = json.load(f)
            if isinstance(loaded_rules, list) and len(loaded_rules) > 0:
                logger.info(f"Loaded {len(loaded_rules)} compliance rules from file (init_compliance_data)")
                validated_rules = validate_data(loaded_rules, 'compliance_rules')
                cache.set(CACHE_KEYS['compliance_rules'], validated_rules)
                # 持久化到文件（确保最新状态）
                try:
                    with open(rules_file, 'w', encoding='utf-8') as f:
                        json.dump(validated_rules, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            else:
                logger.warning("compliance_rules.json is empty")
        except Exception as e:
            logger.warning(f"Failed to load compliance rules from file: {e}")
    
    # ✅ 回退：检查缓存是否有规则（当文件不存在或为空时）
    existing_rules = cache.get(CACHE_KEYS['compliance_rules'], None)
    if existing_rules is not None and len(existing_rules) > 0:
        logger.info(f"Using {len(existing_rules)} compliance rules from cache")
    else:
        # 缓存中无规则，但文件可能已存在且非空（上一步可能已处理）
        logger.info("No compliance rules in cache, using minimal fallback")
    
    # Initialize compliance logs from JSON file
    logs_file = Path(__file__).parent.parent / 'data' / 'compliance.json'
    if logs_file.exists():
        try:
            with open(logs_file, 'r', encoding='utf-8') as f:
                loaded_logs = json.load(f)
            if isinstance(loaded_logs, list) and len(loaded_logs) > 0:
                logger.info(f"Loaded {len(loaded_logs)} compliance logs from file")
                # 验证并存入缓存
                try:
                    validated_logs = validate_data(loaded_logs, 'compliance_logs')
                    cache.set(CACHE_KEYS['compliance_logs'], validated_logs)
                except Exception:
                    cache.set(CACHE_KEYS['compliance_logs'], loaded_logs)
                # 持久化
                try:
                    with open(logs_file, 'w', encoding='utf-8') as f:
                        json.dump(validated_logs, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            else:
                logger.warning("compliance.json is empty, using fallback")
        except Exception as e:
            logger.warning(f"Failed to load compliance logs from file: {e}")
    
    # 最后回退：如果缓存中仍无日志，创建 1 条基础日志记录
    existing_logs = cache.get(CACHE_KEYS['compliance_logs'], [])
    if not existing_logs or len(existing_logs) == 0:
        default_log = {
            'id': 'log_base',
            'rule_id': 'rule_base',
            'target_type': 'product',
            'target_id': '',
            'target_name': '',
            'status': 'pass',
            'details': {'matched_keywords': [], 'checked_fields': []},
            'checked_at': datetime.now().isoformat()
        }
        cache.set(CACHE_KEYS['compliance_logs'], [default_log])
        logger.info("Created 1 default compliance log (fallback)")


def load_all_data() -> None:
    """Load all data files into Redis cache with Pydantic validation."""
    # Load data into Redis cache (list types with automatic validation)
    data_map = {
        'products': (PRODUCTS_FILE, []),
        'orders': (ORDERS_FILE, []),
        'creators': (CREATORS_FILE, []),
        'videos': (VIDEOS_FILE, DEFAULT_VIDEOS),
        'accounts': (ACCOUNTS_FILE, DEFAULT_ACCOUNTS),
        'compliance_rules': (COMPLIANCE_RULES_FILE, DEFAULT_COMPLIANCE),
        'media': (MEDIA_FILE, DEFAULT_MEDIA),
        'auth': (AUTH_FILE, DEFAULT_AUTH_CONFIG),
        'creator_works': (CREATOR_WORKS_FILE, []),
    }
    
    for key, (file_path, default) in data_map.items():
        data = load_json_file(file_path, default, model_type=key)
        cache.set(CACHE_KEYS[key], data)
    
    # Load configs into Redis (dict types with automatic validation)
    config_map = {
        'alert_config': (ALERT_CONFIG_FILE, DEFAULT_ALERT_CONFIG),
        'alert_douyin_config': (ALERT_DOUYIN_CONFIG_FILE, DEFAULT_ALERT_DOUYIN_CONFIG),
        'alert_dian_config': (ALERT_DIAN_CONFIG_FILE, DEFAULT_ALERT_DIAN_CONFIG),
        'auth_config': (AUTH_FILE, DEFAULT_AUTH_CONFIG),
    }
    
    for key, (file_path, default) in config_map.items():
        data = load_json_file(file_path, default, model_type=key)
        cache.set(CACHE_KEYS[key], data)
    
    cache.set('last_update', datetime.now().isoformat())
    
    # Initialize compliance data
    init_compliance_data()
    
    logger.info("All data loaded successfully with Pydantic validation")


def save_all_data() -> None:
    """Save all cached data from Redis to JSON files."""
    save_json_file(PRODUCTS_FILE, cache.get(CACHE_KEYS['products'], []))
    save_json_file(ORDERS_FILE, cache.get(CACHE_KEYS['orders'], []))
    save_json_file(CREATORS_FILE, cache.get(CACHE_KEYS['creators'], []))
    save_json_file(VIDEOS_FILE, cache.get(CACHE_KEYS['videos'], []))
    save_json_file(ACCOUNTS_FILE, cache.get(CACHE_KEYS['accounts'], []))
    save_json_file(COMPLIANCE_RULES_FILE, cache.get(CACHE_KEYS['compliance_rules'], []))
    save_json_file(MEDIA_FILE, cache.get(CACHE_KEYS['media'], []))
    save_json_file(AUTH_FILE, cache.get(CACHE_KEYS['auth'], []))
    save_json_file(CREATOR_WORKS_FILE, cache.get(CACHE_KEYS['creator_works'], []))
    save_json_file(ALERT_CONFIG_FILE, cache.get(CACHE_KEYS['alert_config'], {}))
    save_json_file(ALERT_DOUYIN_CONFIG_FILE, cache.get(CACHE_KEYS['alert_douyin_config'], {}))
    save_json_file(ALERT_DIAN_CONFIG_FILE, cache.get(CACHE_KEYS['alert_dian_config'], {}))
    logger.info("All data saved successfully")


# ==================== Scheduled Job ====================

# 分布式锁配置
SYNC_LOCK_KEY = "douyin:monitor:sync:lock"
SYNC_LOCK_TTL = 300  # 5 分钟锁过期时间（防止死锁）

# File-based lock fallback
SYNC_LOCK_FILE = DATA_DIR / '.sync.lock'


def _acquire_sync_lock() -> bool:
    """尝试获取同步分布式锁（基于 Redis SET NX EX），降级到文件锁。
    
    Returns:
        True 如果获取锁成功，False 如果锁已被占用
    """
    # Try Redis first
    if is_redis_available():
        try:
            # 使用 SET key value NX EX 实现原子加锁
            result = cache._client.set(SYNC_LOCK_KEY, "1", nx=True, ex=SYNC_LOCK_TTL)
            if result:
                logger.info("Acquired sync lock (Redis)")
                return True
            else:
                logger.warning("Sync lock already held by another process, skipping this run")
                return False
        except Exception as e:
            logger.warning(f"Redis lock failed, falling back to file lock: {e}")
    
    # Fallback to file-based lock
    try:
        import fcntl
        lock_file = open(SYNC_LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        # Store lock file handle for release
        _acquire_sync_lock._lock_file = lock_file
        logger.info("Acquired sync lock (file)")
        return True
    except (IOError, OSError) as e:
        logger.warning(f"Sync lock already held by another process (file), skipping this run: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to acquire file sync lock: {e}")
        # 锁获取失败时，为了不阻塞业务，允许继续执行（但记录警告）
        return True


def _release_sync_lock() -> None:
    """释放同步分布式锁。"""
    # Try Redis first
    if is_redis_available():
        try:
            cache._client.delete(SYNC_LOCK_KEY)
            logger.info("Released sync lock (Redis)")
            return
        except Exception as e:
            logger.warning(f"Redis unlock failed, trying file lock: {e}")
    
    # Fallback to file-based lock
    try:
        import fcntl
        lock_file = getattr(_acquire_sync_lock, '_lock_file', None)
        if lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            if SYNC_LOCK_FILE.exists():
                SYNC_LOCK_FILE.unlink()
            logger.info("Released sync lock (file)")
    except Exception as e:
        logger.error(f"Failed to release file sync lock: {e}")


def _check_and_log_auth_errors(results: Dict[str, Any]) -> None:
    """检测 AUTH_ERROR (Cookie 失效) 并仅记录日志（方式 2：最保守）。
    
    此函数不修改 os.environ，不重新执行任务，仅在日志中标记
    哪些服务出现了 Cookie 失效，留给运维人工介入。
    
    Args:
        results: scheduled_job() 返回的各任务结果字典
    """
    auth_services = []
    
    for key, result in (results or {}).items():
        if isinstance(result, dict):
            # _classify_error 返回的 error_type 包含 'COOKIE_EXPIRED' 等
            error_type = result.get('error_type', '')
            error_code = result.get('error_code', '')
            if error_type in ('AUTH_ERROR', 'COOKIE_EXPIRED'):
                auth_services.append({
                    'service': key,
                    'error_code': error_code,
                    'message': result.get('message', '')[:120]
                })
    
    if auth_services:
        logger.warning(
            f"Cookie 失效检测: {len(auth_services)} 个服务需要人工介入",
            extra={
                'event': 'cookie_expired_detected',
                'affected_services': [s['service'] for s in auth_services],
                'error_codes': [s['error_code'] for s in auth_services],
                'require_action': 'manual_refresh_cookies',
                'auto_mode': 'log_only_way2'
            }
        )
        # 此处仅记录日志，不自动刷新 os.environ，
        # 不重新执行任务，留给运维人工判断是否需要介入
    # 如果没有 AUTH_ERROR/COOKIE_EXPIRED，静默返回，不影响流程


def scheduled_job() -> Dict[str, Any]:
    """Main scheduled job to fetch all data and check alerts.
    This function is called by Celery Beat tasks.
    
    使用分布式锁防止并发执行（Celery Beat + 手动触发 /api/v1/sync 可能并发）。
    """
    # CST 时区 (UTC+8)
    CST = timezone(timedelta(hours=8))
    
    # 尝试获取分布式锁
    if not _acquire_sync_lock():
        return {
            'status': 'skipped',
            'reason': 'another_sync_in_progress',
            'message': 'Another sync task is already running, skipping this execution'
        }
    
    logger.info("Running scheduled job...")
    start_time = datetime.now(CST)

    results = {}
    results['products'] = fetch_and_store_products()
    results['orders'] = fetch_and_store_orders()
    results['creators'] = fetch_and_store_creators()
    results['creator_works'] = fetch_and_store_creator_works()
    results['compliance'] = fetch_and_check_compliance()
    results['alerts'] = check_alerts()
    
    # 【P1】方式 2：检测 AUTH_ERROR 并仅记录日志（不自动刷新）
    _check_and_log_auth_errors(results)

    end_time = datetime.now(CST)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Update last_update (Redis or file fallback)
    last_update_file = DATA_DIR / 'last_update.json'
    try:
        if is_redis_available():
            cache.set('last_update', end_time.isoformat())
        else:
            save_json_file(last_update_file, {'last_update': end_time.isoformat()})
    except Exception as e:
        logger.warning(f"Failed to update last_update: {e}")

    # 释放锁
    _release_sync_lock()

    # 计算整体状态
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

    logger.info("Scheduled job completed in %dms with status: %s", duration_ms, overall_status)
    return {'status': overall_status, 'results': results, 'duration_ms': duration_ms}


def _calculate_overall_status(results: Dict[str, Any]) -> str:
    """根据各子任务结果计算整体同步状态。
    
    Returns:
        'success' - 全部成功
        'partial' - 部分成功部分失败
        'failed' - 全部失败
    """
    statuses = [_extract_status(r) for r in results.values()]
    success_count = sum(1 for s in statuses if s == 'success')
    error_count = sum(1 for s in statuses if s == 'error')
    
    if error_count == 0:
        return 'success'
    elif success_count == 0:
        return 'failed'
    else:
        return 'partial'


def _extract_status(result: Any) -> str:
    """Extract status string from fetch result."""
    if isinstance(result, dict):
        return result.get('status', 'unknown')
    return 'unknown'


# File-based sync history fallback
SYNC_HISTORY_FILE = DATA_DIR / 'sync_history.json'


def _load_sync_history() -> List[Dict[str, Any]]:
    """Load sync history from file."""
    try:
        if SYNC_HISTORY_FILE.exists():
            with open(SYNC_HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        logger.warning(f"Failed to load sync history from file: {e}")
    return []


def _save_sync_history(record: Dict[str, Any]) -> None:
    """Persist sync record to history list in Redis cache or file fallback."""
    # Try Redis first
    if is_redis_available():
        try:
            history = cache.get(CACHE_KEYS['sync_history'], [])
            if not isinstance(history, list):
                history = []
            history.insert(0, record)
            # Keep last 100 sync records
            if len(history) > 100:
                history = history[:100]
            cache.set(CACHE_KEYS['sync_history'], history)
            return
        except Exception as e:
            logger.warning(f"Redis sync history save failed, falling back to file: {e}")
    
    # Fallback to file
    try:
        history = _load_sync_history()
        history.insert(0, record)
        if len(history) > 100:
            history = history[:100]
        save_json_file(SYNC_HISTORY_FILE, history)
    except Exception as e:
        logger.error(f"Failed to save sync history to file: {e}")


def get_sync_history(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Get paginated sync history."""
    # Try Redis first
    if is_redis_available():
        try:
            history = cache.get(CACHE_KEYS['sync_history'], [])
            if not isinstance(history, list):
                history = []
            total = len(history)
            paginated = history[offset:offset + limit]
            return {
                'list': paginated,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        except Exception as e:
            logger.warning(f"Redis sync history get failed, falling back to file: {e}")
    
    # Fallback to file
    try:
        history = _load_sync_history()
        total = len(history)
        paginated = history[offset:offset + limit]
        return {
            'list': paginated,
            'total': total,
            'limit': limit,
            'offset': offset,
        }
    except Exception as e:
        logger.error(f"Failed to get sync history from file: {e}")
        return {'list': [], 'total': 0, 'limit': limit, 'offset': offset}


# ==================== Mock Data (DEBUG only) ====================

def _load_mock_data() -> Dict[str, Any]:
    """Load mock data from fixtures (only used when DEBUG=True)."""
    # Import from fixtures only in DEBUG mode
    import os
    if os.getenv('DEBUG', '').lower() not in ('1', 'true', 'yes'):
        return {}
    
    try:
        from tests.fixtures.mock_data import (
            MOCK_PRODUCTS,
            MOCK_ORDERS,
            MOCK_CREATORS,
            MOCK_VIDEOS,
            MOCK_ACCOUNTS,
            MOCK_COMPLIANCE,
            MOCK_MEDIA,
        )
        logger.info("DEBUG mode: Loading mock data from fixtures")
        return {
            'products': MOCK_PRODUCTS,
            'orders': MOCK_ORDERS,
            'creators': MOCK_CREATORS,
            'videos': MOCK_VIDEOS,
            'accounts': MOCK_ACCOUNTS,
            'compliance_rules': MOCK_COMPLIANCE,
            'media': MOCK_MEDIA,
        }
    except ImportError:
        logger.warning("Mock data fixtures not found")
        return {}


def get_mock_data(key: str) -> List[Dict[str, Any]]:
    """Get mock data for a specific key (only in DEBUG mode)."""
    import os
    if os.getenv('DEBUG', '').lower() not in ('1', 'true', 'yes'):
        return []
    
    mock_data = _load_mock_data()
    return mock_data.get(key, [])


# Provide mock data constants for backward compatibility (only in DEBUG)
import os
if os.getenv('DEBUG', '').lower() in ('1', 'true', 'yes'):
    try:
        from tests.fixtures.mock_data import (
            MOCK_PRODUCTS,
            MOCK_ORDERS,
            MOCK_CREATORS,
        )
    except ImportError:
        MOCK_PRODUCTS = []
        MOCK_ORDERS = []
        MOCK_CREATORS = []
else:
    MOCK_PRODUCTS = []
    MOCK_ORDERS = []
    MOCK_CREATORS = []


def get_data_with_fallback(cache_key: str, mock_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Get data from cache, fall back to mock data if cache is empty.
    Only returns mock data in DEBUG mode.
    
    Returns:
        tuple: (data_list, data_source) where data_source is 'real' or 'mock'
    """
    import os
    is_debug = os.getenv('DEBUG', '').lower() in ('1', 'true', 'yes')
    
    data = cache.get(CACHE_KEYS.get(cache_key, cache_key), [])
    if data and len(data) > 0:
        return data, 'real'
    
    # Only return mock data in DEBUG mode
    if is_debug and mock_data:
        return mock_data, 'mock'
    
    return [], 'empty'


# ==================== External Request Forwarder ====================

def _request(endpoint: str, params: dict = None, headers: dict = None, cookies: dict = None,
             method: str = 'GET', json: dict = None, data: str = None, data_headers: dict = None,
             skip_sign: bool = False) -> dict:
    """通用 HTTP 请求转发器，支持 GET/POST，带签名、重试和统一错误处理。
    
    用于将 Flask 蓝图中的请求转发到外部 API（fxg/creator 等）。
    失败时返回包含 'data' 空字典和 'error' 字段的响应，调用方可通过 result.get('data', {}) 安全降级。
    
    Args:
        skip_sign: 跳过签名注入，用于 searchlist 等不需要动态签名的端点
    """
    params = params or {}
    headers = headers or {}
    cookies = cookies or {}
    
    # 仅对 fxg.jinritemai.com 域名做签名（searchlist 等端点不需要签名，设置 skip_sign=True）
    if 'fxg.jinritemai.com' in endpoint and not skip_sign:
        try:
            from douyin_sign import sign_request
            existing_tokens = {
                '__token': _read_secret('token', '__TOKEN'),
                'msToken': _read_secret('ms_token', 'MS_TOKEN'),
                'verifyFp': _read_secret('verify_fp', 'verifyFp'),
                'fp': _read_secret('fp', 'fp'),
            }
            sign_params = sign_request(endpoint, params, existing_tokens, Config.USER_AGENT)
            params = {**params, **sign_params}
        except Exception as e:
            logger.warning(f"签名失败，继续无签名请求: {e}")
    
    try:
        method = (method or 'GET').upper()
        merged_headers = headers.copy()
        if data_headers:
            merged_headers.update(data_headers)
        if method == 'POST':
            # 优先用 json=，否则用 data=
            if json is not None:
                resp = requests.post(endpoint, params=params, json=json, headers=merged_headers, cookies=cookies, timeout=30)
            elif data is not None:
                resp = requests.post(endpoint, params=params, data=data, headers=merged_headers, cookies=cookies, timeout=30)
            else:
                resp = requests.post(endpoint, params=params, headers=merged_headers, cookies=cookies, timeout=30)
        else:
            resp = requests.get(endpoint, params=params, headers=merged_headers, cookies=cookies, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"_request 请求失败: {endpoint} - {e}")
        return {'data': {}, 'error': str(e)}
    except ValueError as e:
        logger.error(f"_request JSON 解析失败: {endpoint} - {e}")
        return {'data': {}, 'error': str(e)}


# ==================== Generic Config Access ====================

_CONFIG_DEFAULTS: Dict[str, Dict[str, Any]] = {
    'alert_config': DEFAULT_ALERT_CONFIG,
    'alert_douyin_config': DEFAULT_ALERT_DOUYIN_CONFIG,
    'alert_dian_config': DEFAULT_ALERT_DIAN_CONFIG,
    'auth_config': DEFAULT_AUTH_CONFIG,
}

_CONFIG_FILES: Dict[str, Path] = {
    'alert_config': ALERT_CONFIG_FILE,
    'alert_douyin_config': ALERT_DOUYIN_CONFIG_FILE,
    'alert_dian_config': ALERT_DIAN_CONFIG_FILE,
    'auth_config': AUTH_FILE,
}


def get_config(key: str) -> Dict[str, Any]:
    """从 Redis 缓存获取配置，缺失时返回对应的默认配置。"""
    value = cache.get(CACHE_KEYS.get(key, key))
    if value is None:
        return _CONFIG_DEFAULTS.get(key, {}).copy()
    return value


def set_config(key: str, value: Dict[str, Any]) -> None:
    """保存配置到 Redis 缓存，并持久化到对应的 JSON 文件。"""
    cache.set(CACHE_KEYS.get(key, key), value)
    file_path = _CONFIG_FILES.get(key)
    if file_path:
        save_json_file(file_path, value)


def get_mock_status() -> Dict[str, Any]:
    """获取各数据源的状态（real/mock/empty）以及 DEBUG 模式开关。"""
    import os
    is_debug = os.getenv('DEBUG', '').lower() in ('1', 'true', 'yes')
    
    sources = ['products', 'orders', 'creators', 'videos', 'accounts', 'creator_works']
    status: Dict[str, Any] = {}
    for key in sources:
        data = cache.get(CACHE_KEYS.get(key, key), [])
        if data and len(data) > 0:
            status[key] = 'real'
        elif is_debug:
            status[key] = 'mock'
        else:
            status[key] = 'empty'
    status['debug_mode'] = is_debug
    return status


def fetch_external_creator_income() -> Dict[str, Any]:
    """Fetch creator income summary from external Creator Platform API.
    
    调用创作者平台收入分类汇总 API：
    GET https://creator.douyin.com/aweme/v1/creator/income/category/summary/
    
    Returns earnings data categorized by business type (ecom_merchant, business_task, etc.).
    This is a system-level external API interface.
    
    Returns:
        Dict with status, income summary data, and error info if any.
    """
    import os
    import requests
    from datetime import datetime
    
    # 获取 Creator 平台 cookie（从环境变量读取）
    cookie_str = os.getenv('CREATOR_COOKIES', '')
    
    # 构建请求头
    headers = {
        'User-Agent': os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://creator.douyin.com/creator-micro/revenue/center?type=1',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': cookie_str,
    }
    
    # Target URL from the curl command
    url = 'https://creator.douyin.com/aweme/v1/creator/income/category/summary/'
    
    try:
        logger.info("Fetching creator income summary from external Creator Platform API...")
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        logger.info(f"Creator income summary API response status: {result.get('status_code')}")
        return result
        
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching creator income: {e}")
        return {
            'status_code': -1,
            'status_msg': 'Connection error - unable to reach Creator Platform',
            'data_update_status': 0,
            'day1_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'connection_error', 'history_total_income': 0, 'link_relative': 0},
            'day7_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'connection_error', 'history_total_income': 0, 'link_relative': 0},
            'day30_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'connection_error', 'history_total_income': 0, 'link_relative': 0},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
            'has_today_total_income': False,
            'today_total_income': 0,
            'total_balance': 0,
            'total_income_summary': {'category_list': [], 'history_total_income': 0, 'link_relative': 0, 'data_update_status': 0},
            'fail_reason': 'connection_error'
        }
        
    except requests.Timeout as e:
        logger.error(f"Timeout fetching creator income: {e}")
        return {
            'status_code': -2,
            'status_msg': 'Timeout - Creator Platform request timed out',
            'data_update_status': 0,
            'day1_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'timeout', 'history_total_income': 0, 'link_relative': 0},
            'day7_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'timeout', 'history_total_income': 0, 'link_relative': 0},
            'day30_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'timeout', 'history_total_income': 0, 'link_relative': 0},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
            'has_today_total_income': False,
            'today_total_income': 0,
            'total_balance': 0,
            'total_income_summary': {'category_list': [], 'history_total_income': 0, 'link_relative': 0, 'data_update_status': 0},
            'fail_reason': 'timeout'
        }
        
    except requests.RequestException as e:
        logger.error(f"Request error fetching creator income: {e}")
        return {
            'status_code': -3,
            'status_msg': f'Request failed: {str(e)}',
            'data_update_status': 0,
            'day1_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'request_error', 'history_total_income': 0, 'link_relative': 0},
            'day7_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'request_error', 'history_total_income': 0, 'link_relative': 0},
            'day30_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'request_error', 'history_total_income': 0, 'link_relative': 0},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
            'has_today_total_income': False,
            'today_total_income': 0,
            'total_balance': 0,
            'total_income_summary': {'category_list': [], 'history_total_income': 0, 'link_relative': 0, 'data_update_status': 0},
            'fail_reason': 'request_error'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error fetching creator income: {e}")
        return {
            'status_code': -99,
            'status_msg': f'Unexpected error: {str(e)}',
            'data_update_status': 0,
            'day1_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'unknown_error', 'history_total_income': 0, 'link_relative': 0},
            'day7_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'unknown_error', 'history_total_income': 0, 'link_relative': 0},
            'day30_income_summary': {'category_list': [], 'data_update_status': 0, 'fail_reason': 'unknown_error', 'history_total_income': 0, 'link_relative': 0},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
            'has_today_total_income': False,
            'today_total_income': 0,
            'total_balance': 0,
            'total_income_summary': {'category_list': [], 'history_total_income': 0, 'link_relative': 0, 'data_update_status': 0},
            'fail_reason': 'unknown_error'
        }


def fetch_external_creator_income_detail() -> Dict[str, Any]:
    """Fetch creator income detail/trend from external Creator Platform API.
    
    调用创作者平台收入明细/趋势 API：
    GET https://creator.douyin.com/aweme/v1/creator/income/category/detail/
    
    Returns detailed income data including:
    - chart_coordinate_list: 趋势图坐标点 [{x, y}]，用于绘制趋势图
    - income_item_list: 收入明细 [{amount, name, timestamp}]，每日收入记录
    - status_code: 接口状态码
    - status_msg: 状态消息
    
    This is a system-level external API interface.
    
    Returns:
        Dict with detailed income data and error info if any.
    """
    import os
    import requests
    from datetime import datetime
    
    # 获取 Creator 平台 cookie（从环境变量读取）
    cookie_str = os.getenv('CREATOR_COOKIES', '')
    
    # 构建请求头 - 基于 curl 命令的 headers
    headers = {
        'User-Agent': os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://creator.douyin.com/creator-micro/revenue/center?type=1',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': cookie_str,
    }
    
    # Target URL from the curl command
    url = 'https://creator.douyin.com/aweme/v1/creator/income/category/detail/'
    
    # Query parameters from the curl command
    # history_day_count=7 表示最近7天
    params = {
        'history_day_count': '7',
    }
    
    try:
        logger.info("Fetching creator income detail/trend from external Creator Platform API...")
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        logger.info(f"Creator income detail API response status: {result.get('status_code')}, items: {len(result.get('income_item_list', []))}")
        return result
        
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching creator income detail: {e}")
        return {
            'status_code': -1,
            'status_msg': 'Connection error - unable to reach Creator Platform',
            'chart_coordinate_list': [],
            'income_item_list': [],
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except requests.Timeout as e:
        logger.error(f"Timeout fetching creator income detail: {e}")
        return {
            'status_code': -2,
            'status_msg': 'Timeout - Creator Platform request timed out',
            'chart_coordinate_list': [],
            'income_item_list': [],
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except requests.RequestException as e:
        logger.error(f"Request error fetching creator income detail: {e}")
        return {
            'status_code': -3,
            'status_msg': f'Request failed: {str(e)}',
            'chart_coordinate_list': [],
            'income_item_list': [],
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except Exception as e:
        logger.error(f"Unexpected error fetching creator income detail: {e}")
        return {
            'status_code': -99,
            'status_msg': f'Unexpected error: {str(e)}',
            'chart_coordinate_list': [],
            'income_item_list': [],
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }


def fetch_compass_shop_core_index() -> Dict[str, Any]:
    """Fetch shop homepage core index data from Compass API.
    
    调用compass店铺首页核心指标 API：
    GET https://compass.jinritemai.com/compass_api/shop/common/homepage/core_index_v3
    
    Returns core business metrics including income, payment, refund, product display and click data.
    This is a system-level external API interface for compass platform.
    
    Returns:
        Dict with compass shop core index data and error info if any.
    """
    import os
    import requests
    from datetime import datetime, timedelta
    
    # 获取 Compass Cookie（从环境变量读取）
    cookie_str = os.getenv('COMPASS_COOKIES', '')
    
    # 动态计算日期（昨天）
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y/%m/%d') + '+00:00:00'
    
    # 构建请求头 - 参照创作者收益 API 完整浏览器指纹风格
    headers = {
        'User-Agent': os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://compass.jinritemai.com/shop',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': cookie_str,
    }
    
    # Target URL
    url = 'https://compass.jinritemai.com/compass_api/shop/common/homepage/core_index_v3'
    
    # Query parameters - 仅保留必要参数，签名参数从环境变量/Secret 读取
    params = {
        'begin_date': date_str,
        'end_date': date_str,
        'date_type': '1',
        'activity_id': '',
        'index_selected': 'income_amt,pay_amt,settlement_amt_pay_time,pay_cnt,product_show_ucnt,product_click_ucnt,per_usr_pay_amt,pay_ucnt,rfndsuc_amt,rfndsuc_amt_pay_time,refund_amt_rate,refund_amt,refund_order_cnt,refund_order_cnt_pay_time,product_show_click_ucnt_ratio,product_click_pay_ucnt_ratio',
        'operate_type': '0',
    }
    
    # 从环境变量读取签名参数（可选，若不配置则不传，由服务端根据 Cookie 校验）
    # _lid 对应 shop_id，可从 COMPASS_LUOPAN_DT 或 ecom_gray_shop_id 获取
    lid = os.getenv('COMPASS_LID', '') or os.getenv('FXG_SHOP_ID', '')
    if lid:
        params['_lid'] = str(lid)
    
    # 从 Cookie 中提取 COMPASS_LUOPAN_DT 作为备选 _lid
    if not lid and 'COMPASS_LUOPAN_DT' in cookie_str:
        import re
        match = re.search(r'COMPASS_LUOPAN_DT=([^;]+)', cookie_str)
        if match:
            params['_lid'] = match.group(1)
    
    try:
        # 详细请求日志用于调试
        logger.info(f"Compass API request (full headers): url={url}, params_keys={list(params.keys())}, headers_keys={list(headers.keys())}")
        logger.debug(f"Compass request headers: {headers}")
        logger.debug(f"Compass request params: {params}")
        
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Compass API response: status={resp.status_code}, content_length={len(resp.content)}")
        logger.debug(f"Compass response headers: {dict(resp.headers)}")
        logger.debug(f"Compass response body (first 500): {resp.text[:500]}")
        
        resp.raise_for_status()
        result = resp.json()
        
        data_obj = result.get('data') or {}
        logger.info(f"Compass shop core index API response status: {result.get('st')}, data modules: {list(data_obj.keys())}")
        return result
        
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching compass shop core index: {e}")
        return {
            'status': 'error',
            'error': 'Connection error - unable to reach Compass Platform',
            'data': {},
        }
        
    except requests.Timeout as e:
        logger.error(f"Timeout fetching compass shop core index: {e}")
        return {
            'status': 'error',
            'error': 'Timeout - Compass Platform request timed out',
            'data': {},
        }
        
    except requests.RequestException as e:
        logger.error(f"Request error fetching compass shop core index: {e}")
        return {
            'status': 'error',
            'error': f'Request failed: {str(e)}',
            'data': {},
        }
        
    except Exception as e:
        logger.error(f"Unexpected error fetching compass shop core index: {e}")
        return {
            'status': 'error',
            'error': f'Unexpected error: {str(e)}',
            'data': {},
        }


def fetch_haohuo_product_preview(promotion_id: str) -> Dict[str, Any]:
    """Fetch product online preview from Haohuo (好货) platform.
    
    调用好货平台商品在线预览 API：
    POST https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/
    
    Returns product preview data including:
    - detail_imgs: 详情图片列表 [url_list, width, height]
    - product_format: 商品规格信息
    - detail_config: 详情配置（价格说明、销量说明、协议等）
    - detail_imgs_new: 新格式详情图片（含 pic_type）
    - title_image: 标题图片
    - jump_url: 跳转链接（直播间/lynxview）
    - extra: 额外信息
    
    This is a system-level external API interface for haohuo platform.
    
    Args:
        promotion_id: 商品推广ID (product_id)
        
    Returns:
        Dict with product preview data and error info if any.
    """
    import os
    import requests
    from datetime import datetime
    
    # 获取 Haohuo 平台 cookie（从环境变量读取）
    cookie_str = os.getenv('HAOHUO_COOKIES', '')
    
    # 构建请求头 - 基于 curl 命令的 headers
    headers = {
        'User-Agent': os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://haohuo.jinritemai.com',
        'Referer': f'https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id={promotion_id}&origin_type=doudian_product_management',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': cookie_str,
    }
    
    # Target URL from the curl command
    url = 'https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/'
    
    # Query parameters from the curl command
    params = {
        'is_h5': '1',
        'origin_type': 'doudian_product_management',
        # msToken 和 a_bogus 是动态签名参数，通常需要从页面 JS 计算或从 Cookie 中提取
        # 这里先不传，服务端可能仅依靠 Cookie 校验
    }
    
    # Form data from the curl command
    data = {
        'promotion_id': promotion_id,
        'enter_from': '',
        'meta_param': '',
        'is_h5': '1',
    }
    
    try:
        logger.info(f"Fetching haohuo product preview for promotion_id={promotion_id}...")
        resp = requests.post(url, headers=headers, params=params, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        
        logger.info(f"Haohuo product preview API response status_code: {result.get('status_code')}, detail_imgs: {len(result.get('detail_info', {}).get('detail_imgs', []))}")
        return result
        
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching haohuo product preview: {e}")
        return {
            'status_code': -1,
            'status_msg': 'Connection error - unable to reach Haohuo Platform',
            'detail_info': {},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except requests.Timeout as e:
        logger.error(f"Timeout fetching haohuo product preview: {e}")
        return {
            'status_code': -2,
            'status_msg': 'Timeout - Haohuo Platform request timed out',
            'detail_info': {},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except requests.RequestException as e:
        logger.error(f"Request error fetching haohuo product preview: {e}")
        return {
            'status_code': -3,
            'status_msg': f'Request failed: {str(e)}',
            'detail_info': {},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }
        
    except Exception as e:
        logger.error(f"Unexpected error fetching haohuo product preview: {e}")
        return {
            'status_code': -99,
            'status_msg': f'Unexpected error: {str(e)}',
            'detail_info': {},
            'extra': {'now': int(datetime.now().timestamp() * 1000)},
        }