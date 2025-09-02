# 故障排除指南

## 常见启动问题及解决方案

### 1. MySQL认证错误：cryptography包缺失

**问题现象**：
```
❌处理积压事件失败:'cryptography' package is required for sha256_password or caching_sha2_password auth methods
```

**解决方案**：
```bash
# 安装cryptography包
pip install cryptography>=3.4.8

# 或者重新安装requirements.txt
cd bigscreen
pip install -r requirements.txt
```

### 2. 微信配置缺失警告

**问题现象**：
```
微信配置检查: 缺少配置: WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_TEMPLATE_ID, WECHAT_USER_OPENID
```

**解决方案**：

#### 方案1：配置微信告警（推荐）
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑.env文件，填入实际的微信配置
vim .env
```

在.env文件中配置：
```bash
# 启用微信告警
WECHAT_ALERT_ENABLED=true
# 填入实际的微信配置
WECHAT_APP_ID=你的微信AppID
WECHAT_APP_SECRET=你的微信AppSecret
WECHAT_TEMPLATE_ID=你的模板消息ID
WECHAT_USER_OPENID=接收告警的用户OpenID
```

#### 方案2：禁用微信告警
```bash
# 在.env文件中设置
WECHAT_ALERT_ENABLED=false
CORP_WECHAT_ENABLED=false
```

### 3. 数据库连接问题

**检查数据库配置**：
```bash
# 确保MySQL服务正在运行
systemctl status mysql

# 检查数据库连接配置
cat .env | grep MYSQL
```

**配置示例**：
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lj-06
```

### 4. Redis连接问题

**检查Redis配置**：
```bash
# 确保Redis服务正在运行
systemctl status redis

# 测试Redis连接
redis-cli -h localhost -p 6379 ping
```

**配置示例**：
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
```

## 启动步骤

### 1. 安装依赖
```bash
cd bigscreen
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 启动应用
```bash
# 方法1：使用run.py启动
python run.py

# 方法2：使用bigScreen目录启动
cd bigScreen && python run_bigscreen.py

# 方法3：启动所有服务（包括Celery和监控）
./start_all.sh
```

## 性能优化

### MySQL连接池优化
```python
# 在config.py中调整连接池参数
DB_POOL_CONFIG = {
    'pool_size': 30,
    'max_overflow': 50,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Redis性能优化
```python
# 启用Redis管道和批处理
PERFORMANCE_CONFIG = {
    'batch_size': 200,
    'redis_pipeline_size': 100,
    'async_workers': 20
}
```

## 日志和监控

### 查看日志
```bash
# 查看应用日志
tail -f bigscreen.log

# 查看系统日志
tail -f system.log

# 查看性能日志
tail -f performance_data.json
```

### 监控端点
- 系统统计：`http://localhost:5001/api/realtime_stats`
- 性能监控：`http://localhost:5001/system_monitor`
- 性能测试：`http://localhost:5001/performance_test_report`

## Docker部署

### 构建镜像
```bash
# 多架构构建
docker buildx build --platform linux/amd64,linux/arm64 -t ljwx-bigscreen:latest .

# 单架构构建
docker build -t ljwx-bigscreen:latest .
```

### 运行容器
```bash
# 使用docker-compose
docker-compose up -d

# 手动运行
docker run -d \
  --name ljwx-bigscreen \
  -p 5001:5001 \
  -e MYSQL_HOST=your_mysql_host \
  -e REDIS_HOST=your_redis_host \
  ljwx-bigscreen:latest
```

## 获取帮助

如果遇到其他问题，请：

1. 检查日志文件中的详细错误信息
2. 确认所有依赖服务（MySQL、Redis）正常运行
3. 验证配置文件中的参数是否正确
4. 查看GitHub Issues获取更多解决方案