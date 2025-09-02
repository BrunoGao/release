# LJWX BigScreen CI/CD 部署指南

## 概述

本文档描述了LJWX BigScreen项目的完整CI/CD流程，包括多架构镜像构建、灰度发布、弹性部署和自动回滚功能。

## 架构图

```
代码提交 → Gitea Actions → 多架构构建 → 安全扫描 → 环境部署
    ↓           ↓              ↓           ↓          ↓
  Git Push   质量检查      AMD64/ARM64    镜像扫描   K8s部署
    ↓           ↓              ↓           ↓          ↓
  触发CI    代码格式化      推送镜像      漏洞检测   灰度发布
```

## 功能特性

### ✅ 已实现功能

- **多架构支持**: 自动构建AMD64和ARM64镜像
- **代码质量检查**: 自动格式化、语法检查、单元测试
- **安全扫描**: 镜像漏洞扫描和安全检测
- **灰度发布**: 10%流量灰度 → 全量部署
- **弹性扩缩容**: 基于CPU/内存的HPA自动扩缩容
- **自动回滚**: 部署失败时自动回滚到上一版本
- **监控告警**: Prometheus监控和告警规则
- **多环境支持**: 开发环境和生产环境分离

## 目录结构

```
ljwx-bigscreen/
├── .gitea/workflows/
│   └── ci-cd.yml                 # Gitea Actions工作流
├── k8s/
│   ├── base/
│   │   └── configmap.yaml        # 基础配置
│   ├── dev/
│   │   └── deployment.yaml       # 开发环境部署
│   ├── prod/
│   │   ├── deployment.yaml       # 生产环境部署
│   │   ├── canary-deployment.yaml # 灰度部署
│   │   ├── service.yaml          # 服务配置
│   │   ├── canary-service.yaml   # 灰度服务
│   │   └── ingress.yaml          # 入口配置
│   └── monitoring/
│       └── servicemonitor.yaml   # 监控配置
├── scripts/
│   ├── deploy.sh                 # 部署脚本
│   └── rollback.sh              # 回滚脚本
└── bigscreen/
    └── Dockerfile.multiarch      # 多架构Dockerfile
```

## 环境要求

### Gitea服务器(192.168.1.83)

- **Gitea**: v1.20+
- **Gitea Actions**: 启用Actions功能
- **Docker Registry**: 内网镜像仓库(端口5000)
- **Kubernetes**: v1.25+
- **Helm**: v3.0+ (可选)

### 必需组件

```bash
# K8s集群组件
- NGINX Ingress Controller
- Prometheus Operator (可选)
- Cert-Manager (可选)
- Metrics Server (HPA必需)

# 镜像仓库
- Docker Registry或Harbor
```

## 配置步骤

### 1. Gitea配置

#### 1.1 启用Actions
```bash
# 在gitea配置文件中启用Actions
[actions]
ENABLED = true
DEFAULT_ACTIONS_URL = https://gitea.com
```

#### 1.2 配置Secrets
在Gitea仓库设置中添加以下Secrets:

```bash
# Docker Registry认证
DOCKER_USERNAME=admin
DOCKER_PASSWORD=your_password

# K8s集群访问
KUBECONFIG=base64_encoded_kubeconfig
```

### 2. K8s集群配置

#### 2.1 创建命名空间
```bash
kubectl create namespace ljwx-system
```

#### 2.2 配置RBAC
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ljwx-deployer
  namespace: ljwx-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ljwx-deployer
rules:
- apiGroups: ["apps", ""]
  resources: ["deployments", "services", "pods", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
```

#### 2.3 安装必需组件
```bash
# 安装NGINX Ingress
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# 安装Metrics Server (HPA必需)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 安装Prometheus Operator (可选)
helm upgrade --install prometheus-operator prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

### 3. Docker Registry配置

#### 3.1 启动Registry
```bash
# 在192.168.1.83上启动Registry
docker run -d -p 5000:5000 --name registry \
  -v /opt/registry:/var/lib/registry \
  registry:2
```

#### 3.2 配置不安全Registry
```json
# /etc/docker/daemon.json
{
  "insecure-registries": ["192.168.1.83:5000"]
}
```

## 使用方法

### 自动部署流程

#### 1. 开发环境部署
```bash
# 推送到develop分支触发开发环境部署
git checkout develop
git add .
git commit -m "feat: 新功能开发"
git push origin develop
```

#### 2. 生产环境灰度部署
```bash
# 推送到main分支触发灰度部署
git checkout main
git merge develop
git push origin main
```

#### 3. 生产环境全量部署
灰度部署验证通过后，Actions会自动执行全量部署。

### 手动部署

#### 1. 使用部署脚本
```bash
# 开发环境部署
./scripts/deploy.sh -e dev -t v1.0.0

# 生产环境灰度部署
./scripts/deploy.sh -e prod -t v1.0.0 --canary

# 生产环境全量部署
./scripts/deploy.sh -e prod -t v1.0.0

# 扩容到5个副本
./scripts/deploy.sh --scale 5

# 查看帮助
./scripts/deploy.sh -h
```

#### 2. 直接使用kubectl
```bash
# 设置环境变量
export REGISTRY=192.168.1.83:5000
export IMAGE_NAME=ljwx-bigscreen
export IMAGE_TAG=v1.0.0

# 应用配置
envsubst < k8s/prod/deployment.yaml | kubectl apply -f -
```

### 回滚操作

#### 1. 自动回滚
部署失败时，Actions会自动触发回滚。

#### 2. 手动回滚
```bash
# 紧急回滚到上一版本
./scripts/rollback.sh --emergency

# 查看历史版本
./scripts/rollback.sh --list

# 回滚到指定版本
./scripts/rollback.sh -r 3

# 开发环境回滚
./scripts/rollback.sh -e dev --emergency
```

## 监控和告警

### Prometheus监控指标

- **应用指标**: HTTP请求数、响应时间、错误率
- **系统指标**: CPU、内存、磁盘使用率
- **K8s指标**: Pod状态、重启次数、资源使用

### 告警规则

- **服务不可用**: 服务停止响应超过1分钟
- **高CPU使用**: CPU使用率超过80%持续5分钟
- **高内存使用**: 内存使用率超过90%持续5分钟
- **频繁重启**: 1小时内重启超过3次

### Grafana仪表板

访问Grafana查看监控仪表板:
```
http://grafana.ljwx.local/d/ljwx-bigscreen
```

## 弹性扩缩容

### HPA配置

```yaml
# 自动扩缩容规则
minReplicas: 3      # 最小副本数
maxReplicas: 10     # 最大副本数
targetCPUUtilization: 70%    # CPU目标使用率
targetMemoryUtilization: 80% # 内存目标使用率
```

### 扩缩容策略

- **扩容**: CPU/内存超过阈值时，60秒内最多扩容100%
- **缩容**: 负载降低后，5分钟内最多缩容10%

## 灰度发布策略

### 流量分配

1. **灰度阶段**: 10%流量 → 新版本，90%流量 → 稳定版本
2. **验证阶段**: 监控新版本指标，确认功能正常
3. **全量阶段**: 100%流量 → 新版本，清理灰度版本

### 灰度验证

```bash
# 通过Header访问灰度版本
curl -H "canary: true" http://bigscreen.ljwx.local

# 查看灰度版本状态
kubectl get pods -n ljwx-system -l version=canary
```

## 故障排查

### 常见问题

#### 1. 镜像拉取失败
```bash
# 检查Registry连接
docker pull 192.168.1.83:5000/ljwx-bigscreen:latest

# 检查K8s节点配置
kubectl describe pod <pod-name> -n ljwx-system
```

#### 2. 部署失败
```bash
# 查看部署状态
kubectl rollout status deployment/ljwx-bigscreen -n ljwx-system

# 查看Pod日志
kubectl logs -f deployment/ljwx-bigscreen -n ljwx-system
```

#### 3. HPA不工作
```bash
# 检查Metrics Server
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml

# 查看HPA状态
kubectl describe hpa ljwx-bigscreen-hpa -n ljwx-system
```

### 日志查看

```bash
# 应用日志
kubectl logs -f deployment/ljwx-bigscreen -n ljwx-system

# Actions日志
# 在Gitea界面查看Actions执行日志

# K8s事件
kubectl get events -n ljwx-system --sort-by='.lastTimestamp'
```

## 安全配置

### 镜像安全

- **基础镜像**: 使用官方Python slim镜像
- **漏洞扫描**: Trivy自动扫描镜像漏洞
- **最小权限**: 非root用户运行应用

### 网络安全

- **TLS加密**: 自动申请Let's Encrypt证书
- **网络策略**: 限制Pod间通信
- **入口控制**: NGINX Ingress限流和访问控制

### 访问控制

- **RBAC**: 最小权限原则
- **Secret管理**: 敏感信息加密存储
- **审计日志**: 记录所有操作日志

## 性能优化

### 镜像优化

- **多阶段构建**: 减小镜像体积
- **缓存策略**: 利用Docker层缓存
- **国内源**: 使用阿里云镜像源加速

### 部署优化

- **资源限制**: 合理设置CPU/内存限制
- **反亲和性**: Pod分布在不同节点
- **就绪探针**: 确保服务完全启动后接收流量

### 网络优化

- **连接池**: 数据库连接池配置
- **缓存**: Redis缓存热点数据
- **CDN**: 静态资源CDN加速

## 最佳实践

### 代码管理

1. **分支策略**: develop → main的GitFlow
2. **提交规范**: 使用conventional commits
3. **代码审查**: PR必须经过审查
4. **自动化测试**: 提交前运行测试

### 部署策略

1. **蓝绿部署**: 生产环境零停机部署
2. **灰度发布**: 降低新版本风险
3. **自动回滚**: 快速恢复服务
4. **监控告警**: 及时发现问题

### 运维管理

1. **版本管理**: 语义化版本号
2. **配置管理**: 环境配置分离
3. **日志管理**: 结构化日志输出
4. **备份策略**: 定期备份重要数据

## 扩展功能

### 多集群部署

支持部署到多个K8s集群:

```yaml
# 添加多集群配置
environments:
  - name: prod-cluster-1
    kubeconfig: ${{ secrets.KUBECONFIG_PROD_1 }}
  - name: prod-cluster-2
    kubeconfig: ${{ secrets.KUBECONFIG_PROD_2 }}
```

### A/B测试

基于用户特征的A/B测试:

```yaml
# A/B测试配置
canary:
  analysis:
    threshold: 5
    interval: 1m
    metrics:
    - name: success-rate
      threshold: 99
```

### 自动化测试

集成更多测试类型:

```yaml
# 测试阶段
test:
  unit: pytest tests/unit/
  integration: pytest tests/integration/
  e2e: cypress run
  performance: k6 run tests/performance.js
```

## 联系支持

如有问题，请联系:

- **技术支持**: tech-support@ljwx.com
- **运维团队**: devops@ljwx.com
- **项目文档**: https://docs.ljwx.com/cicd

---

*最后更新: 2024-06-14* 