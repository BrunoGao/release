# API命名规范文档

## 规范化原则

### 1. RESTful API设计原则
- 使用标准HTTP方法 (GET, POST, PUT, DELETE)
- 资源名词化，动作动词化
- URL层级结构清晰
- 统一的响应格式

### 2. URL路径规范
```
/api/{version}/{resource}/{action}
```

### 3. 命名约定
- 使用小写字母和连字符 (kebab-case)
- 资源名称使用复数形式
- 动作使用动词原形
- 避免冗余的前缀或后缀

## 当前API分析

### bigscreen_main.html API调用分析

#### 🔴 不规范的API (需要标准化)
| 当前API | 问题 | 建议规范化 |
|---------|------|------------|
| `/get_total_info` | 下划线命名，动词前缀 | `/api/v1/organizations/statistics` |
| `/get_departments` | 下划线命名，动词前缀 | `/api/v1/departments` |
| `/fetch_users` | 动词前缀 | `/api/v1/users` |
| `/fetchHealthDataById` | 驼峰命名，动词前缀 | `/api/v1/health/data/{id}` |
| `/health_data/chart/baseline` | 下划线命名，结构混乱 | `/api/v1/health/baseline/chart` |
| `/acknowledge_alert` | 下划线命名 | `/api/v1/alerts/acknowledge` |
| `/dealAlert` | 驼峰命名 | `/api/v1/alerts/deal` |

#### ✅ 规范的API (保持不变)
- `/api/health/score/comprehensive` → `/api/v1/health/scores/comprehensive`
- `/api/baseline/generate` → `/api/v1/health/baseline/generate`
- `/api/statistics/overview` → `/api/v1/statistics/overview`
- `/api/realtime_stats` → `/api/v1/statistics/realtime`

### personal.html API调用分析

#### ✅ 大部分已规范
- `/api/device/user_info` → `/api/v1/devices/user-info`
- `/api/health/realtime_data` → `/api/v1/health/realtime-data`
- `/api/health/trends` → `/api/v1/health/trends`
- `/api/user/profile` → `/api/v1/users/profile`
- `/api/messages/user` → `/api/v1/messages/user`
- `/api/alerts/user` → `/api/v1/alerts/user`

## 标准化建议

### 1. 版本控制
所有API添加版本前缀 `/api/v1/`

### 2. 资源分组
```
/api/v1/health/*     - 健康相关API
/api/v1/devices/*    - 设备相关API  
/api/v1/users/*      - 用户相关API
/api/v1/alerts/*     - 告警相关API
/api/v1/statistics/* - 统计相关API
/api/v1/organizations/* - 组织相关API
```

### 3. 响应格式标准化
```json
{
  "code": 200,
  "message": "success", 
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 4. 错误处理标准化
```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error": "INVALID_PARAMS",
  "details": "userId is required",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 实施计划

1. **阶段一**: 创建新的规范化API端点
2. **阶段二**: 更新前端模板使用新API
3. **阶段三**: 废弃旧的不规范API
4. **阶段四**: 全面测试和文档更新