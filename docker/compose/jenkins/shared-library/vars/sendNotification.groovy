#!/usr/bin/env groovy

def call(Map config) {
    def status = config.status ?: currentBuild.result ?: 'SUCCESS'
    def title = config.title ?: "${env.JOB_NAME} #${env.BUILD_NUMBER}"
    def message = config.message ?: "构建状态: ${status}"
    def channels = config.channels ?: ['slack', 'dingtalk', 'email']
    
    def color = status == 'SUCCESS' ? 'good' : 'danger'
    def emoji = status == 'SUCCESS' ? '✅' : '❌'
    
    channels.each { channel ->
        try {
            switch(channel) {
                case 'slack':
                    if (env.SLACK_TOKEN) {
                        slackSend(
                            color: color,
                            message: "${emoji} ${title}\n${message}\n构建详情: ${env.BUILD_URL}"
                        )
                    }
                    break
                    
                case 'dingtalk':
                    if (env.DINGTALK_WEBHOOK) {
                        dingtalk(
                            robot: env.DINGTALK_WEBHOOK,
                            type: 'MARKDOWN',
                            title: title,
                            text: "## ${emoji} ${title}\n\n${message}\n\n[查看详情](${env.BUILD_URL})"
                        )
                    }
                    break
                    
                case 'email':
                    emailext(
                        subject: "${emoji} ${title}",
                        body: "${message}\n\n构建详情: ${env.BUILD_URL}",
                        to: "${env.CHANGE_AUTHOR_EMAIL ?: 'admin@example.com'}"
                    )
                    break
            }
            
            echo "✅ 通知已发送到 ${channel}"
        } catch (Exception e) {
            echo "⚠️ 发送 ${channel} 通知失败: ${e.message}"
        }
    }
}
