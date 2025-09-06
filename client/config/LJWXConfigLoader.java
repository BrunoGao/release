package com.ljwx.common.config;

import org.yaml.snakeyaml.Yaml;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

import javax.annotation.PostConstruct;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Map;

/**
 * LJWX系统配置加载器 - Java版本
 * 统一配置管理，支持YAML配置文件和环境变量覆盖
 *
 * @author LJWX Team
 * @version 2.0.1
 */
@Component
@Configuration
public class LJWXConfigLoader {

    private Map<String, Object> config;
    
    @Value("${ljwx.config.path:/app/config/ljwx-config.yaml}")
    private String configPath;

    @PostConstruct
    public void init() {
        loadConfig();
    }

    /**
     * 加载配置文件
     */
    private void loadConfig() {
        String[] possiblePaths = {
            "/app/config/ljwx-config.yaml",  // 容器内路径
            "/client/config/ljwx-config.yaml",  // 挂载路径
            "client/config/ljwx-config.yaml",  // 相对路径
            "config/ljwx-config.yaml",  // 简化路径
            configPath  // 配置的路径
        };

        for (String path : possiblePaths) {
            File file = new File(path);
            if (file.exists()) {
                try (InputStream input = new FileInputStream(file)) {
                    Yaml yaml = new Yaml();
                    config = yaml.load(input);
                    
                    // 应用环境变量覆盖
                    applyEnvOverrides();
                    return;
                } catch (IOException e) {
                    // 继续尝试下一个路径
                }
            }
        }
        
        throw new RuntimeException("配置文件未找到，请确保ljwx-config.yaml存在");
    }

    /**
     * 应用环境变量覆盖
     */
    @SuppressWarnings("unchecked")
    private void applyEnvOverrides() {
        // 数据库配置覆盖
        Map<String, Object> database = (Map<String, Object>) config.get("database");
        if (database != null) {
            Map<String, Object> mysql = (Map<String, Object>) database.get("mysql");
            if (mysql != null) {
                overrideFromEnv("MYSQL_HOST", mysql, "host");
                overrideFromEnv("MYSQL_PORT", mysql, "port", Integer.class);
                overrideFromEnv("MYSQL_DATABASE", mysql, "database");
                overrideFromEnv("MYSQL_USERNAME", mysql, "username");
                overrideFromEnv("MYSQL_PASSWORD", mysql, "password");
            }

            Map<String, Object> redis = (Map<String, Object>) database.get("redis");
            if (redis != null) {
                overrideFromEnv("REDIS_HOST", redis, "host");
                overrideFromEnv("REDIS_PORT", redis, "port", Integer.class);
                overrideFromEnv("REDIS_PASSWORD", redis, "password");
            }
        }

        // 服务端口覆盖
        String serverPort = System.getenv("SERVER_PORT");
        String serviceName = System.getenv("SERVICE_NAME");
        if (serverPort != null && serviceName != null) {
            Map<String, Object> services = (Map<String, Object>) config.get("services");
            if (services != null && services.containsKey(serviceName)) {
                Map<String, Object> service = (Map<String, Object>) services.get(serviceName);
                service.put("port", Integer.valueOf(serverPort));
            }
        }
    }

    /**
     * 从环境变量覆盖配置
     */
    private void overrideFromEnv(String envKey, Map<String, Object> configMap, String configKey) {
        overrideFromEnv(envKey, configMap, configKey, String.class);
    }

    @SuppressWarnings("unchecked")
    private <T> void overrideFromEnv(String envKey, Map<String, Object> configMap, String configKey, Class<T> type) {
        String envValue = System.getenv(envKey);
        if (envValue != null) {
            Object value = envValue;
            if (type == Integer.class) {
                value = Integer.valueOf(envValue);
            } else if (type == Boolean.class) {
                value = Boolean.valueOf(envValue);
            }
            configMap.put(configKey, value);
        }
    }

    /**
     * 获取配置值，支持点号分隔的嵌套键
     */
    @SuppressWarnings("unchecked")
    public Object get(String key, Object defaultValue) {
        String[] keys = key.split("\\.");
        Object value = config;

        for (String k : keys) {
            if (value instanceof Map) {
                Map<String, Object> map = (Map<String, Object>) value;
                if (map.containsKey(k)) {
                    value = map.get(k);
                } else {
                    return defaultValue;
                }
            } else {
                return defaultValue;
            }
        }

        return value;
    }

    /**
     * 获取配置值
     */
    public Object get(String key) {
        return get(key, null);
    }

    /**
     * 获取字符串配置
     */
    public String getString(String key, String defaultValue) {
        Object value = get(key, defaultValue);
        return value != null ? value.toString() : defaultValue;
    }

    /**
     * 获取整数配置
     */
    public Integer getInt(String key, Integer defaultValue) {
        Object value = get(key, defaultValue);
        if (value instanceof Integer) {
            return (Integer) value;
        } else if (value instanceof String) {
            try {
                return Integer.valueOf((String) value);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        }
        return defaultValue;
    }

    /**
     * 获取数据库配置
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getDatabaseConfig(String dbType) {
        return (Map<String, Object>) get("database." + dbType, null);
    }

    /**
     * 获取服务配置
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getServiceConfig(String serviceName) {
        return (Map<String, Object>) get("services." + serviceName, null);
    }

    /**
     * 获取镜像配置
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getImageConfig() {
        return (Map<String, Object>) get("images", null);
    }

    /**
     * 获取数据库连接URL
     */
    public String getDatabaseUrl(String dbType) {
        Map<String, Object> dbConfig = getDatabaseConfig(dbType);
        if (dbConfig == null) {
            return "";
        }

        if ("mysql".equals(dbType)) {
            String host = (String) dbConfig.get("host");
            Integer port = (Integer) dbConfig.get("port");
            String database = (String) dbConfig.get("database");
            String username = (String) dbConfig.get("username");
            String password = (String) dbConfig.get("password");
            String charset = (String) dbConfig.getOrDefault("charset", "utf8mb4");
            
            return String.format("jdbc:mysql://%s:%d/%s?useUnicode=true&characterEncoding=%s&useSSL=false&serverTimezone=Asia/Shanghai",
                    host, port, database, charset);
        } else if ("redis".equals(dbType)) {
            String host = (String) dbConfig.get("host");
            Integer port = (Integer) dbConfig.get("port");
            String password = (String) dbConfig.get("password");
            Integer db = (Integer) dbConfig.getOrDefault("db", 0);
            
            if (password != null && !password.isEmpty()) {
                return String.format("redis://:%s@%s:%d/%d", password, host, port, db);
            } else {
                return String.format("redis://%s:%d/%d", host, port, db);
            }
        }

        return "";
    }

    /**
     * 重新加载配置
     */
    public void reload() {
        loadConfig();
    }
}