#!/usr/bin/env groovy

def call(Map config) {
    def imageName = config.imageName ?: error("imageName is required")
    def platforms = config.platforms ?: "linux/amd64,linux/arm64"
    def dockerfile = config.dockerfile ?: "Dockerfile"
    def buildContext = config.buildContext ?: "."
    def pushImage = config.pushImage ?: true
    def registryCredentialsId = config.registryCredentialsId ?: ""
    def buildArgs = config.buildArgs ?: [:]
    
    echo "🔨 构建多平台镜像: ${imageName}"
    echo "📋 平台: ${platforms}"
    
    script {
        // 构建参数
        def buildArgsStr = ""
        buildArgs.each { key, value ->
            buildArgsStr += "--build-arg ${key}=${value} "
        }
        
        if (pushImage && registryCredentialsId) {
            withCredentials([usernamePassword(credentialsId: registryCredentialsId, 
                                              usernameVariable: 'REGISTRY_USER', 
                                              passwordVariable: 'REGISTRY_PASS')]) {
                // 登录到镜像仓库
                sh """
                    echo "\${REGISTRY_PASS}" | docker login -u "\${REGISTRY_USER}" --password-stdin \$(echo "${imageName}" | cut -d'/' -f1)
                """
                
                // 构建并推送
                sh """
                    docker buildx build \\
                        --platform ${platforms} \\
                        --file ${dockerfile} \\
                        ${buildArgsStr} \\
                        --tag ${imageName} \\
                        --push \\
                        ${buildContext}
                """
            }
        } else {
            // 仅构建，不推送
            sh """
                docker buildx build \\
                    --platform ${platforms} \\
                    --file ${dockerfile} \\
                    ${buildArgsStr} \\
                    --tag ${imageName} \\
                    ${buildContext}
            """
        }
    }
    
    echo "✅ 多平台镜像构建完成: ${imageName}"
}
