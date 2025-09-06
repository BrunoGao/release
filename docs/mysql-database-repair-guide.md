# MySQL数据库修复与重建指南

## 问题背景

在LJWX系统部署过程中，遇到了ljwx-mysql Docker镜像数据不完整的问题，导致应用启动时出现"Table 'lj-06.sys_org_closure' doesn't exist"等错误。

## 问题分析

### 根本原因
1. **数据导出不完整**: 原始data.sql文件只包含最小化的test_table测试数据，缺少完整的应用表结构
2. **数据库名称映射**: 导出的完整数据库名称为`lj-06`，而不是`test`
3. **Docker镜像缓存**: 即使更新了data.sql文件，Docker镜像可能仍使用旧的缓存层

### 影响表现
- 应用启动时报告缺少关键表：`sys_org_closure`、`sys_org_units`、`sys_org_manager_cache`等
- MySQL容器能正常启动，但数据库内容不完整
- 前端页面无法正常加载组织架构相关功能

## 修复步骤

### 1. 导出完整数据库
```bash
# 从本地MySQL实例导出完整的lj-06数据库
mysqldump -h 127.0.0.1 -P 3306 -u root -p123456 \
  --single-transaction \
  --routines \
  --triggers \
  --complete-insert \
  --databases lj-06 > data.sql
```

**关键参数说明:**
- `--single-transaction`: 保证数据一致性
- `--routines`: 导出存储过程和函数
- `--triggers`: 导出触发器
- `--complete-insert`: 生成完整的INSERT语句
- `--databases lj-06`: 指定数据库名称

### 2. 清理旧的容器和卷
```bash
# 停止并删除现有容器
docker stop ljwx-mysql && docker rm ljwx-mysql

# 删除旧的数据卷
docker volume rm client-deployment_mysql_data
```

### 3. 重建MySQL镜像
```bash
# 使用--no-cache强制重建，确保使用新的data.sql
PUSH_TO_REGISTRY=false LOCAL_BUILD=true PLATFORMS=linux/amd64 ./build-and-push.sh mysql --no-cache
```

### 4. 启动并验证
```bash
# 启动新的MySQL服务
cd client-deployment && docker-compose up -d ljwx-mysql

# 等待MySQL完成初始化（约30秒）
sleep 30

# 验证数据库和表结构
docker exec ljwx-mysql mysql -u root -p123456 -e "SHOW DATABASES;"
docker exec ljwx-mysql mysql -u root -p123456 -e "USE \`lj-06\`; SHOW TABLES LIKE '%sys_org%';"
```

## 验证结果

修复完成后，MySQL容器应包含以下数据库结构：

### 数据库列表
```
Database
information_schema
lj-06          # 完整的应用数据库
mysql
performance_schema
sys
```

### 关键表验证
```sql
USE `lj-06`;
SHOW TABLES LIKE '%sys_org%';
-- 应返回:
-- sys_org_closure
-- sys_org_manager_cache  
-- sys_org_units
```

## 配置说明

### MySQL 8.0配置 (my.cnf)
```ini
[mysqld]
# 基础配置
default_authentication_plugin=mysql_native_password
sql_mode=STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO

# 字符集配置
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

### Docker构建配置
```dockerfile
FROM mysql:8.0
COPY data.sql /docker-entrypoint-initdb.d/01-init-data.sql
COPY docker/mysql/my.cnf /etc/mysql/conf.d/ljwx.cnf
```

## 注意事项

1. **数据库名称**: 应用连接的数据库名称是`lj-06`，不是`test`
2. **密码配置**: 默认root密码为`123456`
3. **初始化时间**: MySQL初始化需要30秒左右，大数据量情况下可能更长
4. **版本选择**: 使用MySQL 8.0，比MySQL 9.0更稳定且兼容性更好

## 故障排除

### 如果仍然缺少表
1. 检查data.sql文件大小（应该是15MB+，而不是几KB）
2. 确认Docker镜像是否真正重建（使用--no-cache参数）
3. 检查MySQL初始化日志：`docker logs ljwx-mysql`

### 如果数据库连接失败
1. 检查密码配置（默认123456）
2. 检查数据库名称（lj-06 vs test）
3. 确认MySQL服务完全启动

## 总结

此次修复的核心是确保：
1. **数据完整性**: 导出包含所有表、存储过程、触发器的完整数据库
2. **容器重建**: 清理缓存，强制使用新的数据文件重建镜像  
3. **配置正确性**: 使用稳定的MySQL 8.0版本和正确的配置参数

修复后的ljwx-mysql镜像包含了完整的lj-06数据库，能够支持LJWX系统的所有功能模块正常运行。