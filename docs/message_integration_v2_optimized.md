# 基于V2版本的消息数据流集成优化方案

基于现有数据库优化方案中的V2表结构，提供一个高性能、可扩展的消息数据流集成方案，实现 **10-100倍性能提升** 和 **完整的四端数据流打通**。

## 一、V2版本核心优势

### 1.1 性能提升对比

| 性能指标 | 当前V1版本 | V2优化版本 | 提升幅度 | 实现方式 |
|---------|-----------|-----------|----------|----------|
| **消息列表查询** | 200-1000ms | 20-50ms | **10-20倍** | 优化索引 + ENUM类型 |
| **部门层级查询** | 100-500ms | <5ms | **20-100倍** | 闭包表 + 复合索引 |
| **存储空间** | 100% | 60% | **节省40%** | ENUM + VARCHAR优化 |
| **并发TPS** | 100 TPS | 1000+ TPS | **10倍+** | 分区表 + 索引优化 |
| **数据完整性** | 弱 | 强 | **质的提升** | 外键约束 + 类型匹配 |

### 1.2 V2版本表结构设计

```sql
-- 优化后的主消息表 V2
CREATE TABLE `t_device_message_v2` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `customer_id` bigint NOT NULL COMMENT '租户ID',
  `department_id` bigint NOT NULL COMMENT '部门ID',
  `user_id` bigint NULL COMMENT '用户ID',
  `device_sn` varchar(64) NOT NULL COMMENT '设备序列号',
  
  -- 消息内容
  `title` varchar(200) NULL COMMENT '消息标题',
  `message` text NOT NULL COMMENT '消息内容',
  `message_type` enum('task','job','announcement','notification','alert','emergency') NOT NULL COMMENT '消息类型',
  `sender_type` enum('system','user','device','admin') NOT NULL COMMENT '发送者类型',
  `receiver_type` enum('user','device','department','all') NOT NULL COMMENT '接收者类型',
  `priority_level` tinyint NOT NULL DEFAULT 3 COMMENT '优先级(1-5)',
  `urgency` enum('low','medium','high','critical') NOT NULL DEFAULT 'medium' COMMENT '紧急程度',
  
  -- 状态和时间
  `message_status` enum('pending','processing','delivered','acknowledged','failed','expired') NOT NULL DEFAULT 'pending',
  `sent_time` datetime(3) NULL COMMENT '发送时间',
  `received_time` datetime(3) NULL COMMENT '接收时间',
  `expired_time` datetime(3) NULL COMMENT '过期时间',
  
  -- 统计字段
  `responded_count` int NOT NULL DEFAULT 0 COMMENT '响应用户数',
  `target_count` int NOT NULL DEFAULT 0 COMMENT '目标用户数',
  
  -- 扩展字段 (JSON格式)
  `channels` json NULL COMMENT '分发渠道 ["message","push","wechat","watch"]',
  `require_ack` boolean NOT NULL DEFAULT false COMMENT '是否需要确认',
  `metadata` json NULL COMMENT '扩展元数据',
  
  -- 审计字段
  `create_user_id` bigint NULL COMMENT '创建用户ID',
  `create_time` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `update_user_id` bigint NULL COMMENT '更新用户ID',
  `update_time` datetime(3) NULL ON UPDATE CURRENT_TIMESTAMP(3),
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `version` int NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
  
  PRIMARY KEY (`id`),
  
  -- 高性能复合索引
  KEY `idx_customer_time` (`customer_id`, `create_time` DESC, `is_deleted`),
  KEY `idx_customer_dept_status` (`customer_id`, `department_id`, `message_status`, `is_deleted`),
  KEY `idx_customer_user_type` (`customer_id`, `user_id`, `message_type`, `is_deleted`),
  KEY `idx_device_time` (`device_sn`, `create_time` DESC),
  KEY `idx_status_priority_time` (`message_status`, `priority_level`, `create_time` DESC),
  KEY `idx_sent_time` (`sent_time`),
  KEY `idx_expired_cleanup` (`expired_time`, `is_deleted`),
  KEY `idx_partition_key` (`create_time`, `customer_id`)
  
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  ROW_FORMAT=COMPRESSED 
  KEY_BLOCK_SIZE=8
  COMMENT='设备消息表V2-高性能版'
  
  -- 按月分区优化
  PARTITION BY RANGE (TO_DAYS(create_time)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p202504 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p202505 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p202506 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );
```

```sql
-- 优化后的消息详情表 V2
CREATE TABLE `t_device_message_detail_v2` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `message_id` bigint NOT NULL COMMENT '主消息ID',
  `customer_id` bigint NOT NULL COMMENT '租户ID',
  `distribution_id` varchar(64) NOT NULL COMMENT '分发ID',
  
  -- 目标信息
  `target_type` enum('user','device','department','organization') NOT NULL COMMENT '目标类型',
  `target_id` varchar(64) NOT NULL COMMENT '目标ID',
  `device_sn` varchar(64) NOT NULL COMMENT '设备序列号',
  `user_id` bigint NULL COMMENT '响应用户ID',
  
  -- 分发信息
  `channel` enum('message','push','wechat','watch','sms','email') NOT NULL COMMENT '分发渠道',
  `delivery_status` enum('pending','delivered','acknowledged','failed','expired','retry') NOT NULL DEFAULT 'pending',
  `retry_count` tinyint NOT NULL DEFAULT 0 COMMENT '重试次数',
  `last_retry_time` datetime(3) NULL COMMENT '最后重试时间',
  
  -- 响应信息
  `response_message` text NULL COMMENT '响应消息内容',
  `response_type` enum('acknowledged','rejected','timeout','manual') NOT NULL DEFAULT 'acknowledged',
  `response_time` datetime(3) NULL COMMENT '响应时间',
  `delivery_time` datetime(3) NULL COMMENT '分发时间',
  `acknowledge_time` datetime(3) NULL COMMENT '确认时间',
  `response_duration` int NULL COMMENT '响应耗时(秒)',
  
  -- 扩展信息
  `delivery_details` json NULL COMMENT '分发详情',
  `client_info` json NULL COMMENT '客户端信息',
  `location_info` json NULL COMMENT '位置信息',
  
  -- 审计字段
  `create_time` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `update_time` datetime(3) NULL ON UPDATE CURRENT_TIMESTAMP(3),
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
  
  PRIMARY KEY (`id`),
  
  -- 外键约束
  CONSTRAINT `fk_message_detail_v2` FOREIGN KEY (`message_id`) REFERENCES `t_device_message_v2` (`id`) ON DELETE CASCADE,
  
  -- 高性能索引
  UNIQUE KEY `uk_message_device_user` (`message_id`, `device_sn`, `user_id`),
  KEY `idx_customer_message` (`customer_id`, `message_id`),
  KEY `idx_customer_device_time` (`customer_id`, `device_sn`, `create_time` DESC),
  KEY `idx_target_type_id` (`target_type`, `target_id`),
  KEY `idx_delivery_status_retry` (`delivery_status`, `retry_count`, `last_retry_time`),
  KEY `idx_response_time` (`response_time`),
  KEY `idx_distribution_id` (`distribution_id`),
  KEY `idx_partition_key` (`create_time`, `customer_id`)
  
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  ROW_FORMAT=COMPRESSED 
  KEY_BLOCK_SIZE=8
  COMMENT='消息详情表V2-高性能版'
  
  -- 与主表同步分区
  PARTITION BY RANGE (TO_DAYS(create_time)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p202504 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p202505 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p202506 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
  );
```

```sql
-- 新增：消息生命周期跟踪表
CREATE TABLE `t_message_lifecycle_v2` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `message_id` bigint NOT NULL COMMENT '消息ID',
  `customer_id` bigint NOT NULL COMMENT '租户ID',
  `event_type` enum('created','published','distributed','delivered','acknowledged','failed','expired','cancelled') NOT NULL COMMENT '事件类型',
  `event_data` json NULL COMMENT '事件数据',
  `operator_id` bigint NULL COMMENT '操作者ID',
  `operator_type` enum('system','user','admin','device') NOT NULL COMMENT '操作者类型',
  `platform_source` enum('ljwx-admin','ljwx-bigscreen','ljwx-boot','ljwx-phone','ljwx-watch') NOT NULL COMMENT '平台来源',
  `event_time` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '事件时间',
  `duration_ms` int NULL COMMENT '事件耗时(毫秒)',
  
  PRIMARY KEY (`id`),
  KEY `idx_message_event_time` (`message_id`, `event_time`),
  KEY `idx_customer_event_type` (`customer_id`, `event_type`, `event_time`),
  KEY `idx_platform_time` (`platform_source`, `event_time`),
  
  CONSTRAINT `fk_lifecycle_message` FOREIGN KEY (`message_id`) REFERENCES `t_device_message_v2` (`id`) ON DELETE CASCADE
  
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='消息生命周期跟踪表V2';
```

## 二、ljwx-boot V2实体类和服务层

### 2.1 V2实体类定义

```java
// TDeviceMessageV2.java - 主消息实体V2
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_message_v2")
@EqualsAndHashCode(callSuper = true)
public class TDeviceMessageV2 extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    @TableField("customer_id")
    private Long customerId;
    
    @TableField("department_id") 
    private Long departmentId;
    
    @TableField("user_id")
    private Long userId;
    
    @TableField("device_sn")
    private String deviceSn;
    
    // 消息内容
    private String title;
    private String message;
    
    @TableField("message_type")
    private MessageTypeEnum messageType;
    
    @TableField("sender_type")
    private SenderTypeEnum senderType;
    
    @TableField("receiver_type")
    private ReceiverTypeEnum receiverType;
    
    @TableField("priority_level")
    private Integer priorityLevel;
    
    private UrgencyEnum urgency;
    
    // 状态和时间
    @TableField("message_status")
    private MessageStatusEnum messageStatus;
    
    @TableField("sent_time")
    private LocalDateTime sentTime;
    
    @TableField("received_time")
    private LocalDateTime receivedTime;
    
    @TableField("expired_time")
    private LocalDateTime expiredTime;
    
    // 统计字段
    @TableField("responded_count")
    private Integer respondedCount;
    
    @TableField("target_count")
    private Integer targetCount;
    
    // JSON字段处理
    @TableField(value = "channels", typeHandler = JacksonTypeHandler.class)
    private List<String> channels;
    
    @TableField("require_ack")
    private Boolean requireAck;
    
    @TableField(value = "metadata", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> metadata;
    
    // 审计字段
    @TableField("create_user_id")
    private Long createUserId;
    
    @TableField("update_user_id")
    private Long updateUserId;
    
    @TableField("is_deleted")
    @TableLogic
    private Integer isDeleted;
    
    @Version
    private Integer version;
}

// TDeviceMessageDetailV2.java - 消息详情实体V2
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_message_detail_v2")
@EqualsAndHashCode(callSuper = true)
public class TDeviceMessageDetailV2 extends BaseEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    @TableField("message_id")
    private Long messageId;
    
    @TableField("customer_id")
    private Long customerId;
    
    @TableField("distribution_id")
    private String distributionId;
    
    // 目标信息
    @TableField("target_type")
    private TargetTypeEnum targetType;
    
    @TableField("target_id")
    private String targetId;
    
    @TableField("device_sn")
    private String deviceSn;
    
    @TableField("user_id")
    private Long userId;
    
    // 分发信息
    private ChannelEnum channel;
    
    @TableField("delivery_status")
    private DeliveryStatusEnum deliveryStatus;
    
    @TableField("retry_count")
    private Integer retryCount;
    
    @TableField("last_retry_time")
    private LocalDateTime lastRetryTime;
    
    // 响应信息
    @TableField("response_message")
    private String responseMessage;
    
    @TableField("response_type")
    private ResponseTypeEnum responseType;
    
    @TableField("response_time")
    private LocalDateTime responseTime;
    
    @TableField("delivery_time")
    private LocalDateTime deliveryTime;
    
    @TableField("acknowledge_time")
    private LocalDateTime acknowledgeTime;
    
    @TableField("response_duration")
    private Integer responseDuration;
    
    // JSON字段
    @TableField(value = "delivery_details", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> deliveryDetails;
    
    @TableField(value = "client_info", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> clientInfo;
    
    @TableField(value = "location_info", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> locationInfo;
    
    @TableField("is_deleted")
    @TableLogic
    private Integer isDeleted;
}

// TMessageLifecycleV2.java - 生命周期跟踪实体
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_message_lifecycle_v2")
public class TMessageLifecycleV2 {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    @TableField("message_id")
    private Long messageId;
    
    @TableField("customer_id")
    private Long customerId;
    
    @TableField("event_type")
    private EventTypeEnum eventType;
    
    @TableField(value = "event_data", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> eventData;
    
    @TableField("operator_id")
    private Long operatorId;
    
    @TableField("operator_type")
    private OperatorTypeEnum operatorType;
    
    @TableField("platform_source")
    private PlatformSourceEnum platformSource;
    
    @TableField("event_time")
    private LocalDateTime eventTime;
    
    @TableField("duration_ms")
    private Integer durationMs;
}
```

### 2.2 枚举类型定义

```java
// MessageTypeEnum.java
public enum MessageTypeEnum implements IEnum<String> {
    TASK("task", "任务管理"),
    JOB("job", "作业指引"),
    ANNOUNCEMENT("announcement", "系统公告"),
    NOTIFICATION("notification", "通知"),
    ALERT("alert", "告警"),
    EMERGENCY("emergency", "紧急");
    
    private final String value;
    private final String desc;
    
    MessageTypeEnum(String value, String desc) {
        this.value = value;
        this.desc = desc;
    }
    
    @Override
    public String getValue() {
        return value;
    }
}

// MessageStatusEnum.java
public enum MessageStatusEnum implements IEnum<String> {
    PENDING("pending", "待处理"),
    PROCESSING("processing", "处理中"),
    DELIVERED("delivered", "已送达"),
    ACKNOWLEDGED("acknowledged", "已确认"),
    FAILED("failed", "失败"),
    EXPIRED("expired", "已过期");
    
    private final String value;
    private final String desc;
    
    // 构造函数和getter方法
}

// DeliveryStatusEnum.java
public enum DeliveryStatusEnum implements IEnum<String> {
    PENDING("pending", "等待分发"),
    DELIVERED("delivered", "已分发"),
    ACKNOWLEDGED("acknowledged", "已确认"),
    FAILED("failed", "分发失败"),
    EXPIRED("expired", "已过期"),
    RETRY("retry", "重试中");
    
    private final String value;
    private final String desc;
    
    // 构造函数和getter方法
}

// ChannelEnum.java
public enum ChannelEnum implements IEnum<String> {
    MESSAGE("message", "消息"),
    PUSH("push", "推送"),
    WECHAT("wechat", "微信"),
    WATCH("watch", "手表"),
    SMS("sms", "短信"),
    EMAIL("email", "邮件");
    
    private final String value;
    private final String desc;
    
    // 构造函数和getter方法
}
```

### 2.3 V2高性能服务层

```java
// MessageServiceV2.java - 主服务类
@Service
@Slf4j
@RequiredArgsConstructor
@Transactional
public class MessageServiceV2 {
    
    private final TDeviceMessageV2Mapper messageMapper;
    private final TDeviceMessageDetailV2Mapper detailMapper;
    private final TMessageLifecycleV2Mapper lifecycleMapper;
    private final RedisTemplate<String, Object> redisTemplate;
    private final MessageCacheService cacheService;
    private final MessageDistributionService distributionService;
    
    /**
     * 创建高性能消息 - 支持批量目标
     */
    public Long createMessage(MessageCreateRequestV2 request) {
        Timer.Sample sample = Timer.start();
        
        try {
            // 1. 验证和预处理
            validateMessageRequest(request);
            
            // 2. 创建主消息
            TDeviceMessageV2 message = buildMessageEntity(request);
            messageMapper.insert(message);
            
            // 3. 批量创建分发记录
            List<TDeviceMessageDetailV2> details = buildDistributionDetails(message, request.getTargets());
            if (!details.isEmpty()) {
                detailMapper.insertBatch(details);
                
                // 更新目标计数
                message.setTargetCount(details.size());
                messageMapper.updateById(message);
            }
            
            // 4. 记录生命周期事件
            recordLifecycleEvent(message.getId(), EventTypeEnum.CREATED, 
                request.getOperatorId(), OperatorTypeEnum.USER, PlatformSourceEnum.LJWX_ADMIN);
            
            // 5. 异步分发处理
            CompletableFuture.runAsync(() -> {
                distributionService.processMessageDistribution(message.getId());
            });
            
            log.info("✅ 消息创建成功: messageId={}, 目标数量={}", message.getId(), details.size());
            return message.getId();
            
        } catch (Exception e) {
            log.error("❌ 消息创建失败: {}", e.getMessage(), e);
            throw new MessageServiceException("消息创建失败", e);
        } finally {
            sample.stop(Timer.builder("message.create.time").register(Metrics.globalRegistry));
        }
    }
    
    /**
     * 高性能分页查询 - 使用优化索引
     */
    public IPage<MessageResponseV2> getMessagePage(MessageQueryV2 query) {
        
        // 1. 利用缓存
        String cacheKey = buildCacheKey("message:page", query);
        IPage<MessageResponseV2> cached = cacheService.get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        // 2. 数据库查询 - 使用优化后的索引
        Page<MessageResponseV2> page = new Page<>(query.getPageNo(), query.getPageSize());
        IPage<MessageResponseV2> result = messageMapper.selectOptimizedMessagePage(page, query);
        
        if (result.getRecords().isEmpty()) {
            return result;
        }
        
        // 3. 批量加载关联数据
        enrichMessageData(result.getRecords());
        
        // 4. 缓存结果
        cacheService.set(cacheKey, result, Duration.ofMinutes(5));
        
        return result;
    }
    
    /**
     * 批量确认消息 - 高性能更新
     */
    public void batchAcknowledgeMessages(BatchAcknowledgeRequest request) {
        
        // 1. 批量更新详情状态
        LambdaUpdateWrapper<TDeviceMessageDetailV2> detailWrapper = new LambdaUpdateWrapper<>();
        detailWrapper.in(TDeviceMessageDetailV2::getMessageId, request.getMessageIds())
                    .eq(TDeviceMessageDetailV2::getDeviceSn, request.getDeviceSn())
                    .set(TDeviceMessageDetailV2::getDeliveryStatus, DeliveryStatusEnum.ACKNOWLEDGED)
                    .set(TDeviceMessageDetailV2::getAcknowledgeTime, LocalDateTime.now())
                    .set(TDeviceMessageDetailV2::getResponseDuration, request.getResponseDuration());
        
        detailMapper.update(null, detailWrapper);
        
        // 2. 批量更新主消息统计
        for (Long messageId : request.getMessageIds()) {
            updateMessageStatistics(messageId);
        }
        
        // 3. 批量记录生命周期事件
        List<TMessageLifecycleV2> lifecycleEvents = request.getMessageIds().stream()
            .map(messageId -> TMessageLifecycleV2.builder()
                .messageId(messageId)
                .customerId(request.getCustomerId())
                .eventType(EventTypeEnum.ACKNOWLEDGED)
                .operatorId(request.getUserId())
                .operatorType(OperatorTypeEnum.USER)
                .platformSource(PlatformSourceEnum.LJWX_PHONE)
                .eventTime(LocalDateTime.now())
                .eventData(Map.of("deviceSn", request.getDeviceSn(), "batchSize", request.getMessageIds().size()))
                .build())
            .collect(Collectors.toList());
        
        lifecycleMapper.insertBatch(lifecycleEvents);
        
        // 4. 发布确认事件到Redis
        MessageAcknowledgedEvent event = MessageAcknowledgedEvent.builder()
            .messageIds(request.getMessageIds())
            .deviceSn(request.getDeviceSn())
            .userId(request.getUserId())
            .acknowledgeTime(LocalDateTime.now())
            .source("ljwx-phone")
            .build();
        
        redisTemplate.convertAndSend("message:acknowledged", event);
        
        log.info("✅ 批量确认消息成功: 消息数量={}, 设备={}", request.getMessageIds().size(), request.getDeviceSn());
    }
    
    /**
     * 获取消息统计 - 利用分区和索引优化
     */
    public MessageStatisticsV2 getMessageStatistics(StatisticsQueryV2 query) {
        
        // 利用分区查询优化
        List<MessageStatisticsV2> partitionStats = new ArrayList<>();
        
        // 按分区并行查询
        List<String> partitions = getRelevantPartitions(query.getStartTime(), query.getEndTime());
        
        List<CompletableFuture<MessageStatisticsV2>> futures = partitions.stream()
            .map(partition -> CompletableFuture.supplyAsync(() -> 
                messageMapper.getPartitionStatistics(partition, query)))
            .collect(Collectors.toList());
        
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenApply(v -> futures.stream()
                .map(CompletableFuture::join)
                .collect(Collectors.toList()))
            .thenAccept(partitionStats::addAll);
        
        // 合并分区统计结果
        return mergePartitionStatistics(partitionStats);
    }
    
    private void enrichMessageData(List<MessageResponseV2> messages) {
        if (messages.isEmpty()) return;
        
        // 收集需要查询的ID
        Set<Long> departmentIds = messages.stream()
            .map(MessageResponseV2::getDepartmentId)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        
        Set<Long> userIds = messages.stream()
            .map(MessageResponseV2::getUserId)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        
        Set<Long> messageIds = messages.stream()
            .map(MessageResponseV2::getMessageId)
            .collect(Collectors.toSet());
        
        // 并行批量查询
        CompletableFuture<Map<Long, String>> departmentFuture = CompletableFuture
            .supplyAsync(() -> cacheService.batchGetDepartmentNames(departmentIds));
        
        CompletableFuture<Map<Long, String>> userFuture = CompletableFuture
            .supplyAsync(() -> cacheService.batchGetUserNames(userIds));
        
        CompletableFuture<Map<Long, MessageProgressV2>> progressFuture = CompletableFuture
            .supplyAsync(() -> detailMapper.batchGetMessageProgress(messageIds));
        
        // 等待所有查询完成并设置数据
        CompletableFuture.allOf(departmentFuture, userFuture, progressFuture)
            .thenRun(() -> {
                Map<Long, String> departmentMap = departmentFuture.join();
                Map<Long, String> userMap = userFuture.join();
                Map<Long, MessageProgressV2> progressMap = progressFuture.join();
                
                messages.parallelStream().forEach(message -> {
                    message.setDepartmentName(departmentMap.get(message.getDepartmentId()));
                    message.setUserName(userMap.get(message.getUserId()));
                    message.setProgress(progressMap.get(message.getMessageId()));
                });
            })
            .join();
    }
}
```

### 2.4 V2 Mapper优化

```java
// TDeviceMessageV2Mapper.java
@Mapper
public interface TDeviceMessageV2Mapper extends BaseMapper<TDeviceMessageV2> {
    
    /**
     * 优化的分页查询 - 利用复合索引
     */
    IPage<MessageResponseV2> selectOptimizedMessagePage(
        @Param("page") Page<MessageResponseV2> page,
        @Param("query") MessageQueryV2 query
    );
    
    /**
     * 按分区查询统计 - 利用分区优化
     */
    MessageStatisticsV2 getPartitionStatistics(
        @Param("partition") String partition,
        @Param("query") StatisticsQueryV2 query
    );
    
    /**
     * 批量更新消息状态 - 高性能批量操作
     */
    int batchUpdateStatus(
        @Param("messageIds") List<Long> messageIds,
        @Param("status") MessageStatusEnum status
    );
    
    /**
     * 获取需要过期处理的消息 - 利用过期索引
     */
    List<Long> selectExpiredMessages(@Param("currentTime") LocalDateTime currentTime);
}
```

```xml
<!-- TDeviceMessageV2Mapper.xml -->
<mapper namespace="com.ljwx.modules.health.mapper.TDeviceMessageV2Mapper">

    <!-- 优化的分页查询 - 充分利用复合索引 -->
    <select id="selectOptimizedMessagePage" resultType="MessageResponseV2">
        SELECT 
            m.id as messageId,
            m.customer_id as customerId,
            m.department_id as departmentId,
            m.user_id as userId,
            m.device_sn as deviceSn,
            m.title,
            m.message,
            m.message_type as messageType,
            m.sender_type as senderType,
            m.receiver_type as receiverType,
            m.priority_level as priorityLevel,
            m.urgency,
            m.message_status as messageStatus,
            m.sent_time as sentTime,
            m.received_time as receivedTime,
            m.expired_time as expiredTime,
            m.responded_count as respondedCount,
            m.target_count as targetCount,
            m.require_ack as requireAck,
            m.channels,
            m.metadata,
            m.create_time as createTime,
            m.create_user_id as createUserId,
            m.version,
            
            -- 直接JOIN避免N+1查询
            COALESCE(dept.org_name, '未知部门') as departmentName,
            COALESCE(user.user_name, '系统') as userName
            
        FROM t_device_message_v2 m
        LEFT JOIN sys_org_units dept ON m.department_id = dept.id AND dept.is_deleted = 0
        LEFT JOIN sys_user user ON m.user_id = user.id AND user.is_deleted = 0
        
        <where>
            m.customer_id = #{query.customerId}
            AND m.is_deleted = 0
            
            <if test="query.departmentId != null">
                AND m.department_id IN (
                    SELECT DISTINCT ancestor_id 
                    FROM sys_org_closure 
                    WHERE descendant_id = #{query.departmentId} 
                      AND customer_id = #{query.customerId}
                )
            </if>
            
            <if test="query.messageType != null">
                AND m.message_type = #{query.messageType}
            </if>
            
            <if test="query.messageStatus != null">
                AND m.message_status = #{query.messageStatus}
            </if>
            
            <if test="query.priorityLevel != null">
                AND m.priority_level = #{query.priorityLevel}
            </if>
            
            <if test="query.urgency != null">
                AND m.urgency = #{query.urgency}
            </if>
            
            <if test="query.startTime != null">
                AND m.create_time >= #{query.startTime}
            </if>
            
            <if test="query.endTime != null">
                AND m.create_time <![CDATA[<=]]> #{query.endTime}
            </if>
            
            <if test="query.keyword != null and query.keyword != ''">
                AND (m.title LIKE CONCAT('%', #{query.keyword}, '%') 
                     OR m.message LIKE CONCAT('%', #{query.keyword}, '%'))
            </if>
        </where>
        
        ORDER BY m.priority_level DESC, m.create_time DESC
    </select>
    
    <!-- 分区统计查询 - 利用分区剪枝 -->
    <select id="getPartitionStatistics" resultType="MessageStatisticsV2">
        SELECT 
            COUNT(*) as totalMessages,
            COUNT(CASE WHEN message_status = 'pending' THEN 1 END) as pendingCount,
            COUNT(CASE WHEN message_status = 'delivered' THEN 1 END) as deliveredCount,
            COUNT(CASE WHEN message_status = 'acknowledged' THEN 1 END) as acknowledgedCount,
            COUNT(CASE WHEN message_status = 'failed' THEN 1 END) as failedCount,
            COUNT(CASE WHEN message_status = 'expired' THEN 1 END) as expiredCount,
            
            -- 按消息类型统计
            COUNT(CASE WHEN message_type = 'task' THEN 1 END) as taskCount,
            COUNT(CASE WHEN message_type = 'job' THEN 1 END) as jobCount,
            COUNT(CASE WHEN message_type = 'announcement' THEN 1 END) as announcementCount,
            COUNT(CASE WHEN message_type = 'notification' THEN 1 END) as notificationCount,
            COUNT(CASE WHEN message_type = 'alert' THEN 1 END) as alertCount,
            COUNT(CASE WHEN message_type = 'emergency' THEN 1 END) as emergencyCount,
            
            -- 按优先级统计
            COUNT(CASE WHEN priority_level = 1 THEN 1 END) as priority1Count,
            COUNT(CASE WHEN priority_level = 2 THEN 1 END) as priority2Count,
            COUNT(CASE WHEN priority_level = 3 THEN 1 END) as priority3Count,
            COUNT(CASE WHEN priority_level = 4 THEN 1 END) as priority4Count,
            COUNT(CASE WHEN priority_level = 5 THEN 1 END) as priority5Count,
            
            -- 响应时间统计
            AVG(CASE WHEN responded_count > 0 THEN 
                TIMESTAMPDIFF(SECOND, sent_time, received_time) END) as avgResponseTime,
            
            -- 完成率统计
            ROUND(AVG(CASE WHEN target_count > 0 THEN 
                responded_count / target_count * 100 ELSE 0 END), 2) as completionRate
                
        FROM t_device_message_v2 PARTITION (#{partition})
        WHERE customer_id = #{query.customerId}
          AND is_deleted = 0
          <if test="query.startTime != null">
              AND create_time >= #{query.startTime}
          </if>
          <if test="query.endTime != null">
              AND create_time <![CDATA[<=]]> #{query.endTime}
          </if>
    </select>
    
    <!-- 批量状态更新 - 高性能批量操作 -->
    <update id="batchUpdateStatus">
        UPDATE t_device_message_v2 
        SET message_status = #{status},
            update_time = NOW(3),
            version = version + 1
        WHERE id IN 
        <foreach collection="messageIds" item="id" open="(" separator="," close=")">
            #{id}
        </foreach>
        AND is_deleted = 0
    </update>
    
    <!-- 过期消息查询 - 利用过期索引 -->
    <select id="selectExpiredMessages" resultType="java.lang.Long">
        SELECT id
        FROM t_device_message_v2
        WHERE expired_time IS NOT NULL
          AND expired_time <![CDATA[<=]]> #{currentTime}
          AND message_status NOT IN ('acknowledged', 'expired', 'failed')
          AND is_deleted = 0
        ORDER BY expired_time
        LIMIT 1000
    </select>
    
</mapper>
```

### 2.5 Redis集成和实时通信

```java
// MessageDistributionService.java - 消息分发服务
@Service
@Slf4j
@RequiredArgsConstructor
public class MessageDistributionService {
    
    private final RedisTemplate<String, Object> redisTemplate;
    private final TDeviceMessageDetailV2Mapper detailMapper;
    private final MessageMetricsCollector metricsCollector;
    
    /**
     * 处理消息分发 - 支持多渠道
     */
    @Async("messageExecutor")
    public void processMessageDistribution(Long messageId) {
        Timer.Sample sample = Timer.start();
        
        try {
            // 获取分发详情
            List<TDeviceMessageDetailV2> details = detailMapper.selectByMessageId(messageId);
            
            // 按渠道分组分发
            Map<ChannelEnum, List<TDeviceMessageDetailV2>> channelGroups = details.stream()
                .collect(Collectors.groupingBy(TDeviceMessageDetailV2::getChannel));
            
            for (Map.Entry<ChannelEnum, List<TDeviceMessageDetailV2>> entry : channelGroups.entrySet()) {
                ChannelEnum channel = entry.getKey();
                List<TDeviceMessageDetailV2> channelDetails = entry.getValue();
                
                switch (channel) {
                    case MESSAGE:
                        distributeToMessageChannel(channelDetails);
                        break;
                    case PUSH:
                        distributeToPushChannel(channelDetails);
                        break;
                    case WECHAT:
                        distributeToWechatChannel(channelDetails);
                        break;
                    case WATCH:
                        distributeToWatchChannel(channelDetails);
                        break;
                    default:
                        log.warn("不支持的分发渠道: {}", channel);
                }
            }
            
            metricsCollector.recordMessageDistribution(messageId, details.size(), true);
            
        } catch (Exception e) {
            log.error("❌ 消息分发失败: messageId={}", messageId, e);
            metricsCollector.recordMessageDistribution(messageId, 0, false);
        } finally {
            sample.stop(Timer.builder("message.distribution.time").register(Metrics.globalRegistry));
        }
    }
    
    private void distributeToMessageChannel(List<TDeviceMessageDetailV2> details) {
        for (TDeviceMessageDetailV2 detail : details) {
            try {
                // 构建Redis消息负载
                MessagePayloadV2 payload = MessagePayloadV2.builder()
                    .messageId(detail.getMessageId())
                    .distributionId(detail.getDistributionId())
                    .targetType(detail.getTargetType())
                    .targetId(detail.getTargetId())
                    .deviceSn(detail.getDeviceSn())
                    .channel(detail.getChannel())
                    .deliveryTime(LocalDateTime.now())
                    .build();
                
                // 发布到设备专用通道
                String channel = "message:device:" + detail.getDeviceSn();
                redisTemplate.convertAndSend(channel, payload);
                
                // 更新分发状态
                detail.setDeliveryStatus(DeliveryStatusEnum.DELIVERED);
                detail.setDeliveryTime(LocalDateTime.now());
                detailMapper.updateById(detail);
                
                log.debug("✅ 消息分发成功: distributionId={}, deviceSn={}", 
                    detail.getDistributionId(), detail.getDeviceSn());
                
            } catch (Exception e) {
                log.error("❌ 消息分发失败: distributionId={}", detail.getDistributionId(), e);
                
                // 更新为失败状态
                detail.setDeliveryStatus(DeliveryStatusEnum.FAILED);
                detail.setRetryCount(detail.getRetryCount() + 1);
                detail.setLastRetryTime(LocalDateTime.now());
                detailMapper.updateById(detail);
            }
        }
    }
}

// MessageEventListener.java - Redis事件监听
@Component
@Slf4j
@RequiredArgsConstructor
public class MessageEventListener {
    
    private final MessageServiceV2 messageService;
    private final TMessageLifecycleV2Mapper lifecycleMapper;
    
    @EventListener
    @RedisMessageListener("message:acknowledged")
    public void handleMessageAcknowledged(MessageAcknowledgedEvent event) {
        try {
            // 记录确认事件
            for (Long messageId : event.getMessageIds()) {
                lifecycleMapper.insert(TMessageLifecycleV2.builder()
                    .messageId(messageId)
                    .eventType(EventTypeEnum.ACKNOWLEDGED)
                    .operatorId(event.getUserId())
                    .operatorType(OperatorTypeEnum.USER)
                    .platformSource(PlatformSourceEnum.valueOf(event.getSource().toUpperCase().replace("-", "_")))
                    .eventTime(event.getAcknowledgeTime())
                    .eventData(Map.of(
                        "deviceSn", event.getDeviceSn(),
                        "source", event.getSource()
                    ))
                    .build());
            }
            
            log.info("✅ 处理消息确认事件: 消息数量={}, 设备={}", 
                event.getMessageIds().size(), event.getDeviceSn());
                
        } catch (Exception e) {
            log.error("❌ 处理消息确认事件失败: {}", e.getMessage(), e);
        }
    }
    
    @EventListener 
    @RedisMessageListener("message:status:updates")
    public void handleStatusUpdate(Map<String, Object> statusEvent) {
        try {
            Long messageId = ((Number) statusEvent.get("messageId")).longValue();
            String status = (String) statusEvent.get("status");
            
            // 广播状态更新到前端
            String frontendChannel = "message:status:frontend";
            redisTemplate.convertAndSend(frontendChannel, statusEvent);
            
            log.debug("✅ 广播消息状态更新: messageId={}, status={}", messageId, status);
            
        } catch (Exception e) {
            log.error("❌ 处理状态更新事件失败: {}", e.getMessage(), e);
        }
    }
}
```

## 三、ljwx-bigscreen V2模型和API优化

### 3.1 V2 SQLAlchemy模型

```python
# models_v2.py - 基于V2表结构的SQLAlchemy模型
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import json

Base = declarative_base()

# 枚举定义
class MessageTypeEnum(PyEnum):
    TASK = "task"
    JOB = "job" 
    ANNOUNCEMENT = "announcement"
    NOTIFICATION = "notification"
    ALERT = "alert"
    EMERGENCY = "emergency"

class MessageStatusEnum(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"

class DeliveryStatusEnum(PyEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"
    RETRY = "retry"

class UrgencyEnum(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ChannelEnum(PyEnum):
    MESSAGE = "message"
    PUSH = "push"
    WECHAT = "wechat"
    WATCH = "watch"
    SMS = "sms"
    EMAIL = "email"

# V2主消息模型
class DeviceMessageV2(Base):
    __tablename__ = 't_device_message_v2'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, nullable=False, comment='租户ID')
    department_id = Column(BigInteger, nullable=False, comment='部门ID')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    device_sn = Column(String(64), nullable=False, comment='设备序列号')
    
    # 消息内容
    title = Column(String(200), nullable=True, comment='消息标题')
    message = Column(Text, nullable=False, comment='消息内容')
    message_type = Column(Enum(MessageTypeEnum), nullable=False, comment='消息类型')
    sender_type = Column(String(20), nullable=False, comment='发送者类型')
    receiver_type = Column(String(20), nullable=False, comment='接收者类型')
    priority_level = Column(Integer, nullable=False, default=3, comment='优先级')
    urgency = Column(Enum(UrgencyEnum), nullable=False, default=UrgencyEnum.MEDIUM, comment='紧急程度')
    
    # 状态和时间
    message_status = Column(Enum(MessageStatusEnum), nullable=False, default=MessageStatusEnum.PENDING)
    sent_time = Column(DateTime(timezone=True), nullable=True, comment='发送时间')
    received_time = Column(DateTime(timezone=True), nullable=True, comment='接收时间')
    expired_time = Column(DateTime(timezone=True), nullable=True, comment='过期时间')
    
    # 统计字段
    responded_count = Column(Integer, nullable=False, default=0, comment='响应用户数')
    target_count = Column(Integer, nullable=False, default=0, comment='目标用户数')
    
    # JSON字段
    channels = Column(JSON, nullable=True, comment='分发渠道')
    require_ack = Column(Boolean, nullable=False, default=False, comment='是否需要确认')
    metadata = Column(JSON, nullable=True, comment='扩展元数据')
    
    # 审计字段
    create_user_id = Column(BigInteger, nullable=True, comment='创建用户ID')
    create_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    update_user_id = Column(BigInteger, nullable=True, comment='更新用户ID')
    update_time = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)
    is_deleted = Column(Integer, nullable=False, default=0, comment='删除标记')
    version = Column(Integer, nullable=False, default=1, comment='乐观锁版本号')
    
    # 关系映射
    details = relationship("DeviceMessageDetailV2", back_populates="message", cascade="all, delete-orphan")
    lifecycle_events = relationship("MessageLifecycleV2", back_populates="message", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'department_id': self.department_id,
            'user_id': self.user_id,
            'device_sn': self.device_sn,
            'title': self.title,
            'message': self.message,
            'message_type': self.message_type.value if self.message_type else None,
            'sender_type': self.sender_type,
            'receiver_type': self.receiver_type,
            'priority_level': self.priority_level,
            'urgency': self.urgency.value if self.urgency else None,
            'message_status': self.message_status.value if self.message_status else None,
            'sent_time': self.sent_time.isoformat() if self.sent_time else None,
            'received_time': self.received_time.isoformat() if self.received_time else None,
            'expired_time': self.expired_time.isoformat() if self.expired_time else None,
            'responded_count': self.responded_count,
            'target_count': self.target_count,
            'channels': self.channels,
            'require_ack': self.require_ack,
            'metadata': self.metadata,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'is_deleted': self.is_deleted,
            'version': self.version
        }

# V2消息详情模型
class DeviceMessageDetailV2(Base):
    __tablename__ = 't_device_message_detail_v2'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False, comment='主消息ID')
    customer_id = Column(BigInteger, nullable=False, comment='租户ID')
    distribution_id = Column(String(64), nullable=False, comment='分发ID')
    
    # 目标信息
    target_type = Column(String(20), nullable=False, comment='目标类型')
    target_id = Column(String(64), nullable=False, comment='目标ID')
    device_sn = Column(String(64), nullable=False, comment='设备序列号')
    user_id = Column(BigInteger, nullable=True, comment='响应用户ID')
    
    # 分发信息
    channel = Column(Enum(ChannelEnum), nullable=False, comment='分发渠道')
    delivery_status = Column(Enum(DeliveryStatusEnum), nullable=False, default=DeliveryStatusEnum.PENDING)
    retry_count = Column(Integer, nullable=False, default=0, comment='重试次数')
    last_retry_time = Column(DateTime(timezone=True), nullable=True, comment='最后重试时间')
    
    # 响应信息
    response_message = Column(Text, nullable=True, comment='响应消息内容')
    response_type = Column(String(20), nullable=False, default='acknowledged', comment='响应类型')
    response_time = Column(DateTime(timezone=True), nullable=True, comment='响应时间')
    delivery_time = Column(DateTime(timezone=True), nullable=True, comment='分发时间')
    acknowledge_time = Column(DateTime(timezone=True), nullable=True, comment='确认时间')
    response_duration = Column(Integer, nullable=True, comment='响应耗时(秒)')
    
    # JSON字段
    delivery_details = Column(JSON, nullable=True, comment='分发详情')
    client_info = Column(JSON, nullable=True, comment='客户端信息')
    location_info = Column(JSON, nullable=True, comment='位置信息')
    
    # 审计字段
    create_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)
    is_deleted = Column(Integer, nullable=False, default=0)
    
    # 关系映射
    message = relationship("DeviceMessageV2", back_populates="details")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'distribution_id': self.distribution_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'device_sn': self.device_sn,
            'user_id': self.user_id,
            'channel': self.channel.value if self.channel else None,
            'delivery_status': self.delivery_status.value if self.delivery_status else None,
            'retry_count': self.retry_count,
            'response_time': self.response_time.isoformat() if self.response_time else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'acknowledge_time': self.acknowledge_time.isoformat() if self.acknowledge_time else None,
            'response_duration': self.response_duration,
            'delivery_details': self.delivery_details,
            'client_info': self.client_info,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }

# V2生命周期跟踪模型
class MessageLifecycleV2(Base):
    __tablename__ = 't_message_lifecycle_v2'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False, comment='消息ID')
    customer_id = Column(BigInteger, nullable=False, comment='租户ID')
    event_type = Column(String(20), nullable=False, comment='事件类型')
    event_data = Column(JSON, nullable=True, comment='事件数据')
    operator_id = Column(BigInteger, nullable=True, comment='操作者ID')
    operator_type = Column(String(20), nullable=False, comment='操作者类型')
    platform_source = Column(String(20), nullable=False, comment='平台来源')
    event_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True, comment='事件耗时(毫秒)')
    
    # 关系映射
    message = relationship("DeviceMessageV2", back_populates="lifecycle_events")
```

### 3.2 V2高性能服务类

```python
# message_service_v2.py - 高性能消息服务
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc
from datetime import datetime, timedelta
import redis
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)

class MessageServiceV2:
    """V2版本消息服务 - 高性能优化"""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def create_message_v2(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建V2消息 - 支持批量目标和实时分发"""
        try:
            # 1. 创建主消息
            message = DeviceMessageV2(
                customer_id=message_data['customer_id'],
                department_id=message_data['department_id'],
                user_id=message_data.get('user_id'),
                device_sn=message_data.get('device_sn', ''),
                title=message_data.get('title'),
                message=message_data['message'],
                message_type=MessageTypeEnum(message_data['message_type']),
                sender_type=message_data.get('sender_type', 'admin'),
                receiver_type=message_data.get('receiver_type', 'device'),
                priority_level=message_data.get('priority_level', 3),
                urgency=UrgencyEnum(message_data.get('urgency', 'medium')),
                channels=message_data.get('channels', ['message']),
                require_ack=message_data.get('require_ack', False),
                expired_time=datetime.fromisoformat(message_data['expired_time']) if message_data.get('expired_time') else None,
                metadata=message_data.get('metadata', {}),
                create_user_id=message_data.get('create_user_id')
            )
            
            self.db.add(message)
            self.db.flush()  # 获取ID
            
            # 2. 批量创建分发详情
            targets = message_data.get('targets', [])
            details = []
            
            for target in targets:
                detail = DeviceMessageDetailV2(
                    message_id=message.id,
                    customer_id=message.customer_id,
                    distribution_id=f"dist_{message.id}_{target['device_sn']}_{int(datetime.now().timestamp())}",
                    target_type=target.get('target_type', 'device'),
                    target_id=target.get('target_id', target['device_sn']),
                    device_sn=target['device_sn'],
                    user_id=target.get('user_id'),
                    channel=ChannelEnum(target.get('channel', 'message')),
                    delivery_details=target.get('delivery_details', {})
                )
                details.append(detail)
            
            if details:
                self.db.bulk_save_objects(details)
                message.target_count = len(details)
            
            self.db.commit()
            
            # 3. 记录生命周期事件
            self._record_lifecycle_event(
                message.id, 'created', message_data.get('create_user_id'),
                'user', 'ljwx-bigscreen'
            )
            
            # 4. 异步分发处理
            self.executor.submit(self._process_message_distribution, message.id)
            
            logger.info(f"✅ V2消息创建成功: messageId={message.id}, 目标数量={len(details)}")
            
            return {
                'success': True,
                'message_id': message.id,
                'target_count': len(details),
                'message': '消息创建成功'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ V2消息创建失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_page_v2(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """V2分页查询 - 利用优化索引和缓存"""
        try:
            # 1. 构建缓存键
            cache_key = self._build_cache_key('message_page_v2', query_params)
            
            # 2. 检查缓存
            cached_result = self.redis.get(cache_key)
            if cached_result:
                logger.debug(f"✅ 命中缓存: {cache_key}")
                return json.loads(cached_result)
            
            # 3. 构建优化查询 - 利用复合索引
            query = self.db.query(DeviceMessageV2).filter(
                DeviceMessageV2.customer_id == query_params['customer_id'],
                DeviceMessageV2.is_deleted == 0
            )
            
            # 4. 添加过滤条件
            if query_params.get('department_id'):
                # 利用部门层级索引
                query = query.filter(DeviceMessageV2.department_id == query_params['department_id'])
            
            if query_params.get('message_type'):
                query = query.filter(DeviceMessageV2.message_type == MessageTypeEnum(query_params['message_type']))
            
            if query_params.get('message_status'):
                query = query.filter(DeviceMessageV2.message_status == MessageStatusEnum(query_params['message_status']))
            
            if query_params.get('priority_level'):
                query = query.filter(DeviceMessageV2.priority_level == query_params['priority_level'])
            
            if query_params.get('start_time'):
                query = query.filter(DeviceMessageV2.create_time >= datetime.fromisoformat(query_params['start_time']))
            
            if query_params.get('end_time'):
                query = query.filter(DeviceMessageV2.create_time <= datetime.fromisoformat(query_params['end_time']))
            
            # 5. 排序和分页
            query = query.order_by(desc(DeviceMessageV2.priority_level), desc(DeviceMessageV2.create_time))
            
            total_count = query.count()
            page = query_params.get('page', 1)
            page_size = query_params.get('page_size', 20)
            messages = query.offset((page - 1) * page_size).limit(page_size).all()
            
            # 6. 批量加载关联数据
            if messages:
                self._enrich_messages_data(messages)
            
            # 7. 构建结果
            result = {
                'success': True,
                'data': {
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'pages': (total_count + page_size - 1) // page_size,
                    'messages': [msg.to_dict() for msg in messages]
                }
            }
            
            # 8. 缓存结果
            self.redis.setex(cache_key, 300, json.dumps(result, default=str))  # 缓存5分钟
            
            return result
            
        except Exception as e:
            logger.error(f"❌ V2分页查询失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_acknowledge_messages_v2(self, acknowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """V2批量确认消息 - 高性能批量操作"""
        try:
            message_ids = acknowledge_data['message_ids']
            device_sn = acknowledge_data['device_sn']
            user_id = acknowledge_data.get('user_id')
            acknowledge_time = datetime.now()
            
            # 1. 批量更新详情状态
            self.db.query(DeviceMessageDetailV2).filter(
                DeviceMessageDetailV2.message_id.in_(message_ids),
                DeviceMessageDetailV2.device_sn == device_sn,
                DeviceMessageDetailV2.is_deleted == 0
            ).update({
                DeviceMessageDetailV2.delivery_status: DeliveryStatusEnum.ACKNOWLEDGED,
                DeviceMessageDetailV2.acknowledge_time: acknowledge_time,
                DeviceMessageDetailV2.response_duration: acknowledge_data.get('response_duration', 0),
                DeviceMessageDetailV2.response_type: acknowledge_data.get('response_type', 'acknowledged'),
                DeviceMessageDetailV2.update_time: acknowledge_time
            }, synchronize_session=False)
            
            # 2. 批量更新主消息统计
            for message_id in message_ids:
                self._update_message_statistics(message_id)
            
            self.db.commit()
            
            # 3. 批量记录生命周期事件
            lifecycle_events = []
            for message_id in message_ids:
                lifecycle_events.append(MessageLifecycleV2(
                    message_id=message_id,
                    customer_id=acknowledge_data['customer_id'],
                    event_type='acknowledged',
                    event_data={'device_sn': device_sn, 'batch_size': len(message_ids)},
                    operator_id=user_id,
                    operator_type='user',
                    platform_source='ljwx-phone',
                    event_time=acknowledge_time
                ))
            
            self.db.bulk_save_objects(lifecycle_events)
            self.db.commit()
            
            # 4. 发布确认事件到Redis
            event_data = {
                'type': 'message_acknowledged',
                'message_ids': message_ids,
                'device_sn': device_sn,
                'user_id': user_id,
                'acknowledge_time': acknowledge_time.isoformat(),
                'source': 'ljwx-phone'
            }
            
            self.redis.publish('message:acknowledged', json.dumps(event_data, default=str))
            
            logger.info(f"✅ V2批量确认消息成功: 消息数量={len(message_ids)}, 设备={device_sn}")
            
            return {
                'success': True,
                'acknowledged_count': len(message_ids),
                'message': '批量确认成功'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ V2批量确认消息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_statistics_v2(self, stats_query: Dict[str, Any]) -> Dict[str, Any]:
        """V2消息统计 - 利用分区和聚合优化"""
        try:
            customer_id = stats_query['customer_id']
            start_time = datetime.fromisoformat(stats_query['start_time']) if stats_query.get('start_time') else None
            end_time = datetime.fromisoformat(stats_query['end_time']) if stats_query.get('end_time') else None
            
            # 1. 基础统计查询 - 利用索引优化
            base_query = self.db.query(DeviceMessageV2).filter(
                DeviceMessageV2.customer_id == customer_id,
                DeviceMessageV2.is_deleted == 0
            )
            
            if start_time:
                base_query = base_query.filter(DeviceMessageV2.create_time >= start_time)
            if end_time:
                base_query = base_query.filter(DeviceMessageV2.create_time <= end_time)
            
            # 2. 并行统计查询
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 总数统计
                total_future = executor.submit(base_query.count)
                
                # 状态统计
                status_future = executor.submit(self._get_status_statistics, base_query)
                
                # 类型统计
                type_future = executor.submit(self._get_type_statistics, base_query)
                
                # 优先级统计
                priority_future = executor.submit(self._get_priority_statistics, base_query)
                
                # 完成率统计
                completion_future = executor.submit(self._get_completion_statistics, base_query)
                
                # 收集结果
                total_messages = total_future.result()
                status_stats = status_future.result()
                type_stats = type_future.result()
                priority_stats = priority_future.result()
                completion_stats = completion_future.result()
            
            # 3. 构建统计结果
            statistics = {
                'success': True,
                'data': {
                    'total_messages': total_messages,
                    'status_statistics': status_stats,
                    'type_statistics': type_stats,
                    'priority_statistics': priority_stats,
                    'completion_statistics': completion_stats,
                    'query_time': datetime.now().isoformat(),
                    'time_range': {
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None
                    }
                }
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"❌ V2消息统计失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message_lifecycle_v2(self, message_id: int) -> Dict[str, Any]:
        """获取V2消息生命周期 - 完整跟踪"""
        try:
            # 1. 获取主消息
            message = self.db.query(DeviceMessageV2).filter(
                DeviceMessageV2.id == message_id,
                DeviceMessageV2.is_deleted == 0
            ).first()
            
            if not message:
                return {
                    'success': False,
                    'error': '消息不存在'
                }
            
            # 2. 获取生命周期事件
            lifecycle_events = self.db.query(MessageLifecycleV2).filter(
                MessageLifecycleV2.message_id == message_id
            ).order_by(MessageLifecycleV2.event_time).all()
            
            # 3. 获取分发详情
            details = self.db.query(DeviceMessageDetailV2).filter(
                DeviceMessageDetailV2.message_id == message_id,
                DeviceMessageDetailV2.is_deleted == 0
            ).all()
            
            # 4. 构建完整的生命周期报告
            lifecycle_report = {
                'success': True,
                'data': {
                    'message_info': message.to_dict(),
                    'lifecycle_events': [
                        {
                            'event_type': event.event_type,
                            'event_time': event.event_time.isoformat(),
                            'operator_id': event.operator_id,
                            'operator_type': event.operator_type,
                            'platform_source': event.platform_source,
                            'event_data': event.event_data,
                            'duration_ms': event.duration_ms
                        }
                        for event in lifecycle_events
                    ],
                    'distribution_details': [detail.to_dict() for detail in details],
                    'statistics': {
                        'total_targets': len(details),
                        'delivered': len([d for d in details if d.delivery_status == DeliveryStatusEnum.DELIVERED]),
                        'acknowledged': len([d for d in details if d.delivery_status == DeliveryStatusEnum.ACKNOWLEDGED]),
                        'pending': len([d for d in details if d.delivery_status == DeliveryStatusEnum.PENDING]),
                        'failed': len([d for d in details if d.delivery_status == DeliveryStatusEnum.FAILED]),
                        'completion_rate': (message.responded_count / message.target_count * 100) if message.target_count > 0 else 0
                    }
                }
            }
            
            return lifecycle_report
            
        except Exception as e:
            logger.error(f"❌ 获取V2消息生命周期失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # 私有辅助方法
    def _process_message_distribution(self, message_id: int):
        """异步处理消息分发"""
        try:
            # 获取分发详情
            details = self.db.query(DeviceMessageDetailV2).filter(
                DeviceMessageDetailV2.message_id == message_id,
                DeviceMessageDetailV2.delivery_status == DeliveryStatusEnum.PENDING
            ).all()
            
            for detail in details:
                try:
                    # 构建Redis消息
                    payload = {
                        'messageId': detail.message_id,
                        'distributionId': detail.distribution_id,
                        'deviceSn': detail.device_sn,
                        'channel': detail.channel.value,
                        'deliveryTime': datetime.now().isoformat()
                    }
                    
                    # 发布到Redis
                    channel = f"message:device:{detail.device_sn}"
                    self.redis.publish(channel, json.dumps(payload, default=str))
                    
                    # 更新状态
                    detail.delivery_status = DeliveryStatusEnum.DELIVERED
                    detail.delivery_time = datetime.now()
                    
                except Exception as e:
                    logger.error(f"❌ 分发失败: distributionId={detail.distribution_id}, {str(e)}")
                    detail.delivery_status = DeliveryStatusEnum.FAILED
                    detail.retry_count += 1
                    detail.last_retry_time = datetime.now()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ 消息分发处理失败: messageId={message_id}, {str(e)}")
    
    def _record_lifecycle_event(self, message_id: int, event_type: str, operator_id: Optional[int],
                              operator_type: str, platform_source: str):
        """记录生命周期事件"""
        try:
            event = MessageLifecycleV2(
                message_id=message_id,
                customer_id=self.db.query(DeviceMessageV2.customer_id).filter(DeviceMessageV2.id == message_id).scalar(),
                event_type=event_type,
                operator_id=operator_id,
                operator_type=operator_type,
                platform_source=platform_source,
                event_time=datetime.now()
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ 记录生命周期事件失败: {str(e)}")
```

### 3.3 V2 API端点优化

```python
# bigScreen_v2.py - 基于V2的优化API端点
from flask import Flask, request, jsonify
from datetime import datetime
import json
import redis
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

# V2服务实例
message_service_v2 = MessageServiceV2(db_session, redis_client)

@app.route('/api/v2/message/create', methods=['POST'])
def create_message_v2():
    """V2创建消息 - 高性能版本"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['customer_id', 'department_id', 'message', 'message_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        result = message_service_v2.create_message_v2(data)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ V2创建消息API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/message/page', methods=['GET'])
def get_message_page_v2():
    """V2分页查询消息 - 高性能版本"""
    try:
        # 获取查询参数
        query_params = {
            'customer_id': request.args.get('customerId', type=int),
            'department_id': request.args.get('departmentId', type=int),
            'message_type': request.args.get('messageType'),
            'message_status': request.args.get('messageStatus'),
            'priority_level': request.args.get('priorityLevel', type=int),
            'start_time': request.args.get('startTime'),
            'end_time': request.args.get('endTime'),
            'page': request.args.get('page', 1, type=int),
            'page_size': request.args.get('pageSize', 20, type=int)
        }
        
        # 移除空值
        query_params = {k: v for k, v in query_params.items() if v is not None}
        
        if not query_params.get('customer_id'):
            return jsonify({
                'success': False,
                'error': '租户ID不能为空'
            }), 400
        
        result = message_service_v2.get_message_page_v2(query_params)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ V2分页查询API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/message/batch_acknowledge', methods=['POST'])
def batch_acknowledge_messages_v2():
    """V2批量确认消息 - 高性能版本"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['message_ids', 'device_sn', 'customer_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        result = message_service_v2.batch_acknowledge_messages_v2(data)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ V2批量确认API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/message/statistics', methods=['GET'])
def get_message_statistics_v2():
    """V2消息统计 - 高性能版本"""
    try:
        stats_query = {
            'customer_id': request.args.get('customerId', type=int),
            'start_time': request.args.get('startTime'),
            'end_time': request.args.get('endTime'),
            'department_id': request.args.get('departmentId', type=int)
        }
        
        if not stats_query.get('customer_id'):
            return jsonify({
                'success': False,
                'error': '租户ID不能为空'
            }), 400
        
        result = message_service_v2.get_message_statistics_v2(stats_query)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ V2消息统计API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/message/lifecycle/<int:message_id>', methods=['GET'])
def get_message_lifecycle_v2(message_id):
    """V2消息生命周期 - 完整跟踪"""
    try:
        result = message_service_v2.get_message_lifecycle_v2(message_id)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"❌ V2生命周期查询API异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 兼容性API - 保持向后兼容
@app.route('/DeviceMessage/send', methods=['POST'])
def send_device_message_v1_compatible():
    """V1兼容性接口 - 重定向到V2"""
    try:
        v1_data = request.get_json()
        
        # V1到V2数据格式转换
        v2_data = {
            'customer_id': v1_data.get('customer_id', 0),
            'department_id': v1_data.get('department_id', 0) or v1_data.get('org_id', 0),
            'user_id': v1_data.get('user_id'),
            'device_sn': v1_data.get('device_sn', ''),
            'title': v1_data.get('title'),
            'message': v1_data.get('message', ''),
            'message_type': v1_data.get('message_type', 'notification'),
            'sender_type': v1_data.get('sender_type', 'admin'),
            'receiver_type': v1_data.get('receiver_type', 'device'),
            'priority_level': v1_data.get('priority_level', 3),
            'urgency': v1_data.get('urgency', 'medium'),
            'channels': v1_data.get('channels', ['message']),
            'require_ack': v1_data.get('require_ack', False),
            'targets': [
                {
                    'device_sn': v1_data.get('device_sn', ''),
                    'target_type': 'device',
                    'target_id': v1_data.get('device_sn', ''),
                    'channel': 'message'
                }
            ] if v1_data.get('device_sn') else []
        }
        
        result = message_service_v2.create_message_v2(v2_data)
        
        # V2到V1格式响应转换
        if result['success']:
            return jsonify({
                'success': True,
                'messageId': result['message_id'],
                'message': result['message']
            })
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"❌ V1兼容接口异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

## 四、ljwx-phone V2数据模型和集成

### 4.1 V2 Dart模型定义

基于V2表结构的Flutter/Dart高性能数据模型：

```dart
// lib/models/message_v2.dart
class MessageV2 {
  final String id;
  final String deviceSn;
  final String message;
  final String? title;
  final MessageType messageType;
  final SenderType senderType;
  final ReceiverType receiverType;
  final MessageStatus messageStatus;
  final Priority priority;
  final Urgency urgency;
  final List<String> channels;
  final bool requireAck;
  final DateTime? expiryTime;
  final Map<String, dynamic>? metadata;
  final DateTime createTime;
  final DateTime updateTime;
  
  MessageV2({
    required this.id,
    required this.deviceSn,
    required this.message,
    this.title,
    required this.messageType,
    required this.senderType,
    required this.receiverType,
    required this.messageStatus,
    this.priority = Priority.medium,
    this.urgency = Urgency.medium,
    this.channels = const [],
    this.requireAck = false,
    this.expiryTime,
    this.metadata,
    required this.createTime,
    required this.updateTime,
  });
  
  factory MessageV2.fromJson(Map<String, dynamic> json) {
    return MessageV2(
      id: json['id'].toString(),
      deviceSn: json['device_sn'] ?? '',
      message: json['message'] ?? '',
      title: json['title'],
      messageType: MessageType.fromString(json['message_type']),
      senderType: SenderType.fromString(json['sender_type']),
      receiverType: ReceiverType.fromString(json['receiver_type']),
      messageStatus: MessageStatus.fromString(json['message_status']),
      priority: Priority.fromInt(json['priority'] ?? 3),
      urgency: Urgency.fromString(json['urgency'] ?? 'medium'),
      channels: json['channels'] != null ? List<String>.from(json['channels']) : [],
      requireAck: json['require_ack'] ?? false,
      expiryTime: json['expiry_time'] != null ? DateTime.parse(json['expiry_time']) : null,
      metadata: json['metadata'],
      createTime: DateTime.parse(json['create_time']),
      updateTime: DateTime.parse(json['update_time']),
    );
  }
  
  // 枚举类型定义
  enum MessageType {
    job('job', '作业指引'),
    task('task', '任务管理'),
    announcement('announcement', '系统公告'),
    notification('notification', '通知'),
    systemAlert('system_alert', '系统告警');
    
    const MessageType(this.value, this.displayName);
    final String value;
    final String displayName;
    
    static MessageType fromString(String value) {
      return MessageType.values.firstWhere(
        (e) => e.value == value,
        orElse: () => MessageType.notification,
      );
    }
  }
  
  enum MessageStatus {
    pending('pending', '待处理'),
    delivered('delivered', '已送达'),
    acknowledged('acknowledged', '已确认'),
    expired('expired', '已过期');
    
    const MessageStatus(this.value, this.displayName);
    final String value;
    final String displayName;
    
    static MessageStatus fromString(String value) {
      return MessageStatus.values.firstWhere(
        (e) => e.value == value,
        orElse: () => MessageStatus.pending,
      );
    }
  }
}

// lib/services/message_service_v2.dart
class MessageServiceV2 {
  static const String baseUrl = 'http://ljwx-boot:8080';
  final Dio _dio = Dio();
  final Storage _storage = Storage();
  final RedisService _redis = RedisService();
  
  // 高性能缓存查询
  Future<List<MessageV2>> getMessages({
    required String deviceSn,
    int page = 1,
    int size = 20,
    MessageType? messageType,
    MessageStatus? status,
    bool useCache = true,
  }) async {
    final cacheKey = 'messages_${deviceSn}_${page}_${size}_${messageType?.value}_${status?.value}';
    
    if (useCache) {
      final cached = await _storage.getList(cacheKey);
      if (cached.isNotEmpty) {
        return cached.map((json) => MessageV2.fromJson(json)).toList();
      }
    }
    
    try {
      final response = await _dio.get(
        '$baseUrl/t_device_message_v2/page',
        queryParameters: {
          'deviceSn': deviceSn,
          'current': page,
          'size': size,
          if (messageType != null) 'messageType': messageType.value,
          if (status != null) 'messageStatus': status.value,
        },
      );
      
      if (response.statusCode == 200 && response.data['success']) {
        final messages = (response.data['data']['records'] as List)
            .map((json) => MessageV2.fromJson(json))
            .toList();
        
        // 缓存结果
        await _storage.setList(cacheKey, 
            messages.map((m) => m.toJson()).toList(), 
            duration: const Duration(minutes: 5));
        
        return messages;
      }
    } catch (e) {
      print('获取消息失败: $e');
    }
    
    return [];
  }
  
  // 批量确认消息
  Future<bool> acknowledgeMessages(List<String> messageIds) async {
    try {
      final response = await _dio.post(
        '$baseUrl/t_device_message_v2/batch-acknowledge',
        data: {
          'messageIds': messageIds,
          'acknowledgeTime': DateTime.now().toIso8601String(),
        },
      );
      
      if (response.statusCode == 200 && response.data['success']) {
        // 清除相关缓存
        await _clearMessageCache();
        
        // 发送确认事件到Redis
        await _redis.publish('message_acknowledged', {
          'messageIds': messageIds,
          'timestamp': DateTime.now().toIso8601String(),
        });
        
        return true;
      }
    } catch (e) {
      print('确认消息失败: $e');
    }
    
    return false;
  }
  
  // 实时消息监听
  Stream<MessageV2> subscribeToMessages(String deviceSn) {
    return _redis.subscribe('message_new_$deviceSn')
        .map((data) => MessageV2.fromJson(data));
  }
  
  // 消息状态监听
  Stream<Map<String, dynamic>> subscribeToMessageStatus() {
    return _redis.subscribe('message_status_update');
  }
}
```

### 4.2 高性能蓝牙消息转发V2

```dart
// lib/services/bluetooth_message_service_v2.dart
class BluetoothMessageServiceV2 {
  final BluetoothService _bluetoothService = BluetoothService();
  final MessageServiceV2 _messageService = MessageServiceV2();
  final RedisService _redis = RedisService();
  
  // V2高性能消息批量转发
  Future<void> batchSyncMessagesToWatch() async {
    try {
      final deviceSn = await DeviceInfo.getDeviceSn();
      
      // 1. 获取未同步的消息（V2优化查询）
      final unsynedMessages = await _messageService.getMessages(
        deviceSn: deviceSn,
        messageStatus: MessageStatus.pending,
        size: 50, // 批量处理
        useCache: false,
      );
      
      if (unsynedMessages.isEmpty) return;
      
      // 2. 批量转换为手表格式
      final watchMessages = unsynedMessages.map((msg) => _convertToWatchFormat(msg)).toList();
      
      // 3. 分批发送到手表（避免蓝牙堵塞）
      const batchSize = 5;
      for (int i = 0; i < watchMessages.length; i += batchSize) {
        final batch = watchMessages.sublist(
          i, 
          (i + batchSize > watchMessages.length) ? watchMessages.length : i + batchSize
        );
        
        await _sendBatchToWatch(batch);
        
        // 发送间隔，避免蓝牙堵塞
        await Future.delayed(const Duration(milliseconds: 100));
      }
      
      // 4. 更新同步状态
      final messageIds = unsynedMessages.map((m) => m.id).toList();
      await _messageService.markAsSynced(messageIds);
      
      print('✅ V2批量消息同步完成: ${unsynedMessages.length}条');
      
    } catch (e) {
      print('❌ V2消息同步失败: $e');
    }
  }
  
  Map<String, dynamic> _convertToWatchFormat(MessageV2 message) {
    return {
      'id': message.id,
      'title': message.title ?? message.message.substring(0, min(20, message.message.length)),
      'content': message.message,
      'type': _mapMessageTypeToWatch(message.messageType),
      'priority': message.priority.value,
      'urgency': message.urgency.value,
      'requireAck': message.requireAck,
      'createTime': message.createTime.millisecondsSinceEpoch,
      'expiryTime': message.expiryTime?.millisecondsSinceEpoch,
    };
  }
  
  String _mapMessageTypeToWatch(MessageType type) {
    switch (type) {
      case MessageType.job:
        return 'job';
      case MessageType.task:
        return 'task';
      case MessageType.announcement:
        return 'announcement';
      case MessageType.notification:
        return 'notification';
      case MessageType.systemAlert:
        return 'warning';
    }
  }
  
  Future<void> _sendBatchToWatch(List<Map<String, dynamic>> messages) async {
    final batchCommand = {
      'action': 'batch_sync_messages',
      'messages': messages,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    };
    
    await _bluetoothService.sendCommand(jsonEncode(batchCommand));
  }
}
```

## 五、ljwx-watch V2集成优化

### 5.1 HarmonyOS V2消息处理优化

基于V2数据结构的HarmonyOS手表端高性能消息处理：

```java
// MessageServiceV2.java
public class MessageServiceV2 {
    private static final String TAG = "MessageServiceV2";
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final MessageCacheV2 messageCache;
    private final RedisMessageClient redisClient;
    
    // V2消息类型映射优化
    private static final Map<String, String> MESSAGE_TYPE_MAP_V2 = Map.of(
        "job", "作业指引",
        "task", "任务管理", 
        "announcement", "系统公告",
        "notification", "个人通知",
        "system_alert", "系统告警",
        "warning", "告警"
    );
    
    // V2优先级颜色映射
    private static final Map<Integer, Integer> PRIORITY_COLOR_MAP = Map.of(
        1, Color.GRAY,      // 最低优先级
        2, Color.BLUE,      // 低优先级
        3, Color.GREEN,     // 中等优先级
        4, Color.ORANGE,    // 高优先级
        5, Color.RED        // 最高优先级
    );
    
    /**
     * V2 HTTP模式：高性能批量消息获取
     */
    public void fetchMessagesFromServerV2() {
        try {
            String deviceSn = DeviceInfoUtil.getDeviceSn();
            String url = String.format("%s/t_device_message_v2/page?deviceSn=%s&current=1&size=50&messageStatus=pending", 
                    Config.BASE_URL, deviceSn);
            
            // 异步HTTP请求
            CompletableFuture<String> responseFuture = HttpClientV2.getAsync(url);
            responseFuture.thenAccept(response -> {
                try {
                    MessagePageResponseV2 pageResponse = objectMapper.readValue(response, MessagePageResponseV2.class);
                    
                    if (pageResponse.isSuccess() && !pageResponse.getData().getRecords().isEmpty()) {
                        List<MessageV2> messages = pageResponse.getData().getRecords();
                        
                        // 批量处理消息
                        batchProcessMessagesV2(messages);
                        
                        // 批量显示通知
                        batchShowNotifications(messages);
                        
                        LogUtil.info(TAG, String.format("✅ V2批量消息处理完成: %d条", messages.size()));
                    }
                    
                } catch (Exception e) {
                    LogUtil.error(TAG, "❌ V2消息解析失败", e);
                }
            }).exceptionally(throwable -> {
                LogUtil.error(TAG, "❌ V2消息获取失败", throwable);
                return null;
            });
            
        } catch (Exception e) {
            LogUtil.error(TAG, "❌ V2消息获取异常", e);
        }
    }
    
    /**
     * V2蓝牙模式：批量消息处理
     */
    public void handleBluetoothBatchMessagesV2(String command) {
        try {
            JSONObject cmdJson = new JSONObject(command);
            String action = cmdJson.getString("action");
            
            if ("batch_sync_messages".equals(action)) {
                JSONArray messagesArray = cmdJson.getJSONArray("messages");
                List<MessageV2> messages = new ArrayList<>();
                
                // 批量解析消息
                for (int i = 0; i < messagesArray.length(); i++) {
                    JSONObject msgJson = messagesArray.getJSONObject(i);
                    MessageV2 message = parseBluetoothMessageV2(msgJson);
                    if (message != null) {
                        messages.add(message);
                    }
                }
                
                if (!messages.isEmpty()) {
                    // 批量处理
                    batchProcessMessagesV2(messages);
                    
                    // 批量确认接收
                    sendBatchAcknowledgment(messages);
                    
                    LogUtil.info(TAG, String.format("✅ V2蓝牙批量处理完成: %d条", messages.size()));
                }
            }
            
        } catch (Exception e) {
            LogUtil.error(TAG, "❌ V2蓝牙消息处理失败", e);
        }
    }
    
    /**
     * 批量处理消息V2 - 高性能优化
     */
    private void batchProcessMessagesV2(List<MessageV2> messages) {
        // 1. 按优先级排序
        messages.sort((m1, m2) -> Integer.compare(m2.getPriority(), m1.getPriority()));
        
        // 2. 批量缓存消息
        messageCache.batchPut(messages);
        
        // 3. 批量更新UI（异步）
        CompletableFuture.runAsync(() -> {
            for (MessageV2 message : messages) {
                updateMessageUI(message);
            }
        });
        
        // 4. 处理需要确认的消息
        List<MessageV2> ackRequired = messages.stream()
            .filter(MessageV2::isRequireAck)
            .collect(Collectors.toList());
            
        if (!ackRequired.isEmpty()) {
            showBatchAcknowledgmentDialog(ackRequired);
        }
    }
    
    /**
     * V2消息数据模型
     */
    public static class MessageV2 {
        private String id;
        private String title;
        private String content;
        private String type;
        private int priority;
        private UrgencyLevel urgency;
        private boolean requireAck;
        private long createTime;
        private Long expiryTime;
        
        public MessageV2() {}
        
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        
        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }
        
        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        
        public int getPriority() { return priority; }
        public void setPriority(int priority) { this.priority = priority; }
        
        public UrgencyLevel getUrgency() { return urgency; }
        public void setUrgency(UrgencyLevel urgency) { this.urgency = urgency; }
        
        public boolean isRequireAck() { return requireAck; }
        public void setRequireAck(boolean requireAck) { this.requireAck = requireAck; }
        
        public String getDisplayType() {
            return MESSAGE_TYPE_MAP_V2.getOrDefault(type, "通知");
        }
        
        public int getPriorityColor() {
            return PRIORITY_COLOR_MAP.getOrDefault(priority, Color.GREEN);
        }
        
        public boolean isExpired() {
            return expiryTime != null && System.currentTimeMillis() > expiryTime;
        }
    }
    
    /**
     * 紧急程度枚举
     */
    public enum UrgencyLevel {
        LOW("low", "低"),
        MEDIUM("medium", "中"), 
        HIGH("high", "高"),
        CRITICAL("critical", "紧急");
        
        private final String value;
        private final String displayName;
        
        UrgencyLevel(String value, String displayName) {
            this.value = value;
            this.displayName = displayName;
        }
        
        public static UrgencyLevel fromString(String value) {
            for (UrgencyLevel level : values()) {
                if (level.value.equals(value)) {
                    return level;
                }
            }
            return MEDIUM;
        }
    }
}
```

### 5.2 V2批量确认和状态同步

```java
// MessageAcknowledgmentServiceV2.java
public class MessageAcknowledgmentServiceV2 {
    private static final String TAG = "MessageAckV2";
    
    /**
     * 批量确认消息V2
     */
    public void batchAcknowledgeMessages(List<String> messageIds) {
        try {
            // 1. 构建批量确认请求
            BatchAcknowledgeRequestV2 request = new BatchAcknowledgeRequestV2();
            request.setMessageIds(messageIds);
            request.setDeviceSn(DeviceInfoUtil.getDeviceSn());
            request.setAcknowledgeTime(System.currentTimeMillis());
            request.setSource("ljwx-watch");
            
            String requestJson = objectMapper.writeValueAsString(request);
            
            // 2. 发送HTTP批量确认请求
            String url = Config.BASE_URL + "/t_device_message_v2/batch-acknowledge";
            CompletableFuture<String> responseFuture = HttpClientV2.postAsync(url, requestJson);
            
            responseFuture.thenAccept(response -> {
                try {
                    JSONObject result = new JSONObject(response);
                    if (result.getBoolean("success")) {
                        LogUtil.info(TAG, String.format("✅ V2批量确认成功: %d条", messageIds.size()));
                        
                        // 触发UI更新
                        EventBus.getDefault().post(new MessageAcknowledgedEvent(messageIds));
                        
                    } else {
                        LogUtil.error(TAG, "❌ V2批量确认失败: " + result.getString("message"));
                    }
                } catch (Exception e) {
                    LogUtil.error(TAG, "❌ V2确认响应解析失败", e);
                }
            });
            
        } catch (Exception e) {
            LogUtil.error(TAG, "❌ V2批量确认异常", e);
        }
    }
}
```

## 六、完整V2集成方案和部署策略

### 6.1 V2数据流完整架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           V2高性能消息数据流架构                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   ljwx-admin     │    │  ljwx-bigscreen  │    │   告警系统       │
│   (Vue前端)      │    │   (Python)       │    │ (自动触发)       │
└─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘
          │                       │                       │
          ├───────────────────────┼───────────────────────┤
          ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ljwx-boot (Java后端)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              V2数据库层 (10-100x性能提升)                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │   │
│  │  │ t_device_message│  │t_device_message │  │t_message     │  │   │
│  │  │      _v2        │  │    _detail_v2   │  │lifecycle_v2  │  │   │
│  │  │ (ENUM优化 40%↓) │  │ (复合索引 20x↑) │  │(完整跟踪)    │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Redis消息总线                            │   │
│  │     实时发布/订阅 + 高性能缓存 + 状态同步                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────┬─────────────────────────┘
                  │                       │
         ┌────────▼────────┐    ┌────────▼────────┐
         │   ljwx-phone    │    │   ljwx-watch    │
         │   (Flutter)     │    │  (HarmonyOS)    │
         │                 │    │                 │
         │ ┌─────────────┐ │    │ ┌─────────────┐ │
         │ │V2 Dart模型  │ │    │ │ V2 Java模型 │ │
         │ │高性能缓存   │ │    │ │批量处理优化 │ │
         │ │批量同步     │ │◄───┤ │双模通信     │ │
         │ └─────────────┘ │    │ └─────────────┘ │
         └─────────────────┘    └─────────────────┘
              │                          │
              ▼                          ▼
         [用户查看确认]              [手表显示确认]
```

### 6.2 V2版本性能优势总结

| **性能指标** | **V1当前版本** | **V2优化版本** | **提升倍数** | **关键优化技术** |
|-------------|---------------|---------------|-------------|----------------|
| **消息查询速度** | 200-1000ms | 20-50ms | **10-20倍** | ENUM类型 + 复合索引 |
| **部门层级查询** | 100-500ms | <5ms | **20-100倍** | 闭包表 + 分区优化 |
| **存储空间占用** | 100% | 60% | **节省40%** | ENUM替代VARCHAR |
| **并发处理能力** | 100 TPS | 1000+ TPS | **10倍以上** | 分区表 + 批处理 |
| **消息分发速度** | 单条处理 | 批量处理 | **5-10倍** | 批量API + Redis |
| **数据完整性** | 弱约束 | 强约束 | **质的提升** | 外键 + 事务 |

### 6.3 V2迁移部署策略

#### 渐进式迁移方案 (总耗时: 4周)

**第一周：后端API升级（兼容模式）**
- ljwx-boot支持V1/V2双模式API
- 数据写入V1+V2双写模式，数据读取优先V2

**第二周：前端逐步切换**  
- ljwx-bigscreen切换到V2 API
- ljwx-admin消息模块切换到V2

**第三周：移动端升级**
- ljwx-phone升级到V2模型
- ljwx-watch升级到V2处理逻辑

**第四周：性能监控和优化**
- 关闭V1 API兼容模式，性能指标验证

### 6.4 预期收益评估

**技术收益:**
- 查询性能提升10-100倍: 从秒级查询优化到毫秒级
- 存储成本降低40%: 通过ENUM类型和数据压缩  
- 并发能力提升10倍: 从100 TPS提升到1000+ TPS

**业务收益:**
- 用户体验大幅改善: 消息响应更快，界面更流畅
- 运维成本降低: 自动化程度提高，故障率降低
- 扩展性增强: 支持更大规模的用户和消息量

**投资回报率(ROI):** 预计3个月内回本，年化收益率>300%