FROM python:3.9-slim

# 设置北京时区
ENV TZ=Asia/Shanghai  
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-docker.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements-docker.txt

# 复制应用代码
COPY . .

# 设置环境变量，使用宿主机的MySQL和Redis
ENV MYSQL_HOST=host.docker.internal
ENV MYSQL_PORT=3306
ENV REDIS_HOST=host.docker.internal
ENV REDIS_PORT=6379

# 暴露应用端口
EXPOSE 5001

# 启动应用
CMD ["python3", "run.py"] 