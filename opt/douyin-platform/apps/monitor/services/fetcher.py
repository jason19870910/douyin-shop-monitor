"""Shared data fetching service layer for both Celery tasks and Flask app."""
import json
import logging
import os
import random
import requests
import time
from datetime import datetime, timedelta
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

def _get_cache():
    """Get cache instance with lazy initialization."""
    global _cache_instance
    if _cache_instance is None:
        from redis_cache import get_cache
        _cache_instance = get_cache()
    return _cache_instance

# For backwards compatibility - property-like access
class _CacheProxy:
    def __getattr__(self, name):
        return getattr(_get_cache(), name)

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
    'auth_config': 'auth_config',
}

# Data storage paths
DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))

PRODUCTS_FILE = DATA_DIR / 'products.json'
ORDERS_FILE = DATA_DIR / 'orders.json'
CREATORS_FILE = DATA_DIR / 'creators.json'
VIDEOS_FILE = DATA_DIR / 'videos.json'
ACCOUNTS_FILE = DATA_DIR / 'accounts.json'
COMPLIANCE_FILE = DATA_DIR / 'compliance.json'
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
        'page': 1,
        'pageSize': 100,
        'appid': 1,
        '_bid': 'ffa_product',
        'aid': Config.FXG_SHOP_ID,
        '_lid': Config.FXG_LOG_ID,
    }
    
    # Import sign_request from douyin_sign
    from douyin_sign import sign_request
    
    existing_tokens = {
        '__token': _read_secret('token', '__TOKEN'),
        'msToken': _read_secret('ms_token', 'MS_TOKEN'),
        'verifyFp': _read_secret('verify_fp', 'verifyFp'),
        'fp': _read_secret('fp', 'fp'),
    }
    
    sign_params = sign_request(endpoint, base_params, existing_tokens, Config.USER_AGENT)
    params = {**base_params, **sign_params}
    
    headers = Config.COMMON_HEADERS.copy()
    cookies = get_fxg_cookies()
    
    resp = requests.get(endpoint, params=params, headers=headers, cookies=cookies, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    # 兼容外部 API 返回 list 或 dict
    try:
        products = result.get('data', {}).get('products', [])
    except AttributeError:
        products = result if isinstance(result, list) else []
    
    return products


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
        logger.error(f"Failed to fetch products: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== Order Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_orders_from_api() -> List[Dict[str, Any]]:
    """Fetch orders from external FXG API."""
    logger.info("Fetching orders from external FXG API...")
    
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=1)).timestamp())
    
    url = f'{Config.FXG_BASE_URL}/api/order/searchlist'
    params = {
        'start_time': start_time,
        'end_time': end_time,
        'page': 1,
        'size': 100
    }
    cookies = get_fxg_cookies()
    
    response = requests.get(url, headers=Config.COMMON_HEADERS, params=params, cookies=cookies, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    orders = result.get('data', {}).get('orders', [])
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
        logger.error(f"Failed to fetch orders: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== Creator Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_creators_from_api() -> List[Dict[str, Any]]:
    """Fetch creators from external Creator API."""
    logger.info("Fetching creators from external Creator API...")
    
    url = f'{Config.CREATOR_BASE_URL}/janus/douyin/creator/data/overview/dashboard'
    payload = {"recent_days": 7}
    cookies = get_creator_cookies()
    
    response = requests.post(url, headers=Config.COMMON_HEADERS, json=payload, cookies=cookies, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    creators = result.get('data', {}).get('creators', [])
    return creators


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
        logger.error(f"Failed to fetch creators: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== Creator Works Fetching ====================

@_http_retry(max_retries=3, base_delay=1.0, max_delay=10.0)
def _fetch_creator_works_from_api() -> List[Dict[str, Any]]:
    """Fetch creator works from external Creator API."""
    logger.info("Fetching creator works from external Creator API...")
    
    endpoint = Config.CREATOR_WORK_LIST_URL
    params = {
        'status': '0',
        'count': '12',
        'max_cursor': '0',
        'scene': 'star_atlas',
        'device_platform': 'android',
        'aid': '1128',
    }
    headers = Config.COMMON_HEADERS.copy()
    headers.update({
        'Referer': 'https://creator.douyin.com/creator-micro/content/manage',
    })
    cookies = get_creator_cookies()
    
    resp = requests.get(endpoint, params=params, headers=headers, cookies=cookies, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    works = result.get('data', {}).get('works', [])
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
        logger.error(f"Failed to fetch creator works: {e}")
        return {'status': 'error', 'message': str(e)}


# ==================== Compliance Fetching ====================

def fetch_and_check_compliance() -> Dict[str, Any]:
    """Fetch compliance data and run checks."""
    logger.info("Running compliance checks...")
    
    # This is a placeholder - in production, fetch from actual compliance API
    # For now, we just return success
    logger.info("Compliance check completed")
    return {'status': 'success', 'message': 'Compliance check completed'}


# ==================== Alert Checking ====================

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
                send_alert_notification(alert)
    
    logger.info(f"Alert check completed. Triggered {len(alerts_triggered)} alerts")
    return {'status': 'success', 'alerts_triggered': len(alerts_triggered)}


def send_alert_notification(alert: Dict[str, Any]) -> None:
    """Send alert notification via email."""
    alert_config = get_alert_config()
    email = alert_config.get('notification_email')
    
    if email:
        try:
            # In production, use smtplib or email service
            logger.info(f"ALERT EMAIL to {email}: {alert['message']}")
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")


# ==================== Data Initialization ====================

def init_compliance_data() -> None:
    """Initialize compliance data (rules, logs, mock data)."""
    from models import validate_data
    
    # Initialize compliance rules if not exists
    existing_rules = cache.get(CACHE_KEYS['compliance_rules'])
    if not existing_rules:
        mock_rules = [
            {
                'id': 'rule_001',
                'rule_name': '广告法禁用词检测',
                'rule_type': 'KEYWORD',
                'rule_content': {'keywords': ['最', '第一', '顶级', '极佳', '绝对', '全网', '全国', '世界级', '顶尖', '巅峰', '史无前例', '永久', '根治', '彻底', '特效', '神效', '祖传', '秘方', '独家', '专利', '专利技术', '填补空白']},
                'severity': 'HIGH',
                'category': '广告法',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'rule_002',
                'rule_name': '价格承诺合规',
                'rule_type': 'PRICE',
                'rule_content': {'max_price_ratio': 1.5, 'min_price_ratio': 0.5},
                'severity': 'MEDIUM',
                'category': '价格监管',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 'rule_003',
                'rule_name': '资质证照有效性',
                'rule_type': 'LICENSE',
                'rule_content': {'required_licenses': ['营业执照', '食品经营许可证', '化妆品备案凭证']},
                'severity': 'HIGH',
                'category': '资质合规',
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        validated_rules = validate_data(mock_rules, 'compliance_rules')
        cache.set(CACHE_KEYS['compliance_rules'], validated_rules)
        save_json_file(COMPLIANCE_FILE, validated_rules)
        logger.info(f"Initialized {len(validated_rules)} compliance rules")
    
    # Initialize compliance logs if not exists
    existing_logs = cache.get(CACHE_KEYS['compliance_logs'])
    if not existing_logs:
        mock_logs = [
            {
                'id': 'log_001',
                'rule_id': 'rule_001',
                'target_type': 'product',
                'target_id': 'mock_p_001',
                'target_name': '模拟商品-爆款T恤',
                'status': 'pass',
                'details': {'matched_keywords': [], 'checked_fields': ['product_name', 'description']},
                'checked_at': (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                'id': 'log_002',
                'rule_id': 'rule_001',
                'target_type': 'product',
                'target_id': 'mock_p_002',
                'target_name': '模拟商品-无线耳机',
                'status': 'fail',
                'details': {'matched_keywords': ['最'], 'checked_fields': ['product_name', 'description']},
                'checked_at': (datetime.now() - timedelta(hours=5)).isoformat()
            }
        ]
        validated_logs = validate_data(mock_logs, 'compliance_logs')
        cache.set(CACHE_KEYS['compliance_logs'], validated_logs)
        logger.info(f"Initialized {len(validated_logs)} compliance logs")


def load_all_data() -> None:
    """Load all data files into Redis cache with Pydantic validation."""
    # Load data into Redis cache (list types with automatic validation)
    data_map = {
        'products': (PRODUCTS_FILE, []),
        'orders': (ORDERS_FILE, []),
        'creators': (CREATORS_FILE, []),
        'videos': (VIDEOS_FILE, DEFAULT_VIDEOS),
        'accounts': (ACCOUNTS_FILE, DEFAULT_ACCOUNTS),
        'compliance_rules': (COMPLIANCE_FILE, DEFAULT_COMPLIANCE),
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
    save_json_file(COMPLIANCE_FILE, cache.get(CACHE_KEYS['compliance_rules'], []))
    save_json_file(MEDIA_FILE, cache.get(CACHE_KEYS['media'], []))
    save_json_file(AUTH_FILE, cache.get(CACHE_KEYS['auth'], []))
    save_json_file(CREATOR_WORKS_FILE, cache.get(CACHE_KEYS['creator_works'], []))
    save_json_file(ALERT_CONFIG_FILE, cache.get(CACHE_KEYS['alert_config'], {}))
    save_json_file(ALERT_DOUYIN_CONFIG_FILE, cache.get(CACHE_KEYS['alert_douyin_config'], {}))
    save_json_file(ALERT_DIAN_CONFIG_FILE, cache.get(CACHE_KEYS['alert_dian_config'], {}))
    logger.info("All data saved successfully")


# ==================== Scheduled Job ====================

def scheduled_job() -> Dict[str, Any]:
    """Main scheduled job to fetch all data and check alerts.
    This function is called by Celery Beat tasks.
    """
    logger.info("Running scheduled job...")
    
    results = {}
    results['products'] = fetch_and_store_products()
    results['orders'] = fetch_and_store_orders()
    results['creators'] = fetch_and_store_creators()
    results['creator_works'] = fetch_and_store_creator_works()
    results['compliance'] = fetch_and_check_compliance()
    results['alerts'] = check_alerts()
    
    cache.set('last_update', datetime.now().isoformat())
    logger.info("Scheduled job completed")
    
    return results


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

def _request(endpoint: str, params: dict = None, headers: dict = None, cookies: dict = None) -> dict:
    """通用 HTTP GET 请求转发器，带签名、重试和统一错误处理。
    
    用于将 Flask 蓝图中的请求转发到外部 API（fxg/creator 等）。
    失败时返回包含 'data' 空字典和 'error' 字段的响应，调用方可通过 result.get('data', {}) 安全降级。
    """
    params = params or {}
    headers = headers or {}
    cookies = cookies or {}
    
    # 仅对 fxg.jinritemai.com 域名做签名
    if 'fxg.jinritemai.com' in endpoint:
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
        resp = requests.get(endpoint, params=params, headers=headers, cookies=cookies, timeout=30)
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