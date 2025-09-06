# Redis Docker镜像 - 支持多架构构建
# 基于官方Redis 7.2镜像，集成自定义配置

ARG REDIS_VERSION=7.2-alpine
FROM redis:${REDIS_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Redis Cache Server"
LABEL version="2.0.1"

# 设置环境变量
ENV TZ=Asia/Shanghai

# 创建数据目录
RUN mkdir -p /data/redis

# 复制Redis配置文件
COPY docker/redis/redis.conf /usr/local/etc/redis/redis.conf

# 设置时区
RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD redis-cli --raw incr ping_counter

# 暴露端口
EXPOSE 6379

# 设置工作目录
WORKDIR /data

# 启动Redis服务，使用自定义配置
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]