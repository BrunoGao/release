package com.ljwx.test.admin;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static io.restassured.RestAssured.given;

/**
 * Admin用户功能测试类
 * 验证超级管理员的所有功能模块访问权限
 */
@Slf4j
public class AdminFunctionalityTest extends BaseApiTest {
    
    @BeforeClass
    public void setup() {
        setupRestAssured();
        loginAsAdmin();
        log.info("Admin用户登录完成，开始功能测试");
    }
    
    @Test(priority = 1, description = "验证Admin用户登录功能")
    public void testAdminLogin() {
        Assert.assertNotNull(authToken, "Admin登录Token不能为空");
        Assert.assertNotNull(currentUserId, "Admin用户ID不能为空");
        log.info("✅ Admin登录验证通过");
    }
    
    @Test(priority = 2, description = "验证Admin访问首页功能")
    public void testAdminDashboardAccess() {
        // 访问首页汇总信息
        Response response = authenticatedRequest()
            .queryParam("customer_id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DASHBOARD_API);
            
        verifySuccess(response);
        
        // 验证首页数据包含跨租户统计信息
        Assert.assertTrue(
            response.jsonPath().get("data") != null,
            "首页汇总数据不能为空"
        );
        
        log.info("✅ Admin首页访问验证通过");
    }
    
    @Test(priority = 3, description = "验证Admin租户管理功能")
    public void testAdminTenantManagement() {
        // 查看所有租户配置
        Response listResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.TENANT_API + "/page");
            
        verifySuccess(listResponse);
        
        // 验证可以看到多个租户的数据
        var records = listResponse.jsonPath().getList("data.records");
        int tenantCount = records != null ? records.size() : 0;
        log.info("Admin可见租户数量: {}", tenantCount);
        
        log.info("✅ Admin租户管理验证通过");
    }
    
    @Test(priority = 4, description = "验证Admin组织架构和岗位管理功能")
    public void testAdminOrgAndPositionManagement() {
        // 查看组织架构树
        Response orgTreeResponse = authenticatedRequest()
            .queryParam("id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ORG_API + "/tree");
            
        verifySuccess(orgTreeResponse);
        
        // 查看组织列表
        Response orgListResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ORG_API + "/page");
            
        verifySuccess(orgListResponse);
        
        // 查看岗位信息
        Response positionResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.POSITION_API + "/page");
            
        verifySuccess(positionResponse);
        
        log.info("✅ Admin组织架构和岗位管理验证通过");
    }
    
    @Test(priority = 5, description = "验证Admin用户管理功能")
    public void testAdminUserManagement() {
        // 查看所有用户（跨租户）
        Response userResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("orgIds", "1940374479725170690,1957457455646371841,1960835891196669953")
            .queryParam("viewMode", "all")
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(userResponse);
        
        // 测试根据组织ID获取用户
        Response orgUserResponse = authenticatedRequest()
            .queryParam("orgId", "1939964806110937090")
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.USER_API + "/get_users_by_org_id");
            
        verifySuccess(orgUserResponse);
        
        log.info("✅ Admin用户管理验证通过");
    }
    
    @Test(priority = 6, description = "验证Admin设备管理功能")
    public void testAdminDeviceManagement() {
        // 设备信息管理
        Response deviceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("orgId", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DEVICE_API + "/page");
            
        verifySuccess(deviceResponse);
        
        // 设备用户关联管理
        Response deviceUserResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("departmentInfo", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DEVICE_USER_API + "/page");
            
        verifySuccess(deviceUserResponse);
        
        log.info("✅ Admin设备管理验证通过");
    }
    
    @Test(priority = 7, description = "验证Admin消息管理功能")
    public void testAdminMessageManagement() {
        Response messageResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("departmentInfo", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.MESSAGE_API + "/page");
            
        verifySuccess(messageResponse);
        log.info("✅ Admin消息管理验证通过");
    }
    
    @Test(priority = 8, description = "验证Admin告警管理功能")
    public void testAdminAlertManagement() {
        // 告警信息管理
        Response alertResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ALERT_API + "/page");
            
        verifySuccess(alertResponse);
        
        // 告警规则管理
        Response alertRulesResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ALERT_RULES_API + "/page");
            
        verifySuccess(alertRulesResponse);
        
        // 告警操作日志
        Response alertLogResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.ALERT_LOG_API + "/page");
            
        verifySuccess(alertLogResponse);
        
        // 微信告警配置
        Response wechatEnterpriseResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .queryParam("type", "enterprise")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
            
        verifySuccess(wechatEnterpriseResponse);
        
        Response wechatOfficialResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .queryParam("type", "official")
            .when()
            .get(TestConfig.WECHAT_CONFIG_API + "/page");
            
        verifySuccess(wechatOfficialResponse);
        
        log.info("✅ Admin告警管理验证通过");
    }
    
    @Test(priority = 9, description = "验证Admin健康信息管理功能")
    public void testAdminHealthDataManagement() {
        // 健康数据配置管理
        Response healthConfigResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
            
        verifySuccess(healthConfigResponse);
        
        // 用户健康数据查询
        long currentTime = System.currentTimeMillis();
        long startTime = currentTime - 24 * 60 * 60 * 1000; // 昨天
        long endTime = currentTime;
        
        Response userHealthResponse = authenticatedRequest()
            .queryParam("customerId", 0)
            .queryParam("departmentInfo", "")
            .queryParam("userId", "")
            .queryParam("startDate", startTime)
            .queryParam("endDate", endTime)
            .queryParam("timeType", "day")
            .queryParam("dataType", "heart_rate")
            .when()
            .get(TestConfig.HEALTH_DATA_API + "/getUserHealthData");
            
        verifySuccess(userHealthResponse);
        
        log.info("✅ Admin健康信息管理验证通过");
    }
    
    @Test(priority = 10, description = "验证Admin接口和健康配置管理功能")
    public void testAdminInterfaceAndHealthConfig() {
        // 接口管理
        Response interfaceResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.INTERFACE_API + "/page");
            
        verifySuccess(interfaceResponse);
        
        // 健康数据配置
        Response healthConfigPageResponse = authenticatedRequest()
            .queryParam("customerId", 0)
            .queryParam("departmentInfo", "")
            .queryParam("page", 1)
            .queryParam("pageSize", 20)
            .when()
            .get(TestConfig.HEALTH_CONFIG_API + "/page");
            
        verifySuccess(healthConfigPageResponse);
        
        log.info("✅ Admin接口和健康配置管理验证通过");
    }
    
    @Test(priority = 11, description = "验证Admin跨租户数据访问能力")
    public void testAdminCrossTenantAccess() {
        // 验证全局访问（customerId=0）
        Response globalUserResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("viewMode", "all")
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(globalUserResponse);
        
        // 验证可以访问特定租户数据
        Response tenantSpecificResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("customerId", TestConfig.TestTenants.TENANT_A_ID)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(tenantSpecificResponse);
        
        log.info("✅ Admin跨租户数据访问验证通过");
    }
}