# ljwx-boot 本地开发环境配置指南

## 概述

本指南提供了ljwx-boot在本地开发环境中的配置和运行方式，支持连接本地服务器而不是容器内服务器，且不影响现有的镜像制作流程。

## 环境要求

### 必需环境
- **Java**: 17+ (推荐 21)
- **Maven**: 3.8+ 
- **Docker**: 20.10+ (用于依赖服务)
- **Docker Compose**: 1.29+

### 可选环境
- **MySQL客户端**: 用于数据库连接检查
- **Redis客户端**: 用于Redis连接检查
- **Git**: 用于代码管理

## 快速开始

### 1. 启动依赖服务

```bash
# 进入ljwx-boot目录
cd ljwx-boot

# 启动所有依赖服务
./local-services.sh start

# 或者分别启动特定服务
./local-services.sh mysql    # 仅启动MySQL
./local-services.sh redis    # 仅启动Redis
./local-services.sh minio    # 仅启动MinIO
./local-services.sh ollama   # 仅启动Ollama
```

### 2. 初始化数据库

```bash
# 初始化数据库结构
./local-services.sh init
```

### 3. 启动ljwx-boot应用

```bash
# 本地运行ljwx-boot
./run-local.sh

# 或者使用自定义配置文件
./run-local.sh my-config.env
```

## 配置说明

### 本地配置文件 (local-config.env)

```bash
# Spring配置
export SPRING_PROFILES_ACTIVE=local

# MySQL配置
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=lj-06

# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=123456
export REDIS_DB=1

# AI服务配置
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:7b

# 对象存储配置
export OSS_NAME=local
export OSS_ENDPOINT=http://localhost:9000
export OSS_ACCESS_KEY=admin
export OSS_SECRET_KEY=admin123
export OSS_BUCKET_NAME=ljwx-local

# 向量数据库配置
export PGVECTOR_USER=postgres
export PGVECTOR_PASSWORD=postgres
```

### application-local.yml 配置特点

- **数据库连接**: 自动连接到localhost:3306
- **Redis连接**: 自动连接到localhost:6379
- **日志级别**: 调试级别，便于开发调试
- **连接池**: 优化本地开发连接数配置
- **监控**: 完整的监控端点暴露
- **安全**: 禁用开发环境不必要的安全认证

## 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| ljwx-boot | 9998 | 主应用服务 |
| ljwx-boot-monitor | 9999 | 监控端点 |
| MySQL | 3306 | 数据库服务 |
| Redis | 6379 | 缓存服务 |
| MinIO | 9000 | 对象存储API |
| MinIO Console | 9001 | 对象存储控制台 |
| PostgreSQL | 5432 | 向量数据库 |
| Ollama | 11434 | AI服务 |

## 常用命令

### 服务管理

```bash
# 查看服务状态
./local-services.sh status

# 查看服务日志
./local-services.sh logs

# 查看特定服务日志
./local-services.sh logs mysql-local

# 重启服务
./local-services.sh restart

# 停止服务
./local-services.sh stop

# 清理所有数据
./local-services.sh clean
```

### 应用管理

```bash
# 编译应用
cd ljwx-boot-admin
mvn clean compile

# 运行测试
mvn test

# 打包应用
mvn package -DskipTests

# 直接运行(跳过脚本)
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

## 开发调试

### 1. 数据库调试

```bash
# 连接到本地MySQL
mysql -h localhost -P 3306 -u root -p123456 lj-06

# 查看数据库结构
SHOW TABLES;
DESCRIBE table_name;
```

### 2. Redis调试

```bash
# 连接到本地Redis
redis-cli -h localhost -p 6379 -a 123456

# 查看Redis信息
INFO
KEYS *
```

### 3. 应用调试

- **日志文件**: `logs/ljwx-boot-local.log`
- **监控端点**: http://localhost:9999/actuator
- **健康检查**: http://localhost:9999/actuator/health
- **Swagger API**: http://localhost:9998/swagger-ui.html

## 性能优化

### 1. 本地开发优化

- 连接池配置针对本地环境优化
- 日志级别可调整为INFO减少日志输出
- 禁用不必要的监控指标

### 2. 内存优化

```bash
# 设置JVM内存参数
export MAVEN_OPTS="-Xmx2g -Xms1g -XX:MetaspaceSize=256m"

# 或在IDE中设置VM options
-Xmx2g -Xms1g -XX:MetaspaceSize=256m -Dspring.profiles.active=local
```

## 常见问题

### 1. 端口冲突

如果端口被占用，修改配置文件中的端口号：

```bash
# 查看端口占用
lsof -i :3306
lsof -i :6379

# 修改docker-compose-local.yml中的端口映射
```

### 2. 数据库连接失败

```bash
# 检查MySQL服务状态
./local-services.sh status

# 重启MySQL服务
docker restart ljwx-mysql-local

# 查看MySQL日志
docker logs ljwx-mysql-local
```

### 3. 构建失败

```bash
# 清理Maven缓存
mvn clean
rm -rf ~/.m2/repository/com/ljwx

# 重新构建
mvn clean compile -U
```

## 与镜像制作的兼容性

本地开发配置与现有镜像制作完全兼容：

- **配置文件分离**: 本地配置不影响Docker镜像配置
- **Profile隔离**: 使用`local` profile，不影响`docker`或`prod` profile
- **构建脚本**: 镜像构建脚本会自动选择正确的配置文件

## 贡献指南

1. 修改配置时，确保不影响现有的`docker`和`prod`环境
2. 添加新的本地配置项时，在`application-local.yml`中添加
3. 更新文档说明新增的配置项
4. 测试本地环境和Docker环境的兼容性

## 支持

如有问题请查看：
- 应用日志: `logs/ljwx-boot-local.log`
- 服务日志: `./local-services.sh logs`
- 监控端点: http://localhost:9999/actuator 