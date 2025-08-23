# Mac Studio M2 企业级 CI/CD 体系实施方案

## 一、环境信息
- 服务器：Mac Studio M2
- Docker环境：OrbStack
- Git服务：Gitea
- 镜像仓库：Registry
- 操作系统：macOS 24.5.0

## 二、目录结构
```bash
/Users/brunogao/work/infra/
├── cicd/                    # CI/CD相关配置
│   ├── drone/              # Drone CI配置
│   │   ├── config/        # Drone配置文件
│   │   └── scripts/       # 安装脚本
│   └── pipelines/         # CI/CD流水线模板
├── docker/                 # Docker相关配置
│   ├── registry/          # Registry配置
│   └── compose/           # Docker Compose文件
├── deployment/            # 部署相关
│   ├── scripts/          # 部署脚本
│   └── templates/        # 部署模板
├── monitoring/            # 监控配置（预留）
├── docs/                  # 文档
└── README.md             # 项目说明
```

## 三、实施步骤

### 1. 基础环境准备
#### 1.1 OrbStack配置
- [ ] 确认OrbStack安装状态
- [ ] 配置资源限制
- [ ] 配置网络设置
```bash
# 检查OrbStack状态
orb ps
# 配置资源
orb settings
```

#### 1.2 Gitea配置
- [ ] 确认Gitea运行状态
- [ ] 配置Webhook设置
- [ ] 创建CI/CD专用账号
```bash
# 启动Gitea（如果使用OrbStack）
orb start gitea
# 配置Gitea
gitea admin create-user --username=cicd --password=<secure_password> --email=cicd@example.com
```

#### 1.3 Registry配置
- [ ] 确认Registry运行状态
- [ ] 配置认证
- [ ] 配置存储
```bash
# 配置Registry认证
htpasswd -Bbn admin <password> > auth/htpasswd
# 启动Registry
docker compose up -d registry
```

### 2. CI/CD环境搭建
#### 2.1 Drone CI安装
- [ ] 安装Drone Server
- [ ] 安装Drone Runner
- [ ] 配置Gitea集成
```bash
# 创建Drone配置
mkdir -p /Users/brunogao/work/infra/cicd/drone/config
# 配置Drone环境变量
export DRONE_GITEA_SERVER=http://gitea:3000
export DRONE_GIT_ALWAYS_AUTH=true
export DRONE_RUNNER_CAPACITY=2
```

#### 2.2 流水线配置
- [ ] 创建基础流水线模板
- [ ] 配置构建步骤
- [ ] 配置测试步骤
- [ ] 配置镜像推送步骤

### 3. 自动化流程配置
#### 3.1 代码提交触发
- [ ] 配置Gitea Webhook
- [ ] 测试自动触发
- [ ] 配置分支规则

#### 3.2 自动化测试
- [ ] 配置单元测试
- [ ] 配置集成测试
- [ ] 配置测试报告生成

#### 3.3 镜像构建和推送
- [ ] 配置镜像构建流程
- [ ] 配置镜像标签规则
- [ ] 配置推送认证

### 4. 部署流程
#### 4.1 基础部署脚本
- [ ] 创建部署脚本
- [ ] 配置环境变量
- [ ] 配置回滚机制

## 四、配置文件模板

### 4.1 Drone CI配置（.drone.yml）
```yaml
kind: pipeline
type: docker
name: default

steps:
  - name: test
    image: python:3.10
    commands:
      - pip install -r requirements.txt
      - pytest

  - name: build
    image: plugins/docker
    settings:
      registry: localhost:5000
      repo: localhost:5000/myapp
      tags: ${DRONE_COMMIT_SHA:0:8}
```

### 4.2 Registry配置（docker-compose.yml）
```yaml
version: '3'
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - ./auth:/auth
      - ./data:/var/lib/registry
    environment:
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: Registry
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
```

## 五、问题排查指南

### 5.1 CI/CD执行问题
- 检查Webhook配置
- 检查Drone日志
- 检查网络连接
- 检查权限设置

### 5.2 镜像构建问题
- 检查Docker配置
- 检查Registry连接
- 检查存储空间
- 检查认证配置

## 六、维护计划

### 6.1 日常维护
- 定期检查日志
- 清理旧镜像
- 更新配置文件
- 备份重要数据

### 6.2 更新计划
- 定期更新基础镜像
- 更新依赖版本
- 优化构建流程
- 改进部署策略

## 七、安全考虑

### 7.1 访问控制
- 使用HTTPS
- 配置防火墙
- 实施最小权限
- 定期轮换密钥

### 7.2 数据安全
- 配置备份策略
- 加密敏感数据
- 监控异常访问
- 定期安全审计

## 八、扩展计划（预留）

### 8.1 监控系统
- Prometheus配置
- Grafana部署
- 告警规则设置

### 8.2 Kubernetes集成
- 集群配置
- 部署策略
- 服务发现

## 九、文档维护

### 9.1 操作文档
- 环境搭建文档
- 故障排除指南
- 最佳实践指南

### 9.2 更新记录
- 版本变更记录
- 配置修改记录
- 问题解决记录 