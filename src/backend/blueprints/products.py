"""Products blueprint."""
from flask import Blueprint, request
from services.fetcher import _request, _fetch_products_from_api, cache, CACHE_KEYS
from config import Config
from utils.responses import success_response

products_bp = Blueprint('products', __name__, url_prefix='/api/v1')


@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get products list (from cache with external fallback).
    
    Query params:
        start_date: Filter products fetched on or after this date (YYYY-MM-DD)
        end_date: Filter products fetched on or before this date (YYYY-MM-DD)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Try cache first
        cached = cache.get(CACHE_KEYS['products'])
        if cached:
            # Handle both formats: dict with 'items' key, or direct list
            if isinstance(cached, dict):
                products = cached.get('items', [])
            else:
                products = cached  # Assume it's a list
            
            # Apply date filter if provided
            if start_date or end_date:
                products = _filter_products_by_date(products, start_date, end_date)
            
            return success_response({
                'items': products,
                'total': len(products),
                'data_source': 'cache'
            })
        
        # Fallback to external API
        products = _fetch_products_from_api()
        
        # Apply date filter if provided
        if start_date or end_date:
            products = _filter_products_by_date(products, start_date, end_date)
        
        return success_response({
            'items': products,
            'total': len(products),
            'data_source': 'external'
        })
    except Exception as e:
        from flask import current_app
        current_app.logger.error("Failed to fetch products: %s", e)
        return success_response({
            'items': [],
            'total': 0,
            'data_source': 'error'
        }, 'Failed to fetch products', 502)


def _filter_products_by_date(products: list, start_date: str = None, end_date: str = None) -> list:
    """Filter products by fetched_at date range."""
    if not start_date and not end_date:
        return products
    
    from datetime import datetime
    
    filtered = []
    for product in products:
        fetched_at = product.get('fetched_at')
        if not fetched_at:
            continue
        
        try:
            # Parse the fetched_at timestamp (ISO format)
            product_date = datetime.fromisoformat(fetched_at.replace('Z', '+00:00')).date()
            
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                if product_date < start:
                    continue
            
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                if product_date > end:
                    continue
            
            filtered.append(product)
        except (ValueError, TypeError):
            # Skip products with invalid date format
            continue
    
    return filtered


@products_bp.route('/products/<product_id>', methods=['GET'])
def get_product_detail(product_id):
    """Get single product detail."""
    try:
        # Try cache first
        cached = cache.get(CACHE_KEYS['products'])
        if cached:
            # Handle both formats: dict with 'items' key, or direct list
            if isinstance(cached, dict):
                products = cached.get('items', [])
            else:
                products = cached  # Assume it's a list
            product = next((p for p in products if str(p.get('product_id') or p.get('id')) == str(product_id)), None)
            if product:
                return success_response(product, 'Product found in cache')
        
        # Fallback to external API - fetch all and find the one
        products = _fetch_products_from_api()
        product = next((p for p in products if str(p.get('product_id') or p.get('id')) == str(product_id)), None)
        if product:
            return success_response(product, 'Product found from external API')
        
        return success_response(None, 'Product not found', 404)
    except Exception as e:
        from flask import current_app
        current_app.logger.error("Failed to fetch product detail: %s", e)
        return success_response(None, 'Failed to fetch product detail', 502)


@products_bp.route('/products/external', methods=['GET'])
def get_products_external():
    """Get products from external FXG API only (no fallback)."""
    try:
        products = _fetch_products_from_api()
        return success_response({
            'items': products,
            'total': len(products),
            'data_source': 'external'
        })
    except Exception as e:
        from flask import current_app
        current_app.logger.error("Failed to fetch products from external API: %s", e)
        return success_response({
            'items': [],
            'total': 0,
            'data_source': 'external_error'
        }, 'Failed to fetch from external API', 502)


@products_bp.route('/products/stats', methods=['GET'])
def product_stats():
    """Get product statistics from local cache (synced data).
    
    Returns standardized format:
    {
      "total": int,        # 总数
      "onsale": int,       # 在售数
      "stock": int,        # 库存预警数
      "violation": int     # 违规数
    }
    """
    try:
        # 从本地缓存获取已同步的商品数据
        cached = cache.get(CACHE_KEYS['products'])
        if not cached:
            # 缓存为空，尝试从文件加载
            from services.fetcher import PRODUCTS_FILE
            import json
            if PRODUCTS_FILE.exists():
                with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
        
        if not cached:
            # 仍为空，返回零值
            return success_response({
                'total': 0, 'onsale': 0, 'stock': 0, 'violation': 0
            }, 'No product data available')
        
        # 处理缓存格式：可能是列表或包含 items 键的字典
        if isinstance(cached, dict):
            products = cached.get('items', [])
        else:
            products = cached
        
        if not isinstance(products, list):
            products = []
        
        # 统计各状态商品数量
        total = len(products)
        onsale = 0
        stock = 0
        violation = 0
        
        for p in products:
            # 判断商品状态：status 字段可能值为 'onSale'/'在售', 'stock'/'库存', 'violation'/'违规'
            # 也可能通过 inventory (库存) 字段判断库存预警
            status = str(p.get('status', '')).lower()
            inventory = p.get('inventory', p.get('stock', 0))
            
            if 'sale' in status or status in ('onsale', '在售', '1'):
                onsale += 1
            elif 'stock' in status or status in ('库存', '2'):
                stock += 1
            elif 'violation' in status or '违规' in status or status in ('3',):
                violation += 1
            else:
                # 无明确状态时，按库存判断：库存为0或很低视为库存预警
                try:
                    inv = int(inventory)
                    if inv <= 0:
                        stock += 1
                    else:
                        onsale += 1
                except (ValueError, TypeError):
                    onsale += 1
        
        stats = {
            'total': total,
            'onsale': onsale,
            'stock': stock,
            'violation': violation
        }
        
        return success_response(stats, 'Product stats fetched from local cache')
    except Exception as e:
        from flask import current_app
        current_app.logger.error("Failed to fetch product stats from cache: %s", e)
        return success_response({
            'total': 0, 'onsale': 0, 'stock': 0, 'violation': 0
        }, 'Failed to fetch product stats', 502)