# GitHub Secrets 完整配置（从服务器 .env 提取）

> **复制下表的值到 GitHub Web UI**：`Settings → Secrets and variables → Actions → New repository secret`

---

## 🔐 必需 Secrets (19 个)

### 1. 服务器访问
| Secret 名称 | 值 |
|-------------|-----|
| `SERVER_HOST` | `122.51.208.138` |
| `SERVER_USER` | `root` |
| `SERVER_SSH_KEY` | 见下方完整私钥 |

**SSH 私钥 (SERVER_SSH_KEY) 完整内容：**
```
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

### 2. 应用配置
| Secret 名称 | 值 |
|-------------|-----|
| `ALERT_EMAIL` | `262368285@qq.com` |
| `API_AUTH_TOKEN` | `test-secret-key-12345` |
| `WEBHOOK_URL` | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4b6598f0-5864-49da-b185-f864c25241d6` |

### 3. 抖音 API (从开发者后台)
| Secret 名称 | 值 |
|-------------|-----|
| `DOUYIN_APP_ID` | `aw370towtp6bg82b` |
| `DOUYIN_APP_SECRET` | `a4fae3b38c0b1ee982c849fb3b23b353` |
| `DOUYIN_ACCESS_TOKEN` | **需从抖音开放平台获取** (当前 .env 中无) |

### 4. 服务商后台 Cookies & Tokens (从 .env URL 提取)

| Secret 名称 | 值 | 来源 |
|-------------|-----|------|
| `FXG_COOKIES` | `csrf_session_id=d31ca52098fd7a3315cb4f1a4bc40bad; ecom_gray_shop_id=257675707; ecom_us_lt=e15efaf78c5ac26392fe04fa6e61b432b281b014cf93da769498df30ffc2b9ff; ecom_us_lt_ss=e15efaf78c5ac26392fe04fa6e61b432b281b014cf93da769498df30ffc2b9ff; gfkadpd=2631,22740; gfkadpd=4272,23756|4272,47079; has_biz_token=false; Hm_lpvt_b6520b076191ab4b36812da4c90f7a5e=1785045018; Hm_lvt_b6520b076191ab4b36812da4c90f7a5e=1785045018; HMACCOUNT=A3E03C7D1CB932E6; is_staff_user=false; odin_tt=bd5d539222e731092bbeae036a8c93727a753d87f95e4c99d653c17d9eb607e23e34e6d0eaa39637c2cf0580a4fa3199a3e42dc9dc73913bf3ae6cb315100b7c; passport_auth_status=e73269e7c55d198acc2b57ccfbd4bb18%2C; passport_auth_status_ss=e73269e7c55d198acc2b57ccfbd4bb18%2C; passport_csrf_token=e29659c267689024bc663a949dc9bf48; passport_csrf_token_default=e29659c267689024bc663a949dc9bf48; PHPSESSID=3648862cb9f7fc2b0d4ca0d99747d7b2` | .env COOKIE |
| `CREATOR_COOKIES` | 见下方完整值 | .env CREATOR_COOKIE |

**CREATOR_COOKIES 完整值：**
```
bd_ticket_guard_client_web_domain=2; passport_csrf_token=25e76583dcf9b85b48c97b62f9497674; passport_csrf_token_default=25e76583dcf9b85b48c97b62f9497674; n_mh=Pz0yGxme-NaIWjLY6FBjan52DOIXXMxK7V4-c5bQM-Y; is_staff_user=false; has_biz_token=false; _bd_ticket_crypt_doamin=2; __security_server_data_status=1; _tea_utm_cache_2906=undefined; csrf_session_id=3bb80ba3bd640a3f1156bd76c7f72af8; x-web-secsdk-uid=528fd214-20e6-4897-86b9-215a59b2a15d; passport_fe_beating_status=true; gfkadpd=2906,33638; gd_random=eyJtYXRjaCI6ZmFsc2UsInBlcmNlbnQiOjAuOTgxNjY1OTg4MTc4ODc4NX0=.oLFLlFg9vuDSDsgwDPltVyHlUWDFzKQw9hRv3AUrFt8=; biz_trace_id=26d32341; passport_assist_user=CkBSKyuQ3pKZP613tPWW0-pvqt_4RWVE1_wp_UCo-xOXwQuu5uCxa2vF-JGF0ApSOYJ87B-QrfauE5WOHsnSOQ1RGkoKPAAAAAAAAAAAAABQtJW_IadZUhp22XzTqtpPU4CJ8t62rsPeRhQwoSZEo3KEMuChuzuz2Ue1wF1Xlipj7hC_6ZcOGImv1lQgASIBA1DTKdw%3D; sid_guard=95a882b720e9355a1e0729f7780dc2ab%7C1785035030%7C5184000%7CThu%2C+24-Sep-2026+03%3A03%3A50+GMT; uid_tt=f2ed48d95c9ee95a225c6944c64679cb; uid_tt_ss=f2ed48d95c9ee95a225c6944c64679cb; sid_tt=95a882b720e9355a1e0729f7780dc2ab; sessionid=95a882b720e9355a1e0729f7780dc2ab; sessionid_ss=95a882b720e9355a1e0729f7780dc2ab; session_tlb_tag=sttt%7C18%7ClaiCtyDpNVoeByn3eA3Cq__________SIgNuCCkX8grBq1GSt_XcafpIhPAUbhbe670sfY-L6bM%3D; sid_ucp_v1=1.0.0-KGQyNTNhODEzMmQ2ZmQ2NmQ2YzIxNWUzZWQ5ZTdlY2QwMDYxODA3YjAKIAj7j5CtsPQ-EJbyldMGGNoWIAwwkLbB6QU4B0D0B0gEGgJsZiIgOTVhODgyYjcyMGU5MzU1YTFlMDcyOWY3NzgwZGMyYWI; ssid_ucp_v1=1.0.0-KGQyNTNhODEzMmQ2ZmQ2NmQ2YzIxNWUzZWQ5ZTdlY2QwMDYxODA3YjAKIAj7j5CtsPQ-EJbyldMGGNoWIAwwkLbB6QU4B0D0B0gEGgJsZiIgOTVhODgyYjcyMGU5MzU1YTFlMDcyOWY3NzgwZGMyYWI; bd_ticket_guard_generate_ticket_time=2026-07-26/11:03:50; bd_ticket_guard_ts_sign_id=ts.2.6ac27f80b220022; _bd_ticket_crypt_cookie=66032055e31843e1fd6d43f48fd3ad9b; __security_mc_1_s_sdk_sign_data_key_web_protect=11e4a425-49c0-883a; __security_mc_1_s_sdk_cert_key=1828af54-4fe6-a5bb; __security_mc_1_s_sdk_crypt_sdk=b864a888-4a83-8aa8; odin_tt=bbaac8dafd16d7bcbdad49706319eb3bf16c3df7642cea6cd2701e9b14796485efff7c8b1ae15ca19c80c766fc542d02105f6e164ef55636eb06eaaf687e631b; ttwid=1%7CZmT7SecwYoi9fADSbvrHFOZGboX3FtUW4mj0ndaBsow%7C1785035436%7C3d0e1ef3be94225b255df7e92ee988d94e62de97ab37cb855f900a1f4013590d; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQjkzUjc2cnIwbVYwSlc5NXZCYVBrVFllWUhTRU4wQm5sZ0dOVzZzbWNIOWlReFFwRUFuWXhJbFl2TTl6WGlGcUtZWW5TTDNuaXBoeGd3czMweWYzN1U9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJCOTNSNzZycjBtVjBKVzk1dkJhUGtUWWVZSFNFTjBCbmxnR05XNnNtY0g5aVF4UXBFQW5ZeElsWXZNOXpYaUZxS1lZblNMM25pcGh4Z3dzMzB5ZjM3VT0iLCJ0c19zaWduIjoidHMuMi42YWMyN2Y4MGIyMjAwMjI2ZjA1ZWFkOTJkNTAzY2M2ODgzN2I3YmZmNGFkMWU4MmMwY2U1OGE4NzU0ZjgwODg5YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJiY2tqT2JzQjVoWDVydk5PcllKd1Z3MFJaZ3ppWFJXUzhxdHNqUC9EQWVNPSIsInNlY190cyI6IiM3SHFDa1ZTa0pBOGxiWXkwd2gxYldUVngrUUQ3ZE5wZ05JZnZWYnFPWGVHWU9kNjBmYnl3UzBJUFc1N0sifQ%3D%3D
```

### 5. 签名参数 (从 HOMEPAGE_URL 提取)
| Secret 名称 | 值 |
|-------------|-----|
| `TOKEN` | `61fa6e81e686819ef76699051a61b1c1` (HOMEPAGE_URL 中 `__token=`) |
| `MS_TOKEN` | `612NcGI-IYfe4nL6bFruJKJYk9GLj-m6EE_ZzpqKFDbDCfJb63R-lnfjx5HKZFmzrJRB6iMvx--RQuJFdm_dxM0h6ppQGeRCs4wpS9qJH5ySaIl8CjiC5-I5g2bzisvrAr3yvr6cMaVIYdtFVdf_y1FTtKA1xzXyoxHl3E8mKVgHX2VyT11D8A%3D%3D` |
| `A_BOGUS` | `m7UVkztyddQfPplt8CG-eH-lnIL%2Frs8y%2F-ioRaZF7Fzja7ePyzlaadGYcxwBsgDLaYB0ZK3H6VU%2FbdVcuqikZFHpumpvuhzy4GQA9yvLhqhdP-ihXqWmeRGYuJ-KA5uwmQI7icE1l0zLI2Q3hNczl-lGH5FOQYbDWrqSdMscG9WNVSfH99dUtBhS` |
| `VERIFY_FP` | `verify_mruo6fjh_UK1AD7cH_NawY_4Bzg_8MLp_w80M1kB13ddV` |
| `FP` | `verify_mruo6fjh_UK1AD7cH_NawY_4Bzg_8MLp_w80M1kB13ddV` |
| `FXG_SHOP_ID` | `475947298527` (HOMEPAGE_URL 中 `_lid=`) |
| `FXG_LOG_ID` | `287348850796` (ORDERS_URL 中 `_lid=`) |
| `API_KEY` | `test-secret-key-12345` |

---

## 📝 仓库 Variables (非敏感)

| Variable 名称 | 值 |
|---------------|-----|
| `REGISTRY` | `ghcr.io` |
| `IMAGE_NAME` | `<您的GitHub用户名>/douyin` |
| `DEPLOY_PATH` | `/opt/douyin-platform` |

---

## ⚠️ 需您手动补充的值

| Secret | 说明 |
|--------|------|
| `DOUYIN_ACCESS_TOKEN` | 抖音开放平台 OAuth 获取的 access_token，当前 .env 中没有 |

---

## 🚀 配置完成后触发部署

### 方式 1: 推送到 main 分支
```bash
git add .
git commit -m "Configure GitHub Secrets for deployment"
git push origin main
```

### 方式 2: GitHub Web UI 手动触发
1. 进入仓库 **Actions** 标签
2. 选择 **Deploy to Production** 工作流
3. 点击 **Run workflow** → 选择 `main` → **Run workflow**

### 方式 3: GitHub CLI (安装后)
```bash
gh workflow run deploy.yml
```

---

## ✅ 验证部署成功

部署完成后检查：
- `https://wlkj-tech.cn/health` → 返回 `healthy`
- `https://wlkj-tech.cn/api/v1/health` → 返回 `{"success":true,"data":{"status":"healthy"}}`
- GitHub Actions 显示绿色 ✅