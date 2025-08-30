#!/bin/bash

set -e

DOCKER_VERSION="24.0.7"
DOCKER_COMPOSE_VERSION="2.24.5"
CONTAINERD_VERSION="1.7.11"
RUNC_VERSION="1.1.10"
DOWNLOAD_DIR="docker-offline-packages"

echo "=== Docker 离线安装包下载脚本 ==="
echo "Docker版本: $DOCKER_VERSION"
echo "Docker Compose版本: $DOCKER_COMPOSE_VERSION"
echo ""

# 检测操作系统和架构
detect_os_arch() {
    OS=""
    ARCH=""
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="darwin"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        echo "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    # 检测架构
    case $(uname -m) in
        x86_64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        armv7l)
            ARCH="armv7"
            ;;
        *)
            echo "不支持的架构: $(uname -m)"
            exit 1
            ;;
    esac
    
    echo "检测到系统: $OS-$ARCH"
}

# 选择目标系统
select_target_os() {
    echo ""
    echo "请选择目标系统:"
    echo "1) Linux x86_64 (amd64)"
    echo "2) Linux ARM64 (aarch64)"
    echo "3) Linux ARMv7"
    echo "4) macOS x86_64 (Intel)"
    echo "5) macOS ARM64 (Apple Silicon)"
    echo "6) Windows x86_64"
    echo "7) 自动检测当前系统"
    echo "8) 下载全部平台"
    echo ""
    read -p "请输入选择 (1-8): " choice
    
    case $choice in
        1) TARGET_OS="linux"; TARGET_ARCH="amd64" ;;
        2) TARGET_OS="linux"; TARGET_ARCH="arm64" ;;
        3) TARGET_OS="linux"; TARGET_ARCH="armv7" ;;
        4) TARGET_OS="darwin"; TARGET_ARCH="amd64" ;;
        5) TARGET_OS="darwin"; TARGET_ARCH="arm64" ;;
        6) TARGET_OS="windows"; TARGET_ARCH="amd64" ;;
        7) detect_os_arch; TARGET_OS="$OS"; TARGET_ARCH="$ARCH" ;;
        8) TARGET_OS="all"; TARGET_ARCH="all" ;;
        *) echo "无效选择"; exit 1 ;;
    esac
}

download_for_platform() {
    local os=$1
    local arch=$2
    local platform_dir="${DOWNLOAD_DIR}/${os}-${arch}"
    
    echo ""
    echo "=== 下载 $os-$arch 平台文件 ==="
    mkdir -p "$platform_dir"
    
    # Docker 二进制文件URL映射
    case "$os-$arch" in
        "linux-amd64")
            DOCKER_URL="https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz"
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64"
            CONTAINERD_URL="https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-amd64.tar.gz"
            RUNC_URL="https://github.com/opencontainers/runc/releases/download/v${RUNC_VERSION}/runc.amd64"
            ;;
        "linux-arm64")
            DOCKER_URL="https://download.docker.com/linux/static/stable/aarch64/docker-${DOCKER_VERSION}.tgz"
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-aarch64"
            CONTAINERD_URL="https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-arm64.tar.gz"
            RUNC_URL="https://github.com/opencontainers/runc/releases/download/v${RUNC_VERSION}/runc.arm64"
            ;;
        "linux-armv7")
            DOCKER_URL="https://download.docker.com/linux/static/stable/armhf/docker-${DOCKER_VERSION}.tgz"
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-armv7"
            CONTAINERD_URL="https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-arm.v7.tar.gz"
            RUNC_URL="https://github.com/opencontainers/runc/releases/download/v${RUNC_VERSION}/runc.armhf"
            ;;
        "darwin-amd64")
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-darwin-x86_64"
            echo "  注意: macOS 建议使用 Docker Desktop，此处仅下载 Docker Compose"
            ;;
        "darwin-arm64")
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-darwin-aarch64"
            echo "  注意: macOS 建议使用 Docker Desktop，此处仅下载 Docker Compose"
            ;;
        "windows-amd64")
            COMPOSE_URL="https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-windows-x86_64.exe"
            echo "  注意: Windows 建议使用 Docker Desktop，此处仅下载 Docker Compose"
            ;;
        *)
            echo "不支持的平台: $os-$arch"
            return 1
            ;;
    esac
    
    # 下载文件
    if [[ "$os" == "linux" ]]; then
        echo "  下载 Docker..."
        wget "$DOCKER_URL" -O "$platform_dir/docker-${DOCKER_VERSION}.tgz"
        
        echo "  下载 containerd..."
        wget "$CONTAINERD_URL" -O "$platform_dir/containerd-${CONTAINERD_VERSION}-${os}-${arch}.tar.gz"
        
        echo "  下载 runc..."
        wget "$RUNC_URL" -O "$platform_dir/runc-${RUNC_VERSION}.${arch}"
    fi
    
    echo "  下载 Docker Compose..."
    if [[ "$os" == "windows" ]]; then
        wget "$COMPOSE_URL" -O "$platform_dir/docker-compose-${DOCKER_COMPOSE_VERSION}.exe"
    else
        wget "$COMPOSE_URL" -O "$platform_dir/docker-compose-${DOCKER_COMPOSE_VERSION}"
    fi
}

select_target_os

mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

if [[ "$TARGET_OS" == "all" ]]; then
    # 下载所有平台
    platforms=("linux-amd64" "linux-arm64" "linux-armv7" "darwin-amd64" "darwin-arm64" "windows-amd64")
    for platform in "${platforms[@]}"; do
        IFS='-' read -r os arch <<< "$platform"
        download_for_platform "$os" "$arch" || echo "  下载 $platform 失败"
    done
else
    download_for_platform "$TARGET_OS" "$TARGET_ARCH"
fi

cd ..

# 为每个平台创建安装脚本
create_install_scripts() {
    if [[ "$TARGET_OS" == "all" ]]; then
        platforms=("linux-amd64" "linux-arm64" "linux-armv7")
        for platform in "${platforms[@]}"; do
            IFS='-' read -r os arch <<< "$platform"
            create_linux_install_script "$os" "$arch"
        done
        create_macos_install_script
        create_windows_install_script
    elif [[ "$TARGET_OS" == "linux" ]]; then
        create_linux_install_script "$TARGET_OS" "$TARGET_ARCH"
    elif [[ "$TARGET_OS" == "darwin" ]]; then
        create_macos_install_script
    elif [[ "$TARGET_OS" == "windows" ]]; then
        create_windows_install_script
    fi
}

# 创建Linux安装脚本
create_linux_install_script() {
    local os=$1
    local arch=$2
    local platform_dir="${os}-${arch}"
    
    echo "  创建 ${platform_dir}/install-docker-offline.sh..."
    
    cat > "${platform_dir}/install-docker-offline.sh" << EOF
#!/bin/bash

set -e

DOCKER_VERSION="$DOCKER_VERSION"
DOCKER_COMPOSE_VERSION="$DOCKER_COMPOSE_VERSION"
CONTAINERD_VERSION="$CONTAINERD_VERSION"
RUNC_VERSION="$RUNC_VERSION"
ARCH="$arch"

echo "=== Docker 离线安装脚本 ($os-$arch) ==="
echo ""

# 检查是否为root用户
if [[ \$EUID -ne 0 ]]; then
   echo "错误: 此脚本需要root权限运行"
   exit 1
fi

# 检测Linux发行版
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=\$ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="centos"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    echo "检测到Linux发行版: \$DISTRO"
}

detect_distro

echo "1. 停止现有的Docker服务..."
systemctl stop docker 2>/dev/null || true
systemctl stop containerd 2>/dev/null || true

echo "2. 安装 containerd..."
tar -C /usr/local -xzf "containerd-\${CONTAINERD_VERSION}-${os}-${arch}.tar.gz"

echo "3. 安装 runc..."
install -m 755 "runc-\${RUNC_VERSION}.\${ARCH}" /usr/local/sbin/runc

echo "4. 安装 Docker..."
tar -xzf "docker-\${DOCKER_VERSION}.tgz"
cp docker/* /usr/bin/

echo "5. 安装 Docker Compose..."
install -m 755 "docker-compose-\${DOCKER_COMPOSE_VERSION}" /usr/local/bin/docker-compose

echo "6. 创建 containerd 配置..."
mkdir -p /etc/containerd
/usr/local/bin/containerd config default | tee /etc/containerd/config.toml

echo "7. 创建 containerd systemd 服务..."
cat > /etc/systemd/system/containerd.service << 'SERVICE_EOF'
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target local-fs.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/local/bin/containerd

Type=notify
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNPROC=infinity
LimitCORE=infinity
LimitNOFILE=infinity
TasksMax=infinity
OOMScoreAdjust=-999

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "8. 创建 Docker systemd 服务..."
cat > /etc/systemd/system/docker.service << 'SERVICE_EOF'
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service containerd.service
Wants=network-online.target
Requires=docker.socket containerd.service

[Service]
Type=notify
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
ExecReload=/bin/kill -s HUP \$MAINPID
TimeoutStartSec=0
RestartSec=2
Restart=always
StartLimitBurst=3
StartLimitInterval=60s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "9. 创建 Docker socket..."
cat > /etc/systemd/system/docker.socket << 'SERVICE_EOF'
[Unit]
Description=Docker Socket for the API

[Socket]
ListenStream=/var/run/docker.sock
SocketMode=0660
SocketUser=root
SocketGroup=docker

[Install]
WantedBy=sockets.target
SERVICE_EOF

echo "10. 创建 docker 组..."
groupadd docker 2>/dev/null || true

echo "11. 重新加载 systemd..."
systemctl daemon-reload

echo "12. 启用并启动服务..."
systemctl enable containerd
systemctl start containerd
systemctl enable docker.socket
systemctl enable docker
systemctl start docker

echo "13. 验证安装..."
docker version
docker-compose --version

echo ""
echo "=== Docker 离线安装完成! ==="
echo "提示:"
echo "- 将用户添加到docker组: usermod -aG docker \\\$USER"
echo "- 然后重新登录或运行: newgrp docker"
EOF
    
    chmod +x "${platform_dir}/install-docker-offline.sh"
}

# 创建macOS安装脚本
create_macos_install_script() {
    if [[ "$TARGET_ARCH" == "all" ]]; then
        archs=("amd64" "arm64")
    else
        archs=("$TARGET_ARCH")
    fi
    
    for arch in "${archs[@]}"; do
        local platform_dir="darwin-${arch}"
        echo "  创建 ${platform_dir}/install-docker-compose.sh..."
        
        cat > "${platform_dir}/install-docker-compose.sh" << EOF
#!/bin/bash

set -e

echo "=== macOS Docker Compose 安装脚本 (darwin-${arch}) ==="
echo ""
echo "注意: macOS 建议安装 Docker Desktop 来获得完整的 Docker 功能"
echo "此脚本仅安装 Docker Compose"
echo ""

echo "安装 Docker Compose..."
sudo install -m 755 "docker-compose-${DOCKER_COMPOSE_VERSION}" /usr/local/bin/docker-compose

echo "验证安装..."
docker-compose --version

echo ""
echo "=== Docker Compose 安装完成! ==="
echo ""
echo "如需完整的 Docker 功能，请："
echo "1. 访问 https://docs.docker.com/desktop/mac/"
echo "2. 下载并安装 Docker Desktop for Mac"
EOF
        
        chmod +x "${platform_dir}/install-docker-compose.sh"
    done
}

# 创建Windows安装脚本
create_windows_install_script() {
    local platform_dir="windows-amd64"
    echo "  创建 ${platform_dir}/install-docker-compose.bat..."
    
    cat > "${platform_dir}/install-docker-compose.bat" << 'EOF'
@echo off
echo === Windows Docker Compose 安装脚本 ===
echo.
echo 注意: Windows 建议安装 Docker Desktop 来获得完整的 Docker 功能
echo 此脚本仅安装 Docker Compose
echo.

echo 安装 Docker Compose...
copy "docker-compose-${DOCKER_COMPOSE_VERSION}.exe" "C:\Program Files\Docker\docker-compose.exe"

echo 验证安装...
docker-compose --version

echo.
echo === Docker Compose 安装完成! ===
echo.
echo 如需完整的 Docker 功能，请：
echo 1. 访问 https://docs.docker.com/desktop/windows/
echo 2. 下载并安装 Docker Desktop for Windows
pause
EOF
}

echo ""
echo "创建安装脚本..."
create_install_scripts

# 为每个平台创建镜像导入脚本
create_image_import_scripts() {
    if [[ "$TARGET_OS" == "all" ]]; then
        platforms=("linux-amd64" "linux-arm64" "linux-armv7" "darwin-amd64" "darwin-arm64")
        for platform in "${platforms[@]}"; do
            IFS='-' read -r os arch <<< "$platform"
            create_image_import_script "$os" "$arch"
        done
    else
        create_image_import_script "$TARGET_OS" "$TARGET_ARCH"
    fi
}

create_image_import_script() {
    local os=$1
    local arch=$2
    local platform_dir="${os}-${arch}"
    
    echo "  创建 ${platform_dir}/import-docker-images.sh..."
    
    if [[ "$os" == "windows" ]]; then
        # Windows批处理脚本
        cat > "${platform_dir}/import-docker-images.bat" << 'EOF'
@echo off
set IMAGES_DIR=docker-images

echo === Docker 镜像离线导入脚本 (Windows) ===
echo.

if not exist "%IMAGES_DIR%" (
    echo 错误: 镜像目录 %IMAGES_DIR% 不存在
    echo 请先使用 export-docker-images.bat 导出镜像
    pause
    exit /b 1
)

echo 开始导入镜像...
for %%f in ("%IMAGES_DIR%\*.tar") do (
    echo 导入: %%~nxf
    docker load < "%%f"
)

echo.
echo === 镜像导入完成! ===
echo.
echo 当前镜像列表:
docker images
pause
EOF
    else
        # Linux/macOS shell脚本
        cat > "${platform_dir}/import-docker-images.sh" << 'EOF'
#!/bin/bash

set -e

IMAGES_DIR="docker-images"

echo "=== Docker 镜像离线导入脚本 ==="
echo ""

if [ ! -d "$IMAGES_DIR" ]; then
    echo "错误: 镜像目录 $IMAGES_DIR 不存在"
    echo "请先使用 export-docker-images.sh 导出镜像"
    exit 1
fi

echo "开始导入镜像..."
for image_file in "$IMAGES_DIR"/*.tar; do
    if [ -f "$image_file" ]; then
        echo "导入: $(basename "$image_file")"
        docker load < "$image_file"
    fi
done

echo ""
echo "=== 镜像导入完成! ==="
echo ""
echo "当前镜像列表:"
docker images
EOF
        chmod +x "${platform_dir}/import-docker-images.sh"
    fi
}

echo "创建镜像导入脚本..."
create_image_import_scripts

echo ""
echo "=== 下载完成! ==="
echo ""

if [[ "$TARGET_OS" == "all" ]]; then
    echo "下载的平台目录:"
    ls -la docker-offline-packages/
    echo ""
    echo "使用说明:"
    echo "1. 将对应的 docker-offline-packages/<平台> 目录复制到目标服务器"
    echo "2. Linux: sudo bash <平台>/install-docker-offline.sh"
    echo "3. macOS: bash <平台>/install-docker-compose.sh"
    echo "4. Windows: 运行 <平台>/install-docker-compose.bat"
    echo "5. 导入镜像 (如果有): bash <平台>/import-docker-images.sh"
else
    platform_dir="${TARGET_OS}-${TARGET_ARCH}"
    echo "下载的文件 (${platform_dir}):"
    ls -la "docker-offline-packages/${platform_dir}/"
    echo ""
    echo "使用说明:"
    echo "1. 将 docker-offline-packages/${platform_dir} 目录复制到离线服务器"
    
    if [[ "$TARGET_OS" == "linux" ]]; then
        echo "2. 在离线服务器上运行: sudo bash ${platform_dir}/install-docker-offline.sh"
        echo "3. 如需导入镜像，使用: bash ${platform_dir}/import-docker-images.sh"
    elif [[ "$TARGET_OS" == "darwin" ]]; then
        echo "2. 在Mac上运行: bash ${platform_dir}/install-docker-compose.sh"
        echo "3. 如需导入镜像，使用: bash ${platform_dir}/import-docker-images.sh"
        echo "注意: macOS建议使用Docker Desktop获得完整功能"
    elif [[ "$TARGET_OS" == "windows" ]]; then
        echo "2. 在Windows上运行: ${platform_dir}/install-docker-compose.bat"
        echo "3. 如需导入镜像，使用: ${platform_dir}/import-docker-images.bat"
        echo "注意: Windows建议使用Docker Desktop获得完整功能"
    fi
fi

echo ""
echo "支持的平台:"
echo "- Linux: x86_64(amd64), ARM64, ARMv7"  
echo "- macOS: x86_64(Intel), ARM64(Apple Silicon)"
echo "- Windows: x86_64"