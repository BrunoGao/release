package com.ljwx.test.base;

import com.ljwx.test.config.TestConfig;
import io.restassured.RestAssured;
import io.restassured.response.Response;
import io.restassured.specification.RequestSpecification;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;

import java.util.HashMap;
import java.util.Map;

import static io.restassured.RestAssured.given;

/**
 * API测试基础类
 */
@Slf4j
public abstract class BaseApiTest {
    
    protected String authToken;
    protected Long currentUserId;
    protected Long currentCustomerId;
    
    @BeforeClass
    public void setupRestAssured() {
        RestAssured.baseURI = TestConfig.BASE_URL;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();
        log.info("REST-Assured初始化完成，Base URL: {}", TestConfig.BASE_URL);
    }
    
    /**
     * 用户登录获取Token
     */
    protected LoginResult login(String username, String password) {
        Map<String, Object> loginData = new HashMap<>();
        loginData.put("userName", username);
        loginData.put("password", password);
        
        log.info("尝试登录用户: {}", username);
        
        Response response = given()
            .contentType("application/json")
            .body(loginData)
            .when()
            .post(TestConfig.LOGIN_URL)
            .then()
            .statusCode(200)
            .extract().response();
        
        // 打印完整响应用于调试
        log.debug("登录响应: {}", response.asString());
        
        // 解析登录响应 - 根据实际响应结构调整
        String token = null;
        Long userId = null;
        Long customerId = null;
        
        try {
            // 尝试不同的响应结构解析
            if (response.jsonPath().get("data.token") != null) {
                token = response.jsonPath().getString("data.token");
                userId = response.jsonPath().getLong("data.userInfo.id");
                customerId = response.jsonPath().getLong("data.userInfo.customerId");
            } else if (response.jsonPath().get("data.access_token") != null) {
                token = response.jsonPath().getString("data.access_token");
                userId = response.jsonPath().getLong("data.user.id");
                customerId = response.jsonPath().getLong("data.user.customerId");
            } else if (response.jsonPath().get("token") != null) {
                token = response.jsonPath().getString("token");
                userId = response.jsonPath().getLong("userId");
                customerId = response.jsonPath().getLong("customerId");
            } else {
                // 直接从data中获取
                token = response.jsonPath().getString("data");
                // 如果token是字符串，尝试解析用户信息
                if (token != null && !token.startsWith("eyJ")) {
                    // 可能需要额外的用户信息查询
                    log.warn("登录返回的token格式异常，可能需要额外的用户信息查询");
                }
            }
        } catch (Exception e) {
            log.error("解析登录响应失败: {}", e.getMessage());
            log.error("响应内容: {}", response.asString());
        }
        
        Assert.assertNotNull(token, "登录Token不能为空，响应: " + response.asString());
        
        log.info("用户 {} 登录成功, Token: {}, UserId: {}, CustomerId: {}", 
            username, token.substring(0, Math.min(20, token.length())) + "...", userId, customerId);
        
        return new LoginResult(token, userId, customerId);
    }
    
    /**
     * 管理员登录
     */
    protected void loginAsAdmin() {
        LoginResult result = login(TestConfig.TestUsers.ADMIN_USERNAME, TestConfig.TestUsers.ADMIN_PASSWORD);
        this.authToken = result.getToken();
        this.currentUserId = result.getUserId();
        this.currentCustomerId = result.getCustomerId();
    }
    
    /**
     * 租户管理员登录
     */
    protected void loginAsTenantAdmin() {
        LoginResult result = login(TestConfig.TestUsers.TENANT_ADMIN_USERNAME, TestConfig.TestUsers.TENANT_ADMIN_PASSWORD);
        this.authToken = result.getToken();
        this.currentUserId = result.getUserId();
        this.currentCustomerId = result.getCustomerId();
    }
    
    /**
     * 获取认证的请求规范
     */
    protected RequestSpecification authenticatedRequest() {
        Assert.assertNotNull(authToken, "请先登录获取Token");
        
        // 根据SA-Token的标准，通常使用satoken作为header名称
        return given()
            .header("satoken", authToken)
            .header("Authorization", "Bearer " + authToken) // 备用认证方式
            .contentType("application/json");
    }
    
    /**
     * 验证API响应成功
     */
    protected void verifySuccess(Response response) {
        response.then()
            .statusCode(200)
            .body("code", org.hamcrest.Matchers.equalTo(200))
            .body("success", org.hamcrest.Matchers.equalTo(true));
    }
    
    /**
     * 验证API响应失败（权限不足）
     */
    protected void verifyPermissionDenied(Response response) {
        response.then()
            .statusCode(200)
            .body("code", org.hamcrest.Matchers.not(200));
    }
    
    /**
     * 验证数据访问权限
     */
    protected void verifyDataAccess(String apiPath, Long expectedCustomerId, String description) {
        log.info("验证数据访问权限: {}", description);
        
        Response response = authenticatedRequest()
            .queryParam("current", 1)
            .queryParam("size", 5)
            .when()
            .get(apiPath);
            
        verifySuccess(response);
        
        // 如果有数据，验证所有数据都属于预期的租户
        if (expectedCustomerId != null && response.jsonPath().getList("data.records") != null) {
            response.then()
                .body("data.records.findAll { it.customerId != null }.every { it.customerId == " + expectedCustomerId + " }", 
                      org.hamcrest.Matchers.is(true));
        }
    }
    
    /**
     * 验证跨租户访问被拒绝
     */
    protected void verifyCrossTenantAccessDenied(String apiPath, String description) {
        log.info("验证跨租户访问拒绝: {}", description);
        
        Response response = authenticatedRequest()
            .queryParam("customerId", TestConfig.TestTenants.TENANT_B_ID) // 尝试访问其他租户数据
            .when()
            .get(apiPath);
        
        // 应该返回空数据或者权限错误
        Assert.assertTrue(
            response.statusCode() != 200 || 
            response.jsonPath().getList("data.records").isEmpty(),
            "应该无法访问其他租户的数据"
        );
    }
    
    /**
     * 登录结果内部类
     */
    public static class LoginResult {
        private final String token;
        private final Long userId;
        private final Long customerId;
        
        public LoginResult(String token, Long userId, Long customerId) {
            this.token = token;
            this.userId = userId;
            this.customerId = customerId;
        }
        
        public String getToken() { return token; }
        public Long getUserId() { return userId; }
        public Long getCustomerId() { return customerId; }
    }
}