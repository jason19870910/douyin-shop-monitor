# Use official Python runtime
FROM docker.1ms.run/python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Use faster apt mirrors (Aliyun)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        libssl-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt ./
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# 环境变量：禁用字节码缓存、无缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5000

# Health check using Python (no curl needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health').read()" || exit 1

# 入口脚本：启动前清理字节码缓存
RUN echo '#!/bin/sh\nfind /app -name "*.pyc" -delete\nfind /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true\nexec gunicorn app:app --bind 0.0.0.0:5000 --workers 4' > /entrypoint.sh && chmod +x /entrypoint.sh

# Run the application
ENTRYPOINT ["/entrypoint.sh"]
