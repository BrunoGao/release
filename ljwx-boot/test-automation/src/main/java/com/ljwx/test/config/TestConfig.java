package com.ljwx.test.config;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;

/**
 * 测试配置类
 */
@Data
@Slf4j
public class TestConfig {
    
    // API基础配置
    public static final String BASE_URL = "http://192.168.1.83:3333";
    public static final String API_PREFIX = "/proxy-default";
    
    // 登录接口
    public static final String LOGIN_URL = API_PREFIX + "/auth/user_name";
    
    // 核心模块API路径（基于实际接口调用）
    public static final String DASHBOARD_API = API_PREFIX + "/health/gather_total_info";
    public static final String TENANT_API = API_PREFIX + "/t_customer_config";
    public static final String ORG_API = API_PREFIX + "/sys_org_units";
    public static final String INTERFACE_API = API_PREFIX + "/t_interface";
    public static final String HEALTH_CONFIG_API = API_PREFIX + "/t_health_data_config";
    public static final String POSITION_API = API_PREFIX + "/sys_position";
    public static final String USER_API = API_PREFIX + "/sys_user";
    public static final String DEVICE_API = API_PREFIX + "/t_device_info";
    public static final String DEVICE_USER_API = API_PREFIX + "/t_device_user";
    public static final String ALERT_API = API_PREFIX + "/t_alert_info";
    public static final String ALERT_RULES_API = API_PREFIX + "/t_alert_rules";
    public static final String ALERT_LOG_API = API_PREFIX + "/t_alert_action_log";
    public static final String WECHAT_CONFIG_API = API_PREFIX + "/t_wechat_alarm_config";
    public static final String MESSAGE_API = API_PREFIX + "/t_device_message";
    public static final String HEALTH_DATA_API = API_PREFIX + "/t_user_health_data";
    
    // 兼容性API别名（用于旧测试类）
    public static final String ROLE_API = POSITION_API;
    public static final String HEALTH_API = HEALTH_DATA_API;
    
    // 测试用户配置
    public static class TestUsers {
        // 超级管理员
        public static final String ADMIN_USERNAME = "admin";
        public static final String ADMIN_PASSWORD = "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776";
        
        // 租户管理员 - 需要在测试数据中创建
        public static final String TENANT_ADMIN_USERNAME = "tenant_admin_test";
        public static final String TENANT_ADMIN_PASSWORD = "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776";
        public static final Long TENANT_ADMIN_CUSTOMER_ID = 1001L;
        
        // 普通用户
        public static final String REGULAR_USER_USERNAME = "regular_user_test";
        public static final String REGULAR_USER_PASSWORD = "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776";
    }
    
    // 测试租户配置
    public static class TestTenants {
        public static final Long TENANT_A_ID = 1001L;
        public static final String TENANT_A_NAME = "测试租户A";
        
        public static final Long TENANT_B_ID = 1002L;
        public static final String TENANT_B_NAME = "测试租户B";
    }
    
    // 数据库配置
    public static class Database {
        public static final String MYSQL_URL = "jdbc:mysql://127.0.0.1:3306/test?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=UTC";
        public static final String MYSQL_USERNAME = "root";
        public static final String MYSQL_PASSWORD = "123456";
        public static final String MYSQL_DRIVER = "com.mysql.cj.jdbc.Driver";
    }
    
    // 测试超时配置
    public static final int DEFAULT_TIMEOUT_MS = 30000;
    public static final int LOGIN_TIMEOUT_MS = 10000;
    public static final int API_TIMEOUT_MS = 15000;
    
    // 测试数据配置
    public static final int TEST_PAGE_SIZE = 10;
    public static final int MAX_RETRY_COUNT = 3;
    
    static {
        log.info("测试配置加载完成");
        log.info("API Base URL: {}", BASE_URL);
        log.info("数据库连接: {}", Database.MYSQL_URL);
    }
}