import jenkins.model.*
import hudson.security.*
import hudson.security.csrf.DefaultCrumbIssuer
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// 跳过设置向导
if (!instance.getInstallState().isSetupComplete()) {
    println('Skipping initial setup wizard...')
    instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)
}

// 设置 CSRF 保护
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// 设置安全策略
instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

// 保存配置
instance.save()

println('Admin setup completed!')
