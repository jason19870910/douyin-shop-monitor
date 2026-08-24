"""Celery tasks using shared services layer."""
import logging
from celery import shared_task
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
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


@shared_task
def check_alerts_task():
    """Celery task to check alert conditions."""
    logger.info("Running check_alerts_task via shared service...")
    return check_alerts()


@shared_task
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


@shared_task
def scheduled_job_task():
    """Celery task to run the complete scheduled job."""
    logger.info("Running scheduled_job_task via shared service...")
    return scheduled_job()


# Register tasks with celery_app (import here to avoid circular import)
from celery_config import celery_app
celery_app.tasks.register(fetch_products_task)
celery_app.tasks.register(fetch_orders_task)
celery_app.tasks.register(fetch_creators_task)
celery_app.tasks.register(fetch_creator_works_task)
celery_app.tasks.register(check_alerts_task)
celery_app.tasks.register(full_sync_task)
celery_app.tasks.register(scheduled_job_task)