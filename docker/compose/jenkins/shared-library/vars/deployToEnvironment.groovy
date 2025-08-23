def call(Map config) {
    def environment = config.environment ?: 'test'
    def appName = config.appName ?: env.JOB_NAME.split('/')[0]
    def imageTag = config.imageTag ?: "${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
    def registry = config.registry ?: 'localhost:5001'
    def port = config.port ?: 8080
    
    echo "部署到${environment}环境..."
    
    sh """
        docker stop ${appName}-${environment} || true
        docker rm ${appName}-${environment} || true
        docker run -d --name ${appName}-${environment} -p ${port}:5000 ${registry}/${appName}:${imageTag}
    """
    
    // 健康检查
    sh """
        sleep 10
        curl -f http://localhost:${port}/health || echo "健康检查失败"
    """
}
