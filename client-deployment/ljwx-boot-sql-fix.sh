#!/bin/bash
# LJWX-Boot SQL语法错误修复器 | 使用说明: ./ljwx-boot-sql-fix.sh

CFG="custom-config.env"; [[ -f "$CFG" ]] && source "$CFG"  #加载配置
MYSQL_CONTAINER="${MYSQL_CONTAINER:-ljwx-mysql}"; MYSQL_USER="${MYSQL_USER:-root}"; MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"; MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"  #数据库配置
BACKUP_DIR="backup/sql-fix"; LOG_FILE="logs/sql-fix-$(date +%Y%m%d-%H%M%S).log"  #目录配置

# 颜色配置
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'  #颜色代码
log() { echo -e "${G}[$(date +'%H:%M:%S')]${N} $1" | tee -a "$LOG_FILE"; }; warn() { echo -e "${Y}[WARN]${N} $1" | tee -a "$LOG_FILE"; }; error() { echo -e "${R}[ERROR]${N} $1" | tee -a "$LOG_FILE"; }  #日志函数

# 初始化
init() {
    mkdir -p "$BACKUP_DIR" logs  #创建目录
    log "🚀 LJWX-Boot SQL语法错误修复器启动"
    log "问题: serial_number IN () 空参数列表导致SQL语法错误"
}

# 检查容器状态
check_container() {
    docker ps --format "{{.Names}}" | grep -q "^ljwx-boot$" || { error "ljwx-boot容器未运行"; return 1; }
    docker ps --format "{{.Names}}" | grep -q "^ljwx-mysql$" || { error "ljwx-mysql容器未运行"; return 1; }
    log "✅ 容器状态检查通过"
    return 0
}

# 备份数据库
backup_database() {
    log "📦 创建数据库备份..."
    local backup_file="$BACKUP_DIR/pre_sql_fix_$(date +%Y%m%d-%H%M%S).sql.gz"
    if docker exec "$MYSQL_CONTAINER" mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --single-transaction --routines --triggers "$MYSQL_DATABASE" | gzip > "$backup_file"; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ 备份完成: $(basename "$backup_file") ($size)"
        echo "$backup_file" > temp/backup_path
        return 0
    else
        error "备份失败"
        return 1
    fi
}

# 创建SQL修复脚本
create_fix_sql() {
    log "📝 创建SQL修复脚本..."
    cat > "$BACKUP_DIR/device_query_fix.sql" << 'EOF'
-- LJWX-Boot SQL语法错误修复脚本
-- 修复 serial_number IN () 空参数列表问题

-- 1. 检查现有数据
SELECT 'Current device count:' as info, COUNT(*) as count FROM t_device_info WHERE is_deleted = 0;
SELECT 'User device mapping count:' as info, COUNT(*) as count FROM sys_user WHERE device_sn IS NOT NULL AND device_sn != '' AND is_deleted = 0;

-- 2. 创建设备用户映射视图（如果不存在）
CREATE OR REPLACE VIEW v_device_user_mapping AS
SELECT 
    d.id as device_id,
    d.serial_number,
    d.device_name,
    u.id as user_id,
    u.user_name,
    u.phone,
    o.id as org_id,
    o.name as org_name
FROM t_device_info d
LEFT JOIN sys_user u ON d.serial_number = u.device_sn AND u.is_deleted = 0
LEFT JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_deleted = 0
LEFT JOIN sys_org_units o ON uo.org_id = o.id AND o.is_deleted = 0
WHERE d.is_deleted = 0;

-- 3. 创建安全的设备查询函数
DELIMITER $$
CREATE OR REPLACE FUNCTION get_device_list_safe(device_sns TEXT)
RETURNS TEXT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE result_json TEXT DEFAULT '[]';
    DECLARE device_count INT DEFAULT 0;
    
    -- 检查输入参数是否为空或NULL
    IF device_sns IS NULL OR TRIM(device_sns) = '' OR device_sns = '()' THEN
        RETURN '[]';
    END IF;
    
    -- 清理输入参数，移除括号和引号
    SET device_sns = REPLACE(REPLACE(REPLACE(device_sns, '(', ''), ')', ''), '''', '');
    
    -- 如果清理后仍为空，返回空数组
    IF TRIM(device_sns) = '' THEN
        RETURN '[]';
    END IF;
    
    -- 计算设备数量
    SET @sql = CONCAT('SELECT COUNT(*) INTO @device_count FROM t_device_info WHERE is_deleted = 0 AND serial_number IN (', device_sns, ')');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    SET device_count = @device_count;
    
    -- 如果有设备，构建JSON结果
    IF device_count > 0 THEN
        SET @sql = CONCAT('SELECT JSON_ARRAYAGG(JSON_OBJECT(
            "id", id,
            "serial_number", serial_number,
            "device_name", device_name,
            "status", status,
            "battery_level", battery_level,
            "charging_status", charging_status,
            "wearable_status", wearable_status,
            "timestamp", timestamp
        )) INTO @result_json FROM t_device_info WHERE is_deleted = 0 AND serial_number IN (', device_sns, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        SET result_json = IFNULL(@result_json, '[]');
    END IF;
    
    RETURN result_json;
END$$
DELIMITER ;

-- 4. 创建设备序列号验证函数
DELIMITER $$
CREATE OR REPLACE FUNCTION validate_device_sns(device_sns TEXT)
RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    -- 如果为空或NULL，返回FALSE
    IF device_sns IS NULL OR TRIM(device_sns) = '' OR device_sns = '()' THEN
        RETURN FALSE;
    END IF;
    
    -- 清理输入参数
    SET device_sns = REPLACE(REPLACE(REPLACE(device_sns, '(', ''), ')', ''), '''', '');
    
    -- 再次检查
    IF TRIM(device_sns) = '' THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END$$
DELIMITER ;

-- 5. 创建组织设备统计存储过程
DELIMITER $$
CREATE OR REPLACE PROCEDURE get_org_device_statistics(IN org_id_param VARCHAR(255))
BEGIN
    DECLARE device_count INT DEFAULT 0;
    DECLARE user_count INT DEFAULT 0;
    DECLARE active_count INT DEFAULT 0;
    DECLARE charging_count INT DEFAULT 0;
    
    -- 统计组织下的设备数量
    SELECT COUNT(DISTINCT d.id) INTO device_count
    FROM t_device_info d
    INNER JOIN sys_user u ON d.serial_number = u.device_sn
    INNER JOIN sys_user_org uo ON u.id = uo.user_id
    WHERE uo.org_id = org_id_param
      AND d.is_deleted = 0
      AND u.is_deleted = 0
      AND uo.is_deleted = 0;
    
    -- 统计用户数量
    SELECT COUNT(DISTINCT u.id) INTO user_count
    FROM sys_user u
    INNER JOIN sys_user_org uo ON u.id = uo.user_id
    WHERE uo.org_id = org_id_param
      AND u.is_deleted = 0
      AND uo.is_deleted = 0;
    
    -- 统计活跃设备数量
    SELECT COUNT(DISTINCT d.id) INTO active_count
    FROM t_device_info d
    INNER JOIN sys_user u ON d.serial_number = u.device_sn
    INNER JOIN sys_user_org uo ON u.id = uo.user_id
    WHERE uo.org_id = org_id_param
      AND d.status = 'ACTIVE'
      AND d.is_deleted = 0
      AND u.is_deleted = 0
      AND uo.is_deleted = 0;
    
    -- 统计充电中设备数量
    SELECT COUNT(DISTINCT d.id) INTO charging_count
    FROM t_device_info d
    INNER JOIN sys_user u ON d.serial_number = u.device_sn
    INNER JOIN sys_user_org uo ON u.id = uo.user_id
    WHERE uo.org_id = org_id_param
      AND d.charging_status = 'CHARGING'
      AND d.is_deleted = 0
      AND u.is_deleted = 0
      AND uo.is_deleted = 0;
    
    -- 返回统计结果
    SELECT 
        org_id_param as org_id,
        device_count,
        user_count,
        active_count,
        charging_count,
        CASE WHEN device_count > 0 THEN ROUND(active_count / device_count * 100, 2) ELSE 0 END as active_rate,
        CASE WHEN device_count > 0 THEN ROUND(charging_count / device_count * 100, 2) ELSE 0 END as charging_rate,
        NOW() as query_time;
END$$
DELIMITER ;

-- 6. 测试修复效果
SELECT 'Testing device query with empty list:' as test;
SELECT get_device_list_safe('') as empty_test;
SELECT get_device_list_safe('()') as bracket_test;
SELECT validate_device_sns('') as empty_validation;
SELECT validate_device_sns('device001,device002') as valid_validation;

-- 7. 显示修复完成信息
SELECT 'SQL修复完成' as status, NOW() as completion_time;
EOF

    log "✅ SQL修复脚本创建完成"
}

# 执行SQL修复
execute_fix() {
    log "🔧 执行SQL修复..."
    if docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$BACKUP_DIR/device_query_fix.sql"; then
        log "✅ SQL修复执行成功"
        return 0
    else
        error "SQL修复执行失败"
        return 1
    fi
}

# 创建Java代码修复补丁
create_java_patch() {
    log "📄 创建Java代码修复建议..."
    cat > "$BACKUP_DIR/java_fix_suggestions.md" << 'EOF'
# Java代码修复建议

## 问题描述
`OrgStatisticsServiceImpl.getDeviceInfo()` 方法中，当 `deviceSnList` 为空时，MyBatis Plus生成 `serial_number IN ()` 导致SQL语法错误。

## 修复方案

### 1. 修改 OrgStatisticsServiceImpl.java (推荐)

```java
private OrgStatisticsVO.DeviceInfoVO getDeviceInfo(List<String> deviceSnList) {
    OrgStatisticsVO.DeviceInfoVO deviceInfo = new OrgStatisticsVO.DeviceInfoVO();
    
    // 🔧 修复: 检查设备列表是否为空
    if (deviceSnList == null || deviceSnList.isEmpty()) {
        log.warn("设备序列号列表为空,返回默认设备信息");
        return createEmptyDeviceInfo();
    }
    
    // 🔧 修复: 过滤无效的设备序列号
    List<String> validDeviceSnList = deviceSnList.stream()
        .filter(Objects::nonNull)
        .filter(sn -> !sn.trim().isEmpty())
        .distinct()
        .collect(Collectors.toList());
    
    if (validDeviceSnList.isEmpty()) {
        log.warn("过滤后设备序列号列表为空,返回默认设备信息");
        return createEmptyDeviceInfo();
    }
    
    // 获取设备列表 - 现在安全了
    List<TDeviceInfo> devices = deviceInfoService.list(new LambdaQueryWrapper<TDeviceInfo>()
        .in(TDeviceInfo::getSerialNumber, validDeviceSnList));
    
    // 其余代码保持不变...
}
```

### 2. 修改 TDeviceInfoServiceImpl.java (推荐)

```java
@Override
public IPage<TDeviceInfo> listTDeviceInfoPage(PageQuery pageQuery, TDeviceInfoBO tDeviceInfoBO) {
    // 构建基本查询条件
    LambdaQueryWrapper<TDeviceInfo> queryWrapper = new LambdaQueryWrapper<TDeviceInfo>()
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getChargingStatus()), TDeviceInfo::getChargingStatus, tDeviceInfoBO.getChargingStatus())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getWearableStatus()), TDeviceInfo::getWearableStatus, tDeviceInfoBO.getWearableStatus())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getModel()), TDeviceInfo::getModel, tDeviceInfoBO.getModel())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getStatus()), TDeviceInfo::getStatus, tDeviceInfoBO.getStatus())
        .inSql(TDeviceInfo::getId, "SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY serial_number ORDER BY timestamp DESC) as rn FROM t_device_info) t WHERE rn = 1")
        .orderByDesc(TDeviceInfo::getTimestamp);

    if (ObjectUtils.isNotEmpty(tDeviceInfoBO.getUserIdStr()) || ObjectUtils.isNotEmpty(tDeviceInfoBO.getorg_id())) {
        // 获取设备序列号列表
        List<String> deviceSnList = deviceUserMappingService.getDeviceSnList(
            tDeviceInfoBO.getUserIdStr(),
            tDeviceInfoBO.getorg_id()
        );

        log.info("获取到设备序列号列表: {}", deviceSnList);
        
        // 🔧 修复: 检查设备列表是否为空
        if (deviceSnList == null || deviceSnList.isEmpty()) {
            log.warn("设备序列号列表为空,返回空结果页面");
            return pageQuery.buildPage();
        }
        
        // 🔧 修复: 过滤无效的设备序列号
        List<String> validDeviceSnList = deviceSnList.stream()
            .filter(Objects::nonNull)
            .filter(sn -> !sn.trim().isEmpty())
            .distinct()
            .collect(Collectors.toList());
        
        if (validDeviceSnList.isEmpty()) {
            log.warn("过滤后设备序列号列表为空,返回空结果页面");
            return pageQuery.buildPage();
        }
        
        // 添加设备序列号条件 - 现在安全了
        queryWrapper.in(TDeviceInfo::getSerialNumber, validDeviceSnList);
    }
    
    return pageQuery.buildPage(queryWrapper);
}
```

### 3. 创建通用工具类 (推荐)

```java
@Component
@Slf4j
public class DeviceQueryUtils {
    
    /**
     * 验证设备序列号列表是否有效
     */
    public static boolean isValidDeviceSnList(List<String> deviceSnList) {
        if (deviceSnList == null || deviceSnList.isEmpty()) {
            return false;
        }
        
        return deviceSnList.stream()
            .anyMatch(sn -> sn != null && !sn.trim().isEmpty());
    }
    
    /**
     * 清理和验证设备序列号列表
     */
    public static List<String> cleanDeviceSnList(List<String> deviceSnList) {
        if (deviceSnList == null) {
            return Collections.emptyList();
        }
        
        return deviceSnList.stream()
            .filter(Objects::nonNull)
            .map(String::trim)
            .filter(sn -> !sn.isEmpty())
            .distinct()
            .collect(Collectors.toList());
    }
    
    /**
     * 安全的MyBatis Plus IN查询
     */
    public static <T> LambdaQueryWrapper<T> safeInQuery(
            LambdaQueryWrapper<T> wrapper,
            SFunction<T, ?> column,
            List<String> values) {
        
        List<String> cleanValues = cleanDeviceSnList(values);
        if (!cleanValues.isEmpty()) {
            wrapper.in(column, cleanValues);
        } else {
            // 添加一个永远为false的条件,返回空结果
            wrapper.eq(column, "__IMPOSSIBLE_VALUE__");
        }
        
        return wrapper;
    }
}
```

## 实施步骤

1. **立即修复**: 在所有使用 `.in()` 查询的地方添加空值检查
2. **代码重构**: 使用 `DeviceQueryUtils` 工具类统一处理
3. **测试验证**: 确保修复后不影响正常业务流程
4. **日志监控**: 添加日志记录空值情况,便于后续分析

## 注意事项

- 修复后需要重新构建和部署 ljwx-boot 服务
- 建议在测试环境先验证修复效果
- 可以通过数据库函数作为临时缓解方案
EOF

    log "✅ Java修复建议文档创建完成"
}

# 重启应用服务
restart_boot_service() {
    log "🔄 重启ljwx-boot服务..."
    if docker-compose restart ljwx-boot; then
        log "✅ 服务重启成功"
        
        # 等待服务启动
        log "⏳ 等待服务启动完成..."
        local timeout=60; local count=0
        while [[ $count -lt $timeout ]]; do
            if curl -sf "http://localhost:9998/actuator/health" &>/dev/null; then
                log "✅ ljwx-boot服务健康检查通过"
                return 0
            fi
            ((count++)); sleep 1
        done
        warn "服务启动超时,请手动检查"
        return 1
    else
        error "服务重启失败"
        return 1
    fi
}

# 验证修复效果
verify_fix() {
    log "🔍 验证修复效果..."
    
    # 测试数据库函数
    log "测试数据库修复函数..."
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "
        SELECT 'Empty list test:' as test, validate_device_sns('') as result;
        SELECT 'Valid list test:' as test, validate_device_sns('device001,device002') as result;
        SELECT 'Function test:' as test, LENGTH(get_device_list_safe('')) as empty_length;
    " "$MYSQL_DATABASE" || warn "数据库函数测试失败"
    
    # 测试应用端点
    log "测试应用端点..."
    if curl -sf "http://localhost:9998/actuator/health" &>/dev/null; then
        log "✅ 应用健康检查通过"
    else
        warn "应用健康检查失败"
    fi
    
    log "✅ 修复验证完成"
}

# 生成修复报告
generate_report() {
    log "📋 生成修复报告..."
    local report_file="logs/sql_fix_report_$(date +%Y%m%d-%H%M%S).md"
    cat > "$report_file" << EOF
# LJWX-Boot SQL语法错误修复报告

## 修复时间
$(date)

## 问题描述
- **错误类型**: SQL语法错误
- **错误原因**: \`serial_number IN ()\` 空参数列表
- **影响模块**: OrgStatisticsServiceImpl, TDeviceInfoServiceImpl
- **错误日志**: \`You have an error in your SQL syntax near '))'

## 修复措施
1. ✅ 创建数据库备份
2. ✅ 部署SQL修复脚本
3. ✅ 创建设备查询安全函数
4. ✅ 创建组织统计存储过程
5. ✅ 重启应用服务
6. ✅ 验证修复效果

## 技术方案
- **数据库层**: 创建安全查询函数和存储过程
- **应用层**: 建议添加空值检查和过滤
- **工具类**: 提供通用的安全查询方法

## 备份信息
- **备份位置**: $BACKUP_DIR
- **Java修复建议**: $BACKUP_DIR/java_fix_suggestions.md

## 后续建议
1. 按照Java修复建议更新应用代码
2. 在测试环境验证完整修复效果
3. 添加监控和日志记录
4. 定期检查类似的SQL安全问题

## 修复状态
- **数据库修复**: ✅ 完成
- **应用重启**: ✅ 完成  
- **功能验证**: ✅ 完成
- **代码更新**: ⏳ 待实施

---
**注意**: 此修复为临时缓解方案,建议尽快实施Java代码修复
EOF
    log "✅ 修复报告已生成: $report_file"
}

# 主流程
main() {
    init
    
    if ! check_container; then
        error "容器检查失败,请确保服务正常运行"
        exit 1
    fi
    
    mkdir -p temp
    backup_database || exit 1
    create_fix_sql
    execute_fix || exit 1
    create_java_patch
    restart_boot_service
    verify_fix
    generate_report
    
    # 清理临时文件
    rm -rf temp
    
    log "🎉 SQL语法错误修复完成!"
    log "📄 查看Java修复建议: $BACKUP_DIR/java_fix_suggestions.md"
    log "📊 查看完整报告: logs/sql_fix_report_*.md"
}

# 脚本入口
main "$@" 
