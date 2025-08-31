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
        );\n    }\n    \n    @Test(priority = 1, description = \"验证Admin访问所有接口\")\n    public void testAdminAccessAllApis() {\n        loginAsAdmin();\n        \n        log.info(\"开始测试Admin用户访问所有API接口...\");\n        int successCount = 0;\n        \n        for (ApiTestCase testCase : adminTestCases) {\n            try {\n                log.info(\"测试Admin接口: {}\", testCase.description);\n                \n                Response response = authenticatedRequest()\n                    .when()\n                    .get(testCase.url);\n                \n                if (response.statusCode() == 200) {\n                    successCount++;\n                    log.info(\"✅ {}: 访问成功\", testCase.description);\n                } else {\n                    log.warn(\"⚠️ {}: 返回状态码 {}\", testCase.description, response.statusCode());\n                }\n                \n            } catch (Exception e) {\n                log.error(\"❌ {}: 访问异常 - {}\", testCase.description, e.getMessage());\n            }\n        }\n        \n        double successRate = (double) successCount / adminTestCases.size() * 100;\n        log.info(\"Admin接口访问成功率: {}/{} ({}%)\", successCount, adminTestCases.size(), String.format(\"%.1f\", successRate));\n        \n        Assert.assertTrue(successRate >= 80, \"Admin接口访问成功率应该大于80%\");\n    }\n    \n    @Test(priority = 2, description = \"验证租户管理员访问租户范围接口\")\n    public void testTenantAdminAccessTenantApis() {\n        loginAsTenantAdmin();\n        \n        log.info(\"开始测试租户管理员访问租户范围API接口...\");\n        int successCount = 0;\n        \n        for (ApiTestCase testCase : tenantTestCases) {\n            try {\n                // 替换URL中的占位符\n                String actualUrl = testCase.url.replace(\"{customerId}\", currentCustomerId.toString());\n                log.info(\"测试租户管理员接口: {}\", testCase.description);\n                \n                Response response = authenticatedRequest()\n                    .when()\n                    .get(actualUrl);\n                \n                if (response.statusCode() == 200) {\n                    successCount++;\n                    log.info(\"✅ {}: 访问成功\", testCase.description);\n                    \n                    // 验证返回数据的租户隔离\n                    verifyTenantDataIsolation(response, testCase.description);\n                    \n                } else {\n                    log.warn(\"⚠️ {}: 返回状态码 {}\", testCase.description, response.statusCode());\n                }\n                \n            } catch (Exception e) {\n                log.error(\"❌ {}: 访问异常 - {}\", testCase.description, e.getMessage());\n            }\n        }\n        \n        double successRate = (double) successCount / tenantTestCases.size() * 100;\n        log.info(\"租户管理员接口访问成功率: {}/{} ({}%)\", successCount, tenantTestCases.size(), String.format(\"%.1f\", successRate));\n        \n        Assert.assertTrue(successRate >= 80, \"租户管理员接口访问成功率应该大于80%\");\n    }\n    \n    @Test(priority = 3, description = \"验证特殊参数接口功能\")\n    public void testSpecialParameterApis() {\n        loginAsAdmin();\n        \n        // 测试组织ID参数接口\n        String[] orgIds = {\"1940374479725170690\", \"1957457455646371841\", \"1960835891196669953\"};\n        String orgIdsParam = String.join(\"%2C\", orgIds); // URL编码的逗号\n        \n        Response userByOrgsResponse = authenticatedRequest()\n            .queryParam(\"page\", 1)\n            .queryParam(\"pageSize\", 10)\n            .queryParam(\"orgIds\", String.join(\",\", orgIds))\n            .queryParam(\"viewMode\", \"all\")\n            .queryParam(\"customerId\", 0)\n            .when()\n            .get(TestConfig.USER_API + \"/page\");\n            \n        verifySuccess(userByOrgsResponse);\n        log.info(\"✅ 多组织ID用户查询测试通过\");\n        \n        // 测试时间范围健康数据查询\n        long currentTime = System.currentTimeMillis();\n        long startTime = 1756569600000L; // 示例时间戳\n        long endTime = 1756655999999L;\n        \n        Response healthDataTimeResponse = authenticatedRequest()\n            .queryParam(\"customerId\", 0)\n            .queryParam(\"departmentInfo\", \"\")\n            .queryParam(\"userId\", \"\")\n            .queryParam(\"startDate\", startTime)\n            .queryParam(\"endDate\", endTime)\n            .queryParam(\"timeType\", \"day\")\n            .queryParam(\"dataType\", \"heart_rate\")\n            .when()\n            .get(TestConfig.HEALTH_DATA_API + \"/getUserHealthData\");\n            \n        verifySuccess(healthDataTimeResponse);\n        log.info(\"✅ 时间范围健康数据查询测试通过\");\n        \n        // 测试不同健康数据类型\n        String[] dataTypes = {\"heart_rate\", \"blood_pressure\", \"spo2\", \"temperature\"};\n        for (String dataType : dataTypes) {\n            Response typeResponse = authenticatedRequest()\n                .queryParam(\"customerId\", 0)\n                .queryParam(\"departmentInfo\", \"\")\n                .queryParam(\"timeType\", \"day\")\n                .queryParam(\"dataType\", dataType)\n                .when()\n                .get(TestConfig.HEALTH_DATA_API + \"/getUserHealthData\");\n                \n            if (typeResponse.statusCode() == 200) {\n                log.info(\"✅ 健康数据类型 {} 查询成功\", dataType);\n            }\n        }\n    }\n    \n    @Test(priority = 4, description = \"验证微信配置接口的不同类型\")\n    public void testWechatConfigTypes() {\n        loginAsAdmin();\n        \n        // 测试企业号配置\n        Response enterpriseResponse = authenticatedRequest()\n            .queryParam(\"page\", 1)\n            .queryParam(\"pageSize\", 20)\n            .queryParam(\"customerId\", 0)\n            .queryParam(\"type\", \"enterprise\")\n            .when()\n            .get(TestConfig.WECHAT_CONFIG_API + \"/page\");\n            \n        verifySuccess(enterpriseResponse);\n        log.info(\"✅ 微信企业号配置接口测试通过\");\n        \n        // 测试公众号配置\n        Response officialResponse = authenticatedRequest()\n            .queryParam(\"page\", 1)\n            .queryParam(\"pageSize\", 20)\n            .queryParam(\"customerId\", 0)\n            .queryParam(\"type\", \"official\")\n            .when()\n            .get(TestConfig.WECHAT_CONFIG_API + \"/page\");\n            \n        verifySuccess(officialResponse);\n        log.info(\"✅ 微信公众号配置接口测试通过\");\n    }\n    \n    @Test(priority = 5, description = \"验证分页参数规范性\")\n    public void testPaginationParameterStandards() {\n        loginAsAdmin();\n        \n        // 测试不同分页大小\n        int[] pageSizes = {10, 20, 50};\n        \n        for (int pageSize : pageSizes) {\n            Response response = authenticatedRequest()\n                .queryParam(\"page\", 1)\n                .queryParam(\"pageSize\", pageSize)\n                .queryParam(\"customerId\", 0)\n                .when()\n                .get(TestConfig.USER_API + \"/page\");\n                \n            if (response.statusCode() == 200) {\n                var records = response.jsonPath().getList(\"data.records\");\n                int actualSize = records != null ? records.size() : 0;\n                \n                Assert.assertTrue(actualSize <= pageSize, \n                    \"返回记录数不应超过请求的pageSize\");\n                    \n                log.info(\"✅ 分页大小 {} 测试通过，实际返回: {}\", pageSize, actualSize);\n            }\n        }\n    }\n    \n    @Test(priority = 6, description = \"验证接口响应格式一致性\")\n    public void testApiResponseFormatConsistency() {\n        loginAsAdmin();\n        \n        String[] testApis = {\n            TestConfig.TENANT_API + \"/page?page=1&pageSize=5&customerId=0\",\n            TestConfig.USER_API + \"/page?page=1&pageSize=5&customerId=0\",\n            TestConfig.DEVICE_API + \"/page?page=1&pageSize=5&customerId=0\",\n            TestConfig.ALERT_API + \"/page?page=1&pageSize=5&customerId=0\"\n        };\n        \n        for (String api : testApis) {\n            Response response = authenticatedRequest().when().get(api);\n            \n            if (response.statusCode() == 200) {\n                // 验证标准响应格式\n                Assert.assertNotNull(response.jsonPath().get(\"code\"), \"响应应包含code字段\");\n                Assert.assertNotNull(response.jsonPath().get(\"success\"), \"响应应包含success字段\");\n                Assert.assertNotNull(response.jsonPath().get(\"data\"), \"响应应包含data字段\");\n                \n                // 分页接口特有字段\n                if (api.contains(\"/page\")) {\n                    Object records = response.jsonPath().get(\"data.records\");\n                    Object total = response.jsonPath().get(\"data.total\");\n                    Assert.assertNotNull(records, \"分页接口应包含records字段\");\n                    log.info(\"✅ 接口 {} 响应格式验证通过\", api);\n                }\n            }\n        }\n    }\n    \n    /**\n     * 验证租户数据隔离\n     */\n    private void verifyTenantDataIsolation(Response response, String apiDescription) {\n        if (response.statusCode() == 200) {\n            var records = response.jsonPath().getList(\"data.records\");\n            if (records != null && !records.isEmpty()) {\n                // 检查每条记录的customerId\n                for (Object record : records) {\n                    Map<String, Object> recordMap = (Map<String, Object>) record;\n                    Long recordCustomerId = recordMap.get(\"customerId\") != null ?\n                        Long.valueOf(recordMap.get(\"customerId\").toString()) : null;\n                        \n                    if (recordCustomerId != null && !recordCustomerId.equals(currentCustomerId)) {\n                        log.warn(\"⚠️ {}: 发现跨租户数据，记录customerId={}, 当前用户customerId={}\", \n                            apiDescription, recordCustomerId, currentCustomerId);\n                    }\n                }\n            }\n        }\n    }\n    \n    /**\n     * API测试用例数据类\n     */\n    private static class ApiTestCase {\n        public final String description;\n        public final String url;\n        \n        public ApiTestCase(String description, String url) {\n            this.description = description;\n            this.url = url;\n        }\n    }\n}