"""Products blueprint."""
from datetime import datetime
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_PRODUCTS, MOCK_ORDERS, MOCK_CREATORS
from models import validate_data
from utils.responses import success_response, not_found_response

products_bp = Blueprint('products', __name__, url_prefix='/api/v1')


@products_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return success_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'last_update': cache.get('last_update')
    })


@products_bp.route('/products/stats', methods=['GET'])
def get_product_stats():
    """获取商品统计信息（调用外部 API）。"""
    from config import Config
    import requests
    
    endpoint = f"{Config.FXG_BASE_URL}/products/stats"
    params = {
        'tab': request.args.get('tab', 'onSale'),
        'appid': request.args.get('appid', '1')
    }
    headers = Config.COMMON_HEADERS.copy()
    cookies = {}
    fxg_cookies = Config.FXG_COOKIES if hasattr(Config, 'FXG_COOKIES') else ''
    if fxg_cookies:
        for pair in fxg_cookies.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    
    from services.fetcher import _request
    result = _request(endpoint, params=params, headers=headers, cookies=cookies)
    return success_response(result.get('data', {}), 'Product stats fetched from external service')


@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get product list from internal cache with optional filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    
    products, data_source = get_data_with_fallback('products', MOCK_PRODUCTS)
    
    if keyword:
        products = [p for p in products if keyword in p.get('product_name', '').lower()]
    
    total = len(products)
    start = (page - 1) * size
    end = start + size
    
    return success_response({
        'items': products[start:end],
        'total': total,
        'page': page,
        'size': size,
        'data_source': data_source
    })


@products_bp.route('/products/external', methods=['GET'])
def get_external_product_list():
    """转发商品列表请求到外部 API，使用 fxg 基础 URL、统一 Header 与 Cookie。"""
    from config import Config
    from services.fetcher import _request
    
    params = request.args.to_dict(flat=True)
    endpoint = f"{Config.FXG_BASE_URL}/product/tproduct/list"
    headers = Config.COMMON_HEADERS.copy()
    cookies = {}
    fxg_cookies = Config.FXG_COOKIES if hasattr(Config, 'FXG_COOKIES') else ''
    if fxg_cookies:
        for pair in fxg_cookies.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    result = _request(endpoint, params=params, headers=headers, cookies=cookies)
    return success_response(result.get('data', {}), 'Product list fetched from external service')


@products_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id: str):
    """Get single product details."""
    products = cache.get(CACHE_KEYS['products'], [])
    product = next((p for p in products if p.get('product_id') == product_id), None)
    if not product:
        return not_found_response('Product')
    return success_response(product)