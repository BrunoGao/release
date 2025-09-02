import concurrent.futures

# 并行查询昨天数据 - 确保结果不为None
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    yesterday_futures = {
        # 'health_count': executor.submit(query_yesterday_health),  # 临时注释
        'alert_count': executor.submit(query_yesterday_alerts),
        'active_devices': executor.submit(query_yesterday_active_devices)
    }
    
    yesterday_results = {}
    for key, future in yesterday_futures.items():
        try:
            result = future.result(timeout=2)
            yesterday_results[key] = result if result is not None else 0
        except:
            yesterday_results[key] = 0

yesterday_stats = {
    'healthData': yesterday_results['health_count'],
    'pendingAlerts': yesterday_results['alert_count'],
    'activeDevices': yesterday_results['active_devices'],
    'unreadMessages': results['message_count']  # 消息数据用今天的作为基准
} 