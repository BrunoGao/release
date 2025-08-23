# CI/CD 系统问题排查指南

## 常见问题及解决方案

### 1. Gitea Webhook 触发失败

#### 症状
- Webhook 显示发送失败
- CI/CD 流水线没有被触发
- Gitea 界面显示 Webhook 发送错误

#### 排查步骤
1. 检查 Webhook 配置
```bash
# 检查 Gitea 日志
tail -f /var/log/gitea/gitea.log

# 检查 Webhook URL 可访问性
curl -v http://drone-server:8000/hook
```

2. 检查网络连接
```bash
# 检查 Drone 服务是否运行
orb ps | grep drone

# 检查网络连通性
ping drone-server
```

3. 检查认证配置
- 确认 Webhook Secret 是否正确
- 验证 Gitea 和 Drone 的集成配置

### 2. Drone CI 构建失败

#### 症状
- 构建任务启动失败
- 构建过程中断
- 构建完成但结果失败

#### 排查步骤
1. 检查 Drone 日志
```bash
# 查看 Drone 服务日志
orb logs drone-server
orb logs drone-runner
```

2. 检查构建环境
```bash
# 检查 Docker 状态
orb docker ps
orb docker info
```

3. 检查资源使用
```bash
# 检查系统资源
top
df -h
```

### 3. Registry 推送失败

#### 症状
- 镜像推送失败
- 认证错误
- 存储空间不足

#### 排查步骤
1. 检查认证配置
```bash
# 测试 Registry 认证
docker login localhost:5000

# 检查认证配置
cat /Users/brunogao/work/infra/docker/registry/config.yml
```

2. 检查存储状态
```bash
# 检查存储空间
du -sh /Users/brunogao/work/infra/docker/registry/data

# 检查 Registry 日志
orb logs registry
```

### 4. OrbStack 相关问题

#### 症状
- 容器启动失败
- 网络连接问题
- 资源限制问题

#### 排查步骤
1. 检查 OrbStack 状态
```bash
# 检查整体状态
orb ps

# 检查系统信息
orb system info
```

2. 检查网络配置
```bash
# 检查网络列表
orb network ls

# 检查网络连接
orb network inspect bridge
```

3. 检查资源使用
```bash
# 检查容器资源使用
orb stats
```

## 日志收集

### 1. 服务日志
```bash
# Gitea 日志
orb logs gitea

# Drone 日志
orb logs drone-server
orb logs drone-runner

# Registry 日志
orb logs registry
```

### 2. 系统日志
```bash
# 系统日志
tail -f /var/log/system.log

# OrbStack 日志
orb system logs
```

## 常用调试命令

### 1. 服务健康检查
```bash
# 检查 Gitea
curl -I http://localhost:3000

# 检查 Drone
curl -I http://localhost:8000

# 检查 Registry
curl -I http://localhost:5000/v2/
```

### 2. 网络调试
```bash
# 检查端口占用
lsof -i :3000
lsof -i :8000
lsof -i :5000

# 检查网络连接
netstat -an | grep LISTEN
```

### 3. 容器调试
```bash
# 进入容器
orb exec <container_name> sh

# 查看容器详情
orb inspect <container_name>
```

## 性能优化

### 1. 资源限制调整
- 调整 OrbStack 资源限制
- 优化容器资源分配
- 监控资源使用情况

### 2. 网络优化
- 使用本地网络
- 优化 DNS 配置
- 减少网络延迟

### 3. 存储优化
- 定期清理旧数据
- 优化存储配置
- 监控存储使用情况

## 安全检查

### 1. 访问控制
- 检查认证配置
- 验证权限设置
- 审计访问日志

### 2. 网络安全
- 检查防火墙规则
- 验证 SSL/TLS 配置
- 监控异常访问

## 备份和恢复

### 1. 数据备份
```bash
# 备份 Gitea 数据
orb backup gitea

# 备份 Registry 数据
tar -czf registry_backup.tar.gz /Users/brunogao/work/infra/docker/registry/data
```

### 2. 配置备份
```bash
# 备份配置文件
cp -r /Users/brunogao/work/infra/cicd/drone/config /backup/drone_config
cp -r /Users/brunogao/work/infra/docker/registry/config /backup/registry_config
```

## 更新和升级

### 1. 服务更新
```bash
# 更新 OrbStack
orb update

# 更新容器镜像
orb pull gitea
orb pull registry
```

### 2. 配置更新
- 备份旧配置
- 应用新配置
- 验证服务正常 