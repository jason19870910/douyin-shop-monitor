"""Dashboard blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_PRODUCTS, MOCK_ORDERS, MOCK_CREATORS, get_mock_status
from datetime import datetime
from utils.responses import success_response
import requests
import os
from config import Config

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1')


@dashboard_bp.route('/mock/status', methods=['GET'])
def get_mock_status_endpoint():
    """Get mock data status for all data sources."""
    return success_response(get_mock_status())


def _check_external_api(name: str, url: str, method: str = 'GET', headers: dict = None, cookies: dict = None, timeout: int = 10) -> dict:
    """Check external API endpoint health."""
    try:
        response = requests.request(method, url, headers=headers, cookies=cookies, timeout=timeout)
        return {
            'name': name,
            'url': url,
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'status_code': response.status_code,
            'response_time_ms': int(response.elapsed.total_seconds() * 1000),
            'error': None if response.status_code == 200 else f'HTTP {response.status_code}'
        }
    except requests.exceptions.Timeout:
        return {
            'name': name,
            'url': url,
            'status': 'timeout',
            'status_code': None,
            'response_time_ms': timeout * 1000,
            'error': f'Timeout after {timeout}s'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'name': name,
            'url': url,
            'status': 'connection_error',
            'status_code': None,
            'response_time_ms': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'status': 'error',
            'status_code': None,
            'response_time_ms': None,
            'error': str(e)
        }


@dashboard_bp.route('/health/external', methods=['GET'])
def check_external_api_health():
    """Check external API dependencies health."""
    fxg_base = Config.FXG_BASE_URL
    creator_base = Config.CREATOR_BASE_URL
    
    # FXG (抖店) cookies
    fxg_cookies = {}
    if Config.FXG_COOKIES:
        for cookie in Config.FXG_COOKIES.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                k, v = cookie.split('=', 1)
                fxg_cookies[k.strip()] = v.strip()
    
    # Creator (抖音) cookies
    creator_cookies = {}
    if Config.CREATOR_COOKIES:
        for cookie in Config.CREATOR_COOKIES.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                k, v = cookie.split('=', 1)
                creator_cookies[k.strip()] = v.strip()
    
    # Compass (指南针) cookies
    compass_cookies = {}
    compass_cookies_str = os.getenv('COMPASS_COOKIES', '')
    if compass_cookies_str:
        for cookie in compass_cookies_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                k, v = cookie.split('=', 1)
                compass_cookies[k.strip()] = v.strip()
    
    # Common headers for FXG
    fxg_headers = {
        'User-Agent': Config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': fxg_base + '/',
    }
    
    # Creator headers for income endpoints (match fetcher.py)
    creator_income_headers = {
        'User-Agent': Config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
    }
    
    # Creator headers for overview/work_list (simpler)
    creator_headers = {
        'User-Agent': Config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': creator_base + '/',
    }
    
    # Check FXG (抖店) endpoints
    fxg_endpoints = [
        ('抖店-商品列表', f'{fxg_base}/product/tproduct/list', 'GET', fxg_headers, fxg_cookies),
        ('抖店-商品统计', f'{fxg_base}/product/tproduct/aggsProductCount', 'GET', fxg_headers, fxg_cookies),
        ('抖店-订单搜索', f'{fxg_base}/api/order/searchlist', 'POST', fxg_headers, fxg_cookies),
        ('抖店-订单统计', f'{fxg_base}/api/order/tabcnt', 'GET', fxg_headers, fxg_cookies),
    ]
    
    # Check Creator (抖音) endpoints
    creator_endpoints = [
        ('创作者中心-概览', f'{creator_base}/janus/douyin/creator/data/overview/dashboard', 'GET', creator_headers, creator_cookies),
        ('创作者中心-作品列表', f'{creator_base}/janus/douyin/creator/pc/work_list', 'GET', creator_headers, creator_cookies),
        ('创作者中心-收益汇总', f'{creator_base}/aweme/v1/creator/income/category/summary/', 'GET', creator_income_headers, creator_cookies),
        ('创作者中心-收益明细', f'{creator_base}/aweme/v1/creator/income/category/detail/', 'GET', creator_income_headers, creator_cookies),
    ]
    
    # Compass headers
    compass_headers = {
        'User-Agent': Config.USER_AGENT or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://compass.jinritemai.com/',
    }
    
    # Check Compass (指南针) endpoints
    compass_endpoints = [
        ('指南针-店铺核心指标', 'https://compass.jinritemai.com/compass_api/shop/common/homepage/core_index_v3', 'GET', compass_headers, compass_cookies),
    ]
    
    results = []
    for name, url, method, headers, cookies in fxg_endpoints + creator_endpoints + compass_endpoints:
        result = _check_external_api(name, url, method, headers, cookies)
        results.append(result)
    
    # Summary
    healthy_count = sum(1 for r in results if r['status'] == 'healthy')
    total_count = len(results)
    
    return success_response({
        'overall_status': 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy',
        'healthy_count': healthy_count,
        'total_count': total_count,
        'endpoints': results,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


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

    # 销售趋势 - 近 7 天（基于订单创建时间聚合，若无数据则回退模拟）
    from datetime import datetime, timedelta
    sales_trend = []
    revenue_trend = []
    order_trend = []
    
    # 尝试从订单数据聚合真实趋势
    if orders:
        daily_sales = {}
        daily_revenue = {}
        daily_orders = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%m-%d')
            daily_sales[date] = 0
            daily_revenue[date] = 0.0
            daily_orders[date] = 0
        
        for order in orders:
            create_time = order.get('create_time', '')
            if create_time:
                try:
                    order_date = datetime.fromisoformat(create_time.replace('Z', '+00:00')).strftime('%m-%d')
                    if order_date in daily_sales:
                        daily_sales[order_date] += order.get('quantity', 1)
                        daily_revenue[order_date] += order.get('amount', 0)
                        daily_orders[order_date] += 1
                except Exception:
                    pass
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%m-%d')
            sales_trend.append({'date': date, 'sales': daily_sales.get(date, 0)})
            revenue_trend.append({'date': date, 'sales': round(daily_revenue.get(date, 0), 2)})
            order_trend.append({'date': date, 'sales': daily_orders.get(date, 0)})
    else:
        # 回退：基于总销售额分布的模拟数据
        base_sales = total_sales_today / 7 if total_sales_today > 0 else 0
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%m-%d')
            daily_sales = round(base_sales * (0.8 + 0.4 * (i / 6)), 2)
            sales_trend.append({'date': date, 'sales': daily_sales})
            revenue_trend.append({'date': date, 'sales': round(daily_sales * 100, 2)})  # 假设平均客单价
            order_trend.append({'date': date, 'sales': round(base_sales / 100 * (0.8 + 0.4 * (i / 6)), 0)})

    # Top 10 商品
    top_products = sorted(products, key=lambda x: x.get('sales_today', 0), reverse=True)[:10]

    # 订单状态分布
    status_map = {}
    for order in orders:
        status = order.get('status', 'unknown')
        if status not in status_map:
            status_map[status] = {'count': 0, 'amount': 0}
        status_map[status]['count'] += 1
        status_map[status]['amount'] += order.get('amount', 0)

    # 最近 10 个订单
    recent_orders = sorted(orders, key=lambda x: x.get('create_time', ''), reverse=True)[:10]

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
        'revenue_trend': revenue_trend,
        'order_trend': order_trend,
        'top_products': top_products,
        'order_status_distribution': status_map,
        'recent_orders': recent_orders,
        'data_source': 'cache',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })