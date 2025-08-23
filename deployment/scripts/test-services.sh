#!/bin/bash

# 测试服务连接性

echo "=== 测试服务连接性 ==="

# 测试 Gitea
echo "测试 Gitea (http://192.168.1.83:3000)..."
curl -I http://192.168.1.83:3000 2>/dev/null | head -1

# 测试 Drone
echo "测试 Drone (http://localhost:9000)..."
curl -I http://localhost:9000 2>/dev/null | head -1

# 测试 Registry
echo "测试 Registry (http://localhost:5000)..."
curl -I http://localhost:5000/v2/ 2>/dev/null | head -1

echo "=== 测试完成 ===" 