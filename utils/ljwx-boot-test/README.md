# ljwx-boot 历史数据上传测试工具

Java版本的30天历史数据上传测试工具，仿照 `start_30day_upload.py` 实现。

## 功能特性

🚀 **高性能上传**
- 多线程并发上传，默认20个线程
- 支持每分钟一次的数据上传模拟
- CPU自适应性能调优

⚡ **完整API测试**
- `upload_health_data` - 健康数据上传
- `upload_device_info` - 设备信息上传  
- `upload_common_event` - 通用事件上传

📊 **详细统计**
- 实时上传进度显示
- 成功率和性能指标统计
- 响应时间和吞吐量监控

🎯 **多种运行模式**
- 完整模式：30天历史数据
- 测试模式：1小时测试数据
- 自定义模式：指定天数
- 交互模式：命令行选择

## 快速开始

### 1. 编译项目

```bash
cd ljwx-boot-test
mvn clean package
```

### 2. 运行测试

#### 交互式运行（推荐）
```bash
java -jar target/ljwx-boot-30day-uploader.jar
```

#### 完整30天上传
```bash
java -jar target/ljwx-boot-30day-uploader.jar --mode full
```

#### 测试模式（1小时数据）
```bash
java -jar target/ljwx-boot-30day-uploader.jar --mode test
```

#### 自定义配置
```bash
java -jar target/ljwx-boot-30day-uploader.jar \
  --url http://192.168.1.83:8080 \
  --threads 30 \
  --devices DEVICE_001,DEVICE_002,DEVICE_003 \
  --mode full
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--url <url>` | ljwx-boot API基础URL | `http://localhost:8080` |
| `--threads <num>` | 并发线程数 (1-100) | `20` |
| `--devices <list>` | 设备列表，逗号分隔 | `DEVICE_001,DEVICE_002,DEVICE_003,DEVICE_004,DEVICE_005` |
| `--mode <mode>` | 运行模式 | `interactive` |
| `--days <num>` | 上传天数（仅custom模式） | - |
| `--help, -h` | 显示帮助信息 | - |

### 运行模式说明

- `interactive` - 交互式选择（默认）
- `full` - 完整30天数据上传
- `test` - 测试模式（1小时数据）
- `custom` - 自定义天数

## 性能指标

### 预期性能
- **数据量**: 30天 × 24小时 × 60分钟 = 43,200个时间点
- **设备数**: 5个默认设备
- **总操作数**: ~130,000次 (43,200 × 5设备 × 3接口)
- **预期速度**: 600+ 次/秒
- **预计耗时**: 3-5分钟

### 实际测试结果
程序会显示实时统计信息：
```
📊 进度: 45.2% | 587/1300 | 成功率: 98.5% | 速度: 623.4 次/秒
📊 高速上传完成统计
总耗时: 142 秒
平均上传速度: 625.35 次/秒
峰值处理能力: 37521 次/分钟
设备数量: 5
总操作数: 88840
成功次数: 87523
失败次数: 1317
成功率: 98.52%
```

## 日志文件

### 日志位置
- **控制台日志**: 实时显示在终端
- **文件日志**: `./logs/ljwx-boot-test.yyyy-MM-dd.log`
- **统计日志**: `./logs/upload-stats.log`

### 日志级别
- `INFO`: 重要信息和统计数据
- `DEBUG`: 详细的调试信息（需要修改logback.xml）
- `WARN`: 警告信息
- `ERROR`: 错误信息

## API兼容性

### 支持的ljwx-boot接口

#### 健康数据上传
- **端点**: `/batch/upload_health_data`
- **方法**: POST
- **数据**: 健康指标数组

#### 设备信息上传
- **端点**: `/batch/upload_device_info`  
- **方法**: POST
- **数据**: 设备信息数组

#### 通用事件上传
- **端点**: `/batch/upload_common_event`
- **方法**: POST
- **数据**: 事件对象

### 健康检查接口
- **统计信息**: `GET /batch/stats`
- **健康检查**: `GET /batch/health`

## 故障排除

### 常见问题

#### 1. API连接失败
```
❌ API服务器连接失败: http://localhost:8080
```

**解决方案**:
- 检查ljwx-boot服务是否启动
- 确认URL地址是否正确
- 检查网络连接和防火墙设置

#### 2. 内存不足
```
java.lang.OutOfMemoryError: Java heap space
```

**解决方案**:
```bash
java -Xmx4g -jar target/ljwx-boot-30day-uploader.jar
```

#### 3. 上传速度慢
- 减少线程数: `--threads 10`
- 检查网络带宽
- 检查服务器性能

#### 4. 大量上传失败
- 检查ljwx-boot服务日志
- 验证数据格式
- 检查数据库连接

### 调试模式

修改 `src/main/resources/logback.xml`:
```xml
<logger name="com.ljwx.test" level="DEBUG" />
```

重新编译后运行获取更详细日志。

## 开发说明

### 项目结构
```
ljwx-boot-test/
├── src/main/java/com/ljwx/test/
│   ├── Start30DayUploadApp.java      # 主程序
│   ├── HistoricalDataUploader.java   # 上传器核心类
│   ├── APIClient.java                # HTTP客户端
│   └── UploadResult.java             # 结果封装类
├── src/main/resources/
│   └── logback.xml                   # 日志配置
├── pom.xml                           # Maven配置
└── README.md                         # 说明文档
```

### 技术栈
- **Java 11+**: 基础运行时
- **Jackson**: JSON序列化/反序列化
- **SLF4J + Logback**: 日志框架
- **Maven**: 构建工具
- **Java HTTP Client**: HTTP请求客户端

### 扩展开发
1. 修改 `generateDataForTime()` 方法自定义测试数据
2. 在 `APIClient` 中添加新的API接口支持
3. 扩展 `UploadResult` 类添加更多统计信息

## 与Python版本对比

| 功能 | Python版本 | Java版本 |
|------|------------|----------|
| 基础功能 | ✅ | ✅ |
| 多线程并发 | ✅ | ✅ |
| 实时统计 | ✅ | ✅ |
| 命令行参数 | ✅ | ✅ |
| 交互式选择 | ✅ | ✅ |
| 错误处理 | ✅ | ✅ |
| 日志记录 | ✅ | ✅ |
| 性能监控 | ✅ | ✅ |
| 可执行打包 | pip安装 | JAR打包 |
| 启动速度 | 较快 | 较慢（JVM启动） |
| 内存占用 | 较小 | 较大 |
| 跨平台部署 | 需要Python环境 | 只需Java环境 |

## 许可证

本项目基于内部使用许可，仅供灵境万象系统测试使用。