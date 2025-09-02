package com.ljwx.test.permission;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 权限隔离验证测试类
 * 验证Admin和租户管理员的权限差异以及数据隔离效果
 */
@Slf4j
public class PermissionIsolationTest extends BaseApiTest {
    
    @Test(priority = 1, description = "验证Admin全局数据访问权限")
    public void testAdminGlobalDataAccess() {
        setupRestAssured();
        loginAsAdmin();
        
        // 验证Admin可以访问所有租户的数据（customerId=0表示全局访问）
        Response userResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("viewMode", "all")
            .queryParam("customerId", 0) // Admin全局访问
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(userResponse);
        
        // 验证汇总信息接口
        Response dashboardResponse = authenticatedRequest()
            .queryParam("customer_id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DASHBOARD_API);
            
        verifySuccess(dashboardResponse);
        
        // 验证跨租户设备访问
        Response deviceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DEVICE_API + "/page");
            
        verifySuccess(deviceResponse);
        
        List<Map<String, Object>> users = userResponse.jsonPath().getList("data.records");
        if (users != null && users.size() > 0) {
            log.info("Admin可见用户数量: {}", users.size());
        }
        
        log.info("✅ Admin全局数据访问权限验证通过");
    }
    
    @Test(priority = 2, description = "验证租户管理员数据隔离")
    public void testTenantAdminDataIsolation() {
        setupRestAssured();
        loginAsTenantAdmin();
        
        // 验证租户管理员只能访问本租户数据
        Response userResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("viewMode", "all")
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(userResponse);
        
        // 验证租户首页数据隔离
        Response dashboardResponse = authenticatedRequest()
            .queryParam("customer_id", currentCustomerId)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.DASHBOARD_API);
            
        verifySuccess(dashboardResponse);
        
        // 验证设备数据隔离
        Response deviceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.DEVICE_API + "/page");
            
        verifySuccess(deviceResponse);
        
        List<Map<String, Object>> users = userResponse.jsonPath().getList("data.records");
        for (Map<String, Object> user : users) {
            Long userCustomerId = user.get("customerId") != null ? 
                Long.valueOf(user.get("customerId").toString()) : null;
                
            if (userCustomerId != null) {
                Assert.assertEquals(
                    userCustomerId, currentCustomerId,
                    "租户管理员只能看到本租户用户数据"
                );
            }
        }
        
        log.info("✅ 租户管理员数据隔离验证通过");
    }
    
    @Test(priority = 3, description = "验证跨租户数据访问拒绝")
    public void testCrossTenantAccessDenial() {
        setupRestAssured();
        loginAsTenantAdmin();
        
        // 尝试使用customerId=0访问全局数据（租户管理员不应该有此权限）
        Response globalAccessResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", 0) // 尝试全局访问
            .when()
            .get(TestConfig.USER_API + "/page");
            
        // 检查是否被正确拒绝或过滤
        if (globalAccessResponse.statusCode() == 200) {
            var records = globalAccessResponse.jsonPath().getList("data.records");
            if (records != null && !records.isEmpty()) {
                // 如果返回了数据，检查是否都属于当前租户
                for (Object record : records) {
                    Map<String, Object> recordMap = (Map<String, Object>) record;
                    Long recordCustomerId = recordMap.get("customerId") != null ?
                        Long.valueOf(recordMap.get("customerId").toString()) : null;
                    if (recordCustomerId != null && !recordCustomerId.equals(currentCustomerId)) {
                        Assert.fail("租户管理员不应该能访问其他租户数据");
                    }
                }
            }
        }
        
        // 尝试访问其他租户的设备数据
        Response otherTenantDeviceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", TestConfig.TestTenants.TENANT_B_ID)
            .when()
            .get(TestConfig.DEVICE_API + "/page");
            
        Assert.assertTrue(
            otherTenantDeviceResponse.statusCode() != 200 || 
            otherTenantDeviceResponse.jsonPath().getList("data.records").isEmpty(),
            "租户管理员不应该能访问其他租户设备数据"
        );
        
        log.info("✅ 跨租户数据访问拒绝验证通过");
    }
    
    @Test(priority = 4, description = "验证参数边界安全性")
    public void testParameterBoundarySecurity() {
        setupRestAssured();
        loginAsTenantAdmin();
        
        // 测试负数customerId攻击
        Response negativeIdResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", -1)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        // 应该被拒绝或过滤
        Assert.assertTrue(
            negativeIdResponse.statusCode() != 200 || 
            negativeIdResponse.jsonPath().getList("data.records").isEmpty(),
            "负数customerId应该被拒绝"
        );
        
        // 测试大数值customerId攻击
        Response largeIdResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", 999999999L)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        // 应该返回空数据
        Assert.assertTrue(
            largeIdResponse.statusCode() != 200 || 
            largeIdResponse.jsonPath().getList("data.records").isEmpty(),
            "不存在的customerId应该返回空数据"
        );
        
        log.info("✅ 参数边界安全性验证通过");
    }
    
    @Test(priority = 5, description = "验证组织架构权限隔离")
    public void testOrganizationPermissionIsolation() {
        setupRestAssured();
        
        // Admin组织访问（全局）
        loginAsAdmin();
        Response adminOrgResponse = authenticatedRequest()
            .queryParam("id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ORG_API + "/tree");
        verifySuccess(adminOrgResponse);
        
        // 租户管理员组织访问（租户范围）
        loginAsTenantAdmin();
        Response tenantOrgResponse = authenticatedRequest()
            .queryParam("id", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ORG_API + "/tree");
        verifySuccess(tenantOrgResponse);
        
        // 测试组织列表权限
        Response tenantOrgListResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ORG_API + "/page");
        verifySuccess(tenantOrgListResponse);
        
        // 验诇租户管理员看到的组织都属于当前租户
        var tenantOrgs = tenantOrgListResponse.jsonPath().getList("data.records");
        for (Object org : tenantOrgs) {
            Map<String, Object> orgMap = (Map<String, Object>) org;
            Long orgCustomerId = orgMap.get("customerId") != null ?
                Long.valueOf(orgMap.get("customerId").toString()) : null;
            if (orgCustomerId != null) {
                Assert.assertEquals(orgCustomerId, currentCustomerId,
                    "租户管理员只能看到本租户组织");
            }
        }
        
        log.info("✅ 组织架构权限隔离验证通过");
    }
    
    @Test(priority = 6, description = "验证健康数据访问权限")
    public void testHealthDataAccessPermission() {
        setupRestAssured();
        
        // Admin健康数据访问（全局）
        loginAsAdmin();
        
        // 健康数据配置
        Response adminHealthConfigResponse = authenticatedRequest()
            .queryParam("customerId", 0)
            .queryParam("departmentInfo", "")
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
        verifySuccess(adminHealthConfigResponse);
        
        // 用户健康数据查询
        Response adminHealthDataResponse = authenticatedRequest()
            .queryParam("customerId", 0)
            .queryParam("departmentInfo", "")
            .queryParam("userId", "")
            .queryParam("startDate", 1756569600000L)
            .queryParam("endDate", 1756655999999L)
            .queryParam("timeType", "day")
            .queryParam("dataType", "heart_rate")
            .when()
            .get(TestConfig.HEALTH_DATA_API + "/getUserHealthData");
        verifySuccess(adminHealthDataResponse);
        
        // 租户管理员健康数据访问（租户范围）
        loginAsTenantAdmin();
        
        Response tenantHealthConfigResponse = authenticatedRequest()
            .queryParam("customerId", currentCustomerId)
            .queryParam("departmentInfo", "")
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
        verifySuccess(tenantHealthConfigResponse);
        
        Response tenantHealthDataResponse = authenticatedRequest()
            .queryParam("customerId", currentCustomerId)
            .queryParam("departmentInfo", "")
            .queryParam("userId", "")
            .queryParam("startDate", 1756569600000L)
            .queryParam("endDate", 1756655999999L)
            .queryParam("timeType", "day")
            .queryParam("dataType", "heart_rate")
            .when()
            .get(TestConfig.HEALTH_DATA_API + "/getUserHealthData");
        verifySuccess(tenantHealthDataResponse);
        
        log.info("✅ 健康数据访问权限验证通过");
    }
    
    @Test(priority = 7, description = "验证微信配置权限管理")
    public void testWechatConfigPermissionManagement() {
        setupRestAssured();
        
        // Admin可以查看所有租户的微信配置
        loginAsAdmin();
        
        Response adminEnterpriseResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .queryParam("type", "enterprise")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
        verifySuccess(adminEnterpriseResponse);
        
        Response adminOfficialResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .queryParam("type", "official")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
        verifySuccess(adminOfficialResponse);
        
        // 租户管理员只能查看本租户的微信配置
        loginAsTenantAdmin();
        
        Response tenantEnterpriseResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .queryParam("type", "enterprise")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
        verifySuccess(tenantEnterpriseResponse);
        
        // 验证租户数据隔离
        var tenantConfigs = tenantEnterpriseResponse.jsonPath().getList("data.records");
        for (Object config : tenantConfigs) {
            Map<String, Object> configMap = (Map<String, Object>) config;
            Long configCustomerId = configMap.get("customerId") != null ?
                Long.valueOf(configMap.get("customerId").toString()) : null;
            if (configCustomerId != null) {
                Assert.assertEquals(configCustomerId, currentCustomerId,
                    "租户管理员只能查看本租户微信配置");
            }
        }
        
        log.info("✅ 微信配置权限管理验证通过");
    }
}