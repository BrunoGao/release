# 定制Logo配置指南

## 概述

系统支持客户定制Logo功能，可以将客户的Logo文件集成到管理界面中。

## 配置步骤

### 1. 准备Logo文件

将客户的Logo文件命名为以下任意一种：
- `custom-logo.svg` (推荐)
- `customer-logo.svg`
- `logo.svg`
- `company-logo.svg`

**注意：**
- 建议使用SVG格式，支持矢量缩放
- 文件大小建议控制在50KB以内
- 建议尺寸比例为横向布局，如200x60像素

### 2. 放置Logo文件

将Logo文件放置在 `client-deployment` 目录下。

### 3. 启用Logo配置

在 `custom-config.env` 文件中设置：
```bash
VITE_CUSTOM_LOGO=true
```

### 4. 部署系统

执行部署命令：
```bash
./deploy-client.sh
```

系统会自动：
1. 检测Logo文件
2. 将文件复制到容器内正确位置
3. 配置前端应用使用定制Logo

## 故障排除

### 使用诊断工具

如果Logo未正确显示，可使用诊断脚本：
```bash
./diagnose-logo-issue.sh
```

该脚本会：
- ✅ 检查Logo文件是否存在
- ✅ 验证配置是否正确
- ✅ 确认文件挂载状态
- ✅ 测试HTTP访问
- ✅ 自动修复常见问题

### 手动修复

如果需要手动修复，需要替换前端应用中的实际logo文件：
```bash
# 1. 查找前端应用中的logo文件
docker exec ljwx-admin find /usr/share/nginx/html/assets -name "logo*.svg"

# 2. 备份原始文件 (以第一个文件为例)
docker exec ljwx-admin cp /usr/share/nginx/html/assets/logo-DgyNd7sd.svg /usr/share/nginx/html/assets/logo-DgyNd7sd.svg.backup

# 3. 用定制logo替换
docker exec ljwx-admin cp /tmp/custom-logo.svg /usr/share/nginx/html/assets/logo-DgyNd7sd.svg

# 4. 对所有logo文件重复上述操作
```

### 快速修复
使用自动化脚本进行修复：
```bash
./quick-fix-logo.sh          # 快速修复
./replace-logo-correctly.sh  # 完整替换过程
```

### 验证访问

测试Logo是否可访问：
```bash
curl -I http://localhost:8080/custom-logo.svg
```

应返回HTTP 200状态码。

## 支持的文件格式

- **SVG** (推荐) - 矢量格式，任意缩放不失真
- **PNG** - 建议透明背景
- **JPG** - 不推荐，因为有背景色

## 浏览器缓存

如果更新Logo后未生效，请：
1. 清除浏览器缓存
2. 硬刷新页面 (Ctrl+F5)
3. 运行缓存清理脚本：`./clear-browser-cache.sh`

## 技术实现

Logo集成流程：
1. 本地文件 → Docker挂载到 `/tmp/custom-logo.svg`
2. 部署脚本 → 替换前端应用中的编译后logo文件
   - 查找 `/usr/share/nginx/html/assets/logo*.svg`
   - 备份原始文件 (添加.backup后缀)
   - 用定制logo替换所有找到的logo文件
3. 前端应用 → 自动加载替换后的logo文件
4. 配置变量 → `VITE_CUSTOM_LOGO=true` 启用替换功能

**重要说明**：前端应用使用的是编译时打包的logo文件，文件名包含哈希值（如`logo-DgyNd7sd.svg`），因此需要直接替换这些文件内容，而不是创建新文件。

## 联系支持

如有问题，请联系技术支持，并提供：
- 诊断脚本输出
- Logo文件信息
- 浏览器开发者工具错误信息 