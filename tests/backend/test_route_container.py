import sys
sys.path.insert(0, '/app')
import app
app.app.testing = True
c = app.app.test_client()
r = c.get("/dashboard")
print("Status:", r.status_code)
print("Data:", r.data[:500])