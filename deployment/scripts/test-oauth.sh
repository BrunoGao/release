#!/bin/bash

# 测试 OAuth 配置

CLIENT_ID="1ccb6bfa-52d4-4b3b-8428-2e0caef43a39"
REDIRECT_URI="http://192.168.1.83:9000/login"
GITEA_SERVER="http://192.168.1.83:3000"

echo "=== 测试 OAuth 配置 ==="
echo "Client ID: $CLIENT_ID"
echo "Redirect URI: $REDIRECT_URI"
echo "Gitea Server: $GITEA_SERVER"
echo

# 测试 OAuth 授权 URL
AUTH_URL="${GITEA_SERVER}/login/oauth/authorize?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&state=test"
echo "测试 OAuth 授权 URL:"
echo "$AUTH_URL"
echo

# 测试 URL 访问
echo "测试 OAuth 端点响应:"
curl -v "$AUTH_URL" 2>&1 | grep -E "(HTTP|Location|Set-Cookie)" 