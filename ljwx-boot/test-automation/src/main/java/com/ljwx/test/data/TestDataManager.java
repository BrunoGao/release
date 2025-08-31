package com.ljwx.test.data;

import com.ljwx.test.config.TestConfig;
import lombok.extern.slf4j.Slf4j;

import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * 测试数据管理器
 * 负责准备和清理测试数据
 */
@Slf4j
public class TestDataManager {
    
    private Connection connection;
    
    public TestDataManager() throws SQLException {
        this.connection = DriverManager.getConnection(
            TestConfig.Database.MYSQL_URL,
            TestConfig.Database.MYSQL_USERNAME,
            TestConfig.Database.MYSQL_PASSWORD
        );
        this.connection.setAutoCommit(false);
    }
    
    /**
     * 准备完整测试数据
     */
    public void prepareTestData() throws SQLException {
        log.info("开始准备测试数据...");
        
        try {
            // 1. 创建测试租户
            prepareTenantData();
            
            // 2. 创建测试角色
            prepareRoleData();
            
            // 3. 创建测试用户
            prepareUserData();
            
            // 4. 创建测试组织架构
            prepareOrganizationData();
            
            // 5. 创建测试设备数据
            prepareDeviceData();
            
            // 6. 创建测试健康数据
            prepareHealthData();
            
            // 7. 创建测试消息数据
            prepareMessageData();
            
            // 8. 创建测试告警数据
            prepareAlertData();
            
            connection.commit();
            log.info("测试数据准备完成");
            
        } catch (SQLException e) {
            connection.rollback();
            log.error("测试数据准备失败，已回滚", e);
            throw e;
        }
    }
    
    /**
     * 清理测试数据
     */
    public void cleanupTestData() throws SQLException {
        log.info("开始清理测试数据...");
        
        try {
            // 按依赖关系逆序删除
            String[] cleanupTables = {
                "t_alert_action_log",
                "t_alert_info", 
                "t_device_message_detail_v2",
                "t_device_message_v2",
                "t_user_health_data",
                "t_device_info",
                "sys_user_org",
                "sys_user_role",
                "sys_role_permission",
                "sys_user",
                "sys_role",
                "sys_org_closure",
                "sys_org_units",
                "t_customer_config"
            };
            
            for (String table : cleanupTables) {
                executeUpdate(String.format(
                    "DELETE FROM %s WHERE create_user LIKE '%%test%%' OR " +
                    "id IN (SELECT id FROM (SELECT id FROM %s WHERE create_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)) tmp)", 
                    table, table
                ));
            }
            
            connection.commit();
            log.info("测试数据清理完成");
            
        } catch (SQLException e) {
            connection.rollback();
            log.error("测试数据清理失败", e);
            throw e;
        }
    }
    
    private void prepareTenantData() throws SQLException {
        log.info("准备租户测试数据...");
        
        // 租户A
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_customer_config (id, customer_name, contact_person, contact_phone, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(%d, '%s', '测试联系人A', '13800000001', 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_A_ID, TestConfig.TestTenants.TENANT_A_NAME
        ));
        
        // 租户B  
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_customer_config (id, customer_name, contact_person, contact_phone, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(%d, '%s', '测试联系人B', '13800000002', 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_B_ID, TestConfig.TestTenants.TENANT_B_NAME
        ));
    }
    
    private void prepareRoleData() throws SQLException {
        log.info("准备角色测试数据...");
        
        // 租户A管理员角色
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_role (id, role_name, role_code, is_admin, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(2001, '租户A管理员', 'TENANT_A_ADMIN', 1, %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_A_ID
        ));
        
        // 租户B管理员角色
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_role (id, role_name, role_code, is_admin, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(2002, '租户B管理员', 'TENANT_B_ADMIN', 1, %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_B_ID
        ));
    }
    
    private void prepareUserData() throws SQLException {
        log.info("准备用户测试数据...");
        
        // 租户A管理员用户
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_user (id, user_name, password, real_name, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(3001, '%s', '%s', '租户A管理员', %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestUsers.TENANT_ADMIN_USERNAME,
            TestConfig.TestUsers.TENANT_ADMIN_PASSWORD,
            TestConfig.TestTenants.TENANT_A_ID
        ));
        
        // 绑定租户A管理员角色
        executeUpdate(
            "INSERT IGNORE INTO sys_user_role (id, user_id, role_id, status) VALUES " +
            "(4001, 3001, 2001, '1')"
        );
        
        // 租户A普通用户
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_user (id, user_name, password, real_name, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(3002, '%s', '%s', '租户A普通用户', %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestUsers.REGULAR_USER_USERNAME,
            TestConfig.TestUsers.REGULAR_USER_PASSWORD,
            TestConfig.TestTenants.TENANT_A_ID
        ));
    }
    
    private void prepareOrganizationData() throws SQLException {
        log.info("准备组织架构测试数据...");
        
        // 租户A组织架构
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_org_units (id, parent_id, name, level, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(5001, 0, '租户A总部', 1, %d, 'test_system', NOW(), NOW(), 0), " +
            "(5002, 5001, '租户A技术部', 2, %d, 'test_system', NOW(), NOW(), 0), " +
            "(5003, 5001, '租户A运营部', 2, %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID
        ));
        
        // 租户B组织架构
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_org_units (id, parent_id, name, level, customer_id, " +
            "create_user, create_time, update_time, is_deleted) VALUES " +
            "(5101, 0, '租户B总部', 1, %d, 'test_system', NOW(), NOW(), 0), " +
            "(5102, 5101, '租户B业务部', 2, %d, 'test_system', NOW(), NOW(), 0)",
            TestConfig.TestTenants.TENANT_B_ID,
            TestConfig.TestTenants.TENANT_B_ID
        ));
        
        // 创建闭包关系
        prepareClosure();
    }
    
    private void prepareClosure() throws SQLException {
        // 租户A闭包关系
        executeUpdate(String.format(
            "INSERT IGNORE INTO sys_org_closure (ancestor, descendant, depth, customer_id) VALUES " +
            "(5001, 5001, 0, %d), " +
            "(5001, 5002, 1, %d), " +
            "(5001, 5003, 1, %d), " +
            "(5002, 5002, 0, %d), " +
            "(5003, 5003, 0, %d)",
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID,
            TestConfig.TestTenants.TENANT_A_ID
        ));
    }
    
    private void prepareDeviceData() throws SQLException {
        log.info("准备设备测试数据...");
        
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        
        // 租户A设备
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_device_info (id, device_sn, device_name, device_type, customer_id, " +
            "user_id, create_user, create_time, update_time, is_deleted) VALUES " +
            "(6001, 'TEST_DEVICE_A001', '测试设备A001', 'WATCH', %d, 3001, 'test_system', '%s', '%s', 0), " +
            "(6002, 'TEST_DEVICE_A002', '测试设备A002', 'WATCH', %d, 3002, 'test_system', '%s', '%s', 0)",
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp,
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp
        ));
    }
    
    private void prepareHealthData() throws SQLException {
        log.info("准备健康数据测试数据...");
        
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        
        // 租户A健康数据
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_user_health_data (id, user_id, customer_id, device_sn, " +
            "heart_rate, blood_pressure_systolic, blood_pressure_diastolic, spo2, " +
            "data_timestamp, create_user, create_time, update_time, is_deleted) VALUES " +
            "(7001, 3001, %d, 'TEST_DEVICE_A001', 75, 120, 80, 98, '%s', 'test_system', '%s', '%s', 0), " +
            "(7002, 3002, %d, 'TEST_DEVICE_A002', 80, 125, 85, 97, '%s', 'test_system', '%s', '%s', 0)",
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp,
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp
        ));
    }
    
    private void prepareMessageData() throws SQLException {
        log.info("准备消息测试数据...");
        
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        
        // 租户A消息数据
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_device_message_v2 (id, customer_id, department_id, user_id, " +
            "message, message_type, sender_type, receiver_type, message_status, " +
            "sent_time, create_user_id, create_time, update_time, is_deleted) VALUES " +
            "(8001, %d, 5001, 3001, '测试消息A001', 'notification', 'system', 'user', 'delivered', '%s', 1, '%s', '%s', 0), " +
            "(8002, %d, 5002, 3002, '测试消息A002', 'alert', 'system', 'user', 'pending', '%s', 1, '%s', '%s', 0)",
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp,
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp
        ));
    }
    
    private void prepareAlertData() throws SQLException {
        log.info("准备告警测试数据...");
        
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        
        // 租户A告警数据
        executeUpdate(String.format(
            "INSERT IGNORE INTO t_alert_info (id, customer_id, user_id, device_sn, " +
            "alert_type, severity_level, alert_message, alert_status, " +
            "alert_timestamp, create_user, create_time, update_time, is_deleted) VALUES " +
            "(9001, %d, 3001, 'TEST_DEVICE_A001', 'HEART_RATE_HIGH', 'high', '心率过高告警', 'pending', '%s', 'test_system', '%s', '%s', 0), " +
            "(9002, %d, 3002, 'TEST_DEVICE_A002', 'SPO2_LOW', 'medium', '血氧偏低告警', 'acknowledged', '%s', 'test_system', '%s', '%s', 0)",
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp,
            TestConfig.TestTenants.TENANT_A_ID, timestamp, timestamp, timestamp
        ));
    }
    
    /**
     * 验证测试数据完整性
     */
    public boolean verifyTestData() throws SQLException {
        log.info("验证测试数据完整性...");
        
        String[] checkQueries = {
            "SELECT COUNT(*) FROM t_customer_config WHERE id IN (" + 
                TestConfig.TestTenants.TENANT_A_ID + ", " + TestConfig.TestTenants.TENANT_B_ID + ")",
            "SELECT COUNT(*) FROM sys_user WHERE user_name = '" + TestConfig.TestUsers.TENANT_ADMIN_USERNAME + "'",
            "SELECT COUNT(*) FROM sys_role WHERE customer_id = " + TestConfig.TestTenants.TENANT_A_ID,
            "SELECT COUNT(*) FROM sys_org_units WHERE customer_id = " + TestConfig.TestTenants.TENANT_A_ID
        };
        
        for (String query : checkQueries) {
            try (PreparedStatement stmt = connection.prepareStatement(query);
                 ResultSet rs = stmt.executeQuery()) {
                
                if (rs.next() && rs.getInt(1) == 0) {
                    log.warn("测试数据不完整，查询: {}", query);
                    return false;
                }
            }
        }
        
        log.info("✅ 测试数据完整性验证通过");
        return true;
    }
    
    /**
     * 获取测试数据统计
     */
    public TestDataStatistics getTestDataStatistics() throws SQLException {
        TestDataStatistics stats = new TestDataStatistics();
        
        stats.tenantCount = queryCount("SELECT COUNT(*) FROM t_customer_config WHERE id >= 1000");
        stats.userCount = queryCount("SELECT COUNT(*) FROM sys_user WHERE customer_id >= 1000");
        stats.deviceCount = queryCount("SELECT COUNT(*) FROM t_device_info WHERE customer_id >= 1000");
        stats.messageCount = queryCount("SELECT COUNT(*) FROM t_device_message_v2 WHERE customer_id >= 1000");
        stats.alertCount = queryCount("SELECT COUNT(*) FROM t_alert_info WHERE customer_id >= 1000");
        stats.healthDataCount = queryCount("SELECT COUNT(*) FROM t_user_health_data WHERE customer_id >= 1000");
        
        log.info("测试数据统计: {}", stats);
        return stats;
    }
    
    private int queryCount(String sql) throws SQLException {
        try (PreparedStatement stmt = connection.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {
            return rs.next() ? rs.getInt(1) : 0;
        }
    }
    
    private void executeUpdate(String sql) throws SQLException {
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            int result = stmt.executeUpdate();
            log.debug("执行SQL: {}, 影响行数: {}", sql, result);
        }
    }
    
    public void close() throws SQLException {
        if (connection != null && !connection.isClosed()) {
            connection.close();
        }
    }
    
    /**
     * 测试数据统计内部类
     */
    public static class TestDataStatistics {
        public int tenantCount;
        public int userCount;
        public int deviceCount;
        public int messageCount;
        public int alertCount;
        public int healthDataCount;
        
        @Override
        public String toString() {
            return String.format(
                "租户:%d, 用户:%d, 设备:%d, 消息:%d, 告警:%d, 健康数据:%d",
                tenantCount, userCount, deviceCount, messageCount, alertCount, healthDataCount
            );
        }
    }
}