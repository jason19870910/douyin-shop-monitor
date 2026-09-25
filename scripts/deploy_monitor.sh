#!/usr/bin/env bash
set -e
cd /opt/app/opt/douyin-platform/apps/monitor
docker compose down || true
docker compose up -d --build
