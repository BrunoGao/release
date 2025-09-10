# 基于实际代码的消息数据流集成方案

基于对ljwx-boot、ljwx-bigscreen、ljwx-phone、ljwx-watch四个平台的详细代码分析，提供一个贴合实际情况的消息数据流集成优化方案。

## 一、现有架构分析

### 1.1 数据库表结构（已存在）

**t_device_message (主消息表)**
```sql
CREATE TABLE t_device_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_sn VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    org_id VARCHAR(50),
    user_id VARCHAR(50), 
    customer_id BIGINT NOT NULL DEFAULT 0,
    message_type VARCHAR(50) NOT NULL,  -- job/task/announcement/notification/system_alert
    sender_type VARCHAR(50) NOT NULL,   -- system/admin/user
    receiver_type VARCHAR(50) NOT NULL, -- device/user/department
    message_status VARCHAR(50) DEFAULT 'pending', -- pending/delivered/acknowledged
    responded_number INTEGER DEFAULT 0,
    sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    received_time DATETIME NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**t_device_message_detail (消息详情表)**
```sql 
CREATE TABLE t_device_message_detail (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id BIGINT NOT NULL,
    device_sn VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    sender_type VARCHAR(50) NOT NULL,
    receiver_type VARCHAR(50) NOT NULL,
    message_status VARCHAR(50) DEFAULT 'pending',
    sent_time DATETIME,
    received_time DATETIME,
    customer_id BIGINT NOT NULL,
    org_id BIGINT,
    -- 新增字段用于统计和跟踪
    delivery_status VARCHAR(50), -- pending/delivered/acknowledged/failed/expired
    channel VARCHAR(50),         -- message/push/wechat/watch
    response_time INTEGER,       -- 响应时间(秒)
    acknowledge_time DATETIME,   -- 确认时间
    target_type VARCHAR(50),     -- user/device/department/organization
    target_id VARCHAR(255)       -- 目标ID
);
```

### 1.2 现有消息流程

```
ljwx-admin/ljwx-bigscreen → t_device_message → ljwx-phone → ljwx-watch
     ↓ (手动发送)              ↓ (API查询)     ↓ (蓝牙)     ↓ (用户确认)
  告警规则触发              定时获取消息    转发给手表    反向确认回传
```

## 二、各平台现状分析

### 2.1 ljwx-boot (Java后端)

**现有接口**:
- `TDeviceMessageController` - CRUD操作
- `DeviceMessageServiceImpl` - 兼容性服务层
- 支持消息的发送、接收、保存

**优化需求**:
- 增强消息生命周期管理
- 添加实时状态同步
- 支持批量操作和统计

### 2.2 ljwx-bigscreen (Python大屏)

**现有功能**:
- `DeviceMessage`、`DeviceMessageDetail` SQLAlchemy模型
- `/DeviceMessage/send`、`/receive` API接口
- 告警自动转消息机制 (`system_event_alert.py`)
- 消息统计和展示功能

**优化需求**:
- 增强消息跟踪界面
- 实时状态更新
- 完善统计报表

### 2.3 ljwx-phone (Flutter移动端)

**现有功能**:
- `Message`、`MessageInfo` Dart模型
- `ApiService.getDeviceMessages()` - 获取消息
- `markMessageAsRead()` - 标记已读
- 消息列表和详情UI
- 蓝牙消息转发给手表

**优化需求**:
- 实时消息推送
- 批量操作优化
- 离线消息同步

### 2.4 ljwx-watch (HarmonyOS手表)

**现有功能**:
- HTTP和蓝牙双模式消息接收
- `fetchMessageFromServer()` - HTTP拉取
- 蓝牙GATT命令处理
- 系统通知显示和用户确认

**优化需求**:
- 消息确认回传优化
- 显示效果增强
- 电池优化

## 三、集成优化方案

### 3.1 消息统一模型扩展

在现有数据库基础上增加字段，支持完整的消息生命周期：

```sql
-- 扩展 t_device_message 表
ALTER TABLE t_device_message ADD COLUMN title VARCHAR(500);
ALTER TABLE t_device_message ADD COLUMN content TEXT;
ALTER TABLE t_device_message ADD COLUMN priority INTEGER DEFAULT 3;
ALTER TABLE t_device_message ADD COLUMN urgency VARCHAR(20) DEFAULT 'medium';
ALTER TABLE t_device_message ADD COLUMN channels JSON; -- ["message","push","wechat","watch"]
ALTER TABLE t_device_message ADD COLUMN require_ack BOOLEAN DEFAULT false;
ALTER TABLE t_device_message ADD COLUMN expiry_time DATETIME;
ALTER TABLE t_device_message ADD COLUMN metadata JSON;

-- 扩展 t_device_message_detail 表  
ALTER TABLE t_device_message_detail ADD COLUMN distribution_id VARCHAR(255);
ALTER TABLE t_device_message_detail ADD COLUMN target_type VARCHAR(50);
ALTER TABLE t_device_message_detail ADD COLUMN target_id VARCHAR(255);
ALTER TABLE t_device_message_detail ADD COLUMN delivery_status VARCHAR(50);
ALTER TABLE t_device_message_detail ADD COLUMN channel VARCHAR(50);
ALTER TABLE t_device_message_detail ADD COLUMN response_time INTEGER;
ALTER TABLE t_device_message_detail ADD COLUMN acknowledge_time DATETIME;
ALTER TABLE t_device_message_detail ADD COLUMN delivery_details JSON;
```

### 3.2 ljwx-boot 服务层增强

基于现有的 `TDeviceMessageServiceImpl` 扩展功能：

```java
@Service
public class EnhancedMessageService extends TDeviceMessageServiceImpl {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    /**
     * 统一消息发布接口
     */
    @Transactional
    public Long publishMessage(UnifiedMessageRequest request) {
        // 1. 保存主消息
        TDeviceMessage message = buildDeviceMessage(request);
        save(message);
        
        // 2. 创建分发记录
        List<TDeviceMessageDetail> details = createDistributionDetails(message, request);
        messageDetailService.saveBatch(details);
        
        // 3. 发布到Redis
        publishToRedis(message, details);
        
        // 4. 记录生命周期事件
        recordLifecycleEvent(message.getId(), "created", getCurrentUser());
        
        return message.getId();
    }
    
    /**
     * 消息状态批量更新
     */
    public void updateMessageStatus(Long messageId, String status, List<String> targetIds) {
        // 更新主消息状态
        TDeviceMessage message = getById(messageId);
        message.setMessageStatus(status);
        updateById(message);
        
        // 更新详情状态
        LambdaUpdateWrapper<TDeviceMessageDetail> wrapper = new LambdaUpdateWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getMessageId, messageId)
               .in(TDeviceMessageDetail::getTargetId, targetIds)
               .set(TDeviceMessageDetail::getDeliveryStatus, status)
               .set(TDeviceMessageDetail::getAcknowledgeTime, LocalDateTime.now());
        
        messageDetailService.update(wrapper);
        
        // 发布状态更新事件
        publishStatusUpdate(messageId, status);
    }
    
    private void publishToRedis(TDeviceMessage message, List<TDeviceMessageDetail> details) {
        for (TDeviceMessageDetail detail : details) {
            String channel = "message:" + detail.getChannel();
            Map<String, Object> payload = buildRedisPayload(message, detail);
            redisTemplate.convertAndSend(channel, payload);
        }
    }
}
```

### 3.3 ljwx-phone 实时消息集成

在现有Flutter代码基础上增加Redis订阅：

```dart
// lib/services/enhanced_message_service.dart
class EnhancedMessageService extends ApiService {
  StreamSubscription<String>? _redisSubscription;
  final StreamController<Message> _messageStreamController = StreamController<Message>.broadcast();
  
  Stream<Message> get messageStream => _messageStreamController.stream;
  
  @override
  void initState() {
    super.initState();
    _subscribeToRedisMessages();
    _startPeriodicSync(); // 保持现有的定时同步作为备用
  }
  
  void _subscribeToRedisMessages() {
    // 订阅Redis消息通道
    String channel = 'message:${deviceSn}';
    _redisSubscription = RedisClient.subscribe(channel).listen((data) {
      try {
        Map<String, dynamic> messageData = jsonDecode(data);
        Message message = Message.fromJson(messageData);
        
        // 更新本地存储
        _updateLocalMessage(message);
        
        // 发布给UI层
        _messageStreamController.add(message);
        
        // 转发给手表（如果连接）
        if (BluetoothService().isConnected) {
          BluetoothService().forwardMessageToWatch(messageData);
        }
        
      } catch (e) {
        print('解析Redis消息失败: $e');
      }
    });
  }
  
  @override
  Future<bool> markMessageAsRead(String deviceSn, {
    DateTime? receivedTime,
    String? messageId,
    Map<String, dynamic>? originalMessage
  }) async {
    
    // 调用现有API
    final success = await super.markMessageAsRead(deviceSn, 
        receivedTime: receivedTime, messageId: messageId, originalMessage: originalMessage);
    
    if (success) {
      // 发布确认事件到Redis
      Map<String, dynamic> ackEvent = {
        'type': 'message_acknowledged',
        'messageId': messageId,
        'deviceSn': deviceSn,
        'acknowledgeTime': receivedTime?.toIso8601String() ?? DateTime.now().toIso8601String(),
        'source': 'phone'
      };
      
      RedisClient.publish('message:acknowledgments', jsonEncode(ackEvent));
    }
    
    return success;
  }
}
```

### 3.4 ljwx-bigscreen 增强消息跟踪

基于现有的消息处理代码增加实时跟踪：

```python
# bigScreen/enhanced_message_tracking.py
class EnhancedMessageTracker:
    
    @staticmethod
    def create_message_with_tracking(message_data):
        """创建消息并启用跟踪"""
        try:
            # 使用现有的DeviceMessage模型
            message = DeviceMessage(
                device_sn=message_data.get('device_sn'),
                message=message_data.get('content'),
                message_type=message_data.get('message_type', 'notification'),
                sender_type=message_data.get('sender_type', 'admin'),
                receiver_type=message_data.get('receiver_type', 'device'),
                org_id=message_data.get('org_id'),
                user_id=message_data.get('user_id'),
                customer_id=message_data.get('customer_id', 0),
                # 新增字段
                title=message_data.get('title'),
                priority=message_data.get('priority', 3),
                urgency=message_data.get('urgency', 'medium'),
                require_ack=message_data.get('require_ack', False),
                channels=json.dumps(message_data.get('channels', ['message'])),
                metadata=json.dumps(message_data.get('metadata', {}))
            )
            
            db.session.add(message)
            db.session.commit()
            
            # 创建分发记录
            targets = message_data.get('targets', [])
            for target in targets:
                detail = DeviceMessageDetail(
                    message_id=message.id,
                    device_sn=target.get('device_sn'),
                    message=message.message,
                    message_type=message.message_type,
                    sender_type=message.sender_type,
                    receiver_type=message.receiver_type,
                    customer_id=message.customer_id,
                    org_id=message.org_id,
                    # 新增字段
                    target_type=target.get('target_type', 'device'),
                    target_id=target.get('target_id'),
                    delivery_status='pending',
                    channel=target.get('channel', 'message')
                )
                db.session.add(detail)
            
            db.session.commit()
            
            # 发布到Redis
            redis_client.publish(f'message:created', json.dumps({
                'messageId': message.id,
                'targets': [detail.device_sn for detail in message.details]
            }))
            
            return message
            
        except Exception as e:
            db.session.rollback()
            print(f"创建消息失败: {e}")
            return None
    
    @staticmethod
    def get_message_lifecycle(message_id):
        """获取消息生命周期报告"""
        message = DeviceMessage.query.get(message_id)
        if not message:
            return None
            
        details = DeviceMessageDetail.query.filter_by(message_id=message_id).all()
        
        # 计算统计数据
        total_targets = len(details)
        delivered = sum(1 for d in details if d.delivery_status in ['delivered', 'acknowledged'])
        acknowledged = sum(1 for d in details if d.delivery_status == 'acknowledged')
        pending = sum(1 for d in details if d.delivery_status == 'pending')
        failed = sum(1 for d in details if d.delivery_status == 'failed')
        
        # 计算响应时间
        response_times = [d.response_time for d in details if d.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'messageId': message_id,
            'messageType': message.message_type,
            'createTime': message.create_time.isoformat(),
            'sentTime': message.sent_time.isoformat() if message.sent_time else None,
            'progress': {
                'totalTargets': total_targets,
                'delivered': delivered,
                'acknowledged': acknowledged,
                'pending': pending,
                'failed': failed,
                'completionRate': (acknowledged / total_targets * 100) if total_targets > 0 else 0,
                'avgResponseTime': avg_response_time
            },
            'details': [
                {
                    'targetId': d.target_id,
                    'deviceSn': d.device_sn,
                    'deliveryStatus': d.delivery_status,
                    'channel': d.channel,
                    'responseTime': d.response_time,
                    'acknowledgeTime': d.acknowledge_time.isoformat() if d.acknowledge_time else None
                }
                for d in details
            ]
        }

# bigScreen.py 新增API端点
@app.route('/api/message/lifecycle/<int:message_id>', methods=['GET'])
def get_message_lifecycle(message_id):
    """获取消息生命周期"""
    lifecycle_data = EnhancedMessageTracker.get_message_lifecycle(message_id)
    if lifecycle_data:
        return jsonify({'success': True, 'data': lifecycle_data})
    else:
        return jsonify({'success': False, 'error': '消息不存在'}), 404

@app.route('/api/message/stats/<int:org_id>', methods=['GET'])
def get_organization_message_stats(org_id):
    """获取组织消息统计"""
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    query = DeviceMessage.query.filter_by(org_id=str(org_id))
    
    if start_date:
        query = query.filter(DeviceMessage.create_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(DeviceMessage.create_time <= datetime.fromisoformat(end_date))
    
    messages = query.all()
    
    # 生成统计数据
    stats = {
        'totalMessages': len(messages),
        'messageTypes': {},
        'dailyTrend': {},
        'avgCompletionRate': 0,
        'avgResponseTime': 0
    }
    
    # ... 统计计算逻辑
    
    return jsonify({'success': True, 'data': stats})
```

### 3.5 ljwx-watch 消息处理优化

基于现有的HTTP和蓝牙双模式，增加确认反馈优化：

```java
// HttpService.java 消息确认增强
public void enhancedMessageConfirmation(JSONObject message) {
    try {
        String messageId = message.getString("message_id");
        
        // 构建增强的确认响应
        JSONObject enhancedResponse = new JSONObject();
        enhancedResponse.put("type", "message_acknowledgment");
        enhancedResponse.put("messageId", messageId);
        enhancedResponse.put("deviceSn", dataManager.getDeviceSn());
        enhancedResponse.put("acknowledgeTime", getCurrentTimestamp());
        enhancedResponse.put("responseTime", calculateResponseTime(message));
        enhancedResponse.put("channel", "http");
        enhancedResponse.put("deviceInfo", getDeviceInfo());
        enhancedResponse.put("userAction", "acknowledged"); // 用户主动确认
        
        // 复制原消息字段
        copyOriginalMessageFields(enhancedResponse, message);
        
        // 发送确认
        String confirmUrl = dataManager.getFetchMessageUrl() + "/acknowledge";
        JSONObject response = postDataToServer(confirmUrl, enhancedResponse);
        
        if (response != null && response.getBoolean("success")) {
            Log.i(TAG, "✅ 消息确认发送成功: " + messageId);
            
            // 本地标记为已确认
            markMessageAsAcknowledged(messageId);
            
        } else {
            Log.w(TAG, "⚠️ 消息确认发送失败: " + messageId);
            // 缓存确认，稍后重试
            cacheAcknowledgment(enhancedResponse);
        }
        
    } catch (Exception e) {
        Log.e(TAG, "❌ 消息确认处理异常: " + e.getMessage());
    }
}

private int calculateResponseTime(JSONObject message) {
    try {
        String sentTimeStr = message.getString("sent_time");
        long sentTime = parseTimestamp(sentTimeStr);
        long currentTime = System.currentTimeMillis();
        return (int) ((currentTime - sentTime) / 1000); // 返回秒数
    } catch (Exception e) {
        return -1; // 无法计算响应时间
    }
}

private JSONObject getDeviceInfo() {
    JSONObject deviceInfo = new JSONObject();
    try {
        deviceInfo.put("watchModel", "HarmonyOS Watch");
        deviceInfo.put("osVersion", "4.0");
        deviceInfo.put("appVersion", getAppVersion());
        deviceInfo.put("batteryLevel", getBatteryLevel());
        deviceInfo.put("signalStrength", getSignalStrength());
    } catch (Exception e) {
        Log.w(TAG, "获取设备信息失败: " + e.getMessage());
    }
    return deviceInfo;
}
```

## 四、实施路径

### 4.1 阶段一：数据库扩展（1周）
1. 执行SQL脚本扩展现有表结构
2. 更新ljwx-boot实体类
3. 更新ljwx-bigscreen SQLAlchemy模型
4. 数据迁移和兼容性测试

### 4.2 阶段二：后端服务增强（2周）
1. ljwx-boot增强消息服务
2. ljwx-bigscreen增强跟踪功能
3. Redis集成和实时通信
4. API接口联调测试

### 4.3 阶段三：移动端实时化（1周）
1. ljwx-phone集成Redis订阅
2. 增强消息确认机制
3. 蓝牙通信优化
4. 离线同步完善

### 4.4 阶段四：手表端优化（1周）
1. ljwx-watch确认反馈增强
2. 消息显示优化
3. 电池性能优化
4. 端到端测试

### 4.5 阶段五：整体联调（1周）
1. 四端数据流测试
2. 性能压力测试
3. 用户体验优化
4. 文档和培训

## 五、预期效果

1. **完整数据流打通**: 平台→手机→手表→确认回传的完整链路
2. **实时状态同步**: 基于Redis的实时消息推送和状态更新  
3. **全面生命周期跟踪**: 从消息创建到确认完成的全流程监控
4. **增强统计分析**: 组织级、部门级、个人级的多维度分析
5. **向后兼容**: 保持现有API和数据结构的兼容性

此方案基于现有代码架构，最大程度复用已有功能，通过渐进式改进实现完整的消息数据流集成。