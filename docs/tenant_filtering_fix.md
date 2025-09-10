# 租户过滤缺失修复方案 - 告警规则性能优化

## 问题确认

**根本原因**: AlertRules表缺少customer_id字段，导致无法按租户过滤，每次查询都加载全部248条规则！

```python
# 当前的问题查询 - 无租户过滤
alert_rules = AlertRules.query.filter_by(is_deleted=False).all()  # 查询全部248条！
```

这就是压测时看到的性能问题：
- `📋 获取到告警规则 248 条 (Redis缓存: ❌)`
- 大量无关规则被加载和处理
- physical_sign缺失的规则被跳过，浪费CPU资源

## 立即修复方案

### 方案1：数据库Schema修改（推荐）

#### 1.1 添加customer_id字段

```sql
-- 添加customer_id字段
ALTER TABLE t_alert_rules 
ADD COLUMN customer_id BIGINT DEFAULT 1 COMMENT '客户ID';

-- 添加索引
CREATE INDEX idx_alert_rules_customer_id ON t_alert_rules(customer_id, is_deleted);

-- 更新现有数据（假设现有规则属于customer_id=1）
UPDATE t_alert_rules SET customer_id = 1 WHERE customer_id IS NULL;

-- 设置非空约束
ALTER TABLE t_alert_rules 
MODIFY COLUMN customer_id BIGINT NOT NULL COMMENT '客户ID';
```

#### 1.2 更新模型定义

```python
class AlertRules(db.Model):
    __tablename__ = 't_alert_rules'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.BigInteger, nullable=False, comment='客户ID')  # 新增
    rule_type = db.Column(db.String(50), nullable=False)
    physical_sign = db.Column(db.String(50), nullable=True)
    # ... 其他字段保持不变
    
    __table_args__ = (
        db.UniqueConstraint('customer_id', 'rule_type', 'physical_sign', 
                          name='uk_customer_rule_type_physical_sign'),
        db.Index('idx_customer_deleted', 'customer_id', 'is_deleted')
    )
```

#### 1.3 修复查询逻辑

```python
def generate_alerts(data, health_data_id):
    """修复后的告警生成 - 按租户过滤"""
    try:
        # 获取customer_id
        customer_id = data.get('customer_id') or data.get('customerId')
        
        if not customer_id:
            # 如果没有直接传递customer_id，从设备信息获取
            device_info = get_device_user_org_info(data.get('deviceSn'))
            customer_id = device_info.get('customer_id') if device_info.get('success') else None
        
        if not customer_id:
            logger.error("无法获取customer_id，跳过告警生成")
            return
        
        # 🎯 关键修复：按customer_id过滤告警规则
        alert_rules = AlertRules.query.filter_by(
            customer_id=customer_id,
            is_deleted=False
        ).all()
        
        logger.info(f"📋 按租户过滤后的告警规则: customer_id={customer_id}, 规则数={len(alert_rules)}")
        
        # 转换为字典格式进行处理
        alert_rules_dict = {}
        for rule in alert_rules:
            if rule.physical_sign:  # 只处理有效的规则
                alert_rules_dict[rule.id] = {
                    'id': rule.id,
                    'rule_type': rule.rule_type,
                    'physical_sign': rule.physical_sign,
                    'threshold_min': rule.threshold_min,
                    'threshold_max': rule.threshold_max,
                    'trend_duration': rule.trend_duration,
                    'severity_level': rule.severity_level,
                    'alert_message': rule.alert_message,
                    'is_enabled': True
                }
        
        logger.info(f"📋 有效告警规则: {len(alert_rules_dict)}条")
        
        # 后续处理逻辑保持不变...
        
    except Exception as e:
        logger.error(f"告警生成失败: {e}")
        return
```

### 方案2：应用层过滤（临时方案）

如果无法立即修改数据库，可以在应用层实现租户过滤：

```python
def get_customer_alert_rules(customer_id: int):
    """应用层租户过滤 - 临时方案"""
    
    # 缓存键包含customer_id
    cache_key = f"alert_rules_filtered:{customer_id}"
    
    # 检查缓存
    cached_rules = redis.get(cache_key)
    if cached_rules:
        return json.loads(cached_rules)
    
    # 查询所有规则（暂时无法避免）
    all_rules = AlertRules.query.filter_by(is_deleted=False).all()
    
    # 应用层过滤逻辑
    filtered_rules = []
    for rule in all_rules:
        # 基于规则命名约定或其他业务逻辑过滤
        if should_apply_to_customer(rule, customer_id):
            filtered_rules.append(rule)
    
    # 缓存过滤后的结果（30分钟）
    redis.setex(cache_key, 1800, json.dumps([rule.to_dict() for rule in filtered_rules]))
    
    logger.info(f"应用层过滤: customer_id={customer_id}, 从{len(all_rules)}条规则筛选出{len(filtered_rules)}条")
    
    return filtered_rules

def should_apply_to_customer(rule, customer_id):
    """判断规则是否应用于指定客户 - 业务逻辑"""
    # 可以基于规则名称、创建者、或其他业务逻辑
    # 这里是示例逻辑，需要根据实际业务调整
    
    # 方式1：基于规则创建者
    if hasattr(rule, 'create_user_id') and rule.create_user_id:
        # 查询创建者所属客户
        creator_customer = get_user_customer_id(rule.create_user_id)
        return creator_customer == customer_id
    
    # 方式2：基于规则命名约定
    if f"_c{customer_id}_" in rule.rule_type:
        return True
    
    # 方式3：默认规则应用于所有客户
    if rule.rule_type in ['default_heart_rate', 'default_blood_pressure']:
        return True
    
    # 默认不应用
    return False
```

### 方案3：缓存管理器增强（配合方案1）

```python
class TenantAwareAlertRulesCacheManager:
    """租户感知的告警规则缓存管理器"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.local_cache = {}  # {customer_id: {rules, timestamp}}
        self.cache_ttl = 3600  # 1小时
    
    def get_alert_rules(self, customer_id: int) -> List[Dict]:
        """获取指定客户的告警规则"""
        
        # L1: 本地缓存
        if self._is_local_cache_valid(customer_id):
            logger.debug(f"本地缓存命中: customer_id={customer_id}")
            return self.local_cache[customer_id]['rules']
        
        # L2: Redis缓存
        redis_key = f"alert_rules_tenant:{customer_id}"
        cached_data = self.redis_client.get(redis_key)
        
        if cached_data:
            rules_data = json.loads(cached_data)
            self._update_local_cache(customer_id, rules_data)
            logger.info(f"Redis缓存命中: customer_id={customer_id}, 规则数={len(rules_data)}")
            return rules_data
        
        # L3: 数据库查询（按租户过滤）
        logger.warning(f"缓存miss，查询数据库: customer_id={customer_id}")
        rules = self._load_from_database(customer_id)
        
        # 更新缓存
        if rules:
            rules_data = [self._rule_to_dict(rule) for rule in rules]
            self._update_redis_cache(customer_id, rules_data)
            self._update_local_cache(customer_id, rules_data)
            
            logger.info(f"数据库查询完成: customer_id={customer_id}, 规则数={len(rules_data)}")
            return rules_data
        
        return []
    
    def _load_from_database(self, customer_id: int):
        """从数据库加载指定客户的告警规则"""
        try:
            rules = AlertRules.query.filter_by(
                customer_id=customer_id,
                is_deleted=False
            ).filter(
                AlertRules.physical_sign.isnot(None),  # 排除physical_sign为空的规则
                AlertRules.physical_sign != ''
            ).all()
            
            return rules
            
        except Exception as e:
            logger.error(f"查询告警规则失败: customer_id={customer_id}, error={e}")
            return []
    
    def _update_redis_cache(self, customer_id: int, rules_data: List[Dict]):
        """更新Redis缓存"""
        try:
            redis_key = f"alert_rules_tenant:{customer_id}"
            cache_data = {
                'rules': rules_data,
                'timestamp': int(time.time()),
                'version': 1
            }
            
            self.redis_client.setex(redis_key, self.cache_ttl, json.dumps(cache_data))
            logger.debug(f"Redis缓存更新: customer_id={customer_id}")
            
        except Exception as e:
            logger.error(f"更新Redis缓存失败: {e}")
    
    def invalidate_customer_cache(self, customer_id: int):
        """失效指定客户的缓存"""
        try:
            # 清除本地缓存
            self.local_cache.pop(customer_id, None)
            
            # 清除Redis缓存
            redis_key = f"alert_rules_tenant:{customer_id}"
            self.redis_client.delete(redis_key)
            
            logger.info(f"缓存失效: customer_id={customer_id}")
            
        except Exception as e:
            logger.error(f"缓存失效失败: {e}")
```

## 性能优化效果预测

### 当前性能问题
- 每次查询248条规则（全量）
- physical_sign缺失导致跳过规则浪费CPU
- 无租户隔离，数据安全风险

### 修复后效果
- 按租户查询，假设每个客户10-20条规则
- 性能提升：248 → 15条规则，**减少93%的数据量**
- 内存使用减少90%以上
- CPU处理时间减少90%以上
- 缓存命中率大幅提升

## 立即执行计划

### 第1步：验证客户数据分布
```sql
-- 检查当前告警规则分布
SELECT 
    COUNT(*) as total_rules,
    COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) as valid_rules,
    COUNT(CASE WHEN physical_sign IS NULL OR physical_sign = '' THEN 1 END) as invalid_rules
FROM t_alert_rules 
WHERE is_deleted = 0;

-- 检查rule_type分布（用于设计customer_id分配逻辑）
SELECT rule_type, COUNT(*) as count 
FROM t_alert_rules 
WHERE is_deleted = 0 
GROUP BY rule_type 
ORDER BY count DESC;
```

### 第2步：执行数据库修改
```sql
-- 立即执行
ALTER TABLE t_alert_rules ADD COLUMN customer_id BIGINT DEFAULT 1 COMMENT '客户ID';
CREATE INDEX idx_alert_rules_customer_id ON t_alert_rules(customer_id, is_deleted);
UPDATE t_alert_rules SET customer_id = 1 WHERE customer_id IS NULL;
```

### 第3步：更新应用代码
1. 修改models.py中的AlertRules类
2. 更新generate_alerts函数
3. 部署租户感知的缓存管理器

### 第4步：验证效果
```python
# 测试脚本
def test_tenant_filtering():
    customer_id = 1
    
    # 修复前
    old_rules = AlertRules.query.filter_by(is_deleted=False).all()
    
    # 修复后  
    new_rules = AlertRules.query.filter_by(customer_id=customer_id, is_deleted=False).all()
    
    print(f"修复前规则数: {len(old_rules)}")
    print(f"修复后规则数: {len(new_rules)}")
    print(f"性能提升: {(1 - len(new_rules)/len(old_rules)) * 100:.1f}%")
```

## 监控指标

修复后需要监控的关键指标：
- 按客户ID的告警规则查询时间
- 缓存命中率（应该达到95%以上）
- 无效规则跳过次数（应该接近0）
- 内存使用量
- generate_alerts函数执行时间

这个修复将直接解决压测中发现的核心性能问题！