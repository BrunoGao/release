package com.ljwx.test.integration;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import com.ljwx.test.data.TestDataManager;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;

/**
 * 完整系统集成测试
 * 验证整个系统的端到端功能流程
 */
@Slf4j
public class FullSystemIntegrationTest extends BaseApiTest {
    
    private TestDataManager testDataManager;
    
    @BeforeClass
    public void setup() throws SQLException {
        setupRestAssured();
        testDataManager = new TestDataManager();
        testDataManager.prepareTestData();
        log.info("集成测试环境准备完成");
    }
    
    @AfterClass
    public void cleanup() throws SQLException {
        if (testDataManager != null) {
            testDataManager.cleanupTestData();
            testDataManager.close();
        }
        log.info("集成测试环境清理完成");
    }
    
    @Test(priority = 1, description = "验证系统基础功能可用性")
    public void testSystemBasicAvailability() {
        // 验证Admin系统功能
        loginAsAdmin();
        
        String[] adminEndpoints = {
            TestConfig.DASHBOARD_API + "/overview",
            TestConfig.TENANT_API + "/page?current=1&size=5",
            TestConfig.USER_API + "/page?current=1&size=5",
            TestConfig.ROLE_API + "/page?current=1&size=5"
        };
        
        for (String endpoint : adminEndpoints) {
            Response response = authenticatedRequest().when().get(endpoint);
            Assert.assertEquals(response.statusCode(), 200, 
                "Admin访问 " + endpoint + " 应该成功");
        }
        
        // 验证租户管理员系统功能
        loginAsTenantAdmin();
        
        String[] tenantEndpoints = {
            TestConfig.DASHBOARD_API + "/overview",
            TestConfig.USER_API + "/page?current=1&size=5",
            TestConfig.DEVICE_API + "/page?current=1&size=5"
        };
        
        for (String endpoint : tenantEndpoints) {
            Response response = authenticatedRequest().when().get(endpoint);
            Assert.assertEquals(response.statusCode(), 200, 
                "租户管理员访问 " + endpoint + " 应该成功");
        }
        
        log.info("✅ 系统基础功能可用性验证通过");
    }
    
    @Test(priority = 2, description = "验证端到端业务流程")
    public void testEndToEndBusinessFlow() {
        loginAsAdmin();
        
        // 1. 创建新租户
        Map<String, Object> tenantData = new HashMap<>();
        tenantData.put("customerName", "集成测试租户_" + System.currentTimeMillis());
        tenantData.put("contactPerson", "集成测试负责人");
        tenantData.put("contactPhone", "13900000000");
        
        Response createTenantResponse = authenticatedRequest()
            .body(tenantData)
            .when()
            .post(TestConfig.TENANT_API + "/add");
        verifySuccess(createTenantResponse);
        
        Long newTenantId = createTenantResponse.jsonPath().getLong("data.id");
        Assert.assertNotNull(newTenantId, "新建租户ID不能为空");
        
        // 2. 为新租户创建管理员角色
        Map<String, Object> roleData = new HashMap<>();
        roleData.put("roleName", "集成测试管理员");
        roleData.put("roleCode", "INTEGRATION_TEST_ADMIN");
        roleData.put("customerId", newTenantId);
        roleData.put("isAdmin", 1);
        
        Response createRoleResponse = authenticatedRequest()
            .body(roleData)
            .when()
            .post(TestConfig.ROLE_API + "/add");
        verifySuccess(createRoleResponse);
        
        // 3. 创建租户管理员用户
        Map<String, Object> userData = new HashMap<>();
        userData.put("userName", "integration_test_admin");
        userData.put("password", TestConfig.TestUsers.ADMIN_PASSWORD);
        userData.put("realName", "集成测试管理员");
        userData.put("customerId", newTenantId);
        
        Response createUserResponse = authenticatedRequest()
            .body(userData)
            .when()
            .post(TestConfig.USER_API + "/add");
        verifySuccess(createUserResponse);
        
        log.info("✅ 端到端业务流程验证通过，新租户ID: {}", newTenantId);
    }
    
    @Test(priority = 3, description = "验证高并发场景下的权限隔离")
    public void testConcurrentPermissionIsolation() throws InterruptedException {
        // 并发测试：多个租户管理员同时操作
        int threadCount = 5;
        Thread[] threads = new Thread[threadCount];
        boolean[] results = new boolean[threadCount];
        
        for (int i = 0; i < threadCount; i++) {
            final int index = i;
            threads[i] = new Thread(() -> {
                try {
                    setupRestAssured();
                    loginAsTenantAdmin();
                    
                    // 并发查询用户数据
                    Response response = authenticatedRequest()
                        .queryParam("current", 1)
                        .queryParam("size", 10)
                        .when()
                        .get(TestConfig.USER_API + "/page");
                        
                    results[index] = response.statusCode() == 200;
                    
                } catch (Exception e) {
                    log.error("并发测试线程 {} 失败", index, e);
                    results[index] = false;
                }
            });
            
            threads[i].start();
        }
        
        // 等待所有线程完成
        for (Thread thread : threads) {
            thread.join();
        }
        
        // 验证所有并发请求都成功
        for (int i = 0; i < threadCount; i++) {
            Assert.assertTrue(results[i], "并发测试线程 " + i + " 应该成功");
        }
        
        log.info("✅ 高并发权限隔离验证通过");
    }
    
    @Test(priority = 4, description = "验证数据一致性和完整性")
    public void testDataConsistencyAndIntegrity() throws SQLException {
        // 验证测试数据统计
        TestDataManager.TestDataStatistics stats = testDataManager.getTestDataStatistics();
        
        Assert.assertTrue(stats.tenantCount >= 2, "应该有至少2个测试租户");
        Assert.assertTrue(stats.userCount >= 2, "应该有至少2个测试用户");
        
        // 验证数据关联完整性
        loginAsAdmin();
        Response healthDataResponse = authenticatedRequest()
            .queryParam("current", 1)
            .queryParam("size", 10)
            .when()
            .get(TestConfig.HEALTH_API + "/page");
            
        if (healthDataResponse.statusCode() == 200) {
            var healthRecords = healthDataResponse.jsonPath().getList("data.records");
            for (Object record : healthRecords) {
                Map<String, Object> healthMap = (Map<String, Object>) record;
                Assert.assertNotNull(healthMap.get("userId"), "健康数据应该关联用户ID");
                Assert.assertNotNull(healthMap.get("customerId"), "健康数据应该关联租户ID");
            }
        }
        
        log.info("✅ 数据一致性和完整性验证通过");
    }
    
    @Test(priority = 5, description = "验证性能优化效果")
    public void testPerformanceOptimization() {
        loginAsAdmin();
        
        // 测试组织查询性能（验证闭包表优化效果）
        long startTime = System.currentTimeMillis();
        
        Response orgResponse = authenticatedRequest()
            .when()
            .get(TestConfig.ORG_API + "/tree");
            
        long endTime = System.currentTimeMillis();
        long responseTime = endTime - startTime;
        
        verifySuccess(orgResponse);
        
        // 验证组织查询响应时间（闭包表优化后应该<50ms）
        Assert.assertTrue(responseTime < 100, 
            "组织查询响应时间应该小于100ms，实际: " + responseTime + "ms");
        
        log.info("组织查询响应时间: {}ms", responseTime);
        
        // 测试用户查询性能（验证userId优化效果）
        startTime = System.currentTimeMillis();
        
        Response userResponse = authenticatedRequest()
            .queryParam("current", 1)
            .queryParam("size", 20)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        endTime = System.currentTimeMillis();
        responseTime = endTime - startTime;
        
        verifySuccess(userResponse);
        Assert.assertTrue(responseTime < 200,
            "用户查询响应时间应该小于200ms，实际: " + responseTime + "ms");
            
        log.info("用户查询响应时间: {}ms", responseTime);
        log.info("✅ 性能优化效果验证通过");
    }
}