p = '/root/douyin_new/fetcher.py'
s = open(p, encoding='utf-8').read()
old = ("COMPLIANCE_FILE = DATA_DIR / 'compliance.json'  # 合规日志\n"
       "COMPLIANCE_RULES_FILE = DATA_DIR / 'compliance_rules.json'  # 合规规则（权威源）\n"
       "MEDIA_FILE = DATA_DIR / 'media.json'")
new = ("COMPLIANCE_FILE = DATA_DIR / 'compliance.json'  # 合规日志\n"
       "COMPLIANCE_RULES_FILE = DATA_DIR / 'compliance_rules.json'  # 合规规则（权威源）\n"
       "# 合规日志保留上限（Redis + 文件一致），防止无限增长拖慢读写\n"
       "COMPLIANCE_LOG_LIMIT = 10000\n"
       "# 仅记录违规/告警结果（fail/warning/error），pass 流水不落日志，\n"
       "# 避免违规列表被海量通过记录淹没\n"
       "COMPLIANCE_LOG_STATUSES = ('fail', 'warning', 'error')\n"
       "MEDIA_FILE = DATA_DIR / 'media.json'")
assert old in s, 'pattern not found'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
print('patched')
