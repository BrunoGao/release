# 告警规则系统综合优化方案

## 📊 现状分析

### 当前t_alert_rules表结构
```sql
CREATE TABLE `t_alert_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rule_type` varchar(50) NOT NULL DEFAULT 'metric' COMMENT 'metric|custom|fallback',
  `physical_sign` varchar(50) DEFAULT NULL,
  `threshold_min` decimal(10,2) DEFAULT NULL,
  `threshold_max` decimal(10,2) DEFAULT NULL,
  `deviation_percentage` decimal(5,2) DEFAULT NULL,
  `trend_duration` int DEFAULT NULL COMMENT '连续异常次数',
  `parameters` json DEFAULT NULL,
  `trigger_condition` text,
  `alert_message` text,
  `severity_level` varchar(20) DEFAULT NULL,
  `notification_type` varchar(50) DEFAULT 'message',
  `customer_id` bigint DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` bigint DEFAULT NULL,
  `updated_by` bigint DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 当前系统痛点

1. **单体征规则限制** - 当前每条规则只能配置单个`physical_sign`
2. **复合条件缺失** - 无法实现"心率>120 AND 血氧<90"这类多体征关联告警
3. **阈值表达能力有限** - 只支持min/max范围，无法支持复杂阈值逻辑
4. **连续异常判断不灵活** - 只有简单的`trend_duration`计数，缺乏时间窗口概念
5. **高并发处理瓶颈** - 每次告警检测都需要查询数据库

## 🎯 核心需求分析

### 业务场景支持

#### 场景1：单体征阈值告警
- **需求**: 心率高于120连续3次触发告警
- **当前**: ✅ 已支持
- **优化**: 增强时间窗口控制

#### 场景2：多体征关联告警
- **需求**: 心率>120 AND 血氧<90 同时满足时触发告警
- **当前**: ❌ 不支持
- **优化**: 新增复合规则支持

#### 场景3：复杂阈值条件
- **需求**: 心率异常=（心率>最大阈值 OR 心率<最小阈值）AND 持续时间>5分钟
- **当前**: ❌ 部分支持
- **优化**: 增强条件表达式引擎

#### 场景4：智能告警抑制
- **需求**: 避免短时间内重复告警
- **当前**: ❌ 无抑制机制
- **优化**: 添加告警去重和抑制逻辑

## 🚀 优化方案设计

### 1. 数据结构优化

#### 1.1 保持向下兼容的表结构增强
```sql
-- 在现有表基础上增加字段，保持向下兼容
ALTER TABLE `t_alert_rules` 
ADD COLUMN `rule_category` ENUM('SINGLE', 'COMPOSITE', 'COMPLEX') DEFAULT 'SINGLE' COMMENT '规则类型：单体征/复合/复杂',
ADD COLUMN `condition_expression` TEXT COMMENT 'JSON格式的复杂条件表达式',
ADD COLUMN `time_window_seconds` INT DEFAULT 300 COMMENT '时间窗口(秒)',
ADD COLUMN `cooldown_seconds` INT DEFAULT 600 COMMENT '告警冷却期(秒)',
ADD COLUMN `priority_level` INT DEFAULT 3 COMMENT '优先级(1-5，数字越小优先级越高)',
ADD COLUMN `rule_tags` JSON COMMENT '规则标签，便于分类管理',
ADD COLUMN `effective_time_start` TIME COMMENT '生效开始时间',
ADD COLUMN `effective_time_end` TIME COMMENT '生效结束时间',
ADD COLUMN `effective_days` VARCHAR(20) DEFAULT '1,2,3,4,5,6,7' COMMENT '生效星期(1-7)',
ADD INDEX idx_customer_category (`customer_id`, `rule_category`),
ADD INDEX idx_priority (`priority_level`),
ADD INDEX idx_physical_sign_active (`physical_sign`, `is_active`);
```

#### 1.2 复合规则条件表达式设计
```json
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
  "evaluation_window": 300,
  "trigger_threshold": {
    "type": "percentage",
    "value": 80
  }
}
```

#### 1.3 规则处理引擎设计
```python
class AlertRuleEngine:
    """高性能告警规则引擎"""
    
    def __init__(self):
        self.redis = RedisHelper()
        self.rule_cache = {}
        self.evaluation_cache = {}
    
    def evaluate_rules(self, health_data: dict, device_info: dict) -> List[dict]:
        """
        高效规则评估主入口
        
        Args:
            health_data: 健康数据
            device_info: 设备信息 
            
        Returns:
            符合条件的告警列表
        """
        customer_id = device_info.get('customer_id')
        user_id = health_data.get('user_id')
        device_sn = health_data.get('deviceSn')
        
        # 1. 获取缓存的规则
        rules = self._get_cached_rules(customer_id)
        if not rules:
            return []
            
        triggered_alerts = []
        
        # 2. 按优先级和类型分组处理
        for rule in sorted(rules, key=lambda x: x.get('priority_level', 5)):
            if not self._is_rule_effective(rule):
                continue
                
            # 3. 根据规则类型选择评估策略
            if rule['rule_category'] == 'SINGLE':
                alert = self._evaluate_single_rule(rule, health_data, device_info)
            elif rule['rule_category'] == 'COMPOSITE': 
                alert = self._evaluate_composite_rule(rule, health_data, device_info)
            elif rule['rule_category'] == 'COMPLEX':
                alert = self._evaluate_complex_rule(rule, health_data, device_info)
            else:
                continue
                
            if alert:
                # 4. 告警抑制检查
                if not self._is_suppressed(alert, rule):
                    triggered_alerts.append(alert)
                    # 5. 设置冷却期
                    self._set_cooldown(alert, rule)
                    
        return triggered_alerts
    
    def _evaluate_single_rule(self, rule: dict, health_data: dict, device_info: dict) -> Optional[dict]:
        """单体征规则评估 - 兼容现有逻辑"""
        physical_sign = rule.get('physical_sign')
        if not physical_sign or physical_sign not in health_data:
            return None
            
        value = float(health_data[physical_sign])
        threshold_min = rule.get('threshold_min')
        threshold_max = rule.get('threshold_max')
        
        # 阈值检查
        is_abnormal = False
        if threshold_min and value < threshold_min:
            is_abnormal = True
        elif threshold_max and value > threshold_max:
            is_abnormal = True
            
        if not is_abnormal:
            return None
            
        # 连续异常检查（优化后的逻辑）
        trend_duration = rule.get('trend_duration', 1)
        time_window = rule.get('time_window_seconds', 300)
        
        if self._check_trend_duration(health_data, rule, trend_duration, time_window):
            return self._create_alert(rule, health_data, device_info, {
                'trigger_value': value,
                'threshold_min': threshold_min,
                'threshold_max': threshold_max
            })
            
        return None
    
    def _evaluate_composite_rule(self, rule: dict, health_data: dict, device_info: dict) -> Optional[dict]:
        """复合规则评估 - 支持多体征关联"""
        try:
            condition_expr = rule.get('condition_expression')
            if not condition_expr:
                return None
                
            conditions = condition_expr.get('conditions', [])
            logical_op = condition_expr.get('logical_operator', 'AND')
            
            condition_results = []
            trigger_details = {}
            
            for condition in conditions:
                physical_sign = condition['physical_sign'] 
                if physical_sign not in health_data:
                    condition_results.append(False)
                    continue
                    
                value = float(health_data[physical_sign])
                operator = condition['operator']
                threshold = condition['threshold']
                duration = condition.get('duration_seconds', 60)
                
                # 单个条件评估
                condition_met = self._evaluate_condition(value, operator, threshold)
                
                # 持续时间检查
                if condition_met and duration > 0:
                    condition_met = self._check_duration_for_sign(
                        health_data, physical_sign, operator, threshold, duration
                    )
                
                condition_results.append(condition_met)
                if condition_met:
                    trigger_details[physical_sign] = {
                        'value': value,
                        'operator': operator, 
                        'threshold': threshold
                    }
            
            # 逻辑组合评估
            if logical_op == 'AND':
                final_result = all(condition_results)
            elif logical_op == 'OR':
                final_result = any(condition_results)
            else:
                final_result = False
                
            if final_result:
                return self._create_alert(rule, health_data, device_info, {
                    'composite_triggers': trigger_details,
                    'condition_results': condition_results
                })
                
        except Exception as e:
            logger.error(f"复合规则评估失败: {e}")
            
        return None
    
    def _get_cached_rules(self, customer_id: int) -> List[dict]:
        """获取缓存的告警规则"""
        cache_key = f"alert_rules:customer:{customer_id}"
        
        # 先检查内存缓存
        if cache_key in self.rule_cache:
            cached_time, rules = self.rule_cache[cache_key]
            if time.time() - cached_time < 300:  # 5分钟内存缓存
                return rules
        
        # Redis缓存
        cached_rules = self.redis.get_data(cache_key)
        if cached_rules:
            rules = json.loads(cached_rules)
            self.rule_cache[cache_key] = (time.time(), rules)
            return rules
            
        # 数据库查询并缓存
        rules = self._load_rules_from_db(customer_id)
        
        # 缓存到Redis（24小时）
        self.redis.set_data(cache_key, json.dumps(rules, default=str), expire=86400)
        self.rule_cache[cache_key] = (time.time(), rules)
        
        return rules
```

### 2. 管理界面设计

#### 2.1 规则管理页面结构
```typescript
// 前端界面设计 - Vue3 + Element Plus
interface AlertRuleConfig {
  id?: number;
  ruleName: string;
  ruleCategory: 'SINGLE' | 'COMPOSITE' | 'COMPLEX';
  ruleType: string;
  priorityLevel: number;
  
  // 单体征规则
  physicalSign?: string;
  thresholdMin?: number;
  thresholdMax?: number;
  trendDuration?: number;
  
  // 复合规则
  conditionExpression?: {
    conditions: Array<{
      physicalSign: string;
      operator: '>' | '<' | '=' | '>=' | '<=';
      threshold: number;
      durationSeconds: number;
    }>;
    logicalOperator: 'AND' | 'OR';
    evaluationWindow: number;
  };
  
  // 生效时间
  effectiveTimeStart?: string;
  effectiveTimeEnd?: string;
  effectiveDays: string;
  timeWindowSeconds: number;
  cooldownSeconds: number;
  
  // 告警配置
  severityLevel: string;
  alertMessage: string;
  notificationType: string;
  
  customerId: number;
  isActive: boolean;
}
```

#### 2.2 规则配置向导组件
```vue
<template>
  <div class="alert-rule-wizard">
    <!-- 步骤导航 -->
    <el-steps :active="currentStep" align-center>
      <el-step title="规则类型" />
      <el-step title="条件配置" />
      <el-step title="告警设置" />
      <el-step title="生效时间" />
      <el-step title="预览确认" />
    </el-steps>
    
    <!-- 规则类型选择 -->
    <div v-show="currentStep === 0" class="step-content">
      <el-card header="选择规则类型">
        <el-radio-group v-model="ruleConfig.ruleCategory" @change="onRuleCategoryChange">
          <el-radio label="SINGLE" class="rule-type-radio">
            <div class="rule-type-item">
              <h3>单体征规则</h3>
              <p>基于单个生理指标的阈值告警，如：心率 > 120</p>
            </div>
          </el-radio>
          <el-radio label="COMPOSITE" class="rule-type-radio">
            <div class="rule-type-item">
              <h3>复合规则</h3>
              <p>多个生理指标的组合条件，如：心率 > 120 且 血氧 < 90</p>
            </div>
          </el-radio>
          <el-radio label="COMPLEX" class="rule-type-radio">
            <div class="rule-type-item">
              <h3>复杂规则</h3>
              <p>高级逻辑表达式，支持自定义计算公式</p>
            </div>
          </el-radio>
        </el-radio-group>
      </el-card>
    </div>
    
    <!-- 单体征条件配置 -->
    <div v-show="currentStep === 1 && ruleConfig.ruleCategory === 'SINGLE'" class="step-content">
      <el-card header="单体征条件配置">
        <el-form :model="ruleConfig" label-width="120px">
          <el-form-item label="生理指标">
            <el-select v-model="ruleConfig.physicalSign" placeholder="选择生理指标">
              <el-option label="心率" value="heart_rate" />
              <el-option label="血氧" value="blood_oxygen" />
              <el-option label="体温" value="temperature" />
              <el-option label="收缩压" value="pressure_high" />
              <el-option label="舒张压" value="pressure_low" />
              <el-option label="步数" value="step" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="正常范围">
            <el-input-number v-model="ruleConfig.thresholdMin" placeholder="最小值" />
            <span style="margin: 0 10px;">至</span>
            <el-input-number v-model="ruleConfig.thresholdMax" placeholder="最大值" />
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
    <div v-show="currentStep === 1 && ruleConfig.ruleCategory === 'COMPOSITE'" class="step-content">
      <el-card header="复合条件配置">
        <div class="composite-conditions">
          <div v-for="(condition, index) in compositeConditions" :key="index" class="condition-item">
            <el-select v-model="condition.physicalSign" placeholder="生理指标">
              <el-option label="心率" value="heart_rate" />
              <el-option label="血氧" value="blood_oxygen" />
              <el-option label="体温" value="temperature" />
            </el-select>
            
            <el-select v-model="condition.operator" placeholder="运算符">
              <el-option label="大于" value=">" />
              <el-option label="小于" value="<" />
              <el-option label="等于" value="=" />
              <el-option label="大于等于" value=">=" />
              <el-option label="小于等于" value="<=" />
            </el-select>
            
            <el-input-number v-model="condition.threshold" placeholder="阈值" />
            
            <el-input-number v-model="condition.durationSeconds" placeholder="持续时间(秒)" />
            
            <el-button @click="removeCondition(index)" type="danger" icon="el-icon-delete" circle />
          </div>
          
          <div class="condition-logic">
            <el-radio-group v-model="logicalOperator">
              <el-radio label="AND">并且(AND)</el-radio>
              <el-radio label="OR">或者(OR)</el-radio>
            </el-radio-group>
          </div>
          
          <el-button @click="addCondition" type="primary" icon="el-icon-plus">添加条件</el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 实时预览 -->
    <div class="rule-preview">
      <el-card header="规则预览">
        <div class="preview-content">
          <p><strong>规则描述：</strong>{{ generateRuleDescription() }}</p>
          <p><strong>触发逻辑：</strong>{{ generateTriggerLogic() }}</p>
        </div>
      </el-card>
    </div>
    
    <!-- 操作按钮 -->
    <div class="wizard-actions">
      <el-button @click="previousStep" :disabled="currentStep === 0">上一步</el-button>
      <el-button @click="nextStep" type="primary" :disabled="!canNextStep">下一步</el-button>
      <el-button @click="saveRule" type="success" v-show="currentStep === 4">保存规则</el-button>
    </div>
  </div>
</template>
```

### 3. 高并发优化策略

#### 3.1 三层缓存架构
```python
class CachedRuleEngine:
    """三层缓存的告警规则引擎"""
    
    def __init__(self):
        # L1: 应用内存缓存 (最快，容量小)
        self.memory_cache = {}  # 5分钟TTL，最热数据
        
        # L2: Redis缓存 (快速，容量中等)  
        self.redis = RedisHelper()  # 1小时TTL，常用数据
        
        # L3: 数据库 (慢速，容量大)
        # 通过上层缓存减少数据库访问
        
    def get_rules_with_cache(self, customer_id: int) -> List[dict]:
        """三层缓存获取规则"""
        cache_key = f"rules:c{customer_id}"
        
        # L1: 内存缓存
        if cache_key in self.memory_cache:
            cached_time, rules = self.memory_cache[cache_key]
            if time.time() - cached_time < 300:  # 5分钟
                return rules
                
        # L2: Redis缓存
        redis_key = f"alert_rules:customer:{customer_id}"
        cached_rules = self.redis.get_data(redis_key)
        if cached_rules:
            rules = json.loads(cached_rules)
            # 回填L1缓存
            self.memory_cache[cache_key] = (time.time(), rules)
            return rules
            
        # L3: 数据库查询
        rules = self._query_rules_from_db(customer_id)
        
        # 回填缓存
        self.redis.set_data(redis_key, json.dumps(rules, default=str), expire=3600)
        self.memory_cache[cache_key] = (time.time(), rules)
        
        return rules
```

#### 3.2 规则预编译与索引优化
```python
class RuleCompiler:
    """规则预编译器 - 将规则转换为高效的执行结构"""
    
    def compile_rules(self, rules: List[dict]) -> dict:
        """编译规则为高效执行结构"""
        compiled_rules = {
            'single_rules': defaultdict(list),      # 按physical_sign分组
            'composite_rules': [],                   # 复合规则列表
            'priority_index': defaultdict(list),    # 按优先级索引
        }
        
        for rule in rules:
            if not rule.get('is_active'):
                continue
                
            priority = rule.get('priority_level', 5)
            
            if rule['rule_category'] == 'SINGLE':
                physical_sign = rule.get('physical_sign')
                if physical_sign:
                    compiled_rule = self._compile_single_rule(rule)
                    compiled_rules['single_rules'][physical_sign].append(compiled_rule)
                    compiled_rules['priority_index'][priority].append(compiled_rule)
                    
            elif rule['rule_category'] == 'COMPOSITE':
                compiled_rule = self._compile_composite_rule(rule)
                compiled_rules['composite_rules'].append(compiled_rule)
                compiled_rules['priority_index'][priority].append(compiled_rule)
                
        return compiled_rules
    
    def _compile_single_rule(self, rule: dict) -> dict:
        """编译单体征规则为高效结构"""
        return {
            'rule_id': rule['id'],
            'physical_sign': rule['physical_sign'],
            'check_min': rule.get('threshold_min') is not None,
            'check_max': rule.get('threshold_max') is not None,
            'threshold_min': rule.get('threshold_min', 0),
            'threshold_max': rule.get('threshold_max', float('inf')),
            'trend_duration': rule.get('trend_duration', 1),
            'time_window': rule.get('time_window_seconds', 300),
            'severity': rule.get('severity_level', 'MEDIUM'),
            'message_template': rule.get('alert_message', ''),
            'cooldown': rule.get('cooldown_seconds', 600),
            'priority': rule.get('priority_level', 5)
        }
```

#### 3.3 异步处理与批量优化
```python
class AsyncAlertProcessor:
    """异步告警处理器"""
    
    def __init__(self):
        self.alert_queue = asyncio.Queue(maxsize=10000)
        self.batch_size = 100
        self.workers = []
        
    async def start_workers(self, worker_count: int = 4):
        """启动异步工作者"""
        for i in range(worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
            
    async def process_alerts_batch(self, health_data_batch: List[dict]):
        """批量处理告警"""
        # 1. 按customer_id分组批次
        customer_batches = defaultdict(list)
        for data in health_data_batch:
            customer_id = data.get('customer_id')
            customer_batches[customer_id].append(data)
            
        # 2. 并行处理每个客户的数据
        tasks = []
        for customer_id, customer_data in customer_batches.items():
            task = self._process_customer_batch(customer_id, customer_data)
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_customer_batch(self, customer_id: int, health_data_list: List[dict]):
        """处理单个客户的健康数据批次"""
        # 1. 批量获取规则（一次查询）
        rules = await self._get_rules_async(customer_id)
        if not rules:
            return
            
        # 2. 编译规则（一次编译）
        compiled_rules = self.rule_compiler.compile_rules(rules)
        
        # 3. 批量评估
        alert_tasks = []
        for health_data in health_data_list:
            task = self._evaluate_single_data(health_data, compiled_rules)
            alert_tasks.append(task)
            
        results = await asyncio.gather(*alert_tasks, return_exceptions=True)
        
        # 4. 批量保存告警
        valid_alerts = [alert for alert in results if alert and not isinstance(alert, Exception)]
        if valid_alerts:
            await self._save_alerts_batch(valid_alerts)
```

### 4. 性能基准测试

#### 4.1 测试指标设计
```python
class PerformanceTestSuite:
    """告警规则系统性能测试套件"""
    
    async def test_rule_evaluation_performance(self):
        """规则评估性能测试"""
        test_scenarios = [
            {
                'name': '单体征规则-1000条',
                'rule_count': 1000,
                'rule_type': 'SINGLE',
                'data_points': 10000
            },
            {
                'name': '复合规则-500条', 
                'rule_count': 500,
                'rule_type': 'COMPOSITE',
                'data_points': 10000
            },
            {
                'name': '混合规则-高并发',
                'rule_count': 2000,
                'rule_type': 'MIXED',
                'data_points': 50000,
                'concurrent_requests': 100
            }
        ]
        
        for scenario in test_scenarios:
            start_time = time.time()
            
            # 执行测试场景
            await self._run_scenario(scenario)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 计算性能指标
            throughput = scenario['data_points'] / duration
            avg_latency = duration / scenario['data_points'] * 1000
            
            print(f"""
            场景: {scenario['name']}
            总耗时: {duration:.2f}s
            吞吐量: {throughput:.0f} records/s
            平均延迟: {avg_latency:.2f}ms
            """)
```

## 📈 实施计划

### 阶段一：向下兼容增强 (2周)
1. **数据库表结构增强** - 添加新字段，保持现有功能不变
2. **缓存机制优化** - 实现三层缓存架构
3. **性能基准测试** - 建立性能监控基线

### 阶段二：复合规则支持 (3周)
1. **规则引擎开发** - 支持多体征关联告警
2. **管理界面开发** - 可视化规则配置向导
3. **规则编译器** - 预编译优化执行效率

### 阶段三：高并发优化 (2周)  
1. **异步处理架构** - 批量处理和异步队列
2. **告警抑制机制** - 避免重复告警
3. **性能调优** - 达到目标性能指标

### 阶段四：生产部署 (1周)
1. **灰度发布** - 逐步替换现有系统
2. **监控告警** - 建立系统监控
3. **文档完善** - 用户手册和运维文档

## 🎯 预期效果

### 性能提升
- **规则评估速度**: 提升80%以上 (缓存优化)
- **并发处理能力**: 支持10倍以上并发 (异步架构)
- **内存使用**: 减少40% (规则预编译)

### 功能增强
- **规则表达能力**: 支持复杂的多体征关联告警
- **管理易用性**: 可视化配置界面，降低使用门槛
- **系统稳定性**: 告警抑制和冷却机制避免告警风暴

### 业务价值
- **告警准确性**: 减少80%以上误报 (复合条件)
- **响应速度**: 告警延迟降低到秒级
- **运维成本**: 减少50%以上人工干预

这个方案在保持系统稳定性的前提下，逐步提升告警规则的表达能力和处理性能，满足复杂业务场景的需求。