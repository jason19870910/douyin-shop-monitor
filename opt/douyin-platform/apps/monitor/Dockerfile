# Use official Python runtime
FROM docker.1ms.run/python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Use faster apt mirrors (Aliyun)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.debian.sources 2>/dev/null || 
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# Install system dependencies
RUN apt-get update 
    && apt-get install -