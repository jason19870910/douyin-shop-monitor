# Read the current app.py
with open('/opt/douyin-platform/apps/monitor/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of " if __name__ == __main__ :\ (single quotes)
marker = \if __name__ == __main__ :\
pos = content.rfind(marker)
if pos == -1:
 print(\ERROR: Could not find main block\)
 exit(1)

# The new code to insert before the main block
new_code = '''

# -------------------------------------------------
# 1\ufe0f\u20e3 重新加载 .env 并刷新全局变量的函数
# -------------------------------------------------
def reload_env():
 \\\重新读取 .env 并把关键变量写回全局作用域\\\
 load_dotenv(override=True)
 global COOKIE, HOMEPAGE_URL, PRODUCT_URL, ORDERS_URL, PRODUCTS_URL, COMPASS_URL
 global CREATOR_COOKIE, CREATOR_CSRF_TOKEN, CREATOR_URL
 COOKIE = os.getenv(\COOKIE\, \\)
 HOMEPAGE_URL = os.getenv(\HOMEPAGE_URL\, \\)
 PRODUCT_URL = os.getenv(\PRODUCT_URL\, \\)
 ORDERS_URL = os.getenv(\ORDERS_URL\, \\)
 PRODUCTS_URL = os.getenv(\PRODUCTS_URL\, \\)
 COMPASS_URL = os.getenv(\COMPASS_URL\, \\)
 CREATOR_COOKIE = os.getenv(\CREATOR_COOKIE\, \\)
 CREATOR_CSRF_TOKEN = os.getenv(\CREATOR_CSRF_TOKEN\, \\)
 CREATOR_URL = os.getenv(\CREATOR_URL\, \https://creator.douyin.com/janus/douyin/creator/data/overview/dashboard\)
 logger.info(\\u2705 .env \u5df2\u70ed\u91cd\u8f7d\uff0c\u5173\u9525\u914d\u7f6e\u5df2\u5237\u65b0\u5230\u5185\u5b58\)
 return True

# -------------------------------------------------
# 2\ufe0f\u20e3 \u70ed\u91cd\u8f7d\u8def\u7531\uff08\u5916\u90e8\u7a0b\u5e8f\u8c03\u7528\uff09
# -------------------------------------------------
@app.route(\/admin/reload-config\, methods=[\POST\])
def admin_reload_config():
 \\\\u901a\u8fc7 X-API-KEY \u9274\u6743\u540e\u91cd\u65b0\u52a0\u8f7d\u73af\u5883\u53d8\u91cf\\\
 api_key = os.getenv(\API_KEY\)
 req_key = request.headers.get(\X-API-KEY\)
 if api_key and req_key != api_key:
 logger.warning(\\u70ed\u91cd\u8f7d\u9274\u6743\u5931\u8d25\uff0c\u63d0\u4f9b\u7684 X-API-KEY \u4e0d\u5339\u914d\)
 return jsonify({\error\: \Invalid API key\}), 401
 try:
 reload_env()
 return jsonify({
 \status\: \reloaded\,
 \ts\: datetime.utcnow().isoformat() + \Z\,
 \dataSourceMode\: os.getenv(\DATA_SOURCE_MODE\, \api\)
 })
 except Exception as e:
 logger.error(f\\u70ed\u91cd\u8f7d\u5f02\u5e38: -encodedCommand ZQA= \)
 return jsonify({\error\: \Reload failed\}), 500

'''

# Insert before the main block
new_content = content[:pos] + new_code + \\\n\ + content[pos:]

# Also remove the duplicate code that was appended at the end (after app.run)
# Find the last occurrence of the duplicate reload_env function
dup_marker = '# -------------------------------------------------\\n# 1\ufe0f\u20e3 \u91cd\u65b0\u52a0\u8f7d .env \u5e76\u5237\u65b0\u5168\u5c40\u53d8\u91cf\u7684\u51fd\u6570'
last_dup = new_content.rfind(dup_marker)
if last_dup > pos: # Only if it's after the main block
 new_content = new_content[:last_dup]

# Write back
with open('/opt/douyin-platform/apps/monitor/app.py', 'w', encoding='utf-8') as f:
 f.write(new_content)

print(\SUCCESS: app.py updated\)
EOF -inputFormat xml -outputFormat text
