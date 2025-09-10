# 基于现有数据库的统一消息数据模型

## 数据库表结构映射

基于现有的 `t_device_message` 和 `t_device_message_detail` 表结构，定义统一的消息数据模型。

### 主消息表 (t_device_message)

```sql
CREATE TABLE t_device_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_sn VARCHAR(255) NOT NULL,           -- 设备序列号
    message TEXT NOT NULL,                     -- 消息内容
    org_id VARCHAR(50),                        -- 组织ID
    user_id VARCHAR(50),                       -- 用户ID
    customer_id BIGINT NOT NULL DEFAULT 0,     -- 租户ID
    message_type VARCHAR(50) NOT NULL,         -- 消息类型: job/task/announcement/notification/system_alert
    sender_type VARCHAR(50) NOT NULL,          -- 发送者类型: system/admin/user
    receiver_type VARCHAR(50) NOT NULL,        -- 接收者类型: device/user/department
    message_status VARCHAR(50) DEFAULT 'pending', -- 消息状态: pending/delivered/acknowledged
    responded_number INTEGER DEFAULT 0,        -- 响应数量
    sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    received_time DATETIME NULL,
    -- 扩展字段
    title VARCHAR(500),                        -- 消息标题
    priority INTEGER DEFAULT 3,               -- 优先级 1-5
    urgency VARCHAR(20) DEFAULT 'medium',      -- 紧急程度: low/medium/high/critical
    channels JSON,                             -- 分发渠道: ["message","push","wechat","watch"]
    require_ack BOOLEAN DEFAULT false,         -- 是否需要确认
    expiry_time DATETIME,                      -- 过期时间
    metadata JSON,                             -- 元数据
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 消息详情表 (t_device_message_detail)

```sql
CREATE TABLE t_device_message_detail (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id BIGINT NOT NULL,                -- 关联主消息ID
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
    -- 扩展字段用于完整跟踪
    distribution_id VARCHAR(255),             -- 分发ID
    target_type VARCHAR(50),                  -- 目标类型: user/device/department/organization
    target_id VARCHAR(255),                   -- 目标ID
    delivery_status VARCHAR(50),              -- 分发状态: pending/delivered/acknowledged/failed/expired
    channel VARCHAR(50),                      -- 分发渠道: message/push/wechat/watch
    response_time INTEGER,                    -- 响应时间(秒)
    acknowledge_time DATETIME,                -- 确认时间
    delivery_details JSON                     -- 分发详情
);
```

## 统一消息JSON模型

### 完整消息实体

```json
{
  "messageId": "1934567890123456789",
  "messageType": "job|task|announcement|notification|system_alert",
  "title": "消息标题",
  "content": "消息内容", 
  "priority": 3,
  "urgency": "medium",
  
  "sender": {
    "senderId": "发送者ID",
    "senderName": "发送者姓名", 
    "senderType": "admin|system|user",
    "platformSource": "ljwx-admin|ljwx-bigscreen|auto-alert"
  },
  
  "target": {
    "targetType": "user|department|organization|device",
    "targetIds": ["1001", "1002"],
    "deviceSns": ["DEVICE001", "DEVICE002"],
    "customerId": 1,
    "orgIds": [101, 102],
    "userIds": [1001, 1002]
  },
  
  "delivery": {
    "channels": ["message", "push", "wechat", "watch"],
    "deliveryTime": "2025-09-10T08:00:00Z",
    "expiryTime": "2025-09-12T08:00:00Z", 
    "requireAck": true,
    "ackTimeout": 3600
  },
  
  "status": {
    "messageStatus": "pending|delivered|acknowledged|expired",
    "createTime": "2025-09-10T08:00:00Z",
    "sentTime": "2025-09-10T08:00:01Z",
    "deliveryStats": {
      "totalTargets": 100,
      "delivered": 95,
      "acknowledged": 78,
      "pending": 17,
      "failed": 5
    }
  },
  
  "metadata": {
    "source": "manual|auto-alert|scheduled",
    "relatedAlertId": "告警关联ID",
    "relatedHealthId": "健康数据关联ID", 
    "tags": ["urgent", "health", "safety"],
    "customFields": {}
  }
}
```

## 基于实际代码的数据流架构

### 消息数据流向

```
ljwx-admin/ljwx-bigscreen → ljwx-boot → ljwx-phone → ljwx-watch
      ↓                        ↓           ↓           ↓
   消息创建              t_device_message   Redis      HTTP/蓝牙
      ↓                        ↓           ↓           ↓ 
   规则匹配            t_device_message_detail  订阅    系统通知
      ↓                        ↓           ↓           ↓
   告警转消息                API接口        消息转发     用户确认
      ↓                        ↓           ↓           ↓
   数据库存储                Redis发布     蓝牙传输     确认回传
```

### 各平台现有API接口

#### ljwx-boot (Java后端)
```java
// 现有接口
@RestController
@RequestMapping("t_device_message")
public class TDeviceMessageController {
    @GetMapping("/page")              // 分页查询消息
    @GetMapping("/{id}")              // 根据ID获取消息
    @PostMapping("/")                 // 新增消息
    @PutMapping("/")                  // 更新消息
    @DeleteMapping("/")               // 批量删除消息
}

// 兼容性服务
@Service
public class DeviceMessageServiceImpl {
    Result<Map<String, Object>> saveMessage(DeviceMessageSaveRequest)
    Result<Map<String, Object>> sendMessage(DeviceMessageSendRequest)  
    Result<Map<String, Object>> receiveMessages(String deviceSn)
}
```

#### ljwx-bigscreen (Python大屏)
```python
# 现有接口
@app.route("/message")                              # 消息页面
@app.route('/DeviceMessage/save_message', methods=['POST'])  # 保存消息
@app.route('/DeviceMessage/send', methods=['POST'])          # 发送消息
@app.route('/DeviceMessage/receive', methods=['GET'])        # 接收消息
@app.route('/fetch_messages', methods=['GET'])               # 按设备获取消息
@app.route('/get_messages_by_orgIdAndUserId', methods=['GET']) # 按组织用户获取

# 告警转消息机制
class MessageNotifier:
    @staticmethod
    def send_message(device_sn, message, message_type, health_id=None)
```

#### ljwx-phone (Flutter移动端) 
```dart
// 现有服务
class ApiService {
  Future<List<Map<String, dynamic>>> getDeviceMessages(String deviceSn)
  Future<bool> markMessageAsRead(String deviceSn, ...)
  Future<PersonalData> getPersonalInfo(String phone)  // 包含消息信息
}

// 消息模型
class Message {
  final String id, title, content, createTime;
  final String department, messageStatus, messageType;
  final String? imageUrl;
}

// 蓝牙消息转发
class BluetoothService {
  Future<void> _fetchAndSendMessages()  // 获取并发送消息到手表
  Future<bool> sendMsg(Map<String, dynamic> message)
}
```

#### ljwx-watch (HarmonyOS手表)
```java
// HTTP模式
public class HttpService {
    public void fetchMessageFromServer()  // 从服务器获取消息
    private void handleMessageResponse(JSONObject message)  // 处理消息响应
}

// 蓝牙模式  
public class BluetoothService {
    private void handleCommand(BlePeripheralDevice device, String command)
    private void handleMessageCommand(JSONObject cmdJson)  // 处理消息命令
}

// 消息类型映射
private static final Map<String, String> MESSAGE_TYPE_MAP = {
    "announcement" -> "公告",
    "notification" -> "个人通知", 
    "warning" -> "告警",
    "job" -> "作业指引",
    "task" -> "任务管理"
};
```

## 消息分发记录

基于 `t_device_message_detail` 表的分发记录格式：

```json
{
  "distributionId": "1934567890123456790",
  "messageId": "1934567890123456789", 
  "targetId": "1001",
  "targetType": "user",
  "deviceSn": "DEVICE001",
  "channel": "message",
  "deliveryStatus": "pending|delivered|acknowledged|failed|expired",
  "deliveryTime": "2025-09-10T08:00:05Z",
  "acknowledgeTime": "2025-09-10T08:15:30Z", 
  "responseTime": 930,
  
  "deliveryDetails": {
    "attempts": 2,
    "lastAttemptTime": "2025-09-10T08:00:05Z",
    "errorMessage": null,
    "platform": "ljwx-phone",
    "deviceInfo": {
      "phoneModel": "iPhone 13", 
      "watchModel": "HarmonyOS Watch",
      "appVersion": "1.0.3"
    }
  }
}
```

## 现有消息类型定义

基于代码分析，系统支持以下消息类型：

```javascript
const MESSAGE_TYPES = {
  // ljwx-phone定义
  "job": "作业指引",           // 蓝绿色，工作图标
  "task": "任务管理",          // 蓝色，任务图标  
  "announcement": "系统公告",   // 紫色，广播图标
  "notification": "通知",      // 琥珀色，通知图标
  
  // ljwx-bigscreen扩展
  "system_alert": "系统告警",   // 自动告警生成
  
  // ljwx-watch映射
  "warning": "告警"           // 告警类消息
};
```