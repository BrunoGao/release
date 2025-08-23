#!/bin/bash

# GitHub Actions Self-hosted Runner 安装脚本

RUNNER_DIR="/Users/brunogao/work/infra/cicd/github-actions/runner"
RUNNER_VERSION="2.311.0"  # 最新版本

echo "=== 安装 GitHub Actions Runner ==="

# 创建运行目录
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# 下载 Runner
curl -o actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz

# 解压
tar xzf ./actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz

echo "=== Runner 安装完成 ==="
echo "请执行以下步骤完成配置："
echo "1. 在 GitHub 仓库中获取 Runner Token"
echo "2. 运行: ./config.sh --url https://github.com/your-username/your-repo --token YOUR_TOKEN"
echo "3. 运行: ./run.sh" 