# 密码统一配置指南

## 📋 配置概述

为了解决多个配置文件密码不一致的问题，现已统一所有密码配置到 `custom-config.env` 文件中。

## 🔑 统一密码配置

**所有服务统一使用密码：`123456`**

### 配置文件层级

1. **主配置文件**: `custom-config.env` （唯一配置源）
2. **Python配置**: `custom-config.py` （从环境变量读取）
3. **Docker Compose**: `docker-compose-client.yml` （从环境变量读取）

## 📁 配置文件详情

### custom-config.env
```env
# 数据库配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=lj-06

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=123456
REDIS_DB=0
```

### 环境变量优先级

Docker Compose配置中所有密码都使用环境变量引用：
- `MYSQL_PASSWORD=${MYSQL_PASSWORD:-123456}`
- `REDIS_PASSWORD=${REDIS_PASSWORD:-123456}`

## 🛠️ 修改密码方法

### 1. 修改统一密码
只需修改 `custom-config.env` 文件中的密码：
```bash
# 编辑配置文件
vi custom-config.env

# 修改以下行
MYSQL_PASSWORD=新密码
REDIS_PASSWORD=新密码
```

### 2. 重新部署服务
```bash
# 停止所有服务
docker-compose -f docker-compose-client.yml down

# 删除MySQL数据卷（如果需要重新初始化）
docker volume rm client-deployment_mysql_data

# 重新启动服务
docker-compose -f docker-compose-client.yml up -d
```

## ✅ 验证配置

### 检查MySQL连接
```bash
docker exec ljwx-mysql mysql -uroot -p123456 -e "SELECT 'MySQL连接成功' AS result;"
```

### 检查Redis连接
```bash
docker exec ljwx-redis redis-cli auth 123456
```

### 检查环境变量
```bash
# 检查ljwx-boot的密码配置
docker exec ljwx-boot env | grep -E "(MYSQL|REDIS)_PASSWORD"

# 检查ljwx-bigscreen的密码配置
docker exec ljwx-bigscreen env | grep -E "(MYSQL|REDIS)_PASSWORD"
```

## 🔧 配置优化

### 避免硬编码的改进

1. **Docker Compose环境变量化**
   - 所有密码配置使用 `${变量名:-默认值}` 格式
   - 通过 `env_file` 加载配置文件

2. **Python配置动态化**
   - `custom-config.py` 完全依赖环境变量
   - 设置合理的默认值

3. **单一配置源**
   - `custom-config.env` 为唯一配置文件
   - 其他文件通过环境变量读取

## 🚀 部署最佳实践

1. **配置文件权限**
   ```bash
   chmod 600 custom-config.env  # 限制配置文件权限
   ```

2. **密码安全性**
   - 生产环境使用强密码
   - 定期更换密码
   - 避免在日志中记录密码

3. **环境隔离**
   - 开发/测试/生产环境使用不同配置文件
   - 通过环境变量覆盖默认配置

## 📊 当前部署状态

✅ 所有服务正常运行  
✅ MySQL使用统一密码123456  
✅ Redis密码配置统一  
✅ ljwx-boot Redis连接修复完成  
✅ 环境变量正确加载  
✅ 服务间连接正常  

## 🔧 Redis连接问题解决方案

**问题**：ljwx-boot容器中Redis密码未从环境变量正确加载

**解决方案**：在docker-compose-client.yml中使用硬编码密码确保正确传递
```yaml
REDIS_PASSWORD: "123456"
SPRING_DATA_REDIS_PASSWORD: "123456"
```

**验证方法**：
```bash
# 检查容器中的Redis密码
docker exec ljwx-boot env | grep REDIS_PASSWORD
# 应输出：REDIS_PASSWORD=123456

# 检查启动日志中的Redis连接
docker logs ljwx-boot | grep -i redis
# 应看到成功的连接日志
```  

## 🎨 自定义Logo配置已修复

**问题**：custom-logo.svg无法显示
**原因**：
1. VITE_CUSTOM_LOGO环境变量为false
2. custom-admin-config.js中useCustomLogo为false  
3. Logo文件挂载路径不正确

**解决方案**：
1. 修改custom-config.env：`VITE_CUSTOM_LOGO=true`
2. 修改custom-admin-config.js：`useCustomLogo: true`
3. 修改Docker挂载路径：`./custom-logo.svg:/tmp/custom-logo.svg:ro`
4. Docker Compose强制设置：`VITE_CUSTOM_LOGO: "true"`

**验证结果**：
✅ Logo已成功更新到/usr/share/nginx/html/assets/logo-DgyNd7sd.svg
✅ 新Logo文件大小: 10698 bytes
✅ 管理后台正常显示自定义Logo

## 🔗 访问地址

- **管理后台**: http://localhost:8080 (✅ 自定义Logo已生效)
- **数据大屏**: http://localhost:8001
- **API服务**: http://localhost:9998
- **MySQL数据库**: localhost:3306
- **Redis缓存**: localhost:6379 