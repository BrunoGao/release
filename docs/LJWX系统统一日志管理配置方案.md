# LJWX系统统一日志管理配置方案

## 1. 概述

### 1.1 项目背景
灵境万象健康管理系统包含多个微服务组件（ljwx-admin、ljwx-boot、ljwx-bigscreen），在Docker-Compose环境下运行。为了提高系统的可观测性、快速问题定位和运维效率，需要建立统一的日志管理体系。

### 1.2 目标
- **统一标准**: 建立一致的日志格式、级别和存储规范
- **高效检索**: 支持快速问题定位和日志查询
- **环境分离**: 开发、调试、生产环境的日志策略差异化
- **资源优化**: 合理的日志轮转和存储管理
- **监控集成**: 支持日志监控和告警

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ljwx-admin    │    │   ljwx-boot     │    │ ljwx-bigscreen  │
│   Vue3前端      │    │   Spring Boot   │    │   Python Flask │
│   Nginx日志     │    │   Logback配置   │    │   Python日志    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  本地文件存储   │    │  本地文件存储   │    │  本地文件存储   │
│  日志轮转管理   │    │  Logback轮转    │    │  Python轮转     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┼──────────────────────┘
                     │           │
                     ▼           ▼
          ┌─────────────────────────────┐
          │      统一日志收集层          │
          │   Docker Compose Logging   │
          │      Fluentd/Filebeat      │
          └─────────────────────────────┘
                     │
                     ▼
          ┌─────────────────────────────┐
          │       日志存储与分析        │
          │    ELK Stack (可选)        │
          │   Grafana Loki (可选)      │
          └─────────────────────────────┘
```

### 2.2 日志层级设计
- **应用层**: 各服务内部日志配置和输出
- **容器层**: Docker容器日志收集和管理
- **收集层**: 统一日志收集和预处理
- **存储层**: 集中化日志存储和索引
- **分析层**: 日志检索、监控和告警

## 3. 调试环境配置方案

### 3.1 目标特点
- **详细日志**: DEBUG级别，包含完整调试信息
- **实时输出**: 控制台和文件双输出
- **快速迭代**: 支持热重载和实时查看
- **开发友好**: 结构化日志便于开发调试

### 3.2 ljwx-boot (Spring Boot) 调试配置

#### 3.2.1 logback-spring-debug.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <!-- 调试环境日志配置 -->
    <property name="LOG_HOME" value="./logs/debug"/>
    <property name="APP_NAME" value="ljwx-boot"/>
    <property name="LOG_PATTERN" value="%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level [%logger{50}:%line] [%X{traceId:-}] - %msg%n"/>

    <!-- 控制台输出 - 调试环境彩色输出 -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} %highlight(%-5level) [%cyan(%thread)] %yellow(%logger{30}) [%X{traceId:-}] - %msg%n</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- DEBUG日志文件 -->
    <appender name="DEBUG_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_debug.log</file>
        <filter class="ch.qos.logback.classic.filter.LevelFilter">
            <level>DEBUG</level>
            <onMatch>ACCEPT</onMatch>
            <onMismatch>DENY</onMismatch>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_debug.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxFileSize>50MB</maxFileSize>
            <maxHistory>7</maxHistory>
            <totalSizeCap>1GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>${LOG_PATTERN}</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- INFO及以上级别日志 -->
    <appender name="INFO_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_info.log</file>
        <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
            <level>INFO</level>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_info.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>15</maxHistory>
            <totalSizeCap>3GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>${LOG_PATTERN}</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- 错误日志 -->
    <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_error.log</file>
        <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
            <level>ERROR</level>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_error.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxFileSize>50MB</maxFileSize>
            <maxHistory>30</maxHistory>
            <totalSizeCap>2GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>${LOG_PATTERN}</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- 特定包的日志级别配置 -->
    <logger name="com.ljwx" level="DEBUG"/>
    <logger name="org.springframework.web" level="DEBUG"/>
    <logger name="org.springframework.security" level="DEBUG"/>
    <logger name="org.mybatis" level="DEBUG"/>
    <logger name="jdbc.sqlonly" level="DEBUG"/>
    <logger name="jdbc.sqltiming" level="INFO"/>
    <logger name="jdbc.connection" level="WARN"/>

    <root level="DEBUG">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="DEBUG_FILE"/>
        <appender-ref ref="INFO_FILE"/>
        <appender-ref ref="ERROR_FILE"/>
    </root>
</configuration>
```

#### 3.2.2 application-debug.yml
```yaml
spring:
  profiles:
    active: debug
  application:
    name: ljwx-boot-admin

logging:
  config: classpath:logback-spring-debug.xml
  level:
    com.ljwx: DEBUG
    org.springframework.web: DEBUG
    org.springframework.security: DEBUG
    org.mybatis: DEBUG
    root: INFO

# MDC 追踪配置
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,loggers
  endpoint:
    loggers:
      enabled: true
```

### 3.3 ljwx-bigscreen (Python Flask) 调试配置

#### 3.3.1 debug_logging_config.py
```python
import logging
import logging.handlers
import os
from datetime import datetime
import json

def setup_debug_logging(app_name="ljwx-bigscreen"):
    """调试环境日志配置"""
    
    # 确保日志目录存在
    log_dir = "./logs/debug"
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建自定义格式器
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "message": record.getMessage(),
                "app_name": app_name
            }
            
            # 添加异常信息
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            # 添加追踪ID（如果存在）
            if hasattr(record, 'trace_id'):
                log_entry["trace_id"] = record.trace_id
                
            return json.dumps(log_entry, ensure_ascii=False)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] [%(funcName)s] - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # DEBUG文件处理器
    debug_file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_debug.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=7
    )
    debug_file_handler.setFormatter(StructuredFormatter())
    debug_file_handler.setLevel(logging.DEBUG)
    
    # INFO文件处理器
    info_file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_info.log",
        maxBytes=100*1024*1024,  # 100MB
        backupCount=15
    )
    info_file_handler.setFormatter(StructuredFormatter())
    info_file_handler.setLevel(logging.INFO)
    
    # ERROR文件处理器
    error_file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_error.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=30
    )
    error_file_handler.setFormatter(StructuredFormatter())
    error_file_handler.setLevel(logging.ERROR)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(debug_file_handler)
    root_logger.addHandler(info_file_handler)
    root_logger.addHandler(error_file_handler)
    
    # 设置第三方库日志级别
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return root_logger
```

### 3.4 ljwx-admin (Vue3/Nginx) 调试配置

#### 3.4.1 nginx-debug.conf
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 调试环境详细日志格式
    log_format debug_format '$remote_addr - $remote_user [$time_local] '
                            '"$request" $status $body_bytes_sent '
                            '"$http_referer" "$http_user_agent" '
                            'rt=$request_time uct="$upstream_connect_time" '
                            'uht="$upstream_header_time" urt="$upstream_response_time" '
                            'trace_id="$http_x_trace_id"';

    # 访问日志
    access_log /var/log/nginx/ljwx-admin-access-debug.log debug_format;
    
    # 错误日志 - 调试级别
    error_log /var/log/nginx/ljwx-admin-error-debug.log debug;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 100M;

    # Gzip配置
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {
        listen 80;
        server_name localhost;
        
        # 前端静态资源
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # 调试环境启用详细错误信息
            error_page 404 /index.html;
            
            # 开发环境禁用缓存
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }

        # API代理
        location /api/ {
            proxy_pass http://ljwx-boot:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 添加追踪ID
            proxy_set_header X-Trace-ID $request_id;
            
            # 调试环境较长的超时时间
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # 启用代理日志
            access_log /var/log/nginx/ljwx-admin-proxy-debug.log debug_format;
        }
        
        # 健康检查
        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
            access_log off;
        }
    }
}
```

## 4. 生产环境配置方案

### 4.1 目标特点
- **优化性能**: INFO级别，减少不必要日志输出
- **稳定性**: 可靠的日志轮转和清理机制
- **安全性**: 敏感信息脱敏和访问控制
- **可观测性**: 支持监控和告警集成

### 4.2 ljwx-boot (Spring Boot) 生产配置

#### 4.2.1 logback-spring-prod.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <!-- 生产环境日志配置 -->
    <property name="LOG_HOME" value="/app/logs"/>
    <property name="APP_NAME" value="ljwx-boot"/>
    <property name="LOG_PATTERN" value="%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%thread] [%logger{40}:%line] [%X{traceId:-}] - %msg%n"/>

    <!-- 异步输出配置 -->
    <appender name="ASYNC_INFO" class="ch.qos.logback.classic.AsyncAppender">
        <discardingThreshold>0</discardingThreshold>
        <queueSize>1024</queueSize>
        <includeCallerData>false</includeCallerData>
        <appender-ref ref="INFO_FILE"/>
    </appender>

    <appender name="ASYNC_ERROR" class="ch.qos.logback.classic.AsyncAppender">
        <discardingThreshold>0</discardingThreshold>
        <queueSize>256</queueSize>
        <includeCallerData>true</includeCallerData>
        <appender-ref ref="ERROR_FILE"/>
    </appender>

    <!-- INFO日志文件 -->
    <appender name="INFO_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_info.log</file>
        <filter class="ch.qos.logback.classic.filter.LevelFilter">
            <level>ERROR</level>
            <onMatch>DENY</onMatch>
            <onMismatch>ACCEPT</onMismatch>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_info.%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
            <maxFileSize>200MB</maxFileSize>
            <maxHistory>30</maxHistory>
            <totalSizeCap>10GB</totalSizeCap>
            <cleanHistoryOnStart>true</cleanHistoryOnStart>
        </rollingPolicy>
        <encoder>
            <pattern>${LOG_PATTERN}</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- ERROR日志文件 -->
    <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_error.log</file>
        <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
            <level>ERROR</level>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_error.%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>90</maxHistory>
            <totalSizeCap>5GB</totalSizeCap>
            <cleanHistoryOnStart>true</cleanHistoryOnStart>
        </rollingPolicy>
        <encoder>
            <pattern>${LOG_PATTERN}</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- 性能日志 -->
    <appender name="PERF_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_performance.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_performance.%d{yyyy-MM-dd}.log.gz</fileNamePattern>
            <maxHistory>7</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{traceId:-}] - %msg%n</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- 审计日志 -->
    <appender name="AUDIT_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_HOME}/${APP_NAME}_audit.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_HOME}/${APP_NAME}_audit.%d{yyyy-MM-dd}.log.gz</fileNamePattern>
            <maxHistory>365</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{userId:-}] [%X{action:-}] - %msg%n</pattern>
            <charset>UTF-8</charset>
        </encoder>
    </appender>

    <!-- 特定日志记录器 -->
    <logger name="PERFORMANCE" level="INFO" additivity="false">
        <appender-ref ref="PERF_FILE"/>
    </logger>

    <logger name="AUDIT" level="INFO" additivity="false">
        <appender-ref ref="AUDIT_FILE"/>
    </logger>

    <!-- 第三方库日志级别 -->
    <logger name="org.springframework" level="WARN"/>
    <logger name="org.mybatis" level="WARN"/>
    <logger name="org.apache.ibatis" level="WARN"/>
    <logger name="com.zaxxer.hikari" level="WARN"/>
    <logger name="io.lettuce.core.protocol" level="WARN"/>

    <root level="INFO">
        <appender-ref ref="ASYNC_INFO"/>
        <appender-ref ref="ASYNC_ERROR"/>
    </root>
</configuration>
```

### 4.3 ljwx-bigscreen (Python Flask) 生产配置

#### 4.3.1 prod_logging_config.py
```python
import logging
import logging.handlers
import os
import json
from datetime import datetime
import threading
import queue
import time

class AsyncHandler(logging.Handler):
    """异步日志处理器"""
    
    def __init__(self, target_handler):
        super().__init__()
        self.target_handler = target_handler
        self.queue = queue.Queue(maxsize=1000)
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.shutdown = False
    
    def emit(self, record):
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # 队列满时丢弃最旧的记录
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def _worker(self):
        while not self.shutdown:
            try:
                record = self.queue.get(timeout=1)
                self.target_handler.emit(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass
    
    def close(self):
        self.shutdown = True
        self.thread.join(timeout=5)
        self.target_handler.close()
        super().close()

def setup_production_logging(app_name="ljwx-bigscreen"):
    """生产环境日志配置"""
    
    # 确保日志目录存在
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    class ProductionFormatter(logging.Formatter):
        """生产环境格式器 - 结构化JSON输出"""
        
        def format(self, record):
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "message": self.sanitize_message(record.getMessage()),
                "app_name": app_name,
                "thread_id": record.thread,
                "process_id": record.process
            }
            
            # 添加异常信息
            if record.exc_info:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info)
                }
            
            # 添加追踪信息
            if hasattr(record, 'trace_id'):
                log_entry["trace_id"] = record.trace_id
            if hasattr(record, 'user_id'):
                log_entry["user_id"] = record.user_id
                
            return json.dumps(log_entry, ensure_ascii=False)
        
        def sanitize_message(self, message):
            """敏感信息脱敏"""
            import re
            # 脱敏手机号
            message = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', message)
            # 脱敏身份证号
            message = re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', message)
            # 脱敏密码相关
            message = re.sub(r'(password["\']?\s*[:=]\s*["\']?)\w+', r'\1***', message, flags=re.IGNORECASE)
            return message
    
    # INFO日志处理器
    info_file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_info.log",
        maxBytes=200*1024*1024,  # 200MB
        backupCount=30
    )
    info_file_handler.setFormatter(ProductionFormatter())
    info_file_handler.setLevel(logging.INFO)
    info_filter = logging.Filter()
    info_filter.filter = lambda record: record.levelno < logging.ERROR
    info_file_handler.addFilter(info_filter)
    
    # ERROR日志处理器
    error_file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/{app_name}_error.log",
        maxBytes=100*1024*1024,  # 100MB
        backupCount=90
    )
    error_file_handler.setFormatter(ProductionFormatter())
    error_file_handler.setLevel(logging.ERROR)
    
    # 性能日志处理器
    perf_file_handler = logging.handlers.TimedRotatingFileHandler(
        f"{log_dir}/{app_name}_performance.log",
        when='D',
        interval=1,
        backupCount=7
    )
    perf_file_handler.setFormatter(ProductionFormatter())
    perf_file_handler.setLevel(logging.INFO)
    
    # 审计日志处理器
    audit_file_handler = logging.handlers.TimedRotatingFileHandler(
        f"{log_dir}/{app_name}_audit.log",
        when='D',
        interval=1,
        backupCount=365
    )
    audit_file_handler.setFormatter(ProductionFormatter())
    audit_file_handler.setLevel(logging.INFO)
    
    # 配置异步处理器
    async_info_handler = AsyncHandler(info_file_handler)
    async_error_handler = AsyncHandler(error_file_handler)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加异步处理器
    root_logger.addHandler(async_info_handler)
    root_logger.addHandler(async_error_handler)
    
    # 配置特定日志记录器
    perf_logger = logging.getLogger('PERFORMANCE')
    perf_logger.setLevel(logging.INFO)
    perf_logger.addHandler(perf_file_handler)
    perf_logger.propagate = False
    
    audit_logger = logging.getLogger('AUDIT')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_file_handler)
    audit_logger.propagate = False
    
    # 第三方库日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return root_logger
```

### 4.4 ljwx-admin (Nginx) 生产配置

#### 4.4.1 nginx-prod.conf
```nginx
user nginx;
worker_processes auto;
worker_cpu_affinity auto;
worker_rlimit_nofile 65535;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    use epoll;
    worker_connections 4096;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 生产环境日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    # JSON格式日志用于日志收集
    log_format json escape=json '{'
        '"timestamp":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"remote_user":"$remote_user",'
        '"request":"$request",'
        '"status":"$status",'
        '"body_bytes_sent":"$body_bytes_sent",'
        '"http_referer":"$http_referer",'
        '"http_user_agent":"$http_user_agent",'
        '"http_x_forwarded_for":"$http_x_forwarded_for",'
        '"request_time":"$request_time",'
        '"upstream_connect_time":"$upstream_connect_time",'
        '"upstream_header_time":"$upstream_header_time",'
        '"upstream_response_time":"$upstream_response_time",'
        '"app_name":"ljwx-admin"'
        '}';

    # 访问日志
    access_log /var/log/nginx/ljwx-admin-access.log json buffer=32k flush=5s;
    
    # 错误日志
    error_log /var/log/nginx/ljwx-admin-error.log warn;

    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    client_header_buffer_size 4k;
    large_client_header_buffers 8 8k;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # 缓存配置
    open_file_cache max=10000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/s;

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html index.htm;

        # 安全头
        add_header X-Frame-Options SAMEORIGIN always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # 前端页面
        location / {
            try_files $uri $uri/ /index.html;
            
            # HTML文件不缓存
            location ~* \.html$ {
                add_header Cache-Control "no-cache, no-store, must-revalidate";
                add_header Pragma "no-cache";
                add_header Expires "0";
            }
        }

        # API代理
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://ljwx-boot:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 生产环境超时配置
            proxy_connect_timeout 10s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
            
            # 缓冲区配置
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            
            # 代理日志
            access_log /var/log/nginx/ljwx-admin-api.log json;
        }

        # 登录接口限流
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://ljwx-boot:8080/auth/login;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # 健康检查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # 错误页面
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

## 5. Docker-Compose日志配置

### 5.1 统一日志驱动配置

#### 5.1.1 docker-compose-logging.yml
```yaml
version: '3.8'

# 网络配置
networks:
  ljwx-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# 卷配置
volumes:
  ljwx-logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./logs
  mysql-data:
    driver: local
  redis-data:
    driver: local

# 服务配置
services:
  # MySQL数据库
  mysql:
    image: mysql:8.0
    container_name: ljwx-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: 123456
      MYSQL_DATABASE: test
    volumes:
      - mysql-data:/var/lib/mysql
      - ljwx-logs:/var/log/mysql
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=mysql,app=ljwx"

  # Redis缓存
  redis:
    image: redis:8-alpine
    container_name: ljwx-redis
    restart: unless-stopped
    command: redis-server --requirepass 123456 --appendonly yes
    volumes:
      - redis-data:/data
      - ljwx-logs:/var/log/redis
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
        labels: "service=redis,app=ljwx"

  # 后端服务
  ljwx-boot:
    image: ljwx-boot:latest
    container_name: ljwx-boot
    restart: unless-stopped
    environment:
      - SPRING_PROFILES_ACTIVE=${ENV:-prod}
      - MYSQL_HOST=mysql
      - MYSQL_DATABASE=test
      - MYSQL_USER=root
      - MYSQL_PASSWORD=123456
      - REDIS_HOST=redis
      - REDIS_PASSWORD=123456
      - JVM_OPTS=-Xmx2g -Xms1g
    volumes:
      - ljwx-logs:/app/logs
    depends_on:
      - mysql
      - redis
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "200m"
        max-file: "10"
        labels: "service=ljwx-boot,app=ljwx,env=${ENV:-prod}"
        tag: "ljwx-boot"

  # 前端服务
  ljwx-admin:
    image: ljwx-admin:latest
    container_name: ljwx-admin
    restart: unless-stopped
    ports:
      - "3333:80"
    volumes:
      - ljwx-logs:/var/log/nginx
    depends_on:
      - ljwx-boot
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "7"
        labels: "service=ljwx-admin,app=ljwx,env=${ENV:-prod}"
        tag: "ljwx-admin"

  # 告警服务
  ljwx-bigscreen:
    image: ljwx-bigscreen:latest
    container_name: ljwx-bigscreen
    restart: unless-stopped
    environment:
      - FLASK_ENV=${ENV:-production}
      - MYSQL_HOST=mysql
      - MYSQL_DATABASE=test
      - MYSQL_USER=root
      - MYSQL_PASSWORD=123456
      - REDIS_HOST=redis
      - REDIS_PASSWORD=123456
      - IS_DOCKER=true
    volumes:
      - ljwx-logs:/app/logs
    depends_on:
      - mysql
      - redis
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "150m"
        max-file: "8"
        labels: "service=ljwx-bigscreen,app=ljwx,env=${ENV:-prod}"
        tag: "ljwx-bigscreen"

  # 日志收集器 (可选)
  fluentd:
    image: fluentd:v1.16
    container_name: ljwx-fluentd
    restart: unless-stopped
    volumes:
      - ./fluentd/conf:/fluentd/etc
      - ljwx-logs:/var/log/ljwx:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
        labels: "service=fluentd,app=ljwx"
    profiles:
      - logging

  # 日志可视化 (可选)
  grafana:
    image: grafana/grafana:latest
    container_name: ljwx-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - ./grafana/data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - ljwx-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
    profiles:
      - monitoring
```

### 5.2 环境特定配置

#### 5.2.1 .env.debug
```bash
# 调试环境配置
ENV=debug
COMPOSE_PROJECT_NAME=ljwx-debug
LOGGING_LEVEL=DEBUG

# 数据库配置
MYSQL_ROOT_PASSWORD=123456
MYSQL_DATABASE=test

# Redis配置
REDIS_PASSWORD=123456

# 日志配置
LOG_MAX_SIZE=100m
LOG_MAX_FILES=5
LOG_DRIVER=json-file
```

#### 5.2.2 .env.prod
```bash
# 生产环境配置
ENV=prod
COMPOSE_PROJECT_NAME=ljwx-prod
LOGGING_LEVEL=INFO

# 数据库配置
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_DATABASE=ljwx_prod

# Redis配置
REDIS_PASSWORD=${REDIS_PASSWORD}

# 日志配置
LOG_MAX_SIZE=200m
LOG_MAX_FILES=10
LOG_DRIVER=json-file

# 监控配置
ENABLE_MONITORING=true
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
```

## 6. 日志管理工具脚本

### 6.1 日志查看脚本

#### 6.1.1 log-viewer.sh
```bash
#!/bin/bash

# LJWX系统日志查看工具
# 使用方法: ./log-viewer.sh [service] [level] [lines]

set -e

# 默认参数
SERVICE=${1:-"all"}
LEVEL=${2:-"INFO"}
LINES=${3:-"100"}
LOG_DIR="./logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印帮助信息
show_help() {
    echo -e "${GREEN}LJWX系统日志查看工具${NC}"
    echo ""
    echo "使用方法: $0 [service] [level] [lines]"
    echo ""
    echo "参数说明:"
    echo "  service: 服务名称 (ljwx-boot|ljwx-admin|ljwx-bigscreen|all)"
    echo "  level:   日志级别 (DEBUG|INFO|WARN|ERROR|all)"
    echo "  lines:   显示行数 (默认100)"
    echo ""
    echo "示例:"
    echo "  $0 ljwx-boot ERROR 50    # 查看ljwx-boot的ERROR级别日志，最近50行"
    echo "  $0 all INFO 200          # 查看所有服务的INFO级别日志，最近200行"
    echo "  $0 ljwx-bigscreen        # 查看ljwx-bigscreen的INFO级别日志，最近100行"
}

# 格式化JSON日志
format_json_log() {
    local log_file=$1
    local level_filter=$2
    
    if command -v jq &> /dev/null; then
        if [ "$level_filter" = "all" ]; then
            tail -n "$LINES" "$log_file" | grep -E "^{.*}$" | jq -r '
                "\(.timestamp // .time) [\(.level)] [\(.logger // .module)] - \(.message)"
            ' 2>/dev/null || tail -n "$LINES" "$log_file"
        else
            tail -n "$LINES" "$log_file" | grep -E "^{.*}$" | jq -r --arg level "$level_filter" '
                select(.level == $level) |
                "\(.timestamp // .time) [\(.level)] [\(.logger // .module)] - \(.message)"
            ' 2>/dev/null || tail -n "$LINES" "$log_file"
        fi
    else
        # 无jq时的简单处理
        if [ "$level_filter" = "all" ]; then
            tail -n "$LINES" "$log_file"
        else
            tail -n "$LINES" "$log_file" | grep "$level_filter"
        fi
    fi
}

# 查看指定服务日志
view_service_log() {
    local service=$1
    local level=$2
    
    echo -e "${BLUE}=== $service 日志 (级别: $level) ===${NC}"
    
    # 查找日志文件
    local debug_log="$LOG_DIR/debug/${service}_debug.log"
    local info_log="$LOG_DIR/${service}_info.log"
    local error_log="$LOG_DIR/${service}_error.log"
    
    # 根据环境和级别选择日志文件
    case $level in
        "DEBUG")
            if [ -f "$debug_log" ]; then
                format_json_log "$debug_log" "DEBUG"
            elif [ -f "$info_log" ]; then
                format_json_log "$info_log" "DEBUG"
            else
                echo -e "${YELLOW}未找到$service的DEBUG日志文件${NC}"
            fi
            ;;
        "INFO")
            if [ -f "$info_log" ]; then
                format_json_log "$info_log" "INFO"
            else
                echo -e "${YELLOW}未找到$service的INFO日志文件${NC}"
            fi
            ;;
        "ERROR")
            if [ -f "$error_log" ]; then
                format_json_log "$error_log" "ERROR"
            elif [ -f "$info_log" ]; then
                format_json_log "$info_log" "ERROR"
            else
                echo -e "${YELLOW}未找到$service的ERROR日志文件${NC}"
            fi
            ;;
        "all")
            for log_file in "$debug_log" "$info_log" "$error_log"; do
                if [ -f "$log_file" ]; then
                    echo -e "${GREEN}--- $(basename $log_file) ---${NC}"
                    format_json_log "$log_file" "all"
                    echo ""
                fi
            done
            ;;
    esac
}

# 主逻辑
case $1 in
    "-h"|"--help"|"help")
        show_help
        exit 0
        ;;
esac

# 检查日志目录
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}错误: 日志目录 $LOG_DIR 不存在${NC}"
    exit 1
fi

echo -e "${GREEN}LJWX系统日志查看工具${NC}"
echo -e "服务: ${YELLOW}$SERVICE${NC}, 级别: ${YELLOW}$LEVEL${NC}, 行数: ${YELLOW}$LINES${NC}"
echo ""

case $SERVICE in
    "ljwx-boot"|"ljwx-admin"|"ljwx-bigscreen")
        view_service_log "$SERVICE" "$LEVEL"
        ;;
    "all")
        for service in ljwx-boot ljwx-admin ljwx-bigscreen; do
            view_service_log "$service" "$LEVEL"
            echo ""
        done
        ;;
    *)
        echo -e "${RED}错误: 不支持的服务名称 '$SERVICE'${NC}"
        echo "支持的服务: ljwx-boot, ljwx-admin, ljwx-bigscreen, all"
        exit 1
        ;;
esac
```

### 6.2 日志清理脚本

#### 6.2.1 log-cleanup.sh
```bash
#!/bin/bash

# LJWX系统日志清理工具
# 使用方法: ./log-cleanup.sh [days] [--dry-run]

set -e

# 默认参数
DAYS=${1:-30}
DRY_RUN=false
LOG_DIR="./logs"

# 检查参数
if [[ "$2" == "--dry-run" ]] || [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    if [[ "$1" == "--dry-run" ]]; then
        DAYS=30
    fi
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}LJWX系统日志清理工具${NC}"
echo -e "清理 ${YELLOW}$DAYS${NC} 天前的日志文件"
if $DRY_RUN; then
    echo -e "${YELLOW}[DRY RUN 模式] 仅显示将要删除的文件，不会实际删除${NC}"
fi
echo ""

# 检查日志目录
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}错误: 日志目录 $LOG_DIR 不存在${NC}"
    exit 1
fi

# 清理函数
cleanup_logs() {
    local target_dir=$1
    local pattern=$2
    local description=$3
    
    if [ ! -d "$target_dir" ]; then
        return
    fi
    
    echo -e "${BLUE}清理 $description${NC}"
    
    local files_found=0
    local total_size=0
    
    while IFS= read -r -d '' file; do
        if [ -f "$file" ]; then
            files_found=$((files_found + 1))
            local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
            total_size=$((total_size + file_size))
            
            if $DRY_RUN; then
                echo "  [DRY RUN] 将删除: $file ($(numfmt --to=iec-i --suffix=B $file_size))"
            else
                echo "  删除: $file ($(numfmt --to=iec-i --suffix=B $file_size))"
                rm -f "$file"
            fi
        fi
    done < <(find "$target_dir" -name "$pattern" -type f -mtime +$DAYS -print0 2>/dev/null)
    
    if [ $files_found -eq 0 ]; then
        echo -e "  ${GREEN}没有找到需要清理的文件${NC}"
    else
        echo -e "  ${GREEN}找到 $files_found 个文件，总计 $(numfmt --to=iec-i --suffix=B $total_size)${NC}"
    fi
    echo ""
}

# 清理各种类型的日志文件
cleanup_logs "$LOG_DIR" "*.log.*" "轮转的日志文件 (*.log.*)"
cleanup_logs "$LOG_DIR" "*.gz" "压缩的日志文件 (*.gz)"
cleanup_logs "$LOG_DIR/debug" "*.log.*" "调试环境轮转日志"
cleanup_logs "/var/log/nginx" "*ljwx*.log.*" "Nginx轮转日志"

# 清理Docker容器日志
echo -e "${BLUE}检查Docker容器日志大小${NC}"
if command -v docker &> /dev/null; then
    for container in ljwx-boot ljwx-admin ljwx-bigscreen ljwx-mysql ljwx-redis; do
        if docker ps -a --format "table {{.Names}}" | grep -q "^$container$"; then
            local log_path=$(docker inspect --format='{{.LogPath}}' "$container" 2>/dev/null || echo "")
            if [ -n "$log_path" ] && [ -f "$log_path" ]; then
                local log_size=$(stat -f%z "$log_path" 2>/dev/null || stat -c%s "$log_path" 2>/dev/null || echo 0)
                if [ $log_size -gt $((100*1024*1024)) ]; then # 大于100MB
                    echo -e "  ${YELLOW}警告: $container 容器日志较大 ($(numfmt --to=iec-i --suffix=B $log_size))${NC}"
                    echo -e "  ${YELLOW}建议使用: docker logs $container --tail 1000 > backup.log && echo \"\" > \$(docker inspect --format='{{.LogPath}}' $container)${NC}"
                else
                    echo -e "  ${GREEN}$container 容器日志大小正常 ($(numfmt --to=iec-i --suffix=B $log_size))${NC}"
                fi
            fi
        fi
    done
else
    echo -e "  ${YELLOW}Docker未安装或不可用，跳过容器日志检查${NC}"
fi
echo ""

# 显示磁盘空间
echo -e "${BLUE}磁盘空间使用情况${NC}"
df -h "$LOG_DIR" 2>/dev/null || df -h .
echo ""

# 给出建议
echo -e "${GREEN}日志清理完成!${NC}"
if $DRY_RUN; then
    echo -e "${YELLOW}提示: 这是dry-run模式，没有实际删除文件${NC}"
    echo -e "${YELLOW}要实际执行清理，请运行: $0 $DAYS${NC}"
else
    echo -e "${GREEN}建议: 可以将此脚本加入cron任务定期执行${NC}"
    echo -e "示例cron配置: ${YELLOW}0 2 * * 0 /path/to/log-cleanup.sh 30${NC}"
fi
```

### 6.3 日志监控脚本

#### 6.3.1 log-monitor.sh
```bash
#!/bin/bash

# LJWX系统日志监控工具
# 使用方法: ./log-monitor.sh [--alert-webhook=URL] [--check-interval=60]

set -e

# 默认参数
CHECK_INTERVAL=60
ALERT_WEBHOOK=""
LOG_DIR="./logs"
ERROR_THRESHOLD=10  # 错误数量阈值
DISK_THRESHOLD=80   # 磁盘使用率阈值(%)

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --alert-webhook=*)
            ALERT_WEBHOOK="${1#*=}"
            shift
            ;;
        --check-interval=*)
            CHECK_INTERVAL="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "LJWX系统日志监控工具"
            echo "用法: $0 [--alert-webhook=URL] [--check-interval=60]"
            echo "参数:"
            echo "  --alert-webhook=URL    告警webhook URL"
            echo "  --check-interval=SEC   检查间隔(秒，默认60)"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 发送告警
send_alert() {
    local title="$1"
    local message="$2"
    local level="$3"
    
    echo -e "${RED}[ALERT] $title: $message${NC}"
    
    if [ -n "$ALERT_WEBHOOK" ]; then
        local payload=$(cat <<EOF
{
    "title": "$title",
    "message": "$message",
    "level": "$level",
    "timestamp": "$(date -Iseconds)",
    "system": "LJWX"
}
EOF
)
        
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "$payload" > /dev/null 2>&1 || true
    fi
}

# 检查错误日志
check_error_logs() {
    local service=$1
    local log_file="$LOG_DIR/${service}_error.log"
    
    if [ ! -f "$log_file" ]; then
        return
    fi
    
    # 检查最近5分钟的错误
    local recent_errors=$(find "$log_file" -newermt "5 minutes ago" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
    
    if [ "$recent_errors" -gt "$ERROR_THRESHOLD" ]; then
        local latest_error=$(tail -1 "$log_file" 2>/dev/null || echo "无法读取错误信息")
        send_alert "服务错误过多" "$service 在最近5分钟内产生了 $recent_errors 个错误。最新错误: $latest_error" "HIGH"
    fi
}

# 检查日志文件大小
check_log_sizes() {
    local max_size=$((500*1024*1024))  # 500MB
    
    find "$LOG_DIR" -name "*.log" -size +${max_size}c 2>/dev/null | while read -r log_file; do
        local file_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo 0)
        local size_mb=$((file_size / 1024 / 1024))
        send_alert "日志文件过大" "$(basename $log_file) 大小为 ${size_mb}MB，超过500MB阈值" "MEDIUM"
    done
}

# 检查磁盘空间
check_disk_space() {
    local usage=$(df "$LOG_DIR" 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo 0)
    
    if [ "$usage" -gt "$DISK_THRESHOLD" ]; then
        send_alert "磁盘空间不足" "日志目录磁盘使用率为 ${usage}%，超过 ${DISK_THRESHOLD}% 阈值" "HIGH"
    fi
}

# 检查服务健康状态
check_service_health() {
    # 检查Docker容器状态
    if command -v docker &> /dev/null; then
        for container in ljwx-boot ljwx-admin ljwx-bigscreen; do
            if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "^$container.*Up"; then
                local status=$(docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep "^$container" | awk '{print $2}' || echo "未知")
                send_alert "服务状态异常" "$container 容器状态: $status" "HIGH"
            fi
        done
    fi
}

# 分析日志模式
analyze_log_patterns() {
    # 检查异常模式
    local patterns=(
        "OutOfMemoryError"
        "Connection timeout"
        "Database connection failed"
        "Redis connection failed"
        "HTTP 50[0-9]"
        "Exception.*Exception"
    )
    
    for service in ljwx-boot ljwx-admin ljwx-bigscreen; do
        local info_log="$LOG_DIR/${service}_info.log"
        local error_log="$LOG_DIR/${service}_error.log"
        
        for log_file in "$info_log" "$error_log"; do
            if [ ! -f "$log_file" ]; then
                continue
            fi
            
            for pattern in "${patterns[@]}"; do
                # 检查最近1小时内的日志
                local count=$(tail -n 1000 "$log_file" 2>/dev/null | grep -E "$(date '+%Y-%m-%d %H:' --date='1 hour ago')" | grep -c "$pattern" 2>/dev/null || echo 0)
                
                if [ "$count" -gt 5 ]; then
                    send_alert "异常模式检测" "$service 在最近1小时内出现 '$pattern' 模式 $count 次" "MEDIUM"
                fi
            done
        done
    done
}

# 生成监控报告
generate_report() {
    local report_file="/tmp/ljwx_log_monitor_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "LJWX系统日志监控报告"
        echo "生成时间: $(date)"
        echo "===================="
        echo ""
        
        echo "1. 磁盘使用情况:"
        df -h "$LOG_DIR" 2>/dev/null || df -h .
        echo ""
        
        echo "2. 日志文件大小:"
        find "$LOG_DIR" -name "*.log" -exec ls -lh {} \; 2>/dev/null | head -10
        echo ""
        
        echo "3. 最近错误统计:"
        for service in ljwx-boot ljwx-admin ljwx-bigscreen; do
            local error_log="$LOG_DIR/${service}_error.log"
            if [ -f "$error_log" ]; then
                local error_count=$(wc -l < "$error_log" 2>/dev/null || echo 0)
                echo "  $service: $error_count 个错误"
            fi
        done
        echo ""
        
        echo "4. 服务状态:"
        if command -v docker &> /dev/null; then
            docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(ljwx-|NAMES)" || echo "  无Docker服务信息"
        else
            echo "  Docker不可用"
        fi
        
    } > "$report_file"
    
    echo "$report_file"
}

# 主监控循环
main_monitor() {
    echo -e "${GREEN}LJWX日志监控启动${NC}"
    echo -e "检查间隔: ${YELLOW}${CHECK_INTERVAL}秒${NC}"
    echo -e "告警webhook: ${YELLOW}${ALERT_WEBHOOK:-"未配置"}${NC}"
    echo -e "日志目录: ${YELLOW}$LOG_DIR${NC}"
    echo ""
    
    while true; do
        local check_time=$(date '+%Y-%m-%d %H:%M:%S')
        echo -e "${BLUE}[$check_time] 执行监控检查...${NC}"
        
        # 执行各项检查
        for service in ljwx-boot ljwx-admin ljwx-bigscreen; do
            check_error_logs "$service"
        done
        
        check_log_sizes
        check_disk_space
        check_service_health
        analyze_log_patterns
        
        echo -e "${GREEN}监控检查完成${NC}"
        
        # 等待下次检查
        sleep "$CHECK_INTERVAL"
    done
}

# 检查日志目录
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}错误: 日志目录 $LOG_DIR 不存在${NC}"
    exit 1
fi

# 启动监控
trap 'echo -e "\n${YELLOW}监控已停止${NC}"; exit 0' INT TERM
main_monitor
```

## 7. 运维操作指南

### 7.1 日志查看常用命令

#### 实时查看日志
```bash
# 实时查看所有服务日志
docker-compose logs -f

# 实时查看指定服务日志
docker-compose logs -f ljwx-boot

# 查看最近100行日志
docker-compose logs --tail=100 ljwx-boot

# 查看特定时间段日志
docker-compose logs --since="2024-01-01T10:00:00" ljwx-boot
```

#### 使用自定义工具
```bash
# 查看所有服务的ERROR级别日志
./log-viewer.sh all ERROR 50

# 查看ljwx-bigscreen的最近200行日志
./log-viewer.sh ljwx-bigscreen INFO 200

# 清理30天前的日志
./log-cleanup.sh 30

# 启动日志监控
./log-monitor.sh --alert-webhook=http://your-webhook-url --check-interval=30
```

### 7.2 问题定位流程

#### 7.2.1 服务无响应
1. 查看容器状态: `docker ps -a`
2. 查看服务日志: `docker-compose logs ljwx-boot`
3. 检查资源使用: `docker stats`
4. 查看错误日志: `./log-viewer.sh ljwx-boot ERROR 100`

#### 7.2.2 性能问题
1. 查看性能日志: `tail -f logs/ljwx-boot_performance.log`
2. 监控数据库连接: `grep "connection" logs/ljwx-boot_info.log`
3. 检查内存使用: `docker stats ljwx-boot`

#### 7.2.3 告警异常
1. 查看告警服务日志: `./log-viewer.sh ljwx-bigscreen ERROR`
2. 检查Redis连接: `docker logs ljwx-redis`
3. 验证微信配置: `grep "wechat" logs/ljwx-bigscreen_error.log`

### 7.3 维护建议

#### 7.3.1 定期维护任务
```bash
# 添加到cron任务
# 每天凌晨2点清理30天前的日志
0 2 * * * /path/to/log-cleanup.sh 30

# 每小时检查日志状态
0 * * * * /path/to/log-monitor.sh --check-interval=3600 --alert-webhook=http://your-webhook-url

# 每周生成日志报告
0 0 * * 0 /path/to/generate-weekly-report.sh
```

#### 7.3.2 监控指标
- **日志错误率**: ERROR日志占总日志的比例 < 1%
- **日志文件大小**: 单个文件 < 500MB
- **磁盘使用率**: 日志目录使用率 < 80%
- **响应时间**: API响应时间 < 2s
- **告警延迟**: 告警处理延迟 < 30s

## 8. 总结

### 8.1 方案优势
1. **统一标准**: 建立了一致的日志格式和管理规范
2. **环境适配**: 针对调试和生产环境的差异化配置
3. **高效检索**: 结构化日志和完善的查看工具
4. **自动化**: 日志轮转、清理和监控的自动化
5. **可扩展**: 支持集成ELK Stack等外部日志系统

### 8.2 实施建议
1. **分阶段实施**: 先实施基础日志配置，再逐步完善监控和告警
2. **测试验证**: 在调试环境充分测试后再部署到生产环境
3. **团队培训**: 确保运维团队掌握日志查看和问题定位技能
4. **持续优化**: 根据实际使用情况持续优化日志策略

### 8.3 扩展规划
1. **集中化日志**: 集成ELK Stack或Grafana Loki
2. **智能告警**: 基于机器学习的异常检测
3. **可视化展示**: Grafana仪表板和实时监控
4. **审计合规**: 满足安全审计和合规要求

---

*文档版本: v1.0*  
*创建时间: 2025-08-31*  
*维护人员: LJWX开发团队*