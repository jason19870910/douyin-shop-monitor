# Release ${version}

${changelog}

---

## 📦 Docker Images

| Image | Tag |
|-------|-----|
| Backend | `ghcr.io/jason19870910/douyin-shop-monitor-backend:${version}` |
| Frontend | `ghcr.io/jason19870910/douyin-shop-monitor-frontend:${version}` |

## 🚀 部署

推送到 main 分支后，GitHub Actions 将自动构建并部署到服务器。

```bash
# 服务器手动拉取指定版本
docker pull ghcr.io/jason19870910/douyin-shop-monitor-backend:${version}
docker pull ghcr.io/jason19870910/douyin-shop-monitor-frontend:${version}
```

---

> 此 PR 由 [release-please](https://github.com/googleapis/release-please) 自动生成。