# 健康数据分片传输与合并方案

## 功能描述

为解决手表和手机之间蓝牙传输大型健康数据（如睡眠数据、运动数据等）引起的问题，我们实现了以下功能：

1. **健康数据分片器**：将大型健康数据拆分成多个小型数据包进行传输
2. **健康数据合并器**：在手机端重新组装收到的数据片段为完整健康数据

此方案可有效解决以下问题：
- 避免因蓝牙传输数据包过大导致的传输失败
- 解决嵌套JSON字段解析错误问题
- 提高数据传输的稳定性和成功率

## 主要组件

### 1. 健康数据分片器 (HealthDataSplitter)

位置：`lib/utils/health_data_splitter.dart`

功能：
- 将完整健康数据拆分成多个数据片段
- 为同一组数据片段分配唯一的组ID
- 根据数据类型创建不同的数据包（元数据包、睡眠数据包等）

### 2. 健康数据合并器 (HealthDataMerger)

位置：`lib/utils/health_data_merger.dart`

功能：
- 接收并缓存数据片段
- 根据组ID将同一组数据片段组合在一起
- 当所有片段接收完成后，合并为完整的健康数据
- 将合并完成的数据发送到数据流供应用程序使用

### 3. JSON工具类 (JsonUtil)

位置：`lib/utils/json_util.dart`

功能：
- 提供安全获取JSON值的工具方法
- 避免因数据类型不匹配或缺失导致的异常

## 数据流程

1. **手表端**：
   - 收集健康数据
   - 使用HealthDataSplitter将数据拆分为多个片段
   - 通过蓝牙逐个发送数据片段

2. **手机端**：
   - 蓝牙服务收到数据片段
   - 识别健康数据片段并转发给HealthDataMerger
   - HealthDataMerger缓存并组装数据片段
   - 完整数据组装后，通知应用程序

## 数据包格式

### 元数据包

```json
{
  "type": "health_meta",
  "data": {
    "health_group_id": "health_1234567890",
    "id": "device_id",
    "upload_method": "bluetooth",
    "heart_rate": 75,
    "blood_oxygen": 98,
    ...
  }
}
```

### 嵌套数据包（如睡眠数据）

```json
{
  "type": "health_sleep",
  "data": {
    "health_group_id": "health_1234567890",
    "content": { /* 睡眠数据内容 */ }
  }
}
```

## 使用方法

### 在蓝牙服务中使用

已在蓝牙服务 (BluetoothService) 中集成健康数据合并器，无需额外配置。系统会自动识别健康数据分片并进行处理。

### 手动分片和合并

如需手动分片数据：

```dart
// 分片健康数据
List<Map<String, dynamic>> dataPackets = HealthDataSplitter.splitHealthData(healthData);

// 发送数据片段
for (var packet in dataPackets) {
  sendDataViaBluetoothOrOtherChannel(packet);
}
```

如需手动合并数据：

```dart
// 监听合并完成的健康数据
HealthDataMerger.i.healthDataStream.listen((mergedData) {
  // 处理完整的健康数据
  processHealthData(mergedData);
});

// 接收数据片段
void onDataReceived(String jsonData) {
  HealthDataMerger.i.receiveData(jsonData);
}
``` 