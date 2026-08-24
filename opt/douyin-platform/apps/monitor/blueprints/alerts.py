"""Alerts blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, get_config, set_config
from config import Config
from utils.responses import success_response, bad_request_response

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/v1')


@alerts_bp.route('/alerts/config', methods=['GET'])
def get_alert_config():
    """Get alert configuration."""
    return success_response(get_config('alert_config'))


@alerts_bp.route('/alerts/config', methods=['POST'])
def update_alert_config():
    """Update alert configuration."""
    new_config = request.get_json()
    
    if not new_config:
        return bad_request_response('Invalid config')
    
    # Validate required fields
    allowed_fields = [
        'sales_drop_threshold',
        'conversion_drop_threshold',
        'inventory_low_threshold',
        'notification_email',
        'enabled'
    ]
    
    current_config = get_config('alert_config')
    for key, value in new_config.items():
        if key in allowed_fields:
            current_config[key] = value
    
    set_config('alert_config', current_config)
    return success_response(current_config, 'Alert config updated')


@alerts_bp.route('/alerts/douyin/config', methods=['GET'])
def get_alert_douyin_config():
    """Get Douyin-specific alert configuration."""
    return success_response(get_config('alert_douyin_config'))


@alerts_bp.route('/alerts/douyin/config', methods=['POST'])
def update_alert_douyin_config():
    """Update Douyin-specific alert configuration."""
    new_config = request.get_json()
    
    if not new_config:
        return bad_request_response('Invalid config')
    
    allowed_fields = [
        'video_view_drop_threshold',
        'video_like_drop_threshold',
        'creator_follower_drop_threshold',
        'notification_email',
        'enabled'
    ]
    
    current_config = get_config('alert_douyin_config')
    for key, value in new_config.items():
        if key in allowed_fields:
            current_config[key] = value
    
    set_config('alert_douyin_config', current_config)
    return success_response(current_config, 'Douyin alert config updated')


@alerts_bp.route('/alerts/dian/config', methods=['GET'])
def get_alert_dian_config():
    """Get Dian-specific alert configuration."""
    return success_response(get_config('alert_dian_config'))


@alerts_bp.route('/alerts/dian/config', methods=['POST'])
def update_alert_dian_config():
    """Update Dian-specific alert configuration."""
    new_config = request.get_json()
    
    if not new_config:
        return bad_request_response('Invalid config')
    
    allowed_fields = [
        'product_sales_drop_threshold',
        'order_refund_rate_threshold',
        'compliance_risk_threshold',
        'notification_email',
        'enabled'
    ]
    
    current_config = get_config('alert_dian_config')
    for key, value in new_config.items():
        if key in allowed_fields:
            current_config[key] = value
    
    set_config('alert_dian_config', current_config)
    return success_response(current_config, 'Dian alert config updated')