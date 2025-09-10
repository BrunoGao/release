-- =============================================================================
-- 告警规则表租户过滤修复脚本
-- 解决压测中发现的性能问题：查询全部248条规则 -> 按租户过滤
-- =============================================================================

-- 1. 检查当前数据状况
SELECT '=== 当前告警规则统计 ===' as info;

SELECT 
    COUNT(*) as total_rules,
    COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) as valid_rules,
    COUNT(CASE WHEN physical_sign IS NULL OR physical_sign = '' THEN 1 END) as invalid_rules,
    COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted_rules
FROM t_alert_rules;

-- 2. 检查规则类型分布
SELECT '=== 规则类型分布 ===' as info;

SELECT rule_type, COUNT(*) as count, 
       COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) as valid_count
FROM t_alert_rules 
WHERE is_deleted = 0 
GROUP BY rule_type 
ORDER BY count DESC 
LIMIT 10;

-- 3. 添加customer_id字段
SELECT '=== 添加customer_id字段 ===' as info;

ALTER TABLE t_alert_rules 
ADD COLUMN customer_id BIGINT DEFAULT 1 COMMENT '客户ID';

-- 4. 创建索引（提升按租户查询性能）
SELECT '=== 创建索引 ===' as info;

CREATE INDEX idx_alert_rules_customer_deleted ON t_alert_rules(customer_id, is_deleted);
CREATE INDEX idx_alert_rules_customer_type ON t_alert_rules(customer_id, rule_type);

-- 5. 更新现有数据
SELECT '=== 更新现有数据 ===' as info;

-- 将所有现有规则设置为customer_id=1
UPDATE t_alert_rules 
SET customer_id = 1 
WHERE customer_id IS NULL OR customer_id = 0;

-- 6. 设置字段为非空
SELECT '=== 设置非空约束 ===' as info;

ALTER TABLE t_alert_rules 
MODIFY COLUMN customer_id BIGINT NOT NULL COMMENT '客户ID';

-- 7. 清理无效规则（physical_sign为空的规则）
SELECT '=== 清理无效规则 ===' as info;

-- 先查看要清理的规则
SELECT 
    id, rule_type, physical_sign, alert_message,
    CASE 
        WHEN physical_sign IS NULL THEN 'NULL'
        WHEN physical_sign = '' THEN 'EMPTY'
        ELSE 'VALID'
    END as sign_status
FROM t_alert_rules 
WHERE is_deleted = 0 
  AND (physical_sign IS NULL OR physical_sign = '' OR TRIM(physical_sign) = '')
ORDER BY rule_type;

-- 可选：删除无效规则（谨慎执行，建议先备份）
-- UPDATE t_alert_rules 
-- SET is_deleted = 1, 
--     update_time = NOW(),
--     update_user = 'system_cleanup'
-- WHERE is_deleted = 0 
--   AND (physical_sign IS NULL OR physical_sign = '' OR TRIM(physical_sign) = '');

-- 8. 修复常见physical_sign缺失问题
SELECT '=== 修复physical_sign ===' as info;

-- 基于rule_type推断并修复physical_sign
UPDATE t_alert_rules SET physical_sign = 'heartRate' 
WHERE rule_type LIKE '%heart_rate%' AND (physical_sign IS NULL OR physical_sign = '');

UPDATE t_alert_rules SET physical_sign = 'bloodPressure' 
WHERE rule_type LIKE '%blood_pressure%' AND (physical_sign IS NULL OR physical_sign = '');

UPDATE t_alert_rules SET physical_sign = 'bloodOxygen' 
WHERE rule_type LIKE '%blood_oxygen%' AND (physical_sign IS NULL OR physical_sign = '');

UPDATE t_alert_rules SET physical_sign = 'temperature' 
WHERE rule_type LIKE '%temperature%' AND (physical_sign IS NULL OR physical_sign = '');

UPDATE t_alert_rules SET physical_sign = 'step' 
WHERE rule_type LIKE '%step%' AND (physical_sign IS NULL OR physical_sign = '');

UPDATE t_alert_rules SET physical_sign = 'sleep' 
WHERE rule_type LIKE '%sleep%' AND (physical_sign IS NULL OR physical_sign = '');

-- 9. 验证修复结果
SELECT '=== 修复结果验证 ===' as info;

-- 按customer_id统计
SELECT 
    customer_id,
    COUNT(*) as total_rules,
    COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) as valid_rules,
    COUNT(CASE WHEN physical_sign IS NULL OR physical_sign = '' THEN 1 END) as invalid_rules
FROM t_alert_rules 
WHERE is_deleted = 0
GROUP BY customer_id;

-- 检查修复后的规则分布
SELECT 
    rule_type, 
    physical_sign,
    COUNT(*) as count
FROM t_alert_rules 
WHERE is_deleted = 0 AND customer_id = 1
GROUP BY rule_type, physical_sign
ORDER BY rule_type, count DESC;

-- 10. 性能测试查询
SELECT '=== 性能测试 ===' as info;

-- 修复前的查询（全量）
EXPLAIN SELECT * FROM t_alert_rules WHERE is_deleted = 0;

-- 修复后的查询（按租户过滤）
EXPLAIN SELECT * FROM t_alert_rules WHERE customer_id = 1 AND is_deleted = 0;

-- 11. 最终统计
SELECT '=== 最终统计 ===' as info;

SELECT 
    '修复完成' as status,
    COUNT(*) as total_rules,
    COUNT(CASE WHEN customer_id = 1 THEN 1 END) as customer_1_rules,
    COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) as valid_rules,
    COUNT(CASE WHEN physical_sign IS NULL OR physical_sign = '' THEN 1 END) as remaining_invalid_rules,
    ROUND(
        COUNT(CASE WHEN physical_sign IS NOT NULL AND physical_sign != '' THEN 1 END) / COUNT(*) * 100, 
        2
    ) as valid_percentage
FROM t_alert_rules 
WHERE is_deleted = 0;

-- 12. 建议的应用层查询优化
SELECT '=== 建议的应用层查询 ===' as info;

-- 替换原来的查询：
-- AlertRules.query.filter_by(is_deleted=False).all()  -- 248条规则
-- 
-- 改为：
-- AlertRules.query.filter_by(customer_id=customer_id, is_deleted=False).all()  -- 约15-20条规则

SELECT 'SQL修复脚本执行完成！' as final_status;
SELECT '请更新Python代码中的查询逻辑以使用customer_id过滤' as next_step;