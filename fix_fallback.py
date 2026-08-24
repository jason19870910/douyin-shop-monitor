import re

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'r') as f:
    content = f.read()

# Find and replace the get_data_with_fallback function
old_func = '''def get_data_with_fallback(cache_key: str, mock_data: list) -> tuple[list, str]:
    """
    获取数据，如果缓存为空则返回模拟数据
    返回: (data_list, data_source)  data_source: 'real' 或 'mock'
    """
    data = data_cache.get(cache_key, [])
    if data and len(data) > 0:
        # 数据恢复真实，记录日志并重置告警状态
        tracker = _get_redis_tracker()
        if tracker.get(cache_key, {}).get('is_mock'):
            logger.info(f"[Fallback] {cache_key} 数据源已恢复: mock -> real")
            tracker[cache_key] = {'is_mock': False, 'start_time': None}
            _save_redis_tracker(tracker)
            alert_sent = _get_redis_alert_sent()
            alert_sent[cache_key] = False
            _save_redis_alert_sent(alert_sent)
        return data, 'real'

    # 使用模拟数据
    tracker = _get_redis_tracker()
    now = datetime.now()

    if not tracker.get(cache_key, {}).get('is_mock'):
        # 首次切换到 mock，记录开始时间
        tracker[cache_key] = {'is_mock': True, 'start_time': now.isoformat()}
        _save_redis_tracker(tracker)
        logger.warning(f"[Fallback] {cache_key} 数据源切换: real -> mock (外部 API 无数据，启用模拟数据)")
    else:
        # 持续使用 mock，检查是否超过阈值需告警
        start_time = datetime.fromisoformat(tracker[cache_key]['start_time'])
        elapsed_minutes = (now - start_time).total_seconds() / 60
        alert_sent = _get_redis_alert_sent()
        if elapsed_minutes >= MOCK_ALERT_THRESHOLD_MINUTES and not alert_sent.get(cache_key, False):
            logger.error(f"[Fallback Alert] {cache_key} 持续使用模拟数据超过 {MOCK_ALERT_THRESHOLD_MINUTES} 分钟，请检查外部 API 凭证！")
            # 发送告警邮件
            send_mock_fallback_alert(cache_key, int(elapsed_minutes))
            alert_sent[cache_key] = True
            _save_redis_alert_sent(alert_sent)

    '''

new_func = '''def get_data_with_fallback(cache_key: str, mock_data: list) -> tuple[list, str]:
    """
    获取数据，如果缓存为空则返回模拟数据
    返回: (data_list, data_source)  data_source: 'real' 或 'mock'
    """
    data = data_cache.get(cache_key, [])
    if data and len(data) > 0:
        # 数据恢复真实，记录日志并重置告警状态
        tracker = _get_redis_tracker()
        if tracker.get(cache_key, {}).get('is_mock'):
            logger.info(f"[Fallback] {cache_key} 数据源已恢复: mock -> real")
            tracker[cache_key] = {'is_mock': False, 'start_time': None}
            _save_redis_tracker(tracker)
            alert_sent = _get_redis_alert_sent()
            alert_sent[cache_key] = False
            _save_redis_alert_sent(alert_sent)
        return data, 'real'

    # 使用模拟数据
    tracker = _get_redis_tracker()
    now = datetime.now()

    if not tracker.get(cache_key, {}).get('is_mock'):
        # 首次切换到 mock，记录开始时间
        tracker[cache_key] = {'is_mock': True, 'start_time': now.isoformat()}
        _save_redis_tracker(tracker)
        logger.warning(f"[Fallback] {cache_key} 数据源切换: real -> mock (外部 API 无数据，启用模拟数据)")
    else:
        # 持续使用 mock，检查是否超过阈值需告警
        start_time = datetime.fromisoformat(tracker[cache_key]['start_time'])
        elapsed_minutes = (now - start_time).total_seconds() / 60
        alert_sent = _get_redis_alert_sent()
        if elapsed_minutes >= MOCK_ALERT_THRESHOLD_MINUTES and not alert_sent.get(cache_key, False):
            logger.error(f"[Fallback Alert] {cache_key} 持续使用模拟数据超过 {MOCK_ALERT_THRESHOLD_MINUTES} 分钟，请检查外部 API 凭证！")
            # 发送告警邮件
            send_mock_fallback_alert(cache_key, int(elapsed_minutes))
            alert_sent[cache_key] = True
            _save_redis_alert_sent(alert_sent)

    # 更新缓存，确保后续任务也能使用模拟数据
    data_cache[cache_key] = mock_data
    return mock_data, 'mock'
'''

content = content.replace(old_func, new_func)

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'w') as f:
    f.write(content)

print("Fixed!")