package org.example

class Utils {
    static def getGitCommitInfo(script) {
        def commit = script.sh(
            script: 'git rev-parse HEAD',
            returnStdout: true
        ).trim()
        
        def shortCommit = script.sh(
            script: 'git rev-parse --short HEAD',
            returnStdout: true
        ).trim()
        
        def author = script.sh(
            script: 'git log -1 --pretty=format:"%an"',
            returnStdout: true
        ).trim()
        
        def message = script.sh(
            script: 'git log -1 --pretty=format:"%s"',
            returnStdout: true
        ).trim()
        
        return [
            commit: commit,
            shortCommit: shortCommit,
            author: author,
            message: message
        ]
    }
    
    static def generateImageTag(buildNumber, gitCommit) {
        return "${buildNumber}-${gitCommit[0..7]}"
    }
    
    static def cleanupOldImages(script, registry, appName, keepCount = 5) {
        script.sh """
            images=\$(docker images ${registry}/${appName} --format "{{.Tag}}" | grep -E '^[0-9]+-[a-f0-9]{8}\$' | sort -nr | tail -n +${keepCount + 1})
            for img in \$images; do
                docker rmi ${registry}/${appName}:\$img || true
            done
        """
    }
}
