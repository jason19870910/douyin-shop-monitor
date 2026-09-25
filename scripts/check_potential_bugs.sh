#!/bin/bash
# Check for potential bugs similar to INC-20260824-001
set -e

echo "=========================================="
echo "  Potential Bug Check (based on INC-20260824-001)"
echo "=========================================="

echo ""
echo "=== 1. Frontend container file permissions ==="
docker exec douyin_frontend ls -la /usr/share/nginx/html/ 2>&1 | head -15
echo ""
echo "--- assets dir ---"
docker exec douyin_frontend ls -la /usr/share/nginx/html/assets/ 2>&1 | head -10

echo ""
echo "=== 2. Check if any files have 700/600 permissions (potential 403) ==="
docker exec douyin_frontend find /usr/share/nginx/html -maxdepth 3 -perm 700 -o -perm 600 2>&1 | head -10
echo "(empty = no issues)"

echo ""
echo "=== 3. Monitor container file permissions ==="
docker exec douyin_monitor ls -la /app/ 2>&1 | head -15

echo ""
echo "=== 4. Monitor container - check for permission issues ==="
docker exec douyin_monitor find /app -maxdepth 2 -perm 700 -type d 2>&1 | head -10
echo "(empty = no issues)"

echo ""
echo "=== 5. Nginx config - check CSP and upstream ==="
echo "--- CSP policy ---"
grep -rn "Content-Security-Policy" /opt/douyin-platform/nginx/ 2>&1 | head -5
echo ""
echo "--- upstream config ---"
grep -n "server " /opt/douyin-platform/nginx/nginx.conf 2>&1 | head -5

echo ""
echo "=== 6. Check if Google Fonts is referenced in frontend ==="
docker exec douyin_frontend grep -r "fonts.googleapis.com" /usr/share/nginx/html/ 2>&1 | head -5

echo ""
echo "=== 7. Check all containers' file ownership ==="
for c in douyin_monitor douyin_frontend douyin_redis; do
  echo "--- $c ---"
  docker exec $c ls -la / 2>&1 | grep -E "app|usr|var|home" | head -5
done

echo ""
echo "=== 8. Check nginx error log for recent 403/404 ==="
docker logs douyin_nginx 2>&1 | grep -E "403|404" | tail -10

echo ""
echo "=== 9. Check frontend index.html for external resources ==="
docker exec douyin_frontend cat /usr/share/nginx/html/index.html 2>&1 | grep -E "https?://" | head -10

echo ""
echo "=== 10. Test all key endpoints ==="
curl -sk -o /dev/null -w "Frontend index.html: HTTP %{http_code}\n" https://wlkj-tech.cn
curl -sk -o /dev/null -w "Frontend JS: HTTP %{http_code}\n" https://wlkj-tech.cn/assets/index-DAmdn99Y.js
curl -sk -o /dev/null -w "API health: HTTP %{http_code}\n" https://wlkj-tech.cn/api/v1/health
curl -sk -o /dev/null -w "Google Fonts (via CSP): HTTP %{http_code}\n" https://fonts.googleapis.com/css2?family=Inter

echo ""
echo "=== Check Complete ==="
