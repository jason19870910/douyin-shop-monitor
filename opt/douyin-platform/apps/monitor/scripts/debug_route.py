import sys
sys.path.insert(0, '/app')
import app

# Test the route handler directly
with app.app.test_request_context('/dashboard'):
    from app import serve_frontend
    result = serve_frontend('dashboard')
    print("Result status:", result.status_code)
    print("Result data:", result.data[:500])