# Spring Boot API实现指南

## 概述

本文档提供了在Spring Boot中实现LJWX v1 API的详细指南，包括控制器、服务接口、DTO类和配置示例。

## 项目结构

```
src/main/java/com/ljwx/
├── api/v1/
│   ├── controller/          # API控制器
│   │   ├── HealthController.java
│   │   ├── DeviceController.java
│   │   ├── UserController.java
│   │   ├── OrganizationController.java
│   │   ├── StatisticsController.java
│   │   ├── AlertController.java
│   │   └── MessageController.java
│   ├── service/             # 服务接口
│   │   ├── HealthService.java
│   │   ├── DeviceService.java
│   │   └── ...
│   ├── dto/                 # 数据传输对象
│   │   ├── request/         # 请求DTO
│   │   └── response/        # 响应DTO
│   └── config/              # 配置类
├── common/                  # 公共组件
│   ├── response/           # 统一响应格式
│   ├── exception/          # 异常处理
│   └── config/            # 全局配置
└── infrastructure/         # 基础设施层
    ├── persistence/       # 数据持久化
    └── external/         # 外部服务调用
```

## 核心组件

### 1. 统一响应格式

```java
package com.ljwx.common.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponse<T> {
    
    private int code;
    private String message;
    private T data;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime timestamp;
    
    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
                .code(200)
                .message("success")
                .data(data)
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    public static <T> ApiResponse<T> success(T data, String message) {
        return ApiResponse.<T>builder()
                .code(200)
                .message(message)
                .data(data)
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    public static <T> ApiResponse<T> error(int code, String message) {
        return ApiResponse.<T>builder()
                .code(code)
                .message(message)
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    public static <T> ApiResponse<T> error(String message) {
        return error(500, message);
    }
}
```

### 2. 全局异常处理

```java
package com.ljwx.common.exception;

import com.ljwx.common.response.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException e) {
        log.error("Business exception: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error(400, e.getMessage()));
    }
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleResourceNotFoundException(ResourceNotFoundException e) {
        log.error("Resource not found: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.error(404, e.getMessage()));
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .reduce("", (a, b) -> a + "; " + b);
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.error(400, "参数验证失败: " + message));
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleException(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error(500, "服务器内部错误"));
    }
}
```

### 3. 自定义异常类

```java
package com.ljwx.common.exception;

public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
    
    public BusinessException(String message, Throwable cause) {
        super(message, cause);
    }
}

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
```

## 服务接口定义

### HealthService 接口

```java
package com.ljwx.api.v1.service;

import com.ljwx.api.v1.dto.request.*;
import com.ljwx.api.v1.dto.response.*;

import java.util.List;

public interface HealthService {
    
    /**
     * 获取健康综合评分
     */
    HealthScoreDTO getComprehensiveHealthScore(HealthScoreQueryDTO query);
    
    /**
     * 获取实时健康数据
     */
    RealtimeHealthDataDTO getRealtimeHealthData(RealtimeHealthQueryDTO query);
    
    /**
     * 获取健康趋势数据
     */
    List<HealthTrendDTO> getHealthTrends(HealthTrendQueryDTO query);
    
    /**
     * 获取基线数据图表
     */
    BaselineChartDTO getBaselineChart(BaselineChartQueryDTO query);
    
    /**
     * 生成基线数据
     */
    BaselineGenerateResultDTO generateBaseline(BaselineGenerateRequestDTO request);
    
    /**
     * 根据ID获取健康数据
     */
    HealthDataDetailDTO getHealthDataById(String id);
    
    /**
     * 获取个人健康评分
     */
    PersonalHealthScoreDTO getPersonalHealthScores(PersonalHealthScoreQueryDTO query);
    
    /**
     * 获取健康建议
     */
    List<HealthRecommendationDTO> getHealthRecommendations(String userId);
    
    /**
     * 获取健康预测
     */
    List<HealthPredictionDTO> getHealthPredictions(String userId);
}
```

### DeviceService 接口

```java
package com.ljwx.api.v1.service;

import com.ljwx.api.v1.dto.response.*;

public interface DeviceService {
    
    /**
     * 获取设备用户信息
     */
    DeviceUserInfoDTO getDeviceUserInfo(String deviceSn);
    
    /**
     * 获取设备状态信息
     */
    DeviceStatusDTO getDeviceStatus(String deviceSn);
    
    /**
     * 获取设备用户组织信息
     */
    DeviceUserOrganizationDTO getDeviceUserOrganization(String deviceSn);
}
```

## DTO类定义示例

### 请求DTO

```java
package com.ljwx.api.v1.dto.request;

import lombok.Builder;
import lombok.Data;
import javax.validation.constraints.NotBlank;

@Data
@Builder
public class HealthScoreQueryDTO {
    private String userId;
    private String orgId;
    private String date;
}

@Data
@Builder
public class RealtimeHealthQueryDTO {
    private String userId;
    private String deviceSn;
}

@Data
@Builder
public class BaselineGenerateRequestDTO {
    @NotBlank(message = "组织ID不能为空")
    private String orgId;
    
    private DateRangeDTO dateRange;
    
    @Data
    @Builder
    public static class DateRangeDTO {
        private String startDate;
        private String endDate;
    }
}
```

### 响应DTO

```java
package com.ljwx.api.v1.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthScoreDTO {
    private Integer score;
    private String level;
    private String description;
    private LocalDateTime timestamp;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RealtimeHealthDataDTO {
    private Integer heartRate;
    private String bloodPressure;
    private Double temperature;
    private Integer oxygenLevel;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime timestamp;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceUserInfoDTO {
    private String userId;
    private String userName;
    private String deviceSn;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'")
    private LocalDateTime bindTime;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthRecommendationDTO {
    private String type;
    private String title;
    private String description;
    private String priority;
}
```

## Swagger配置

### OpenAPI 3配置

```java
package com.ljwx.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Arrays;

@Configuration
public class OpenApiConfig {
    
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("LJWX Health Monitoring API v1")
                        .description("智能健康监测系统API接口文档 v1.0.0")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("LJWX Team")
                                .email("support@ljwx.com"))
                        .license(new License()
                                .name("MIT")
                                .url("https://opensource.org/licenses/MIT")))
                .servers(Arrays.asList(
                        new Server().url("http://localhost:8080").description("开发环境"),
                        new Server().url("https://api.ljwx.com").description("生产环境")));
    }
}
```

## 服务实现示例

### HealthServiceImpl

```java
package com.ljwx.api.v1.service.impl;

import com.ljwx.api.v1.dto.request.*;
import com.ljwx.api.v1.dto.response.*;
import com.ljwx.api.v1.service.HealthService;
import com.ljwx.common.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class HealthServiceImpl implements HealthService {
    
    @Override
    public HealthScoreDTO getComprehensiveHealthScore(HealthScoreQueryDTO query) {
        log.info("Getting comprehensive health score for query: {}", query);
        
        // 这里实现具体的业务逻辑
        // 1. 参数验证
        // 2. 数据查询
        // 3. 业务处理
        // 4. 返回结果
        
        return HealthScoreDTO.builder()
                .score(85)
                .level("良好")
                .description("健康状况良好")
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    @Override
    public RealtimeHealthDataDTO getRealtimeHealthData(RealtimeHealthQueryDTO query) {
        log.info("Getting realtime health data for query: {}", query);
        
        if (query.getUserId() == null && query.getDeviceSn() == null) {
            throw new IllegalArgumentException("用户ID或设备序列号至少需要提供一个");
        }
        
        // 实现实时数据获取逻辑
        return RealtimeHealthDataDTO.builder()
                .heartRate(75)
                .bloodPressure("120/80")
                .temperature(36.5)
                .oxygenLevel(98)
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    @Override
    public HealthDataDetailDTO getHealthDataById(String id) {
        log.info("Getting health data by id: {}", id);
        
        if (id == null || id.trim().isEmpty()) {
            throw new IllegalArgumentException("健康数据ID不能为空");
        }
        
        // 根据ID查询健康数据
        // 如果数据不存在，抛出ResourceNotFoundException
        
        return HealthDataDetailDTO.builder()
                .id(id)
                .userId("123")
                .deviceSn("CRFTQ23409001890")
                .data("健康数据详情")
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    // 其他方法实现...
}
```

## 数据验证

### 使用Bean Validation

```java
package com.ljwx.api.v1.dto.request;

import lombok.Data;
import javax.validation.constraints.*;

@Data
public class HealthTrendQueryDTO {
    
    @NotBlank(message = "用户ID不能为空")
    private String userId;
    
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}", message = "日期格式必须为yyyy-MM-dd")
    private String startDate;
    
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}", message = "日期格式必须为yyyy-MM-dd")  
    private String endDate;
}
```

### 控制器中启用验证

```java
@PostMapping("/baseline/generate")
@Operation(summary = "生成基线数据")
public ApiResponse<BaselineGenerateResultDTO> generateBaseline(
        @Valid @RequestBody BaselineGenerateRequestDTO request) {
    
    BaselineGenerateResultDTO result = healthService.generateBaseline(request);
    return ApiResponse.success(result);
}
```

## 数据库配置

### application.yml 示例

```yaml
spring:
  application:
    name: ljwx-health-api
  
  datasource:
    url: jdbc:mysql://localhost:3306/ljwx_health?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC
    username: ${DB_USERNAME:ljwx}
    password: ${DB_PASSWORD:ljwx123}
    driver-class-name: com.mysql.cj.jdbc.Driver
    
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.MySQL8Dialect
        format_sql: true
        
  redis:
    host: ${REDIS_HOST:localhost}
    port: ${REDIS_PORT:6379}
    password: ${REDIS_PASSWORD:}
    timeout: 6000ms
    lettuce:
      pool:
        max-active: 10
        max-wait: -1ms
        max-idle: 5
        min-idle: 0

logging:
  level:
    com.ljwx: DEBUG
    org.springframework.web: DEBUG
  pattern:
    console: "%clr(%d{yyyy-MM-dd HH:mm:ss.SSS}){faint} %clr(%5p) %clr(${PID:- }){magenta} %clr(---){faint} %clr([%15.15t]){faint} %clr(%-40.40logger{39}){cyan} %clr(:){faint} %m%n%wEx"

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always

server:
  port: 8080
  servlet:
    context-path: /
```

## 部署配置

### Docker配置

```dockerfile
FROM openjdk:11-jre-slim

COPY target/ljwx-health-api-*.jar app.jar

EXPOSE 8080

ENV JAVA_OPTS="-Xmx512m -Xms256m"
ENV SPRING_PROFILES_ACTIVE=prod

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -Djava.security.egd=file:/dev/./urandom -jar /app.jar"]
```

### Maven依赖

```xml
<dependencies>
    <!-- Spring Boot Starters -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-redis</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
    
    <!-- OpenAPI 3 -->
    <dependency>
        <groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-ui</artifactId>
        <version>1.6.14</version>
    </dependency>
    
    <!-- Database -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <scope>runtime</scope>
    </dependency>
    
    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
    
    <!-- Test -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## 测试示例

### 单元测试

```java
package com.ljwx.api.v1.service;

import com.ljwx.api.v1.dto.request.HealthScoreQueryDTO;
import com.ljwx.api.v1.dto.response.HealthScoreDTO;
import com.ljwx.api.v1.service.impl.HealthServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
class HealthServiceTest {
    
    @InjectMocks
    private HealthServiceImpl healthService;
    
    @Test
    void getComprehensiveHealthScore_ShouldReturnValidScore() {
        // Given
        HealthScoreQueryDTO query = HealthScoreQueryDTO.builder()
                .userId("123")
                .build();
        
        // When
        HealthScoreDTO result = healthService.getComprehensiveHealthScore(query);
        
        // Then
        assertThat(result).isNotNull();
        assertThat(result.getScore()).isGreaterThan(0);
        assertThat(result.getLevel()).isNotBlank();
    }
}
```

### 集成测试

```java
package com.ljwx.api.v1.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(HealthController.class)
class HealthControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private HealthService healthService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Test
    void getComprehensiveHealthScore_ShouldReturnSuccess() throws Exception {
        mockMvc.perform(get("/api/v1/health/scores/comprehensive")
                .param("userId", "123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.message").value("success"));
    }
}
```

## 最佳实践

### 1. 错误处理
- 使用全局异常处理器统一处理异常
- 定义业务异常类，提供有意义的错误信息
- 记录详细的错误日志

### 2. 参数验证
- 使用Bean Validation进行参数验证
- 在Service层进行业务逻辑验证
- 提供清晰的验证错误信息

### 3. 日志记录
- 记录关键业务操作的日志
- 使用结构化日志格式
- 包含请求ID用于链路追踪

### 4. 缓存策略
- 对频繁查询的数据进行缓存
- 设置合适的缓存过期时间
- 实现缓存更新策略

### 5. 性能优化
- 使用数据库连接池
- 实现分页查询
- 优化数据库索引
- 使用异步处理耗时操作

这个实现指南提供了完整的Spring Boot API开发框架，可以直接用于实现LJWX健康监测系统的后端服务。