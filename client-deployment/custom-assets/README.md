# 自定义资源目录

此目录用于存放客户定制化的资源文件。

## Logo文件要求

### 支持的格式
- PNG格式 (推荐)
- JPG/JPEG格式
- SVG格式

### 文件命名
请将logo文件命名为以下格式之一：
- `logo.png`
- `logo.jpg`
- `logo.jpeg`
- `logo.svg`

或任何包含 `logo` 关键字的文件名，如：
- `company-logo.png`
- `brand-logo.svg`

### 文件要求
- **推荐尺寸**: 32x32 像素或 64x64 像素
- **最大尺寸**: 不超过 256x256 像素
- **文件大小**: 建议不超过 500KB
- **背景**: 建议使用透明背景（PNG/SVG）

### 使用方法

1. 将logo文件放入此目录
2. 在 `custom-config.env` 中设置 `VITE_CUSTOM_LOGO=true`
3. 运行部署脚本: `./deploy-client.sh`
4. logo会自动应用到管理端界面

### 注意事项

- logo会显示在管理端的侧边栏和页面标题处
- 如果logo文件不存在或加载失败，会自动使用默认logo
- 更新logo后需要强制刷新浏览器缓存 (Ctrl+F5)

### 测试logo效果

部署完成后，访问管理端界面查看logo效果：
```
http://YOUR_SERVER_IP:8088
```

### 故障排除

如果logo没有生效：
1. 检查文件路径和文件名是否正确
2. 确认 `VITE_CUSTOM_LOGO=true` 已设置
3. 检查文件格式和大小是否符合要求
4. 清理浏览器缓存并强制刷新页面
5. 查看浏览器控制台是否有错误信息