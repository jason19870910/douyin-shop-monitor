"""Celery tasks using shared services layer."""
import logging
from datetime import timedelta
from celery_config import celery_app
from services.fetcher import (
    fetch_and_store_products,
    fetch_and_store_orders,
    fetch_and_store_creators,
    fetch_and_store_creator_works,
    fetch_and_check_compliance,
    check_alerts,
    scheduled_job,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_products_task(self):
    """Celery task to fetch products from external FXG API."""
    logger.info("Running fetch_products_task via shared service...")
    try:
        result = fetch_and_store_products()
        if result.get('status') == 'error':
            raise Exception(result.get('message', 'Unknown error'))
        return result
    except Exception as e:
        logger.error(f"Failed to fetch products: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_orders_task(self):
    """Celery task to fetch orders from external FXG API."""
    logger.info("Running fetch_orders_task via shared service...")
    try:
        result = fetch_and_store_orders()
        if result.get('status') == 'error':
            raise Exception(result.get('message', 'Unknown error'))
        return result
    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_creators_task(self):
    """Celery task to fetch creator data from external Creator API."""
    logger.info("Running fetch_creators_task via shared service...")
    try:
        result = fetch_and_store_creators()
        if result.get('status') == 'error':
            raise Exception(result.get('message', 'Unknown error'))
        return result
    except Exception as e:
        logger.error(f"Failed to fetch creators: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_creator_works_task(self):
    """Celery task to fetch creator works from external Creator API."""
    logger.info("Running fetch_creator_works_task via shared service...")
    try:
        result = fetch_and_store_creator_works()
        if result.get('status') == 'error':
            raise Exception(result.get('message', 'Unknown error'))
        return result
    except Exception as e:
        logger.error(f"Failed to fetch creator works: {e}")
        raise self.retry(exc=e)


@celery_app.task
def check_alerts_task():
    """Celery task to check alert conditions."""
    logger.info("Running check_alerts_task via shared service...")
    return check_alerts()


@celery_app.task
def full_sync_task():
    """Celery task to run full data synchronization."""
    logger.info("Running full_sync_task via shared service...")

    # Chain tasks
    fetch_products_task.delay()
    fetch_orders_task.delay()
    fetch_creators_task.delay()
    fetch_creator_works_task.delay()

    # Check alerts after a short delay
    check_alerts_task.apply_async(countdown=10)

    return {'status': 'started', 'message': 'Full sync initiated'}


@celery_app.task
def scheduled_job_task():
    """Celery task to run the complete scheduled job."""
    logger.info("Running scheduled_job_task via shared service...")
    return scheduled_job()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def refresh_oauth_token_task(self):
    """Celery task to refresh OAuth access token if needed."""
    logger.info("Checking OAuth token refresh...")

    try:
        from services.fetcher import get_config, cache, CACHE_KEYS
        from datetime import datetime

        auth_config = get_config('auth_config')

        if not auth_config.get('authorized'):
            logger.info("Not authorized, skipping token refresh")
            return {'status': 'skipped', 'reason': 'not authorized'}

        expires_at = auth_config.get('expires_at', 0)
        refresh_expires_at = auth_config.get('refresh_expires_at', 0)
        now = datetime.now().timestamp()

        # Refresh if access token expires within 1 hour
        if expires_at > 0 and (expires_at - now) < 3600:
            logger.info("Access token expiring soon, refreshing...")

            if refresh_expires_at > 0 and now >= refresh_expires_at:
                logger.warning("Refresh token also expired, cannot auto-refresh")
                return {'status': 'failed', 'reason': 'refresh_token_expired'}

            # Call the refresh endpoint logic
            from blueprints.auth import _refresh_access_token

            refresh_token = auth_config.get('refresh_token')
            if not refresh_token:
                logger.error("No refresh token available")
                return {'status': 'failed', 'reason': 'no_refresh_token'}

            token_result = _refresh_access_token(refresh_token, auth_config)

            if not token_result['success']:
                logger.error(f"Token refresh failed: {token_result['error']}")
                return {'status': 'failed', 'reason': token_result['error']}

            token_data = token_result['data']
            expires_in = token_data.get('expires_in', 86400)
            refresh_expires_in = token_data.get('refresh_expires_in', 2592000)

            auth_config.update({
                'access_token': token_data.get('access_token', ''),
                'refresh_token': token_data.get('refresh_token', ''),
                'expires_at': int((datetime.now() + timedelta(seconds=expires_in)).timestamp()),
                'refresh_expires_at': int((datetime.now() + timedelta(seconds=refresh_expires_in)).timestamp()),
                'scope': token_data.get('scope', 'user_info').split(','),
                'last_updated': datetime.now().isoformat()
            })

            from services.fetcher import set_config
            set_config('auth_config', auth_config)
            cache.set(CACHE_KEYS['auth'], auth_config)

            logger.info("OAuth token refreshed successfully via scheduled task")
            return {'status': 'success', 'message': 'Token refreshed'}

        return {'status': 'skipped', 'reason': 'token still valid'}

    except Exception as e:
        logger.error(f"Token refresh task failed: {e}")
        raise self.retry(exc=e)