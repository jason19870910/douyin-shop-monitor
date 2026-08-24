from app import app
app.testing = True
c = app.test_client()
r = c.get("/dashboard")
print("Status:", r.status_code)
print("Data:", r.data[:500])