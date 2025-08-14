#!/bin/bash
# 动态生成docker-compose配置 #智能处理首次部署和升级部署

# 检查是否为首次部署
is_first_deployment() {
    for volume in mysql_data redis_data ljwx_boot_data ljwx_bigscreen_data; do
        if docker volume ls -q | grep -q "^client-deployment_${volume}$"; then
            return 1 #不是首次部署
        fi
    done
    return 0 #首次部署
}

# 生成MySQL服务配置
generate_mysql_config() {
    local client_data_mount=""
    
    # 只有首次部署且client-data.sql存在时才挂载
    if is_first_deployment && [ -f "client-data.sql" ] && [ -s "client-data.sql" ]; then
        client_data_mount="      - ./client-data.sql:/docker-entrypoint-initdb.d/client/data.sql:ro"
        echo "📦 首次部署: 启用client-data.sql挂载"
    else
        echo "🔄 升级部署: 跳过client-data.sql挂载"
    fi

    cat > docker-compose-generated.yml << EOF
services:
  mysql:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-mysql:1.2.16
    container_name: ljwx-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: \${MYSQL_DATABASE:-lj-06}
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./logs/mysql:/var/log/mysql
      - ./backup/mysql:/backup/mysql
$client_data_mount
    command:
      - --default-authentication-plugin=mysql_native_password
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --max_connections=200
      - --wait_timeout=28800
      - --interactive_timeout=28800
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p123456"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    networks:
      - ljwx-network

  redis:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-redis:1.2.16
    container_name: ljwx-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./logs/redis:/var/log/redis
      - ./backup/redis:/backup/redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - ljwx-network

  ljwx-boot:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-boot:1.2.16
    container_name: ljwx-boot
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      SPRING_PROFILES_ACTIVE: common
      MYSQL_HOST: \${MYSQL_HOST:-mysql}
      MYSQL_PORT: \${MYSQL_PORT:-3306}
      MYSQL_USER: \${MYSQL_USER:-root}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: \${MYSQL_DATABASE:-lj-06}
      REDIS_HOST: \${REDIS_HOST:-redis}
      REDIS_PORT: \${REDIS_PORT:-6379}
      REDIS_PASSWORD: "123456"
      TZ: Asia/Shanghai
      SPRING_DATASOURCE_URL: jdbc:mysql://\${MYSQL_HOST:-mysql}:\${MYSQL_PORT:-3306}/\${MYSQL_DATABASE:-lj-06}?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
      SPRING_DATASOURCE_USERNAME: \${MYSQL_USER:-root}
      SPRING_DATASOURCE_PASSWORD: \${MYSQL_PASSWORD:-123456}
      SPRING_DATASOURCE_DRIVER_CLASS_NAME: com.mysql.cj.jdbc.Driver
      SPRING_DATA_REDIS_HOST: \${REDIS_HOST:-redis}
      SPRING_DATA_REDIS_PORT: \${REDIS_PORT:-6379}
      SPRING_DATA_REDIS_PASSWORD: "123456"
    ports:
      - "9998:9998"
    volumes:
      - ./logs/ljwx-boot:/app/ljwx-boot-logs
      - ljwx_boot_data:/app/data
      - ./backup/ljwx-boot:/backup/ljwx-boot
    command: ["sh", "-c", "sleep 30 && java -jar /app/ljwx-boot-admin.jar"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9998/actuator/health"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 120s
    networks:
      - ljwx-network

  ljwx-bigscreen:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-bigscreen:1.2.16
    container_name: ljwx-bigscreen
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      MYSQL_HOST: \${MYSQL_HOST:-mysql}
      MYSQL_PORT: \${MYSQL_PORT:-3306}
      MYSQL_USER: \${MYSQL_USER:-root}
      MYSQL_PASSWORD: \${MYSQL_PASSWORD:-123456}
      MYSQL_DATABASE: \${MYSQL_DATABASE:-lj-06}
      REDIS_HOST: \${REDIS_HOST:-redis}
      REDIS_PORT: \${REDIS_PORT:-6379}
      REDIS_PASSWORD: \${REDIS_PASSWORD:-123456}
      IS_DOCKER: "true"
      APP_PORT: 8001
      TZ: Asia/Shanghai
    ports:
      - "8001:8001"
    volumes:
      - ./custom-config.py:/app/config.py:ro
      - ./custom-assets:/app/static/images:ro
      - ./logs/ljwx-bigscreen:/app/logs
      - ljwx_bigscreen_data:/app/data
      - ./backup/ljwx-bigscreen:/backup/ljwx-bigscreen
    command: ["sh", "-c", "sleep 45 && python app.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 90s
    networks:
      - ljwx-network

  ljwx-admin:
    image: crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-admin:1.2.16
    container_name: ljwx-admin
    restart: unless-stopped
    env_file:
      - custom-config.env
    environment:
      VITE_API_URL: http://ljwx-boot:9998
      VITE_BIGSCREEN_URL: \${VITE_BIGSCREEN_URL:-http://localhost:8001}
      VITE_APP_TITLE: \${VITE_APP_TITLE:-穿戴管理演示系统}
      TZ: Asia/Shanghai
    ports:
      - "8080:80"
    volumes:
      - ./logs/ljwx-admin:/var/log/nginx
      - ./custom-admin-config.js:/tmp/custom-admin-config.js:ro
    command: ["sh", "-c", "sleep 60 && nginx -g 'daemon off;'"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 60s
      timeout: 5s
      retries: 3
      start_period: 60s
    networks:
      - ljwx-network

volumes:
  mysql_data:
  redis_data:
  ljwx_boot_data:
  ljwx_bigscreen_data:

networks:
  ljwx-network:
    driver: bridge
EOF

    echo "✅ docker-compose-generated.yml 已生成"
}

# 主函数
main() {
    echo "🔧 生成动态docker-compose配置..."
    generate_mysql_config
    echo "✅ 配置生成完成"
}

main "$@" 