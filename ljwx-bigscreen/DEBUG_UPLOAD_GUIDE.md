# 上传接口调试信息指南

## 概述

为了帮助排查客户端上传数据问题，我们为 `upload_device_info` 和 `upload_health_data` 接口添加了详细的调试信息输出。

## 调试信息说明

### 1. 设备信息上传调试 (`upload_device_info`)

**调试信息包含：**
- 📱 接口请求接收
- 📱 请求头信息
- 📱 请求体大小和内容
- 📱 设备SN提取
- 📱 批量处理器状态
- 📱 数据字段解析
- 💾 数据库操作详情
- ✅ 成功标识
- ❌ 错误信息和异常堆栈

**调试信息示例：**
```
📱 /upload_device_info 接口收到请求
📱 请求头: {'Content-Type': 'application/json', 'User-Agent': 'PostmanRuntime/7.28.4'}
📱 请求体大小: 285 字符
📱 原始JSON数据: {
  "SerialNumber": "TD001",
  "batteryLevel": "85",
  "chargingStatus": "NOT_CHARGING"
}
📱 提取的设备SN: TD001
📱 调用upload_device_info处理函数
📱 设备信息上传开始 - 原始数据: {...}
📱 批量处理器获取成功，队列状态: 未知
📱 设备信息提交队列成功: TD001
```

### 2. 健康数据上传调试 (`upload_health_data`)

**调试信息包含：**
- 🏥 接口请求接收
- 🏥 请求头和请求体信息
- 🔍 data字段解析
- 🔧 优化器处理过程
- 🔍 用户组织信息查询
- 🔍 字段映射和数据构建
- ✅ 成功标识
- ❌ 错误信息和异常堆栈

**调试信息示例：**
```
🏥 /upload_health_data 接口收到请求
🏥 原始JSON数据: {
  "data": {
    "deviceSn": "TD001",
    "heart_rate": 75,
    "blood_oxygen": 98
  }
}
🔍 data字段类型: <class 'dict'>, 内容: {...}
🔍 从对象提取device_sn: TD001
🏥 调用optimized_upload_health_data处理函数
🔧 优化器添加数据开始: device_sn=TD001
🔍 查找设备对应用户信息: TD001
✅ 用户组织信息: user_id=1, org_id=2, customer_id=100
```

## 常见问题排查

### 1. 上传数据为0的问题

**可能原因：**
- 设备SN未找到对应用户
- 数据字段映射错误
- 重复数据被跳过
- 数据库连接问题

**调试信息关键点：**
```
❌ 未找到设备对应用户: TD001
⚠️ 数据重复，已跳过处理
🔍 字段映射: heart_rate -> heart_rate = None
```

### 2. 500错误问题

**可能原因：**
- 数据库连接失败
- 字段类型错误
- 必填字段缺失
- 异常未捕获

**调试信息关键点：**
```
❌ 数据库操作失败: (1054, "Unknown column 'xxx' in 'field list'")
❌ 异常详情: MySQLError - Connection refused
❌ 完整异常堆栈: Traceback (most recent call last)...
```

## 测试脚本使用

我们提供了测试脚本 `test_debug_upload.py` 来验证调试信息：

```bash
# 运行测试脚本
cd ljwx-bigscreen
python test_debug_upload.py
```

**修改配置：**
```python
# 修改BASE_URL为实际服务器地址
BASE_URL = "http://your-server:port"
```

## 日志文件位置

调试信息会输出到以下位置：
- 控制台输出（print语句）
- 应用日志文件
- 特定模块日志（device_logger, health_logger）

## 生产环境注意事项

⚠️ **重要提醒：**
1. 调试信息包含敏感数据，生产环境需要控制输出级别
2. 大量调试信息可能影响性能
3. 建议通过配置开关控制调试信息输出
4. 定期清理调试日志文件

## 调试信息符号说明

| 符号 | 含义 |
|------|------|
| 📱 | 设备信息相关 |
| 🏥 | 健康数据相关 |
| 🔍 | 数据解析和查询 |
| 🔧 | 优化器处理 |
| 💾 | 数据库操作 |
| ✅ | 成功操作 |
| ❌ | 错误或失败 |
| ⚠️ | 警告信息 |

## 常用排查步骤

1. **检查请求格式**
   - 查看原始JSON数据格式
   - 确认Content-Type头
   - 验证必填字段

2. **检查设备注册**
   - 确认设备SN在数据库中存在
   - 检查用户组织关联关系
   - 验证customer_id获取

3. **检查数据库连接**
   - 查看数据库连接状态
   - 检查SQL执行结果
   - 验证表结构和字段

4. **检查数据处理**
   - 查看字段映射结果
   - 检查数据类型转换
   - 验证业务逻辑执行

通过这些详细的调试信息，可以快速定位和解决客户端上传数据的问题。 