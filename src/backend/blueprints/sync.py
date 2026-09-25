"""Sync blueprint - manual sync and sync history."""
from datetime import datetime
import logging

from flask import Blueprint, request

from services.fetcher import (
    scheduled_job,
    get_sync_history,
    cache,
)
from utils.responses import success_response, bad_request_response, internal_error_response

sync_bp = Blueprint('sync', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)


@sync_bp.route('/sync', methods=['POST'])
def manual_sync():
    """Trigger a full data synchronization job."""
    try:
        async_mode = request.args.get('async', 'false').lower() in ('1', 'true', 'yes')

        if async_mode:
            try:
                from tasks import full_sync_task
                task = full_sync_task.delay()
                return success_response({
                    'status': 'started',
                    'mode': 'async',
                    'task_id': task.id,
                    'message': 'Full sync task queued',
                }, code=202)
            except Exception as e:
                logger.warning("Celery unavailable, falling back to sync mode: %s", e)

        results = scheduled_job()
        last_update = cache.get('last_update') or datetime.now().isoformat()
        return success_response({
            'status': 'completed',
            'mode': 'sync',
            'last_update': last_update,
            'results': {
                k: (v.get('status') if isinstance(v, dict) else str(v))
                for k, v in (results or {}).items()
            },
        })
    except Exception as e:
        logger.exception("Manual sync failed")
        return internal_error_response(f'Sync failed: {e}')


@sync_bp.route('/sync/history', methods=['GET'])
def sync_history():
    """Return paginated sync history."""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
    except (TypeError, ValueError):
        return bad_request_response('limit and offset must be integers')

    data = get_sync_history(limit=limit, offset=offset)
    return success_response(data)
