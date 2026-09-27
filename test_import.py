from celery_config import celery_app
print("Before import tasks:", list(celery_app.tasks.keys()))

import tasks

print("After import tasks:", list(celery_app.tasks.keys()))