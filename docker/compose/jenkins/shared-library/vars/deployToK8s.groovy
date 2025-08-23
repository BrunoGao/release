#!/usr/bin/env groovy
// K8s部署共享库

def call(Map config) {
    def namespace = config.namespace ?: 'default'
    def appName = config.appName ?: env.JOB_NAME.toLowerCase()
    def image = config.image
    def manifests = config.manifests ?: 'k8s/'
    def kubeconfig = config.kubeconfig ?: 'k8s-config'
    def dryRun = config.dryRun ?: false
    def waitForRollout = config.waitForRollout != false
    def timeout = config.timeout ?: '300s'
    
    if (!image) {
        error "❌ 必须指定镜像地址"
    }
    
    echo "🚀 开始K8s部署"
    echo "Namespace: ${namespace}"
    echo "App: ${appName}"
    echo "Image: ${image}"
    echo "Manifests: ${manifests}"
    
    withCredentials([string(credentialsId: kubeconfig, variable: 'KUBECONFIG_CONTENT')]) {
        try {
            // 创建kubeconfig文件
            writeFile file: 'kubeconfig', text: env.KUBECONFIG_CONTENT
            
            // 设置环境变量
            env.KUBECONFIG = "${env.WORKSPACE}/kubeconfig"
            
            // 检查集群连接
            sh 'kubectl cluster-info'
            
            // 创建命名空间(如果不存在)
            sh """
                kubectl create namespace ${namespace} --dry-run=client -o yaml | \
                kubectl apply -f -
            """
            
            // 更新镜像标签
            if (fileExists(manifests)) {
                sh """
                    find ${manifests} -name "*.yaml" -o -name "*.yml" | \
                    xargs sed -i '' 's|image:.*${appName}.*|image: ${image}|g'
                """
            }
            
            // 执行部署
            def deployCmd = "kubectl apply -f ${manifests} -n ${namespace}"
            if (dryRun) {
                deployCmd += " --dry-run=client"
            }
            
            sh deployCmd
            
            if (!dryRun && waitForRollout) {
                // 等待部署完成
                sh """
                    kubectl rollout status deployment/${appName} -n ${namespace} --timeout=${timeout} || \
                    kubectl rollout status statefulset/${appName} -n ${namespace} --timeout=${timeout} || \
                    echo "等待部署完成..."
                """
                
                // 验证Pod状态
                sh """
                    kubectl get pods -n ${namespace} -l app=${appName} -o wide
                    kubectl describe pods -n ${namespace} -l app=${appName} | grep -A 5 Events: || true
                """
            }
            
            echo "✅ K8s部署成功"
            
            return [
                namespace: namespace,
                appName: appName,
                image: image,
                deployed: !dryRun
            ]
            
        } catch (Exception e) {
            echo "❌ K8s部署失败: ${e.message}"
            
            // 显示调试信息
            sh """
                echo "=== Pod状态 ==="
                kubectl get pods -n ${namespace} -l app=${appName} || true
                echo "=== Events ==="
                kubectl get events -n ${namespace} --sort-by='.lastTimestamp' | tail -10 || true
            """
            
            throw e
        } finally {
            // 清理kubeconfig
            sh 'rm -f kubeconfig'
        }
    }
} 