# LJWX 智能手表系统 v1.3.4

[![HarmonyOS](https://img.shields.io/badge/HarmonyOS-4.0-blue.svg)](https://developer.harmonyos.com/)
[![版本](https://img.shields.io/badge/version-1.3.4-green.svg)](https://github.com/your-org/ljwx-watch)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 项目概述

本项目是基于鸿蒙系统(HarmonyOS)开发的企业级智能手表系统，专为工业环境下的健康监测和设备管理而设计。系统集成了全面的健康数据采集、实时蓝牙通信、HTTP数据上传和智能缓存机制。

### 🎯 主要特性

- **多模式数据传输**：支持蓝牙和HTTP双通道数据上传
- **智能健康监测**：实时采集心率、血氧、体温等多项生理指标
- **高效缓存机制**：三种数据类型独立缓存，支持断点续传
- **二进制传输协议**：自研TLV协议，数据压缩率达80%+
- **电池优化**：统一定时器调度，续航提升至15-18小时
- **企业级稳定性**：完善的错误处理和自恢复机制

## 🆕 最新功能：自定义日志系统 (v1.3.4)

### 功能概述
为了解决HarmonyOS HiLog日志打印不完整且不支持中文的问题，系统新增了自定义日志工具，能够完整打印断点续传时的健康信息、设备信息和通用事件数据。

### 主要改进
- **完整数据打印**：解决HiLog数据截断问题，通过分段输出保证完整性
- **中文字符支持**：原生支持中文字符输出，无需编码转换
- **专业化日志方法**：针对健康数据、设备信息、通用事件提供专用日志方法
- **断点续传调试**：重点加强断点续传场景下的数据追踪能力

### 技术实现

#### 1. 自定义日志工具类
```java
/**
 * 分段打印长数据，避免HiLog截断
 */
public static void logLongData(String tag, String title, String data) {
    // 每段500字符分段输出
    final int chunkSize = 500;
    int chunkCount = (totalLength + chunkSize - 1) / chunkSize;
    
    for (int i = 0; i < chunkCount; i++) {
        String chunk = data.substring(start, end);
        info(tag, String.format("%s 第%d/%d段: %s", title, i + 1, chunkCount, chunk));
    }
}
```

#### 2. 专业化日志方法
```java
// 健康数据专用日志
CustomLogger.logHealthInfo("断点续传", healthData);

// 设备信息专用日志
CustomLogger.logDeviceInfo("设备状态检查", deviceData);

// 通用事件专用日志
CustomLogger.logCommonEvent("SOS事件", deviceInfo, healthInfo);
```

#### 3. 断点续传增强调试
```java
// 在HttpService中添加完整数据日志
CustomLogger.info("HttpService::uploadAllCachedData", "开始打印完整上传数据");
CustomLogger.logLongData("HttpService::uploadAllCachedData", "准备上传的完整缓存数据", uploadData);
```

### 日志系统优势

#### 1. 解决HiLog限制
- **数据截断问题**：HiLog默认对长数据进行截断，导致重要信息丢失
- **中文字符问题**：原生HiLog对中文字符显示支持不够完善
- **调试效率**：完整的数据输出大幅提升调试效率

#### 2. 空间占用统计
基于实际日志数据统计的缓存空间占用：
- **健康数据**：480字节/条，100条约47KB
- **设备信息**：425字节/条，100条约41KB  
- **通用事件**：1,397字节/条，100条约136KB
- **总计**：三种数据类型缓存满载约224KB

#### 3. 使用场景
```java
// 断点续传场景下的完整数据追踪
public void uploadAllCachedData() {
    List<String> healthDataList = healthDataCache.getAllCachedData(DataType.HEALTH_DATA);
    
    // 使用自定义日志完整打印缓存内容
    for (String healthData : healthDataList) {
        CustomLogger.logHealthInfo("缓存数据上传", healthData);
    }
    
    // 打印上传的完整JSON数据
    String uploadData = finalJson.toString();
    CustomLogger.logLongData("HttpService", "上传数据", uploadData);
}
```

### 调试建议
- 使用 `CustomLogger.logHealthInfo()` 查看健康数据详情
- 使用 `CustomLogger.logDeviceInfo()` 检查设备状态
- 使用 `CustomLogger.logLongData()` 输出完整JSON数据
- 关注断点续传场景下的数据完整性验证

## 🔋 耗电性能优化（v1.3.3）

为了解决手表在仅开启HTTP服务模式下只能使用11小时的耗电问题，我们对系统进行了深度优化：

### 优化1：健康数据采集优化
**问题**：多个独立Timer导致过度资源消耗
**解决方案**：
- ✅ 将所有体征数据采集Timer合并为一个统一主定时器
- ✅ 采用心率5秒基础周期，用计数器控制不同采集频率
- ✅ 一个Timer替代之前的10+个独立Timer，大幅降低系统开销

**技术实现**：
```java
// 统一定时器调度 - 以心率为基数
masterTimer = new Timer();
masterTimer.schedule(new TimerTask() {
    @Override
    public void run() {
        tick++;
        // 各种体征数据按不同周期采集
        if (dataManager.isSupportStep() && tick % (dataManager.getStepsMeasurePeriod() / basePeriod) == 0) {
            getStepData(startTime, endTime);
        }
        // ... 其他体征数据类似处理
    }
}, 0, basePeriod * 1000);
```

### 优化2：HTTP服务优化 
**问题**：频繁的网络请求和多个HTTP定时器
**解决方案**：
- ✅ 合并所有HTTP定时器为一个统一定时器
- ✅ 健康数据改为本地缓存+10分钟批量上传策略
- ✅ 优化上传频率，减少不必要的网络活动

**技术实现**：
```java
// 统一定时器调度 - 60秒基础周期
masterHttpTimer = new Timer();
masterHttpTimer.schedule(new TimerTask() {
    @Override
    public void run() {
        httpTick++;
        // 健康数据每10分钟批量上传
        if (dataManager.getUploadHealthInterval() > 0 && httpTick % 10 == 0) {
            uploadHealthData(); // 批量上传缓存数据
        }
        // 其他任务按需执行...
    }
}, 0, baseHttpPeriod * 1000);
```

### 优化3：智能缓存机制
**问题**：实时上传导致频繁网络活动
**解决方案**：
- ✅ 数据采集后先本地缓存，延迟批量上传
- ✅ 支持断点续传，网络异常时数据不丢失
- ✅ 缓存分片存储，突破8192字符限制

### 性能提升成果
- **CPU使用率降低**：Timer数量从15+减少到2个 ✅
- **网络活动减少**：从实时上传改为10分钟批量上传 ✅
- **系统唤醒减少**：统一调度减少系统中断 ✅
- **续航大幅提升**：从11小时提升至15-18小时 ✅
- **数据传输优化**：二进制协议减少80%+数据量 ✅
- **缓存机制完善**：三类数据独立缓存，支持断点续传 ✅

## 🏗️ 系统架构

### 核心模块架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    LJWX智能手表系统                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   用户界面层    │     数据处理层   │       通信传输层        │
│ MainAbilitySlice│ HealthDataCache │    BluetoothService     │
│   配置管理      │   数据分片处理   │       HttpService       │
│   状态显示      │   智能缓存      │      二进制协议         │
├─────────────────┼─────────────────┼─────────────────────────┤
│   工具支撑层    │     健康服务层   │       设备管理层        │
│  CustomLogger   │ HealthDataService│      DeviceManager      │
│  完整日志输出   │   体征数据采集   │       设备状态管理       │
│  中文字符支持   │   智能告警      │       电池优化管理       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 主要功能模块

1. **主界面模块 (MainAbilitySlice)**
   - 配置管理
   - 数据展示
   - 服务调度

2. **蓝牙通信模块 (BluetoothService)**
   - 蓝牙连接管理
   - 数据透传
   - 命令处理

3. **HTTP服务模块 (HttpService)**
   - 网络状态管理
   - 数据上传
   - 断点续传

4. **健康数据模块 (HealthDataService)**
   - 健康数据采集
   - 实时监测
   - 告警管理

5. **智能缓存模块 (HealthDataCache)**
   - 三种数据类型独立缓存
   - 环形队列管理
   - 分片存储机制

6. **自定义日志模块 (CustomLogger)**
   - 解决HiLog数据截断问题
   - 支持中文字符完整输出
   - 专业化日志方法支持
   - 断点续传调试增强

## ⚙️ 配置管理

### 健康数据采集配置
```json
{
  "heart_rate": "5:1:1:100.0:80.0:5",  // 间隔:启用:实时:高阈值:低阈值:告警次数
  "blood_oxygen": "20:1:1:100.0:90.0:5",
  "temperature": "20:1:1:37.5:35.0:5",
  "stress": "1800:1:1:66.0:0.0:5"
}
```

### 接口配置
```json
{
  "健康数据上传接口": "http://example.com/upload_health_data;60;1;API_ID;AUTH_TOKEN",
  "设备信息上传接口": "http://example.com/upload_device_info;18000;1;API_ID;AUTH_TOKEN"
}
```

## 🔄 数据传输机制

### 三类数据独立缓存
- **健康数据缓存** (health_data)：心率、血氧、体温等生理指标
- **设备信息缓存** (device_info)：电量、版本、网络状态等设备状态
- **通用事件缓存** (common_event)：SOS告警、跌倒检测等紧急事件

### 二进制传输协议
```
协议格式：[版本1字节][类型1字节][格式1字节][长度2字节][TLV数据N字节]

数据类型：
- 0x01: 健康数据 (TLV编码)
- 0x02: 设备信息  
- 0x03: 通用事件
- 0xFE: 心跳包
```

### 分片存储机制
- 每片最大7000字符，避免8192字符限制
- 支持最多10个分片，满足大容量缓存需求
- 智能加载机制，自动检测并拼接所有有效分片

## 🚀 快速开始

### 环境要求
- HarmonyOS 4.0+
- DevEco Studio 4.0+
- Java 8+

### 安装步骤
1. 克隆项目到本地
2. 使用DevEco Studio打开项目
3. 配置设备证书和签名
4. 编译并安装到目标设备

### 基本配置
1. 配置更新后需要重启相应服务
2. 蓝牙连接需要先配对
3. 网络状态变化会自动重试
4. 健康数据采集需要相应权限
5. 告警阈值设置需要合理范围

## 📊 性能基准测试

### 数据传输性能
| 指标 | 优化前 | 优化后 | 提升幅度 |
|------|--------|--------|----------|
| 续航时间 | 11小时 | 15-18小时 | +40-60% |
| 数据压缩率 | 0% | 80%+ | 大幅减少传输量 |
| CPU占用 | 高 | 降低40% | 统一定时器调度 |
| 连接稳定性 | 60% | >95% | GATT优化 |
| 传输成功率 | 70% | >90% | 智能重试机制 |

### 健康数据采集频率
- **心率监测**：5秒/次（可配置）
- **血氧检测**：20秒/次
- **体温测量**：20秒/次  
- **压力评估**：30分钟/次
- **步数统计**：实时更新

## 🔧 开发与调试

### 自定义日志系统
```java
// 使用自定义日志工具类
import com.ljwx.watch.utils.CustomLogger;

// 基础日志输出
CustomLogger.info("Tag", "信息日志，支持中文");
CustomLogger.warn("Tag", "警告日志");
CustomLogger.error("Tag", "错误日志");

// 长数据分段输出（解决HiLog截断问题）
CustomLogger.logLongData("HttpService", "上传数据", jsonData);

// 专业化日志方法
CustomLogger.logHealthInfo("断点续传", healthData);
CustomLogger.logDeviceInfo("设备检查", deviceInfo);
CustomLogger.logCommonEvent("SOS事件", deviceInfo, healthInfo);
```

### 传统日志级别配置
```java
// 启用详细日志输出
DataManager.getInstance().setDebugMode(true);

// 配置日志级别
HiLog.setLevel(HiLogLabel.LOG_APP, HiLog.DEBUG);
```

### 性能监控
```java
// 查看缓存状态
HealthDataCache.getInstance().logCacheStatus();

// 监控数据传输
BluetoothService.printTransferStats();

// 缓存空间监控
String summary = healthDataCache.getCacheStatusSummary();
CustomLogger.info("CacheMonitor", summary);
```

### 调试最佳实践
1. **断点续传调试**：使用 `CustomLogger.logLongData()` 完整查看上传数据
2. **健康数据验证**：使用 `CustomLogger.logHealthInfo()` 检查数据字段
3. **设备状态监控**：使用 `CustomLogger.logDeviceInfo()` 跟踪设备变化
4. **缓存状态追踪**：定期打印缓存统计信息
5. **中文日志输出**：直接使用中文描述，无需编码转换

## 🛠️ 核心特性详解

### 电池优化机制
- **统一定时器架构**：从15+个Timer整合为2个主定时器
- **批量上传策略**：10分钟批量上传替代实时传输
- **智能休眠**：系统空闲时自动降低采集频率
- **网络适应性**：根据网络状况动态调整重试策略

### 蓝牙连接稳定性
- **GATT写入优化**：立即响应机制，避免超时
- **连接状态管理**：实时监控连接质量
- **自动重连机制**：网络中断时智能重连
- **流量控制**：防止GATT队列溢出

### 数据完整性保障
- **断点续传**：网络异常时数据自动缓存
- **重复检测**：避免数据重复上传
- **完整性校验**：传输过程数据校验
- **优雅降级**：关键功能异常时的备用方案

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

- **项目主页**：[GitHub Repository](https://github.com/your-org/ljwx-watch)
- **问题反馈**：[Issues](https://github.com/your-org/ljwx-watch/issues)
- **技术文档**：[Wiki](https://github.com/your-org/ljwx-watch/wiki)

## 🔗 相关项目

- [ljwx-bigscreen](../ljwx-bigscreen) - 大屏监控系统
- [ljwx-phone](../ljwx-phone) - 手机客户端
- [ljwx-admin](../ljwx-admin) - 管理后台

---

*最后更新：2025年8月26日 - 新增自定义日志系统，解决HiLog截断和中文显示问题*