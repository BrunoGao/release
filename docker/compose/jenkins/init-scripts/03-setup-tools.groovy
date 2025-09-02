import jenkins.model.*
import hudson.model.*
import hudson.tools.*
import hudson.util.DescribableList
import jenkins.plugins.nodejs.tools.*
import org.jenkinsci.plugins.docker.commons.tools.*

def instance = Jenkins.getInstance()

// 配置 Git
def gitDesc = instance.getDescriptor(hudson.plugins.git.GitTool.class)
def gitInstallations = [
    new hudson.plugins.git.GitTool("Default", "/usr/bin/git", [])
]
gitDesc.setInstallations(gitInstallations.toArray(new hudson.plugins.git.GitTool[0]))

// 配置 Docker
def dockerDesc = instance.getDescriptor(org.jenkinsci.plugins.docker.commons.tools.DockerTool.class)
if (dockerDesc) {
    def dockerInstallations = [
        new org.jenkinsci.plugins.docker.commons.tools.DockerTool("Docker", "/usr/bin/docker", [])
    ]
    dockerDesc.setInstallations(dockerInstallations.toArray(new org.jenkinsci.plugins.docker.commons.tools.DockerTool[0]))
}

instance.save()
println('Tools setup completed!')
