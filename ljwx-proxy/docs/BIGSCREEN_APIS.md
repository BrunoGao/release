# BigScreen主屏API接口文档

## 概述
此文档描述bigscreen_main.html页面中使用的所有API接口。

## API接口列表

### 1. 健康相关API

#### 1.1 获取健康综合评分
- **当前URL**: `/api/health/score/comprehensive`
- **规范化URL**: `/api/v1/health/scores/comprehensive`
- **方法**: GET
- **描述**: 获取指定用户或组织的健康综合评分
- **参数**:
  ```
  userId?: string - 用户ID (可选)
  orgId?: string - 组织ID (可选) 
  date?: string - 日期 (可选)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "score": 85,
      "level": "良好",
      "details": {...}
    }
  }
  ```

#### 1.2 获取基线健康数据图表
- **当前URL**: `/health_data/chart/baseline`
- **规范化URL**: `/api/v1/health/baseline/chart`
- **方法**: GET
- **描述**: 获取基线健康数据的图表数据
- **参数**:
  ```
  orgId: string - 组织ID (必需)
  startDate: string - 开始日期 (必需)
  endDate: string - 结束日期 (必需)
  ```

#### 1.3 生成基线数据
- **当前URL**: `/api/baseline/generate`
- **规范化URL**: `/api/v1/health/baseline/generate`
- **方法**: POST
- **描述**: 生成健康基线数据
- **请求体**: 
  ```json
  {
    "orgId": "string",
    "dateRange": {...}
  }
  ```

#### 1.4 根据ID获取健康数据
- **当前URL**: `/fetchHealthDataById`
- **规范化URL**: `/api/v1/health/data/{id}`
- **方法**: GET
- **描述**: 根据ID获取具体的健康数据详情
- **参数**:
  ```
  id: string - 健康数据ID (必需)
  ```

### 2. 组织与用户API

#### 2.1 获取总体信息
- **当前URL**: `/get_total_info`
- **规范化URL**: `/api/v1/organizations/statistics`
- **方法**: GET
- **描述**: 获取客户总体统计信息
- **参数**:
  ```
  customer_id: string - 客户ID (必需)
  ```
- **响应示例**:
  ```json
  {
    "code": 200,
    "data": {
      "totalUsers": 1000,
      "activeDevices": 850,
      "departments": 12
    }
  }
  ```

#### 2.2 获取部门信息
- **当前URL**: `/get_departments`
- **规范化URL**: `/api/v1/departments`
- **方法**: GET
- **描述**: 获取指定组织下的部门列表
- **参数**:
  ```
  orgId: string - 组织ID (必需)
  ```

#### 2.3 获取用户信息
- **当前URL**: `/fetch_users`
- **规范化URL**: `/api/v1/users`
- **方法**: GET
- **描述**: 获取指定组织下的用户列表
- **参数**:
  ```
  orgId: string - 组织ID (必需)
  ```

### 3. 统计相关API

#### 3.1 统计概览
- **当前URL**: `/api/statistics/overview`
- **规范化URL**: `/api/v1/statistics/overview`
- **方法**: GET
- **描述**: 获取统计数据概览
- **参数**:
  ```
  orgId: string - 组织ID (必需)
  date?: string - 日期 (可选)
  ```

#### 3.2 实时统计
- **当前URL**: `/api/realtime_stats`
- **规范化URL**: `/api/v1/statistics/realtime`
- **方法**: GET
- **描述**: 获取实时统计数据
- **参数**:
  ```
  customerId: string - 客户ID (必需)
  date?: string - 日期 (可选)
  ```

### 4. 告警相关API

#### 4.1 确认告警
- **当前URL**: `/acknowledge_alert`
- **规范化URL**: `/api/v1/alerts/acknowledge`
- **方法**: POST
- **描述**: 确认指定的告警信息
- **请求体**:
  ```json
  {
    "alertId": "string",
    "userId": "string",
    "comment": "string"
  }
  ```

#### 4.2 处理告警
- **当前URL**: `/dealAlert`
- **规范化URL**: `/api/v1/alerts/deal`
- **方法**: GET/POST
- **描述**: 处理指定的告警
- **参数**:
  ```
  alertId: string - 告警ID (必需)
  ```

## 前端调用示例

### JavaScript调用规范

```javascript
// 规范化的API调用方式
class BigScreenAPI {
  constructor(baseURL = '/api/v1') {
    this.baseURL = baseURL;
  }

  // 获取健康评分
  async getHealthScore(params = {}) {
    const url = new URL(`${this.baseURL}/health/scores/comprehensive`, window.location.origin);
    Object.keys(params).forEach(key => {
      if (params[key]) url.searchParams.append(key, params[key]);
    });
    
    const response = await fetch(url);
    return await response.json();
  }

  // 获取部门列表
  async getDepartments(orgId) {
    const response = await fetch(`${this.baseURL}/departments?orgId=${orgId}`);
    return await response.json();
  }

  // 处理告警
  async dealAlert(alertId) {
    const response = await fetch(`${this.baseURL}/alerts/deal`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ alertId })
    });
    return await response.json();
  }
}

// 使用示例
const api = new BigScreenAPI();
api.getHealthScore({ orgId: '123', date: '2024-01-01' })
   .then(data => console.log(data));
```

## 迁移计划

### 阶段1: 并行支持
- 保持当前API正常工作
- 新增规范化API端点
- 逐步更新前端调用

### 阶段2: 逐步迁移
- 更新bigscreen_main.html中的API调用
- 添加错误处理和回退机制
- 完善API响应格式

### 阶段3: 废弃旧API
- 标记旧API为已废弃
- 完全切换到新API
- 清理冗余代码

## 注意事项

1. **向后兼容**: 在迁移过程中确保向后兼容性
2. **错误处理**: 统一错误响应格式和状态码
3. **参数验证**: 加强输入参数的验证和类型检查
4. **缓存策略**: 对频繁调用的API实施适当的缓存策略
5. **性能监控**: 监控API响应时间和成功率