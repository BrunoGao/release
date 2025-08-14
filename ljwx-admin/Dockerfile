# 使用 Node.js 官方镜像作为基础镜像
FROM node:18-alpine

# 设置北京时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 安装 pnpm
RUN corepack enable && corepack prepare pnpm@10.8.0 --activate

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache python3 make g++

# 复制 package.json、pnpm-lock.yaml 和其他配置文件
COPY package.json pnpm-lock.yaml .npmrc pnpm-workspace.yaml ./
COPY packages/ ./packages/
COPY tsconfig.json vite.config.ts ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 设置环境变量
ENV NODE_ENV=development
ENV VITE_USER_NODE_ENV=development

# 暴露端口
EXPOSE 5173

# 启动开发服务器
CMD ["pnpm", "run", "dev"]
