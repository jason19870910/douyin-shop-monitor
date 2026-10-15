"""Creators blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_data_with_fallback, MOCK_CREATORS, _fetch_creators_from_api, _fetch_creator_overview_from_api
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


@creators_bp.route('/creators/overview', methods=['GET'])
def get_creator_overview():
    """获取创作者中心概览数据（近 N 天） - 返回前端期望格式。"""
    recent_days = int(request.args.get('recent_days', 7))

    # 优先调用外部概览 API（实时数据，包含 total_followers, total_videos, recent_view, recent_like）
    try:
        overview_data = _fetch_creator_overview_from_api(recent_days)
        return success_response({
            'recent_days': recent_days,
            'total_followers': overview_data.get('total_followers', 0),
            'total_videos': overview_data.get('total_videos', 0),
            'recent_view': overview_data.get('recent_view', 0),
            'recent_like': overview_data.get('recent_like', 0),
            'data_source': 'external'
        })
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.error("Failed to fetch creator overview from external API: %s", e)

    # 回退：使用缓存计算（仅包含基础统计，不含 recent_view/recent_like）
    creators = cache.get(CACHE_KEYS['creators'], [])
    if creators:
        total_followers = sum(c.get('total_followers', c.get('follower_count', 0)) for c in creators)
        total_videos = sum(c.get('total_videos', c.get('video_count', 0)) for c in creators)

        return success_response({
            'recent_days': recent_days,
            'total_followers': total_followers,
            'total_videos': total_videos,
            'recent_view': 0,
            'recent_like': 0,
            'data_source': 'cache'
        })

    # 最后回退：返回空数据
    return success_response({
        'recent_days': recent_days,
        'total_followers': 0,
        'total_videos': 0,
        'recent_view': 0,
        'recent_like': 0,
        'data_source': 'empty'
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
    """Get creator works list."""
    recent_days = int(request.args.get('recent_days', 7))
    try:
        works = _fetch_creator_works_from_api(recent_days)
        return success_response({
            'recent_days': recent_days,
            'items': works,
            'total': len(works),
            'data_source': 'external'
        })
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.error("Failed to fetch creator works from external API: %s", e)
    # 回退缓存
    works = cache.get(CACHE_KEYS['creator_works'], [])
    return success_response({
        'recent_days': recent_days,
        'items': works,
        'total': len(works),
        'data_source': 'cache' if works else 'empty'
    })