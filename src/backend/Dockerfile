# Use official Python runtime
FROM python:3.11-slim AS builder

# Build args for version info
ARG APP_VERSION=dev
ARG APP_COMMIT=unknown
ARG APP_BUILT_AT=

# Set working directory
WORKDIR /app

# Use faster apt mirrors (Aliyun)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.lock.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy application code
COPY . .

# Generate version info file from build args
RUN mkdir -p /data && \
    echo "{\"version\":\"${APP_VERSION}\",\"commit\":\"${APP_COMMIT}\",\"builtAt\":\"${APP_BUILT_AT}\"}" > /data/version_info.json && \
    cat /data/version_info.json

# Generate changes info file (recent git log)
RUN git log --oneline -10 --pretty=format:'{"id":"%h","message":"%s","author":"%an","date":"%aI","type":"chore"}' 2>/dev/null | \
    sed 's/}{/},{/g' | \
    sed 's/^/[/' | \
    sed 's/$/]/' > /data/changes_info.json && \
    cat /data/changes_info.json

# Set entrypoint
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health').read()" || exit 1

# Use entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]