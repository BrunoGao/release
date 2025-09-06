# Personal个人页面API接口文档

## 概述
此文档描述personal.html个人健康页面中使用的所有API接口。

## API接口列表

### 1. 设备相关API

#### 1.1 获取设备用户信息
- **当前URL**: `/api/device/user_info`
- **规范化URL**: `/api/v1/devices/user-info`
- **方法**: GET
- **描述**: 根据设备序列号获取绑定的用户信息
- **参数**:
  ```
  deviceSn: string - 设备序列号 (必需)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "userId": "123",
      "userName": "张三", 
      "deviceSn": "CRFTQ23409001890",
      "bindTime": "2024-01-01T00:00:00Z"
    }
  }
  ```

#### 1.2 获取设备状态信息
- **当前URL**: `/api/device/info`
- **规范化URL**: `/api/v1/devices/status`
- **方法**: GET
- **描述**: 获取设备的运行状态和基本信息
- **参数**:
  ```
  deviceSn: string - 设备序列号 (必需)
  ```

#### 1.3 获取设备用户组织信息
- **当前URL**: `/api/device/user_org`
- **规范化URL**: `/api/v1/devices/user-organization`
- **方法**: GET
- **描述**: 获取设备用户所属的组织信息
- **参数**:
  ```
  deviceSn: string - 设备序列号 (必需)
  ```

### 2. 健康数据API

#### 2.1 获取实时健康数据
- **当前URL**: `/api/health/realtime_data`
- **规范化URL**: `/api/v1/health/realtime-data`
- **方法**: GET
- **描述**: 获取用户的实时健康监测数据
- **参数**:
  ```
  userId?: string - 用户ID (可选)
  deviceSn?: string - 设备序列号 (可选)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "heartRate": 75,
      "bloodPressure": "120/80",
      "temperature": 36.5,
      "oxygenLevel": 98,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  }
  ```

#### 2.2 获取健康趋势数据
- **当前URL**: `/api/health/trends`
- **规范化URL**: `/api/v1/health/trends`
- **方法**: GET
- **描述**: 获取用户健康数据的历史趋势
- **参数**:
  ```
  userId: string - 用户ID (必需)
  startDate?: string - 开始日期 (可选)
  endDate?: string - 结束日期 (可选)
  ```

#### 2.3 获取个人健康评分
- **当前URL**: `/api/personal/health/scores`
- **规范化URL**: `/api/v1/health/personal/scores`
- **方法**: GET
- **描述**: 获取个人的健康评分详情
- **参数**:
  ```
  userId: string - 用户ID (必需)
  date?: string - 日期 (可选)
  ```

#### 2.4 获取健康建议
- **当前URL**: `/api/health/recommendations`
- **规范化URL**: `/api/v1/health/recommendations`
- **方法**: GET
- **描述**: 基于健康数据获取个性化健康建议
- **参数**:
  ```
  userId: string - 用户ID (必需)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "recommendations": [
        {
          "type": "exercise",
          "title": "增加有氧运动",
          "description": "建议每周进行3-4次有氧运动，每次30分钟",
          "priority": "high"
        }
      ]
    }
  }
  ```

#### 2.5 获取健康预测
- **当前URL**: `/api/health/predictions`
- **规范化URL**: `/api/v1/health/predictions`
- **方法**: GET
- **描述**: 基于历史数据预测健康趋势
- **参数**:
  ```
  userId: string - 用户ID (必需)
  ```

### 3. 用户相关API

#### 3.1 获取用户资料
- **当前URL**: `/api/user/profile`
- **规范化URL**: `/api/v1/users/profile`
- **方法**: GET
- **描述**: 获取用户的详细资料信息
- **参数**:
  ```
  userId: string - 用户ID (必需)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "userId": "123",
      "userName": "张三",
      "age": 30,
      "gender": "male",
      "height": 175,
      "weight": 70,
      "avatar": "avatar.jpg"
    }
  }
  ```

#### 3.2 获取用户消息
- **当前URL**: `/api/messages/user`
- **规范化URL**: `/api/v1/messages/user`
- **方法**: GET
- **描述**: 获取用户的消息列表
- **参数**:
  ```
  userId: string - 用户ID (必需)
  ```

### 4. 告警相关API

#### 4.1 获取用户告警
- **当前URL**: `/api/alerts/user`
- **规范化URL**: `/api/v1/alerts/user`
- **方法**: GET
- **描述**: 获取指定用户的告警信息
- **参数**:
  ```
  userId: string - 用户ID (必需)
  ```

#### 4.2 获取个人告警
- **当前URL**: `/api/personal/alerts`
- **规范化URL**: `/api/v1/alerts/personal`
- **方法**: GET
- **描述**: 获取基于设备的个人告警信息
- **参数**:
  ```
  deviceSn: string - 设备序列号 (必需)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "alerts": [
        {
          "id": "alert_001",
          "type": "HEART_RATE_HIGH",
          "level": "warning",
          "message": "心率过高，请注意休息",
          "timestamp": "2024-01-01T12:00:00Z",
          "status": "active"
        }
      ]
    }
  }
  ```

## 前端调用示例

### JavaScript调用规范

```javascript
// Personal页面API调用类
class PersonalPageAPI {
  constructor(baseURL = '/api/v1') {
    this.baseURL = baseURL;
    this.deviceSn = this.getDeviceSn(); // 从URL参数获取
  }

  // 从URL参数获取设备序列号
  getDeviceSn() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('deviceSn');
  }

  // 获取设备用户信息
  async getDeviceUserInfo() {
    if (!this.deviceSn) throw new Error('Device SN is required');
    
    const response = await fetch(
      `${this.baseURL}/devices/user-info?deviceSn=${this.deviceSn}`
    );
    return await response.json();
  }

  // 获取实时健康数据
  async getRealtimeHealthData() {
    const response = await fetch(
      `${this.baseURL}/health/realtime-data?deviceSn=${this.deviceSn}`
    );
    return await response.json();
  }

  // 获取健康趋势
  async getHealthTrends(userId, dateRange = {}) {
    const params = new URLSearchParams({ userId });
    if (dateRange.startDate) params.append('startDate', dateRange.startDate);
    if (dateRange.endDate) params.append('endDate', dateRange.endDate);
    
    const response = await fetch(`${this.baseURL}/health/trends?${params}`);
    return await response.json();
  }

  // 获取个人告警
  async getPersonalAlerts() {
    const response = await fetch(
      `${this.baseURL}/alerts/personal?deviceSn=${this.deviceSn}`
    );
    return await response.json();
  }

  // 获取健康建议
  async getHealthRecommendations(userId) {
    const response = await fetch(
      `${this.baseURL}/health/recommendations?userId=${userId}`
    );
    return await response.json();
  }
}

// 页面初始化使用示例
document.addEventListener('DOMContentLoaded', async () => {
  const personalAPI = new PersonalPageAPI();
  
  try {
    // 获取设备用户信息
    const userInfo = await personalAPI.getDeviceUserInfo();
    if (userInfo.code === 200) {
      const userId = userInfo.data.userId;
      
      // 并行获取多个数据
      const [healthData, alerts, recommendations] = await Promise.all([
        personalAPI.getRealtimeHealthData(),
        personalAPI.getPersonalAlerts(), 
        personalAPI.getHealthRecommendations(userId)
      ]);
      
      // 渲染页面数据
      renderUserInfo(userInfo.data);
      renderHealthData(healthData.data);
      renderAlerts(alerts.data);
      renderRecommendations(recommendations.data);
    }
  } catch (error) {
    console.error('Failed to load personal page data:', error);
    showErrorMessage('数据加载失败，请刷新重试');
  }
});
```

## 数据流程

### 页面加载流程
1. 从URL获取`deviceSn`参数
2. 调用`/api/v1/devices/user-info`获取用户信息
3. 基于用户ID获取其他相关数据
4. 渲染页面组件

### 实时数据更新
```javascript
// 定时更新实时健康数据
setInterval(async () => {
  const healthData = await personalAPI.getRealtimeHealthData();
  updateHealthDisplay(healthData.data);
}, 10000); // 每10秒更新一次
```

## 错误处理

### 统一错误处理
```javascript
class APIError extends Error {
  constructor(response) {
    super(response.message);
    this.code = response.code;
    this.error = response.error;
    this.details = response.details;
  }
}

async function handleAPIResponse(response) {
  const data = await response.json();
  if (data.code !== 200) {
    throw new APIError(data);
  }
  return data;
}
```

## 性能优化建议

1. **数据缓存**: 对用户资料等不常变化的数据进行缓存
2. **请求合并**: 将多个相关请求合并为单个请求
3. **懒加载**: 非关键数据延迟加载
4. **WebSocket**: 对实时数据使用WebSocket连接
5. **错误重试**: 实现请求失败的自动重试机制