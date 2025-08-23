# Gitea Webhook配置指南

## 1. 在Gitea中配置Webhook

### 1.1 访问仓库设置
1. 登录Gitea: http://localhost:3000
2. 进入目标仓库 (如: jenkins-test-app)
3. 点击 "设置" -> "Webhooks"

### 1.2 添加Webhook
1. 点击 "添加Webhook" -> "Gitea"
2. 配置以下信息:
   - **目标URL**: `http://jenkins:8080/generic-webhook-trigger/invoke`
   - **HTTP方法**: POST
   - **内容类型**: application/json
   - **密钥**: (可选，增强安全性)

### 1.3 触发事件
选择以下事件:
- [x] Push events
- [x] Pull request events
- [x] Create events
- [x] Delete events

### 1.4 测试Webhook
1. 点击 "测试推送"
2. 检查Jenkins是否收到触发信号

## 2. Jenkins Generic Webhook Trigger配置

### 2.1 在Jenkins作业中配置
1. 进入Jenkins作业配置
2. 在 "构建触发器" 中勾选 "Generic Webhook Trigger"
3. 配置变量提取:

```
变量名: GITEA_REPO
表达式: $.repository.name
表达式类型: JSONPath

变量名: GITEA_BRANCH  
表达式: $.ref
表达式类型: JSONPath

变量名: GITEA_COMMIT
表达式: $.after
表达式类型: JSONPath
```

### 2.2 过滤器配置
- **过滤器表达式**: `jenkins-test-app`
- **过滤器文本**: `$GITEA_REPO`

## 3. 网络配置

### 3.1 Docker网络
确保Jenkins和Gitea在同一Docker网络中:
```bash
docker network create cicd-network
```

### 3.2 服务间通信
- Jenkins访问Gitea: `http://gitea:3000`
- Gitea访问Jenkins: `http://jenkins:8080`

## 4. 故障排除

### 4.1 常见问题
1. **Webhook无法触发**
   - 检查URL是否正确
   - 确认网络连通性
   - 查看Jenkins日志

2. **认证失败**
   - 检查凭据配置
   - 确认用户权限

3. **构建失败**
   - 检查Jenkinsfile语法
   - 确认环境变量配置

### 4.2 调试命令
```bash
# 查看Jenkins日志
docker logs jenkins

# 查看Gitea日志  
docker logs gitea

# 测试网络连通性
docker exec jenkins ping gitea
docker exec gitea ping jenkins
```

## 5. 高级配置

### 5.1 分支策略
```groovy
when {
    anyOf {
        branch 'main'
        branch 'develop'
        branch 'feature/*'
    }
}
```

### 5.2 条件部署
```groovy
when {
    allOf {
        branch 'main'
        not { changeRequest() }
    }
}
```

### 5.3 并行构建
```groovy
parallel {
    stage('单元测试') {
        steps {
            sh 'pytest tests/unit'
        }
    }
    stage('集成测试') {
        steps {
            sh 'pytest tests/integration'
        }
    }
}
```
