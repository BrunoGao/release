# LJWX AlertManager 定制化镜像
# 基于官方AlertManager镜像，集成LJWX告警配置

ARG ALERTMANAGER_VERSION=latest
FROM prom/alertmanager:${ALERTMANAGER_VERSION}

# 设置维护者信息
LABEL maintainer="LJWX Team <dev@ljwx.com>"
LABEL description="LJWX Customized AlertManager with pre-configured rules"
LABEL version="${LJWX_ALERTMANAGER_VERSION:-1.2.6}"

# 切换到root用户进行配置
USER root

# 设置环境变量
ENV TZ=Asia/Shanghai

# 复制配置文件
COPY docker/alertmanager/alertmanager.yml /etc/alertmanager/alertmanager.yml

# 设置权限
RUN chown -R alertmanager:alertmanager /etc/alertmanager

# 切换回alertmanager用户
USER alertmanager

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:9093/-/healthy || exit 1

# 暴露端口
EXPOSE 9093

# 启动命令
ENTRYPOINT ["/bin/alertmanager"]
CMD ["--config.file=/etc/alertmanager/alertmanager.yml", \
     "--storage.path=/alertmanager", \
     "--web.external-url=http://localhost:9093"]