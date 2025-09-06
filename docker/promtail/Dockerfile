# LJWX Promtail 定制化镜像
# 基于官方Promtail镜像，集成LJWX日志收集配置

ARG PROMTAIL_VERSION=2.9.0
FROM grafana/promtail:${PROMTAIL_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Customized Promtail for log collection"
LABEL version="${LJWX_PROMTAIL_VERSION:-1.2.6}"

# 设置环境变量
ENV TZ=Asia/Shanghai

# 复制配置文件
COPY docker/promtail/promtail.yml /etc/promtail/config.yml

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:9080/ready || exit 1

# 暴露端口
EXPOSE 9080

# 启动命令
ENTRYPOINT ["/usr/bin/promtail"]
CMD ["-config.file=/etc/promtail/config.yml"]