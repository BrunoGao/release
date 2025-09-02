# 使用eclipse-temurin官方Alpine Linux带JRE的轻量级镜像
FROM eclipse-temurin:21-jre-alpine
# 指定维护者信息(可选)
LABEL maintainer="gaojunivas@gmail.com"
# 设置时区
ENV TZ='Asia/Shanghai'
RUN ln -snf /usr/share/zoneinfo/"$TZ" /etc/localtime && echo "$TZ" > /etc/timezone
# 设置工作目录
WORKDIR /app
# 将构建的jar文件复制到镜像中
COPY target/ljwx-boot-admin-1.0.6-SNAPSHOT.jar app.jar
# 允许外界访问容器的9998端口
EXPOSE 9998
# 配置容器启动后执行的命令
ENTRYPOINT ["java", "-jar", "app.jar"]