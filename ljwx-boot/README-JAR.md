# ljwx-boot JAR方式运行指南

## 概述

本指南提供了ljwx-boot以JAR包形式在宿主机上运行的配置和使用方法，直接连接宿主机的MySQL和Redis服务，适合生产环境部署和本地开发。

## 环境要求

### 必需环境
- **Java**: 17+ (推荐 21)
- **MySQL**: 8.0+ (宿主机安装)
- **Redis**: 6.0+ (宿主机安装)

### 可选环境
- **Maven**: 3.8+ (用于编译)
- **MySQL客户端**: 用于数据库管理
- **Redis客户端**: 用于Redis管理

## 快速开始

### 1. 准备宿主机服务

```bash
# 检查服务状态
./host-services.sh check

# 启动MySQL和Redis服务
./host-services.sh start

# 测试服务连接
./host-services.sh test
```

### 2. 运行JAR应用

```bash
# 使用默认配置运行
./run-jar.sh

# 使用自定义配置运行
./run-jar.sh my-config.env
```

## 宿主机服务管理

### 安装MySQL和Redis

#### macOS (使用Homebrew)
```bash
# 安装Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装MySQL和Redis
brew install mysql redis

# 启动服务
brew services start mysql
brew services start redis
```

#### Ubuntu/Debian
```bash
# 更新包列表
sudo apt-get update

# 安装MySQL和Redis
sudo apt-get install -y mysql-server redis-server

# 启动服务
sudo systemctl start mysql
sudo systemctl start redis-server

# 设置开机自启
sudo systemctl enable mysql
sudo systemctl enable redis-server
```

#### CentOS/RHEL
```bash
# 安装MySQL和Redis
sudo yum install -y mysql-server redis

# 启动服务
sudo systemctl start mysqld
sudo systemctl start redis

# 设置开机自启
sudo systemctl enable mysqld
sudo systemctl enable redis
```

### 服务管理命令

```bash
# 检查服务状态
./host-services.sh check

# 启动所有服务
./host-services.sh start

# 停止所有服务
./host-services.sh stop

# 重启所有服务
./host-services.sh restart

# 显示详细状态
./host-services.sh status

# 测试连接
./host-services.sh test

# 安装服务 (自动检测操作系统)
./host-services.sh install
```

## 配置说明

### 宿主机配置文件 (host-config.env)

```bash
# Spring配置
export SPRING_PROFILES_ACTIVE=host

# MySQL配置 - 宿主机MySQL
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=lj-06

# Redis配置 - 宿主机Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=         # 通常无密码
export REDIS_DB=0

# 服务端口配置
export SERVER_PORT=9998
export MANAGEMENT_PORT=9999

# 日志配置
export LOG_LEVEL=info
export LOG_FILE=logs/ljwx-boot-host.log

# OSS配置
export OSS_NAME=local
export OSS_LOCAL_PATH=./data/uploads

# AI服务配置（可选）
export OLLAMA_ENABLED=false
export OLLAMA_BASE_URL=http://localhost:11434

# JVM参数优化
export JAVA_OPTS="-Xmx2g -Xms1g -XX:MetaspaceSize=256m -XX:+UseG1GC"
```

### application-host.yml 配置特点

- **数据库连接**: 直连宿主机MySQL (localhost:3306)
- **Redis连接**: 直连宿主机Redis (localhost:6379)
- **日志级别**: 生产级别 (INFO)
- **连接池**: 适合生产环境的连接数配置
- **监控**: 基础监控端点
- **定时任务**: 使用数据库存储

## 数据库配置

### MySQL配置建议

#### 创建数据库和用户
```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS `lj-06` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'ljwx'@'localhost' IDENTIFIED BY 'ljwx123456';

-- 授权
GRANT ALL PRIVILEGES ON `lj-06`.* TO 'ljwx'@'localhost';
FLUSH PRIVILEGES;
```

#### MySQL配置文件优化
```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf (Ubuntu)
# /etc/my.cnf (CentOS)
# /usr/local/etc/my.cnf (macOS Homebrew)

[mysqld]
# 基础配置
port = 3306
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
default-time-zone = '+08:00'

# 连接配置
max_connections = 200
wait_timeout = 28800
interactive_timeout = 28800

# 缓存配置
innodb_buffer_pool_size = 1G
key_buffer_size = 256M
query_cache_size = 64M

# 日志配置
slow_query_log = 1
long_query_time = 2
log_error = /var/log/mysql/error.log
```

### Redis配置建议

#### Redis配置文件优化
```ini
# /etc/redis/redis.conf (Linux)
# /usr/local/etc/redis.conf (macOS Homebrew)

# 基础配置
port 6379
bind 127.0.0.1
protected-mode yes

# 内存配置
maxmemory 512mb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000
rdbcompression yes

# 日志配置
loglevel notice
logfile /var/log/redis/redis-server.log
```

## 性能优化

### JVM参数优化

```bash
# 生产环境推荐配置
export JAVA_OPTS="-Xmx4g -Xms2g -XX:MetaspaceSize=512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+DisableExplicitGC -XX:+UseStringDeduplication"

# 开发环境配置
export JAVA_OPTS="-Xmx2g -Xms1g -XX:MetaspaceSize=256m -XX:+UseG1GC"

# 内存受限环境配置
export JAVA_OPTS="-Xmx1g -Xms512m -XX:MetaspaceSize=128m -XX:+UseSerialGC"
```

### 系统资源监控

```bash
# 查看Java进程
jps -v

# 查看内存使用
free -h

# 查看磁盘使用
df -h

# 查看服务端口
netstat -tlnp | grep -E "(3306|6379|9998|9999)"

# 查看应用日志
tail -f logs/ljwx-boot-host.log
```

## 部署建议

### 生产环境部署

1. **服务器配置**
   - CPU: 4核+
   - 内存: 8GB+
   - 磁盘: SSD 100GB+

2. **安全配置**
   - 创建专用用户运行应用
   - 配置防火墙规则
   - MySQL用户权限最小化
   - Redis密码保护

3. **监控配置**
   - 应用监控: http://localhost:9999/actuator
   - 数据库监控: MySQL Workbench或Navicat
   - 系统监控: top、htop、iostat

### 自动化脚本

#### 创建systemd服务文件
```ini
# /etc/systemd/system/ljwx-boot.service
[Unit]
Description=LJWX Boot Application
After=mysql.service redis.service
Requires=mysql.service redis.service

[Service]
Type=simple
User=ljwx
WorkingDirectory=/opt/ljwx-boot
Environment=SPRING_PROFILES_ACTIVE=host
ExecStart=/usr/bin/java -jar ljwx-boot-admin.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 服务管理命令
```bash
# 启用服务
sudo systemctl enable ljwx-boot

# 启动服务
sudo systemctl start ljwx-boot

# 查看状态
sudo systemctl status ljwx-boot

# 查看日志
sudo journalctl -u ljwx-boot -f
```

## 常见问题

### 1. MySQL连接失败

```bash
# 检查MySQL服务状态
./host-services.sh check

# 重启MySQL服务
./host-services.sh restart

# 检查MySQL配置
mysql -u root -p -e "SHOW VARIABLES LIKE 'port';"

# 检查防火墙
sudo ufw status
```

### 2. Redis连接失败

```bash
# 检查Redis服务状态
redis-cli ping

# 查看Redis配置
redis-cli CONFIG GET "*"

# 重启Redis服务
./host-services.sh restart
```

### 3. JAR文件找不到

```bash
# 手动构建JAR
cd ljwx-boot-admin
mvn clean package -DskipTests

# 检查target目录
ls -la target/ljwx-boot-*.jar
```

### 4. 内存不足

```bash
# 调整JVM参数
export JAVA_OPTS="-Xmx1g -Xms512m"

# 查看内存使用
java -XX:+PrintGCDetails -version
```

## 日志管理

### 日志文件位置
- 应用日志: `logs/ljwx-boot-host.log`
- MySQL日志: `/var/log/mysql/error.log`
- Redis日志: `/var/log/redis/redis-server.log`

### 日志轮转配置
```bash
# /etc/logrotate.d/ljwx-boot
/opt/ljwx-boot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        kill -USR1 $(cat /var/run/ljwx-boot.pid)
    endscript
}
```

## 备份恢复

### 数据库备份
```bash
# 备份数据库
mysqldump -u root -p lj-06 > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u root -p lj-06 < backup_20241225.sql
```

### Redis备份
```bash
# Redis自动备份 (RDB文件)
cp /var/lib/redis/dump.rdb backup/dump_$(date +%Y%m%d).rdb

# 手动备份
redis-cli BGSAVE
```

## 支持

如有问题请检查：
- 应用日志: `logs/ljwx-boot-host.log`
- 系统服务: `./host-services.sh status`
- 连接测试: `./host-services.sh test`
- 监控端点: http://localhost:9999/actuator/health 