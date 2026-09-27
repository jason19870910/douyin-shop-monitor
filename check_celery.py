from celery_config import celery_app
print("Registered tasks:")
for name in sorted(celery_app.tasks.keys()):
    print(f"  {name}")