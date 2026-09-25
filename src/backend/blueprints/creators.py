"""Creators blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_CREATORS
from config import Config
from services.fetcher import _request
from utils.responses import success_response, not_found_response

creators_bp = Blueprint('creators', __name__, url_prefix='/api/v1')


@creators_bp.route('/creators', methods=['GET'])
def get_creators():
    """Get creator list."""
    creators, data_source = get_data_with_fallback('creators', MOCK_CREATORS)
    return success_response({
        'items': creators,
        'total': len(creators),
        'data_source': data_source
    })


@creators_bp.route('/creators/<creator_id>', methods=['GET'])
def get_creator(creator_id: str):
    """Get single creator details."""
    creators = cache.get(CACHE_KEYS['creators'], [])
    creator = next((c for c in creators if c.get('creator_id') == creator_id), None)
    if not creator:
        return not_found_response('Creator')
    return success_response(creator)


@creators_bp.route('/creators/works', methods=['GET'])
def get_creator_works():
    """Get creator work list (content management)."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    status_filter = request.args.get('status')
    
    works = cache.get(CACHE_KEYS['creator_works'], [])
    
    if keyword:
        works = [w for w in works if keyword in w.get('title', '').lower() or keyword in w.get('creator_name', '').lower()]
    if status_filter:
        works = [w for w in works if w.get('status') == status_filter]
    
    total = len(works)
    start = (page - 1) * size
    end = start + size
    
    return success_response({
        'items': works[start:end],
        'total': total,
        'page': page,
        'size': size
    })


@creators_bp.route('/creators/works/external', methods=['GET'])
def get_external_creator_works():
    """转发创作者作品列表请求到外部 API，使用 creator 基础 URL、统一 Header 与 Cookie。"""
    params = request.args.to_dict(flat=True)
    # 设置默认参数
    params.setdefault('status', '0')
    params.setdefault('count', '12')
    params.setdefault('max_cursor', '0')
    params.setdefault('scene', 'star_atlas')
    params.setdefault('device_platform', 'android')
    params.setdefault('aid', '1128')
    
    endpoint = Config.CREATOR_WORK_LIST_URL
    headers = Config.COMMON_HEADERS.copy()
    headers.update({
        'Referer': 'https://creator.douyin.com/creator-micro/content/manage',
    })
    cookies = {}
    if Config.CREATOR_COOKIES:
        for pair in Config.CREATOR_COOKIES.split(';'):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                cookies[k] = v
    result = _request(endpoint, params=params, headers=headers, cookies=cookies)
    return success_response(result.get('data', {}), 'Creator works fetched from external service')