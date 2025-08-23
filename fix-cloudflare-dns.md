# 🔧 Cloudflare DNS 配置修复指南

## 🚨 问题诊断

当前问题：**Cloudflare 522错误 - 连接超时**

**根本原因**：
- 域名`omniverseai.net`设置了A记录指向`104.234.227.29`(你的动态IP)
- 但通过Cloudflare Tunnel访问需要CNAME记录
- 导致流量直接访问你的IP而不是通过tunnel

## ✅ 解决方案

### 方案1: 使用Cloudflare Tunnel (推荐)

#### 步骤1: 删除现有A记录
登录Cloudflare Dashboard → DNS Records → 删除：
```
Type: A
Name: omniverseai.net  
Value: 104.234.227.29
```

#### 步骤2: 创建CNAME记录
```bash
# 自动创建正确的DNS记录
cloudflared tunnel route dns mytunnel omniverseai.net
cloudflared tunnel route dns mytunnel www.omniverseai.net
cloudflared tunnel route dns mytunnel jenkins.omniverseai.net  
cloudflared tunnel route dns mytunnel registry.omniverseai.net
```

#### 步骤3: 验证配置
```bash
# 检查tunnel状态
cloudflared tunnel info mytunnel

# 测试访问
curl -I https://omniverseai.net
curl -I https://www.omniverseai.net
curl -I https://jenkins.omniverseai.net
curl -I https://registry.omniverseai.net
```

### 方案2: 保持A记录 + 端口转发

如果你想保持A记录，需要：

#### 步骤1: 开放端口
```bash
# 在路由器中开放端口（需要管理员权限）
80 → localhost:3001    # HTTP
443 → localhost:3443   # HTTPS
8081 → localhost:8081  # Jenkins
5001 → localhost:5001  # Registry
```

#### 步骤2: 配置HTTPS证书
```bash
# 使用Let's Encrypt获取证书
sudo certbot --standalone -d omniverseai.net -d www.omniverseai.net
```

## 🌐 推荐的最终DNS配置

使用Cloudflare Tunnel后，DNS记录应该是：

```
Type: CNAME    Name: omniverseai.net      Value: mytunnel.cfargotunnel.com
Type: CNAME    Name: www                  Value: mytunnel.cfargotunnel.com  
Type: CNAME    Name: jenkins              Value: mytunnel.cfargotunnel.com
Type: CNAME    Name: registry             Value: mytunnel.cfargotunnel.com
```

## 🔄 当前tunnel配置验证

当前`/Users/brunogao/.cloudflared/config.yml`配置：

```yaml
tunnel: 52e8fbf5-d2b3-4bc2-82c6-8a5e44104bd5
credentials-file: /Users/brunogao/.cloudflared/52e8fbf5-d2b3-4bc2-82c6-8a5e44104bd5.json

ingress:
  # www子域名
  - hostname: www.omniverseai.net
    service: http://localhost:3001
  # 根域名  
  - hostname: omniverseai.net
    service: http://localhost:3001
  # Jenkins CI/CD服务
  - hostname: jenkins.omniverseai.net
    service: http://localhost:8081
  # Registry镜像仓库
  - hostname: registry.omniverseai.net
    service: http://localhost:5001
  # 默认服务
  - service: http_status:404
```

## 🚀 执行修复

### 立即执行（推荐方案1）：

1. **登录Cloudflare Dashboard**
2. **删除A记录** `omniverseai.net → 104.234.227.29`
3. **运行DNS路由命令**：
   ```bash
   cloudflared tunnel route dns mytunnel omniverseai.net
   cloudflared tunnel route dns mytunnel www.omniverseai.net
   cloudflared tunnel route dns mytunnel jenkins.omniverseai.net
   cloudflared tunnel route dns mytunnel registry.omniverseai.net
   ```
4. **等待DNS传播** (2-10分钟)
5. **测试访问**

### 验证成功标志：
- ✅ https://omniverseai.net 正常访问
- ✅ https://www.omniverseai.net 正常访问  
- ✅ https://jenkins.omniverseai.net 显示Jenkins登录页
- ✅ https://registry.omniverseai.net 显示Registry API

## 💡 额外优化

设置自动重启tunnel：
```bash
# 添加到crontab
@reboot /usr/local/bin/cloudflared tunnel run mytunnel
```

## 🎯 预期结果

修复后你将拥有：
- **主站**: https://omniverseai.net
- **Jenkins**: https://jenkins.omniverseai.net  
- **Registry**: https://registry.omniverseai.net
- **自动HTTPS**: Cloudflare提供免费SSL证书
- **防护**: Cloudflare提供DDoS防护和CDN加速 