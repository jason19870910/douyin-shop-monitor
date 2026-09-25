"""Media blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_MEDIA
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

media_bp = Blueprint('media', __name__, url_prefix='/api/v1')


@media_bp.route('/media/video-edit', methods=['GET'])
def get_video_edit_media():
    """Get media list for video editing."""
    media_list = cache.get(CACHE_KEYS['media'], DEFAULT_MEDIA)
    videos = [m for m in media_list if m.get('type') == 'video']
    return success_response({'items': videos, 'total': len(videos)})


@media_bp.route('/media/image-edit', methods=['GET'])
def get_image_edit_media():
    """Get media list for image editing."""
    media_list = cache.get(CACHE_KEYS['media'], DEFAULT_MEDIA)
    images = [m for m in media_list if m.get('type') == 'image']
    return success_response({'items': images, 'total': len(images)})


@media_bp.route('/media', methods=['POST'])
def create_media():
    """Create new media entry."""
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    media = {
        'media_id': f"media_{int(datetime.now().timestamp())}",
        'title': data.get('title', ''),
        'type': data.get('type', 'video'),
        'url': data.get('url', ''),
        'status': data.get('status', 'active'),
        'size': data.get('size', 0),
        'mime_type': data.get('mime_type', ''),
        'created_at': datetime.now().isoformat()
    }
    
    media_list = cache.get(CACHE_KEYS['media'], DEFAULT_MEDIA)
    media_list.insert(0, media)
    cache.set(CACHE_KEYS['media'], media_list)
    
    return success_response(media, 'Media created', 201)


@media_bp.route('/media/<media_id>', methods=['PUT'])
def update_media(media_id: str):
    """Update media entry."""
    media_list = cache.get(CACHE_KEYS['media'], DEFAULT_MEDIA)
    media = next((m for m in media_list if m.get('media_id') == media_id), None)
    if not media:
        return not_found_response('Media')
    
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    media.update({
        'title': data.get('title', media['title']),
        'status': data.get('status', media['status']),
        'source_url': data.get('source_url', media.get('source_url', '')),
        'output_url': data.get('output_url', media.get('output_url', '')),
        'update_time': datetime.now().isoformat()
    })
    
    cache.set(CACHE_KEYS['media'], media_list)
    return success_response(media, 'Media updated')