#!/usr/bin/env groovy
// Jenkins自动化初始化脚本

import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// 设置系统消息
instance.setSystemMessage("""
🎉 Jenkins已完全自动配置！

📦 已安装插件: ${instance.pluginManager.plugins.size()} 个
🔧 工具配置: Git, JDK, Maven, Gradle, NodeJS, Docker, Python
☁️  云配置: Docker Cloud, Kubernetes Cloud  
🔐 凭据模板: Gitea, Registry, SSH, K8s等
📋 预创建作业: 多平台构建, 系统监控, 镜像模板
📚 管理文档: docs/jenkins-persistence-guide.md

🌐 访问地址: http://localhost:8081
👤 登录账号: admin / admin123
""")

// 保存配置
instance.save()

println "🎉 Jenkins自动化初始化完成!"
