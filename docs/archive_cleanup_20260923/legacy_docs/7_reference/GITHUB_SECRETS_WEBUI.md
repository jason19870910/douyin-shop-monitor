# GitHub Secrets Web UI Configuration Guide

Since `gh` CLI is not installed, configure secrets via **GitHub Web UI**:

## Step 1: Open Repository Settings
1. Go to: `https://github.com/<YOUR_USERNAME>/<YOUR_REPO>/settings/secrets/actions`
2. Or navigate: Repository → Settings → Secrets and variables → Actions

## Step 2: Add Repository Secrets (Click "New repository secret" for each)

### Server Access (REQUIRED)
| Name | Value | Notes |
|------|-------|-------|
| `SERVER_HOST` | `122.51.208.138` | Production server IP |
| `SERVER_USER` | `root` | SSH username |
| `SERVER_SSH_KEY` | *(private key content)* | Copy from `C:\Users\Administrator\.ssh\id_rsa` |

### Application Config (REQUIRED)
| Name | Value | Notes |
|------|-------|-------|
| `ALERT_EMAIL` | `your-email@example.com` | Alert notifications |
| `API_AUTH_TOKEN` | `your-secure-token` | API authentication |

### Douyin API (REQUIRED - from Developer Console)
| Name | Value | Source |
|------|-------|--------|
| `DOUYIN_APP_ID` | `...` | Douyin Developer Console |
| `DOUYIN_APP_SECRET` | `...` | Douyin Developer Console |
| `DOUYIN_ACCESS_TOKEN` | `...` | OAuth flow |

### Service Cookies & Tokens (REQUIRED - from Browser DevTools)
| Name | Value | Source |
|------|-------|--------|
| `FXG_COOKIES` | `...` | Browser DevTools → Application → Cookies |
| `CREATOR_COOKIES` | `...` | Browser DevTools → Application → Cookies |
| `TOKEN` | `...` | API response |
| `MS_TOKEN` | `...` | API response |
| `A_BOGUS` | `...` | API response |
| `VERIFY_FP` | `...` | API response |
| `FP` | `...` | API response |
| `FXG_SHOP_ID` | `...` | Douyin Service Provider |
| `FXG_LOG_ID` | `...` | Douyin Service Provider |
| `API_KEY` | `...` | Generated |

### Notifications (OPTIONAL)
| Name | Value |
|------|-------|
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/...` |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` |
| `WEBHOOK_URL` | `https://your-webhook-url` |

## Step 3: Add Repository Variables (Non-sensitive)
Go to: **Settings → Secrets and variables → Actions → Variables tab**

| Name | Value |
|------|-------|
| `REGISTRY` | `ghcr.io` |
| `IMAGE_NAME` | `<YOUR_GITHUB_USERNAME>/douyin` |
| `DEPLOY_PATH` | `/opt/douyin-platform` |

## Step 4: Trigger Workflow
After ALL secrets are configured:

### Option A: GitHub Web UI
1. Go to: **Actions → Deploy to Production**
2. Click **Run workflow** → Select `main` branch → **Run workflow**

### Option B: GitHub CLI (after installing)
```bash
winget install GitHub.cli
gh auth login
gh workflow run deploy.yml
```

### Option C: Push to main
```bash
git add .
git commit -m "Configure deployment"
git push origin main
```

## Step 5: Verify
1. Check **Actions** tab for workflow run
2. Monitor deployment logs
3. Verify health checks pass:
   - `https://wlkj-tech.cn/health` → `healthy`
   - `https://wlkj-tech.cn/api/v1/health` → `{"success":true}`

## ⚠️ Important Notes
- **Never commit secrets** to the repository
- **Rotate secrets** periodically
- **Test manually first** using `./scripts/deploy-production.sh` on server
- **SSH key must be private key** (not public), with no passphrase
- **Server user needs Docker permissions**: `usermod -aG docker root`