def call(Map config) {
    def status = config.status ?: 'SUCCESS'
    def message = config.message ?: "构建${status}"
    def channel = config.channel ?: '#ci-cd'
    
    def color = 'good'
    def emoji = '✅'
    
    if (status == 'FAILURE') {
        color = 'danger'
        emoji = '❌'
    } else if (status == 'UNSTABLE') {
        color = 'warning'
        emoji = '⚠️'
    }
    
    echo "${emoji} ${message}"
    
    // 这里可以集成Slack、钉钉等通知
    /*
    slackSend(
        channel: channel,
        color: color,
        message: "${emoji} ${message}\n构建: ${env.BUILD_URL}"
    )
    */
}
