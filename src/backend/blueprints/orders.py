"""Orders blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_ORDERS
from config import Config
from services.fetcher import _request
from utils.order_normalizer import normalize_orders
from utils.responses import success_response

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1')


@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get order list with optional filtering and summary statistics."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status_filter = request.args.get('status')
    
    orders, data_source = get_data_with_fallback('orders', MOCK_ORDERS)

    # 抖店订单原始字段 → 平台标准字段（前端表格直接消费）
    orders = normalize_orders(orders)

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
    """Get order statistics from local cache (synced data).
    
    Returns standardized format matching frontend OrderStatsData:
    {
      "all": {"count": int, "amount": int},
      "pay": {"count": int, "amount": int},
      "cancel": {"count": int, "amount": int},
      "sub_tab_count_map": {...}
    }
    """
    try:
        # 从本地缓存获取已同步的订单数据
        cached = cache.get(CACHE_KEYS['orders'])
        if not cached:
            # 缓存为空，尝试从文件加载
            from services.fetcher import ORDERS_FILE
            import json
            if ORDERS_FILE.exists():
                with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
        
        if not cached:
            # 仍为空，返回零值
            return success_response({
                'all': {'count': 0, 'amount': 0},
                'pay': {'count': 0, 'amount': 0},
                'cancel': {'count': 0, 'amount': 0},
                'sub_tab_count_map': {}
            }, 'No order data available')
        
        # 处理缓存格式：可能是列表或包含 items 键的字典
        if isinstance(cached, dict):
            orders = cached.get('items', [])
        else:
            orders = cached
        
        if not isinstance(orders, list):
            orders = []
        
        # 统计各状态订单数量和金额
        all_count = len(orders)
        all_amount = 0
        pay_count = 0
        pay_amount = 0
        cancel_count = 0
        cancel_amount = 0
        sub_tab_count_map = {}
        
        for o in orders:
            # 累计总金额 (外部 API 返回分，需除以 100 转为元)
            try:
                amt_raw = float(o.get('amount', o.get('order_amount', o.get('pay_amount', 0))))
                all_amount += amt_raw / 100
            except (ValueError, TypeError):
                pass
            
            # 判断订单状态
            status = str(o.get('status', '')).lower()
            
            # 状态归一化映射
            if status in ('all', '全部', ''):
                # all 状态不单独计数，已包含在 all_count 中
                pass
            elif status in ('pay', 'paid', '支付', '已支付', '完成', 'done', 'finished'):
                pay_count += 1
                try:
                    pay_amount += float(o.get('amount', o.get('order_amount', o.get('pay_amount', 0)))) / 100
                except (ValueError, TypeError):
                    pass
            elif status in ('cancel', 'cancelled', '取消', '已取消', '退款', 'refund'):
                cancel_count += 1
                try:
                    cancel_amount += float(o.get('amount', o.get('order_amount', o.get('pay_amount', 0)))) / 100
                except (ValueError, TypeError):
                    pass
            else:
                # 其他状态归入 sub_tab_count_map
                tab_key = status or 'unknown'
                if tab_key not in sub_tab_count_map:
                    sub_tab_count_map[tab_key] = {'count': 0, 'amount': 0}
                sub_tab_count_map[tab_key]['count'] += 1
                try:
                    sub_tab_count_map[tab_key]['amount'] += float(o.get('amount', o.get('order_amount', o.get('pay_amount', 0)))) / 100
                except (ValueError, TypeError):
                    pass
        
        normalized = {
            'all': {'count': all_count, 'amount': all_amount},
            'pay': {'count': pay_count, 'amount': pay_amount},
            'cancel': {'count': cancel_count, 'amount': cancel_amount},
            'sub_tab_count_map': sub_tab_count_map
        }
        
        return success_response(normalized, 'Order stats fetched from local cache')
    except Exception as e:
        from flask import current_app
        current_app.logger.error("Failed to fetch order stats from cache: %s", e)
        return success_response({
            'all': {'count': 0, 'amount': 0},
            'pay': {'count': 0, 'amount': 0},
            'cancel': {'count': 0, 'amount': 0},
            'sub_tab_count_map': {}
        }, 'Failed to fetch order stats', 502)