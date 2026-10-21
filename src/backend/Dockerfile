# Use official Python runtime
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Use faster apt mirrors (Aliyun)
# 注意：python:3.11-slim 基于 Debian trixie，deb822 源文件位于
# /etc/apt/sources.list.d/debian.sources（旧路径在 trixie 中不存在，
# sed 曾因路径不匹配静默失效，导致 apt 直连 deb.debian.org 失败）。
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# Install system dependencies (no git needed - version files are pre-generated)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.lock.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy pre-generated version info files (generated on host with git access)
COPY data/version_info.json /data/version_info.json
COPY data/changes_info.json /data/changes_info.json

# Copy application code
COPY . .

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