import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import hudson.util.Secret

def instance = Jenkins.getInstance()
def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// 确保 Docker 可用
try {
    def proc = "docker --version".execute()
    proc.waitFor()
    if (proc.exitValue() == 0) {
        println("Docker is available: ${proc.text.trim()}")
    } else {
        println("Docker command failed")
    }
} catch (Exception e) {
    println("Docker check failed: ${e.message}")
}

// 设置 Docker buildx
try {
    def buildxProc = "docker buildx version".execute()
    buildxProc.waitFor()
    if (buildxProc.exitValue() == 0) {
        println("Docker buildx is available")
        
        // 创建 multiarch builder
        def createBuilder = "docker buildx create --name multiarch --driver docker-container --use".execute()
        createBuilder.waitFor()
        
        def inspectBuilder = "docker buildx inspect --bootstrap".execute()
        inspectBuilder.waitFor()
        
        println("Multi-architecture builder created")
    }
} catch (Exception e) {
    println("Docker buildx setup failed: ${e.message}")
}

instance.save()
println('Docker setup completed!')
