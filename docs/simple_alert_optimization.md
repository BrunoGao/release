# 简洁告警系统优化方案

## 📋 基于现有代码的简单改进

基于对 ljwx-bigscreen 现有 `generate_alerts` 函数的分析，提供最简洁有效的优化方案。

## 🔍 现状分析

### 当前 generate_alerts 函数问题：
1. **规则查询无过滤** - 每次都加载所有告警规则，未按数据类型过滤
2. **重复设备信息查询** - 每条规则都可能重复查询相同设备信息  
3. **缺乏通知渠道处理** - 触发告警后没有自动通知机制

### 现有优势：
- 已有 Redis 缓存机制
- 已有规则预编译逻辑
- 数据库查询已优化

## 🚀 三个简单优化

### 1. 规则按数据类型过滤 (最简单改进)

**问题**: 当前所有规则都被加载，浪费处理时间

**解决**: 在 `generate_alerts` 函数中按 physical_sign 过滤规则

```python
def generate_alerts(data, health_data_id):
    # 现有代码...获取所有规则
    
    # 🚀 新增: 从数据中提取当前的 physical_sign 类型
    current_physical_signs = set()
    for key in data.keys():
        if key in ['heartRate', 'bloodOxygen', 'temperature', 'pressureHigh', 'pressureLow', 
                  'stress', 'step', 'calorie', 'distance', 'sleep']:
            # 将前端字段映射到数据库字段
            sign_mapping = {
                'heartRate': 'heart_rate',
                'bloodOxygen': 'blood_oxygen', 
                'pressureHigh': 'bloodPressure',
                'pressureLow': 'bloodPressure',
                'step': 'steps'
            }
            current_physical_signs.add(sign_mapping.get(key, key))
    
    # 🚀 过滤规则: 只处理当前数据相关的规则
    filtered_rules = {}
    for rule_id, rule in alert_rules_dict.items():
        physical_sign = rule.get('physical_sign')
        if physical_sign in current_physical_signs:
            filtered_rules[rule_id] = rule
    
    print(f"📋 规则过滤: {len(alert_rules_dict)} -> {len(filtered_rules)} 条")
    
    # 后续处理使用 filtered_rules 替代 alert_rules_dict
    alert_rules_dict = filtered_rules
    
    # 现有代码继续...
```

### 2. 设备信息缓存 (性能提升)

**问题**: `get_device_user_org_info` 在每个规则匹配时都可能被调用

**解决**: 在函数开头一次性获取并缓存

```python
def generate_alerts(data, health_data_id):
    # 现有代码...
    
    # 🚀 新增: 提前获取设备信息并缓存
    device_sn = data.get('deviceSn')
    device_info_cache = None
    
    if device_sn:
        try:
            device_info_cache = get_device_user_org_info(device_sn)
            print(f"📱 设备信息已缓存: {device_sn}")
        except Exception as e:
            print(f"⚠️ 获取设备信息失败: {e}")
    
    # 遍历规则时使用缓存的设备信息
    for rule_id, rule in filtered_rules.items():
        # 现有规则匹配逻辑...
        
        # 当需要设备信息时，使用缓存
        if device_info_cache:
            user_id = device_info_cache.get('user_id')
            org_id = device_info_cache.get('org_id')
            user_name = device_info_cache.get('user_name', 'Unknown')
            # 使用缓存的信息而不是重复查询
```

### 3. 简单通知渠道处理

**问题**: 告警生成后没有自动通知机制

**解决**: 在现有告警保存后添加简单的通知处理

```python
def send_simple_notification(alert_info, device_info):
    """简单的通知发送函数"""
    try:
        user_name = device_info.get('user_name', 'Unknown')
        org_name = device_info.get('org_name', 'Unknown')
        
        # 构建通知消息
        message = f"【健康告警】{user_name}({org_name}) - {alert_info.get('alert_type', '')}: {alert_info.get('alert_desc', '')}"
        
        # 如果有微信配置，发送微信通知
        if hasattr(current_app, 'config') and current_app.config.get('WECHAT_ENABLED'):
            openid = device_info.get('openid')  # 需要在设备信息中包含openid
            if openid:
                send_wechat_alert(
                    alert_type=alert_info.get('alert_type'),
                    user_openid=openid,
                    user_name=user_name,
                    severity_level=alert_info.get('severity_level', 'medium')
                )
                print(f"📱 微信通知已发送: {user_name}")
        
        # 记录通知日志
        print(f"🔔 告警通知: {message}")
        
    except Exception as e:
        print(f"⚠️ 通知发送失败: {e}")

def generate_alerts(data, health_data_id):
    # 现有代码...处理规则匹配
    
    # 在保存告警后添加通知
    if alert_triggered:  # 当有告警触发时
        # 现有保存逻辑...
        
        # 🚀 新增: 发送通知
        try:
            send_simple_notification(alert_info, device_info_cache)
        except Exception as notify_error:
            print(f"通知发送异常: {notify_error}")
```

## 📝 完整集成代码

将以上三个改进集成到现有 `generate_alerts` 函数：

```python
def generate_alerts(data, health_data_id):
    start_time = time.time()
    try:
        print(f"🔍 generate_alerts started with data keys: {list(data.keys()) if data else 'None'}")
        
        # 现有代码: 获取告警规则...
        customer_id = data.get('customer_id') or data.get('customerId')
        alert_rules_dict = {}
        cache_hit = False
        
        # [保留现有的规则获取逻辑]
        # ...
        
        # 🚀 优化1: 规则按数据类型过滤
        current_physical_signs = set()
        sign_mapping = {
            'heartRate': 'heart_rate', 'bloodOxygen': 'blood_oxygen',
            'pressureHigh': 'bloodPressure', 'pressureLow': 'bloodPressure',
            'step': 'steps', 'calorie': 'calories', 'distance': 'distance',
            'temperature': 'temperature', 'stress': 'stress', 'sleep': 'sleep'
        }
        
        for key in data.keys():
            if key in sign_mapping:
                current_physical_signs.add(sign_mapping[key])
        
        # 过滤规则
        filtered_rules = {rid: rule for rid, rule in alert_rules_dict.items() 
                         if rule.get('physical_sign') in current_physical_signs}
        
        print(f"📋 规则过滤: {len(alert_rules_dict)} -> {len(filtered_rules)}")
        
        # 🚀 优化2: 设备信息预获取
        device_sn = data.get('deviceSn')
        device_info_cache = None
        if device_sn:
            try:
                device_info_cache = get_device_user_org_info(device_sn)
            except Exception as e:
                print(f"⚠️ 设备信息获取失败: {e}")
        
        # 现有规则匹配逻辑，使用 filtered_rules 和 device_info_cache
        abnormal_counts = {}
        alerts_generated = 0
        
        for rule_id, rule in filtered_rules.items():
            # [保留现有的规则匹配逻辑]
            # 使用 device_info_cache 替代重复查询
            
            # 当触发告警时
            if alert_condition_met:  # 现有的触发条件判断
                # [保留现有的告警创建和保存逻辑]
                
                # 🚀 优化3: 简单通知处理
                if device_info_cache:
                    try:
                        send_simple_notification(alert_info, device_info_cache)
                    except Exception as notify_error:
                        print(f"通知异常: {notify_error}")
                
                alerts_generated += 1
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        print(f"⏱️ generate_alerts 完成: 处理{len(filtered_rules)}条规则, 生成{alerts_generated}个告警, 耗时{processing_time}ms")
        
        return alerts_generated
        
    except Exception as e:
        print(f"❌ generate_alerts 异常: {e}")
        return 0
```

## 📊 预期效果

### 性能提升
- **规则过滤**: 减少 60-80% 不必要的规则处理
- **设备查询**: 消除重复查询，节省 50-70% 数据库调用
- **响应时间**: 整体处理时间减少 40-60%

### 功能增强  
- **自动通知**: 告警触发后自动发送通知
- **日志完善**: 更清晰的处理过程日志
- **错误处理**: 更好的异常处理机制

## 🔧 部署建议

### 实施步骤
1. **第一步**: 仅实施规则过滤优化 (风险最小)
2. **第二步**: 添加设备信息缓存 (性能提升明显)
3. **第三步**: 集成通知处理 (功能增强)

### 配置要求
```python
# config.py 中添加
WECHAT_ENABLED = True  # 是否启用微信通知
NOTIFICATION_ENABLED = True  # 是否启用通知功能
```

### 监控要点
- 规则过滤效率: 过滤前后规则数量
- 设备查询次数: 确认缓存生效
- 通知成功率: 监控通知发送情况

这个方案基于现有代码架构，改动最小，风险可控，可以立即实施并看到效果。

---
*简化版本: v1.0*  
*基于现有代码: ljwx-bigscreen/alert.py*