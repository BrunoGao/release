#!/bin/bash

# Ubuntu 22.04 初始化脚本
# 适用于灵境万象健康管理系统(LJWX) + CI/CD基础设施
# 版本: v1.0
# 日期: 2025-01-23

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统版本
check_system() {
    log_info "检查系统版本..."
    
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测系统版本"
        exit 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]] || [[ "$VERSION_ID" != "22.04" ]]; then
        log_warning "检测到系统: $PRETTY_NAME"
        log_warning "此脚本专为Ubuntu 22.04设计，可能存在兼容性问题"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "系统版本检查通过: Ubuntu 22.04"
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包管理器..."
    
    # 更新包列表
    apt update
    
    # 升级系统包
    log_info "升级系统包..."
    apt upgrade -y
    
    # 安装基础工具
    log_info "安装基础工具..."
    apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        tree \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        net-tools \
        telnet \
        jq \
        build-essential
    
    log_success "系统更新完成"
}

# 安装Docker
install_docker() {
    log_info "安装Docker..."
    
    # 检查Docker是否已安装
    if command -v docker &> /dev/null; then
        log_warning "Docker已安装，版本: $(docker --version)"
        return 0
    fi
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker APT仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 更新包列表
    apt update
    
    # 安装Docker
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    # 添加当前用户到docker组（如果不是root用户）
    if [[ $SUDO_USER ]]; then
        usermod -aG docker $SUDO_USER
        log_info "用户 $SUDO_USER 已添加到docker组，请重新登录生效"
    fi
    
    log_success "Docker安装完成，版本: $(docker --version)"
}

# 安装Docker Compose (Legacy)
install_docker_compose() {
    log_info "安装Docker Compose (Legacy)..."
    
    # 检查docker-compose是否已安装
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose已安装，版本: $(docker-compose --version)"
        return 0
    fi
    
    # 下载最新版本的docker-compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
    curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 赋予执行权限
    chmod +x /usr/local/bin/docker-compose
    
    # 创建软链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose安装完成，版本: $(docker-compose --version)"
}

# 安装Java JDK 21
install_java() {
    log_info "安装Java JDK 21..."
    
    # 检查Java是否已安装
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | grep -o 'openjdk version "[^"]*"' | cut -d'"' -f2)
        log_warning "Java已安装，版本: $JAVA_VERSION"
        
        # 检查是否为JDK 21
        if [[ $JAVA_VERSION == *"21"* ]]; then
            log_success "JDK 21已安装"
            return 0
        else
            log_warning "当前Java版本不是JDK 21，将安装JDK 21"
        fi
    fi
    
    # 安装OpenJDK 21
    apt install -y openjdk-21-jdk
    
    # 设置JAVA_HOME环境变量
    echo 'export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64' >> /etc/environment
    echo 'export PATH=$PATH:$JAVA_HOME/bin' >> /etc/environment
    
    # 更新alternatives
    update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-21-openjdk-amd64/bin/java 1
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-21-openjdk-amd64/bin/javac 1
    
    log_success "Java JDK 21安装完成"
}

# 安装Maven
install_maven() {
    log_info "安装Maven..."
    
    # 检查Maven是否已安装
    if command -v mvn &> /dev/null; then
        log_warning "Maven已安装，版本: $(mvn -version | head -n 1)"
        return 0
    fi
    
    # 安装Maven
    apt install -y maven
    
    log_success "Maven安装完成，版本: $(mvn -version | head -n 1)"
}

# 安装Node.js
install_nodejs() {
    log_info "安装Node.js..."
    
    # 检查Node.js是否已安装
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_warning "Node.js已安装，版本: $NODE_VERSION"
        
        # 检查版本是否大于等于18
        NODE_MAJOR_VERSION=$(echo $NODE_VERSION | cut -d. -f1 | sed 's/v//')
        if [[ $NODE_MAJOR_VERSION -ge 18 ]]; then
            log_success "Node.js版本满足要求(>=18)"
            return 0
        else
            log_warning "Node.js版本过低，将安装最新LTS版本"
        fi
    fi
    
    # 添加NodeSource仓库
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    
    # 安装Node.js
    apt install -y nodejs
    
    # 安装pnpm
    npm install -g pnpm
    
    log_success "Node.js安装完成，版本: $(node --version)"
    log_success "npm版本: $(npm --version)"
    log_success "pnpm版本: $(pnpm --version)"
}

# 安装Python3和pip
install_python() {
    log_info "安装Python3和pip..."
    
    # 检查Python3是否已安装
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_warning "Python3已安装，版本: $PYTHON_VERSION"
    else
        # 安装Python3
        apt install -y python3 python3-pip python3-venv
    fi
    
    # 安装pipenv
    pip3 install pipenv
    
    # 创建python命令软链接
    if [[ ! -f /usr/bin/python ]]; then
        ln -sf /usr/bin/python3 /usr/bin/python
    fi
    
    log_success "Python3安装完成，版本: $(python3 --version)"
    log_success "pip版本: $(pip3 --version)"
}

# 安装MySQL
install_mysql() {
    log_info "安装MySQL 8.0..."
    
    # 检查MySQL是否已安装
    if command -v mysql &> /dev/null; then
        log_warning "MySQL已安装"
        return 0
    fi
    
    # 安装MySQL
    apt install -y mysql-server mysql-client
    
    # 启动MySQL服务
    systemctl start mysql
    systemctl enable mysql
    
    log_success "MySQL安装完成"
    log_warning "请手动运行 mysql_secure_installation 来配置MySQL安全设置"
}

# 安装Redis
install_redis() {
    log_info "安装Redis..."
    
    # 检查Redis是否已安装
    if command -v redis-server &> /dev/null; then
        log_warning "Redis已安装，版本: $(redis-server --version)"
        return 0
    fi
    
    # 安装Redis
    apt install -y redis-server
    
    # 启动Redis服务
    systemctl start redis-server
    systemctl enable redis-server
    
    log_success "Redis安装完成，版本: $(redis-server --version)"
}

# 安装Nginx
install_nginx() {
    log_info "安装Nginx..."
    
    # 检查Nginx是否已安装
    if command -v nginx &> /dev/null; then
        log_warning "Nginx已安装，版本: $(nginx -v 2>&1)"
        return 0
    fi
    
    # 安装Nginx
    apt install -y nginx
    
    # 启动Nginx服务
    systemctl start nginx
    systemctl enable nginx
    
    log_success "Nginx安装完成，版本: $(nginx -v 2>&1)"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否安装
    if ! command -v ufw &> /dev/null; then
        apt install -y ufw
    fi
    
    # 配置基础规则
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # 允许SSH
    ufw allow 22/tcp
    
    # 允许LJWX系统端口
    ufw allow 3306/tcp     # MySQL
    ufw allow 6379/tcp     # Redis
    ufw allow 8001/tcp     # ljwx-bigscreen
    ufw allow 8088/tcp     # ljwx-admin
    ufw allow 9998/tcp     # ljwx-boot
    
    # 允许CI/CD基础设施端口
    ufw allow 33000/tcp    # Gitea Web
    ufw allow 32222/tcp    # Gitea SSH
    ufw allow 38080/tcp    # Jenkins
    ufw allow 35001/tcp    # Docker Registry
    ufw allow 35002/tcp    # Registry UI
    
    # 允许HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # 启用防火墙
    ufw --force enable
    
    log_success "防火墙配置完成"
    ufw status
}

# 优化系统参数
optimize_system() {
    log_info "优化系统参数..."
    
    # 优化内核参数
    cat > /etc/sysctl.d/99-ljwx-optimization.conf << 'EOF'
# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# 文件句柄优化
fs.file-max = 1000000
fs.nr_open = 1000000

# 虚拟内存优化
vm.max_map_count = 262144
vm.swappiness = 10

# Docker优化
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF
    
    # 应用内核参数
    sysctl -p /etc/sysctl.d/99-ljwx-optimization.conf
    
    # 优化文件句柄限制
    cat > /etc/security/limits.d/99-ljwx.conf << 'EOF'
# LJWX系统文件句柄优化
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
root soft nofile 65535
root hard nofile 65535
root soft nproc 65535
root hard nproc 65535
EOF
    
    log_success "系统参数优化完成"
}

# 创建项目目录结构
create_project_structure() {
    log_info "创建项目目录结构..."
    
    # 创建主目录
    mkdir -p /opt/ljwx
    cd /opt/ljwx
    
    # 创建子目录
    mkdir -p {data,logs,backup,config,scripts}
    mkdir -p data/{mysql,redis,jenkins,gitea}
    mkdir -p logs/{mysql,redis,ljwx-boot,ljwx-admin,ljwx-bigscreen,jenkins,gitea}
    mkdir -p backup/{mysql,redis,ljwx-boot,ljwx-admin,ljwx-bigscreen,jenkins,gitea}
    mkdir -p config/{mysql,redis,nginx,jenkins,gitea}
    
    # 设置权限
    chown -R $SUDO_USER:$SUDO_USER /opt/ljwx 2>/dev/null || true
    chmod -R 755 /opt/ljwx
    
    log_success "项目目录结构创建完成: /opt/ljwx"
}

# 生成配置文件模板
generate_config_templates() {
    log_info "生成配置文件模板..."
    
    # Docker Compose环境变量模板
    cat > /opt/ljwx/config/ljwx.env << 'EOF'
# LJWX系统配置
COMPOSE_VERSION=3.8

# MySQL配置
MYSQL_IMAGE_VERSION=1.3.3
MYSQL_PASSWORD=ljwx_mysql_2024
MYSQL_DATABASE=ljwx_health
MYSQL_EXTERNAL_PORT=3306
MYSQL_HOST=ljwx-mysql
MYSQL_PORT=3306
MYSQL_USER=root

# Redis配置
REDIS_IMAGE_VERSION=1.3.3
REDIS_EXTERNAL_PORT=6379
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=ljwx_redis_2024

# ljwx-boot配置
LJWX_BOOT_VERSION=1.3.8
LJWX_BOOT_EXTERNAL_PORT=9998

# ljwx-admin配置
LJWX_ADMIN_VERSION=1.3.8
LJWX_ADMIN_EXTERNAL_PORT=8088
VITE_APP_TITLE=灵境万象健康管理系统

# ljwx-bigscreen配置
LJWX_BIGSCREEN_VERSION=1.3.8
LJWX_BIGSCREEN_EXTERNAL_PORT=8001
VITE_BIGSCREEN_URL=http://localhost:8001
EOF
    
    # CI/CD环境变量模板
    cat > /opt/ljwx/config/cicd.env << 'EOF'
# CI/CD基础设施配置

# Gitea配置
GITEA_VERSION=1.21
GITEA_HTTP_PORT=33000
GITEA_SSH_PORT=32222
GITEA_DB_TYPE=sqlite3

# Jenkins配置
JENKINS_VERSION=lts-jdk21
JENKINS_HTTP_PORT=38080
JENKINS_AGENT_PORT=35000
JENKINS_ADMIN_ID=admin
JENKINS_ADMIN_PASSWORD=ljwx_jenkins_2024

# Docker Registry配置
REGISTRY_VERSION=2
REGISTRY_PORT=35001
REGISTRY_UI_PORT=35002

# 监控配置 (可选)
PROMETHEUS_PORT=37001
GRAFANA_PORT=37002
EOF
    
    # 系统维护脚本
    cat > /opt/ljwx/scripts/system-status.sh << 'EOF'
#!/bin/bash
# LJWX系统状态检查脚本

echo "=== LJWX系统状态检查 ==="
echo

# 检查Docker服务
echo "1. Docker服务状态:"
systemctl is-active docker

# 检查MySQL服务
echo "2. MySQL服务状态:"
systemctl is-active mysql

# 检查Redis服务
echo "3. Redis服务状态:"
systemctl is-active redis-server

# 检查Nginx服务
echo "4. Nginx服务状态:"
systemctl is-active nginx

# 检查Docker容器
echo "5. Docker容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 检查端口占用
echo "6. 关键端口占用:"
netstat -tlnp | grep -E ':(3306|6379|8001|8088|9998|33000|38080|35001|35002)'

echo
echo "=== 检查完成 ==="
EOF
    
    chmod +x /opt/ljwx/scripts/system-status.sh
    
    log_success "配置文件模板生成完成"
}

# 安装常用工具
install_utilities() {
    log_info "安装常用工具..."
    
    # 安装监控工具
    apt install -y \
        htop \
        iotop \
        nethogs \
        iftop \
        nload \
        sysstat \
        tree \
        ncdu
    
    # 安装开发工具
    apt install -y \
        git \
        vim \
        nano \
        screen \
        tmux \
        zip \
        unzip \
        rsync
    
    # 安装网络工具
    apt install -y \
        curl \
        wget \
        net-tools \
        telnet \
        nmap \
        tcpdump \
        dnsutils
    
    log_success "常用工具安装完成"
}

# 主函数
main() {
    log_info "开始Ubuntu 22.04系统初始化..."
    log_info "适用于灵境万象健康管理系统(LJWX) + CI/CD基础设施"
    echo
    
    check_root
    check_system
    
    echo
    log_info "即将执行以下操作:"
    echo "1. 更新系统包"
    echo "2. 安装Docker和Docker Compose"
    echo "3. 安装Java JDK 21和Maven"
    echo "4. 安装Node.js和npm/pnpm"
    echo "5. 安装Python3和pip"
    echo "6. 安装MySQL 8.0"
    echo "7. 安装Redis"
    echo "8. 安装Nginx"
    echo "9. 配置防火墙"
    echo "10. 优化系统参数"
    echo "11. 创建项目目录结构"
    echo "12. 生成配置文件模板"
    echo "13. 安装常用工具"
    echo
    
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi
    
    echo
    log_info "开始执行初始化..."
    echo
    
    # 执行安装步骤
    update_system
    install_docker
    install_docker_compose
    install_java
    install_maven
    install_nodejs
    install_python
    install_mysql
    install_redis
    install_nginx
    configure_firewall
    optimize_system
    create_project_structure
    generate_config_templates
    install_utilities
    
    echo
    log_success "===== Ubuntu 22.04初始化完成! ====="
    echo
    log_info "下一步操作建议:"
    echo "1. 重新登录或运行 'source /etc/environment' 以加载环境变量"
    echo "2. 运行 'mysql_secure_installation' 配置MySQL安全设置"
    echo "3. 检查系统状态: /opt/ljwx/scripts/system-status.sh"
    echo "4. 克隆LJWX项目代码到 /opt/ljwx/"
    echo "5. 根据需要修改配置文件: /opt/ljwx/config/"
    echo
    log_info "系统已准备就绪，可以部署LJWX健康管理系统!"
    echo
    
    # 显示安装的软件版本
    echo "========== 已安装软件版本 =========="
    echo "Docker: $(docker --version 2>/dev/null || echo '未安装')"
    echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo '未安装')"
    echo "Java: $(java -version 2>&1 | head -n1 2>/dev/null || echo '未安装')"
    echo "Maven: $(mvn -version 2>/dev/null | head -n1 || echo '未安装')"
    echo "Node.js: $(node --version 2>/dev/null || echo '未安装')"
    echo "npm: $(npm --version 2>/dev/null || echo '未安装')"
    echo "Python3: $(python3 --version 2>/dev/null || echo '未安装')"
    echo "MySQL: $(mysql --version 2>/dev/null || echo '未安装')"
    echo "Redis: $(redis-server --version 2>/dev/null || echo '未安装')"
    echo "Nginx: $(nginx -v 2>&1 || echo '未安装')"
    echo "=================================="
}

# 执行主函数
main "$@"