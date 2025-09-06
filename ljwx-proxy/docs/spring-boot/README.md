# Spring Boot API实现文档

## 概述

本目录包含了LJWX健康监测系统v1 API的Spring Boot实现模板和文档。

🎉 **实现状态**: ✅ **已完成** (2025-01-01)  
📍 **实现位置**: `ljwx-boot/ljwx-boot-admin/src/main/java/com/ljwx/admin/controller/health/BigscreenApiV1Controller.java`

## 文件说明

### 控制器文件 (Controllers)
- `HealthController.java` - 健康数据API控制器
- `DeviceController.java` - 设备管理API控制器  
- `UserController.java` - 用户管理API控制器
- `OrganizationController.java` - 组织管理API控制器
- `StatisticsController.java` - 统计分析API控制器
- `AlertController.java` - 告警管理API控制器
- `MessageController.java` - 消息管理API控制器

### 文档文件
- `openapi.yaml` - OpenAPI 3.0规范文档，可用于Swagger UI
- `SPRING_BOOT_IMPLEMENTATION.md` - 完整的实现指南
- `README.md` - 本文件

## 快速开始

### 1. 创建Spring Boot项目

```bash
# 使用Spring Initializr创建项目
curl https://start.spring.io/starter.tgz \
  -d dependencies=web,data-jpa,validation,actuator,mysql \
  -d javaVersion=11 \
  -d artifactId=ljwx-health-api \
  -d groupId=com.ljwx \
  -d name=ljwx-health-api \
  -d packageName=com.ljwx | tar -xzvf -
```

### 2. 添加依赖

在`pom.xml`中添加以下依赖：

```xml
<dependencies>
    <!-- Spring Boot Starters -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- OpenAPI 3 -->
    <dependency>
        <groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-ui</artifactId>
        <version>1.6.14</version>
    </dependency>
    
    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

### 3. 复制控制器文件

将所有`.java`控制器文件复制到你的Spring Boot项目的相应包路径下：

```
src/main/java/com/ljwx/api/v1/controller/
```

### 4. 实现服务接口

根据`SPRING_BOOT_IMPLEMENTATION.md`中的指南实现服务接口和DTO类。

### 5. 配置Swagger

```java
@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("LJWX Health Monitoring API v1")
                        .version("1.0.0"));
    }
}
```

### 6. 启动应用

```bash
mvn spring-boot:run
```

### 7. 访问API文档

启动后访问以下URL查看API文档：

- Swagger UI: http://localhost:8080/swagger-ui.html
- OpenAPI JSON: http://localhost:8080/v3/api-docs
- OpenAPI YAML: http://localhost:8080/v3/api-docs.yaml

## API端点列表

### 健康数据 API
- `GET /api/v1/health/scores/comprehensive` - 获取健康综合评分
- `GET /api/v1/health/realtime-data` - 获取实时健康数据
- `GET /api/v1/health/trends` - 获取健康趋势数据
- `GET /api/v1/health/baseline/chart` - 获取基线数据图表
- `POST /api/v1/health/baseline/generate` - 生成基线数据
- `GET /api/v1/health/data/{id}` - 根据ID获取健康数据
- `GET /api/v1/health/personal/scores` - 获取个人健康评分
- `GET /api/v1/health/recommendations` - 获取健康建议
- `GET /api/v1/health/predictions` - 获取健康预测

### 设备管理 API
- `GET /api/v1/devices/user-info` - 获取设备用户信息
- `GET /api/v1/devices/status` - 获取设备状态信息
- `GET /api/v1/devices/user-organization` - 获取设备用户组织信息

### 用户管理 API
- `GET /api/v1/users/profile` - 获取用户资料
- `GET /api/v1/users` - 获取用户列表

### 组织管理 API
- `GET /api/v1/organizations/statistics` - 获取组织统计信息
- `GET /api/v1/departments` - 获取部门列表

### 统计分析 API
- `GET /api/v1/statistics/overview` - 获取统计概览
- `GET /api/v1/statistics/realtime` - 获取实时统计数据

### 告警管理 API
- `GET /api/v1/alerts/user` - 获取用户告警
- `GET /api/v1/alerts/personal` - 获取个人告警
- `POST /api/v1/alerts/acknowledge` - 确认告警
- `POST /api/v1/alerts/deal` - 处理告警

### 消息管理 API
- `GET /api/v1/messages/user` - 获取用户消息

## 统一响应格式

所有API都返回统一格式的JSON响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 错误处理

API使用标准HTTP状态码和统一的错误响应格式：

```json
{
  "code": 400,
  "message": "参数验证失败: userId不能为空",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 数据验证

使用Bean Validation进行参数验证：

```java
public ApiResponse<HealthScoreDTO> getHealthScore(
    @NotBlank(message = "用户ID不能为空") @RequestParam String userId) {
    // ...
}
```

## 开发建议

### 1. 目录结构
```
com.ljwx/
├── api.v1.controller/     # API控制器
├── api.v1.service/        # 业务服务接口
├── api.v1.service.impl/   # 业务服务实现
├── api.v1.dto/           # 数据传输对象
├── common/               # 公共组件
├── config/              # 配置类
└── infrastructure/      # 基础设施
```

### 2. 最佳实践
- 使用`@RestController`和`@RequestMapping`定义API
- 使用`@Operation`和`@Tag`添加Swagger注解
- 使用`@Valid`进行参数验证
- 实现全局异常处理器
- 使用Lombok减少样板代码
- 添加详细的日志记录

### 3. 测试
- 编写单元测试覆盖业务逻辑
- 使用`@WebMvcTest`进行控制器测试
- 使用`@SpringBootTest`进行集成测试
- 使用MockMvc测试HTTP端点

### 4. 部署
- 配置合适的`application.yml`
- 使用Docker进行容器化部署
- 配置健康检查端点
- 设置监控和日志收集

## 扩展功能

### 1. 认证授权
```java
@EnableWebSecurity
public class SecurityConfig {
    // JWT or OAuth2 配置
}
```

### 2. 缓存
```java
@Cacheable(value = "healthScores", key = "#userId")
public HealthScoreDTO getHealthScore(String userId) {
    // 实现
}
```

### 3. 异步处理
```java
@Async
public CompletableFuture<Void> processHealthData(String data) {
    // 异步处理
}
```

### 4. 消息队列
```java
@EventListener
public void handleHealthAlert(HealthAlertEvent event) {
    // 处理健康告警事件
}
```

## 相关资源

- [Spring Boot官方文档](https://spring.io/projects/spring-boot)
- [OpenAPI 3规范](https://swagger.io/specification/)
- [Spring Boot最佳实践](https://spring.io/guides)
- [Lombok使用指南](https://projectlombok.org/)

---

通过本文档和提供的模板代码，你可以快速搭建一个符合LJWX v1 API规范的Spring Boot应用程序。