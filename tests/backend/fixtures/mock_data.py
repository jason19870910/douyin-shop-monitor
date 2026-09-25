"""Mock data fixtures for testing and development only.
Only imported when DEBUG=True to avoid polluting production logic.
"""
from datetime import datetime, timedelta


MOCK_PRODUCTS = [
    {
        'product_id': 'mock_p_001',
        'product_name': '模拟商品-爆款T恤',
        'category': '服饰',
        'price': 99.9,
        'sales_today': 156,
        'sales_yesterday': 134,
        'inventory': 234,
        'conversion_rate': 0.032,
        'conversion_rate_today': 0.035,
        'conversion_rate_yesterday': 0.028,
        'status': 'on_sale',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'product_id': 'mock_p_002',
        'product_name': '模拟商品-无线耳机',
        'category': '电子',
        'price': 299.0,
        'sales_today': 89,
        'sales_yesterday': 95,
        'inventory': 67,
        'conversion_rate': 0.045,
        'conversion_rate_today': 0.042,
        'conversion_rate_yesterday': 0.048,
        'status': 'on_sale',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'product_id': 'mock_p_003',
        'product_name': '模拟商品-智能水杯',
        'category': '家居',
        'price': 159.0,
        'sales_today': 203,
        'sales_yesterday': 187,
        'inventory': 12,
        'conversion_rate': 0.028,
        'conversion_rate_today': 0.031,
        'conversion_rate_yesterday': 0.025,
        'status': 'on_sale',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'product_id': 'mock_p_004',
        'product_name': '模拟商品-便携风扇',
        'category': '家电',
        'price': 79.9,
        'sales_today': 312,
        'sales_yesterday': 298,
        'inventory': 456,
        'conversion_rate': 0.051,
        'conversion_rate_today': 0.055,
        'conversion_rate_yesterday': 0.048,
        'status': 'on_sale',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'product_id': 'mock_p_005',
        'product_name': '模拟商品-防晒喷雾',
        'category': '美妆',
        'price': 59.9,
        'sales_today': 178,
        'sales_yesterday': 165,
        'inventory': 89,
        'conversion_rate': 0.038,
        'conversion_rate_today': 0.041,
        'conversion_rate_yesterday': 0.035,
        'status': 'on_sale',
        'fetched_at': datetime.now().isoformat(),
    },
]


MOCK_ORDERS = [
    {
        'order_id': 'mock_o_001',
        'product_name': '模拟商品-爆款T恤',
        'product_id': 'mock_p_001',
        'amount': 99.9,
        'status': 'completed',
        'create_time': (datetime.now() - timedelta(hours=2)).isoformat(),
        'buyer_id': 'buyer_001',
        'buyer_name': '用户001',
        'quantity': 1,
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'order_id': 'mock_o_002',
        'product_name': '模拟商品-无线耳机',
        'product_id': 'mock_p_002',
        'amount': 299.0,
        'status': 'completed',
        'create_time': (datetime.now() - timedelta(hours=5)).isoformat(),
        'buyer_id': 'buyer_002',
        'buyer_name': '用户002',
        'quantity': 1,
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'order_id': 'mock_o_003',
        'product_name': '模拟商品-智能水杯',
        'product_id': 'mock_p_003',
        'amount': 159.0,
        'status': 'shipped',
        'create_time': (datetime.now() - timedelta(hours=8)).isoformat(),
        'buyer_id': 'buyer_003',
        'buyer_name': '用户003',
        'quantity': 2,
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'order_id': 'mock_o_004',
        'product_name': '模拟商品-便携风扇',
        'product_id': 'mock_p_004',
        'amount': 79.9,
        'status': 'pending',
        'create_time': (datetime.now() - timedelta(hours=12)).isoformat(),
        'buyer_id': 'buyer_004',
        'buyer_name': '用户004',
        'quantity': 3,
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'order_id': 'mock_o_005',
        'product_name': '模拟商品-防晒喷雾',
        'product_id': 'mock_p_005',
        'amount': 59.9,
        'status': 'completed',
        'create_time': (datetime.now() - timedelta(hours=24)).isoformat(),
        'buyer_id': 'buyer_005',
        'buyer_name': '用户005',
        'quantity': 1,
        'fetched_at': datetime.now().isoformat(),
    },
]


MOCK_CREATORS = [
    {
        'creator_id': 'mock_c_001',
        'creator_name': '模拟达人-美妆博主',
        'follower_count': 125000,
        'following_count': 500,
        'video_count': 234,
        'total_likes': 1200000,
        'category': '美妆',
        'level': 'L4',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'creator_id': 'mock_c_002',
        'creator_name': '模拟达人-数码评测',
        'follower_count': 89000,
        'following_count': 300,
        'video_count': 156,
        'total_likes': 890000,
        'category': '数码',
        'level': 'L3',
        'fetched_at': datetime.now().isoformat(),
    },
    {
        'creator_id': 'mock_c_003',
        'creator_name': '模拟达人-家居好物',
        'follower_count': 56000,
        'following_count': 200,
        'video_count': 89,
        'total_likes': 450000,
        'category': '家居',
        'level': 'L2',
        'fetched_at': datetime.now().isoformat(),
    },
]


MOCK_VIDEOS = []

MOCK_ACCOUNTS = []

MOCK_COMPLIANCE = []

MOCK_MEDIA = []