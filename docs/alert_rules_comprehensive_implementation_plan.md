# 告警规则系统全流程可落地实施方案

## 📋 方案概述

基于现有系统架构和优化文档，整合告警规则、缓存同步、消息发布等所有优化策略，提供一个完整的、可直接落地的实施方案。

### 🎯 核心目标
- **统一规则管理**: 支持单体征、复合、复杂三类告警规则
- **高效缓存同步**: Redis三层缓存架构，TTL延长至24小时
- **消息发布优化**: 统一消息模型，支持多渠道分发
- **高并发处理**: 异步队列+批量处理，性能提升80%以上
- **管理界面友好**: 可视化规则配置向导

## 🏗️ 整体架构设计

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ljwx-admin    │    │   ljwx-boot     │    │ ljwx-bigscreen  │
│ 规则管理界面    │ ←→ │ 规则引擎+缓存   │ ←→ │ 告警生成+处理   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Vue3配置界面    │    │ Redis缓存同步   │    │ 异步队列处理    │
│ 可视化规则向导  │    │ DB=1 ←pub/sub→ │    │ 三层缓存优化    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据流向
```
告警规则配置 → ljwx-admin → ljwx-boot API → MySQL数据库
                                    ↓
                            Redis发布订阅通知
                                    ↓
                    ljwx-bigscreen订阅更新 → 本地缓存刷新
                                    ↓
                        健康数据上传 → 规则评估引擎
                                    ↓
                        复合条件评估 → 告警生成
                                    ↓
                        消息分发 → 微信/短信/大屏推送
```

## 🗄️ 数据库设计

### 1. 告警规则表优化 (t_alert_rules)

#### 1.1 向下兼容的表结构增强
```sql
-- 保持现有字段，新增扩展字段
ALTER TABLE `t_alert_rules` 
ADD COLUMN `rule_category` ENUM('SINGLE', 'COMPOSITE', 'COMPLEX') DEFAULT 'SINGLE' COMMENT '规则类型：单体征/复合/复杂',
ADD COLUMN `condition_expression` JSON COMMENT '复合条件表达式',
ADD COLUMN `time_window_seconds` INT DEFAULT 300 COMMENT '时间窗口(秒)',
ADD COLUMN `cooldown_seconds` INT DEFAULT 600 COMMENT '告警冷却期(秒)',
ADD COLUMN `priority_level` INT DEFAULT 3 COMMENT '优先级(1-5，数字越小优先级越高)',
ADD COLUMN `rule_tags` JSON COMMENT '规则标签，便于分类管理',
ADD COLUMN `effective_time_start` TIME COMMENT '生效开始时间',
ADD COLUMN `effective_time_end` TIME COMMENT '生效结束时间',
ADD COLUMN `effective_days` VARCHAR(20) DEFAULT '1,2,3,4,5,6,7' COMMENT '生效星期(1-7)',
ADD COLUMN `version` BIGINT DEFAULT 1 COMMENT '规则版本号',
ADD COLUMN `enabled_channels` JSON COMMENT '启用的通知渠道',
ADD INDEX idx_customer_category (`customer_id`, `rule_category`),
ADD INDEX idx_priority (`priority_level`),
ADD INDEX idx_physical_sign_active (`physical_sign`, `is_active`);
```

#### 1.2 规则条件表达式设计
```json
-- 单体征规则 (现有兼容)
{
  "rule_type": "single",
  "physical_sign": "heart_rate",
  "threshold_min": 60,
  "threshold_max": 120,
  "trend_duration": 3
}

-- 复合规则 (新增)
{
  "rule_type": "composite",
  "conditions": [
    {
      "physical_sign": "heart_rate",
      "operator": ">",
      "threshold": 120,
      "duration_seconds": 180
    },
    {
      "physical_sign": "blood_oxygen", 
      "operator": "<",
      "threshold": 90,
      "duration_seconds": 60
    }
  ],
  "logical_operator": "AND",
  "evaluation_window": 300
}

-- 复杂规则 (高级)
{
  "rule_type": "complex",
  "expression": "((heart_rate > 120 AND blood_oxygen < 90) OR (temperature > 38.5)) AND time_of_day BETWEEN '09:00' AND '17:00'",
  "variables": {
    "heart_rate": "health_data.heart_rate",
    "blood_oxygen": "health_data.blood_oxygen",
    "temperature": "health_data.temperature",
    "time_of_day": "CURRENT_TIME"
  }
}
```

### 2. 告警记录表增强 (t_alert_info)
```sql
ALTER TABLE `t_alert_info`
ADD COLUMN `rule_version` BIGINT COMMENT '规则版本',
ADD COLUMN `trigger_conditions` JSON COMMENT '触发条件详情',
ADD COLUMN `evaluation_context` JSON COMMENT '评估上下文',
ADD COLUMN `suppression_key` VARCHAR(128) COMMENT '抑制键',
ADD COLUMN `escalation_level` INT DEFAULT 0 COMMENT '升级级别',
ADD COLUMN `ack_required` BOOLEAN DEFAULT FALSE COMMENT '是否需要确认',
ADD COLUMN `auto_resolve` BOOLEAN DEFAULT FALSE COMMENT '是否自动恢复',
ADD INDEX idx_suppression (`suppression_key`),
ADD INDEX idx_escalation (`escalation_level`),
ADD INDEX idx_rule_version (`rule_id`, `rule_version`);
```

### 3. 缓存同步表 (新增)
```sql
CREATE TABLE `t_alert_cache_sync` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `customer_id` BIGINT NOT NULL,
  `cache_key` VARCHAR(255) NOT NULL,
  `version` BIGINT NOT NULL DEFAULT 1,
  `last_sync_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `sync_status` ENUM('pending', 'synced', 'failed') DEFAULT 'pending',
  `error_message` TEXT,
  UNIQUE KEY uk_customer_cache (`customer_id`, `cache_key`),
  INDEX idx_sync_status (`sync_status`),
  INDEX idx_last_sync (`last_sync_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则缓存同步状态表';
```

## 🚀 后端实现 (ljwx-boot)

### 1. 规则引擎核心类
```java
@Service
@Slf4j
public class AlertRuleEngineService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private TAlertRulesMapper alertRulesMapper;
    
    /**
     * 规则评估主入口
     */
    public List<AlertResult> evaluateRules(HealthDataEvent healthData) {
        String customerId = healthData.getCustomerId();
        
        // 1. 获取缓存的规则
        List<TAlertRules> rules = getCachedRules(customerId);
        
        // 2. 规则预编译和分组
        CompiledRuleSet compiledRules = compileRules(rules);
        
        // 3. 并行评估
        return evaluateRulesParallel(healthData, compiledRules);
    }
    
    /**
     * 三层缓存获取规则
     */
    private List<TAlertRules> getCachedRules(String customerId) {
        String cacheKey = "alert_rules:" + customerId;
        
        // L1: JVM缓存 (5分钟)
        List<TAlertRules> rules = localCache.get(cacheKey);
        if (rules != null) {
            return rules;
        }
        
        // L2: Redis缓存 (24小时)
        rules = (List<TAlertRules>) redisTemplate.opsForValue().get(cacheKey);
        if (rules != null) {
            localCache.put(cacheKey, rules);
            return rules;
        }
        
        // L3: 数据库
        rules = alertRulesMapper.selectByCustomerId(Long.valueOf(customerId));
        
        // 回填缓存
        redisTemplate.opsForValue().set(cacheKey, rules, Duration.ofHours(24));
        localCache.put(cacheKey, rules);
        
        return rules;
    }
    
    /**
     * 规则预编译
     */
    private CompiledRuleSet compileRules(List<TAlertRules> rules) {
        CompiledRuleSet compiledRules = new CompiledRuleSet();
        
        for (TAlertRules rule : rules) {
            if (!rule.getIsActive()) continue;
            
            switch (rule.getRuleCategory()) {
                case SINGLE:
                    compiledRules.addSingleRule(compileSingleRule(rule));
                    break;
                case COMPOSITE:
                    compiledRules.addCompositeRule(compileCompositeRule(rule));
                    break;
                case COMPLEX:
                    compiledRules.addComplexRule(compileComplexRule(rule));
                    break;
            }
        }
        
        return compiledRules;
    }
    
    /**
     * 并行规则评估
     */
    private List<AlertResult> evaluateRulesParallel(HealthDataEvent healthData, CompiledRuleSet compiledRules) {
        List<CompletableFuture<List<AlertResult>>> futures = new ArrayList<>();
        
        // 单体征规则并行评估
        futures.add(CompletableFuture.supplyAsync(() -> 
            evaluateSingleRules(healthData, compiledRules.getSingleRules())));
        
        // 复合规则并行评估
        futures.add(CompletableFuture.supplyAsync(() -> 
            evaluateCompositeRules(healthData, compiledRules.getCompositeRules())));
        
        // 复杂规则并行评估
        futures.add(CompletableFuture.supplyAsync(() -> 
            evaluateComplexRules(healthData, compiledRules.getComplexRules())));
        
        // 合并结果
        return futures.stream()
            .map(CompletableFuture::join)
            .flatMap(List::stream)
            .collect(Collectors.toList());
    }
}
```

### 2. 缓存同步增强版
```java
@Component
@Slf4j
public class AlertRulesCacheManager {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private TAlertCacheSyncMapper cacheSyncMapper;
    
    /**
     * 更新告警规则缓存 - 增强版本
     */
    @Transactional
    public void updateAlertRulesCache(Long customerId) {
        String lockKey = "alert_rules_lock_" + customerId;
        
        // 分布式锁
        Boolean lockAcquired = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "locked", Duration.ofMinutes(5));
        
        if (!lockAcquired) {
            log.warn("获取分布式锁失败: {}", lockKey);
            return;
        }
        
        try {
            // 1. 查询最新规则
            List<TAlertRules> rules = alertRulesMapper.selectByCustomerId(customerId);
            
            // 2. 增加版本号
            Long version = redisTemplate.opsForValue().increment("alert_rules_version_" + customerId);
            
            // 3. 构建缓存数据
            CacheData cacheData = CacheData.builder()
                .version(version)
                .rules(rules)
                .updateTime(System.currentTimeMillis())
                .customerId(customerId)
                .build();
            
            // 4. 更新Redis缓存
            String cacheKey = "alert_rules_" + customerId;
            redisTemplate.opsForValue().set(cacheKey, cacheData, Duration.ofHours(24));
            
            // 5. 发布更新通知
            String message = String.format("update:%s:%s", customerId, version);
            redisTemplate.convertAndSend("alert_rules_channel", message);
            
            // 6. 记录同步状态
            updateSyncStatus(customerId, cacheKey, version, "synced", null);
            
            log.info("告警规则缓存更新成功: customerId={}, version={}", customerId, version);
            
        } catch (Exception e) {
            log.error("告警规则缓存更新失败: customerId={}", customerId, e);
            updateSyncStatus(customerId, "alert_rules_" + customerId, 0L, "failed", e.getMessage());
            throw e;
        } finally {
            redisTemplate.delete(lockKey);
        }
    }
    
    /**
     * 批量更新缓存 - 性能优化
     */
    public void batchUpdateCache(List<Long> customerIds) {
        // 分批处理，避免阻塞
        int batchSize = 10;
        for (int i = 0; i < customerIds.size(); i += batchSize) {
            List<Long> batch = customerIds.subList(i, Math.min(i + batchSize, customerIds.size()));
            
            CompletableFuture.runAsync(() -> {
                batch.parallelStream().forEach(this::updateAlertRulesCache);
            });
        }
    }
    
    private void updateSyncStatus(Long customerId, String cacheKey, Long version, String status, String errorMessage) {
        TAlertCacheSync syncRecord = TAlertCacheSync.builder()
            .customerId(customerId)
            .cacheKey(cacheKey)
            .version(version)
            .lastSyncTime(LocalDateTime.now())
            .syncStatus(status)
            .errorMessage(errorMessage)
            .build();
        
        cacheSyncMapper.insertOrUpdate(syncRecord);
    }
}
```

### 3. 统一消息发布器
```java
@Service
@Slf4j
public class UnifiedMessagePublisher {
    
    @Autowired
    private WeChatNotifier weChatNotifier;
    
    @Autowired
    private SmsNotifier smsNotifier;
    
    @Autowired
    private WebSocketNotifier webSocketNotifier;
    
    @Autowired
    private MessageQueueProducer messageProducer;
    
    /**
     * 统一消息发布入口
     */
    public void publishAlert(AlertMessage alertMessage) {
        // 1. 消息预处理
        UnifiedMessage unifiedMessage = buildUnifiedMessage(alertMessage);
        
        // 2. 渠道路由
        List<NotificationChannel> channels = routeChannels(alertMessage);
        
        // 3. 并行发送
        List<CompletableFuture<NotificationResult>> futures = channels.stream()
            .map(channel -> CompletableFuture.supplyAsync(() -> 
                sendToChannel(unifiedMessage, channel)))
            .collect(Collectors.toList());
        
        // 4. 结果汇总
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenRun(() -> {
                List<NotificationResult> results = futures.stream()
                    .map(CompletableFuture::join)
                    .collect(Collectors.toList());
                
                logResults(alertMessage, results);
            });
    }
    
    /**
     * 构建统一消息模型
     */
    private UnifiedMessage buildUnifiedMessage(AlertMessage alertMessage) {
        return UnifiedMessage.builder()
            .messageId(generateMessageId())
            .messageType("alert")
            .subType(alertMessage.getAlertType())
            .title(buildTitle(alertMessage))
            .content(buildContent(alertMessage))
            .priority(mapPriority(alertMessage.getSeverityLevel()))
            .urgency(mapUrgency(alertMessage.getSeverityLevel()))
            .sender(buildSender())
            .target(buildTarget(alertMessage))
            .delivery(buildDelivery(alertMessage))
            .metadata(buildMetadata(alertMessage))
            .build();
    }
    
    /**
     * 渠道智能路由
     */
    private List<NotificationChannel> routeChannels(AlertMessage alertMessage) {
        List<NotificationChannel> channels = new ArrayList<>();
        
        // 基于严重程度决定渠道
        String severity = alertMessage.getSeverityLevel();
        List<String> enabledChannels = alertMessage.getEnabledChannels();
        
        if (enabledChannels.contains("wechat")) {
            channels.add(NotificationChannel.WECHAT);
        }
        
        if (enabledChannels.contains("message")) {
            channels.add(NotificationChannel.INTERNAL_MESSAGE);
        }
        
        // Critical级别强制WebSocket推送
        if ("critical".equals(severity)) {
            channels.add(NotificationChannel.WEBSOCKET);
        }
        
        // 高优先级添加短信通道
        if (Arrays.asList("critical", "high").contains(severity) && 
            enabledChannels.contains("sms")) {
            channels.add(NotificationChannel.SMS);
        }
        
        return channels;
    }
    
    /**
     * 发送到指定渠道
     */
    private NotificationResult sendToChannel(UnifiedMessage message, NotificationChannel channel) {
        try {
            switch (channel) {
                case WECHAT:
                    return weChatNotifier.send(message);
                case SMS:
                    return smsNotifier.send(message);
                case WEBSOCKET:
                    return webSocketNotifier.send(message);
                case INTERNAL_MESSAGE:
                    return insertInternalMessage(message);
                default:
                    return NotificationResult.failed("未知渠道");
            }
        } catch (Exception e) {
            log.error("发送消息失败: channel={}, messageId={}", channel, message.getMessageId(), e);
            return NotificationResult.failed(e.getMessage());
        }
    }
}
```

## 🔧 前端实现 (ljwx-bigscreen优化)

### 1. 缓存订阅管理器增强
```python
class AlertRulesCacheSubscriber:
    """增强版Redis缓存订阅管理器"""
    
    def __init__(self):
        self.redis_bigscreen = RedisHelper()  # DB=0
        self.redis_boot = redis.Redis(host='127.0.0.1', port=6379, password='123456', db=1)  # DB=1
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'updates': 0,
            'errors': 0
        }
        self.running = True
        
    def start_subscriber(self):
        """启动缓存订阅器"""
        def subscriber_thread():
            pubsub = self.redis_bigscreen.pubsub()
            pubsub.subscribe('alert_rules_channel')
            
            logger.info("告警规则缓存订阅器已启动")
            
            for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    self.handle_cache_update(message['data'])
                    
        Thread(target=subscriber_thread, daemon=True).start()
    
    def handle_cache_update(self, message):
        """处理缓存更新消息 - 增强版本"""
        try:
            # 解析消息: "update:customer_id:version"
            parts = message.decode('utf-8').split(':')
            if len(parts) >= 2 and parts[0] == 'update':
                customer_id = parts[1]
                version = int(parts[2]) if len(parts) > 2 else 0
                
                # 检查是否需要更新
                if self.should_update_cache(customer_id, version):
                    success = self.refresh_local_cache(customer_id)
                    if success:
                        self.cache_stats['updates'] += 1
                        logger.info(f"缓存更新成功: customer_id={customer_id}, version={version}")
                    else:
                        self.cache_stats['errors'] += 1
                        
        except Exception as e:
            self.cache_stats['errors'] += 1
            logger.error(f"处理缓存更新失败: {e}")
    
    def get_alert_rules(self, customer_id):
        """三层缓存获取告警规则 - 性能优化"""
        cache_key = f"rules:{customer_id}"
        
        # L1: 内存缓存
        if cache_key in self.local_cache:
            cached_data = self.local_cache[cache_key]
            if time.time() - cached_data['timestamp'] < 300:  # 5分钟有效
                self.cache_stats['hits'] += 1
                return cached_data['rules']
        
        self.cache_stats['misses'] += 1
        
        # L2: ljwx-boot Redis缓存
        try:
            boot_cache_key = f"alert_rules_{customer_id}"
            cached_data = self.redis_boot.get(boot_cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                rules = data.get('rules', [])
                
                # 更新L1缓存
                self.local_cache[cache_key] = {
                    'rules': rules,
                    'timestamp': time.time(),
                    'version': data.get('version', 0)
                }
                
                return rules
                
        except Exception as e:
            logger.error(f"从ljwx-boot Redis获取规则失败: {e}")
        
        # L3: 数据库兜底
        try:
            return self.get_rules_from_database(customer_id)
        except Exception as e:
            logger.error(f"数据库兜底查询失败: {e}")
            return []
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_hits': self.cache_stats['hits'],
            'total_misses': self.cache_stats['misses'],
            'cache_updates': self.cache_stats['updates'],
            'cache_errors': self.cache_stats['errors'],
            'local_cache_size': len(self.local_cache)
        }
```

### 2. 高性能告警生成器
```python
class HighPerformanceAlertGenerator:
    """高性能告警生成器 - 异步队列处理"""
    
    def __init__(self):
        self.alert_queue = asyncio.Queue(maxsize=10000)
        self.batch_size = 100
        self.max_wait_time = 2.0
        self.workers = []
        self.rule_engine = AlertRuleEngine()
        self.cache_subscriber = AlertRulesCacheSubscriber()
        
        # 性能统计
        self.performance_stats = {
            'total_processed': 0,
            'total_generated': 0,
            'avg_processing_time': 0.0,
            'queue_size': 0,
            'cache_hit_rate': 0.0
        }
    
    async def start_workers(self, worker_count=4):
        """启动异步工作者"""
        for i in range(worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        # 启动缓存订阅器
        self.cache_subscriber.start_subscriber()
        
        logger.info(f"告警生成器已启动 {worker_count} 个工作者")
    
    async def submit_health_data(self, health_data, health_data_id=None):
        """提交健康数据到处理队列"""
        try:
            item = {
                'health_data': health_data,
                'health_data_id': health_data_id,
                'timestamp': time.time(),
                'device_sn': health_data.get('deviceSn', '')
            }
            
            await self.alert_queue.put(item)
            return True
            
        except asyncio.QueueFull:
            logger.warning("告警处理队列已满，丢弃请求")
            return False
    
    async def _worker_loop(self, worker_name):
        """工作者主循环"""
        batch = []
        last_process_time = time.time()
        
        while True:
            try:
                # 收集批次
                while len(batch) < self.batch_size and (time.time() - last_process_time) < self.max_wait_time:
                    try:
                        item = await asyncio.wait_for(self.alert_queue.get(), timeout=0.5)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                # 处理批次
                if batch:
                    await self._process_batch(batch, worker_name)
                    batch.clear()
                    last_process_time = time.time()
                    
            except Exception as e:
                logger.error(f"{worker_name} 异常: {e}")
                batch.clear()
    
    async def _process_batch(self, health_data_batch, worker_name):
        """批量处理健康数据"""
        start_time = time.time()
        processed_count = 0
        generated_alerts = 0
        
        try:
            # 按customer_id分组批次
            customer_batches = defaultdict(list)
            for item in health_data_batch:
                customer_id = item['health_data'].get('customer_id') or item['health_data'].get('customerId')
                customer_batches[customer_id].append(item)
            
            # 并行处理每个客户的数据
            tasks = []
            for customer_id, customer_data in customer_batches.items():
                task = self._process_customer_batch(customer_id, customer_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            for result in results:
                if isinstance(result, dict):
                    processed_count += result.get('processed', 0)
                    generated_alerts += result.get('generated', 0)
            
        except Exception as e:
            logger.error(f"{worker_name} 批量处理异常: {e}")
        
        # 更新性能统计
        processing_time = time.time() - start_time
        self.performance_stats['total_processed'] += processed_count
        self.performance_stats['total_generated'] += generated_alerts
        self.performance_stats['avg_processing_time'] = (
            self.performance_stats['avg_processing_time'] * 0.9 + processing_time * 0.1
        )
        self.performance_stats['queue_size'] = self.alert_queue.qsize()
        
        logger.info(f"{worker_name} 批量处理完成: 处理{processed_count}条, 生成告警{generated_alerts}条, 耗时{processing_time:.3f}s")
    
    async def _process_customer_batch(self, customer_id, health_data_list):
        """处理单个客户的健康数据批次"""
        try:
            # 1. 批量获取规则（一次查询）
            rules = self.cache_subscriber.get_alert_rules(customer_id)
            if not rules:
                return {'processed': len(health_data_list), 'generated': 0}
            
            # 2. 编译规则（一次编译）
            compiled_rules = self.rule_engine.compile_rules(rules)
            
            # 3. 批量评估
            generated_alerts = 0
            for item in health_data_list:
                alerts = await self.rule_engine.evaluate_rules_async(
                    item['health_data'], 
                    item['health_data_id'], 
                    compiled_rules
                )
                generated_alerts += len(alerts)
            
            return {'processed': len(health_data_list), 'generated': generated_alerts}
            
        except Exception as e:
            logger.error(f"处理客户批次失败: customer_id={customer_id}, error={e}")
            return {'processed': 0, 'generated': 0}
    
    def get_performance_stats(self):
        """获取性能统计"""
        cache_stats = self.cache_subscriber.get_cache_stats()
        self.performance_stats['cache_hit_rate'] = cache_stats['hit_rate']
        
        return {
            **self.performance_stats,
            'cache_stats': cache_stats
        }
```

### 3. 复合规则引擎
```python
class AlertRuleEngine:
    """告警规则引擎 - 支持复合条件"""
    
    def __init__(self):
        self.condition_cache = {}
        self.evaluation_history = defaultdict(list)
        
    def compile_rules(self, rules):
        """规则预编译"""
        compiled_rules = {
            'single_rules': defaultdict(list),
            'composite_rules': [],
            'complex_rules': [],
            'priority_index': defaultdict(list)
        }
        
        for rule in rules:
            if not rule.get('is_active', True):
                continue
            
            rule_category = rule.get('rule_category', 'SINGLE')
            priority = rule.get('priority_level', 5)
            
            if rule_category == 'SINGLE':
                physical_sign = rule.get('physical_sign')
                if physical_sign:
                    compiled_rule = self._compile_single_rule(rule)
                    compiled_rules['single_rules'][physical_sign].append(compiled_rule)
                    compiled_rules['priority_index'][priority].append(compiled_rule)
                    
            elif rule_category == 'COMPOSITE':
                compiled_rule = self._compile_composite_rule(rule)
                if compiled_rule:
                    compiled_rules['composite_rules'].append(compiled_rule)
                    compiled_rules['priority_index'][priority].append(compiled_rule)
                    
            elif rule_category == 'COMPLEX':
                compiled_rule = self._compile_complex_rule(rule)
                if compiled_rule:
                    compiled_rules['complex_rules'].append(compiled_rule)
                    compiled_rules['priority_index'][priority].append(compiled_rule)
        
        return compiled_rules
    
    async def evaluate_rules_async(self, health_data, health_data_id, compiled_rules):
        """异步规则评估"""
        triggered_alerts = []
        device_sn = health_data.get('deviceSn', '')
        
        try:
            # 1. 按优先级评估
            for priority in sorted(compiled_rules['priority_index'].keys()):
                priority_rules = compiled_rules['priority_index'][priority]
                
                for rule in priority_rules:
                    # 检查生效时间
                    if not self._is_rule_effective(rule):
                        continue
                    
                    # 根据规则类型评估
                    alert = None
                    if rule['type'] == 'single':
                        alert = await self._evaluate_single_rule_async(rule, health_data, health_data_id)
                    elif rule['type'] == 'composite':
                        alert = await self._evaluate_composite_rule_async(rule, health_data, health_data_id)
                    elif rule['type'] == 'complex':
                        alert = await self._evaluate_complex_rule_async(rule, health_data, health_data_id)
                    
                    if alert:
                        # 检查告警抑制
                        if not self._is_suppressed(alert, rule):
                            triggered_alerts.append(alert)
                            # 设置冷却期
                            self._set_cooldown(alert, rule)
            
            # 2. 批量保存告警
            if triggered_alerts:
                await self._save_alerts_batch(triggered_alerts)
            
        except Exception as e:
            logger.error(f"规则评估异常: device_sn={device_sn}, error={e}")
        
        return triggered_alerts
    
    async def _evaluate_composite_rule_async(self, rule, health_data, health_data_id):
        """复合规则异步评估"""
        try:
            condition_expr = rule.get('condition_expression', {})
            conditions = condition_expr.get('conditions', [])
            logical_op = condition_expr.get('logical_operator', 'AND')
            
            if not conditions:
                return None
            
            # 并行评估所有条件
            condition_tasks = []
            for condition in conditions:
                task = self._evaluate_condition_async(condition, health_data)
                condition_tasks.append(task)
            
            condition_results = await asyncio.gather(*condition_tasks)
            
            # 逻辑组合
            if logical_op == 'AND':
                final_result = all(condition_results)
            elif logical_op == 'OR':
                final_result = any(condition_results)
            else:
                final_result = False
            
            if final_result:
                return await self._create_alert_async(rule, health_data, health_data_id, {
                    'condition_results': condition_results,
                    'trigger_type': 'composite'
                })
            
        except Exception as e:
            logger.error(f"复合规则评估失败: rule_id={rule.get('id')}, error={e}")
        
        return None
    
    async def _evaluate_condition_async(self, condition, health_data):
        """异步条件评估"""
        try:
            physical_sign = condition['physical_sign']
            operator = condition['operator']
            threshold = condition['threshold']
            duration = condition.get('duration_seconds', 0)
            
            value = health_data.get(physical_sign)
            if value is None:
                return False
            
            # 基础条件检查
            condition_met = self._check_condition(float(value), operator, threshold)
            
            # 持续时间检查
            if condition_met and duration > 0:
                condition_met = await self._check_duration_async(
                    health_data, physical_sign, operator, threshold, duration
                )
            
            return condition_met
            
        except Exception as e:
            logger.error(f"条件评估失败: condition={condition}, error={e}")
            return False
    
    def _check_condition(self, value, operator, threshold):
        """检查单个条件"""
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return value == threshold
        else:
            return False
    
    async def _check_duration_async(self, health_data, physical_sign, operator, threshold, duration):
        """异步检查持续时间条件"""
        device_sn = health_data.get('deviceSn', '')
        condition_key = f"{device_sn}:{physical_sign}:{operator}:{threshold}"
        
        # 获取历史评估记录
        history = self.evaluation_history[condition_key]
        current_time = time.time()
        
        # 清理过期记录
        history[:] = [t for t in history if current_time - t < duration]
        
        # 添加当前时间
        history.append(current_time)
        
        # 检查是否满足持续时间要求
        return len(history) >= 3  # 至少3次连续满足条件
    
    async def _save_alerts_batch(self, alerts):
        """批量保存告警"""
        try:
            for alert in alerts:
                alert_info = AlertInfo(
                    rule_id=alert['rule_id'],
                    alert_type=alert['alert_type'],
                    device_sn=alert['device_sn'],
                    alert_desc=alert['alert_desc'],
                    severity_level=alert['severity_level'],
                    alert_status='pending',
                    alert_timestamp=get_now(),
                    health_id=alert.get('health_data_id'),
                    user_id=alert.get('user_id'),
                    org_id=alert.get('org_id'),
                    latitude=alert.get('latitude'),
                    longitude=alert.get('longitude'),
                    trigger_conditions=json.dumps(alert.get('trigger_conditions', {})),
                    evaluation_context=json.dumps(alert.get('evaluation_context', {}))
                )
                db.session.add(alert_info)
            
            db.session.commit()
            logger.info(f"批量保存告警成功: {len(alerts)}条")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"批量保存告警失败: {e}")
```

## 🎨 前端管理界面 (ljwx-admin)

### 1. 规则配置向导组件
```vue
<template>
  <div class="alert-rule-wizard">
    <!-- 步骤导航 -->
    <el-steps :active="currentStep" align-center>
      <el-step title="基础信息" />
      <el-step title="规则类型" />
      <el-step title="条件配置" />
      <el-step title="通知设置" />
      <el-step title="生效时间" />
      <el-step title="预览确认" />
    </el-steps>
    
    <!-- 基础信息步骤 -->
    <div v-show="currentStep === 0" class="step-content">
      <el-card header="基础信息">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="规则名称" required>
            <el-input v-model="ruleConfig.ruleName" placeholder="请输入规则名称" />
          </el-form-item>
          
          <el-form-item label="规则描述">
            <el-input type="textarea" v-model="ruleConfig.ruleDescription" 
                     placeholder="请描述此规则的用途" />
          </el-form-item>
          
          <el-form-item label="优先级">
            <el-select v-model="ruleConfig.priorityLevel">
              <el-option label="最高 (1)" :value="1" />
              <el-option label="高 (2)" :value="2" />
              <el-option label="中 (3)" :value="3" />
              <el-option label="低 (4)" :value="4" />
              <el-option label="最低 (5)" :value="5" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="规则标签">
            <el-tag v-for="tag in ruleConfig.ruleTags" :key="tag" closable 
                    @close="removeTag(tag)">{{ tag }}</el-tag>
            <el-input v-model="newTag" @keyup.enter="addTag" 
                     placeholder="输入标签按回车添加" style="width: 200px; margin-left: 10px;" />
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 规则类型选择 -->
    <div v-show="currentStep === 1" class="step-content">
      <el-card header="选择规则类型">
        <div class="rule-type-grid">
          <div class="rule-type-card" 
               :class="{ active: ruleConfig.ruleCategory === 'SINGLE' }"
               @click="selectRuleType('SINGLE')">
            <el-icon><Monitor /></el-icon>
            <h3>单体征规则</h3>
            <p>基于单个生理指标的阈值告警</p>
            <div class="example">例：心率 > 120 连续3次</div>
          </div>
          
          <div class="rule-type-card" 
               :class="{ active: ruleConfig.ruleCategory === 'COMPOSITE' }"
               @click="selectRuleType('COMPOSITE')">
            <el-icon><Connection /></el-icon>
            <h3>复合规则</h3>
            <p>多个生理指标的组合条件</p>
            <div class="example">例：心率 > 120 且 血氧 < 90</div>
          </div>
          
          <div class="rule-type-card" 
               :class="{ active: ruleConfig.ruleCategory === 'COMPLEX' }"
               @click="selectRuleType('COMPLEX')">
            <el-icon><Setting /></el-icon>
            <h3>复杂规则</h3>
            <p>高级逻辑表达式和自定义公式</p>
            <div class="example">例：自定义算法判断</div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 单体征条件配置 -->
    <div v-show="currentStep === 2 && ruleConfig.ruleCategory === 'SINGLE'" class="step-content">
      <el-card header="单体征条件配置">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="生理指标">
            <el-select v-model="ruleConfig.physicalSign" placeholder="选择生理指标">
              <el-option v-for="sign in physicalSigns" :key="sign.value" 
                        :label="sign.label" :value="sign.value">
                <span style="float: left">{{ sign.label }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ sign.unit }}</span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="正常范围">
            <div class="threshold-range">
              <el-input-number v-model="ruleConfig.thresholdMin" placeholder="最小值" />
              <span class="range-separator">至</span>
              <el-input-number v-model="ruleConfig.thresholdMax" placeholder="最大值" />
              <span class="unit">{{ getSelectedSignUnit() }}</span>
            </div>
          </el-form-item>
          
          <el-form-item label="连续异常次数">
            <el-input-number v-model="ruleConfig.trendDuration" :min="1" />
            <span class="help-text">连续超出阈值多少次后触发告警</span>
          </el-form-item>
          
          <el-form-item label="时间窗口">
            <el-input-number v-model="ruleConfig.timeWindowSeconds" :min="60" />
            <span class="help-text">秒，在此时间窗口内统计异常次数</span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 复合条件配置 -->
    <div v-show="currentStep === 2 && ruleConfig.ruleCategory === 'COMPOSITE'" class="step-content">
      <el-card header="复合条件配置">
        <div class="composite-conditions">
          <div v-for="(condition, index) in compositeConditions" :key="index" 
               class="condition-item">
            <div class="condition-row">
              <el-select v-model="condition.physicalSign" placeholder="生理指标">
                <el-option v-for="sign in physicalSigns" :key="sign.value"
                          :label="sign.label" :value="sign.value" />
              </el-select>
              
              <el-select v-model="condition.operator" placeholder="运算符">
                <el-option label="大于 >" value=">" />
                <el-option label="小于 <" value="<" />
                <el-option label="等于 =" value="=" />
                <el-option label="大于等于 >=" value=">=" />
                <el-option label="小于等于 <=" value="<=" />
              </el-select>
              
              <el-input-number v-model="condition.threshold" placeholder="阈值" />
              
              <el-input-number v-model="condition.durationSeconds" 
                              placeholder="持续时间(秒)" :min="0" />
              
              <el-button @click="removeCondition(index)" type="danger" 
                        icon="el-icon-delete" circle />
            </div>
            
            <!-- 逻辑连接符 -->
            <div v-if="index < compositeConditions.length - 1" class="logic-connector">
              <el-radio-group v-model="logicalOperator">
                <el-radio-button label="AND">并且</el-radio-button>
                <el-radio-button label="OR">或者</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          
          <el-button @click="addCondition" type="primary" icon="el-icon-plus">
            添加条件
          </el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 通知设置 -->
    <div v-show="currentStep === 3" class="step-content">
      <el-card header="通知设置">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="严重程度">
            <el-select v-model="ruleConfig.severityLevel">
              <el-option label="低 (Low)" value="low" />
              <el-option label="中 (Medium)" value="medium" />
              <el-option label="高 (High)" value="high" />
              <el-option label="紧急 (Critical)" value="critical" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="通知渠道">
            <el-checkbox-group v-model="ruleConfig.enabledChannels">
              <el-checkbox label="wechat">微信通知</el-checkbox>
              <el-checkbox label="message">内部消息</el-checkbox>
              <el-checkbox label="sms">短信通知</el-checkbox>
              <el-checkbox label="email">邮件通知</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="告警消息模板">
            <el-input type="textarea" v-model="ruleConfig.alertMessage" 
                     placeholder="可使用变量: {user_name}, {device_sn}, {value}, {threshold}" />
          </el-form-item>
          
          <el-form-item label="冷却期">
            <el-input-number v-model="ruleConfig.cooldownSeconds" :min="0" />
            <span class="help-text">秒，避免重复告警的冷却时间</span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 生效时间 -->
    <div v-show="currentStep === 4" class="step-content">
      <el-card header="生效时间设置">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="生效时间段">
            <el-time-picker v-model="effectiveTimeRange" is-range 
                           range-separator="至" format="HH:mm" />
          </el-form-item>
          
          <el-form-item label="生效星期">
            <el-checkbox-group v-model="ruleConfig.effectiveDays">
              <el-checkbox label="1">周一</el-checkbox>
              <el-checkbox label="2">周二</el-checkbox>
              <el-checkbox label="3">周三</el-checkbox>
              <el-checkbox label="4">周四</el-checkbox>
              <el-checkbox label="5">周五</el-checkbox>
              <el-checkbox label="6">周六</el-checkbox>
              <el-checkbox label="7">周日</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="立即生效">
            <el-switch v-model="ruleConfig.isActive" />
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 预览确认 -->
    <div v-show="currentStep === 5" class="step-content">
      <el-card header="规则预览">
        <div class="rule-preview">
          <div class="preview-section">
            <h4>基础信息</h4>
            <p><strong>规则名称：</strong>{{ ruleConfig.ruleName }}</p>
            <p><strong>规则类型：</strong>{{ getRuleTypeText() }}</p>
            <p><strong>优先级：</strong>{{ getPriorityText() }}</p>
          </div>
          
          <div class="preview-section">
            <h4>触发条件</h4>
            <div class="condition-preview">{{ generateConditionText() }}</div>
          </div>
          
          <div class="preview-section">
            <h4>通知配置</h4>
            <p><strong>严重程度：</strong>{{ ruleConfig.severityLevel }}</p>
            <p><strong>通知渠道：</strong>{{ ruleConfig.enabledChannels.join(', ') }}</p>
            <p><strong>告警消息：</strong>{{ ruleConfig.alertMessage }}</p>
          </div>
          
          <div class="preview-section">
            <h4>生效时间</h4>
            <p><strong>时间段：</strong>{{ formatEffectiveTime() }}</p>
            <p><strong>生效日期：</strong>{{ formatEffectiveDays() }}</p>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 操作按钮 -->
    <div class="wizard-actions">
      <el-button @click="previousStep" :disabled="currentStep === 0">上一步</el-button>
      <el-button @click="nextStep" type="primary" 
                :disabled="!canNextStep" v-if="currentStep < 5">下一步</el-button>
      <el-button @click="saveRule" type="success" 
                v-if="currentStep === 5" :loading="saving">保存规则</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Connection, Setting } from '@element-plus/icons-vue'

// 响应式数据
const currentStep = ref(0)
const saving = ref(false)
const newTag = ref('')

// 规则配置
const ruleConfig = reactive({
  ruleName: '',
  ruleDescription: '',
  ruleCategory: 'SINGLE',
  physicalSign: '',
  thresholdMin: null,
  thresholdMax: null,
  trendDuration: 1,
  timeWindowSeconds: 300,
  priorityLevel: 3,
  severityLevel: 'medium',
  alertMessage: '',
  enabledChannels: ['message'],
  cooldownSeconds: 600,
  effectiveTimeStart: null,
  effectiveTimeEnd: null,
  effectiveDays: ['1','2','3','4','5','6','7'],
  ruleTags: [],
  isActive: true
})

// 复合条件
const compositeConditions = ref([
  { physicalSign: '', operator: '>', threshold: 0, durationSeconds: 60 }
])
const logicalOperator = ref('AND')

// 生理指标选项
const physicalSigns = ref([
  { label: '心率', value: 'heart_rate', unit: 'bpm' },
  { label: '血氧', value: 'blood_oxygen', unit: '%' },
  { label: '体温', value: 'temperature', unit: '℃' },
  { label: '收缩压', value: 'pressure_high', unit: 'mmHg' },
  { label: '舒张压', value: 'pressure_low', unit: 'mmHg' },
  { label: '步数', value: 'step', unit: '步' },
  { label: '卡路里', value: 'calorie', unit: 'kcal' },
  { label: '距离', value: 'distance', unit: 'km' },
  { label: '压力指数', value: 'stress', unit: '分' }
])

// 计算属性
const canNextStep = computed(() => {
  switch (currentStep.value) {
    case 0: return ruleConfig.ruleName.trim() !== ''
    case 1: return ruleConfig.ruleCategory !== ''
    case 2: 
      if (ruleConfig.ruleCategory === 'SINGLE') {
        return ruleConfig.physicalSign !== ''
      } else if (ruleConfig.ruleCategory === 'COMPOSITE') {
        return compositeConditions.value.every(c => 
          c.physicalSign && c.operator && c.threshold !== null)
      }
      return true
    case 3: return ruleConfig.severityLevel && ruleConfig.enabledChannels.length > 0
    case 4: return true
    default: return true
  }
})

// 方法
const selectRuleType = (type) => {
  ruleConfig.ruleCategory = type
}

const addCondition = () => {
  compositeConditions.value.push({
    physicalSign: '',
    operator: '>',
    threshold: 0,
    durationSeconds: 60
  })
}

const removeCondition = (index) => {
  if (compositeConditions.value.length > 1) {
    compositeConditions.value.splice(index, 1)
  }
}

const addTag = () => {
  if (newTag.value && !ruleConfig.ruleTags.includes(newTag.value)) {
    ruleConfig.ruleTags.push(newTag.value)
    newTag.value = ''
  }
}

const removeTag = (tag) => {
  const index = ruleConfig.ruleTags.indexOf(tag)
  if (index > -1) {
    ruleConfig.ruleTags.splice(index, 1)
  }
}

const nextStep = () => {
  if (canNextStep.value && currentStep.value < 5) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const saveRule = async () => {
  saving.value = true
  try {
    // 构建保存数据
    const saveData = {
      ...ruleConfig,
      conditionExpression: ruleConfig.ruleCategory === 'COMPOSITE' ? {
        conditions: compositeConditions.value,
        logicalOperator: logicalOperator.value
      } : null
    }
    
    // 调用API保存
    await saveAlertRule(saveData)
    
    ElMessage.success('告警规则保存成功')
    // 返回规则列表页面
    
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  } finally {
    saving.value = false
  }
}

// 格式化方法
const getRuleTypeText = () => {
  const types = {
    'SINGLE': '单体征规则',
    'COMPOSITE': '复合规则', 
    'COMPLEX': '复杂规则'
  }
  return types[ruleConfig.ruleCategory] || ''
}

const getPriorityText = () => {
  const priorities = { 1: '最高', 2: '高', 3: '中', 4: '低', 5: '最低' }
  return priorities[ruleConfig.priorityLevel] || ''
}

const generateConditionText = () => {
  if (ruleConfig.ruleCategory === 'SINGLE') {
    const sign = physicalSigns.value.find(s => s.value === ruleConfig.physicalSign)
    return `${sign?.label || ''} 在 ${ruleConfig.thresholdMin} - ${ruleConfig.thresholdMax} 范围外连续 ${ruleConfig.trendDuration} 次`
  } else if (ruleConfig.ruleCategory === 'COMPOSITE') {
    return compositeConditions.value.map(c => {
      const sign = physicalSigns.value.find(s => s.value === c.physicalSign)
      return `${sign?.label || ''} ${c.operator} ${c.threshold}`
    }).join(` ${logicalOperator.value} `)
  }
  return ''
}

const getSelectedSignUnit = () => {
  const sign = physicalSigns.value.find(s => s.value === ruleConfig.physicalSign)
  return sign?.unit || ''
}

const formatEffectiveTime = () => {
  // 实现时间格式化
  return '全天'
}

const formatEffectiveDays = () => {
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return ruleConfig.effectiveDays.map(d => dayNames[parseInt(d) - 1]).join(', ')
}

// API调用
const saveAlertRule = async (ruleData) => {
  // 实现API调用
  console.log('保存规则数据:', ruleData)
}
</script>

<style scoped>
.alert-rule-wizard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.step-content {
  margin: 20px 0;
  min-height: 400px;
}

.rule-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.rule-type-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.rule-type-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.rule-type-card.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.rule-type-card .el-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 15px;
}

.rule-type-card h3 {
  margin: 15px 0 10px;
  color: #303133;
}

.rule-type-card p {
  color: #606266;
  margin-bottom: 15px;
}

.example {
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

.threshold-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-separator {
  color: #606266;
}

.unit {
  color: #909399;
  font-size: 12px;
}

.help-text {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.condition-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
}

.condition-row {
  display: flex;
  gap: 15px;
  align-items: center;
}

.logic-connector {
  text-align: center;
  margin: 10px 0;
}

.rule-preview {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 20px;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-section h4 {
  color: #303133;
  margin-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 5px;
}

.condition-preview {
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #606266;
}

.wizard-actions {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.wizard-actions .el-button {
  margin: 0 10px;
  min-width: 100px;
}
</style>
```

### 2. 规则列表管理页面
```vue
<template>
  <div class="alert-rules-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>告警规则管理</h2>
        <p>管理和配置系统告警规则，支持单体征、复合和复杂规则</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createRule">
          <el-icon><Plus /></el-icon>
          新建规则
        </el-button>
      </div>
    </div>
    
    <!-- 搜索和过滤 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input v-model="searchForm.keyword" placeholder="搜索规则名称" clearable>
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchForm.ruleCategory" placeholder="规则类型" clearable>
            <el-option label="单体征规则" value="SINGLE" />
            <el-option label="复合规则" value="COMPOSITE" />
            <el-option label="复杂规则" value="COMPLEX" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchForm.severityLevel" placeholder="严重程度" clearable>
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchForm.isActive" placeholder="状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="searchRules">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="success" @click="batchEnable" :disabled="!selectedRules.length">
            批量启用
          </el-button>
          <el-button type="warning" @click="batchDisable" :disabled="!selectedRules.length">
            批量禁用
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 规则列表 -->
    <el-card class="table-card">
      <el-table :data="rulesList" v-loading="loading" 
                @selection-change="handleSelectionChange"
                @sort-change="handleSortChange">
        <el-table-column type="selection" width="50" />
        
        <el-table-column prop="ruleName" label="规则名称" min-width="200">
          <template #default="{ row }">
            <div class="rule-name-cell">
              <span class="rule-name">{{ row.ruleName }}</span>
              <div class="rule-tags">
                <el-tag v-for="tag in row.ruleTags" :key="tag" size="small">
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ruleCategory" label="规则类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTagType(row.ruleCategory)">
              {{ getRuleTypeText(row.ruleCategory) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="physicalSign" label="监测指标" width="120">
          <template #default="{ row }">
            <span v-if="row.ruleCategory === 'SINGLE'">
              {{ getPhysicalSignText(row.physicalSign) }}
            </span>
            <span v-else-if="row.ruleCategory === 'COMPOSITE'">
              {{ getCompositeSignsText(row.conditionExpression) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="severityLevel" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityTagType(row.severityLevel)">
              {{ getSeverityText(row.severityLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="priorityLevel" label="优先级" width="80" sortable>
          <template #default="{ row }">
            <el-rate v-model="row.priorityLevel" disabled show-score 
                    text-color="#ff9900" :max="5" />
          </template>
        </el-table-column>
        
        <el-table-column prop="enabledChannels" label="通知渠道" width="150">
          <template #default="{ row }">
            <div class="channels">
              <el-icon v-if="row.enabledChannels.includes('wechat')" class="channel-icon wechat">
                <ChatDotRound />
              </el-icon>
              <el-icon v-if="row.enabledChannels.includes('message')" class="channel-icon message">
                <Message />
              </el-icon>
              <el-icon v-if="row.enabledChannels.includes('sms')" class="channel-icon sms">
                <Phone />
              </el-icon>
              <el-icon v-if="row.enabledChannels.includes('email')" class="channel-icon email">
                <Monitor />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="isActive" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.isActive" @change="toggleRuleStatus(row)" />
          </template>
        </el-table-column>
        
        <el-table-column prop="updateTime" label="更新时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatTime(row.updateTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewRule(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editRule(row)">编辑</el-button>
            <el-button size="small" @click="duplicateRule(row)">复制</el-button>
            <el-popconfirm title="确定删除此规则吗？" @confirm="deleteRule(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.current" 
                      v-model:page-size="pagination.pageSize"
                      :total="pagination.total"
                      :page-sizes="[10, 20, 50, 100]"
                      layout="total, sizes, prev, pager, next, jumper"
                      @size-change="handleSizeChange"
                      @current-change="handleCurrentChange" />
      </div>
    </el-card>
    
    <!-- 规则详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="规则详情" width="800px">
      <div v-if="selectedRule" class="rule-detail">
        <!-- 规则详情内容 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="规则名称">{{ selectedRule.ruleName }}</el-descriptions-item>
          <el-descriptions-item label="规则类型">{{ getRuleTypeText(selectedRule.ruleCategory) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ getSeverityText(selectedRule.severityLevel) }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ selectedRule.priorityLevel }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedRule.isActive ? 'success' : 'danger'">
              {{ selectedRule.isActive ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="通知渠道">{{ selectedRule.enabledChannels.join(', ') }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ formatTime(selectedRule.createTime) }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 条件详情 -->
        <div class="condition-detail" v-if="selectedRule.ruleCategory === 'COMPOSITE'">
          <h4>复合条件</h4>
          <div class="composite-condition">
            <!-- 显示复合条件详情 -->
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, ChatDotRound, Message, Phone, Monitor } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const rulesList = ref([])
const selectedRules = ref([])
const detailDialogVisible = ref(false)
const selectedRule = ref(null)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  ruleCategory: '',
  severityLevel: '',
  isActive: null
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 排序
const sortConfig = reactive({
  prop: '',
  order: ''
})

// 生命周期
onMounted(() => {
  loadRulesList()
})

// 方法
const loadRulesList = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.current,
      pageSize: pagination.pageSize,
      sortProp: sortConfig.prop,
      sortOrder: sortConfig.order
    }
    
    const response = await fetchAlertRules(params)
    rulesList.value = response.data.list
    pagination.total = response.data.total
    
  } catch (error) {
    ElMessage.error('加载规则列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const createRule = () => {
  // 跳转到规则创建页面
  router.push('/alert-rules/create')
}

const editRule = (rule) => {
  // 跳转到规则编辑页面
  router.push(`/alert-rules/edit/${rule.id}`)
}

const viewRule = (rule) => {
  selectedRule.value = rule
  detailDialogVisible.value = true
}

const duplicateRule = async (rule) => {
  try {
    await ElMessageBox.confirm('确定复制此规则吗？', '确认操作')
    
    const duplicatedRule = {
      ...rule,
      id: undefined,
      ruleName: rule.ruleName + ' (副本)',
      isActive: false
    }
    
    await saveAlertRule(duplicatedRule)
    ElMessage.success('规则复制成功')
    loadRulesList()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('复制失败：' + error.message)
    }
  }
}

const deleteRule = async (ruleId) => {
  try {
    await deleteAlertRule(ruleId)
    ElMessage.success('删除成功')
    loadRulesList()
  } catch (error) {
    ElMessage.error('删除失败：' + error.message)
  }
}

const toggleRuleStatus = async (rule) => {
  try {
    await updateRuleStatus(rule.id, rule.isActive)
    ElMessage.success(rule.isActive ? '规则已启用' : '规则已禁用')
  } catch (error) {
    rule.isActive = !rule.isActive // 回滚状态
    ElMessage.error('状态更新失败：' + error.message)
  }
}

const batchEnable = async () => {
  try {
    const ruleIds = selectedRules.value.map(rule => rule.id)
    await batchUpdateRuleStatus(ruleIds, true)
    ElMessage.success('批量启用成功')
    loadRulesList()
  } catch (error) {
    ElMessage.error('批量启用失败：' + error.message)
  }
}

const batchDisable = async () => {
  try {
    const ruleIds = selectedRules.value.map(rule => rule.id)
    await batchUpdateRuleStatus(ruleIds, false)
    ElMessage.success('批量禁用成功')
    loadRulesList()
  } catch (error) {
    ElMessage.error('批量禁用失败：' + error.message)
  }
}

const searchRules = () => {
  pagination.current = 1
  loadRulesList()
}

const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = key === 'isActive' ? null : ''
  })
  searchRules()
}

const handleSelectionChange = (selection) => {
  selectedRules.value = selection
}

const handleSortChange = ({ prop, order }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  loadRulesList()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.current = 1
  loadRulesList()
}

const handleCurrentChange = (page) => {
  pagination.current = page
  loadRulesList()
}

// 格式化方法
const getRuleTypeText = (category) => {
  const types = {
    'SINGLE': '单体征',
    'COMPOSITE': '复合',
    'COMPLEX': '复杂'
  }
  return types[category] || ''
}

const getRuleTypeTagType = (category) => {
  const types = {
    'SINGLE': '',
    'COMPOSITE': 'success',
    'COMPLEX': 'warning'
  }
  return types[category] || ''
}

const getSeverityText = (level) => {
  const levels = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'critical': '紧急'
  }
  return levels[level] || ''
}

const getSeverityTagType = (level) => {
  const types = {
    'low': 'info',
    'medium': '',
    'high': 'warning',
    'critical': 'danger'
  }
  return types[level] || ''
}

const getPhysicalSignText = (sign) => {
  const signs = {
    'heart_rate': '心率',
    'blood_oxygen': '血氧',
    'temperature': '体温',
    'pressure_high': '收缩压',
    'pressure_low': '舒张压'
  }
  return signs[sign] || sign
}

const getCompositeSignsText = (expression) => {
  if (!expression || !expression.conditions) return '-'
  
  return expression.conditions.map(c => getPhysicalSignText(c.physicalSign)).join(', ')
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// API 调用方法
const fetchAlertRules = async (params) => {
  // 实现API调用
  console.log('获取规则列表:', params)
  return { data: { list: [], total: 0 } }
}

const saveAlertRule = async (rule) => {
  // 实现API调用
  console.log('保存规则:', rule)
}

const deleteAlertRule = async (ruleId) => {
  // 实现API调用
  console.log('删除规则:', ruleId)
}

const updateRuleStatus = async (ruleId, isActive) => {
  // 实现API调用
  console.log('更新规则状态:', ruleId, isActive)
}

const batchUpdateRuleStatus = async (ruleIds, isActive) => {
  // 实现API调用
  console.log('批量更新规则状态:', ruleIds, isActive)
}
</script>

<style scoped>
.alert-rules-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.header-left p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.rule-name-cell {
  .rule-name {
    font-weight: 500;
    color: #303133;
  }
  
  .rule-tags {
    margin-top: 5px;
    
    .el-tag {
      margin-right: 5px;
    }
  }
}

.channels {
  display: flex;
  gap: 8px;
  
  .channel-icon {
    font-size: 16px;
    
    &.wechat { color: #1aad19; }
    &.message { color: #409eff; }
    &.sms { color: #e6a23c; }
    &.email { color: #909399; }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

.rule-detail {
  .condition-detail {
    margin-top: 20px;
    
    h4 {
      margin-bottom: 10px;
      color: #303133;
    }
  }
}
</style>
```

## 📊 性能监控与统计

### 1. 性能监控接口
```python
@app.route('/api/alert_rules/performance_stats', methods=['GET'])
def get_alert_rules_performance_stats():
    """获取告警规则系统性能统计"""
    try:
        # 获取高性能生成器统计
        generator_stats = high_performance_generator.get_performance_stats()
        
        # 获取缓存统计
        cache_subscriber = get_alert_rules_cache_subscriber()
        cache_stats = cache_subscriber.get_cache_stats()
        
        # 获取数据库统计
        db_stats = get_database_performance_stats()
        
        # 获取告警统计
        alert_stats = get_alert_generation_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'performance': {
                    'generator': generator_stats,
                    'cache': cache_stats,
                    'database': db_stats,
                    'alerts': alert_stats
                },
                'timestamp': time.time()
            }
        })
        
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_database_performance_stats():
    """获取数据库性能统计"""
    return {
        'connection_pool_size': db.engine.pool.size(),
        'connection_pool_checked_out': db.engine.pool.checkedout(),
        'query_count': getattr(db.engine, '_query_count', 0),
        'avg_query_time': getattr(db.engine, '_avg_query_time', 0)
    }

def get_alert_generation_stats():
    """获取告警生成统计"""
    today = datetime.now().date()
    
    # 今日告警统计
    today_alerts = db.session.query(AlertInfo).filter(
        func.date(AlertInfo.alert_timestamp) == today
    ).count()
    
    # 按严重程度统计
    severity_stats = db.session.query(
        AlertInfo.severity_level,
        func.count(AlertInfo.id)
    ).filter(
        func.date(AlertInfo.alert_timestamp) == today
    ).group_by(AlertInfo.severity_level).all()
    
    # 按规则类型统计
    rule_type_stats = db.session.query(
        AlertRules.rule_type,
        func.count(AlertInfo.id)
    ).join(
        AlertInfo, AlertRules.id == AlertInfo.rule_id
    ).filter(
        func.date(AlertInfo.alert_timestamp) == today
    ).group_by(AlertRules.rule_type).all()
    
    return {
        'today_total': today_alerts,
        'severity_distribution': dict(severity_stats),
        'rule_type_distribution': dict(rule_type_stats)
    }
```

### 2. 监控仪表板页面
```vue
<template>
  <div class="performance-dashboard">
    <el-row :gutter="20">
      <!-- 整体性能卡片 -->
      <el-col :span="6" v-for="metric in overallMetrics" :key="metric.key">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon" :style="{ color: metric.color }">
              <component :is="metric.icon" />
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-trend" :class="metric.trendClass">
                {{ metric.trend }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 缓存性能图表 -->
      <el-col :span="12">
        <el-card title="缓存性能">
          <div ref="cacheChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      
      <!-- 告警生成趋势 -->
      <el-col :span="12">
        <el-card title="告警生成趋势">
          <div ref="alertTrendChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 规则执行性能 -->
      <el-col :span="24">
        <el-card title="规则执行性能">
          <el-table :data="rulePerformanceData" max-height="400">
            <el-table-column prop="ruleName" label="规则名称" />
            <el-table-column prop="ruleType" label="规则类型" />
            <el-table-column prop="avgExecutionTime" label="平均执行时间(ms)" />
            <el-table-column prop="totalExecutions" label="执行次数" />
            <el-table-column prop="successRate" label="成功率" />
            <el-table-column prop="lastExecution" label="最后执行时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { TrendChartUp, Timer, CheckCircle, Warning } from '@element-plus/icons-vue'

// 响应式数据
const cacheChartRef = ref(null)
const alertTrendChartRef = ref(null)
const rulePerformanceData = ref([])

// 性能指标
const overallMetrics = ref([
  {
    key: 'processing_speed',
    label: '处理速度',
    value: '1,250/s',
    trend: '+15%',
    trendClass: 'trend-up',
    color: '#67c23a',
    icon: TrendChartUp
  },
  {
    key: 'avg_response_time',
    label: '平均响应时间',
    value: '45ms',
    trend: '-8%',
    trendClass: 'trend-down',
    color: '#409eff',
    icon: Timer
  },
  {
    key: 'success_rate',
    label: '成功率',
    value: '99.8%',
    trend: '+0.2%',
    trendClass: 'trend-up',
    color: '#67c23a',
    icon: CheckCircle
  },
  {
    key: 'cache_hit_rate',
    label: '缓存命中率',
    value: '94.2%',
    trend: '+12%',
    trendClass: 'trend-up',
    color: '#e6a23c',
    icon: Warning
  }
])

let cacheChart = null
let alertTrendChart = null
let refreshTimer = null

// 生命周期
onMounted(() => {
  initCharts()
  loadPerformanceData()
  
  // 定时刷新
  refreshTimer = setInterval(loadPerformanceData, 30000) // 30秒刷新
})

onUnmounted(() => {
  if (cacheChart) cacheChart.dispose()
  if (alertTrendChart) alertTrendChart.dispose()
  if (refreshTimer) clearInterval(refreshTimer)
})

// 方法
const initCharts = () => {
  // 初始化缓存性能图表
  cacheChart = echarts.init(cacheChartRef.value)
  
  const cacheOption = {
    title: { text: '缓存命中率', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', max: 100 },
    series: [
      {
        name: 'L1缓存',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: 'L2缓存',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#67c23a' }
      },
      {
        name: 'L3数据库',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }
  
  cacheChart.setOption(cacheOption)
  
  // 初始化告警趋势图表
  alertTrendChart = echarts.init(alertTrendChartRef.value)
  
  const alertOption = {
    title: { text: '告警生成趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value' },
    series: [
      {
        name: '总告警数',
        type: 'bar',
        data: [],
        itemStyle: { color: '#409eff' }
      },
      {
        name: '紧急告警',
        type: 'line',
        data: [],
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }
  
  alertTrendChart.setOption(alertOption)
}

const loadPerformanceData = async () => {
  try {
    // 获取性能统计数据
    const response = await fetch('/api/alert_rules/performance_stats')
    const data = await response.json()
    
    if (data.success) {
      updateMetrics(data.data.performance)
      updateCharts(data.data.performance)
      updateRulePerformanceTable(data.data.performance)
    }
  } catch (error) {
    console.error('加载性能数据失败:', error)
  }
}

const updateMetrics = (performanceData) => {
  // 更新整体性能指标
  const generator = performanceData.generator
  const cache = performanceData.cache
  
  overallMetrics.value[0].value = `${Math.round(generator.total_processed / generator.avg_processing_time)}/s`
  overallMetrics.value[1].value = `${Math.round(generator.avg_processing_time * 1000)}ms`
  overallMetrics.value[2].value = `${(generator.total_processed / (generator.total_processed + generator.total_failed) * 100).toFixed(1)}%`
  overallMetrics.value[3].value = `${cache.hit_rate}%`
}

const updateCharts = (performanceData) => {
  // 更新图表数据（示例数据）
  const timeLabels = generateTimeLabels()
  
  // 更新缓存图表
  cacheChart.setOption({
    xAxis: { data: timeLabels },
    series: [
      { data: generateRandomData(24, 85, 95) },
      { data: generateRandomData(24, 75, 85) },
      { data: generateRandomData(24, 60, 75) }
    ]
  })
  
  // 更新告警趋势图表
  alertTrendChart.setOption({
    xAxis: { data: timeLabels },
    series: [
      { data: generateRandomData(24, 50, 200) },
      { data: generateRandomData(24, 0, 20) }
    ]
  })
}

const updateRulePerformanceTable = (performanceData) => {
  // 更新规则性能表格（示例数据）
  rulePerformanceData.value = [
    {
      ruleName: '心率异常规则',
      ruleType: '单体征',
      avgExecutionTime: 12,
      totalExecutions: 1250,
      successRate: '99.8%',
      lastExecution: '2025-09-10 14:30:25'
    },
    {
      ruleName: '综合健康评估',
      ruleType: '复合',
      avgExecutionTime: 28,
      totalExecutions: 680,
      successRate: '99.5%',
      lastExecution: '2025-09-10 14:30:18'
    }
  ]
}

// 工具函数
const generateTimeLabels = () => {
  const labels = []
  for (let i = 23; i >= 0; i--) {
    const time = new Date()
    time.setHours(time.getHours() - i)
    labels.push(time.getHours() + ':00')
  }
  return labels
}

const generateRandomData = (count, min, max) => {
  return Array.from({ length: count }, () => 
    Math.floor(Math.random() * (max - min + 1)) + min
  )
}
</script>

<style scoped>
.performance-dashboard {
  padding: 20px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.metric-icon {
  font-size: 36px;
  margin-right: 15px;
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.metric-trend {
  font-size: 12px;
  font-weight: 500;
}

.trend-up {
  color: #67c23a;
}

.trend-down {
  color: #409eff;
}
</style>
```

## 📋 实施计划与部署

### 阶段一：基础设施准备 (1周)
1. **数据库表结构升级**
   - 执行表结构变更SQL
   - 数据迁移和验证
   - 索引优化

2. **Redis配置优化**
   - TTL调整为24小时
   - 发布订阅通道配置
   - 连接池优化

3. **基础设施监控**
   - 性能基线建立
   - 监控指标配置

### 阶段二：后端核心实现 (2周)
1. **规则引擎开发**
   - 单体征规则兼容
   - 复合规则引擎
   - 规则预编译优化

2. **缓存同步优化**
   - 三层缓存架构
   - 跨DB订阅机制
   - 容错和恢复

3. **消息发布统一**
   - 统一消息模型
   - 多渠道路由
   - 异步处理队列

### 阶段三：前端界面开发 (2周)
1. **规则配置向导**
   - 步骤式配置界面
   - 实时预览功能
   - 条件可视化编辑

2. **规则管理页面**
   - 列表展示和筛选
   - 批量操作功能
   - 性能监控面板

3. **性能监控仪表板**
   - 实时性能图表
   - 告警统计分析
   - 系统健康状态

### 阶段四：性能优化和测试 (1周)
1. **性能压力测试**
   - 1000并发处理验证
   - 响应时间优化
   - 内存使用优化

2. **功能集成测试**
   - 端到端流程测试
   - 异常场景验证
   - 兼容性测试

### 阶段五：生产部署 (1周)
1. **灰度发布**
   - 小流量验证
   - 性能监控
   - 问题快速响应

2. **全量发布**
   - 配置迁移
   - 数据同步
   - 性能调优

## 🎯 预期效果

### 性能提升指标
- **规则评估速度**: 提升80%以上
- **并发处理能力**: 支持1000+并发
- **内存使用**: 减少40%
- **响应时间**: 平均50ms以下

### 功能增强效果
- **规则表达能力**: 支持复杂的多体征关联
- **管理效率**: 可视化配置，降低80%配置时间
- **系统稳定性**: 告警抑制，减少90%重复告警
- **运维便利性**: 完整监控体系，问题快速定位

### 业务价值
- **告警准确性**: 减少误报85%以上
- **响应速度**: 告警延迟降至秒级
- **运维成本**: 减少人工干预60%
- **用户体验**: 更精准的健康监护服务

这个完整的实施方案整合了所有优化策略，提供了从数据库设计、后端实现、前端界面到部署监控的全流程解决方案，可以直接按照计划逐步实施落地。