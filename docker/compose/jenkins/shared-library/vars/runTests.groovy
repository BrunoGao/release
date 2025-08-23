def call(Map config = [:]) {
    def testType = config.testType ?: 'unit'
    def testPath = config.testPath ?: 'tests/'
    def coverage = config.coverage ?: false
    
    echo "运行${testType}测试..."
    
    sh """
        python -m venv venv || true
        . venv/bin/activate
        pip install -r requirements.txt
        
        if [ "${coverage}" == "true" ]; then
            pip install coverage
            coverage run -m pytest ${testPath} -v
            coverage report
            coverage html
        else
            python -m pytest ${testPath} -v
        fi
    """
    
    if (coverage) {
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'htmlcov',
            reportFiles: 'index.html',
            reportName: 'Coverage Report'
        ])
    }
}
