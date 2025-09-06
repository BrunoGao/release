#!/bin/bash
# LJWX系统配置生成脚本
# 从统一配置文件生成各服务的运行时配置

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/ljwx-config.json"
COMPOSE_TEMPLATE="$SCRIPT_DIR/docker-compose.template.yml"
COMPOSE_OUTPUT="$SCRIPT_DIR/docker-compose.yml"

echo "🔧 LJWX系统配置生成器"
echo "配置文件: $CONFIG_FILE"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 检查Python和PyYAML是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 创建临时Python脚本来解析JSON配置
cat > /tmp/parse_ljwx_config.py << 'EOF'
import json
import sys
import os

def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 parse_ljwx_config.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    config = load_config(config_file)
    
    # 输出环境变量格式
    registry = config['images']['registry']
    
    # 镜像版本
    print(f"export REGISTRY='{registry}'")
    print(f"export MYSQL_VERSION='{config['images']['ljwx-mysql']}'")
    print(f"export REDIS_VERSION='{config['images']['ljwx-redis']}'")
    print(f"export BOOT_VERSION='{config['images']['ljwx-boot']}'")
    print(f"export BIGSCREEN_VERSION='{config['images']['ljwx-bigscreen']}'")
    print(f"export ADMIN_VERSION='{config['images']['ljwx-admin']}'")
    
    # 数据库配置
    mysql_config = config['database']['mysql']
    print(f"export MYSQL_HOST='{mysql_config['host']}'")
    print(f"export MYSQL_PORT={mysql_config['port']}")
    print(f"export MYSQL_DATABASE='{mysql_config['database']}'")
    print(f"export MYSQL_USERNAME='{mysql_config['username']}'")
    print(f"export MYSQL_PASSWORD='{mysql_config['password']}'")
    
    redis_config = config['database']['redis']
    print(f"export REDIS_HOST='{redis_config['host']}'")
    print(f"export REDIS_PORT={redis_config['port']}")
    
    # 服务端口
    print(f"export ADMIN_PORT={config['services']['ljwx-admin']['port']}")
    print(f"export BIGSCREEN_PORT={config['services']['ljwx-bigscreen']['port']}")
    print(f"export BOOT_PORT={config['services']['ljwx-boot']['port']}")

if __name__ == "__main__":
    main()
EOF

# 生成环境变量
echo "📋 解析配置文件..."
ENV_VARS=$(python3 /tmp/parse_ljwx_config.py "$CONFIG_FILE")

# 导出环境变量
eval "$ENV_VARS"

echo "✅ 环境变量已设置:"
echo "   Registry: $REGISTRY"
echo "   MySQL: $MYSQL_VERSION (Port: $MYSQL_PORT)"
echo "   Redis: $REDIS_VERSION (Port: $REDIS_PORT)"
echo "   Boot: $BOOT_VERSION (Port: $BOOT_PORT)"
echo "   Bigscreen: $BIGSCREEN_VERSION (Port: $BIGSCREEN_PORT)"
echo "   Admin: $ADMIN_VERSION (Port: $ADMIN_PORT)"

# 生成docker-compose.yml文件
if [ -f "$COMPOSE_TEMPLATE" ]; then
    echo "🐳 生成Docker Compose配置..."
    envsubst < "$COMPOSE_TEMPLATE" > "$COMPOSE_OUTPUT"
    echo "✅ Docker Compose配置已生成: $COMPOSE_OUTPUT"
else
    echo "⚠️  Docker Compose模板不存在: $COMPOSE_TEMPLATE"
fi

# 生成.env文件用于docker-compose
echo "📄 生成.env文件..."
cat > "$SCRIPT_DIR/.env" << EOF
# LJWX系统环境变量配置
# 由generate-config.sh自动生成，请勿手动修改

# 镜像仓库和版本
REGISTRY=$REGISTRY
MYSQL_VERSION=$MYSQL_VERSION
REDIS_VERSION=$REDIS_VERSION
BOOT_VERSION=$BOOT_VERSION
BIGSCREEN_VERSION=$BIGSCREEN_VERSION
ADMIN_VERSION=$ADMIN_VERSION

# 数据库配置
MYSQL_HOST=$MYSQL_HOST
MYSQL_PORT=$MYSQL_PORT
MYSQL_DATABASE=$MYSQL_DATABASE
MYSQL_USERNAME=$MYSQL_USERNAME
MYSQL_PASSWORD=$MYSQL_PASSWORD

REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT

# 服务端口
ADMIN_PORT=$ADMIN_PORT
BIGSCREEN_PORT=$BIGSCREEN_PORT
BOOT_PORT=$BOOT_PORT

# 生成时间
GENERATED_AT=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
EOF

echo "✅ .env文件已生成: $SCRIPT_DIR/.env"

# 生成服务特定配置文件
echo "⚙️  生成服务特定配置..."

# 为ljwx-bigscreen生成Python配置文件
mkdir -p "$SCRIPT_DIR/config/bigscreen"
cat > "$SCRIPT_DIR/config/bigscreen/config.py" << EOF
# ljwx-bigscreen配置文件
# 由generate-config.sh自动生成

# 从统一配置加载
import sys
import os
sys.path.append('/app/config')
sys.path.append('/client/config')

try:
    from config_loader import get_database_config, get_service_config, get_config
    
    # 数据库配置
    MYSQL_CONFIG = get_database_config('mysql')
    REDIS_CONFIG = get_database_config('redis')
    
    # 服务配置
    SERVICE_CONFIG = get_service_config('ljwx-bigscreen')
    
    # 应用配置
    APP_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': SERVICE_CONFIG.get('port', 8001),
        'DEBUG': False,
        'SECRET_KEY': get_config().get('security.jwt_secret', 'ljwx-secret'),
    }
    
except ImportError:
    # 备用静态配置
    MYSQL_CONFIG = {
        'host': '$MYSQL_HOST',
        'port': $MYSQL_PORT,
        'database': '$MYSQL_DATABASE',
        'username': '$MYSQL_USERNAME',
        'password': '$MYSQL_PASSWORD'
    }
    
    REDIS_CONFIG = {
        'host': '$REDIS_HOST',
        'port': $REDIS_PORT,
        'password': '',
        'db': 0
    }
    
    APP_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': $BIGSCREEN_PORT,
        'DEBUG': False,
        'SECRET_KEY': 'ljwx-secret',
    }
EOF

# 为ljwx-boot生成application.yml
mkdir -p "$SCRIPT_DIR/config/boot"
cat > "$SCRIPT_DIR/config/boot/application-prod.yml" << EOF
# ljwx-boot生产环境配置文件
# 由generate-config.sh自动生成

server:
  port: $BOOT_PORT
  servlet:
    context-path: /api

spring:
  profiles:
    active: prod
  
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://$MYSQL_HOST:$MYSQL_PORT/$MYSQL_DATABASE?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai
    username: $MYSQL_USERNAME
    password: $MYSQL_PASSWORD
    
    hikari:
      pool-name: ljwx-boot-pool
      minimum-idle: 5
      maximum-pool-size: 20
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
  
  redis:
    host: $REDIS_HOST
    port: $REDIS_PORT
    database: 0
    timeout: 5000
    jedis:
      pool:
        max-active: 50
        max-wait: 3000
        max-idle: 20
        min-idle: 2

  jpa:
    hibernate:
      ddl-auto: none
    show-sql: false
    database-platform: org.hibernate.dialect.MySQL8Dialect

# 日志配置
logging:
  level:
    root: INFO
    com.ljwx: INFO
  file:
    name: /app/logs/ljwx-boot.log
  pattern:
    file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"

# 管理端点
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always
EOF

echo "✅ 服务配置文件已生成"

# 清理临时文件
rm -f /tmp/parse_ljwx_config.py

echo ""
echo "🎉 配置生成完成！"
echo ""
echo "📋 生成的文件:"
echo "   - $COMPOSE_OUTPUT"
echo "   - $SCRIPT_DIR/.env"
echo "   - $SCRIPT_DIR/config/bigscreen/config.py"
echo "   - $SCRIPT_DIR/config/boot/application-prod.yml"
echo ""
echo "🚀 启动服务:"
echo "   cd $SCRIPT_DIR"
echo "   docker-compose up -d"
echo ""
echo "🔍 查看服务:"
echo "   docker-compose ps"
echo "   docker-compose logs -f [service_name]"