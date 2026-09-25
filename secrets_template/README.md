# Docker Secrets 模板说明

将以下 13 个文件放入服务器 `/opt/douyin-platform/secrets/` 目录，**必须替换为真实值**（不要留 placeholder）。

## 必填项 (7 个) - 外部 API 抓取依赖

| 文件名                   | 对应环境变量              | 获取方式                                                                     | 示例格式                                                                         |
| --------------------- | ------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `fxg_cookies.txt`     | `FXG_COOKIES`       | 浏览器登录 fxg.jinritemai.com → F12 Network → 任意请求 → Request Headers → Cookie | `passport_csrf_token=xxx; sessionid=xxx; PHPSESSID=xxx; ...` (完整 Cookie 字符串) |
| `creator_cookies.txt` | `CREATOR_COOKIES`   | 浏览器登录 creator.douyin.com → F12 Network → 任意请求 → Cookie                   | `passport_csrf_token=xxx; sessionid=xxx; ttwid=xxx; ...`                     |
| `token.txt`           | `__TOKEN` / `TOKEN` | 从 Cookie 中的 `passport_csrf_token` 或页面 `__TOKEN` 变量获取                     | `abc123def456`                                                               |
| `ms_token.txt`        | `MS_TOKEN`          | 页面 JS 变量 `window.__INIT_DATA__` 或抓包获取                                    | `xxx.yyy.zzz` (JWT 格式)                                                       |
| `a_bogus.txt`         | `a_bogus`           | 由后端 `douyin_sign.py` (V8) 实时生成，**也可手工填入长效值**                             | `abc123...` (长字符串)                                                           |
| `verify_fp.txt`       | `verifyFp`          | 页面渲染时注入的指纹参数                                                             | `verify_xxx...`                                                              |
| `fp.txt`              | `fp`                | 同上                                                                       | `fp_xxx...`                                                                  |

## 选填项 (6 个) - 补充配置

| 文件名                       | 对应环境变量                | 说明                                 | 示例                                 |
| ------------------------- | --------------------- | ---------------------------------- | ---------------------------------- |
| `douyin_access_token.txt` | `DOUYIN_ACCESS_TOKEN` | OAuth 2.0 access\_token (用于开放平台调用) | `xxx.xxx.xxx`                      |
| `fxg_shop_id.txt`         | `FXG_SHOP_ID`         | 抖店店铺 ID (数字)                       | `4272`                             |
| `fxg_log_id.txt`          | `FXG_LOG_ID`          | 抖店日志 ID                            | `104476165896`                     |
| `api_key.txt`             | `API_KEY`             | 内部服务间调用认证                          | `your_api_key`                     |
| `douyin_app_id.txt`       | `DOUYIN_APP_ID`       | 已有真实值                              | `aw370towtp6bg82b`                 |
| `douyin_app_secret.txt`   | `DOUYIN_APP_SECRET`   | 已有真实值                              | `a4fae3b38c0b1ee982c849fb3b23b353` |

***

## 快速生成脚本 (在服务器执行)

```bash
cd /opt/douyin-platform/secrets

# 示例：批量写入 (请替换 YOUR_REAL_VALUE)
cat > fxg_cookies.txt <<'EOF'
YOUR_REAL_FXG_COOKIES_STRING
EOF

cat > creator_cookies.txt <<'EOF'
YOUR_REAL_CREATOR_COOKIES_STRING
EOF

cat > token.txt <<'EOF'
YOUR_REAL_TOKEN
EOF

cat > ms_token.txt <<'EOF'
YOUR_REAL_MS_TOKEN
EOF

cat > a_bogus.txt <<'EOF'
YOUR_REAL_A_BOGUS
EOF

cat > verify_fp.txt <<'EOF'
YOUR_REAL_VERIFY_FP
EOF

cat > fp.txt <<'EOF'
YOUR_REAL_FP
EOF

# 选填 (如有)
echo "4272" > fxg_shop_id.txt
echo "104476165896" > fxg_log_id.txt
```

***

## 验证 Secrets 生效

```bash
# 1. 重启服务
cd /opt/douyin-platform && docker compose restart monitor celery_worker celery_beat

# 2. 检查配置加载
docker exec douyin_monitor python -c "
from config import Config
print('FXG_COOKIES:', 'loaded' if Config.FXG_COOKIES != 'placeholder' else 'MISSING')
print('CREATOR_COOKIES:', 'loaded' if Config.CREATOR_COOKIES != 'placeholder' else 'MISSING')
"

# 3. 触发同步测试
curl -X POST http://localhost:5000/api/v1/sync

# 4. 看 Worker 日志
docker logs --tail 50 douyin_celery_worker
```

***

## 常见问题

| 现象                   | 原因                     | 解决               |
| -------------------- | ---------------------- | ---------------- |
| 抓取返回 401             | Cookie 过期/不全           | 重新抓包获取完整 Cookie  |
| 返回 403               | `a_bogus`/`msToken` 错误 | 确认签名参数实时生成或更新长效值 |
| 返回 429               | 频率限制                   | 降低定时任务频率 / 增加延迟  |
| data\_source 仍为 mock | Redis 无数据 / 抓取失败       | 检查 Worker 日志报错   |

***

## 文件权限

```bash
chmod 600 /opt/douyin-platform/secrets/*.txt
chown root:root /opt/douyin-platform/secrets/*.txt
```

