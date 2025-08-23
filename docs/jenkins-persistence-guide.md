# Jenkins 完整持久化指南

## 🎯 持久化目标

确保Jenkins的以下数据完全持久化，不会因容器重启或重建而丢失：
- ✅ **配置文件**: config.xml, credentials.xml等
- ✅ **插件数据**: 所有已安装插件及其配置
- ✅ **作业定义**: 所有Jenkins作业的配置
- ✅ **构建历史**: 构建记录和制品
- ✅ **用户数据**: 用户账号和权限设置
- ✅ **凭据信息**: API密钥、SSH密钥等敏感信息
- ✅ **系统设置**: 全局配置和工具设置

## 📁 持久化架构

### 目录结构
```
/Users/brunogao/work/infra/
├── data/jenkins/                    # Jenkins主数据目录
│   ├── home/                       # Jenkins核心配置
│   ├── workspace/                  # 构建工作空间
│   ├── jobs/                       # 作业配置
│   ├── builds/                     # 构建历史
│   ├── plugins/                    # 插件数据
│   ├── secrets/                    # 凭据和密钥
│   ├── users/                      # 用户数据
│   ├── logs/                       # 日志文件
│   ├── cache/                      # 缓存数据
│   └── tmp/                        # 临时文件
├── backup/jenkins/                  # 备份存储
│   ├── full/                       # 完整备份
│   ├── incremental/                # 增量备份
│   └── config/                     # 配置备份
└── docker/compose/jenkins/         # 配置文件
    ├── casc/                       # Configuration as Code
    ├── init-scripts/               # 初始化脚本
    └── plugins.txt                 # 插件列表
```

### 数据卷映射
```yaml
services:
  jenkins:
    volumes:
      # 核心数据持久化
      - jenkins-home:/var/jenkins_home
      - jenkins-workspace:/var/jenkins_home/workspace
      - jenkins-jobs:/var/jenkins_home/jobs
      - jenkins-builds:/var/jenkins_home/builds
      - jenkins-plugins:/var/jenkins_home/plugins
      - jenkins-secrets:/var/jenkins_home/secrets
      - jenkins-users:/var/jenkins_home/users
      - jenkins-logs:/var/jenkins_home/logs
      
      # 配置文件持久化
      - ./jenkins/casc:/var/jenkins_home/casc_configs:ro
      - ./jenkins/init-scripts:/usr/share/jenkins/ref/init.groovy.d:ro
      - ./jenkins/plugins.txt:/usr/share/jenkins/ref/plugins.txt:ro
      
      # 扩展数据
      - jenkins-backup:/var/jenkins_backup
      - jenkins-cache:/var/jenkins_home/.cache
      - jenkins-tmp:/var/jenkins_home/tmp
```

## 🚀 部署持久化Jenkins

### 1. 使用持久化配置启动
```bash
# 使用持久化管理脚本
./jenkins-persistence-manager.sh init     # 初始化环境
./jenkins-persistence-manager.sh start    # 启动持久化Jenkins

# 或直接使用docker-compose
cd docker/compose
docker-compose -f jenkins-persistent.yml up -d
```

### 2. 验证持久化配置
```bash
# 检查数据目录
ls -la data/jenkins/

# 验证数据完整性
./jenkins-persistence-manager.sh verify

# 查看存储使用
./jenkins-persistence-manager.sh storage
```

## 💾 备份策略

### 自动备份
Jenkins持久化方案包含三种自动备份：

#### 1. 完整备份（每周）
- **频率**: 每周日凌晨2点
- **内容**: 所有Jenkins数据和配置
- **保留**: 最近10个备份
- **位置**: `backup/jenkins/full/`

#### 2. 增量备份（每日）
- **频率**: 每日（除周日外）
- **内容**: 自上次备份后修改的文件
- **保留**: 最近30个备份
- **位置**: `backup/jenkins/incremental/`

#### 3. 配置备份（每日）
- **频率**: 每日
- **内容**: 配置文件和凭据
- **保留**: 最近20个备份
- **位置**: `backup/jenkins/config/`

### 手动备份
```bash
# 完整备份
./jenkins-persistence-manager.sh full-backup

# 增量备份
./jenkins-persistence-manager.sh incremental-backup

# 配置备份
./jenkins-persistence-manager.sh config-backup
```

### 设置自动备份
```bash
# 配置自动备份任务
./jenkins-persistence-manager.sh auto-backup

# 查看备份日志
tail -f backup/backup.log
```

## 🔄 数据恢复

### 从备份恢复
```bash
# 列出可用备份并选择恢复
./jenkins-persistence-manager.sh restore

# 示例恢复命令
./jenkins-persistence-manager.sh restore /path/to/backup.tar.gz
```

### 数据迁移
```bash
# 从旧Jenkins实例迁移
./jenkins-persistence-manager.sh migrate

# 选择迁移源：
# 1. 从旧Jenkins容器迁移
# 2. 从Docker卷迁移  
# 3. 从目录迁移
```

## ⚙️ Configuration as Code (CasC)

Jenkins使用CasC实现配置即代码，确保配置的版本控制和重现性。

### 主配置文件
- `docker/compose/jenkins/casc/jenkins.yaml` - 基础配置
- `docker/compose/jenkins/casc/persistence.yaml` - 持久化专用配置

### 配置内容
```yaml
jenkins:
  # 构建历史保留策略
  buildDiscarders:
    - buildDiscarder:
        strategy:
          logRotator:
            daysToKeepStr: "30"        # 保留30天
            numToKeepStr: "50"         # 保留50次构建
            artifactDaysToKeepStr: "7" # 制品保留7天
            artifactNumToKeepStr: "10" # 制品保留10个

# 工作空间清理
unclassified:
  workspaceCleanupPlugin:
    deleteDirectories: true
    cleanWhenAborted: true
    cleanWhenFailure: true
    cleanWhenSuccess: true
```

### 配置更新
修改CasC配置后，重启Jenkins即可生效：
```bash
./jenkins-persistence-manager.sh start
```

## 🔍 监控与维护

### 预置监控作业
持久化配置自动创建以下监控作业：

1. **jenkins-data-backup** - 数据备份作业
   - 每周日执行完整备份
   - 自动清理旧备份
   - 邮件通知备份结果

2. **cleanup-disk-space** - 磁盘清理作业
   - 每日执行
   - 清理旧工作空间、临时文件、日志
   - 显示清理前后磁盘使用情况

3. **system-health-monitor** - 健康监控作业
   - 每30分钟执行
   - 监控磁盘使用率、内存使用
   - 检查关键文件完整性
   - 验证备份状态

### 手动维护
```bash
# 查看存储使用情况
./jenkins-persistence-manager.sh storage

# 清理旧备份
./jenkins-persistence-manager.sh cleanup

# 数据完整性验证
./jenkins-persistence-manager.sh verify
```

## 📊 数据保留策略

### 构建数据
- **构建历史**: 保留30天或最近50次构建
- **构建制品**: 保留7天或最近10个制品
- **工作空间**: 7天后自动清理
- **日志文件**: 保留30天

### 备份数据
- **完整备份**: 保留10个（约10周）
- **增量备份**: 保留30个（约30天）
- **配置备份**: 保留20个（约20天）

### 清理策略
- **自动清理**: 每日凌晨3点执行
- **手动清理**: 使用管理脚本
- **备份清理**: 自动删除过期备份

## 🔐 安全考虑

### 数据安全
- 敏感数据存储在`secrets/`目录
- 凭据信息加密存储
- 备份文件可选加密
- 文件权限正确设置(1000:1000)

### 访问控制
- Jenkins用户隔离
- 目录权限限制
- 网络访问控制
- API访问限制

## 🚨 故障恢复

### 常见故障场景
1. **容器意外停止**: 数据完整保留，重启即可
2. **配置损坏**: 从配置备份快速恢复
3. **数据丢失**: 从完整备份恢复
4. **磁盘空间不足**: 自动清理和告警

### 紧急恢复步骤
```bash
# 1. 停止损坏的Jenkins
docker stop jenkins-persistent

# 2. 查看可用备份
ls -la backup/jenkins/full/

# 3. 恢复数据
./jenkins-persistence-manager.sh restore [backup-file]

# 4. 重启Jenkins
./jenkins-persistence-manager.sh start

# 5. 验证恢复
./jenkins-persistence-manager.sh verify
```

## 📈 性能优化

### 存储优化
- 分离不同类型数据到不同卷
- 定期清理临时文件和缓存
- 工作空间自动清理
- 构建历史合理保留

### 内存优化
- JVM参数调优: `-Xmx2g -Xms1g`
- G1垃圾收集器: `-XX:+UseG1GC`
- GC暂停时间控制: `-XX:MaxGCPauseMillis=200`

### I/O优化
- 使用SSD存储
- 合理的卷映射策略
- 缓存目录分离
- 日志轮转配置

## 🎉 最佳实践

1. **定期备份验证**: 每月验证备份可用性
2. **监控磁盘使用**: 设置使用率告警
3. **配置版本控制**: CasC配置纳入Git管理
4. **文档及时更新**: 记录配置变更
5. **权限最小化**: 只授予必要权限
6. **安全更新**: 定期更新Jenkins和插件

## 🔧 管理命令速查

```bash
# 环境管理
./jenkins-persistence-manager.sh init      # 初始化
./jenkins-persistence-manager.sh start     # 启动
./jenkins-persistence-manager.sh verify    # 验证

# 备份管理
./jenkins-persistence-manager.sh full-backup      # 完整备份
./jenkins-persistence-manager.sh incremental-backup # 增量备份
./jenkins-persistence-manager.sh config-backup    # 配置备份
./jenkins-persistence-manager.sh restore          # 恢复

# 维护管理
./jenkins-persistence-manager.sh storage    # 存储使用
./jenkins-persistence-manager.sh cleanup    # 清理备份
./jenkins-persistence-manager.sh auto-backup # 设置自动备份
./jenkins-persistence-manager.sh migrate    # 数据迁移
```

通过以上完整的持久化方案，Jenkins的所有重要数据都得到了可靠的持久化保护，确保在任何情况下都不会丢失关键的配置、作业和构建数据。 