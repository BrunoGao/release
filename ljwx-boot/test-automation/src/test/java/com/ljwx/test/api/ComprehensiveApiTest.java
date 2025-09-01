package com.ljwx.test.api;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.Arrays;
import java.util.List;

/**
 * 基于实际API接口列表的全面接口测试
 * 验证所有管理端调用的ljwx-boot接口
 */
@Slf4j
public class ComprehensiveApiTest extends BaseApiTest {
    
    private List<ApiTestCase> adminTestCases;
    private List<ApiTestCase> tenantTestCases;
    
    @BeforeClass
    public void setup() {
        setupRestAssured();
        initializeTestCases();
        log.info("全面API接口测试初始化完成");
    }
    
    private void initializeTestCases() {
        // Admin测试用例（customerId=0 全局访问）
        adminTestCases = Arrays.asList(
            new ApiTestCase("首页汇总信息", 
                TestConfig.DASHBOARD_API + "?customer_id=0&customerId=0"),
            new ApiTestCase("租户配置管理", 
                TestConfig.TENANT_API + "/page?page=1&pageSize=20&id=0&customerId=0"),
            new ApiTestCase("组织架构树", 
                TestConfig.ORG_API + "/tree?id=0&customerId=0"),
            new ApiTestCase("接口管理", 
                TestConfig.INTERFACE_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("健康数据配置", 
                TestConfig.HEALTH_CONFIG_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("组织单位列表", 
                TestConfig.ORG_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("岗位管理", 
                TestConfig.POSITION_API + "/page?page=1&pageSize=20&orgId=0&customerId=0"),
            new ApiTestCase("用户管理", 
                TestConfig.USER_API + "/page?page=1&pageSize=10&viewMode=all&customerId=0"),
            new ApiTestCase("根据组织获取用户", 
                TestConfig.USER_API + "/get_users_by_org_id?orgId=1939964806110937090&customerId=0"),
            new ApiTestCase("设备信息管理", 
                TestConfig.DEVICE_API + "/page?page=1&pageSize=20&orgId=0&customerId=0"),
            new ApiTestCase("设备用户关联", 
                TestConfig.DEVICE_USER_API + "/page?page=1&pageSize=20&departmentInfo=0&customerId=0"),
            new ApiTestCase("告警信息", 
                TestConfig.ALERT_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("告警规则", 
                TestConfig.ALERT_RULES_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("告警操作日志", 
                TestConfig.ALERT_LOG_API + "/page?page=1&pageSize=20&customerId=0"),
            new ApiTestCase("微信企业号配置", 
                TestConfig.WECHAT_CONFIG_API + "/page?page=1&pageSize=20&customerId=0&type=enterprise"),
            new ApiTestCase("微信公众号配置", 
                TestConfig.WECHAT_CONFIG_API + "/page?page=1&pageSize=20&customerId=0&type=official"),
            new ApiTestCase("设备消息", 
                TestConfig.MESSAGE_API + "/page?page=1&pageSize=20&departmentInfo=0&customerId=0"),
            new ApiTestCase("健康数据配置页", 
                TestConfig.HEALTH_CONFIG_API + "/page?customerId=0&departmentInfo=&page=1&pageSize=20"),
            new ApiTestCase("用户健康数据", 
                TestConfig.HEALTH_DATA_API + "/getUserHealthData?customerId=0&departmentInfo=&userId=&startDate=1756569600000&endDate=1756655999999&timeType=day&dataType=heart_rate")
        );
        
        // 租户管理员测试用例（使用具体customerId）
        tenantTestCases = Arrays.asList(
            new ApiTestCase("租户首页汇总", 
                TestConfig.DASHBOARD_API + "?customer_id={customerId}&customerId={customerId}"),
            new ApiTestCase("租户配置查看", 
                TestConfig.TENANT_API + "/page?page=1&pageSize=20&id=0&customerId={customerId}"),
            new ApiTestCase("租户组织架构", 
                TestConfig.ORG_API + "/tree?id=0&customerId={customerId}"),
            new ApiTestCase("租户接口管理", 
                TestConfig.INTERFACE_API + "/page?page=1&pageSize=20&customerId={customerId}"),
            new ApiTestCase("租户健康配置", 
                TestConfig.HEALTH_CONFIG_API + "/page?page=1&pageSize=20&customerId={customerId}"),
            new ApiTestCase("租户组织列表", 
                TestConfig.ORG_API + "/page?page=1&pageSize=20&customerId={customerId}"),
            new ApiTestCase("租户岗位管理", 
                TestConfig.POSITION_API + "/page?page=1&pageSize=20&orgId=0&customerId={customerId}"),
            new ApiTestCase("租户用户管理", 
                TestConfig.USER_API + "/page?page=1&pageSize=10&viewMode=all&customerId={customerId}"),
            new ApiTestCase("租户设备管理", 
                TestConfig.DEVICE_API + "/page?page=1&pageSize=20&orgId=0&customerId={customerId}"),
            new ApiTestCase("租户设备用户", 
                TestConfig.DEVICE_USER_API + "/page?page=1&pageSize=20&departmentInfo=0&customerId={customerId}"),
            new ApiTestCase("租户告警信息", 
                TestConfig.ALERT_API + "/page?page=1&pageSize=20&customerId={customerId}"),
            new ApiTestCase("租户告警规则", 
                TestConfig.ALERT_RULES_API + "/page?page=1&pageSize=20&customerId={customerId}"),
            new ApiTestCase("租户微信配置", 
                TestConfig.WECHAT_CONFIG_API + "/page?page=1&pageSize=20&customerId={customerId}&type=enterprise"),
            new ApiTestCase("租户消息管理", 
                TestConfig.MESSAGE_API + "/page?page=1&pageSize=20&departmentInfo=0&customerId={customerId}"),
            new ApiTestCase("租户健康数据", 
                TestConfig.HEALTH_DATA_API + "/getUserHealthData?customerId={customerId}&departmentInfo=&userId=&startDate=1756569600000&endDate=1756655999999&timeType=day&dataType=heart_rate")
        );
    }
    
    @Test(priority = 1, description = "验证Admin访问所有接口")
    public void testAdminAccessAllApis() {
        loginAsAdmin();
        
        log.info("开始测试Admin用户访问所有API接口...");
        int successCount = 0;
        
        for (ApiTestCase testCase : adminTestCases) {
            try {
                log.info("测试Admin接口: {}", testCase.description);
                
                Response response = authenticatedRequest()
                    .when()
                    .get(testCase.url);
                
                if (response.statusCode() == 200) {
                    successCount++;
                    log.info("✅ {}: 访问成功", testCase.description);
                } else {
                    log.warn("⚠️ {}: 返回状态码 {}", testCase.description, response.statusCode());
                }
                
            } catch (Exception e) {
                log.error("❌ {}: 访问异常 - {}", testCase.description, e.getMessage());
            }
        }
        
        double successRate = (double) successCount / adminTestCases.size() * 100;
        log.info("Admin接口访问成功率: {}/{} ({}%)", successCount, adminTestCases.size(), String.format("%.1f", successRate));
        
        Assert.assertTrue(successRate >= 80, "Admin接口访问成功率应该大于80%");
    }
    
    @Test(priority = 2, description = "验证租户管理员访问租户范围接口")
    public void testTenantAdminAccessTenantApis() {
        loginAsTenantAdmin();
        
        log.info("开始测试租户管理员访问租户范围API接口...");
        int successCount = 0;
        
        for (ApiTestCase testCase : tenantTestCases) {
            try {
                String actualUrl = testCase.url.replace("{customerId}", currentCustomerId.toString());
                log.info("测试租户管理员接口: {}", testCase.description);
                
                Response response = authenticatedRequest()
                    .when()
                    .get(actualUrl);
                
                if (response.statusCode() == 200) {
                    successCount++;
                    log.info("✅ {}: 访问成功", testCase.description);
                    
                    verifyTenantDataIsolation(response, testCase.description);
                    
                } else {
                    log.warn("⚠️ {}: 返回状态码 {}", testCase.description, response.statusCode());
                }
                
            } catch (Exception e) {
                log.error("❌ {}: 访问异常 - {}", testCase.description, e.getMessage());
            }
        }
        
        double successRate = (double) successCount / tenantTestCases.size() * 100;
        log.info("租户管理员接口访问成功率: {}/{} ({}%)", successCount, tenantTestCases.size(), String.format("%.1f", successRate));
        
        Assert.assertTrue(successRate >= 80, "租户管理员接口访问成功率应该大于80%");
    }
    
    @Test(priority = 3, description = "验证特殊参数接口功能")
    public void testSpecialParameterApis() {
        loginAsAdmin();
        
        String[] orgIds = {"1940374479725170690", "1957457455646371841", "1960835891196669953"};
        
        Response userByOrgsResponse = authenticatedRequest()
            .queryParam("page", 1)
            .queryParam("pageSize", 10)
            .queryParam("orgIds", String.join(",", orgIds))
            .queryParam("viewMode", "all")
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.USER_API + "/page");
            
        verifySuccess(userByOrgsResponse);
        log.info("✅ 多组织ID用户查询测试通过");
    }
    
    private void verifyTenantDataIsolation(Response response, String apiDescription) {
        if (response.statusCode() == 200) {
            var records = response.jsonPath().getList("data.records");
            if (records != null && !records.isEmpty()) {
                for (Object record : records) {
                    java.util.Map<String, Object> recordMap = (java.util.Map<String, Object>) record;
                    Long recordCustomerId = recordMap.get("customerId") != null ?
                        Long.valueOf(recordMap.get("customerId").toString()) : null;
                        
                    if (recordCustomerId != null && !recordCustomerId.equals(currentCustomerId)) {
                        log.warn("⚠️ {}: 发现跨租户数据，记录customerId={}, 当前用户customerId={}", 
                            apiDescription, recordCustomerId, currentCustomerId);
                    }
                }
            }
        }
    }
    
    private static class ApiTestCase {
        public final String description;
        public final String url;
        
        public ApiTestCase(String description, String url) {
            this.description = description;
            this.url = url;
        }
    }
}