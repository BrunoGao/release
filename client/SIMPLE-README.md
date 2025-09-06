# LJWX系统简单配置

## 📁 文件说明

- `ljwx.env` - 所有配置都在这里
- `docker-compose.yml` - Docker服务编排
- `start-ljwx.sh` - 一键启动脚本

## 🔧 修改配置

编辑 `ljwx.env` 文件：

```bash
# 数据库配置
MYSQL_HOST=ljwx-mysql
MYSQL_PORT=3306
MYSQL_DATABASE=test
MYSQL_USERNAME=ljwx
MYSQL_PASSWORD=123456

# 服务端口
ADMIN_PORT=8080
BIGSCREEN_PORT=8001
BOOT_PORT=8082

# 镜像版本
MYSQL_VERSION=2.0.1
BIGSCREEN_VERSION=2.0.1
BOOT_VERSION=2.0.1
```

## 🚀 启动系统

```bash
./start-ljwx.sh
```

## 🛠️ 常用命令

```bash
# 启动所有服务
docker-compose --env-file ljwx.env up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f ljwx-bigscreen

# 重启单个服务
docker-compose restart ljwx-bigscreen
```

## 📊 服务地址

- 管理后台: http://localhost:8080
- 大屏系统: http://localhost:8001  
- 后端API: http://localhost:8082

就这么简单！所有配置都在 `ljwx.env` 文件里。