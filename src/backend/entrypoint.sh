#!/bin/sh
# Flexible entrypoint that runs the command passed as arguments
# Cleans up Python cache before starting

# Clean up Python bytecode cache
find /app -name '*.pyc' -delete 2>/dev/null || true
find /app -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# Execute the command passed as arguments (from docker-compose CMD)
exec "$@"
