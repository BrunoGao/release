#!/usr/bin/env groovy
// Jenkins简化自动化配置脚本

import jenkins.model.*
import hudson.security.*
import hudson.util.Secret
import jenkins.security.s2m.AdminWhitelistRule
import hudson.security.csrf.DefaultCrumbIssuer

def instance = Jenkins.getInstance()

println "🚀 开始Jenkins自动化配置..."

// 1. 基础安全配置
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def adminUsername = System.getenv('JENKINS_ADMIN_ID') ?: 'admin'
def adminPassword = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin123'

// 创建管理员用户
if (!hudsonRealm.getAllUsers().find { it.getId() == adminUsername }) {
    hudsonRealm.createAccount(adminUsername, adminPassword)
    instance.setSecurityRealm(hudsonRealm)
    println "✅ 创建管理员用户: ${adminUsername}"
}

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 启用CSRF保护
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// 设置代理安全
instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

println "✅ 安全配置完成"

// 2. 系统配置
instance.setNumExecutors(4)
instance.setSystemMessage("""
🎉 Jenkins CI/CD服务器 - 完全自动化配置

📦 插件: 自动安装30+核心插件
🔧 工具: Maven, Gradle, NodeJS, Docker自动配置
🔐 凭据: Gitea, Registry认证模板
📋 作业: 多平台构建演示
📚 文档: docs/jenkins-persistence-guide.md

🌐 访问地址: http://localhost:8081
👤 登录账号: ${adminUsername} / ${adminPassword}
""")

// 设置Jenkins URL
def location = instance.getDescriptor("jenkins.model.JenkinsLocationConfiguration")
location.setUrl("http://localhost:8081/")
location.setAdminAddress("admin@example.com")
location.save()

println "✅ 系统配置完成"

// 3. 保存配置
instance.save()

// 4. 跳过设置向导
def setupWizard = instance.getSetupWizard()
if (setupWizard != null) {
    setupWizard.completeSetup()
    println "✅ 跳过设置向导"
}

println """
🎉 Jenkins基础自动化配置完成！

📋 配置摘要:
- ✅ 管理员用户: ${adminUsername}
- ✅ 安全策略: 已配置
- ✅ 系统消息: 已设置
- ✅ 设置向导: 已跳过

🌐 访问地址: http://localhost:8081
👤 登录信息: ${adminUsername} / ${adminPassword}

📚 下一步: 访问Web界面完成剩余配置
""" 