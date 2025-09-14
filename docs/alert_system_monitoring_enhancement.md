# 告警系统监控增强方案

## 📋 当前状况分析

### 观察到的日志信息
```
📊 性能统计: 处理时间=0.009s, 规则数量=25, Redis缓存=命中
Skipping rule 1963764274519986177: missing physical_sign
Skipping rule 1963764274524180481: missing physical_sign
Skipping rule 1963764274528374785: missing physical_sign
Skipping rule 1963764274515791873: missing physical_sign
```

### 问题识别
1. **告警规则执行效率高**: 25个规则仅用时0.009秒
2. **Redis缓存命中**: 性能良好
3. **数据完整性问题**: 多个规则因缺少`physical_sign`字段被跳过
4. **静默失败**: 跳过的规则没有统计和告警

## 🎯 监控增强目标

### 核心改进点
1. **告警规则执行监控**: 跟踪规则执行成功率和失败原因
2. **数据完整性监控**: 监控健康数据字段缺失情况
3. **告警系统性能监控**: 优化告警处理流程监控
4. **规则配置质量监控**: 识别无效或配置错误的规则

---

## 1. 告警规则执行监控

### 1.1 规则执行统计收集器

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from collections import defaultdict
import time
import json

@dataclass
class AlertRuleExecutionStats:
    """告警规则执行统计"""
    rule_id: str
    rule_name: Optional[str]
    execution_time: float
    status: str  # 'success', 'skipped', 'error'
    skip_reason: Optional[str]
    device_sn: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'execution_time': self.execution_time,
            'status': self.status,
            'skip_reason': self.skip_reason,
            'device_sn': self.device_sn,
            'timestamp': self.timestamp
        }

class AlertRuleMonitor:
    """告警规则监控器"""
    
    def __init__(self):
        self.execution_stats = []
        self.stats_lock = threading.Lock()
        self.summary_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'skipped_executions': 0,
            'error_executions': 0,
            'skip_reasons': defaultdict(int),
            'rule_performance': defaultdict(list)
        }
        
        # 启动统计输出线程
        self.start_stats_reporter()
        
        logger.info("🔍 AlertRuleMonitor已启动")
    
    def record_rule_execution(self, rule_id: str, rule_name: Optional[str], 
                            execution_time: float, status: str, 
                            skip_reason: Optional[str] = None, 
                            device_sn: str = 'unknown'):
        """记录规则执行结果"""
        stat = AlertRuleExecutionStats(
            rule_id=rule_id,
            rule_name=rule_name,
            execution_time=execution_time,
            status=status,
            skip_reason=skip_reason,
            device_sn=device_sn,
            timestamp=time.time()
        )
        
        with self.stats_lock:
            self.execution_stats.append(stat)
            
            # 更新汇总统计
            self.summary_stats['total_executions'] += 1
            if status == 'success':
                self.summary_stats['successful_executions'] += 1
            elif status == 'skipped':
                self.summary_stats['skipped_executions'] += 1
                if skip_reason:
                    self.summary_stats['skip_reasons'][skip_reason] += 1
            elif status == 'error':
                self.summary_stats['error_executions'] += 1
            
            # 记录规则性能
            self.summary_stats['rule_performance'][rule_id].append(execution_time)
            
            # 限制内存使用，保留最近1000条记录
            if len(self.execution_stats) > 1000:
                self.execution_stats = self.execution_stats[-1000:]
    
    def get_rule_execution_summary(self, time_window_minutes: int = 60) -> Dict:
        """获取规则执行汇总统计"""
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        with self.stats_lock:
            recent_stats = [
                stat for stat in self.execution_stats 
                if stat.timestamp > cutoff_time
            ]
        
        if not recent_stats:
            return {'message': 'No recent rule executions'}
        
        # 计算统计指标
        total_count = len(recent_stats)
        success_count = len([s for s in recent_stats if s.status == 'success'])
        skipped_count = len([s for s in recent_stats if s.status == 'skipped'])
        error_count = len([s for s in recent_stats if s.status == 'error'])
        
        # 跳过原因统计
        skip_reasons = defaultdict(int)
        for stat in recent_stats:
            if stat.skip_reason:
                skip_reasons[stat.skip_reason] += 1
        
        # 规则性能统计
        rule_performance = defaultdict(list)
        for stat in recent_stats:
            rule_performance[stat.rule_id].append(stat.execution_time)
        
        # 计算平均执行时间
        avg_performance = {}
        for rule_id, times in rule_performance.items():
            avg_performance[rule_id] = {
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times),
                'execution_count': len(times)
            }
        
        return {
            'time_window_minutes': time_window_minutes,
            'summary': {
                'total_executions': total_count,
                'success_rate': success_count / total_count if total_count > 0 else 0,
                'skip_rate': skipped_count / total_count if total_count > 0 else 0,
                'error_rate': error_count / total_count if total_count > 0 else 0
            },
            'skip_reasons': dict(skip_reasons),
            'rule_performance': avg_performance,
            'timestamp': time.time()
        }
    
    def start_stats_reporter(self):
        """启动统计报告线程"""
        def reporter_worker():
            while True:
                try:
                    time.sleep(300)  # 每5分钟输出一次统计
                    summary = self.get_rule_execution_summary(60)  # 最近1小时统计
                    
                    if 'summary' in summary:
                        logger.info(f"📊 告警规则执行统计: {json.dumps(summary, ensure_ascii=False, indent=2)}")
                        
                        # 检查是否有问题需要告警
                        self._check_rule_execution_alerts(summary)
                    
                except Exception as e:
                    logger.error(f"统计报告线程异常: {e}")
        
        thread = threading.Thread(target=reporter_worker, daemon=True)
        thread.start()
    
    def _check_rule_execution_alerts(self, summary: Dict):
        """检查规则执行相关告警"""
        summary_data = summary.get('summary', {})
        
        # 高跳过率告警
        skip_rate = summary_data.get('skip_rate', 0)
        if skip_rate > 0.3:  # 30%以上跳过率
            logger.warning(f"🚨 告警规则跳过率过高: {skip_rate:.2%}")
        
        # 高错误率告警
        error_rate = summary_data.get('error_rate', 0) 
        if error_rate > 0.05:  # 5%以上错误率
            logger.critical(f"🚨 告警规则错误率过高: {error_rate:.2%}")
        
        # 特定跳过原因告警
        skip_reasons = summary.get('skip_reasons', {})
        for reason, count in skip_reasons.items():
            if count > 50:  # 单个原因跳过超过50次
                logger.warning(f"🚨 频繁跳过告警规则: {reason} ({count}次)")

# 全局监控器实例
alert_rule_monitor = AlertRuleMonitor()
```

### 1.2 集成到现有告警系统

```python
# 在现有的告警处理逻辑中添加监控
def enhanced_alert_processing(health_data, device_sn):
    """增强的告警处理，包含监控功能"""
    
    start_time = time.time()
    total_rules = 0
    processed_rules = 0
    skipped_rules = 0
    
    try:
        # 获取告警规则
        rules = get_alert_rules(device_sn, health_data.get('customer_id'))
        total_rules = len(rules)
        
        logger.info(f"📊 开始处理告警: device_sn={device_sn}, 规则数量={total_rules}")
        
        for rule in rules:
            rule_start_time = time.time()
            rule_id = str(rule.get('id', 'unknown'))
            rule_name = rule.get('name', 'unnamed')
            
            try:
                # 检查规则执行条件
                if not _check_rule_conditions(rule, health_data):
                    skip_reason = _determine_skip_reason(rule, health_data)
                    
                    # 记录跳过统计
                    alert_rule_monitor.record_rule_execution(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        execution_time=time.time() - rule_start_time,
                        status='skipped',
                        skip_reason=skip_reason,
                        device_sn=device_sn
                    )
                    
                    skipped_rules += 1
                    logger.debug(f"Skipping rule {rule_id}: {skip_reason}")
                    continue
                
                # 执行告警规则
                alert_result = execute_alert_rule(rule, health_data, device_sn)
                
                # 记录成功统计
                alert_rule_monitor.record_rule_execution(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    execution_time=time.time() - rule_start_time,
                    status='success',
                    device_sn=device_sn
                )
                
                processed_rules += 1
                
            except Exception as rule_error:
                # 记录错误统计
                alert_rule_monitor.record_rule_execution(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    execution_time=time.time() - rule_start_time,
                    status='error',
                    skip_reason=str(rule_error),
                    device_sn=device_sn
                )
                
                logger.error(f"规则执行失败 {rule_id}: {rule_error}")
        
        # 输出处理统计
        total_time = time.time() - start_time
        cache_status = "命中" if _check_redis_cache_hit() else "未命中"
        
        logger.info(f"📊 性能统计: 处理时间={total_time:.3f}s, 规则数量={total_rules}, "
                   f"成功={processed_rules}, 跳过={skipped_rules}, Redis缓存={cache_status}")
        
    except Exception as e:
        logger.error(f"告警处理异常: {e}")

def _determine_skip_reason(rule: Dict, health_data: Dict) -> str:
    """确定规则跳过原因"""
    required_fields = rule.get('required_fields', [])
    
    for field in required_fields:
        if field not in health_data or health_data[field] is None:
            return f"missing {field}"
    
    # 检查其他跳过条件
    if rule.get('enabled', True) == False:
        return "rule disabled"
    
    if not _check_time_conditions(rule):
        return "time condition not met"
    
    if not _check_device_conditions(rule, health_data):
        return "device condition not met"
    
    return "unknown reason"
```

## 2. 数据完整性监控

### 2.1 健康数据字段完整性检查

```python
class HealthDataCompletenessMonitor:
    """健康数据完整性监控器"""
    
    def __init__(self):
        self.field_stats = defaultdict(lambda: {'total': 0, 'missing': 0, 'null': 0})
        self.stats_lock = threading.Lock()
        
        # 定义预期的健康数据字段
        self.expected_fields = {
            'basic_vitals': ['heart_rate', 'blood_oxygen', 'temperature'],
            'blood_pressure': ['pressure_high', 'pressure_low'],
            'activity': ['step', 'distance', 'calorie'],
            'location': ['latitude', 'longitude', 'altitude'],
            'physical_signs': ['physical_sign'],  # 导致告警规则跳过的字段
            'sleep': ['sleep', 'sleepData'],
            'exercise': ['exerciseDailyData', 'exerciseWeekData'],
            'device': ['deviceSn', 'upload_method', 'timestamp']
        }
        
        logger.info("🔍 HealthDataCompletenessMonitor已启动")
    
    def check_data_completeness(self, health_data: Dict, device_sn: str = 'unknown') -> Dict:
        """检查健康数据完整性"""
        completeness_report = {
            'device_sn': device_sn,
            'timestamp': time.time(),
            'field_categories': {},
            'overall_completeness': 0.0,
            'missing_fields': [],
            'null_fields': []
        }
        
        total_fields = 0
        complete_fields = 0
        
        for category, fields in self.expected_fields.items():
            category_stats = {
                'total_fields': len(fields),
                'complete_fields': 0,
                'missing_fields': [],
                'null_fields': [],
                'completeness_rate': 0.0
            }
            
            for field in fields:
                total_fields += 1
                
                with self.stats_lock:
                    self.field_stats[field]['total'] += 1
                
                if field not in health_data:
                    # 字段完全缺失
                    category_stats['missing_fields'].append(field)
                    completeness_report['missing_fields'].append(field)
                    
                    with self.stats_lock:
                        self.field_stats[field]['missing'] += 1
                        
                elif health_data[field] is None or health_data[field] == 'null' or health_data[field] == '':
                    # 字段存在但值为空
                    category_stats['null_fields'].append(field)
                    completeness_report['null_fields'].append(field)
                    
                    with self.stats_lock:
                        self.field_stats[field]['null'] += 1
                else:
                    # 字段完整
                    category_stats['complete_fields'] += 1
                    complete_fields += 1
            
            category_stats['completeness_rate'] = (
                category_stats['complete_fields'] / category_stats['total_fields']
                if category_stats['total_fields'] > 0 else 0
            )
            
            completeness_report['field_categories'][category] = category_stats
        
        # 计算整体完整性
        completeness_report['overall_completeness'] = (
            complete_fields / total_fields if total_fields > 0 else 0
        )
        
        return completeness_report
    
    def get_completeness_summary(self, time_window_minutes: int = 60) -> Dict:
        """获取数据完整性汇总统计"""
        with self.stats_lock:
            field_summary = {}
            
            for field, stats in self.field_stats.items():
                if stats['total'] > 0:
                    field_summary[field] = {
                        'total_checks': stats['total'],
                        'missing_rate': stats['missing'] / stats['total'],
                        'null_rate': stats['null'] / stats['total'],
                        'completeness_rate': 1 - (stats['missing'] + stats['null']) / stats['total']
                    }
        
        return {
            'time_window_minutes': time_window_minutes,
            'field_completeness': field_summary,
            'timestamp': time.time()
        }

# 全局完整性监控器
health_completeness_monitor = HealthDataCompletenessMonitor()
```

### 2.2 集成到数据处理流程

```python
def enhanced_health_data_processing(health_data, device_sn):
    """增强的健康数据处理，包含完整性检查"""
    
    # 1. 数据完整性检查
    completeness_report = health_completeness_monitor.check_data_completeness(
        health_data, device_sn
    )
    
    # 2. 记录完整性问题
    if completeness_report['overall_completeness'] < 0.8:  # 80%完整性阈值
        logger.warning(f"📊 数据完整性较低: device_sn={device_sn}, "
                      f"完整性={completeness_report['overall_completeness']:.2%}")
        
        # 记录缺失的关键字段
        missing_critical = set(completeness_report['missing_fields']).intersection({
            'physical_sign', 'heart_rate', 'blood_oxygen', 'temperature'
        })
        
        if missing_critical:
            logger.warning(f"🚨 关键字段缺失: {list(missing_critical)}")
    
    # 3. 继续正常处理流程
    return process_health_data(health_data, device_sn)
```

## 3. 监控API端点

### 3.1 告警系统监控API

```python
@app.route('/api/alert_system/stats', methods=['GET'])
def alert_system_stats():
    """获取告警系统统计信息"""
    try:
        time_window = request.args.get('time_window', 60, type=int)
        
        # 获取规则执行统计
        rule_stats = alert_rule_monitor.get_rule_execution_summary(time_window)
        
        # 获取数据完整性统计
        completeness_stats = health_completeness_monitor.get_completeness_summary(time_window)
        
        return jsonify({
            'timestamp': time.time(),
            'time_window_minutes': time_window,
            'rule_execution': rule_stats,
            'data_completeness': completeness_stats
        })
        
    except Exception as e:
        logger.error(f"获取告警系统统计失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert_system/health', methods=['GET'])
def alert_system_health():
    """告警系统健康检查"""
    try:
        rule_stats = alert_rule_monitor.get_rule_execution_summary(60)
        completeness_stats = health_completeness_monitor.get_completeness_summary(60)
        
        # 计算健康状态
        health_issues = []
        overall_status = 'healthy'
        
        # 检查规则执行健康状态
        if 'summary' in rule_stats:
            skip_rate = rule_stats['summary'].get('skip_rate', 0)
            error_rate = rule_stats['summary'].get('error_rate', 0)
            
            if error_rate > 0.1:
                health_issues.append(f"高规则错误率: {error_rate:.2%}")
                overall_status = 'unhealthy'
            elif skip_rate > 0.5:
                health_issues.append(f"高规则跳过率: {skip_rate:.2%}")
                overall_status = 'degraded' if overall_status == 'healthy' else overall_status
        
        # 检查数据完整性健康状态
        field_completeness = completeness_stats.get('field_completeness', {})
        critical_fields = ['heart_rate', 'blood_oxygen', 'physical_sign']
        
        for field in critical_fields:
            if field in field_completeness:
                completeness_rate = field_completeness[field]['completeness_rate']
                if completeness_rate < 0.5:
                    health_issues.append(f"关键字段{field}完整性低: {completeness_rate:.2%}")
                    overall_status = 'unhealthy'
        
        return jsonify({
            'status': overall_status,
            'timestamp': time.time(),
            'health_issues': health_issues,
            'checks': {
                'rule_execution_health': 'healthy' if not any('规则' in issue for issue in health_issues) else 'unhealthy',
                'data_completeness_health': 'healthy' if not any('字段' in issue for issue in health_issues) else 'unhealthy'
            },
            'details': {
                'rule_stats': rule_stats,
                'completeness_stats': completeness_stats
            }
        })
        
    except Exception as e:
        logger.error(f"告警系统健康检查失败: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': time.time(),
            'error': str(e)
        }), 500
```

## 4. 实施建议

### 4.1 立即实施 (1-2天)

1. **集成规则执行监控**
   - 在现有告警处理逻辑中添加监控代码
   - 开始收集规则跳过统计
   - 添加性能统计日志

2. **添加监控API**
   - 实现 `/api/alert_system/health` 健康检查端点
   - 实现 `/api/alert_system/stats` 统计查询端点

### 4.2 后续优化 (3-5天)

1. **完善数据完整性监控**
   - 实现HealthDataCompletenessMonitor
   - 集成到数据处理流程

2. **告警规则质量分析**
   - 分析经常被跳过的规则
   - 优化规则配置
   - 清理无效规则

### 4.3 预期改进效果

1. **可观测性提升**
   - 告警规则执行情况完全透明
   - 数据质量问题及时发现
   - 系统健康状态实时监控

2. **运维效率提升**
   - 快速定位告警规则问题
   - 数据质量问题预警
   - 自动化健康检查

3. **系统稳定性提升**
   - 减少因数据问题导致的告警失效
   - 提高告警系统可靠性
   - 优化规则配置质量

---

## 总结

基于观察到的日志信息，这个监控增强方案针对性地解决了：

1. **规则跳过问题**: 通过监控统计跳过原因，识别数据质量问题
2. **性能监控**: 增强现有的性能统计，提供更详细的执行分析
3. **数据完整性**: 建立完整的字段缺失监控体系
4. **系统健康**: 提供告警系统的整体健康状态评估

这些改进可以帮助更好地理解和优化告警系统的运行状况，提高整体的可靠性和效率。