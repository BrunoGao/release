#!/usr/bin/env groovy
// 跳过Jenkins设置向导并配置基础安全

import jenkins.model.*
import hudson.security.*
import hudson.security.csrf.DefaultCrumbIssuer
import hudson.util.Secret
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// 设置管理员账号（如果不存在）
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def adminUsername = System.getenv('JENKINS_ADMIN_ID') ?: 'admin'
def adminPassword = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin123'

if (!hudsonRealm.getAllUsers().find { it.getId() == adminUsername }) {
    hudsonRealm.createAccount(adminUsername, adminPassword)
    instance.setSecurityRealm(hudsonRealm)
    
    println "✅ 创建管理员用户: ${adminUsername}"
} else {
    println "ℹ️  管理员用户已存在: ${adminUsername}"
}

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 启用CSRF保护
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// 设置代理到主服务器安全
instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

// 设置Jenkins版本以跳过向导
def setupWizard = instance.getSetupWizard()
if (setupWizard != null) {
    setupWizard.completeSetup()
    println "✅ 已跳过设置向导"
}

// 禁用使用统计
instance.setNoUsageStatistics(true)

// 保存配置
instance.save()

println "🎉 Jenkins安全配置完成" 