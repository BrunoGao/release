#!/bin/bash
# Jenkins插件安装脚本

PLUGINS=(
    "configuration-as-code:latest"
    "job-dsl:latest"
    "pipeline-stage-view:latest"
    "blueocean:latest"
    "gitea:latest"
    "docker-plugin:latest"
    "docker-workflow:latest"
    "credentials-binding:latest"
    "timestamper:latest"
    "ws-cleanup:latest"
    "build-timeout:latest"
    "generic-webhook-trigger:latest"
    "pipeline-utility-steps:latest"
    "http_request:latest"
    "email-ext:latest"
    "maven-plugin:latest"
    "gradle:latest"
    "nodejs:latest"
    "python:latest"
)

echo "推荐安装的插件列表："
for plugin in "${PLUGINS[@]}"; do
    echo "- $plugin"
done

echo ""
echo "在Jenkins管理界面中，进入 '管理Jenkins' -> '插件管理' -> '可选插件'"
echo "搜索并安装上述插件"
