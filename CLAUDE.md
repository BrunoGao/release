# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive CI/CD infrastructure setup for Mac Studio M2 environment, featuring Jenkins, Gitea, and Docker Registry with full automation support.

## Quick Start Commands

```bash
# Complete automated deployment - fully configured Jenkins
./jenkins-auto-deploy.sh

# Daily management
./jenkins-manager.sh start     # Start services
./jenkins-manager.sh stop      # Stop services  
./jenkins-manager.sh status    # Check status
./jenkins-manager.sh logs      # View Jenkins logs
./jenkins-manager.sh backup    # Backup configuration
./jenkins-manager.sh health    # Health check

# Simple quick start (manual setup required)
./quick-start-jenkins.sh
```

## Service Access Points

- **Jenkins**: http://localhost:8081 (admin/admin123 for auto-deployed)
- **Docker Registry**: http://localhost:5001
- **Registry UI**: http://localhost:5002  
- **Gitea**: http://192.168.1.6:3000

## Architecture

### Core Components
- **Jenkins LTS**: CI/CD server with Configuration as Code (CasC)
- **Gitea**: Git repository server with Actions support
- **Docker Registry**: Local container registry for multi-platform images
- **Multi-platform Build**: Supports linux/amd64 and linux/arm64

### Key Directories
```
infra/
├── jenkins-auto-deploy.sh              # ⭐ Main automated deployment
├── jenkins-manager.sh                  # Daily management script
├── docker/compose/
│   ├── jenkins-simple.yml             # Primary Jenkins Compose file
│   ├── jenkins-complete-auto.yml       # Full auto-configuration
│   └── jenkins/
│       ├── casc/jenkins.yaml          # ⭐ Configuration as Code
│       ├── plugins.txt                # Jenkins plugins list
│       ├── init-scripts/              # Initialization scripts
│       ├── shared-library/            # Pipeline shared libraries
│       └── templates/                 # Dockerfile & Pipeline templates
├── deployment/scripts/                # Management & integration scripts
└── docs/                              # Documentation and guides
```

## Docker Configuration Files

### Main Compose Files
- `jenkins-simple.yml` - Basic Jenkins setup
- `jenkins-complete-auto.yml` - Full automation with CasC
- `gitea-compose.yml` - Gitea service
- `registry-compose.yml` - Docker registry

### Jenkins Automation
The Jenkins instance uses Configuration as Code located at `docker/compose/jenkins/casc/jenkins.yaml` which includes:
- Auto-configured tools (Git, Maven, Gradle, NodeJS, Docker, Python)
- Pre-configured credentials (Gitea, Registry, SSH)
- Cloud configurations (Docker, Kubernetes)
- Security settings and user management
- Pre-created jobs (multi-platform builds, system monitoring)

## Development Workflow

### For Infrastructure Changes
1. Modify configuration files in `docker/compose/jenkins/casc/`
2. Test with: `./jenkins-manager.sh restart`
3. Use: `./jenkins-manager.sh health` to verify

### For Adding New Services
1. Create/modify compose files in `docker/compose/`
2. Update management scripts in `deployment/scripts/`
3. Test deployment with appropriate script

### Pipeline Development
- Templates available in `docker/compose/jenkins/templates/`
- Shared libraries in `docker/compose/jenkins/shared-library/`
- Multi-platform Docker builds supported by default

## Important Configuration Files

- `docker/compose/jenkins/casc/jenkins.yaml` - Jenkins Configuration as Code
- `docker/compose/jenkins/plugins.txt` - Jenkins plugins
- `jenkins-manager.sh` - Primary management interface
- `deployment/scripts/` - Various automation scripts

## Multi-Platform Build Support

All Docker builds support both linux/amd64 and linux/arm64 platforms. The Jenkins configuration includes buildx setup and multi-platform pipeline templates.

## Backup and Recovery

```bash
./jenkins-manager.sh backup    # Create backup
./jenkins-manager.sh restore   # Restore from backup
```

Backups are stored in `backup/jenkins/` with timestamps.

## Troubleshooting

1. Check service health: `./jenkins-manager.sh health`
2. View logs: `./jenkins-manager.sh logs`
3. Restart services: `./jenkins-manager.sh restart`
4. Full reset: `./jenkins-manager.sh cleanup` (⚠️ destructive)

Detailed troubleshooting guide available at `docs/troubleshooting.md`.

## ljwx-boot 健康定时任务系统

### 健康定时任务概览

ljwx-boot 包含一套完整的健康数据处理定时任务系统，主要包括：

1. **HealthBaselineScoreTasks** - 核心定时任务类
   - 位置: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/task/HealthBaselineScoreTasks.java`
   - 使用 `@Scheduled` 注解实现多个定时任务
   - 支持分表架构和并行处理

2. **HealthRecommendationJob** - 健康建议生成作业
   - 位置: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/job/HealthRecommendationJob.java`
   - 实现 Quartz Job 接口，集成到 mon_scheduler 系统

### 定时任务执行时间表

```
01:00 - 权重配置验证任务 (validateWeightConfigurations)
02:00 - 生成用户健康基线 (generateUserHealthBaseline)
02:05 - 生成部门健康基线聚合 (generateDepartmentHealthBaseline)
02:10 - 生成组织健康基线 (generateOrgHealthBaseline)
02:15 - 生成部门健康评分 (generateDepartmentHealthScore)
04:00 - 生成用户健康评分 (generateHealthScore)
04:10 - 生成组织健康评分 (generateOrgHealthScore)
05:00 - 数据清理任务 (cleanupOldData)

每月1日凌晨 - 按月分表任务 (archiveAndResetUserHealthTable)
```

### 管理界面

前端管理界面位于：
- **ljwx-admin**: `/src/views/monitor/scheduler/index.vue`
- **API接口**: `/src/service/api/monitor/scheduler.ts`
- **访问地址**: http://localhost:3000/#/monitor/scheduler

管理界面功能：
- 查看所有调度任务状态
- 立即执行任务 (immediate)
- 暂停/恢复任务 (pause/resume)
- 暂停/恢复任务组 (pauseGroup/resumeGroup)
- 编辑任务配置
- 删除任务

### 核心功能

1. **多表支持**: 自动检测并查询主表和月度分表
2. **并行处理**: 使用线程池并行处理多个健康特征
3. **异常检测**: 自动检测和修复数据异常
4. **覆盖率监控**: 检查各个特征的数据覆盖率
5. **权重计算**: 集成客户自定义权重配置

### 健康特征支持

系统支持以下健康指标的基线和评分计算：
- heart_rate (心率)
- blood_oxygen (血氧)
- temperature (体温)
- pressure_high/pressure_low (血压)
- stress (压力)
- step (步数)
- calorie (卡路里)
- distance (距离)
- sleep (睡眠)

### 调试说明

**重要**: 调试过程中不要重启 ljwx-boot 服务，用户会手动重启。

使用以下命令检查服务状态：
```bash
cd ljwx-boot && ./run-local.sh status  # 检查状态
# 不要使用 ./run-local.sh start 或 ./run-local.sh restart
```

### 任务监控

1. **日志监控**: 所有任务执行都有详细的日志输出
2. **性能指标**: 记录任务执行时间和处理数据量
3. **异常处理**: 自动捕获和记录异常，不会影响其他任务
4. **状态跟踪**: 通过 mon_scheduler 系统跟踪任务状态

### IP地址解析修复

系统已修复IPv6地址解析问题：
- **问题**: IPv6 localhost地址 "0:0:0:0:0:0:0:1" 无法被 ip2region 库识别
- **解决**: 在 `IPUtil.java` 中添加IPv6和本地地址检测
- **位置**: `ljwx-boot/ljwx-boot-common/src/main/java/com/ljwx/common/util/IPUtil.java`
- **处理策略**:
  - 本地地址 (127.0.0.1, ::1, 0:0:0:0:0:0:0:1) → "本地|本地|本地|本地"
  - IPv6地址 → "IPv6|IPv6|IPv6|IPv6"  
  - 内网IP → "内网|内网|内网|内网"
  - 查询失败 → "未知|未知|未知|未知"

### 权重缓存表修复

系统已修复权重计算功能：
- **问题**: `t_weight_cache` 表不存在导致健康评分任务失败
- **解决**: 创建了完整的权重缓存表结构
- **位置**: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/WeightCalculationService.java`
- **表结构**: 支持用户权重配置、岗位风险倍数、归一化权重等功能
- **安全处理**: 添加表存在性检查，避免SQL错误

### 健康建议服务修复

系统已修复健康建议生成功能：
- **问题**: `HealthRecommendationService` 中 NullPointerException，由于数据分组时遇到null键
- **解决**: 在流处理前过滤null值，添加数据验证和日志记录
- **位置**: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/HealthRecommendationService.java`
- **改进**: 增强了数据质量检测和错误处理

### 权重配置优化和合理化

系统已完成权重分配的标准化：
- **问题**: 权重配置不合理（总和超过1.0、存在null值、分配不科学）
- **解决**: 实现了基于医学重要性的标准化权重分配算法
- **位置**: `ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/WeightCalculationService.java`

#### 标准权重分配方案

**核心生命体征 (65%)**:
- 心率: 20% - 最重要的生命体征指标
- 血氧: 18% - 呼吸系统核心指标  
- 体温: 15% - 基础生命体征
- 收缩压: 6% - 心血管健康指标
- 舒张压: 6% - 心血管健康指标

**健康状态指标 (20%)**:
- 压力指数: 12% - 心理健康重要指标
- 睡眠质量: 8% - 恢复性健康指标

**运动健康指标 (10%)**:
- 步数: 4% - 日常活动量
- 距离: 3% - 运动强度
- 卡路里: 3% - 代谢水平

**辅助指标 (5%)**:
- 心电图: 2% - 深度心血管监测
- 位置/锻炼等: 各1%以下

#### 技术改进

- **类型安全**: 修复了BigDecimal到Double的类型转换问题
- **数据验证**: 添加了权重配置的自动验证和修复
- **标准化**: 实现了科学的权重分配标准
- **自动修复**: 系统自动检测和修复不合理的权重配置
