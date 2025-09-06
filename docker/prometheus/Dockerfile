# LJWX Prometheus 定制化镜像
# 基于官方Prometheus镜像，集成LJWX监控配置

ARG PROMETHEUS_VERSION=v2.40.0
FROM prom/prometheus:${PROMETHEUS_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Customized Prometheus with pre-configured rules"
LABEL version="${LJWX_PROMETHEUS_VERSION:-1.2.6}"

# 切换到root用户进行配置
USER root

# 设置环境变量
ENV TZ=Asia/Shanghai

# 创建必要目录
RUN mkdir -p /etc/prometheus/rules /etc/prometheus/conf.d

# 复制配置文件
COPY docker/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
COPY docker/prometheus/rules/ /etc/prometheus/rules/

# 设置权限
RUN chown -R prometheus:prometheus /etc/prometheus \
    && chmod -R 755 /etc/prometheus

# 切换回prometheus用户
USER prometheus

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD promtool query instant 'up' || exit 1

# 暴露端口
EXPOSE 9090

# 启动命令
ENTRYPOINT ["/bin/prometheus"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/etc/prometheus/console_libraries", \
     "--web.console.templates=/etc/prometheus/consoles", \
     "--web.enable-lifecycle", \
     "--web.enable-admin-api"]