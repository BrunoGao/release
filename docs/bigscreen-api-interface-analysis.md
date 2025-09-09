# BigScreen 系统 API 接口完整分析报告

## 概述

本文档详细分析了 ljwx-bigscreen 系统中所有模板文件的 API 接口调用情况，为系统重构和优化提供技术支持。

## 分析范围

- ***_view.html 文件**: 10个专门的视图文件
- **bigscreen_main.html**: 主界面文件 
- **personal.html**: 个人健康大屏文件

## API 接口分类与汇总

### 1. 数据获取类接口 (Data Retrieval APIs)

#### 1.1 组织用户数据接口
```
GET /get_users_by_orgIdAndUserId?orgId={orgId}&userId={userId}
GET /get_devices_by_orgIdAndUserId?orgId={orgId}&userId={userId}
GET /get_health_data_by_orgIdAndUserId?orgId={orgId}&userId={userId}
GET /get_messages_by_orgIdAndUserId?orgId={orgId}&userId={userId}
GET /get_alerts_by_orgIdAndUserId?orgId={orgId}&userId={userId}
```
**使用文件**: alert_view.html, device_view.html, health_view.html, message_view.html, user_view.html
**参数模式**: 统一的 orgId + userId 过滤模式
**响应处理**: 更新相应的数据表格和统计图表

#### 1.2 组织架构接口
```
GET /get_departments?orgId={orgId}&customerId={customerId}
GET /fetch_users?orgId={deptId}
```
**使用文件**: message_view.html, bigscreen_main.html
**用途**: 获取部门列表和用户列表，支持级联选择

#### 1.3 个人详细数据接口
```
GET /get_health_data_by_deviceSn?deviceSn={deviceSn}
GET /get_personal_info?deviceSn={deviceSn}
GET /personal?deviceSn={deviceSn}
```
**使用文件**: health_view.html, user_view.html, personal.html
**用途**: 获取特定设备/用户的详细信息

### 2. 健康数据分析接口 (Health Analysis APIs)

#### 2.1 健康评分接口
```
GET /api/health/score/comprehensive?orgId={orgId}&startDate={startDate}&endDate={endDate}&includeFactors=true
GET /api/health/score/comprehensive?days=7
GET /api/health/score/comprehensive?deviceSns[]={deviceSns}&includeDeviceBreakdown=true
```
**使用文件**: bigscreen_main.html
**参数特点**: 支持多种查询模式（时间范围、天数、设备列表）
**功能**: 综合健康评分计算和分析

#### 2.2 健康基线接口
```
GET /health_data/chart/baseline?orgId={orgId}&startDate={startDate}&endDate={endDate}
POST /api/baseline/generate
```
**使用文件**: bigscreen_main.html
**功能**: 健康基线数据获取和生成

#### 2.3 健康分析接口
```
GET /api/health/trends/analysis?deviceSn={deviceSn}&timeRange={timeRange}
GET /api/health/analysis/comprehensive?deviceSn={deviceSn}&days=30
GET /api/health/recommendations?analysisType=comprehensive
GET /api/health/recommendations?deviceSn={deviceSn}&analysisType=comprehensive
```
**使用文件**: bigscreen_main.html, personal.html
**功能**: 健康趋势分析、综合分析、健康建议生成

### 3. 实时数据接口 (Real-time Data APIs)

#### 3.1 统计概览接口
```
GET /api/statistics/overview?orgId={orgId}&date={date}
GET /api/realtime_stats?customerId={customerId}&date={date}
GET /get_total_info
```
**使用文件**: bigscreen_main.html
**功能**: 实时统计数据获取，支持按日期和组织过滤

#### 3.2 个人实时数据接口
```
GET /api/personal/realtime-health?userId={userId}&cardType={cardType}&deviceSn={deviceSn}
GET /api/personal/history-health?userId={userId}&cardType={cardType}&days=7
GET /api/personal/ai-analysis?userId={userId}&cardType={cardType}&analysisType=comprehensive
GET /api/personal/alerts?deviceSn={deviceSn}
```
**使用文件**: personal.html
**功能**: 个人健康数据的实时获取和AI分析

### 4. 设备管理接口 (Device Management APIs)

#### 4.1 设备信息接口
```
GET /api/device/info?deviceSn={deviceSn}
GET /api/device/user_org?deviceSn={deviceSn}
GET /api/health_data/latest?deviceSn={deviceSn}
```
**使用文件**: personal.html
**功能**: 设备基本信息、用户组织关联、最新健康数据

#### 4.2 设备分析接口
```
GET /api/device/history/trends?orgId={orgId}&userId={userId}&days={days}
GET /api/device/battery/prediction?orgId={orgId}&userId={userId}&days={days}
GET /api/device/analysis/comprehensive?orgId={orgId}&userId={userId}&days={days}
```
**使用文件**: device_view.html
**功能**: 设备历史趋势、电池预测、综合分析

### 5. 告警处理接口 (Alert Management APIs)

#### 5.1 告警处理接口
```
GET ./dealAlert?alertId={alertId}
POST ./batchDealAlert
     Body: {alertIds: [...]}
POST /acknowledge_alert
     Body: {alertId, acknowledgedBy, ...}
```
**使用文件**: alert_view.html, bigscreen_main.html
**功能**: 单个告警处理、批量告警处理、告警确认

### 6. 消息通信接口 (Message Communication APIs)

#### 6.1 消息发送接口
```
POST /DeviceMessage/save_message
     Content-Type: application/json
     Body: {content, type, receivers, ...}
```
**使用文件**: message_view.html
**功能**: 发送系统消息

### 7. 轨迹数据接口 (Track Data APIs)

```
GET /api/tracks
```
**使用文件**: track_view.html
**功能**: 获取轨迹数据用于地图可视化

### 8. 外部服务接口 (External Service APIs)

#### 8.1 地理编码服务
```
GET https://restapi.amap.com/v3/geocode/regeo?key={key}&location={lng},{lat}
```
**使用文件**: bigscreen_main.html
**功能**: 高德地图逆地理编码服务

#### 8.2 CDN资源
```
https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js
https://webapi.amap.com/maps?v=2.0&key={key}
https://webapi.amap.com/loca?v=2.0.0&key={key}
```
**使用文件**: bigscreen_main.html
**功能**: Socket.IO实时通信、高德地图API

## API 接口命名模式分析

### 当前命名问题

1. **不一致的命名风格**:
   - 旧式: `/get_xxx_by_orgIdAndUserId`
   - RESTful: `/api/xxx/xxx`
   - 简化式: `./dealAlert`

2. **参数传递不统一**:
   - URL参数: `?orgId={orgId}&userId={userId}`
   - 路径参数: `/api/device/{deviceSn}`
   - 请求体参数: JSON格式

3. **缺乏版本控制**:
   - 大部分接口没有版本标识
   - 新旧接口混用

### 接口使用模式统计

| 命名模式 | 接口数量 | 使用频率 | 示例 |
|---------|---------|---------|------|
| `/get_xxx_by_xxx` | 8 | 高 | `/get_health_data_by_orgIdAndUserId` |
| `/api/xxx/xxx` | 15 | 中高 | `/api/health/score/comprehensive` |
| `./xxxAction` | 3 | 低 | `./dealAlert` |
| `/fetch_xxx` | 2 | 低 | `/fetch_users` |

## 技术特性分析

### 1. 统一API调用函数

**bigscreen_main.html** 实现了统一的API调用封装:
```javascript
function apiCall(url, options = {}) {
    // 自动添加customerId参数
    // 统一错误处理
    // 请求日志记录
    return fetch(urlWithCustomerId, finalOptions);
}
```

### 2. 数据缓存机制

所有 `*_view.html` 文件都实现了数据缓存:
```javascript
window.addEventListener('message', function(event) {
    if (event.data.type === 'xxxInfo') {
        cachedXxxInfo = event.data.data;
        // 使用缓存避免重复API调用
    }
});
```

### 3. 自动刷新机制

大部分页面支持可配置的自动刷新:
- 刷新间隔: 5-30秒
- 手动控制: 暂停/恢复
- 智能暂停: 页面隐藏时自动暂停

### 4. 错误处理机制

统一的错误处理模式:
- 网络错误捕获
- HTTP状态码检查
- 用户友好的错误提示
- 自动重试机制

## 性能优化特性

### 1. 并行数据加载

多个相关API同时调用以减少加载时间:
```javascript
Promise.all([
    apiCall('/api/health/score'),
    apiCall('/api/device/info'),
    apiCall('/api/statistics/overview')
]).then(results => {
    // 并行处理结果
});
```

### 2. 条件加载

根据用户权限和页面状态条件加载数据:
- 用户ID存在时才加载个人数据
- 设备在线时才加载实时数据
- 权限验证后才显示敏感信息

### 3. 数据预处理

前端进行数据预处理减少后端压力:
- 日期格式标准化
- 参数验证和清理
- 默认值设置

## 安全特性

### 1. 参数验证

所有用户输入都进行前端验证:
- 必填字段检查
- 数据格式验证
- 长度限制检查

### 2. 权限控制

基于用户角色和组织的访问控制:
- orgId参数强制传递
- 用户级别数据过滤
- 敏感操作二次确认

## 重构建议概述

基于以上分析，系统需要进行以下重构优化:

1. **统一API命名规范**
2. **实现RESTful架构**
3. **添加API版本控制**
4. **优化参数传递模式**
5. **增强错误处理机制**
6. **改善数据缓存策略**
7. **提升安全性和性能**

详细的重构建议和实施方案将在下一份文档中提供。

---

*本文档生成时间: 2025-09-09*
*分析范围: ljwx-bigscreen/bigscreen/bigScreen/templates/ 目录*
*总计分析文件: 12个主要模板文件*
*发现API接口: 35+个不同的接口端点*