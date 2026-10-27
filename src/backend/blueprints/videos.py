"""Videos blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_VIDEOS, VIDEOS_FILE, save_json_file
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

videos_bp = Blueprint('videos', __name__, url_prefix='/api/v1')


def _persist_videos(videos: list) -> None:
    """双写视频数据：Redis 持久化（无 TTL）+ JSON 文件，避免缓存过期后丢失。"""
    cache.set(CACHE_KEYS['videos'], videos, ttl=None)
    save_json_file(VIDEOS_FILE, videos)


@videos_bp.route('/videos', methods=['GET'])
def get_videos():
    """Get video list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    status_filter = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    videos = cache.get(CACHE_KEYS['videos'], DEFAULT_VIDEOS)
    
    if keyword:
        videos = [v for v in videos if keyword in v.get('title', '').lower() or keyword in v.get('creator_name', '').lower()]
    if status_filter:
        videos = [v for v in videos if v.get('status') == status_filter]
    if start_date:
        videos = [v for v in videos if v.get('create_time', '') >= start_date]
    if end_date:
        videos = [v for v in videos if v.get('create_time', '') <= end_date]
    
    total = len(videos)
    start = (page - 1) * size
    end = start + size
    
    return success_response({
        'items': videos[start:end],
        'total': total,
        'page': page,
        'size': size
    })


@videos_bp.route('/videos/<video_id>', methods=['GET'])
def get_video(video_id: str):
    """Get single video details."""
    videos = cache.get(CACHE_KEYS['videos'], DEFAULT_VIDEOS)
    video = next((v for v in videos if v.get('video_id') == video_id), None)
    if not video:
        return not_found_response('Video')
    return success_response(video)


@videos_bp.route('/videos', methods=['POST'])
def create_video():
    """Create new video entry."""
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    video = {
        'video_id': f"video_{int(datetime.now().timestamp())}",
        'title': data.get('title', ''),
        'creator_id': data.get('creator_id', ''),
        'creator_name': data.get('creator_name', ''),
        'view_count': data.get('view_count', 0),
        'like_count': data.get('like_count', 0),
        'comment_count': data.get('comment_count', 0),
        'share_count': data.get('share_count', 0),
        'duration': data.get('duration', 0),
        'create_time': datetime.now().isoformat(),
        'status': data.get('status', 'draft'),
        'cover_url': data.get('cover_url', ''),
        'video_url': data.get('video_url', ''),
    }
    
    videos = cache.get(CACHE_KEYS['videos'], DEFAULT_VIDEOS)
    videos.insert(0, video)
    _persist_videos(videos)
    
    return success_response(video, 'Video created', 201)


@videos_bp.route('/videos/<video_id>', methods=['PUT'])
def update_video(video_id: str):
    """Update video entry."""
    videos = cache.get(CACHE_KEYS['videos'], DEFAULT_VIDEOS)
    video = next((v for v in videos if v.get('video_id') == video_id), None)
    if not video:
        return not_found_response('Video')
    
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    video.update({
        'title': data.get('title', video['title']),
        'status': data.get('status', video['status']),
        'source_url': data.get('source_url', video.get('source_url', '')),
        'output_url': data.get('output_url', video.get('output_url', '')),
        'update_time': datetime.now().isoformat()
    })
    
    _persist_videos(videos)
    return success_response(video, 'Video updated')


@videos_bp.route('/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id: str):
    """Delete video entry."""
    videos = cache.get(CACHE_KEYS['videos'], DEFAULT_VIDEOS)
    video = next((v for v in videos if v.get('video_id') == video_id), None)
    if not video:
        return not_found_response('Video')
    
    videos = [v for v in videos if v.get('video_id') != video_id]
    _persist_videos(videos)
    return success_response(None, 'Video deleted')