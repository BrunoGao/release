# MySQL Docker镜像 - 支持多架构构建
# 基于官方MySQL 8.0镜像，集成数据初始化功能

ARG MYSQL_VERSION=8.0
FROM mysql:${MYSQL_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX MySQL Database with initialization data"
LABEL version="2.0.1"

# 设置默认环境变量
ENV MYSQL_ROOT_PASSWORD=123456
ENV MYSQL_DATABASE=test  
ENV MYSQL_USER=ljwx
ENV MYSQL_PASSWORD=123456
ENV TZ=Asia/Shanghai

# 复制初始化脚本和数据
COPY data.sql /docker-entrypoint-initdb.d/01-init-data.sql

# 复制自定义MySQL配置
COPY docker/mysql/my.cnf /etc/mysql/conf.d/ljwx.cnf

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD mysqladmin ping -h localhost -u root -p$MYSQL_ROOT_PASSWORD || exit 1

# 暴露端口
EXPOSE 3306

# 使用官方入口点
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["mysqld"]