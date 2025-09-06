# LJWX系统统一配置集成示例

## ljwx-bigscreen (Python Flask) 集成示例

### 1. 修改主应用文件

在 `ljwx-bigscreen/bigscreen/app.py` 或 `run.py` 中：

```python
# 原有代码
import os
from flask import Flask
# ... 其他导入

# 新增：导入统一配置
import sys
sys.path.append('/client/config')
sys.path.append('/app/config')

try:
    from config_loader import get_database_config, get_service_config, get_config
    
    # 从统一配置加载
    mysql_config = get_database_config('mysql')
    redis_config = get_database_config('redis')
    service_config = get_service_config('ljwx-bigscreen')
    
    # 数据库连接配置
    DATABASE_CONFIG = {
        'host': mysql_config['host'],
        'port': mysql_config['port'],
        'database': mysql_config['database'],
        'username': mysql_config['username'],
        'password': mysql_config['password'],
        'charset': mysql_config.get('charset', 'utf8mb4')
    }
    
    # Redis配置
    REDIS_CONFIG = {
        'host': redis_config['host'],
        'port': redis_config['port'],
        'password': redis_config.get('password', ''),
        'db': redis_config.get('db', 0)
    }
    
    # 应用配置
    APP_PORT = service_config['port']
    
except ImportError:
    # 备用配置（兼容现有部署）
    DATABASE_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'ljwx-mysql'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'database': os.getenv('MYSQL_DATABASE', 'test'),
        'username': os.getenv('MYSQL_USERNAME', 'ljwx'),
        'password': os.getenv('MYSQL_PASSWORD', '123456'),
        'charset': 'utf8mb4'
    }
    
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'ljwx-redis'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD', ''),
        'db': int(os.getenv('REDIS_DB', 0))
    }
    
    APP_PORT = int(os.getenv('SERVER_PORT', 8001))

# Flask应用初始化
app = Flask(__name__)

# 使用统一配置
app.config.update({
    'MYSQL_HOST': DATABASE_CONFIG['host'],
    'MYSQL_PORT': DATABASE_CONFIG['port'],
    'MYSQL_DATABASE': DATABASE_CONFIG['database'],
    'MYSQL_USER': DATABASE_CONFIG['username'],
    'MYSQL_PASSWORD': DATABASE_CONFIG['password'],
    'REDIS_HOST': REDIS_CONFIG['host'],
    'REDIS_PORT': REDIS_CONFIG['port'],
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT, debug=False)
```

### 2. 修改数据库连接模块

在数据库连接文件中：

```python
# 原有代码中的数据库连接部分
import pymysql
from sqlalchemy import create_engine

# 使用统一配置
from app import DATABASE_CONFIG

# SQLAlchemy连接
def get_database_engine():
    connection_url = f"mysql+pymysql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"
    return create_engine(connection_url, pool_pre_ping=True, pool_recycle=3600)

# PyMySQL直接连接
def get_mysql_connection():
    return pymysql.connect(
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port'],
        user=DATABASE_CONFIG['username'],
        password=DATABASE_CONFIG['password'],
        database=DATABASE_CONFIG['database'],
        charset=DATABASE_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
```

## ljwx-boot (Spring Boot) 集成示例

### 1. 添加配置类

创建 `src/main/java/com/ljwx/common/config/LJWXConfiguration.java`：

```java
@Configuration
@EnableConfigurationProperties
public class LJWXConfiguration {

    @Autowired
    private LJWXConfigLoader configLoader;

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource")
    public DataSourceProperties dataSourceProperties() {
        DataSourceProperties properties = new DataSourceProperties();
        
        Map<String, Object> mysqlConfig = configLoader.getDatabaseConfig("mysql");
        if (mysqlConfig != null) {
            String host = (String) mysqlConfig.get("host");
            Integer port = (Integer) mysqlConfig.get("port");
            String database = (String) mysqlConfig.get("database");
            String username = (String) mysqlConfig.get("username");
            String password = (String) mysqlConfig.get("password");
            
            String url = String.format("jdbc:mysql://%s:%d/%s?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai",
                    host, port, database);
            
            properties.setUrl(url);
            properties.setUsername(username);
            properties.setPassword(password);
            properties.setDriverClassName("com.mysql.cj.jdbc.Driver");
        }
        
        return properties;
    }

    @Bean
    @ConfigurationProperties(prefix = "spring.redis")
    public LettuceConnectionFactory redisConnectionFactory() {
        Map<String, Object> redisConfig = configLoader.getDatabaseConfig("redis");
        if (redisConfig != null) {
            String host = (String) redisConfig.get("host");
            Integer port = (Integer) redisConfig.get("port");
            String password = (String) redisConfig.get("password");
            
            RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
            config.setHostName(host);
            config.setPort(port);
            if (password != null && !password.isEmpty()) {
                config.setPassword(password);
            }
            
            return new LettuceConnectionFactory(config);
        }
        
        return new LettuceConnectionFactory();
    }
}
```

### 2. 修改应用启动类

在 `Application.java` 中：

```java
@SpringBootApplication
@ComponentScan(basePackages = {"com.ljwx"})
public class LJWXBootApplication {

    @Autowired
    private LJWXConfigLoader configLoader;

    public static void main(String[] args) {
        SpringApplication.run(LJWXBootApplication.class, args);
    }

    @PostConstruct
    public void init() {
        // 打印配置信息用于调试
        Map<String, Object> serviceConfig = configLoader.getServiceConfig("ljwx-boot");
        log.info("LJWX Boot服务配置: {}", serviceConfig);
    }
}
```

## ljwx-admin (Vue.js + Node.js) 集成示例

### 1. 在构建配置中使用

在 `vite.config.js` 或 `webpack.config.js` 中：

```javascript
const { getConfig, getDatabaseConfig } = require('../client/config/config-loader');

// 加载统一配置
const config = getConfig();
const serviceConfig = config.getServiceConfig('ljwx-admin');

export default defineConfig({
  server: {
    port: serviceConfig.port,
    proxy: {
      '/api': {
        target: `http://ljwx-boot:${config.getServiceConfig('ljwx-boot').port}`,
        changeOrigin: true,
      }
    }
  },
  define: {
    // 将配置注入到环境变量
    __LJWX_CONFIG__: JSON.stringify({
      apiUrl: `/api`,
      version: config.get('system.version'),
    })
  }
});
```

### 2. 在前端代码中使用

创建 `src/config/index.js`：

```javascript
// 前端配置
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || '/api',
  version: import.meta.env.VITE_VERSION || '2.0.1',
  
  // 从后端获取的配置
  async loadRuntimeConfig() {
    try {
      const response = await fetch('/api/system/config');
      return await response.json();
    } catch (error) {
      console.warn('无法加载运行时配置:', error);
      return {};
    }
  }
};
```

## Docker配置挂载示例

### 1. 在 Dockerfile 中添加配置支持

```dockerfile
# ljwx-bigscreen Dockerfile
FROM python:3.12-slim

# 创建配置目录
RUN mkdir -p /app/config

# 复制应用代码
COPY . /app
WORKDIR /app

# 安装依赖
RUN pip install -r requirements.txt

# 复制配置加载器
COPY client/config/config_loader.py /app/config/

# 启动应用
CMD ["python", "run.py"]
```

### 2. 在 docker-compose.yml 中挂载配置

```yaml
services:
  ljwx-bigscreen:
    image: ljwx-bigscreen:2.0.1
    volumes:
      - ./client/config/ljwx-config.json:/app/config/ljwx-config.json:ro
      - ./client/config/config_loader.py:/app/config/config_loader.py:ro
    environment:
      - SERVICE_NAME=ljwx-bigscreen
      - PYTHONPATH=/app:/app/config
```

## 配置热更新支持

### 1. Python中的配置热更新

```python
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloadHandler(FileSystemEventHandler):
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def on_modified(self, event):
        if event.src_path.endswith('ljwx-config.json'):
            print("配置文件已更新，重新加载...")
            self.config_loader.reload()

# 在应用启动时启用配置监控
def start_config_watcher(config_loader):
    event_handler = ConfigReloadHandler(config_loader)
    observer = Observer()
    observer.schedule(event_handler, '/app/config', recursive=False)
    observer.start()
    return observer
```

### 2. Java中的配置热更新

```java
@Component
public class ConfigReloadService {
    
    @Autowired
    private LJWXConfigLoader configLoader;
    
    @EventListener
    @Async
    public void handleConfigReload(ConfigReloadEvent event) {
        log.info("重新加载配置...");
        configLoader.reload();
        // 触发相关服务重新初始化
    }
    
    // 定期检查配置文件修改时间
    @Scheduled(fixedDelay = 30000)
    public void checkConfigFile() {
        // 检查配置文件是否修改
        // 如果修改，发布ConfigReloadEvent
    }
}
```

## 配置验证

### 1. Python配置验证

```python
def validate_config(config):
    """验证配置的完整性和正确性"""
    required_keys = [
        'database.mysql.host',
        'database.mysql.port', 
        'database.mysql.username',
        'database.mysql.password',
        'services.ljwx-bigscreen.port'
    ]
    
    for key in required_keys:
        if config.get(key) is None:
            raise ValueError(f"配置项 {key} 不能为空")
    
    # 端口范围验证
    port = config.get('services.ljwx-bigscreen.port')
    if not (1 <= port <= 65535):
        raise ValueError(f"端口 {port} 超出有效范围")
    
    return True
```

### 2. 启动时配置检查

```python
# 在应用启动时验证配置
try:
    config = get_config()
    validate_config(config)
    print("✅ 配置验证通过")
except Exception as e:
    print(f"❌ 配置验证失败: {e}")
    sys.exit(1)
```

通过以上集成示例，各服务可以无缝使用统一配置系统，同时保持向后兼容性。