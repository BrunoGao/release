# Gitea 数据保护解决方案

## 问题解决

✅ **自动定时备份** - 每6小时自动备份，无需手动干预  
✅ **实时数据同步** - 数据变更实时同步到保护目录  
✅ **一键恢复** - 单命令快速恢复任意备份点  
✅ **多层保护** - 卷备份 + 实时同步 + 安全备份  
✅ **智能清理** - 自动清理30天前的旧备份  
✅ **健康监控** - 全方位监控数据完整性  

## 快速开始

### 1. 初始化数据保护

```bash
# 一键设置所有数据保护机制
./gitea-data-protection.sh auto-setup
```

### 2. 启动保护服务

```bash
# 启动 Gitea + 数据保护
./gitea-data-protection.sh start
```

### 3. 验证保护状态

```bash
# 检查所有保护机制
./gitea-data-protection.sh health
```

## 核心功能

### 自动备份

- **定时备份**: 每6小时自动执行
- **命名规范**: `gitea-YYYYMMDD-HHMMSS.tar.gz`
- **元数据记录**: 每个备份都有详细信息
- **自动清理**: 保留30天内的备份

```bash
# 手动创建备份
./gitea-data-protection.sh backup

# 创建命名备份
./gitea-data-protection.sh backup "important-milestone"
```

### 数据恢复

```bash
# 列出可用备份并恢复
./gitea-data-protection.sh restore

# 恢复特定备份
./gitea-data-protection.sh restore gitea-20240824-120000.tar.gz
```

### 实时同步

- 每5分钟同步数据变更到 `data-protection/gitea/realtime-sync/`
- 守护进程持续运行，确保数据实时保护
- 即使主备份丢失，同步目录仍有最新数据

### 健康监控

```bash
# 全面健康检查
./gitea-data-protection.sh health

# 检查内容包括:
# - 服务运行状态
# - 数据卷完整性  
# - Git 仓库数量统计
# - 最近备份状态
# - 保护机制工作状态
```

## 目录结构

```
infra/
├── gitea-data-protection.sh           # 主管理脚本
├── backup/gitea/                      # 备份文件存储
│   ├── gitea-20240824-120000.tar.gz  # 备份文件
│   ├── gitea-20240824-120000.meta    # 备份元数据
│   └── safety-backup-*.tar.gz        # 恢复前安全备份
├── data-protection/gitea/             # 保护机制配置
│   ├── protection-config.yaml        # 保护配置
│   ├── realtime-sync/                # 实时同步目录
│   ├── sync-daemon.sh                # 同步守护进程
│   └── sync-daemon.pid               # 守护进程 PID
├── scripts/
│   └── gitea-auto-backup.sh          # 自动备份脚本
└── logs/
    └── gitea-protection.log           # 保护日志
```

## 多层保护机制

### 第1层：Docker 数据卷持久化
- 使用命名卷 `gitea-data` 存储所有 Gitea 数据
- 卷生命周期独立于容器，重启不丢失

### 第2层：定时自动备份
- Cron 任务每6小时自动备份
- 完整的数据卷快照，包含所有仓库和配置
- 备份前停止服务确保数据一致性

### 第3层：实时数据同步
- 守护进程每5分钟同步数据变更
- 本地文件系统镜像，可直接访问
- 即使备份丢失也能快速恢复

### 第4层：恢复前安全备份
- 每次恢复前自动创建当前状态备份
- 防止恢复操作意外损坏现有数据
- 提供恢复操作的"后悔药"

## 故障恢复场景

### 场景1: 容器重启后数据丢失
```bash
# 检查数据卷状态
./gitea-data-protection.sh health

# 如果数据卷完好，直接重启服务
./gitea-data-protection.sh start

# 如果数据卷损坏，恢复最新备份
./gitea-data-protection.sh restore
```

### 场景2: 误操作删除仓库
```bash
# 查看可用备份时间点
ls -la backup/gitea/

# 恢复到误操作前的备份
./gitea-data-protection.sh restore gitea-20240824-100000.tar.gz
```

### 场景3: 系统完全重装
```bash
# 重新部署基础环境
docker-compose -f docker/compose/gitea-compose.yml up -d

# 恢复数据（自动创建卷并恢复）
./gitea-data-protection.sh restore <backup-file>

# 重新初始化保护机制
./gitea-data-protection.sh auto-setup
```

## 监控和维护

### 日志监控
```bash
# 查看保护日志
tail -f logs/gitea-protection.log

# 查看 Gitea 服务日志
docker-compose -f docker/compose/gitea-compose.yml logs -f gitea
```

### 存储管理
```bash
# 查看备份占用空间
du -sh backup/gitea/

# 手动清理旧备份（超过30天）
find backup/gitea/ -name "gitea-*.tar.gz" -mtime +30 -delete
```

### 定时任务管理
```bash
# 查看当前定时任务
crontab -l | grep gitea

# 临时禁用自动备份
crontab -l | grep -v gitea-auto-backup | crontab -

# 重新启用自动备份
./gitea-data-protection.sh auto-setup
```

## 高级配置

### 自定义备份间隔
编辑 `data-protection/gitea/protection-config.yaml`:
```yaml
settings:
  backup_interval_hours: 4  # 改为4小时一次
```

重新运行: `./gitea-data-protection.sh auto-setup`

### 自定义同步间隔
编辑 `data-protection/gitea/sync-daemon.sh` 中的 `sleep 300` 改为其他秒数。

### 远程备份
可在备份脚本基础上添加 rsync 或 scp 命令，将备份同步到远程服务器：

```bash
# 在 backup() 函数末尾添加
rsync -av "${BACKUP_PATH}" user@remote-server:/path/to/remote/backup/
```

## 最佳实践

1. **定期验证**: 每月验证一次备份恢复流程
2. **监控空间**: 定期检查备份目录磁盘空间
3. **测试恢复**: 在测试环境验证恢复流程
4. **多地备份**: 考虑将备份同步到远程位置
5. **文档更新**: 记录重要的配置变更和恢复操作

## 故障排除

### 备份失败
```bash
# 检查 Docker 服务状态
docker system df
docker volume ls

# 检查磁盘空间
df -h

# 查看详细错误日志
tail -50 logs/gitea-protection.log
```

### 恢复失败
```bash
# 检查备份文件完整性
tar -tzf backup/gitea/backup-file.tar.gz

# 手动验证数据卷
docker run --rm -v gitea-data:/data busybox ls -la /data
```

### 同步守护进程异常
```bash
# 检查进程状态
ps aux | grep sync-daemon

# 重启同步守护进程
./gitea-data-protection.sh stop
./gitea-data-protection.sh start
```