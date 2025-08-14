# 启动异常解决指南

## 问题描述
启动时出现 `Exception in thread Thread-2 (run_server)` 异常

## 解决方案

### 1. 快速修复 (推荐)
```bash
# 运行修复脚本
python fix_startup.py

# 然后正常启动
python run.py
```

### 2. 手动修复步骤

#### 检查端口占用
```bash
# 检查5001端口
lsof -i :5001

# 检查8001端口  
lsof -i :8001

# 杀掉占用进程
kill -9 <PID>
```

#### 检查数据库连接
```bash
# 确保MySQL服务运行
brew services start mysql
# 或
sudo systemctl start mysql

# 确保Redis服务运行
brew services start redis
# 或
sudo systemctl start redis
```

#### 检查环境变量
```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=lj-06
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=123456
export APP_PORT=5001
```

### 3. 常见问题

#### 端口被占用
- 症状：`Address already in use`
- 解决：运行 `python fix_startup.py` 自动清理端口

#### 数据库连接失败
- 症状：`MySQL连接失败`
- 解决：检查MySQL服务状态和配置

#### Redis连接失败
- 症状：`Redis连接失败`
- 解决：检查Redis服务状态和密码配置

#### SocketIO启动失败
- 症状：`Thread-2 (run_server)` 异常
- 解决：使用优化后的启动脚本，已增加异常处理

### 4. 启动流程优化

新的启动流程包含：
1. ✅ 端口检查和清理
2. ✅ 数据库连接验证
3. ✅ Redis连接验证
4. ✅ 优雅关闭处理
5. ✅ 端口重试机制
6. ✅ 详细错误日志

### 5. 调试模式
```bash
# 开启调试模式
export DEBUG=true
python run.py

# 生产模式（默认）
export DEBUG=false
python run.py
```

### 6. 服务状态检查
```bash
# 检查服务是否正常启动
curl http://localhost:5001/test

# 检查健康状态
curl http://localhost:5001/checkLicense
```

## 修复完成标志
- ✅ 端口5001/8001可用
- ✅ MySQL连接正常
- ✅ Redis连接正常
- ✅ 应用启动成功
- ✅ 无Thread异常 