# Nginx 配置参考

**文件**：`/etc/nginx/conf.d/wlkj-tech.cn.conf`
**作用**：为 `wlkj-tech.cn` 提供 HTTPS 反向代理，分发 `/api/` 到 Python 数据服务，其余到 Node 管理后台。

---

## 完整配置

```nginx
server {
    listen 80;
    server_name wlkj-tech.cn www.wlkj-tech.cn;
    return 301 https://wlkj-tech.cn$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wlkj-tech.cn www.wlkj-tech.cn;

    ssl_certificate /etc/letsencrypt/live/wlkj-tech.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wlkj-tech.cn/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # API 代理（注意：proxy_pass 末尾无斜杠）
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cookie_domain localhost $host;
    }

    # 主应用（Node 管理后台）
    location / {
        client_max_body_size 200M;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 关键说明

### HTTP → HTTPS 重定向
`server` 监听 80 端口，将所有请求 301 跳转到 HTTPS。

### API 代理细节
- `location /api/` 匹配所有以 `/api/` 开头的请求
- `proxy_pass http://127.0.0.1:5000;` **不带尾部 `/`**
  - 如果写成 `proxy_pass http://127.0.0.1:5000/;`，nginx 会**剥离** `/api` 前缀，再转发到上游。
  - 例如：`/api/creator` → 上游收到 `/creator` → Flask 路由不匹配（Flask 期望 `/api/creator`）→ 404。
  - 去掉尾部 `/`，原路径 `/api/creator` 会完整传递到上游，匹配成功。

### WebSocket 支持
`/` location 中 `Upgrade`/`Connection` 头支持 WebSocket（Node 应用如果需要）。

### Cookie 域转换
`proxy_cookie_domain localhost $host;` 确保上游 `Set-Cookie` 中的 `localhost` 被替换为实际域名，避免客户端拒收。

---

## 验证与重载

```bash
# 测试配置语法
nginx -t

# 重载（不中断服务）
systemctl reload nginx

# 检查监听端口
ss -tlnp | grep -E ':80|:443'
```

---

## 问题排查

| 现象 | 可能原因 | 检查点 |
|------|----------|--------|
| `https://wlkj-tech.cn/api/creator` 返回 404 | `proxy_pass` 末尾多 `/` | 确认该行无尾部 `/` |
| API 响应缓慢 | 上游服务未响应 | 检查 5000 端口进程：`ss -tlnp \| grep 5000` |
| SSL 证书错误 | 证书文件路径或权限 | 确认 `/etc/letsencrypt/live/wlkj-tech.cn/` 存在且 nginx 可读 |

---

**维护记录**：
- 2026-06-16：首次添加 `/api/` 代理，并修正尾部斜杠问题。
