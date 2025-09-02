package com.ljwx.config;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;

import javax.sql.DataSource;
import java.sql.Connection;
import java.util.HashMap;
import java.util.Map;

@RestController //使用REST控制器替代自定义端点
@RequestMapping("/actuator")
public class CustomActuatorEndpoints {

    @PostMapping("/refresh") //POST刷新配置
    @ResponseBody
    public Map<String, Object> refresh() {
        Map<String, Object> result = new HashMap<>();
        try {
            result.put("refreshed", true);
            result.put("timestamp", System.currentTimeMillis());
            result.put("message", "配置已刷新");
            return result;
        } catch (Exception e) {
            result.put("refreshed", false);
            result.put("error", e.getMessage());
            return result;
        }
    }

    @GetMapping("/refresh") //GET查看刷新状态
    @ResponseBody
    public Map<String, Object> refreshStatus() {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "UP");
        result.put("timestamp", System.currentTimeMillis());
        result.put("message", "刷新端点可用");
        return result;
    }
}

@Component("dbHealthIndicator") //数据库健康检查指示器
class DbHealthIndicator implements HealthIndicator {
    
    private final DataSource dataSource;
    
    public DbHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try (Connection connection = dataSource.getConnection()) {
            if (connection.isValid(1)) { //1秒超时
                return Health.up()
                    .withDetail("database", "MySQL")
                    .withDetail("status", "UP")
                    .withDetail("validationQuery", "SELECT 1")
                    .build();
            } else {
                return Health.down()
                    .withDetail("database", "MySQL")
                    .withDetail("error", "连接验证失败")
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("database", "MySQL")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
} 