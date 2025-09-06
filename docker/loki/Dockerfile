# LJWX Loki 定制化镜像
# 基于官方Loki镜像，集成LJWX日志配置

ARG LOKI_VERSION=2.9.0
FROM grafana/loki:${LOKI_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Customized Loki for log aggregation"
LABEL version="${LJWX_LOKI_VERSION:-1.2.6}"

# 设置环境变量
ENV TZ=Asia/Shanghai

# 复制配置文件
COPY docker/loki/loki.yml /etc/loki/local-config.yaml

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1

# 暴露端口
EXPOSE 3100

# 启动命令
ENTRYPOINT ["/usr/bin/loki"]
CMD ["-config.file=/etc/loki/local-config.yaml"]