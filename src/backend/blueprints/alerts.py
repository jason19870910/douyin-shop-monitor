"""Alerts blueprint."""
import math
from flask import Blueprint, request
from services.fetcher import (
    cache, CACHE_KEYS, get_config, set_config,
    get_alert_history, clear_alert_history,
)
from config import Config
from utils.responses import success_response, bad_request_response

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/v1')


def _parse_int_param(value, default, minimum=0, maximum=None):
    """Safely parse integer query params while enforcing sane bounds."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    if maximum is not None and parsed > maximum:
        return maximum
    return parsed


def _sanitize_alert_config(payload: dict, allowed_fields: list[str], *, allow_string_thresholds: bool = False):
    """Validate alert config updates and reject unknown keys or malformed values."""
    if not isinstance(payload, dict):
        raise ValueError('Request body must be a JSON object')

    unknown_keys = set(payload.keys()) - set(allowed_fields)
    if unknown_keys:
        raise ValueError(f'Unsupported alert fields: {sorted(unknown_keys)}')

    cleaned = {}
    for key in allowed_fields:
        if key not in payload:
            continue

        value = payload[key]

        if key == 'enabled':
            if not isinstance(value, bool):
                raise ValueError('enabled must be a boolean')
            cleaned[key] = value
            continue

        if key == 'notification_email':
            if not isinstance(value, str):
                raise ValueError('notification_email must be a string')
            email = value.strip()
            if email and '@' not in email:
                raise ValueError('notification_email must be a valid email address or empty')
            cleaned[key] = email
            continue

        if allow_string_thresholds and key == 'compliance_risk_threshold':
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {'low', 'medium', 'high'}:
                    cleaned[key] = normalized
                    continue
            if isinstance(value, bool):
                raise ValueError('compliance_risk_threshold must be a numeric value or low/medium/high')

        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError(f'{key} must be numeric or string')

        if isinstance(value, str):
            if not value.strip():
                raise ValueError(f'{key} cannot be empty')
            try:
                numeric_value = float(value)
            except ValueError as exc:
                raise ValueError(f'{key} must be numeric') from exc
        else:
            numeric_value = float(value)

        if not math.isfinite(numeric_value):
            raise ValueError(f'{key} must be finite')
        if numeric_value < 0 or numeric_value > 1000000:
            raise ValueError(f'{key} must be between 0 and 1000000')
        cleaned[key] = numeric_value

    return cleaned


@alerts_bp.route('/alerts/config', methods=['GET'])
def get_alert_config():
    """Get alert configuration."""
    return success_response(get_config('alert_config'))


@alerts_bp.route('/alerts/config', methods=['POST'])
def update_alert_config():
    """Update alert configuration."""
    payload = request.get_json(silent=True)
    if payload is None:
        return bad_request_response('Invalid config')

    try:
        sanitized = _sanitize_alert_config(
            payload,
            ['sales_drop_threshold', 'conversion_drop_threshold', 'inventory_low_threshold', 'notification_email', 'enabled'],
        )
    except ValueError as exc:
        return bad_request_response(str(exc))

    current_config = get_config('alert_config')
    current_config.update(sanitized)
    set_config('alert_config', current_config)
    return success_response(current_config, 'Alert config updated')


@alerts_bp.route('/alerts/douyin/config', methods=['GET'])
def get_alert_douyin_config():
    """Get Douyin-specific alert configuration."""
    return success_response(get_config('alert_douyin_config'))


@alerts_bp.route('/alerts/douyin/config', methods=['POST'])
def update_alert_douyin_config():
    """Update Douyin-specific alert configuration."""
    payload = request.get_json(silent=True)
    if payload is None:
        return bad_request_response('Invalid config')

    try:
        sanitized = _sanitize_alert_config(
            payload,
            ['video_view_drop_threshold', 'video_like_drop_threshold', 'creator_follower_drop_threshold', 'notification_email', 'enabled'],
        )
    except ValueError as exc:
        return bad_request_response(str(exc))

    current_config = get_config('alert_douyin_config')
    current_config.update(sanitized)
    set_config('alert_douyin_config', current_config)
    return success_response(current_config, 'Douyin alert config updated')


@alerts_bp.route('/alerts/dian/config', methods=['GET'])
def get_alert_dian_config():
    """Get Dian-specific alert configuration."""
    return success_response(get_config('alert_dian_config'))


@alerts_bp.route('/alerts/dian/config', methods=['POST'])
def update_alert_dian_config():
    """Update Dian-specific alert configuration."""
    payload = request.get_json(silent=True)
    if payload is None:
        return bad_request_response('Invalid config')

    try:
        sanitized = _sanitize_alert_config(
            payload,
            ['product_sales_drop_threshold', 'order_refund_rate_threshold', 'compliance_risk_threshold', 'notification_email', 'enabled'],
            allow_string_thresholds=True,
        )
    except ValueError as exc:
        return bad_request_response(str(exc))

    current_config = get_config('alert_dian_config')
    current_config.update(sanitized)
    set_config('alert_dian_config', current_config)
    return success_response(current_config, 'Dian alert config updated')


# ==================== Alert History ====================

@alerts_bp.route('/alerts/history', methods=['GET'])
def get_alerts_history():
    """Get paginated alert history with optional type filter.

    Query params:
        limit: Number of items per page (default 50, max 200)
        offset: Offset for pagination (default 0)
        type: Filter by alert type (sales_drop, low_inventory, conversion_drop)
    """
    limit = _parse_int_param(request.args.get('limit', 50), 50, minimum=1, maximum=200)
    offset = _parse_int_param(request.args.get('offset', 0), 0, minimum=0)
    alert_type = request.args.get('type', '').strip() or None

    result = get_alert_history(limit=limit, offset=offset, alert_type=alert_type)
    return success_response(result, 'Alert history retrieved')


@alerts_bp.route('/alerts/history', methods=['DELETE'])
def delete_alerts_history():
    """Clear all alert history."""
    count = clear_alert_history()
    return success_response({'cleared': count}, f'Cleared {count} alert records')


@alerts_bp.route('/alerts/clear-history', methods=['POST'])
def clear_alerts_history():
    """Clear all alert history (POST alias for frontend compatibility)."""
    count = clear_alert_history()
    return success_response({'cleared': count}, f'Cleared {count} alert records')


@alerts_bp.route('/alerts/history/stats', methods=['GET'])
def get_alerts_stats():
    """Get alert statistics summary."""
    history = cache.get(CACHE_KEYS['alert_history'], [])
    if not isinstance(history, list):
        history = []

    # Count by type
    type_counts = {}
    for alert in history:
        t = alert.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1

    return success_response({
        'total': len(history),
        'by_type': type_counts,
    }, 'Alert stats retrieved')