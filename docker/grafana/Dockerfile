# LJWX Grafana 定制化镜像
# 基于官方Grafana镜像，集成LJWX监控仪表板

ARG GRAFANA_VERSION=9.5.0
FROM grafana/grafana:${GRAFANA_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Customized Grafana with pre-configured dashboards"
LABEL version="${LJWX_GRAFANA_VERSION:-1.2.6}"

# 切换到root用户进行配置
USER root

# 设置环境变量
ENV TZ=Asia/Shanghai
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin123
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS=""

# 创建必要目录
RUN mkdir -p /etc/grafana/provisioning/dashboards \
    && mkdir -p /etc/grafana/provisioning/datasources \
    && mkdir -p /var/lib/grafana/dashboards

# 复制配置文件
COPY docker/grafana/grafana.ini /etc/grafana/grafana.ini
COPY docker/grafana/provisioning/ /etc/grafana/provisioning/
COPY docker/grafana/dashboards/ /var/lib/grafana/dashboards/

# 设置权限（grafana用户在官方镜像中已存在）
RUN chown -R 472:472 /etc/grafana \
    && chown -R 472:472 /var/lib/grafana

# 切换回grafana用户
USER 472

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# 暴露端口
EXPOSE 3000

# 启动命令
ENTRYPOINT ["/run.sh"]