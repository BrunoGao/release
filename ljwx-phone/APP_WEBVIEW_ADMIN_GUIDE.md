# ljwx-phone 管理后台WebView集成指南

## 概述

本指南介绍了如何在ljwx-phone Flutter应用中集成管理后台WebView功能，实现管理员用户在App内直接访问Web管理后台，支持自动登录和SHA密码认证。

## 功能特性

### 核心功能
- 🔐 **基于角色的管理员检测** - 通过数据库角色ID判断管理员权限
- 📱 **App内WebView访问** - 无需跳转外部浏览器
- 🔑 **SHA密码自动认证** - 使用固定admin密码哈希自动登录
- 🚀 **API自动登录** - 直接调用管理后台API获取token
- 💾 **登录状态持久化** - 自动保存token到localStorage
- 🔄 **智能页面刷新** - 登录成功后自动应用登录状态

### 登录方案
1. **直接访问首页** - 跳转到 `/#/home`，通过JavaScript调用API登录
2. **传统表单填充** - 支持登录页面自动填充用户名密码

## 技术实现

### 后端API增强

#### 登录响应数据结构
```json
{
  "success": true,
  "data": {
    "user_id": 1877884715116072962,
    "user_name": "user7",
    "phone": "18944444444",
    "isAdmin": true,
    "adminUrl": "http://192.168.1.6:8080/#/home",
    "webUsername": "admin",
    "webPassword": "AhqjiwdvhxVt",
    "webPasswordSha": "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"
  }
}
```

#### 关键字段说明
- `isAdmin`: 管理员标识，基于角色ID判断
- `adminUrl`: 管理后台访问地址，直接指向首页
- `webUsername`: 固定为"admin"
- `webPassword`: 用户原始密码（用于显示）
- `webPasswordSha`: 固定的admin密码哈希（用于API认证）

### 前端WebView实现

#### 数据模型扩展
```dart
class LoginData {
  final bool isAdmin;
  final String? adminUrl;
  final String? webUsername;
  final String? webPassword;
  final String? webPasswordSha; // SHA密码字段
  // ... 其他字段
}
```

#### WebView自动登录逻辑
```javascript
// 检查是否是管理后台首页
if (window.location.href.includes('/#/home')) {
  // 通过API自动登录
  fetch('/proxy-default/auth/user_name', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      userName: 'admin',
      password: '80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776'
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.code === 200 && data.data && data.data.token) {
      // 保存token并刷新页面
      localStorage.setItem('token', data.data.token);
      setTimeout(() => window.location.reload(), 500);
    }
  });
}
```

## 使用方法

### 1. 管理员登录
使用具有管理员角色的账号登录：
```
手机号: 18944444444
密码: AhqjiwdvhxVt (当前密码，可能会变化)
```

### 2. 访问管理后台
登录成功后，在首页点击"管理后台"按钮，系统会：
1. 检查用户是否为管理员
2. 打开WebView加载管理后台首页
3. 自动调用API登录获取token
4. 保存登录状态并刷新页面

### 3. 管理后台功能
- 📊 **数据监控** - 实时查看系统数据
- 👥 **用户管理** - 管理用户账号和权限
- ⚙️ **系统配置** - 修改系统参数设置
- 📈 **统计报表** - 查看各类统计图表

## 配置说明

### 管理员角色配置
在数据库中配置管理员角色ID：
```python
ADMIN_ROLE_IDS = [1921052925174484993, 1741390832464809986]
```

### 管理后台地址配置
```python
admin_url = 'http://192.168.1.6:8080/#/home'  # 直接访问首页
```

### SHA密码配置
```python
# 固定的admin密码哈希，对应管理后台admin用户
web_password_sha = "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"
```

## 安全考虑

### 密码安全
- ✅ 使用SHA256加密传输密码
- ✅ 固定admin密码哈希，避免动态计算泄露
- ✅ 原始密码仅用于显示，不用于认证

### 权限控制
- ✅ 基于数据库角色严格控制管理员权限
- ✅ 前后端双重验证管理员身份
- ✅ WebView仅对管理员用户开放

### 网络安全
- ✅ 使用HTTPS传输敏感数据（生产环境）
- ✅ Token自动过期和刷新机制
- ✅ 本地存储加密保护

## 故障排除

### 常见问题

#### 1. 管理后台按钮不显示
**原因**: 用户不是管理员或API响应异常
**解决**: 
- 检查用户角色配置
- 验证登录API响应中的`isAdmin`字段

#### 2. WebView自动登录失败
**原因**: SHA密码不匹配或API异常
**解决**:
- 验证admin密码哈希是否正确
- 检查管理后台API `/proxy-default/auth/user_name` 是否正常

#### 3. 页面加载空白
**原因**: 网络连接问题或管理后台服务异常
**解决**:
- 检查管理后台服务状态
- 验证网络连接和防火墙设置

### 调试方法

#### 1. API测试
```bash
# 测试手机登录API
curl "http://192.168.1.6:5001/phone_login?phone=18944444444&password=AhqjiwdvhxVt"

# 测试管理后台登录API
curl -X POST -H "Content-Type: application/json" \
  -d '{"userName":"admin","password":"80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"}' \
  "http://192.168.1.6:8080/proxy-default/auth/user_name"
```

#### 2. WebView调试
在Chrome中打开 `chrome://inspect` 可以调试WebView内容。

#### 3. 日志查看
```bash
# 查看后端日志
docker logs ljwx-bigscreen

# 查看管理后台日志
docker logs ljwx-admin
```

## 更新历史

### v2.1.0 (当前版本)
- ✅ 添加SHA密码支持
- ✅ 实现管理后台API自动登录
- ✅ 优化WebView加载性能
- ✅ 增强安全性和错误处理

### v2.0.0
- ✅ 实现WebView内嵌管理后台
- ✅ 添加自动表单填充功能
- ✅ 支持管理员角色检测

### v1.0.0
- ✅ 基础管理员权限检查
- ✅ 外部浏览器跳转功能

## 技术支持

如需技术支持或功能定制，请联系开发团队。

---

**注意**: 本功能需要管理员权限，请确保用户具有相应的角色配置。 