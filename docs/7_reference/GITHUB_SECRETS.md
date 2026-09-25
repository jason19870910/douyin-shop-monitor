# GitHub Secrets Configuration for Automated Deployment

Configure these secrets in your GitHub repository: **Settings → Secrets and variables → Actions**

## Required Secrets

### Server Access
| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SERVER_HOST` | Production server IP or hostname | `122.51.208.138` |
| `SERVER_USER` | SSH username for deployment | `root` |
| `SERVER_SSH_KEY` | Private SSH key for server access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### Application Secrets (Monitor Service)
| Secret Name | Description | Source |
|-------------|-------------|--------|
| `ALERT_EMAIL` | Email for alert notifications | `admin@example.com` |
| `API_AUTH_TOKEN` | API authentication token | `your-secure-token` |
| `DOUYIN_APP_ID` | 抖音应用 App ID | From Douyin Developer Console |
| `DOUYIN_APP_SECRET` | 抖音应用 App Secret | From Douyin Developer Console |
| `DOUYIN_ACCESS_TOKEN` | 抖音访问令牌 | From OAuth flow |
| `FXG_COOKIES` | 服务商后台 Cookie | Browser DevTools |
| `CREATOR_COOKIES` | 创作者后台 Cookie | Browser DevTools |
| `TOKEN` | 通用 token | From API |
| `MS_TOKEN` | msToken 参数 | From API |
| `A_BOGUS` | a_bogus 签名参数 | From API |
| `VERIFY_FP` | verify_fp 指纹 | From API |
| `FP` | fp 指纹 | From API |
| `FXG_SHOP_ID` | 服务商店铺 ID | From Douyin |
| `FXG_LOG_ID` | 服务商日志 ID | From Douyin |
| `API_KEY` | API 密钥 | Generated |

## Optional Secrets

### Notifications
| Secret Name | Description |
|-------------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook for notifications |
| `DISCORD_WEBHOOK_URL` | Discord webhook for notifications |
| `WEBHOOK_URL` | Generic webhook URL |

### Container Registry (if not using GHCR)
| Secret Name | Description |
|-------------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

## Setup Instructions

### 1. Generate SSH Key for Deployment
```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-actions-deploy

# Add public key to server's authorized_keys
ssh-copy-id -i ~/.ssh/github-actions-deploy.pub root@122.51.208.138

# Copy private key to GitHub secret SERVER_SSH_KEY
cat ~/.ssh/github-actions-deploy
```

### 2. Configure Server for Passwordless Docker
```bash
# On production server
usermod -aG docker root  # or your deployment user
systemctl restart docker
```

### 3. Set Up GitHub Secrets
1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret** for each secret above
4. Paste the values accordingly

### 4. Verify Deployment Works
```bash
# Test manual deployment
./scripts/deploy-production.sh latest

# Or trigger via GitHub Actions
gh workflow run deploy.yml
```

## Environment Variables (Repository Variables)

For non-sensitive configuration, use **Repository Variables** instead of secrets:

| Variable Name | Value |
|---------------|-------|
| `REGISTRY` | `ghcr.io` |
| `IMAGE_NAME` | `your-github-username/your-repo-name` |
| `DEPLOY_PATH` | `/opt/douyin-platform` |

## Security Notes

1. **Rotate secrets regularly** - Especially API tokens and cookies
2. **Use least privilege** - Create dedicated service accounts where possible
3. **Monitor secret access** - Check GitHub audit logs periodically
4. **Never commit secrets** - Use `.gitignore` for local `.env` files
5. **Separate environments** - Use different secrets for staging vs production

## Troubleshooting

### SSH Connection Fails
- Verify `SERVER_SSH_KEY` is the **private** key (not public)
- Check server allows key-based authentication
- Ensure deployment user has Docker permissions

### Docker Pull Fails
- Verify `GITHUB_TOKEN` has `packages:read` permission
- Check image names match: `ghcr.io/owner/repo/monitor:latest`

### Health Checks Fail
- Check container logs: `docker compose logs monitor`
- Verify ports 5000, 3000, 80, 443 are open
- Check nginx configuration and SSL certificates

### Secrets Not Found
- Secret names are **case-sensitive** in the workflow
- Must match exactly: `DOUYIN_APP_ID` not `douyin_app_id`