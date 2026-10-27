"""Orders blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_ORDERS
from config import Config
from services.fetcher import _request
from utils.responses import success_response

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1')


@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get order list with optional filtering and summary statistics."""
    page = max(1, int(request.args.get('page', 1)))
    size = int(request.args.get('size', 20))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status_filter = request.args.get('status')

    orders, data_source = get_data_with_fallback('orders', MOCK_ORDERS)

    # 过滤时间范围
    if start_date:
        orders = [o for o in orders if o.get('create_time', '') >= start_date]
    if end_date:
        orders = [o for o in orders if o.get('create_time', '') <= end_date]

    # 过滤状态（保持向后兼容）
    if status_filter:
        orders = [o for o in orders if o.get('status') == status_filter]

    total = len(orders)
    start = (page - 1) * size
    end = start + size

    # 统计汇总（示例实现，仅返回 all，其他分类默认 0）
    summary = {
        'abnormal': {'amount': 0, 'count': 0},
        'after_sale': {'amount': 0, 'count': 0},
        'all': {'amount': sum(o.get('amount', 0) for o in orders), 'count': total},
        'closed': {'amount': 0, 'count': 0},
        'done': {'amount': 0, 'count': 0},
        'sent': {'amount': 0, 'count': 0},
        'timeout_send': {'amount': 0, 'count': 0},
        'urgent_send': {'amount': 0, 'count': 0},
        'wait_pay': {'amount': 0, 'count': 0},
        'wait_send': {'amount': 0, 'count': 0},
    }

    return success_response({
        'summary': summary,
        'items': orders[start:end],
        'total': total,
        'page': page,
        'size': size,
        'data_source': data_source
    })


@orders_bp.route('/orders/stats', methods=['GET'])
def get_external_order_stats():
    """转发订单统计请求到外部 API，使用 fxg 基础 URL、统一 Header 与 Cookie。"""
    params = request.args.to_dict(flat=True)
    endpoint = f"{Config.FXG_BASE_URL}/api/order/tabcnt"
    headers = Config.COMMON_HEADERS.copy()
    cookies = {}
    if Config.FXG_COOKIES:
        for pair in Config.FXG_COOKIES.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    result = _request(endpoint, params=params, headers=headers, cookies=cookies)
    return success_response(result.get('data', {}), 'Order stats fetched from external service')
