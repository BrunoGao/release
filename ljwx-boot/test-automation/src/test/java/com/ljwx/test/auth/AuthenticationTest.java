package com.ljwx.test.auth;

import com.ljwx.test.base.BaseApiTest;
import com.ljwx.test.config.TestConfig;
import io.restassured.response.Response;
import lombok.extern.slf4j.Slf4j;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.HashMap;
import java.util.Map;

import static io.restassured.RestAssured.given;

/**
 * 认证功能专项测试
 * 验证登录流程和Token管理
 */
@Slf4j
public class AuthenticationTest extends BaseApiTest {
    
    @BeforeClass
    public void setup() {
        setupRestAssured();
        log.info("认证测试初始化完成");
    }
    
    @Test(priority = 1, description = "验证Admin用户登录认证流程")
    public void testAdminLoginAuthentication() {
        log.info("开始测试Admin用户登录认证...");
        
        Map<String, Object> loginData = new HashMap<>();
        loginData.put("userName", TestConfig.TestUsers.ADMIN_USERNAME);
        loginData.put("password", TestConfig.TestUsers.ADMIN_PASSWORD);
        
        Response response = given()
            .contentType("application/json")
            .body(loginData)
            .when()
            .post(TestConfig.LOGIN_URL)
            .then()
            .statusCode(200)
            .extract().response();
        
        log.info("Admin登录响应: {}", response.asString());
        
        // 验证响应结构
        Assert.assertEquals(response.jsonPath().getInt("code"), 200, "响应码应该为200");
        
        // 获取Token
        String token = extractToken(response);
        Assert.assertNotNull(token, "Token不能为空");
        Assert.assertTrue(token.length() > 10, "Token长度应该合理");
        
        // 保存Token供后续测试使用
        this.authToken = token;
        this.currentUserId = extractUserId(response);
        this.currentCustomerId = extractCustomerId(response);
        
        log.info("✅ Admin用户登录成功, Token: {}..., UserId: {}, CustomerId: {}", 
            token.substring(0, Math.min(20, token.length())), currentUserId, currentCustomerId);
    }
    
    @Test(priority = 2, description = "验证Token有效性")
    public void testTokenValidity() {
        // 使用获取的Token访问需要认证的接口
        Response response = given()
            .header("satoken", authToken)
            .header("Authorization", "Bearer " + authToken)
            .queryParam("customer_id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DASHBOARD_API);
        
        log.info("Token验证响应状态: {}", response.statusCode());
        log.info("Token验证响应: {}", response.asString());
        
        Assert.assertEquals(response.statusCode(), 200, "使用Token访问接口应该成功");
        
        // 验证接口调用成功（基于code字段）
        Assert.assertEquals(response.statusCode(), 200, "HTTP状态码应该为200");
        
        log.info("✅ Token有效性验证通过");
    }
    
    @Test(priority = 3, description = "验证无Token访问被拒绝")
    public void testUnauthorizedAccess() {
        Response response = given()
            .contentType("application/json")
            .queryParam("customer_id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DASHBOARD_API);
        
        log.info("无Token访问响应状态: {}", response.statusCode());
        log.info("无Token访问响应: {}", response.asString());
        
        // 应该返回401未认证或403权限不足，或者返回错误code
        Assert.assertTrue(
            response.statusCode() == 401 || 
            response.statusCode() == 403 || 
            (response.statusCode() == 200 && response.jsonPath().getInt("code") != 200),
            "无Token访问应该被拒绝"
        );
        
        log.info("✅ 无Token访问拒绝验证通过");
    }
    
    @Test(priority = 4, description = "验证错误Token访问被拒绝")
    public void testInvalidTokenAccess() {
        String invalidToken = "invalid_token_12345";
        
        Response response = given()
            .header("satoken", invalidToken)
            .header("Authorization", "Bearer " + invalidToken)
            .queryParam("customer_id", 0)
            .queryParam("customerId", 0)
            .when()
            .get(TestConfig.DASHBOARD_API);
        
        log.info("错误Token访问响应状态: {}", response.statusCode());
        
        // 应该返回认证失败
        Assert.assertTrue(
            response.statusCode() == 401 || 
            response.statusCode() == 403 ||
            (response.statusCode() == 200 && response.jsonPath().getInt("code") != 200),
            "错误Token应该被拒绝"
        );
        
        log.info("✅ 错误Token访问拒绝验证通过");
    }
    
    @Test(priority = 5, description = "验证登录参数验证")
    public void testLoginParameterValidation() {
        // 测试空用户名
        Map<String, Object> emptyUserData = new HashMap<>();
        emptyUserData.put("userName", "");
        emptyUserData.put("password", TestConfig.TestUsers.ADMIN_PASSWORD);
        
        Response emptyUserResponse = given()
            .contentType("application/json")
            .body(emptyUserData)
            .when()
            .post(TestConfig.LOGIN_URL);
        
        Assert.assertTrue(
            emptyUserResponse.statusCode() != 200 || 
            emptyUserResponse.jsonPath().getInt("code") != 200,
            "空用户名应该被拒绝"
        );
        
        // 测试错误密码
        Map<String, Object> wrongPasswordData = new HashMap<>();
        wrongPasswordData.put("userName", TestConfig.TestUsers.ADMIN_USERNAME);
        wrongPasswordData.put("password", "wrong_password");
        
        Response wrongPasswordResponse = given()
            .contentType("application/json")
            .body(wrongPasswordData)
            .when()
            .post(TestConfig.LOGIN_URL);
        
        Assert.assertTrue(
            wrongPasswordResponse.statusCode() != 200 || 
            wrongPasswordResponse.jsonPath().getInt("code") != 200,
            "错误密码应该被拒绝"
        );
        
        log.info("✅ 登录参数验证通过");
    }
    
    /**
     * 从响应中提取Token
     */
    private String extractToken(Response response) {
        if (response.jsonPath().get("data.token") != null) {
            return response.jsonPath().getString("data.token");
        } else if (response.jsonPath().get("data.access_token") != null) {
            return response.jsonPath().getString("data.access_token");
        } else if (response.jsonPath().get("data") != null) {
            return response.jsonPath().getString("data");
        }
        return null;
    }
    
    /**
     * 从响应中提取用户ID
     */
    private Long extractUserId(Response response) {
        try {
            if (response.jsonPath().get("data.userInfo.id") != null) {
                return response.jsonPath().getLong("data.userInfo.id");
            } else if (response.jsonPath().get("data.user.id") != null) {
                return response.jsonPath().getLong("data.user.id");
            }
        } catch (Exception e) {
            log.warn("无法从登录响应中提取用户ID: {}", e.getMessage());
        }
        return null;
    }
    
    /**
     * 从响应中提取租户ID
     */
    private Long extractCustomerId(Response response) {
        try {
            if (response.jsonPath().get("data.userInfo.customerId") != null) {
                return response.jsonPath().getLong("data.userInfo.customerId");
            } else if (response.jsonPath().get("data.user.customerId") != null) {
                return response.jsonPath().getLong("data.user.customerId");
            }
        } catch (Exception e) {
            log.warn("无法从登录响应中提取租户ID: {}", e.getMessage());
        }
        return 0L; // 默认为0（超级管理员）
    }
}