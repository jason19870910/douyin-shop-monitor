#!/usr/bin/env bash
# GitHub Secrets Configuration Script (Bash/Linux version)
# Run after installing GitHub CLI: https://cli.github.com/
# Then authenticate: gh auth login

# ==========================================
# REQUIRED: Server Access Secrets
# ==========================================
# gh secret set SERVER_HOST --body "122.51.208.138"
# gh secret set SERVER_USER --body "root"
# gh secret set SERVER_SSH_KEY --body "$(cat ~/.ssh/id_rsa)"

# ==========================================
# REQUIRED: Application Config
# ==========================================
# gh secret set ALERT_EMAIL --body "your-email@example.com"
# gh secret set API_AUTH_TOKEN --body "your-secure-api-token-here"

# ==========================================
# REQUIRED: Douyin API Secrets (from Douyin Developer Console)
# ==========================================
# gh secret set DOUYIN_APP_ID --body "your-douyin-app-id"
# gh secret set DOUYIN_APP_SECRET --body "your-douyin-app-secret"
# gh secret set DOUYIN_ACCESS_TOKEN --body "your-douyin-access-token"

# ==========================================
# REQUIRED: Service Cookies & Tokens (from Browser DevTools)
# ==========================================
# gh secret set FXG_COOKIES --body "your-fxg-cookies"
# gh secret set CREATOR_COOKIES --body "your-creator-cookies"
# gh secret set TOKEN --body "your-token"
# gh secret set MS_TOKEN --body "your-ms-token"
# gh secret set A_BOGUS --body "your-a-bogus"
# gh secret set VERIFY_FP --body "your-verify-fp"
# gh secret set FP --body "your-fp"
# gh secret set FXG_SHOP_ID --body "your-fxg-shop-id"
# gh secret set FXG_LOG_ID --body "your-fxg-log-id"
# gh secret set API_KEY --body "your-api-key"

# ==========================================
# OPTIONAL: Notifications
# ==========================================
# gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/xxx"
# gh secret set DISCORD_WEBHOOK_URL --body "https://discord.com/api/webhooks/xxx"
# gh secret set WEBHOOK_URL --body "https://your-webhook-url"

# ==========================================
# REPOSITORY VARIABLES (non-sensitive config)
# ==========================================
# gh variable set REGISTRY --body "ghcr.io"
# gh variable set IMAGE_NAME --body "your-github-username/douyin"
# gh variable set DEPLOY_PATH --body "/opt/douyin-platform"

# ==========================================
# AFTER CONFIGURING SECRETS: Trigger Workflow
# ==========================================
# gh workflow run deploy.yml

# ==========================================
# VERIFY SECRETS ARE SET
# ==========================================
# gh secret list
# gh variable list