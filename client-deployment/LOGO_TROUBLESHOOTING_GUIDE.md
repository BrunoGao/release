# Logo无法加载问题排查指南

## 🔍 问题现象

- 管理后台页面中Logo显示异常
- 浏览器开发者工具显示：`<img src="false" alt="logo">`
- 启动日志显示Logo已更新但实际未生效

## 🕵️ 问题根源分析

### 1. 前端逻辑分析
```javascript
// 前端JavaScript伪代码
const logoSrc = useCustomLogo ? customLogoPath : defaultLogo;
// 当useCustomLogo=true但customLogoPath指向不存在文件时
// 可能回退到布尔值false，导致src="false"
```

### 2. 问题链路追踪

```mermaid
graph TD
    A[Docker启动] --> B[环境变量VITE_CUSTOM_LOGO=true]
    B --> C[config.js: useCustomLogo=true]
    C --> D[customLogoPath=/assets/svg-icon/logo.svg]
    D --> E[文件不存在] 
    E --> F[前端回退逻辑错误]
    F --> G[img src=false]
    
    H[Logo文件实际路径] --> I[/assets/logo-DgyNd7sd.svg]
    I --> J[路径不匹配]
    J --> K[加载失败]
```

### 3. 关键发现

| 配置项 | 期望值 | 实际值 | 状态 |
|--------|--------|--------|------|
| VITE_CUSTOM_LOGO | true | true | ✅ |
| useCustomLogo | true | true | ✅ |
| customLogoPath | /assets/logo-DgyNd7sd.svg | /assets/svg-icon/logo.svg | ❌ |
| Logo文件位置 | /assets/logo-DgyNd7sd.svg | /assets/logo-DgyNd7sd.svg | ✅ |

## 🛠️ 解决方案

### 修复1：路径配置同步
```js
// custom-admin-config.js
customLogoPath: '/assets/logo-DgyNd7sd.svg'  // 匹配实际文件路径
```

### 修复2：Docker挂载策略
```yaml
# docker-compose-client.yml
volumes:
  - ./custom-logo.svg:/tmp/custom-logo.svg:ro  # 启动脚本期望位置
  - ./custom-admin-config.js:/tmp/custom-admin-config.js:ro  # 避免Resource busy
```

### 修复3：环境变量强制设置
```yaml
environment:
  VITE_CUSTOM_LOGO: "true"  # 硬编码避免环境变量传递问题
```

## 🔧 排查工具和方法

### 1. 检查Web资源可访问性
```bash
curl -I http://localhost:8080/config.js
curl -I http://localhost:8080/assets/logo-DgyNd7sd.svg
```

### 2. 验证配置文件内容
```bash
curl -s http://localhost:8080/config.js | grep customLogoPath
```

### 3. 检查容器内文件
```bash
docker exec ljwx-admin ls -la /usr/share/nginx/html/assets/ | grep logo
```

### 4. 环境变量验证
```bash
docker exec ljwx-admin env | grep VITE_CUSTOM_LOGO
```

### 5. 浏览器开发者工具
- Network标签页：检查资源加载状态
- Console标签页：查看JavaScript错误
- Elements标签页：检查img标签src属性

## ⚠️ 常见陷阱

1. **路径大小写敏感**：Linux容器对文件路径大小写敏感
2. **缓存问题**：浏览器可能缓存了错误的配置
3. **时序问题**：config.js可能在主JS之后加载
4. **文件权限**：只读挂载可能导致启动脚本无法修改配置

## 📈 验证清单

- [ ] 环境变量VITE_CUSTOM_LOGO=true
- [ ] config.js中useCustomLogo=true  
- [ ] customLogoPath指向正确的文件路径
- [ ] Logo文件可通过Web访问（200状态码）
- [ ] 浏览器开发者工具中img标签src属性正确
- [ ] 清除浏览器缓存后重新测试

## 🎯 最佳实践

1. **统一路径管理**：Logo路径在配置文件中统一管理
2. **健康检查**：启动脚本应验证Logo文件是否存在
3. **回退机制**：前端应有合理的Logo加载失败回退策略
4. **监控告警**：关键资源加载失败应有日志记录 