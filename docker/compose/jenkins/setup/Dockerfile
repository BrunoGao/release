FROM jenkins/jenkins:lts-jdk21

# 切换到root用户安装插件和配置
USER root

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 切换回jenkins用户
USER jenkins

# 跳过初始设置向导
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# 复制插件列表
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# 安装插件
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# 复制初始化脚本
COPY init.groovy /usr/share/jenkins/ref/init.groovy.d/init.groovy

# 设置环境变量
ENV JENKINS_USER=admin
ENV JENKINS_PASS=admin123

# 暴露端口
EXPOSE 8080 50000 