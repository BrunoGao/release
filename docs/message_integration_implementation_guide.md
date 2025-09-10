# 消息数据流集成实施指南

基于对现有代码的详细分析，本文档提供具体的实施步骤和代码改动建议。

## 一、实施概览

### 目标
- 完整打通 ljwx-admin/ljwx-bigscreen → ljwx-boot → ljwx-phone → ljwx-watch 的消息数据流
- 实现实时消息推送和状态跟踪
- 支持消息生命周期管理和统计分析
- 保持现有API和数据结构的向后兼容

### 技术栈
- **ljwx-boot**: Java Spring Boot + MyBatis Plus + Redis
- **ljwx-bigscreen**: Python Flask + SQLAlchemy + Redis  
- **ljwx-phone**: Flutter + Dart + Redis Client
- **ljwx-watch**: HarmonyOS 4.0 + Java

## 二、数据库扩展（阶段一）

### 2.1 SQL脚本

```sql
-- 扩展 t_device_message 表
ALTER TABLE t_device_message 
ADD COLUMN title VARCHAR(500) COMMENT '消息标题',
ADD COLUMN priority INTEGER DEFAULT 3 COMMENT '优先级1-5',
ADD COLUMN urgency VARCHAR(20) DEFAULT 'medium' COMMENT '紧急程度',
ADD COLUMN channels JSON COMMENT '分发渠道',
ADD COLUMN require_ack BOOLEAN DEFAULT false COMMENT '需要确认',
ADD COLUMN expiry_time DATETIME COMMENT '过期时间',
ADD COLUMN metadata JSON COMMENT '元数据';

-- 扩展 t_device_message_detail 表
ALTER TABLE t_device_message_detail
ADD COLUMN distribution_id VARCHAR(255) COMMENT '分发ID',
ADD COLUMN target_type VARCHAR(50) COMMENT '目标类型',
ADD COLUMN target_id VARCHAR(255) COMMENT '目标ID', 
ADD COLUMN delivery_status VARCHAR(50) COMMENT '分发状态',
ADD COLUMN channel VARCHAR(50) COMMENT '分发渠道',
ADD COLUMN response_time INTEGER COMMENT '响应时间秒',
ADD COLUMN acknowledge_time DATETIME COMMENT '确认时间',
ADD COLUMN delivery_details JSON COMMENT '分发详情';

-- 创建索引优化查询
CREATE INDEX idx_message_device_sn ON t_device_message(device_sn);
CREATE INDEX idx_message_org_id ON t_device_message(org_id);
CREATE INDEX idx_message_type_status ON t_device_message(message_type, message_status);
CREATE INDEX idx_detail_message_id ON t_device_message_detail(message_id);
CREATE INDEX idx_detail_device_sn ON t_device_message_detail(device_sn);
CREATE INDEX idx_detail_delivery_status ON t_device_message_detail(delivery_status);
```

### 2.2 ljwx-boot实体类更新

```java
// TDeviceMessage.java 新增字段
@TableName("t_device_message")
public class TDeviceMessage extends BaseEntity {
    // 现有字段...
    
    private String title;
    private Integer priority;
    private String urgency;
    private String channels;  // JSON字符串
    private Boolean requireAck;
    private LocalDateTime expiryTime;
    private String metadata;  // JSON字符串
}

// TDeviceMessageDetail.java 新增字段  
@TableName("t_device_message_detail")
public class TDeviceMessageDetail extends BaseEntity {
    // 现有字段...
    
    private String distributionId;
    private String targetType;
    private String targetId;
    private String deliveryStatus;
    private String channel;
    private Integer responseTime;
    private LocalDateTime acknowledgeTime;
    private String deliveryDetails;  // JSON字符串
}
```

### 2.3 ljwx-bigscreen模型更新

```python
# models.py 扩展
class DeviceMessage(db.Model):
    __tablename__ = 't_device_message'
    # 现有字段...
    
    title = db.Column(db.String(500), nullable=True)
    priority = db.Column(db.Integer, default=3)
    urgency = db.Column(db.String(20), default='medium')
    channels = db.Column(db.JSON, nullable=True)
    require_ack = db.Column(db.Boolean, default=False)
    expiry_time = db.Column(db.DateTime, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)

class DeviceMessageDetail(db.Model):
    __tablename__ = 't_device_message_detail'
    # 现有字段...
    
    distribution_id = db.Column(db.String(255), nullable=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.String(255), nullable=True)
    delivery_status = db.Column(db.String(50), nullable=True)
    channel = db.Column(db.String(50), nullable=True)
    response_time = db.Column(db.Integer, nullable=True)
    acknowledge_time = db.Column(db.DateTime, nullable=True)
    delivery_details = db.Column(db.JSON, nullable=True)
```

## 三、后端服务增强（阶段二）

### 3.1 ljwx-boot Redis配置

```java
// RedisConfig.java
@Configuration
public class RedisConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        template.setDefaultSerializer(new GenericJackson2JsonRedisSerializer());
        return template;
    }
    
    @Bean
    public RedisMessageListenerContainer container(RedisConnectionFactory factory) {
        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
        container.setConnectionFactory(factory);
        return container;
    }
}
```

### 3.2 ljwx-boot增强消息服务

```java
// EnhancedMessageService.java
@Service
@Slf4j
public class EnhancedMessageService {
    
    @Autowired
    private ITDeviceMessageService messageService;
    
    @Autowired
    private ITDeviceMessageDetailService detailService;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    /**
     * 统一消息发布接口
     */
    @Transactional
    public Long publishMessage(MessagePublishRequest request) {
        try {
            // 1. 创建主消息
            TDeviceMessage message = buildMainMessage(request);
            messageService.save(message);
            
            // 2. 创建分发详情
            List<TDeviceMessageDetail> details = buildMessageDetails(message, request.getTargets());
            detailService.saveBatch(details);
            
            // 3. 发布到Redis
            publishToRedis(message, details);
            
            log.info("✅ 消息发布成功: messageId={}, 目标数量={}", message.getId(), details.size());
            return message.getId();
            
        } catch (Exception e) {
            log.error("❌ 消息发布失败: {}", e.getMessage(), e);
            throw new RuntimeException("消息发布失败", e);
        }
    }
    
    /**
     * 批量更新消息状态
     */
    public void updateMessageStatus(Long messageId, String status, List<String> deviceSns) {
        // 更新详情状态
        LambdaUpdateWrapper<TDeviceMessageDetail> wrapper = new LambdaUpdateWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getMessageId, messageId)
               .in(TDeviceMessageDetail::getDeviceSn, deviceSns)
               .set(TDeviceMessageDetail::getDeliveryStatus, status)
               .set(TDeviceMessageDetail::getAcknowledgeTime, LocalDateTime.now());
        
        detailService.update(wrapper);
        
        // 检查是否需要更新主消息状态
        updateMainMessageStatus(messageId);
        
        // 发布状态更新事件
        Map<String, Object> statusEvent = new HashMap<>();
        statusEvent.put("messageId", messageId);
        statusEvent.put("status", status);
        statusEvent.put("deviceSns", deviceSns);
        statusEvent.put("timestamp", System.currentTimeMillis());
        
        redisTemplate.convertAndSend("message:status:updates", statusEvent);
    }
    
    private void publishToRedis(TDeviceMessage message, List<TDeviceMessageDetail> details) {
        for (TDeviceMessageDetail detail : details) {
            Map<String, Object> payload = new HashMap<>();
            payload.put("messageId", message.getId());
            payload.put("deviceSn", detail.getDeviceSn());
            payload.put("messageType", message.getMessageType());
            payload.put("title", message.getTitle());
            payload.put("content", message.getMessage());
            payload.put("priority", message.getPriority());
            payload.put("urgency", message.getUrgency());
            payload.put("sentTime", message.getSentTime());
            payload.put("requireAck", message.getRequireAck());
            payload.put("channel", detail.getChannel());
            
            String channel = "message:device:" + detail.getDeviceSn();
            redisTemplate.convertAndSend(channel, payload);
        }
    }
}
```

### 3.3 ljwx-bigscreen增强跟踪

```python
# enhanced_message_service.py
class EnhancedMessageService:
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def create_tracked_message(self, message_data):
        """创建带跟踪的消息"""
        try:
            # 创建主消息
            message = DeviceMessage(
                device_sn=message_data.get('device_sn'),
                message=message_data.get('content'),
                title=message_data.get('title'),
                message_type=message_data.get('message_type', 'notification'),
                sender_type=message_data.get('sender_type', 'admin'),
                receiver_type=message_data.get('receiver_type', 'device'),
                priority=message_data.get('priority', 3),
                urgency=message_data.get('urgency', 'medium'),
                channels=json.dumps(message_data.get('channels', ['message'])),
                require_ack=message_data.get('require_ack', False),
                org_id=message_data.get('org_id'),
                user_id=message_data.get('user_id'),
                customer_id=message_data.get('customer_id', 0),
                metadata=json.dumps(message_data.get('metadata', {}))
            )
            
            db.session.add(message)
            db.session.flush()  # 获取ID
            
            # 创建分发记录
            targets = message_data.get('targets', [])
            details = []
            
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
                    distribution_id=f"dist_{message.id}_{target.get('device_sn')}",
                    target_type=target.get('target_type', 'device'),
                    target_id=target.get('target_id', target.get('device_sn')),
                    delivery_status='pending',
                    channel=target.get('channel', 'message')
                )
                details.append(detail)
                db.session.add(detail)
            
            db.session.commit()
            
            # 发布到Redis
            self._publish_message_created(message, details)
            
            return message
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建跟踪消息失败: {e}")
            return None
    
    def _publish_message_created(self, message, details):
        """发布消息创建事件"""
        for detail in details:
            payload = {
                'messageId': message.id,
                'deviceSn': detail.device_sn,
                'messageType': message.message_type,
                'title': message.title,
                'content': message.message,
                'priority': message.priority,
                'urgency': message.urgency,
                'sentTime': message.sent_time.isoformat() if message.sent_time else None,
                'requireAck': message.require_ack,
                'channel': detail.channel
            }
            
            channel = f'message:device:{detail.device_sn}'
            self.redis_client.publish(channel, json.dumps(payload))
    
    def get_message_statistics(self, org_id, start_date=None, end_date=None):
        """获取消息统计"""
        query = DeviceMessage.query.filter_by(org_id=str(org_id))
        
        if start_date:
            query = query.filter(DeviceMessage.create_time >= start_date)
        if end_date:
            query = query.filter(DeviceMessage.create_time <= end_date)
        
        messages = query.all()
        
        # 统计计算
        stats = {
            'totalMessages': len(messages),
            'messageTypes': {},
            'completionStats': {
                'totalTargets': 0,
                'delivered': 0,
                'acknowledged': 0,
                'pending': 0,
                'failed': 0
            }
        }
        
        # 消息类型统计
        for message in messages:
            msg_type = message.message_type
            stats['messageTypes'][msg_type] = stats['messageTypes'].get(msg_type, 0) + 1
            
            # 获取详情统计
            details = DeviceMessageDetail.query.filter_by(message_id=message.id).all()
            stats['completionStats']['totalTargets'] += len(details)
            
            for detail in details:
                status = detail.delivery_status or 'pending'
                if status in stats['completionStats']:
                    stats['completionStats'][status] += 1
        
        # 计算完成率
        total = stats['completionStats']['totalTargets']
        if total > 0:
            acknowledged = stats['completionStats']['acknowledged']
            stats['completionStats']['completionRate'] = round(acknowledged / total * 100, 2)
        else:
            stats['completionStats']['completionRate'] = 0.0
        
        return stats

# 新增API端点
@app.route('/api/enhanced/message/create', methods=['POST'])
def create_enhanced_message():
    """创建增强消息"""
    data = request.get_json()
    
    service = EnhancedMessageService()
    message = service.create_tracked_message(data)
    
    if message:
        return jsonify({
            'success': True,
            'messageId': message.id,
            'message': '消息创建成功'
        })
    else:
        return jsonify({
            'success': False,
            'error': '消息创建失败'
        }), 500

@app.route('/api/enhanced/message/stats/<int:org_id>', methods=['GET'])
def get_enhanced_message_stats(org_id):
    """获取增强消息统计"""
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    service = EnhancedMessageService()
    stats = service.get_message_statistics(org_id, start_date, end_date)
    
    return jsonify({
        'success': True,
        'data': stats
    })
```

## 四、移动端实时化（阶段三）

### 4.1 ljwx-phone Redis集成

```dart
// lib/services/redis_service.dart
import 'dart:convert';
import 'dart:async';

class RedisService {
  static RedisService? _instance;
  StreamController<Map<String, dynamic>>? _messageController;
  
  static RedisService get instance {
    _instance ??= RedisService._internal();
    return _instance!;
  }
  
  RedisService._internal();
  
  Stream<Map<String, dynamic>> get messageStream {
    _messageController ??= StreamController<Map<String, dynamic>>.broadcast();
    return _messageController!.stream;
  }
  
  Future<void> subscribeToMessages(String deviceSn) async {
    try {
      // 订阅设备消息通道
      String channel = 'message:device:$deviceSn';
      
      // 这里需要集成实际的Redis客户端
      // 示例使用WebSocket或HTTP长连接模拟
      await _connectToRedis(channel);
      
    } catch (e) {
      print('Redis订阅失败: $e');
    }
  }
  
  Future<void> _connectToRedis(String channel) async {
    // 实际实现中可以使用redis_client包或者WebSocket
    // 这里提供框架结构
  }
  
  void publishAcknowledgment(Map<String, dynamic> ackData) {
    try {
      String channel = 'message:acknowledgments';
      String payload = jsonEncode(ackData);
      
      // 发布确认事件
      _publishToRedis(channel, payload);
      
    } catch (e) {
      print('发布确认失败: $e');
    }
  }
  
  void _publishToRedis(String channel, String payload) {
    // 实际Redis发布实现
  }
}
```

```dart
// lib/services/enhanced_message_service.dart
class EnhancedMessageService extends ApiService {
  StreamSubscription<Map<String, dynamic>>? _redisSubscription;
  final StreamController<Message> _localMessageController = StreamController<Message>.broadcast();
  
  Stream<Message> get localMessageStream => _localMessageController.stream;
  
  @override
  void initState() {
    super.initState();
    _initializeRedisSubscription();
    _startPeriodicSync(); // 保持现有定时同步作为备用
  }
  
  void _initializeRedisSubscription() async {
    try {
      String deviceSn = AppConfig.instance.deviceSn;
      await RedisService.instance.subscribeToMessages(deviceSn);
      
      _redisSubscription = RedisService.instance.messageStream.listen((data) {
        _handleRedisMessage(data);
      });
      
    } catch (e) {
      print('初始化Redis订阅失败: $e');
    }
  }
  
  void _handleRedisMessage(Map<String, dynamic> data) {
    try {
      // 转换为Message对象
      Message message = Message(
        id: data['messageId'].toString(),
        title: data['title'] ?? '',
        content: data['content'] ?? '',
        createTime: data['sentTime'] ?? DateTime.now().toIso8601String(),
        department: '', // 从设备信息获取
        messageStatus: '1', // 未读状态
        messageType: data['messageType'] ?? 'notification',
      );
      
      // 保存到本地
      _saveMessageLocally(message);
      
      // 通知UI更新
      _localMessageController.add(message);
      
      // 转发给手表（如果蓝牙连接）
      if (BluetoothService().isConnected) {
        BluetoothService().forwardMessageToWatch(data);
      }
      
    } catch (e) {
      print('处理Redis消息失败: $e');
    }
  }
  
  @override
  Future<bool> markMessageAsRead(String deviceSn, {
    DateTime? receivedTime,
    String? messageId,
    Map<String, dynamic>? originalMessage
  }) async {
    
    // 调用现有API
    final success = await super.markMessageAsRead(
      deviceSn,
      receivedTime: receivedTime,
      messageId: messageId,
      originalMessage: originalMessage
    );
    
    if (success && messageId != null) {
      // 发布确认事件到Redis
      RedisService.instance.publishAcknowledgment({
        'type': 'message_acknowledged',
        'messageId': messageId,
        'deviceSn': deviceSn,
        'acknowledgeTime': (receivedTime ?? DateTime.now()).toIso8601String(),
        'responseTime': _calculateResponseTime(originalMessage),
        'source': 'phone',
        'platform': 'ljwx-phone'
      });
    }
    
    return success;
  }
  
  int _calculateResponseTime(Map<String, dynamic>? originalMessage) {
    if (originalMessage == null || originalMessage['sentTime'] == null) {
      return 0;
    }
    
    try {
      DateTime sentTime = DateTime.parse(originalMessage['sentTime']);
      DateTime now = DateTime.now();
      return now.difference(sentTime).inSeconds;
    } catch (e) {
      return 0;
    }
  }
  
  void _saveMessageLocally(Message message) {
    // 保存到本地数据库或缓存
    // 可以使用sqflite或hive
  }
}
```

### 4.2 ljwx-phone UI更新

```dart
// lib/screens/enhanced_messages_screen.dart
class EnhancedMessagesScreen extends StatefulWidget {
  @override
  _EnhancedMessagesScreenState createState() => _EnhancedMessagesScreenState();
}

class _EnhancedMessagesScreenState extends State<EnhancedMessagesScreen> {
  late EnhancedMessageService _messageService;
  StreamSubscription<Message>? _messageSubscription;
  
  @override
  void initState() {
    super.initState();
    _messageService = EnhancedMessageService();
    _messageService.initState();
    
    // 监听实时消息
    _messageSubscription = _messageService.localMessageStream.listen((message) {
      setState(() {
        // 更新UI
      });
      
      // 显示通知
      _showMessageNotification(message);
    });
  }
  
  void _showMessageNotification(Message message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('新消息: ${message.title}'),
        action: SnackBarAction(
          label: '查看',
          onPressed: () => _openMessageDetail(message),
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    _messageSubscription?.cancel();
    super.dispose();
  }
}
```

## 五、手表端优化（阶段四）

### 5.1 ljwx-watch增强确认机制

```java
// HttpService.java 增强确认
public void sendEnhancedMessageAcknowledgment(JSONObject originalMessage) {
    try {
        String messageId = originalMessage.getString("message_id");
        
        // 构建增强确认数据
        JSONObject ackData = new JSONObject();
        ackData.put("type", "message_acknowledgment");
        ackData.put("messageId", messageId);
        ackData.put("deviceSn", dataManager.getDeviceSn());
        ackData.put("acknowledgeTime", getCurrentISOTimestamp());
        ackData.put("responseTime", calculateResponseTime(originalMessage));
        ackData.put("channel", "http");
        ackData.put("source", "watch");
        ackData.put("platform", "ljwx-watch");
        
        // 设备信息
        JSONObject deviceInfo = new JSONObject();
        deviceInfo.put("watchModel", "HarmonyOS Watch");
        deviceInfo.put("osVersion", "4.0");
        deviceInfo.put("appVersion", getAppVersion());
        deviceInfo.put("batteryLevel", getBatteryLevel());
        ackData.put("deviceInfo", deviceInfo);
        
        // 用户行为信息
        ackData.put("userAction", "acknowledged");
        ackData.put("interactionMethod", "touch");
        
        // 复制原消息关键字段
        copyMessageFields(ackData, originalMessage);
        
        // 发送确认
        String ackUrl = dataManager.getFetchMessageUrl() + "/acknowledge";
        JSONObject response = postDataToServer(ackUrl, ackData);
        
        if (response != null && response.getBoolean("success")) {
            Log.i(TAG, "✅ 增强消息确认发送成功: " + messageId);
            showConfirmationFeedback(); // 显示确认反馈
        } else {
            Log.w(TAG, "⚠️ 增强消息确认发送失败，缓存重试: " + messageId);
            cacheAcknowledgmentForRetry(ackData);
        }
        
    } catch (Exception e) {
        Log.e(TAG, "❌ 增强消息确认异常: " + e.getMessage());
    }
}

private int calculateResponseTime(JSONObject originalMessage) {
    try {
        String sentTimeStr = originalMessage.getString("sent_time");
        // 解析发送时间并计算差值
        long sentTime = parseDateToTimestamp(sentTimeStr);
        long currentTime = System.currentTimeMillis();
        return (int) ((currentTime - sentTime) / 1000);
    } catch (Exception e) {
        Log.w(TAG, "无法计算响应时间: " + e.getMessage());
        return -1;
    }
}

private void showConfirmationFeedback() {
    // 显示确认成功的视觉反馈
    vibrate(100); // 震动反馈
    showToast("消息已确认");
}

private void copyMessageFields(JSONObject ackData, JSONObject originalMessage) {
    String[] fieldsToCoopy = {
        "message", "message_type", "sent_time", "user_id", 
        "user_name", "department_id", "department_name", "is_public"
    };
    
    for (String field : fieldsToCoopy) {
        if (originalMessage.has(field)) {
            try {
                ackData.put(field, originalMessage.get(field));
            } catch (JSONException e) {
                Log.w(TAG, "复制字段失败: " + field);
            }
        }
    }
}
```

## 六、部署和测试

### 6.1 环境配置

```yaml
# docker-compose.yml 添加Redis
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  ljwx-boot:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379

volumes:
  redis_data:
```

### 6.2 测试脚本

```python
# test_message_flow.py
import requests
import json
import time

class MessageFlowTester:
    
    def __init__(self):
        self.bigscreen_url = "http://localhost:5000"
        self.boot_url = "http://localhost:8080"
    
    def test_complete_flow(self):
        """测试完整消息流"""
        
        # 1. 在大屏创建消息
        message_data = {
            "title": "测试消息",
            "content": "这是一条测试消息",
            "message_type": "notification",
            "sender_type": "admin",
            "priority": 3,
            "urgency": "medium",
            "channels": ["message", "push"],
            "require_ack": True,
            "targets": [
                {
                    "device_sn": "TEST_DEVICE_001",
                    "target_type": "device",
                    "channel": "message"
                }
            ],
            "org_id": "1",
            "customer_id": 1
        }
        
        response = requests.post(
            f"{self.bigscreen_url}/api/enhanced/message/create",
            json=message_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] == True
        
        message_id = result['messageId']
        print(f"✅ 消息创建成功: {message_id}")
        
        # 2. 等待消息传播
        time.sleep(2)
        
        # 3. 检查消息状态
        stats_response = requests.get(
            f"{self.bigscreen_url}/api/enhanced/message/stats/1"
        )
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        print(f"✅ 消息统计: {stats['data']}")
        
        return message_id
    
    def test_acknowledgment(self, message_id):
        """测试消息确认"""
        
        ack_data = {
            "messageId": message_id,
            "deviceSn": "TEST_DEVICE_001",
            "acknowledgeTime": "2025-09-10T10:00:00Z",
            "responseTime": 30,
            "source": "phone"
        }
        
        # 模拟手机端确认
        response = requests.post(
            f"{self.boot_url}/api/message/acknowledge",
            json=ack_data
        )
        
        print(f"✅ 消息确认测试完成")

if __name__ == "__main__":
    tester = MessageFlowTester()
    message_id = tester.test_complete_flow()
    tester.test_acknowledgment(message_id)
    print("🎉 完整流程测试成功!")
```

## 七、监控和维护

### 7.1 性能监控

```java
// MessagePerformanceMonitor.java
@Component
public class MessagePerformanceMonitor {
    
    private final MeterRegistry meterRegistry;
    
    public MessagePerformanceMonitor(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }
    
    public void recordMessageCreated(String messageType) {
        meterRegistry.counter("message.created", "type", messageType).increment();
    }
    
    public void recordMessageDelivered(String channel, long deliveryTime) {
        meterRegistry.timer("message.delivery.time", "channel", channel)
            .record(deliveryTime, TimeUnit.MILLISECONDS);
    }
    
    public void recordMessageAcknowledged(String source, long responseTime) {
        meterRegistry.timer("message.response.time", "source", source)
            .record(responseTime, TimeUnit.SECONDS);
    }
}
```

### 7.2 日志配置

```yaml
# logback-spring.xml
<configuration>
    <appender name="MESSAGE_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/message.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/message.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <logger name="com.ljwx.modules.health.service.EnhancedMessageService" level="INFO" additivity="false">
        <appender-ref ref="MESSAGE_FILE"/>
    </logger>
</configuration>
```

## 八、总结

通过以上实施方案，可以实现：

1. **完整数据流打通**: 四端消息传递无缝连接
2. **实时状态同步**: Redis驱动的实时更新
3. **全面跟踪能力**: 从创建到确认的完整监控
4. **向后兼容性**: 保持现有API不变
5. **可监控性**: 完善的日志和性能指标

实施周期约为5-6周，每个阶段独立部署，风险可控。