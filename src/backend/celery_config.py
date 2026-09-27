import os
from celery import Celery
from celery.schedules import crontab

# Celery configuration
celery_app = Celery('douyin_monitor', include=['tasks'])

celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    beat_schedule={
        'fetch-products-every-15-minutes': {
            'task': 'tasks.fetch_products_task',
            'schedule': 900.0,  # 15 minutes
        },
        'fetch-orders-every-15-minutes': {
            'task': 'tasks.fetch_orders_task',
            'schedule': 900.0,
        },
        'fetch-creators-every-hour': {
            'task': 'tasks.fetch_creators_task',
            'schedule': 3600.0,  # 1 hour
        },
        'fetch-creator-works-every-hour': {
            'task': 'tasks.fetch_creator_works_task',
            'schedule': 3600.0,  # 1 hour
        },
        'check-alerts-every-5-minutes': {
            'task': 'tasks.check_alerts_task',
            'schedule': 300.0,  # 5 minutes
        },
        'refresh-oauth-token-every-30-minutes': {
            'task': 'tasks.refresh_oauth_token_task',
            'schedule': 1800.0,  # 30 minutes
        },
        'scheduled-job-every-hour': {
            'task': 'tasks.scheduled_job_task',
            'schedule': 3600.0,  # 1 hour
        },
    },
)
