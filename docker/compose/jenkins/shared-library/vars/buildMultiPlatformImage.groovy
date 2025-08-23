#!/usr/bin/env groovy
// 多平台Docker镜像构建共享库

def call(Map config) {
    def registry = config.registry ?: env.DOCKER_REGISTRY ?: 'localhost:5001'
    def imageName = config.imageName ?: env.JOB_NAME.toLowerCase()
    def platforms = config.platforms ?: 'linux/amd64,linux/arm64'
    def dockerfile = config.dockerfile ?: 'Dockerfile'
    def context = config.context ?: '.'
    def tags = config.tags ?: ["latest", env.BUILD_NUMBER]
    def push = config.push != false
    def builderName = config.builderName ?: 'multiplatform-builder'
    
    echo "🚀 开始多平台镜像构建"
    echo "Registry: ${registry}"
    echo "Image: ${imageName}"
    echo "Platforms: ${platforms}"
    echo "Tags: ${tags.join(', ')}"
    
    try {
        // 创建和配置builder
        sh """
            docker buildx create --use --name ${builderName} --driver docker-container 2>/dev/null || \
            docker buildx use ${builderName} 2>/dev/null || \
            docker buildx create --use --name ${builderName} --driver docker-container
            docker buildx inspect --bootstrap ${builderName}
        """
        
        // 构建标签参数
        def tagArgs = tags.collect { tag -> 
            "-t ${registry}/${imageName}:${tag}"
        }.join(' ')
        
        // 执行多平台构建
        def buildCmd = """
            docker buildx build \\
                --platform ${platforms} \\
                --file ${dockerfile} \\
                ${tagArgs} \\
                ${push ? '--push' : '--load'} \\
                ${context}
        """
        
        sh buildCmd
        
        echo "✅ 多平台镜像构建成功"
        
        // 返回构建信息
        return [
            registry: registry,
            imageName: imageName,
            tags: tags,
            platforms: platforms,
            pushed: push
        ]
        
    } catch (Exception e) {
        echo "❌ 多平台构建失败: ${e.message}"
        throw e
    }
} 