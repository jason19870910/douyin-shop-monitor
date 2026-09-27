import celery_config
print("celery_app:", celery_config.celery_app)
print("Tasks:", list(celery_config.celery_app.tasks.keys()))