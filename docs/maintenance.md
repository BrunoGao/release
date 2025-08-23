# CI/CD 系统维护指南

## 日常维护任务

### 1. 系统监控
#### 1.1 资源监控
```bash
# 检查系统资源使用
orb stats

# 检查磁盘使用
df -h
du -sh /Users/brunogao/work/infra/docker/registry/data
```

#### 1.2 服务状态监控
```bash
# 检查所有服务状态
orb ps

# 检查各服务健康状态
curl -I http://localhost:3000  # Gitea
curl -I http://localhost:8000  # Drone
curl -I http://localhost:5000  # Registry
```

### 2. 数据清理
#### 2.1 Docker 镜像清理
```bash
# 清理未使用的镜像
orb docker image prune -a --filter "until=24h"

# 清理未使用的卷
orb docker volume prune
```

#### 2.2 Registry 清理
```bash
# 查看 Registry 存储使用
du -sh /Users/brunogao/work/infra/docker/registry/data

# 清理旧镜像（需要配置 Registry GC）
registry garbage-collect /etc/docker/registry/config.yml
```

#### 2.3 构建缓存清理
```bash
# 清理 Drone 缓存
rm -rf /var/lib/drone/cache/*

# 清理构建产物
find /var/lib/drone/builds -mtime +7 -delete
```

### 3. 备份策略
#### 3.1 配置文件备份
```bash
# 创建备份目录
mkdir -p /backup/$(date +%Y%m%d)

# 备份配置文件
cp -r /Users/brunogao/work/infra/cicd/drone/config /backup/$(date +%Y%m%d)/drone
cp -r /Users/brunogao/work/infra/docker/registry/config /backup/$(date +%Y%m%d)/registry
```

#### 3.2 数据备份
```bash
# 备份 Gitea 数据
orb backup gitea > /backup/$(date +%Y%m%d)/gitea_backup.sql

# 备份 Registry 数据
tar -czf /backup/$(date +%Y%m%d)/registry_data.tar.gz /Users/brunogao/work/infra/docker/registry/data
```

## 定期维护任务

### 1. 每周维护
- [ ] 检查服务日志中的错误和警告
- [ ] 清理未使用的 Docker 镜像和容器
- [ ] 验证备份是否正常执行
- [ ] 检查磁盘使用情况

### 2. 每月维护
- [ ] 更新服务组件版本
- [ ] 检查安全更新
- [ ] 进行完整备份
- [ ] 检查和更新证书（如果需要）

### 3. 季度维护
- [ ] 全面审查系统性能
- [ ] 更新文档
- [ ] 检查和优化资源配置
- [ ] 进行安全审计

## 更新和升级

### 1. OrbStack 更新
```bash
# 检查更新
orb update check

# 执行更新
orb update
```

### 2. 服务更新
```bash
# 更新 Gitea
orb pull gitea
orb restart gitea

# 更新 Drone
orb pull drone-server
orb pull drone-runner
orb restart drone-server drone-runner

# 更新 Registry
orb pull registry
orb restart registry
```

## 监控指标

### 1. 系统指标
- CPU 使用率 < 80%
- 内存使用率 < 80%
- 磁盘使用率 < 85%
- 网络延迟 < 100ms

### 2. 服务指标
- 服务可用性 > 99.9%
- API 响应时间 < 1s
- 构建成功率 > 95%
- 镜像推送成功率 > 99%

## 故障恢复

### 1. 服务故障恢复
```bash
# 重启服务
orb restart <service_name>

# 检查服务状态
orb ps
orb logs <service_name>
```

### 2. 数据恢复
```bash
# 从备份恢复 Gitea 数据
orb restore gitea /backup/gitea_backup.sql

# 从备份恢复 Registry 数据
tar -xzf registry_data.tar.gz -C /
```

## 安全维护

### 1. 访问控制
- 定期更新访问密钥
- 检查用户权限
- 审计访问日志

### 2. 网络安全
- 检查防火墙规则
- 更新 SSL 证书
- 监控异常访问

### 3. 数据安全
- 加密敏感数据
- 定期更改密码
- 检查数据完整性

## 性能优化

### 1. 构建优化
- 优化构建缓存
- 减少构建时间
- 优化构建脚本

### 2. 存储优化
- 优化镜像存储
- 压缩旧数据
- 清理无用数据

### 3. 网络优化
- 优化网络配置
- 使用本地缓存
- 减少网络延迟

## 文档维护

### 1. 更新记录
- 记录配置变更
- 记录问题解决方案
- 更新操作手册

### 2. 知识库
- 整理常见问题
- 更新最佳实践
- 维护故障案例 