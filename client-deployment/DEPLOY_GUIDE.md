# 灵境万象健康管理系统 - 一键部署指南

## 概述
本指南介绍如何使用 `deploy-client.sh` 脚本一键启动所有应用，确保 `ljwx-admin` 可以正确跳转到 `ljwx-bigscreen`。

## 部署流程

### 1. 配置环境变量
编辑 `custom-config.env` 文件，设置服务器IP和端口：

```bash
# ==================== 网络配置 ====================
# 服务器IP地址 - 根据实际部署环境修改
SERVER_IP=192.168.1.83
# 大屏服务端口 - 必须与docker-compose.yml中ljwx-bigscreen的端口一致
BIGSCREEN_PORT=8001
```

### 2. 一键部署
执行部署脚本：

```bash
./deploy-client.sh
```

## 部署过程说明

### 步骤1：配置验证
- 自动验证 `VITE_BIGSCREEN_URL` 端口与 `docker-compose.yml` 一致性
- 检查IP地址和URL格式正确性

### 步骤2：外挂目录配置
- 自动执行 `fix-volume-mounts.sh` 配置外挂目录
- 创建数据、日志、备份目录结构：
  ```
  data/
  ├── mysql/
  ├── redis/
  ├── ljwx-boot/
  └── ljwx-bigscreen/
  
  logs/
  ├── mysql/
  ├── redis/
  ├── ljwx-boot/
  ├── ljwx-bigscreen/
  └── ljwx-admin/
  
  ../backup/
  ├── mysql/
  ├── redis/
  ├── ljwx-boot/
  └── ljwx-bigscreen/
  ```

### 步骤3：镜像拉取
- 自动登录阿里云镜像仓库
- 拉取最新版本镜像（与docker-compose.yml版本一致）

### 步骤4：服务启动
- 使用 `docker-compose.yml` 启动所有服务
- 自动健康检查，确保服务正常启动

### 步骤5：数据恢复（可选）
如果是重新部署或需要恢复历史数据，在服务启动后执行数据恢复：

**MySQL数据恢复：**
```bash
# 方式1：自动恢复最新备份
./restore-database.sh

# 方式2：指定备份文件恢复
./restore-database.sh backup/mysql/ljwx_backup_20241201.sql

# 方式3：手动恢复
docker exec -i ljwx-mysql mysql -uroot -p123456 ljwx < backup/mysql/ljwx_backup_latest.sql
```

**Redis数据恢复：**
```bash
# 恢复Redis缓存数据
./restore-redis.sh

# 或手动恢复
docker exec ljwx-redis redis-cli FLUSHALL
docker cp backup/redis/dump.rdb ljwx-redis:/data/
docker-compose restart ljwx-redis
```

**应用数据恢复：**
```bash
# 恢复应用配置和上传文件
cp -r backup/ljwx-boot/* data/ljwx-boot/
cp -r backup/ljwx-bigscreen/* data/ljwx-bigscreen/
```

### 步骤6：前端URL替换
- 自动执行 `replace-bigscreen-url.sh` 替换前端硬编码URL
- 将JavaScript文件中的localhost:8001替换为配置的大屏地址
- 确保管理端能正确跳转到大屏

## 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| ljwx-admin | 8080 | 管理端界面 |
| ljwx-bigscreen | 8001 | 大屏展示 |
| ljwx-boot | 9998 | 后端API |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |

## 重要配置项

### VITE_BIGSCREEN_URL
此配置项决定管理端如何跳转到大屏，在 `custom-config.env` 中配置：
```bash
# 大屏访问地址 - ljwx-admin中跳转大屏的URL（客户端浏览器可访问）
VITE_BIGSCREEN_URL=http://192.168.1.83:8001
```

**配置传递链路：**
```
custom-config.env → docker-compose.yml → ljwx-admin容器 → 前端页面
```

**注意事项：**
- IP地址必须是客户端浏览器可访问的服务器IP
- 端口必须与 `docker-compose.yml` 中 `ljwx-bigscreen` 服务端口一致
- 此URL将在 `http://localhost:8080/#/home` 页面中作为大屏跳转链接使用

## 配置验证

### 验证大屏跳转配置
```bash
# 验证配置文件正确性
./validate-config.sh

# 验证前端大屏URL配置
./test-bigscreen-url.sh

# 手动替换URL（如果需要）
./replace-bigscreen-url.sh
```

**验证要点：**
- `custom-config.env` 中 `VITE_BIGSCREEN_URL` 配置正确
- JavaScript文件中的localhost:8001已替换为实际IP
- 大屏地址可正常访问

**前端URL替换原理：**
Vue.js应用在打包时将环境变量编译到静态文件中，运行时环境变量无法直接生效。因此需要动态替换JavaScript文件中的硬编码URL。

## 数据管理

### 数据备份
系统支持自动和手动备份：

```bash
# 自动备份（包含MySQL、Redis、应用数据）
./backup-all.sh

# 仅备份MySQL数据库
./backup-database.sh

# 仅备份Redis数据
./backup-redis.sh

# 查看备份列表
ls -la backup/mysql/
ls -la backup/redis/
```

### 数据恢复详细说明

#### MySQL恢复流程
```bash
# 1. 检查可用备份文件
ls -la backup/mysql/

# 2. 停止相关服务（确保数据一致性）
docker-compose stop ljwx-boot ljwx-bigscreen ljwx-admin

# 3. 恢复数据库
./restore-database.sh backup/mysql/ljwx_backup_20241201_143022.sql

# 4. 验证恢复结果
docker exec ljwx-mysql mysql -uroot -p123456 -e "USE ljwx; SELECT COUNT(*) FROM t_user_info;"

# 5. 重启所有服务
docker-compose up -d
```

#### Redis恢复流程
```bash
# 1. 停止Redis服务
docker-compose stop ljwx-redis

# 2. 恢复Redis数据
./restore-redis.sh backup/redis/dump_20241201.rdb

# 3. 启动Redis服务
docker-compose start ljwx-redis

# 4. 验证缓存数据
docker exec ljwx-redis redis-cli ping
```

#### 应用文件恢复
```bash
# 恢复后端上传文件
cp -r backup/ljwx-boot/uploads/* data/ljwx-boot/uploads/

# 恢复大屏静态资源
cp -r backup/ljwx-bigscreen/static/* data/ljwx-bigscreen/static/

# 恢复配置文件
cp -r backup/ljwx-boot/config/* data/ljwx-boot/config/
```

### 数据恢复验证
恢复完成后，执行以下验证：

```bash
# 验证MySQL数据
./verify-database.sh

# 验证Redis缓存
./verify-redis.sh

# 验证应用服务
curl http://localhost:9998/actuator/health
curl http://localhost:8001/health

# 验证管理界面
curl http://localhost:8080
```

## 常用命令

### 查看服务状态
```bash
docker-compose -f docker-compose.yml ps
```

### 查看服务日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.yml logs -f ljwx-admin
docker-compose -f docker-compose.yml logs -f ljwx-bigscreen
docker-compose -f docker-compose.yml logs -f ljwx-boot
```

### 重启服务
```bash
# 重启特定服务
docker-compose -f docker-compose.yml restart ljwx-admin

# 重启所有服务
docker-compose -f docker-compose.yml restart
```

### 停止服务
```bash
docker-compose -f docker-compose.yml down
```

## 故障排查

### 管理端无法跳转到大屏
1. **一键诊断**：`./diagnose-bigscreen-issue.sh`
2. **浏览器缓存问题**：
   - 硬刷新页面：`Ctrl+F5` (Windows) 或 `Cmd+Shift+R` (Mac)
   - 清除浏览器缓存：`./clear-browser-cache.sh`
   - 使用隐私模式访问：`http://localhost:8080/#/home`
3. **手动修复**：
   - 检查配置：`./validate-config.sh`
   - 替换URL：`./replace-bigscreen-url.sh`
   - 验证替换：`./test-bigscreen-url.sh`
4. **服务检查**：
   - 后端服务：`curl http://localhost:9998/actuator/health`
   - 大屏服务：`curl http://localhost:8001`

**常见原因：浏览器缓存了旧的JavaScript文件，需要强制刷新或清除缓存**

### 服务启动失败
1. 检查Docker和docker-compose是否正确安装
2. 查看具体服务日志定位问题
3. 确认镜像是否成功拉取

### 数据持久化问题
1. 确认外挂目录权限设置正确
2. 检查磁盘空间是否充足
3. 验证备份目录是否可写

### 数据恢复问题
1. **恢复失败**：
   - 检查备份文件完整性：`./verify-backup.sh`
   - 确认MySQL容器状态：`docker logs ljwx-mysql`
   - 验证数据库连接：`docker exec ljwx-mysql mysql -uroot -p123456 -e "SHOW DATABASES;"`

2. **恢复后数据异常**：
   - 检查恢复日志：`cat logs/restore_*.log`
   - 验证表结构：`./check-database-schema.sh`
   - 重建索引：`./rebuild-database-indexes.sh`

3. **Redis恢复问题**：
   - 检查Redis日志：`docker logs ljwx-redis`
   - 验证RDB文件：`redis-check-rdb backup/redis/dump.rdb`
   - 手动重启：`docker-compose restart ljwx-redis`

### 完整恢复流程
如果需要完全重新部署并恢复所有数据：

```bash
# 1. 停止所有服务
docker-compose down -v

# 2. 清理数据目录（谨慎操作）
rm -rf data/* logs/*

# 3. 重新部署
./deploy-client.sh

# 4. 等待服务完全启动
sleep 60

# 5. 恢复所有数据
./restore-all-data.sh

# 6. 验证恢复结果
./verify-deployment.sh
```

## 联系支持
如遇到部署问题，请提供：
- 错误日志信息
- 服务器环境信息
- 配置文件内容

技术支持将协助解决问题。 