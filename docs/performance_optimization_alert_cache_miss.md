# 告警规则缓存Miss性能优化方案

## 问题分析

在压测过程中发现以下性能问题：

1. **告警规则缓存miss**：`WARNING:alert_rules_cache_manager:告警规则缓存miss，尝试自动预热: customer_id=1`
2. **physical_sign缺失问题**：`Skipping rule 1963736801749045250: missing physical_sign`
3. **设备用户组织信息缓存频繁查询**：`从缓存获取设备用户组织信息，device_sn:CRFTQ23409000847`
4. **规则数量过多**：`📋 获取到告警规则 248 条 (Redis缓存: ❌)`

## 根本原因分析

### 1. 告警规则缓存miss的原因

- **缓存预热不充分**：系统启动后没有主动预热活跃客户的告警规则缓存
- **缓存TTL过短**：Redis缓存过期时间可能设置得过短
- **缓存键策略**：缓存键可能没有正确处理customer_id的映射关系

### 2. physical_sign缺失问题

- **数据质量问题**：数据库中的告警规则存在physical_sign为空的记录
- **规则跳过频繁**：大量规则因为physical_sign缺失被跳过，影响性能

### 3. 设备用户组织信息缓存效率

- **单次查询**：每次都需要查询设备信息，没有批量优化
- **缓存命中率低**：10分钟的缓存时间可能过短

## 优化方案

### 1. 告警规则缓存优化

#### A. 增强预热机制

```python
class AlertRulesCacheManager:
    def __init__(self):
        self.preload_on_startup = True
        self.cache_ttl = 3600  # 增加到1小时
        
    def startup_warmup(self):
        """系统启动时预热缓存"""
        try:
            # 获取最近7天活跃的客户ID
            active_customers = self._get_active_customers(days=7)
            
            # 批量预热
            for customer_id in active_customers:
                self.get_alert_rules(customer_id)
                
            logger.info(f"启动预热完成：{len(active_customers)}个客户")
            
        except Exception as e:
            logger.error(f"启动预热失败: {e}")
    
    def _get_active_customers(self, days=7):
        """获取活跃客户ID列表"""
        try:
            # 从健康数据表查询活跃客户
            query = """
                SELECT DISTINCT customer_id 
                FROM t_user_health_data 
                WHERE create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND customer_id IS NOT NULL
                ORDER BY customer_id
            """
            
            result = db.session.execute(text(query), (days,))
            customer_ids = [row[0] for row in result.fetchall()]
            
            return customer_ids
            
        except Exception as e:
            logger.error(f"获取活跃客户失败: {e}")
            return []
```

#### B. 改进缓存策略

```python
def get_alert_rules(self, customer_id: int) -> List[AlertRule]:
    """三级缓存策略 + 预加载优化"""
    
    # L1: 本地缓存（内存）
    local_key = f"rules_{customer_id}"
    if local_key in self.local_cache:
        return self.local_cache[local_key]
    
    # L2: Redis缓存（1小时TTL）
    redis_key = f"alert_rules_{customer_id}"
    try:
        cached_data = self.boot_redis_client.get(redis_key)
        if cached_data:
            data = json.loads(cached_data)
            rules = self._convert_rules_data(data.get('rules', []))
            
            # 更新本地缓存
            self.local_cache[local_key] = rules
            
            logger.debug(f"Redis缓存命中: customer_id={customer_id}")
            return rules
            
    except Exception as e:
        logger.error(f"Redis缓存读取失败: {e}")
    
    # L3: 数据库查询 + 智能预加载
    logger.warning(f"缓存miss，数据库查询: customer_id={customer_id}")
    rules = self._load_rules_from_db(customer_id)
    
    # 异步预加载相关客户的规则
    self._async_preload_related_customers(customer_id)
    
    return rules
```

### 2. physical_sign缺失问题优化

#### A. 数据清理脚本

```python
def fix_missing_physical_sign():
    """修复缺失的physical_sign字段"""
    try:
        # 查找physical_sign为空的规则
        empty_rules = AlertRules.query.filter(
            or_(
                AlertRules.physical_sign.is_(None),
                AlertRules.physical_sign == '',
                AlertRules.physical_sign == 'NULL'
            ),
            AlertRules.is_deleted == False
        ).all()
        
        logger.info(f"发现{len(empty_rules)}条physical_sign缺失的规则")
        
        # 基于rule_type推断physical_sign
        type_mapping = {
            'heart_rate_abnormal': 'heartRate',
            'blood_pressure_abnormal': 'bloodPressure', 
            'blood_oxygen_abnormal': 'bloodOxygen',
            'temperature_abnormal': 'temperature',
            'step_abnormal': 'step',
            'sleep_abnormal': 'sleep'
        }
        
        fixed_count = 0
        for rule in empty_rules:
            if rule.rule_type in type_mapping:
                rule.physical_sign = type_mapping[rule.rule_type]
                fixed_count += 1
            else:
                logger.warning(f"未知规则类型，跳过修复: {rule.rule_type}")
        
        db.session.commit()
        logger.info(f"修复完成：{fixed_count}条规则")
        
        return fixed_count
        
    except Exception as e:
        logger.error(f"修复physical_sign失败: {e}")
        db.session.rollback()
        return 0
```

#### B. 规则验证和过滤优化

```python
def get_valid_rules(self, customer_id: int) -> List[AlertRule]:
    """获取有效的告警规则（过滤无效规则）"""
    rules = self.get_alert_rules(customer_id)
    
    valid_rules = []
    skipped_count = 0
    
    for rule in rules:
        # 验证规则完整性
        if not rule.physical_sign or rule.physical_sign.strip() == '':
            skipped_count += 1
            continue
            
        # 验证阈值合理性
        if (rule.threshold_min is None or rule.threshold_max is None or 
            rule.threshold_min >= rule.threshold_max):
            skipped_count += 1
            continue
            
        valid_rules.append(rule)
    
    if skipped_count > 0:
        logger.warning(f"跳过{skipped_count}条无效规则，有效规则{len(valid_rules)}条")
    
    return valid_rules
```

### 3. 设备用户组织信息缓存优化

#### A. 批量缓存预热

```python
class DeviceInfoCacheManager:
    def __init__(self):
        self.cache_ttl = 1800  # 30分钟
        self.batch_size = 100
        
    def batch_warmup_devices(self, device_sns: List[str]):
        """批量预热设备缓存"""
        try:
            # 过滤已缓存的设备
            uncached_devices = []
            for device_sn in device_sns:
                cache_key = f"device_user_org:{device_sn}"
                if not redis.exists(cache_key):
                    uncached_devices.append(device_sn)
            
            if not uncached_devices:
                return
            
            logger.info(f"批量预热设备信息：{len(uncached_devices)}个设备")
            
            # 批量查询数据库
            for i in range(0, len(uncached_devices), self.batch_size):
                batch = uncached_devices[i:i + self.batch_size]
                self._batch_load_device_info(batch)
                
        except Exception as e:
            logger.error(f"批量预热设备信息失败: {e}")
    
    def _batch_load_device_info(self, device_sns: List[str]):
        """批量加载设备信息"""
        try:
            # 批量查询
            results = db.session.query(
                UserInfo.device_sn,
                UserInfo.id.label('user_id'),
                UserInfo.user_name,
                UserInfo.customer_id,
                UserOrg.org_id,
                OrgInfo.name.label('org_name')
            ).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo, UserOrg.org_id == OrgInfo.id
            ).filter(
                UserInfo.device_sn.in_(device_sns),
                UserInfo.is_deleted.is_(False),
                OrgInfo.is_deleted.is_(False)
            ).all()
            
            # 批量写入缓存
            cache_data = {}
            for result in results:
                cache_key = f"device_user_org:{result.device_sn}"
                device_info = {
                    'success': True,
                    'user_id': result.user_id,
                    'user_name': result.user_name,
                    'org_id': result.org_id,
                    'org_name': result.org_name,
                    'customer_id': result.customer_id,
                    'device_sn': result.device_sn
                }
                cache_data[cache_key] = json.dumps(device_info, ensure_ascii=False)
            
            # 批量写入Redis
            if cache_data:
                pipe = redis.pipeline()
                for key, data in cache_data.items():
                    pipe.setex(key, self.cache_ttl, data)
                pipe.execute()
                
                logger.info(f"批量缓存设备信息：{len(cache_data)}个设备")
                
        except Exception as e:
            logger.error(f"批量加载设备信息失败: {e}")
```

### 4. 高效Redis缓存策略

#### A. 分布式缓存一致性

```python
class DistributedCacheManager:
    def __init__(self):
        self.cache_version_key = "cache_version:alert_rules"
        
    def invalidate_cache(self, customer_id: int):
        """分布式缓存失效通知"""
        try:
            # 更新版本号
            version = redis.incr(self.cache_version_key)
            
            # 发布失效通知
            message = f"invalidate:{customer_id}:{version}"
            redis.publish("cache_invalidation", message)
            
            logger.info(f"缓存失效通知已发送: customer_id={customer_id}, version={version}")
            
        except Exception as e:
            logger.error(f"缓存失效通知失败: {e}")
    
    def check_cache_validity(self, customer_id: int, cached_version: int) -> bool:
        """检查缓存有效性"""
        try:
            current_version = int(redis.get(self.cache_version_key) or 0)
            return cached_version >= current_version
            
        except Exception as e:
            logger.error(f"缓存版本检查失败: {e}")
            return False
```

#### B. 智能预加载策略

```python
class IntelligentPreloader:
    def __init__(self):
        self.preload_patterns = {}
        
    def analyze_access_patterns(self):
        """分析访问模式"""
        try:
            # 分析最近24小时的访问模式
            access_logs = redis.zrange("cache_access_log", 0, -1, withscores=True)
            
            # 计算访问频率
            for key, timestamp in access_logs:
                customer_id = self._extract_customer_id(key)
                if customer_id:
                    self.preload_patterns[customer_id] = self.preload_patterns.get(customer_id, 0) + 1
            
            # 预加载高频访问的客户
            high_freq_customers = [
                customer_id for customer_id, freq in self.preload_patterns.items()
                if freq >= 10  # 访问次数>=10
            ]
            
            for customer_id in high_freq_customers:
                self._preload_customer_cache(customer_id)
                
        except Exception as e:
            logger.error(f"智能预加载分析失败: {e}")
```

## 实施计划

### 阶段1：数据清理（立即执行）
1. 执行physical_sign修复脚本
2. 验证数据质量
3. 更新告警规则缓存

### 阶段2：缓存策略优化（1-2天）
1. 部署新的缓存管理器
2. 配置启动预热机制
3. 实施批量设备信息缓存

### 阶段3：性能监控（持续）
1. 添加缓存命中率监控
2. 分析访问模式
3. 调优缓存参数

## 预期效果

1. **缓存命中率提升**：从当前的低命中率提升到90%以上
2. **响应时间优化**：告警处理响应时间减少60%以上
3. **资源使用优化**：减少数据库查询压力50%以上
4. **系统稳定性**：消除缓存miss导致的性能抖动

## 监控指标

- 告警规则缓存命中率
- 设备信息缓存命中率
- 平均响应时间
- 数据库查询次数
- Redis内存使用量
- 无效规则跳过次数

## 配置参数调优建议

```python
# Redis缓存配置
ALERT_RULES_CACHE_TTL = 3600  # 1小时
DEVICE_INFO_CACHE_TTL = 1800  # 30分钟
PRELOAD_ACTIVE_DAYS = 7       # 预热7天内活跃客户

# 批处理配置
BATCH_PRELOAD_SIZE = 100      # 批量预热大小
MAX_CONCURRENT_PRELOAD = 5    # 最大并发预热数

# 缓存清理配置
CACHE_CLEANUP_INTERVAL = 3600 # 1小时清理一次过期缓存
MAX_CACHE_SIZE_MB = 512       # 最大缓存大小512MB
```