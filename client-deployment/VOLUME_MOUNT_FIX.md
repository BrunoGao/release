# Docker数据挂载修复说明

## 问题描述
原配置使用命名卷（named volumes），导致数据、日志、备份等文件无法在宿主机直接访问，目录显示为空。

## 修复内容

### 1. 移除命名卷配置
- 删除了 `volumes:` 部分的 `mysql_data` 和 `redis_data` 命名卷定义
- 改用宿主机目录直接挂载

### 2. 修正挂载路径

#### MySQL服务
```yaml
volumes:
  - ./data/mysql:/var/lib/mysql                  # MySQL数据外挂
  - ./logs/mysql:/var/log/mysql                  # MySQL日志外挂
  - ../backup/mysql:/backup/mysql                # MySQL备份外挂
```

#### Redis服务
```yaml
volumes:
  - ./data/redis:/data                           # Redis数据外挂
  - ./logs/redis:/var/log/redis                  # Redis日志外挂
  - ../backup/redis:/backup/redis                # Redis备份外挂
```

#### ljwx-boot服务
```yaml
volumes:
  - ./logs/ljwx-boot:/app/ljwx-boot-logs         # 应用日志外挂
  - ./data/ljwx-boot:/app/data                   # 应用数据外挂
  - ../backup/ljwx-boot:/backup/ljwx-boot        # 应用备份外挂
```

#### ljwx-bigscreen服务
```yaml
volumes:
  - ./logs/ljwx-bigscreen:/app/logs              # 大屏日志外挂
  - ./data/ljwx-bigscreen:/app/data              # 大屏数据外挂
  - ../backup/ljwx-bigscreen:/backup/ljwx-bigscreen # 大屏备份外挂
```

### 3. 目录结构
修复后的目录结构：
```
client-deployment/
├── data/                    # 应用数据目录
│   ├── mysql/              # MySQL数据文件
│   ├── redis/              # Redis数据文件
│   ├── ljwx-boot/          # Boot应用数据
│   └── ljwx-bigscreen/     # 大屏应用数据
├── logs/                   # 应用日志目录
│   ├── mysql/              # MySQL日志
│   ├── redis/              # Redis日志
│   ├── ljwx-boot/          # Boot应用日志
│   ├── ljwx-bigscreen/     # 大屏应用日志
│   └── ljwx-admin/         # 管理后台日志
└── ../backup/              # 备份目录
    ├── mysql/              # MySQL备份
    ├── redis/              # Redis备份
    ├── ljwx-boot/          # Boot应用备份
    └── ljwx-bigscreen/     # 大屏应用备份
```

## 使用方法

### 1. 应用修复
配置已自动应用到 `docker-compose-enhanced.yml`，原配置已备份为 `docker-compose-enhanced.yml.backup`

### 2. 启动服务
```bash
docker-compose -f docker-compose-enhanced.yml up -d
```

### 3. 验证挂载
启动后检查目录是否有数据：
```bash
# 检查数据目录
ls -la data/
ls -la logs/
ls -la ../backup/

# 检查容器挂载
docker inspect ljwx-mysql | grep -A 10 "Mounts"
```

## 优势
1. **数据可见性**：所有数据、日志、备份在宿主机直接可见
2. **备份便利**：可直接访问和备份宿主机目录
3. **调试方便**：日志文件可直接查看和分析
4. **数据安全**：容器删除后数据仍保留在宿主机
5. **迁移简单**：直接复制目录即可迁移数据

## 注意事项
1. 确保宿主机有足够磁盘空间
2. 定期清理日志文件避免占用过多空间
3. 备份目录建议定期同步到远程存储 