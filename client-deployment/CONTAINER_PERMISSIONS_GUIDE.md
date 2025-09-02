# 容器权限修复指南

## 问题描述
客户部署时可能遇到容器内脚本无执行权限的问题，导致wait-for-it.sh无法运行，容器启动失败。

## 解决方案

### 1. 预防措施（已在docker-compose.yml中实现）
每个容器启动时自动设置脚本权限：
```bash
command: ["sh", "-c", "chmod +x /usr/local/bin/wait-for-it.sh && wait-for-it.sh ..."]
```

### 2. 权限检查
运行权限检查脚本：
```bash
./fix-container-permissions.sh
```

### 3. 容器运行时测试
容器启动后测试权限：
```bash
./test-container-permissions.sh
```

### 4. 手动修复（如果需要）
如果容器已运行但权限有问题：
```bash
# 修复ljwx-boot容器权限
docker exec ljwx-boot chmod +x /usr/local/bin/wait-for-it.sh

# 修复ljwx-bigscreen容器权限  
docker exec ljwx-bigscreen chmod +x /usr/local/bin/wait-for-it.sh

# 修复ljwx-admin容器权限
docker exec ljwx-admin chmod +x /usr/local/bin/wait-for-it.sh
```

## 权限问题排查

### 症状
- 容器启动失败
- 日志显示 "permission denied" 或 "command not found"
- wait-for-it.sh 无法执行

### 排查步骤
1. 检查宿主机脚本权限：`ls -la wait-for-it.sh`
2. 检查容器内权限：`docker exec <容器名> ls -la /usr/local/bin/wait-for-it.sh`
3. 测试脚本执行：`docker exec <容器名> /usr/local/bin/wait-for-it.sh --help`

### 常见错误
- **挂载为只读**: 确保docker-compose.yml中没有:ro标记
- **宿主机无权限**: 运行 `chmod +x wait-for-it.sh`
- **容器内无权限**: 在command中添加 `chmod +x` 命令

## 最佳实践
1. 部署前运行 `./fix-container-permissions.sh` 检查
2. 容器启动后运行 `./test-container-permissions.sh` 验证
3. 监控容器启动日志，及时发现权限问题
4. 定期检查脚本文件权限

## 技术原理
- Docker挂载会保持宿主机文件权限
- 容器内chmod可以修改挂载文件权限
- 启动命令中的chmod确保权限正确性
- 移除:ro标记允许容器内修改权限
