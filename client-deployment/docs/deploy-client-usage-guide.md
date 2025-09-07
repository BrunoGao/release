# 智能穿戴系统客户现场部署使用说明

## 概述

`deploy-client.sh` 是智能穿戴系统的客户现场部署脚本，支持使用预构建镜像进行快速部署，采用Docker命名卷实现数据持久化。该脚本提供完整的自动化部署流程，包括配置验证、镜像管理、服务启动、定制化配置等功能。

## 核心特性

- ✅ **智能部署模式**: 支持在线/离线两种部署模式
- ✅ **数据持久化**: 使用Docker命名卷确保数据安全
- ✅ **配置验证**: 自动验证配置文件一致性
- ✅ **智能备份**: 升级前自动备份现有数据
- ✅ **定制化支持**: 自动应用客户定制配置
- ✅ **健康检查**: 完整的服务启动状态监控
- ✅ **跨平台兼容**: 支持CentOS等多种Linux发行版

## 系统架构

### 服务组件
- **ljwx-mysql**: 数据库服务 (端口: 3306)
- **ljwx-redis**: 缓存服务 (端口: 6379)  
- **ljwx-boot**: 后端API服务 (端口: 9998)
- **ljwx-bigscreen**: 数据大屏服务 (端口: 8001)
- **ljwx-admin**: 管理端服务 (端口: 8088)

### 数据持久化
- `client-deployment_mysql_data`: MySQL数据卷
- `client-deployment_redis_data`: Redis数据卷
- `client-deployment_ljwx_boot_data`: 后端数据卷
- `client-deployment_ljwx_bigscreen_data`: 大屏数据卷

## 使用方法

### 基本语法
```bash
./deploy-client.sh [配置文件名] [offline]
```

### 部署模式

#### 在线部署 (推荐)
```bash
# 使用默认配置文件
./deploy-client.sh

# 使用指定配置文件
./deploy-client.sh my-config.env
```

#### 离线部署
```bash
# 离线模式 + 默认配置
./deploy-client.sh offline

# 离线模式 + 指定配置
./deploy-client.sh my-config.env offline
```

## 部署前准备

### 1. 环境要求
- Docker Engine (已安装并运行)
- docker-compose (已安装)
- 网络连接 (在线模式需要)

### 2. 必需文件检查
```
client-deployment/
├── deploy-client.sh           # 主部署脚本
├── custom-config.env          # 配置文件
├── custom-config.py           # Python自定义配置
├── custom-admin-config.js     # 前端自定义配置
├── docker-compose.yml         # Docker编排文件
├── client-data.sql           # 客户数据(首次部署)
└── custom-assets/            # 自定义资源目录
    └── logo.svg              # 自定义logo文件
```

### 3. 配置文件准备

复制并编辑配置文件：
```bash
cp custom-config.env my-client-config.env
```

关键配置项：
```env
# 服务器地址
SERVER_IP=192.168.1.83

# 端口配置
LJWX_ADMIN_EXTERNAL_PORT=8088
LJWX_BIGSCREEN_EXTERNAL_PORT=8001
LJWX_BOOT_EXTERNAL_PORT=9998

# 定制化配置
VITE_APP_TITLE=客户定制管理平台
BIGSCREEN_TITLE=客户数据大屏
COMPANY_NAME=客户公司名称
VITE_CUSTOM_LOGO=true

# 镜像版本
LJWX_ADMIN_VERSION=2.0.1
LJWX_BIGSCREEN_VERSION=2.0.1
LJWX_BOOT_VERSION=2.0.1
```

## 部署流程详解

### 第一阶段：环境检查与配置验证
1. **系统兼容性检查**: 自动检测CentOS并处理文件格式
2. **依赖检查**: 验证Docker和docker-compose安装
3. **配置文件验证**: 加载并验证配置文件格式
4. **必需文件检查**: 确认所有必需的配置文件存在

### 第二阶段：数据策略选择
根据现有数据卷情况自动判断部署类型：

#### 首次部署
- 创建新的Docker命名卷
- 使用 `client-data.sql` 进行数据初始化
- 无需备份操作

#### 升级部署
- 检测现有命名卷
- 提供备份策略选择：
  1. **在线备份**: 完整SQL导出 (推荐)
  2. **离线卷备份**: 直接备份Docker卷
  3. **跳过备份**: 风险自担
  4. **退出部署**: 手动处理

### 第三阶段：镜像管理
1. **镜像版本检查**: 验证配置文件中的镜像版本
2. **本地镜像检查**: 扫描本地已有镜像
3. **镜像拉取策略**:
   - 在线模式：自动登录阿里云镜像仓库并拉取缺失镜像
   - 离线模式：仅使用本地镜像，缺失时给出警告

### 第四阶段：服务部署
1. **数据初始化配置**: 首次部署时动态添加数据初始化挂载
2. **容器清理**: 清理可能冲突的旧容器
3. **目录权限设置**: 确保日志和备份目录权限正确
4. **服务启动**: 根据部署模式启动所有服务
5. **启动等待**: 等待服务完全启动

### 第五阶段：健康检查
对每个服务进行健康状态验证：
- **ljwx-boot**: 检查 `/actuator/health` 端点
- **ljwx-bigscreen**: 检查 `/health` 端点  
- **ljwx-admin**: 检查首页访问
- 超时时间：每个服务120秒

### 第六阶段：定制化配置
1. **大屏URL更新**: 替换前端中的大屏访问地址
2. **浏览器缓存清理**: 清除可能的缓存问题
3. **自定义Logo应用**: 
   - 检查 `VITE_CUSTOM_LOGO=true` 配置
   - 调用 `customize-admin-logo.sh` 进行logo替换
4. **挂载配置验证**: 验证容器挂载是否正确

## 定制化功能详解

### 自定义Logo功能
脚本支持自动替换管理端Logo：

1. **启用条件**: `VITE_CUSTOM_LOGO=true`
2. **支持格式**: png, jpg, jpeg, svg
3. **文件位置**: `custom-assets/logo.*` 或包含"logo"的图片文件
4. **实现机制**:
   - 复制logo文件到容器 `/usr/share/nginx/html/logo-custom.*`
   - 生成JavaScript配置文件
   - 在index.html中注入配置脚本
   - 重新加载nginx配置

### 大屏URL配置
自动更新前端应用中的大屏跳转链接：
- 读取 `VITE_BIGSCREEN_URL` 配置
- 在ljwx-admin容器中替换相关配置
- 确保管理端可正确跳转到数据大屏

## 错误处理和故障排除

### 常见问题解决

#### 1. Docker登录失败
```bash
❌ Docker登录失败，请检查用户名和密码
```
**解决方案**: 检查网络连接和镜像仓库访问权限

#### 2. 镜像拉取失败
```bash
❌ 警告: 无法拉取 xxx 镜像
```
**解决方案**: 
- 检查网络连接
- 确认镜像版本号正确
- 考虑使用离线部署模式

#### 3. 服务启动超时
```bash
⚠️ 后端服务启动超时，请检查日志
```
**解决方案**:
```bash
# 查看详细日志
docker-compose logs ljwx-boot

# 检查容器状态  
docker ps -a

# 查看文件日志
tail -f logs/ljwx-boot/*.log
```

#### 4. 端口冲突
确保以下端口未被占用：
- 3306 (MySQL)
- 6379 (Redis)  
- 9998 (后端API)
- 8001 (数据大屏)
- 8088 (管理端)

### 日志查看工具

#### 实时日志监控
```bash
# 使用内置日志查看器(推荐)
./logs-viewer.sh

# 查看特定服务日志
docker-compose logs -f ljwx-boot
docker-compose logs -f ljwx-admin

# 查看文件日志
tail -f logs/ljwx-boot/*.log
tail -f logs/mysql/slow.log
```

#### 日志目录结构
```
logs/
├── mysql/           # MySQL数据库日志
├── redis/           # Redis缓存日志
├── ljwx-boot/       # 后端服务日志
├── ljwx-bigscreen/  # 数据大屏日志
└── ljwx-admin/      # 管理端日志
```

## 部署后管理

### 服务管理命令
```bash
# 查看服务状态
docker-compose ps

# 重启特定服务
docker-compose restart ljwx-admin

# 停止所有服务(保留数据)
docker-compose down

# 完全清理(⚠️删除数据卷)
docker-compose down -v
```

### 数据备份恢复
```bash
# 在线备份(推荐)
./auto-backup.sh

# 数据恢复
./restore-backup.sh

# 跨平台备份
./auto-backup-crossplatform.sh
```

### 访问地址
部署完成后的访问地址：
- **管理端**: `http://服务器IP:8088`
- **数据大屏**: `http://服务器IP:8001`  
- **后端API**: `http://服务器IP:9998`

默认登录账号：`admin / 123456`

## 最佳实践建议

### 1. 部署前准备
- 备份现有数据和配置
- 确认服务器资源充足 (CPU: 4核, 内存: 8GB, 磁盘: 50GB)
- 准备好客户定制化资源文件

### 2. 配置管理
- 为每个客户创建独立的配置文件
- 定期备份配置文件到版本控制系统
- 记录客户特殊需求和配置变更

### 3. 运维监控
- 定期检查服务健康状态
- 监控磁盘空间使用情况
- 设置定时备份任务

### 4. 安全注意事项
- 修改默认管理员密码
- 配置防火墙规则限制端口访问
- 定期更新系统和Docker版本

## 技术支持

如在部署过程中遇到问题，请：

1. 查看详细错误日志
2. 检查系统资源使用情况  
3. 参考故障排除章节
4. 联系技术支持团队

---

**文档版本**: v2.0.1  
**更新时间**: 2025-09-06  
**适用版本**: deploy-client.sh v2.0+