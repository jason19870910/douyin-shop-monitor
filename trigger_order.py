from tasks import fetch_orders_task
result = fetch_orders_task.delay()
print('Task ID:', result.id)
print('Result:', result.get(timeout=60))