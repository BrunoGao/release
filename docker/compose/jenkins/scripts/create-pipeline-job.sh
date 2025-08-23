#!/bin/bash
# Pipeline作业生成器

set -e

# 参数
JOB_NAME="$1"
REPO_URL="$2"
PIPELINE_TYPE="$3"
BRANCH="$4"

if [[ -z "$JOB_NAME" || -z "$REPO_URL" ]]; then
    echo "用法: $0 <作业名称> <仓库URL> [Pipeline类型] [分支]"
    echo ""
    echo "Pipeline类型:"
    echo "  webapp      - Web应用 (默认)"
    echo "  microservice - 微服务"
    echo "  docker      - Docker构建"
    echo "  multistage  - 多阶段构建"
    echo ""
    echo "示例:"
    echo "  $0 my-webapp http://gitea:3000/user/repo.git webapp main"
    exit 1
fi

PIPELINE_TYPE=${PIPELINE_TYPE:-webapp}
BRANCH=${BRANCH:-main}

# 生成作业配置XML
cat > "/tmp/${JOB_NAME}.xml" << EOF
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>自动生成的${PIPELINE_TYPE} Pipeline作业</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <org.jenkinsci.plugins.gwt.GenericTrigger plugin="generic-webhook-trigger">
          <spec></spec>
          <genericVariables>
            <org.jenkinsci.plugins.gwt.GenericVariable>
              <expressionType>JSONPath</expressionType>
              <key>GITEA_REPO</key>
              <value>\$.repository.name</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
            <org.jenkinsci.plugins.gwt.GenericVariable>
              <expressionType>JSONPath</expressionType>
              <key>GITEA_BRANCH</key>
              <value>\$.ref</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
          </genericVariables>
          <regexpFilterText>\$GITEA_REPO</regexpFilterText>
          <regexpFilterExpression>$JOB_NAME</regexpFilterExpression>
          <printContributedVariables>true</printContributedVariables>
          <printPostContent>true</printPostContent>
        </org.jenkinsci.plugins.gwt.GenericTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>$REPO_URL</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/$BRANCH</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
