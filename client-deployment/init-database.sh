#!/bin/bash

# 数据库初始化脚本 - 清空指定表数据并保留特定记录
# 使用方法: ./init-database.sh [数据库配置]

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# 默认配置
MYSQL_HOST=${MYSQL_HOST:-"127.0.0.1"}
MYSQL_PORT=${MYSQL_PORT:-"3306"}
MYSQL_USER=${MYSQL_USER:-"root"}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-"123456"}
MYSQL_DATABASE=${MYSQL_DATABASE:-"test"}

# 加载配置文件（如果提供）
CONFIG_FILE=${1:-"custom-config.env"}
if [ -f "$CONFIG_FILE" ]; then
    . "$CONFIG_FILE"
    log "已加载配置文件: $CONFIG_FILE"
fi

echo "==================== 数据库初始化脚本 ===================="
echo "目标数据库: $MYSQL_HOST:$MYSQL_PORT/$MYSQL_DATABASE"
echo "用户: $MYSQL_USER"
echo ""

# 确认操作
warn "⚠️  此操作将清空以下表的数据:"
echo "📋 完全清空的表:"
echo "   - t_device_info (设备信息)"
echo "   - t_device_info_history (设备历史)"
echo "   - t_device_user (设备用户关联)"
echo "   - t_alert_info (告警信息)"
echo "   - t_alert_action_log (告警操作日志)"
echo "   - t_device_message (设备消息)"
echo "   - t_device_message_detail (设备消息详情)"
echo "   - t_user_health_data (用户健康数据)"
echo "   - sys_org_units (组织单位)"
echo "   - sys_user_org (用户组织关联)"
echo "   - sys_position (职位信息)"
echo "   - sys_user_postion (用户职位关联)"
echo ""
echo "📋 保留特定记录的表:"
echo "   - t_customer_config (保留 id=0 的记录)"
echo "   - t_interface (保留 customer_id=1 的记录)"
echo "   - t_health_data_config (保留 customer_id=1 的记录)"
echo ""

read -p "确认执行数据库初始化操作? 此操作不可逆! (yes/N): " confirm
if [ "$confirm" != "yes" ]; then
    log "操作已取消"
    exit 0
fi

# 测试数据库连接
log "测试数据库连接..."
if ! mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
    error "无法连接到数据库，请检查配置"
    exit 1
fi
log "✅ 数据库连接成功"

# 检查数据库是否存在
log "检查目标数据库..."
if ! mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "USE \`$MYSQL_DATABASE\`;" > /dev/null 2>&1; then
    error "数据库 '$MYSQL_DATABASE' 不存在"
    exit 1
fi
log "✅ 目标数据库存在"

# 创建备份
BACKUP_FILE="backup/database_backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backup
log "创建数据库备份..."
mysqldump -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
    --single-transaction --routines --triggers "$MYSQL_DATABASE" > "$BACKUP_FILE"
log "✅ 备份完成: $BACKUP_FILE"

# 执行数据库初始化
log "开始执行数据库初始化..."

# 创建SQL脚本
# 显示操作前的数据统计
log "查询操作前的数据统计..."
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" << 'EOF'
SELECT '=== 操作前数据统计 ===' as info;
SELECT 't_device_info' as table_name, COUNT(*) as current_count FROM t_device_info
UNION ALL
SELECT 't_alert_info', COUNT(*) FROM t_alert_info
UNION ALL
SELECT 't_user_health_data', COUNT(*) FROM t_user_health_data
UNION ALL
SELECT 'sys_org_units', COUNT(*) FROM sys_org_units
UNION ALL
SELECT 't_customer_config', COUNT(*) FROM t_customer_config
UNION ALL
SELECT 't_interface', COUNT(*) FROM t_interface
UNION ALL
SELECT 't_health_data_config', COUNT(*) FROM t_health_data_config;
EOF

echo ""
read -p "查看数据统计后，确认继续执行清理操作? (yes/N): " final_confirm
if [ "$final_confirm" != "yes" ]; then
    log "操作已取消"
    exit 0
fi

cat > temp_init.sql << 'EOF'
-- 数据库初始化脚本
-- 清空指定表数据并保留特定记录

-- 设置SQL模式
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

-- 开始事务
START TRANSACTION;

-- 显示操作前统计
SELECT '=== 开始数据清理操作 ===' as info;

-- 1. 完全清空的表
DELETE FROM t_device_info;
SELECT CONCAT('✅ t_device_info 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_device_info_history;
SELECT CONCAT('✅ t_device_info_history 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_device_user;
SELECT CONCAT('✅ t_device_user 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_alert_info;
SELECT CONCAT('✅ t_alert_info 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_alert_action_log;
SELECT CONCAT('✅ t_alert_action_log 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_device_message;
SELECT CONCAT('✅ t_device_message 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_device_message_detail;
SELECT CONCAT('✅ t_device_message_detail 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM t_user_health_data;
SELECT CONCAT('✅ t_user_health_data 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM sys_org_units;
SELECT CONCAT('✅ sys_org_units 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM sys_user_org;
SELECT CONCAT('✅ sys_user_org 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM sys_position;
SELECT CONCAT('✅ sys_position 清空完成, 删除记录数: ', ROW_COUNT()) as result;

DELETE FROM sys_user_postion;
SELECT CONCAT('✅ sys_user_postion 清空完成, 删除记录数: ', ROW_COUNT()) as result;

-- 2. 保留特定记录的表

-- t_customer_config: 保留 id=0 的记录
DELETE FROM t_customer_config WHERE id != 0;
SELECT CONCAT('✅ t_customer_config 部分清理完成, 删除记录数: ', ROW_COUNT(), ', 保留 id=0 记录') as result;

-- t_interface: 保留 customer_id=1 的记录
DELETE FROM t_interface WHERE customer_id != 1;
SELECT CONCAT('✅ t_interface 部分清理完成, 删除记录数: ', ROW_COUNT(), ', 保留 customer_id=1 记录') as result;

-- t_health_data_config: 保留 customer_id=1 的记录
DELETE FROM t_health_data_config WHERE customer_id != 1;
SELECT CONCAT('✅ t_health_data_config 部分清理完成, 删除记录数: ', ROW_COUNT(), ', 保留 customer_id=1 记录') as result;

-- 重置自增ID到合理值
ALTER TABLE t_device_info AUTO_INCREMENT = 1;
ALTER TABLE t_alert_info AUTO_INCREMENT = 1;
ALTER TABLE sys_org_units AUTO_INCREMENT = 1;
ALTER TABLE t_device_message AUTO_INCREMENT = 1;

-- 恢复外键检查
SET foreign_key_checks = 1;

-- 提交事务
COMMIT;

-- 显示最终结果统计
SELECT '=== 最终数据统计 ===' as result;
SELECT 't_device_info' as table_name, COUNT(*) as remaining_count FROM t_device_info
UNION ALL
SELECT 't_device_info_history', COUNT(*) FROM t_device_info_history
UNION ALL
SELECT 't_device_user', COUNT(*) FROM t_device_user
UNION ALL
SELECT 't_alert_info', COUNT(*) FROM t_alert_info
UNION ALL
SELECT 't_alert_action_log', COUNT(*) FROM t_alert_action_log
UNION ALL
SELECT 't_device_message', COUNT(*) FROM t_device_message
UNION ALL
SELECT 't_device_message_detail', COUNT(*) FROM t_device_message_detail
UNION ALL
SELECT 't_user_health_data', COUNT(*) FROM t_user_health_data
UNION ALL
SELECT 'sys_org_units', COUNT(*) FROM sys_org_units
UNION ALL
SELECT 'sys_user_org', COUNT(*) FROM sys_user_org
UNION ALL
SELECT 'sys_position', COUNT(*) FROM sys_position
UNION ALL
SELECT 'sys_user_postion', COUNT(*) FROM sys_user_postion;

SELECT '=== 保留的配置记录 ===' as result;
SELECT 't_customer_config' as table_name, COUNT(*) as remaining_count FROM t_customer_config
UNION ALL
SELECT 't_interface', COUNT(*) FROM t_interface WHERE customer_id = 1
UNION ALL
SELECT 't_health_data_config', COUNT(*) FROM t_health_data_config WHERE customer_id = 1;

EOF

# 执行SQL脚本
log "执行数据库初始化SQL..."
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < temp_init.sql

if [ $? -eq 0 ]; then
    log "✅ 数据库初始化完成"
else
    error "❌ 数据库初始化失败"
    warn "可以使用备份文件恢复: mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < $BACKUP_FILE"
    exit 1
fi

# 清理临时文件
rm -f temp_init.sql

echo ""
echo "==================== 初始化完成 ===================="
log "🎉 数据库初始化成功完成!"
echo ""
echo "📊 操作总结:"
echo "   - 备份文件: $BACKUP_FILE"
echo "   - 清空表数量: 12个表"
echo "   - 保留配置表: 3个表 (特定记录)"
echo ""
echo "📋 下一步操作:"
echo "   - 重启应用服务: docker-compose restart ljwx-boot"
echo "   - 验证系统功能: 访问管理后台和监控大屏"
echo "   - 导入新的业务数据"
echo ""
echo "🔄 如需恢复数据:"
echo "   mysql -h$MYSQL_HOST -P$MYSQL_PORT -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < $BACKUP_FILE"