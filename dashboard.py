"""Dashboard blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_PRODUCTS, MOCK_ORDERS, MOCK_CREATORS, get_mock_status
from datetime import datetime
from utils.responses import success_response

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1')


@dashboard_bp.route('/mock/status', methods=['GET'])
def get_mock_status_endpoint():
    """Get mock data status for all data sources."""
    return success_response(get_mock_status())


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    products = cache.get(CACHE_KEYS['products'], [])
    orders = cache.get(CACHE_KEYS['orders'], [])
    creators = cache.get(CACHE_KEYS['creators'], [])
    videos = cache.get(CACHE_KEYS['videos'], [])
    
    # 计算商品统计
    total_products = len(products)
    on_sale_products = len([p for p in products if p.get('status') == 'on_sale'])
    total_sales_today = sum(p.get('sales_today', 0) for p in products)
    total_sales_yesterday = sum(p.get('sales_yesterday', 0) for p in products)
    avg_conversion_today = sum(p.get('conversion_rate_today', 0) for p in products) / total_products if total_products > 0 else 0
    avg_conversion_yesterday = sum(p.get('conversion_rate_yesterday', 0) for p in products) / total_products if total_products > 0 else 0
    
    # 销售趋势
    sales_trend = 'up' if total_sales_today > total_sales_yesterday else 'down' if total_sales_today < total_sales_yesterday else 'flat'
    
    # Top 5 商品
    top_products = sorted(products, key=lambda x: x.get('sales_today', 0), reverse=True)[:5]
    
    return success_response({
        'products': {
            'total': total_products,
            'on_sale': on_sale_products,
            'total_sales_today': total_sales_today,
            'total_sales_yesterday': total_sales_yesterday,
            'avg_conversion_rate': round(avg_conversion_today, 4),
            'avg_conversion_rate_yesterday': round(avg_conversion_yesterday, 4),
        },
        'orders': {
            'total': len(orders),
            'total_amount': sum(o.get('amount', 0) for o in orders),
        },
        'creators': {
            'total': len(creators),
            'total_followers': sum(c.get('follower_count', 0) for c in creators),
        },
        'videos': {
            'total': len(videos),
            'total_views': sum(v.get('view_count', 0) for v in videos),
        },
        'sales_trend': sales_trend,
        'top_products': top_products
    }, data_source='cache')


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计数据（兼容旧接口）。"""
    products, _ = get_data_with_fallback('products', MOCK_PRODUCTS)
    orders, _ = get_data_with_fallback('orders', MOCK_ORDERS)
    creators, _ = get_data_with_fallback('creators', MOCK_CREATORS)
    
    return success_response({
        'products': {
            'total': len(products),
            'on_sale': len([p for p in products if p.get('status') == 'on_sale']),
            'total_sales_today': sum(p.get('sales_today', 0) for p in products),
            'total_sales_yesterday': sum(p.get('sales_yesterday', 0) for p in products),
        },
        'orders': {
            'total': len(orders),
            'total_amount': sum(o.get('amount', 0) for o in orders),
        },
        'creators': {
            'total': len(creators),
            'total_followers': sum(c.get('follower_count', 0) for c in creators),
        }
    })


@dashboard_bp.route('/sync', methods=['POST'])
def manual_sync():
    """Manually trigger data synchronization."""
    from services.fetcher import scheduled_job
    result = scheduled_job()
    return success_response(result, 'Sync completed', data_source=cache.get('last_update'))