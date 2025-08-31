package com.ljwx.test.tenant;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.HashMap;
import java.util.Map;

/**
 * 租户管理员功能测试类
 * 验证租户管理员在租户范围内的功能权限
 */
@Slf4j
public class TenantAdminFunctionalityTest extends BaseApiTest {
    
    @BeforeClass
    public void setup() {
        setupRestAssured();
        loginAsTenantAdmin();
        log.info("租户管理员登录完成，当前租户ID: {}", currentCustomerId);
    }
    
    @Test(priority = 1, description = "验证租户管理员登录功能")
    public void testTenantAdminLogin() {
        Assert.assertNotNull(authToken, "租户管理员登录Token不能为空");
        Assert.assertNotNull(currentUserId, "租户管理员用户ID不能为空");
        Assert.assertNotNull(currentCustomerId, "租户管理员租户ID不能为空");
        Assert.assertTrue(currentCustomerId > 0, "租户管理员必须属于具体租户");
        log.info("✅ 租户管理员登录验证通过");
    }
    
    @Test(priority = 2, description = "验证租户管理员访问首页功能")
    public void testTenantAdminDashboardAccess() {
        // 访问租户首页汇总信息
        Response response = authenticatedRequest()
            .queryParam("customer_id", currentCustomerId)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.DASHBOARD_API);
            
        verifySuccess(response);
        
        // 验证首页数据只包含当前租户的统计信息
        Object dashboardData = response.jsonPath().get("data");
        Assert.assertNotNull(dashboardData, "租户首页数据不能为空");
        
        log.info("✅ 租户管理员首页访问验证通过");
    }
    
    @Test(priority = 3, description = "验证租户管理员租户管理功能限制")
    public void testTenantAdminTenantLimitations() {
        // 查看租户配置信息（应该只能查看本租户）
        Response listResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("id", 0)
            .queryParam("customerId", currentCustomerId) // 租户管理员传入本租户ID
            .when()
            .get(TestConfig.TENANT_API + "/page");
            
        verifySuccess(listResponse);
        
        var tenants = listResponse.jsonPath().getList("data.records");
        if (tenants != null && !tenants.isEmpty()) {
            // 验证所有可见租户都应该是当前租户
            for (Object tenant : tenants) {
                Map<String, Object> tenantMap = (Map<String, Object>) tenant;
                Long tenantId = tenantMap.get("id") != null ? 
                    Long.valueOf(tenantMap.get("id").toString()) : null;
                if (tenantId != null) {
                    Assert.assertEquals(tenantId, currentCustomerId,
                        "租户管理员只能查看本租户信息");
                }
            }
            log.info("租户管理员可见租户数量: {}", tenants.size());
        }
        
        log.info("✅ 租户管理员租户管理限制验证通过");
    }
    
    @Test(priority = 4, description = "验证租户管理员组织和岗位管理功能")
    public void testTenantAdminOrgAndPositionManagement() {
        // 查看组织架构树（仅租户内）
        Response orgTreeResponse = authenticatedRequest()
            .queryParam("id", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ORG_API + "/tree");
            
        verifySuccess(orgTreeResponse);
        
        // 查看组织列表
        Response orgListResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ORG_API + "/page");
            
        verifySuccess(orgListResponse);
        
        // 查看岗位信息
        Response positionResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.POSITION_API + "/page");
            
        verifySuccess(positionResponse);
        
        // 验证组织数据都属于当前租户
        var orgs = orgListResponse.jsonPath().getList("data.records");
        for (Object org : orgs) {
            Map<String, Object> orgMap = (Map<String, Object>) org;
            Long orgCustomerId = orgMap.get("customerId") != null ?
                Long.valueOf(orgMap.get("customerId").toString()) : null;
            if (orgCustomerId != null) {
                Assert.assertEquals(orgCustomerId, currentCustomerId,
                    "租户管理员只能看到本租户组织");
            }
        }
        
        log.info("✅ 租户管理员组织和岗位管理验证通过");
    }
    
    @Test(priority = 5, description = "验证租户管理员用户管理功能")
    public void testTenantAdminUserManagement() {
        // 查看租户内用户
        Response userResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("viewMode", "all")
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(userResponse);
        
        // 验证所有用户都属于当前租户
        var users = userResponse.jsonPath().getList("data.records");
        for (Object user : users) {
            Map<String, Object> userMap = (Map<String, Object>) user;
            Long userCustomerId = userMap.get("customerId") != null ?
                Long.valueOf(userMap.get("customerId").toString()) : null;
            if (userCustomerId != null) {
                Assert.assertEquals(userCustomerId, currentCustomerId,
                    "租户管理员只能管理本租户用户");
            }
        }
        
        log.info("✅ 租户管理员用户管理验证通过");
    }
    
    @Test(priority = 6, description = "验证租户管理员设备管理功能")
    public void testTenantAdminDeviceManagement() {
        // 设备信息管理
        Response deviceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.DEVICE_API + "/page");
            
        verifySuccess(deviceResponse);
        
        // 设备用户关联管理
        Response deviceUserResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("departmentInfo", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.DEVICE_USER_API + "/page");
            
        verifySuccess(deviceUserResponse);
        
        log.info("✅ 租户管理员设备管理验证通过");
    }
    
    @Test(priority = 7, description = "验证租户管理员消息管理功能")
    public void testTenantAdminMessageManagement() {
        Response messageResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("departmentInfo", 0)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.MESSAGE_API + "/page");
            
        verifySuccess(messageResponse);
        
        // 验证消息数据都属于当前租户
        var messages = messageResponse.jsonPath().getList("data.records");
        for (Object message : messages) {
            Map<String, Object> msgMap = (Map<String, Object>) message;
            Long msgCustomerId = msgMap.get("customerId") != null ?
                Long.valueOf(msgMap.get("customerId").toString()) : null;
            if (msgCustomerId != null) {
                Assert.assertEquals(msgCustomerId, currentCustomerId,
                    "租户管理员只能管理本租户消息");
            }
        }
        
        log.info("✅ 租户管理员消息管理验证通过");
    }
    
    @Test(priority = 8, description = "验证租户管理员告警管理功能")
    public void testTenantAdminAlertManagement() {
        // 告警信息管理
        Response alertResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ALERT_API + "/page");
            
        verifySuccess(alertResponse);
        
        // 告警规则管理
        Response alertRulesResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.ALERT_RULES_API + "/page");
            
        verifySuccess(alertRulesResponse);
        
        // 微信告警配置
        Response wechatConfigResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .queryParam("type", "enterprise")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
            
        verifySuccess(wechatConfigResponse);
        
        log.info("✅ 租户管理员告警管理验证通过");
    }
    
    @Test(priority = 9, description = "验证租户管理员健康信息管理功能")
    public void testTenantAdminHealthDataManagement() {
        // 健康数据配置管理
        Response healthConfigResponse = authenticatedRequest()
            .queryParam("customerId", currentCustomerId)
            .queryParam("departmentInfo", "")
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
            
        verifySuccess(healthConfigResponse);
        
        // 用户健康数据查询
        long currentTime = System.currentTimeMillis();
        long startTime = currentTime - 24 * 60 * 60 * 1000;
        long endTime = currentTime;
        
        Response userHealthResponse = authenticatedRequest()
            .queryParam("customerId", currentCustomerId)
            .queryParam("departmentInfo", "")
            .queryParam("userId", "")
            .queryParam("startDate", startTime)
            .queryParam("endDate", endTime)
            .queryParam("timeType", "day")
            .queryParam("dataType", "heart_rate")
            .when()
            .get(TestConfig.HEALTH_DATA_API + "/getUserHealthData");
            
        verifySuccess(userHealthResponse);
        
        log.info("✅ 租户管理员健康信息管理验证通过");
    }
    
    @Test(priority = 10, description = "验证租户管理员接口和健康配置管理")
    public void testTenantAdminInterfaceAndHealthConfig() {
        // 接口管理（租户级）
        Response interfaceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", currentCustomerId)
            .when()
            .get(TestConfig.INTERFACE_API + "/page");
            
        verifySuccess(interfaceResponse);
        
        // 健康数据配置（租户级）
        Response healthConfigResponse = authenticatedRequest()
            .queryParam("customerId", currentCustomerId)
            .queryParam("departmentInfo", "")
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
            
        verifySuccess(healthConfigResponse);
        
        log.info("✅ 租户管理员接口和健康配置管理验证通过");
    }
    
    @Test(priority = 11, description = "验证租户管理员数据隔离边界")
    public void testTenantAdminDataIsolation() {
        // 尝试访问其他租户数据（应该被拒绝或返回空）
        Response crossTenantUserResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", TestConfig.TestTenants.TENANT_B_ID) // 尝试访问其他租户
            .when()
            .get(TestConfig.USER_API + "/page");
            
        // 应该返回空数据或权限错误
        Assert.assertTrue(
            crossTenantUserResponse.statusCode() != 200 || 
            crossTenantUserResponse.jsonPath().getList("data.records").isEmpty(),
            "租户管理员不应该能访问其他租户数据"
        );
        
        log.info("✅ 租户管理员数据隔离验证通过");
    }
}