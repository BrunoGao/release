# 客户现场部署指南

## 概述

本指南适用于客户现场使用预构建Docker镜像进行系统部署，无需源代码编译，快速完成定制化部署。

## 部署包内容

客户部署包应包含以下文件：

```
ljwx-client-deployment/
├── docker-compose-client.yml    # 客户部署Docker编排文件
├── deploy-client.sh             # 一键部署脚本
├── quick-start.sh               # 快速启动脚本
├── custom-config.env            # 主配置文件
├── customer-example.env         # 客户配置示例
├── custom-config.py             # Python配置文件(可选)
├── custom-admin-config.js       # 前端配置文件(可选)
├── custom-assets/               # 自定义资源目录
├── client-data.sql.example      # 客户数据示例
├── data.sql                     # 内置数据库初始化脚本
└── CLIENT_DEPLOYMENT_GUIDE.md   # 本部署指南
```

## 系统要求

### 硬件要求
- **CPU**: 16核心以上 (推荐32核心)
- **内存**: 32GB以上 (推荐64GB)
- **磁盘**: 1TB以上可用空间 (推荐2TB SSD)
- **网络**: 千兆网络，稳定的互联网连接(用于拉取镜像)

### 软件要求
- 操作系统: Linux(推荐CentOS 8+/Ubuntu 20.04+)/macOS/Windows
- Docker: 24.0+
- Docker Compose: 2.20+

## 快速部署

### 1. 环境准备

#### 安装Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# CentOS/RHEL 8+
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker

# macOS - 安装Docker Desktop
# Windows - 安装Docker Desktop with WSL2
```

#### 验证安装
```bash
docker --version
docker compose version
```

### 2. 配置定制化参数

#### 复制并编辑主配置文件
```bash
cp custom-config.env client-config.env
vim client-config.env
```

#### 核心配置说明

##### 数据库配置 (MySQL)
```bash
# MySQL 数据库配置
MYSQL_ROOT_PASSWORD=您的安全密码           # 必须修改，建议16位以上复杂密码
MYSQL_DATABASE=lj-05                       # 数据库名称，可自定义
MYSQL_USER=ljwx_user                       # 应用用户名，可自定义
MYSQL_PASSWORD=您的应用密码                # 应用密码，必须修改

# MySQL 性能配置
MYSQL_INNODB_BUFFER_POOL_SIZE=16G         # InnoDB缓冲池大小，建议为内存的50-70%
MYSQL_MAX_CONNECTIONS=1000                # 最大连接数
MYSQL_QUERY_CACHE_SIZE=256M               # 查询缓存大小
MYSQL_TABLE_OPEN_CACHE=4000               # 表缓存数量

# MySQL 数据目录
MYSQL_DATA_DIR=/var/lib/mysql             # 数据存储目录
MYSQL_LOG_DIR=/var/log/mysql              # 日志目录
```

##### Redis配置
```bash
# Redis 缓存配置
REDIS_PASSWORD=您的Redis密码              # 必须修改，建议16位以上
REDIS_PORT=6379                           # Redis端口，默认6379
REDIS_MAXMEMORY=8gb                       # 最大内存使用，建议设置为物理内存的20-30%
REDIS_MAXMEMORY_POLICY=allkeys-lru        # 内存回收策略

# Redis 性能配置
REDIS_SAVE_INTERVAL=900 1                 # 持久化配置：900秒内至少1个键改变则保存
REDIS_DATABASES=16                        # 数据库数量
REDIS_TIMEOUT=300                         # 客户端超时时间(秒)
REDIS_TCP_KEEPALIVE=300                   # TCP keepalive时间

# Redis 集群配置(可选)
REDIS_CLUSTER_ENABLED=no                  # 是否启用集群模式
REDIS_CLUSTER_NODES=3                     # 集群节点数量
```





##### 应用配置
```bash
# 应用标题定制
BIGSCREEN_TITLE=客户大屏标题               # 大屏显示标题
VITE_APP_TITLE=客户管理系统                # 管理端标题
COMPANY_NAME=客户公司名称                  # 公司名称
FOOTERTEXT=© 2025 客户公司 版权所有        # 页脚信息

# 主题配色
THEME_COLOR=#1890ff                       # 主题色，支持十六进制颜色

# 网络配置
VITE_BIGSCREEN_URL=http://您的域名:8001    # 大屏访问地址
ADMIN_PORT=8080                           # 管理端端口
BIGSCREEN_PORT=8001                       # 大屏端口
LJWX_BOOT_PORT=9998                       # API服务端口

# 应用性能配置
JVM_OPTS=-Xms2g -Xmx8g -XX:+UseG1GC      # Java应用JVM参数
BIGSCREEN_WORKERS=8                       # Python应用工作进程数
LOG_LEVEL=info                            # 日志级别
```

##### 监控配置
```bash
# Prometheus 监控
PROMETHEUS_PORT=9090
PROMETHEUS_RETENTION_TIME=30d             # 数据保留时间

# Grafana 可视化
GRAFANA_PORT=3000
GRAFANA_PASSWORD=您的Grafana密码          # 必须修改

# 告警配置
ALERTMANAGER_PORT=9093
WECHAT_ALERT_ENABLED=true                 # 启用微信告警
WECHAT_API_URL=您的微信API地址            # 微信API接口
WECHAT_TEMPLATE_ID=您的模板ID             # 微信消息模板
```

### 3. 高级配置

#### 自定义前端配置
```bash
# 编辑前端配置文件
vim custom-admin-config.js
```

```javascript
window.CUSTOM_CONFIG = {
  // 应用标题
  appTitle: '客户管理平台',
  
  // 应用描述
  appDesc: '智能穿戴管理平台',
  
  // 大屏访问地址
  bigscreenUrl: 'http://您的域名:8001',
  
  // 主题配色
  themeColor: '#1890ff',
  
  // 公司信息
  companyName: '客户公司名称',
  
  // 页脚信息
  footerText: '© 2025 客户公司 版权所有'
};
```

#### 自定义Python配置
```bash
# 编辑Python配置文件
vim custom-config.py
```

```python
# 客户定制配置
COMPANY_NAME = "客户公司名称"
SYSTEM_TITLE = "客户大屏标题"

# 数据库连接配置
DATABASE_CONFIG = {
    'host': 'ljwx-mysql',
    'port': 3306,
    'user': 'ljwx_user',
    'password': '您的应用密码',
    'database': 'lj-05',
    'charset': 'utf8mb4'
}

# Redis连接配置
REDIS_CONFIG = {
    'host': 'ljwx-redis',
    'port': 6379,
    'password': '您的Redis密码',
    'db': 0,
    'decode_responses': True
}

# 业务配置
ALERT_CONFIG = {
    'enabled': True,
    'wechat_api': '您的微信API地址',
    'template_id': '您的模板ID'
}
```

### 4. 客户数据配置

#### 准备客户数据(可选)
```bash
# 复制数据示例
cp client-data.sql.example client-data.sql

# 编辑客户数据
vim client-data.sql
```

客户数据格式示例：
```sql
-- 健康数据
INSERT INTO t_user_health_data (device_sn, user_id, org_id, heart_rate, blood_oxygen, temperature, created_time) VALUES
('CLIENT001', 1, 1, 75, 98, 36.6, NOW()),
('CLIENT002', 2, 1, 80, 97, 36.5, NOW());

-- 设备信息
INSERT INTO t_device_info (device_sn, user_id, org_id, device_name, device_type, status) VALUES
('CLIENT001', 1, 1, '客户设备001', 'SMARTWATCH', 1),
('CLIENT002', 2, 1, '客户设备002', 'SMARTWATCH', 1);

-- 用户信息
INSERT INTO t_user_info (user_id, user_name, org_id, phone, email, age, gender) VALUES
(1, '张三', 1, '13800138001', 'zhangsan@client.com', 30, 1),
(2, '李四', 1, '13800138002', 'lisi@client.com', 25, 0);
```

### 5. 一键部署

#### 使用默认配置快速启动
```bash
# 使用内置数据，快速演示
./quick-start.sh
```

#### 使用客户配置部署
```bash
# 使用客户定制配置
./deploy-client.sh client-config.env
```

#### 部署过程
部署脚本将自动执行：
1. ✅ 检查系统环境和依赖
2. ✅ 验证配置文件语法
3. ✅ 拉取最新镜像版本
4. ✅ 初始化数据卷和网络
5. ✅ 启动所有服务容器
6. ✅ 执行健康状态检查
7. ✅ 显示访问地址和状态

### 6. 验证部署

部署完成后访问：
- **管理端**: http://localhost:8080 (或您配置的域名和端口)
- **大屏端**: http://localhost:8001 (或您配置的域名和端口)
- **API接口**: http://localhost:9998/doc.html (Swagger文档)
- **监控面板**: http://localhost:3000 (Grafana，admin/您配置的密码)

默认登录账号：`admin` / `123456`

## 生产环境优化

### 域名和SSL配置

#### 配置域名
```bash
# 修改配置文件
VITE_BIGSCREEN_URL=https://bigscreen.客户域名.com
ADMIN_DOMAIN=admin.客户域名.com
API_DOMAIN=api.客户域名.com
```

#### SSL证书配置
```yaml
# 在docker-compose-client.yml中添加SSL
volumes:
  - ./ssl/cert.pem:/etc/nginx/ssl/cert.pem:ro
  - ./ssl/key.pem:/etc/nginx/ssl/key.pem:ro
```

### 负载均衡配置

```yaml
# 多实例部署
deploy:
  replicas: 3
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '1.0'
```

### 数据库优化

```bash
# MySQL 生产配置
MYSQL_INNODB_BUFFER_POOL_SIZE=24G         # 设置为内存的60-70%
MYSQL_INNODB_LOG_FILE_SIZE=2G             # 事务日志大小
MYSQL_MAX_CONNECTIONS=2000                # 根据并发需求调整
MYSQL_QUERY_CACHE_SIZE=512M               # 查询缓存
MYSQL_THREAD_CACHE_SIZE=64                # 线程缓存
```

## 运维管理

### 服务管理命令

```bash
# 查看服务状态
docker compose -f docker-compose-client.yml ps

# 查看实时日志
docker compose -f docker-compose-client.yml logs -f --tail=100

# 查看特定服务日志
docker compose -f docker-compose-client.yml logs ljwx-boot
docker compose -f docker-compose-client.yml logs ljwx-admin
docker compose -f docker-compose-client.yml logs ljwx-bigscreen

# 重启特定服务
docker compose -f docker-compose-client.yml restart ljwx-admin

# 停止所有服务
docker compose -f docker-compose-client.yml down

# 更新镜像并重启
docker compose -f docker-compose-client.yml pull
docker compose -f docker-compose-client.yml up -d
```

### 数据备份和恢复

#### 数据库备份
```bash
# 自动备份脚本
cat > backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec ljwx-mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD $MYSQL_DATABASE > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/backup_$DATE.sql

# 清理7天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "数据库备份完成: backup_$DATE.sql.gz"
EOF

chmod +x backup-db.sh

# 设置定时备份
crontab -e
# 添加: 0 2 * * * /path/to/backup-db.sh
```

#### Redis备份
```bash
# Redis数据备份
docker exec ljwx-redis redis-cli --rdb /backup/redis/dump_$(date +%Y%m%d_%H%M%S).rdb
```

#### 配置文件备份
```bash
# 备份所有配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  custom-config.env \
  client-config.env \
  custom-config.py \
  custom-admin-config.js \
  custom-assets/
```

### 监控和告警

#### Grafana监控面板
- 访问: http://localhost:3000
- 账号: admin / 您配置的密码
- 内置面板:
  - 系统概览面板
  - 应用性能面板
  - 数据库监控面板
  - Redis监控面板

#### 告警配置
```bash
# 配置微信告警
WECHAT_ALERT_ENABLED=true
WECHAT_API_URL=您的企业微信机器人地址
WECHAT_TEMPLATE_ID=您的消息模板ID

# 告警规则
- 服务宕机告警
- CPU使用率超过80%告警
- 内存使用率超过85%告警  
- 磁盘使用率超过90%告警
- 数据库连接数告警
```

## 故障排除

### 常见问题

#### 1. 镜像拉取失败
```bash
# 检查网络连接
ping registry.cn-hangzhou.aliyuncs.com

# 配置镜像加速器
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.cn-hangzhou.aliyuncs.com"
  ]
}
EOF
sudo systemctl restart docker

# 手动拉取镜像
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-boot:latest
```

#### 2. 端口冲突
```bash
# 检查端口占用
ss -tlnp | grep :8080
ss -tlnp | grep :8001
ss -tlnp | grep :9998

# 修改端口配置
vim client-config.env
# 修改ADMIN_PORT、BIGSCREEN_PORT、LJWX_BOOT_PORT
```

#### 3. 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 调整JVM内存
vim client-config.env
# 修改JVM_OPTS=-Xms1g -Xmx4g
```

#### 4. 数据库连接失败
```bash
# 检查MySQL服务
docker compose -f docker-compose-client.yml logs ljwx-mysql

# 测试数据库连接
docker compose -f docker-compose-client.yml exec ljwx-mysql mysql -u root -p$MYSQL_ROOT_PASSWORD

# 重置数据库
docker compose -f docker-compose-client.yml down
docker volume rm ljwx-client_mysql_data
docker compose -f docker-compose-client.yml up -d
```

### 性能优化

#### 系统级优化
```bash
# 调整系统参数
echo 'vm.max_map_count = 262144' >> /etc/sysctl.conf
echo 'fs.file-max = 65536' >> /etc/sysctl.conf
sysctl -p

# 调整Docker配置
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
```

#### 应用级优化
```bash
# MySQL优化
MYSQL_INNODB_BUFFER_POOL_SIZE=24G
MYSQL_INNODB_LOG_BUFFER_SIZE=64M
MYSQL_KEY_BUFFER_SIZE=256M

# Redis优化  
REDIS_MAXMEMORY=16gb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

### 磁盘清理
```bash
# 清理Docker资源
docker system prune -af
docker volume prune -f

# 清理日志文件
find /var/log -name "*.log" -mtime +7 -delete
```

## 技术支持

### 联系方式
- 技术支持邮箱: support@ljwx.com
- 技术支持电话: 400-xxx-xxxx
- 在线文档: https://docs.ljwx.com

### 问题反馈
提交问题时请提供：
1. 系统环境信息 (`uname -a`, `docker version`)
2. 完整错误日志
3. 配置文件内容(脱敏后)
4. 详细复现步骤

### 版本更新
```bash
# 检查最新版本
docker compose -f docker-compose-client.yml pull

# 平滑更新
./deploy-client.sh client-config.env
``` 