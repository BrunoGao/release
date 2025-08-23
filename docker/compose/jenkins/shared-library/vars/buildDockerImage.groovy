def call(Map config) {
    def registry = config.registry ?: 'localhost:5001'
    def appName = config.appName ?: env.JOB_NAME.split('/')[0]
    def imageTag = config.imageTag ?: "${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
    def credentialsId = config.credentialsId ?: 'registry-auth'
    
    echo "构建Docker镜像: ${registry}/${appName}:${imageTag}"
    
    script {
        def image = docker.build("${registry}/${appName}:${imageTag}")
        
        docker.withRegistry("http://${registry}", credentialsId) {
            image.push()
            image.push("latest")
        }
        
        return image
    }
}
