# 大屏系统API文档

## 目录
1. [设备信息接口](#设备信息接口)
2. [健康数据接口](#健康数据接口)
3. [用户信息接口](#用户信息接口)
4. [告警接口](#告警接口)
5. [组织接口](#组织接口)
6. [配置接口](#配置接口)
7. [许可证接口](#许可证接口)
8. [数据查询接口](#数据查询接口)

## 设备信息接口

### 1.1 上传设备信息
- **URL**: `/upload_device_info`
- **Method**: POST
- **Description**: 上传设备信息
- **Request Body**:
```json
{
    "System Software Version": "string",
    "Wifi Address": "string",
    "Bluetooth Address": "string",
    "IP Address": "string",
    "Network Access Mode": "string",
    "SerialNumber": "string",
    "Device Name": "string",
    "IMEI": "string",
    "batteryLevel": "string",
    "wearState": "number",
    "status": "string",
    "customerId": "string",
    "chargingStatus": "string"
}
```
- **Response**: 
```json
{
    "status": "success",
    "message": "设备信息已接收并处理"
}
```

### 1.2 获取设备信息
- **URL**: `/fetch_device_info`
- **Method**: GET
- **Description**: 获取指定设备详细信息
- **Parameters**:
  - `serial_number`: 设备序列号
  - `include_user`: 是否包含用户信息（可选，默认false）
  - `include_org`: 是否包含组织信息（可选，默认false）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "id": "number",
        "device_sn": "string",
        "device_type": "string",
        "device_name": "string",
        "status": "string",
        "battery_level": "number",
        "firmware_version": "string",
        "last_online": "string",
        "system_software_version": "string",
        "wifi_address": "string",
        "bluetooth_address": "string",
        "ip_address": "string",
        "network_access_mode": "string",
        "imei": "string",
        "wear_state": "number",
        "charging_status": "string",
        "user_info": {
            "id": "number",
            "name": "string",
            "phone": "string",
            "department": "string",
            "position": "string"
        },
        "organization_info": {
            "id": "number",
            "name": "string",
            "code": "string"
        }
    }
}
```

### 1.3 收集设备信息
- **URL**: `/gather_device_info`
- **Method**: GET
- **Description**: 收集设备统计信息
- **Parameters**:
  - `customer_id`: 客户ID
  - `orgId`: 组织ID（可选）
  - `deviceType`: 设备类型（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total_devices": "number",
        "online_devices": "number",
        "offline_devices": "number",
        "device_types": {
            "type1": {
                "total": "number",
                "online": "number",
                "offline": "number"
            },
            "type2": {
                "total": "number",
                "online": "number",
                "offline": "number"
            }
        },
        "battery_status": {
            "high": "number",
            "medium": "number",
            "low": "number"
        },
        "wear_status": {
            "worn": "number",
            "not_worn": "number"
        },
        "charging_status": {
            "charging": "number",
            "not_charging": "number"
        },
        "firmware_versions": {
            "version1": "number",
            "version2": "number"
        },
        "organization_stats": [
            {
                "org_id": "number",
                "org_name": "string",
                "total_devices": "number",
                "online_devices": "number"
            }
        ]
    }
}
```

### 1.4 获取组织用户设备
- **URL**: `/fetch_devices_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的设备信息
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `deviceSn`: 设备序列号（可选）
  - `status`: 设备状态（可选，如：online, offline）
  - `deviceType`: 设备类型（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "devices": [
            {
                "id": "number",
                "device_sn": "string",
                "device_type": "string",
                "device_name": "string",
                "status": "string",
                "battery_level": "number",
                "firmware_version": "string",
                "last_online": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "organization_info": {
                    "id": "number",
                    "name": "string",
                    "code": "string"
                }
            }
        ],
        "statistics": {
            "total_devices": "number",
            "online_devices": "number",
            "offline_devices": "number",
            "device_types": {
                "type1": "number",
                "type2": "number"
            },
            "battery_status": {
                "high": "number",
                "medium": "number",
                "low": "number"
            }
        }
    }
}
```

## 健康数据接口

### 2.1 上传健康数据
- **URL**: `/upload_health_data`
- **Method**: POST
- **Description**: 上传健康数据
- **Request Body**: 健康数据对象
- **Response**: 
```json
{
    "success": true,
    "message": "健康数据已接收并处理"
}
```

### 2.2 获取健康数据
- **URL**: `/fetch_health_data`
- **Method**: GET
- **Description**: 获取指定设备的健康数据
- **Parameters**:
  - `deviceSn`: 设备序列号
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
  - `dataType`: 数据类型（可选，如：heart_rate, blood_pressure, temperature 等）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "device_info": {
            "device_sn": "string",
            "device_type": "string",
            "status": "string",
            "battery_level": "number"
        },
        "health_data": [
            {
                "id": "number",
                "device_sn": "string",
                "blood_oxygen": "number",
                "heart_rate": "number",
                "pressure_high": "number",
                "pressure_low": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number",
                "latitude": "number",
                "longitude": "number",
                "altitude": "number",
                "sleep_data": "string",
                "workout_data": "string",
                "exercise_daily_data": "string",
                "exercise_week_data": "string",
                "scientific_sleep_data": "string"
            }
        ],
        "statistics": {
            "heart_rate": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "blood_pressure": {
                "average": "string",
                "min": "string",
                "max": "string",
                "trend": "string"
            },
            "temperature": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "steps": {
                "total": "number",
                "average": "number",
                "trend": "string"
            },
            "blood_oxygen": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            }
        }
    }
}
```

### 2.3 按日期获取健康数据
- **URL**: `/get_health_data_by_date`
- **Method**: GET
- **Description**: 按日期获取健康数据
- **Parameters**:
  - `date`: 日期，格式：YYYY-MM-DD
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `deviceSn`: 设备序列号（可选）
  - `dataType`: 数据类型（可选，如：heart_rate, blood_pressure, temperature 等）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "date": "string",
        "health_data": [
            {
                "id": "number",
                "device_sn": "string",
                "blood_oxygen": "number",
                "heart_rate": "number",
                "pressure_high": "number",
                "pressure_low": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number",
                "latitude": "number",
                "longitude": "number",
                "altitude": "number",
                "sleep_data": "string",
                "workout_data": "string",
                "exercise_daily_data": "string",
                "exercise_week_data": "string",
                "scientific_sleep_data": "string"
            }
        ],
        "statistics": {
            "heart_rate": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "blood_pressure": {
                "average": "string",
                "min": "string",
                "max": "string",
                "trend": "string"
            },
            "temperature": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "steps": {
                "total": "number",
                "average": "number",
                "trend": "string"
            },
            "blood_oxygen": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            }
        }
    }
}
```

### 2.4 获取组织用户健康数据
- **URL**: `/fetch_health_data_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的健康数据，支持按时间范围筛选
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
  - `dataType`: 数据类型（可选，如：heart_rate, blood_pressure, temperature 等）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "user_info": {
            "id": "number",
            "name": "string",
            "phone": "string",
            "department": "string",
            "position": "string",
            "device_sn": "string"
        },
        "health_data": [
            {
                "id": "number",
                "device_sn": "string",
                "blood_oxygen": "number",
                "heart_rate": "number",
                "pressure_high": "number",
                "pressure_low": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number",
                "latitude": "number",
                "longitude": "number",
                "altitude": "number",
                "sleep_data": "string",
                "workout_data": "string",
                "exercise_daily_data": "string",
                "exercise_week_data": "string",
                "scientific_sleep_data": "string"
            }
        ],
        "statistics": {
            "heart_rate": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "blood_pressure": {
                "average": "string",
                "min": "string",
                "max": "string",
                "trend": "string"
            },
            "temperature": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "steps": {
                "total": "number",
                "average": "number",
                "trend": "string"
            },
            "blood_oxygen": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            }
        }
    }
}
```

### 2.5 获取所有健康数据
- **URL**: `/get_all_health_data_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的所有健康数据，支持按时间范围筛选
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "user_info": {
            "id": "number",
            "name": "string",
            "phone": "string",
            "department": "string",
            "position": "string",
            "device_sn": "string"
        },
        "health_data": [
            {
                "id": "number",
                "device_sn": "string",
                "blood_oxygen": "number",
                "heart_rate": "number",
                "pressure_high": "number",
                "pressure_low": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number",
                "latitude": "number",
                "longitude": "number",
                "altitude": "number",
                "sleep_data": "string",
                "workout_data": "string",
                "exercise_daily_data": "string",
                "exercise_week_data": "string",
                "scientific_sleep_data": "string"
            }
        ],
        "statistics": {
            "heart_rate": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "blood_pressure": {
                "average": "string",
                "min": "string",
                "max": "string",
                "trend": "string"
            },
            "temperature": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            },
            "steps": {
                "total": "number",
                "average": "number",
                "trend": "string"
            },
            "blood_oxygen": {
                "average": "number",
                "min": "number",
                "max": "number",
                "trend": "string"
            }
        },
        "health_score": "number",
        "health_level": "string",
        "health_advice": "string"
    }
}
```

## 用户信息接口

### 3.1 获取所有用户
- **URL**: `/get_all_users`
- **Method**: GET
- **Description**: 获取所有用户信息
- **Response**: 
```json
[
    {
        "id": "number",
        "user_name": "string",
        "phone": "string",
        "device_sn": "string",
        "is_deleted": "boolean",
        "create_time": "string",
        "update_time": "string"
    }
]
```

### 3.2 获取个人用户信息
- **URL**: `/fetch_personal_user_info`
- **Method**: GET
- **Description**: 获取个人用户信息
- **Parameters**:
  - `deviceSn`: 设备序列号
- **Response**: 
```json
{
    "success": true,
    "data": {
        "id": "number",
        "user_name": "string",
        "phone": "string",
        "device_sn": "string",
        "is_deleted": "boolean",
        "create_time": "string",
        "update_time": "string"
    }
}
```

### 3.3 获取用户位置
- **URL**: `/fetch_user_locations`
- **Method**: GET
- **Description**: 获取用户位置信息
- **Parameters**:
  - `deviceSn`: 设备序列号
  - `date_str`: 日期字符串
- **Response**: 
```json
{
    "success": true,
    "data": [
        {
            "latitude": "number",
            "longitude": "number",
            "altitude": "number",
            "timestamp": "string"
        }
    ]
}
```

### 3.4 获取组织用户信息
- **URL**: `/get_user_info_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的详细信息
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `phone`: 手机号（可选）
  - `name`: 用户名（可选）
  - `department`: 部门（可选）
  - `status`: 用户状态（可选，如：active, inactive）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "users": [
            {
                "id": "number",
                "user_name": "string",
                "phone": "string",
                "email": "string",
                "department": "string",
                "position": "string",
                "status": "string",
                "create_time": "string",
                "update_time": "string",
                "device_info": {
                    "device_sn": "string",
                    "device_type": "string",
                    "device_name": "string",
                    "status": "string",
                    "battery_level": "number",
                    "last_online": "string"
                },
                "organization_info": {
                    "id": "number",
                    "name": "string",
                    "code": "string",
                    "parent_id": "number"
                },
                "health_info": {
                    "last_heart_rate": "number",
                    "last_blood_pressure": "string",
                    "last_temperature": "number",
                    "last_update": "string"
                }
            }
        ],
        "statistics": {
            "total_users": "number",
            "active_users": "number",
            "inactive_users": "number",
            "department_stats": [
                {
                    "department": "string",
                    "user_count": "number"
                }
            ],
            "position_stats": [
                {
                    "position": "string",
                    "user_count": "number"
                }
            ]
        }
    }
}
```

### 3.5 获取个人综合信息
- **URL**: `/get_personal_info`
- **Method**: GET
- **Description**: 获取个人综合信息，包括用户信息、设备信息和健康数据
- **Parameters**:
  - `deviceSn`: 设备序列号
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "user_info": {
            "id": "number",
            "user_name": "string",
            "phone": "string",
            "email": "string",
            "department": "string",
            "position": "string",
            "status": "string",
            "create_time": "string",
            "update_time": "string"
        },
        "device_info": {
            "id": "number",
            "device_sn": "string",
            "device_type": "string",
            "device_name": "string",
            "status": "string",
            "battery_level": "number",
            "firmware_version": "string",
            "last_online": "string",
            "system_software_version": "string",
            "wifi_address": "string",
            "bluetooth_address": "string",
            "ip_address": "string",
            "network_access_mode": "string",
            "imei": "string",
            "wear_state": "number",
            "charging_status": "string"
        },
        "health_info": {
            "latest": {
                "blood_oxygen": "number",
                "heart_rate": "number",
                "pressure_high": "number",
                "pressure_low": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number"
            },
            "statistics": {
                "heart_rate": {
                    "average": "number",
                    "min": "number",
                    "max": "number",
                    "trend": "string"
                },
                "blood_pressure": {
                    "average": "string",
                    "min": "string",
                    "max": "string",
                    "trend": "string"
                },
                "temperature": {
                    "average": "number",
                    "min": "number",
                    "max": "number",
                    "trend": "string"
                },
                "steps": {
                    "total": "number",
                    "average": "number",
                    "trend": "string"
                },
                "blood_oxygen": {
                    "average": "number",
                    "min": "number",
                    "max": "number",
                    "trend": "string"
                }
            },
            "sleep_data": {
                "total_sleep": "number",
                "deep_sleep": "number",
                "light_sleep": "number",
                "awake_time": "number",
                "sleep_score": "number"
            },
            "exercise_data": {
                "total_steps": "number",
                "total_distance": "number",
                "total_calories": "number",
                "active_minutes": "number",
                "exercise_score": "number"
            }
        },
        "alerts": {
            "total": "number",
            "unhandled": "number",
            "latest": [
                {
                    "id": "number",
                    "alert_type": "string",
                    "alert_level": "string",
                    "alert_time": "string",
                    "alert_message": "string",
                    "status": "string"
                }
            ]
        },
        "messages": {
            "total": "number",
            "unread": "number",
            "latest": [
                {
                    "id": "number",
                    "message_type": "string",
                    "content": "string",
                    "sender": "string",
                    "send_time": "string",
                    "status": "string"
                }
            ]
        }
    }
}
```

### 3.6 获取总体信息
- **URL**: `/get_total_info`
- **Method**: GET
- **Description**: 获取系统总体信息，包括告警、消息、设备、健康数据和用户信息
- **Parameters**:
  - `customer_id`: 客户ID（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "alert_info": {
            "total": "number",
            "alerts": [
                {
                    "id": "number",
                    "device_sn": "string",
                    "alert_type": "string",
                    "alert_level": "string",
                    "alert_time": "string",
                    "alert_message": "string",
                    "status": "string",
                    "handler": "string",
                    "handle_time": "string",
                    "user_info": {
                        "id": "number",
                        "name": "string",
                        "phone": "string",
                        "department": "string",
                        "position": "string"
                    }
                }
            ],
            "statistics": {
                "total_alerts": "number",
                "unhandled_alerts": "number",
                "handled_alerts": "number",
                "alert_types": {
                    "type1": "number",
                    "type2": "number"
                },
                "alert_levels": {
                    "high": "number",
                    "medium": "number",
                    "low": "number"
                }
            }
        },
        "message_info": {
            "total": "number",
            "messages": [
                {
                    "id": "number",
                    "message_type": "string",
                    "content": "string",
                    "sender": "string",
                    "receiver": "string",
                    "send_time": "string",
                    "status": "string",
                    "read_time": "string",
                    "user_info": {
                        "id": "number",
                        "name": "string",
                        "phone": "string",
                        "department": "string",
                        "position": "string"
                    }
                }
            ],
            "statistics": {
                "total_messages": "number",
                "unread_messages": "number",
                "read_messages": "number",
                "message_types": {
                    "type1": "number",
                    "type2": "number"
                }
            }
        },
        "device_info": {
            "total": "number",
            "devices": [
                {
                    "id": "number",
                    "device_sn": "string",
                    "device_type": "string",
                    "device_name": "string",
                    "status": "string",
                    "battery_level": "number",
                    "firmware_version": "string",
                    "last_online": "string",
                    "user_info": {
                        "id": "number",
                        "name": "string",
                        "phone": "string",
                        "department": "string",
                        "position": "string"
                    }
                }
            ],
            "statistics": {
                "total_devices": "number",
                "online_devices": "number",
                "offline_devices": "number",
                "device_types": {
                    "type1": "number",
                    "type2": "number"
                },
                "battery_status": {
                    "high": "number",
                    "medium": "number",
                    "low": "number"
                }
            }
        },
        "health_data": {
            "total": "number",
            "health_records": [
                {
                    "id": "number",
                    "device_sn": "string",
                    "blood_oxygen": "number",
                    "heart_rate": "number",
                    "pressure_high": "number",
                    "pressure_low": "number",
                    "stress": "number",
                    "step": "number",
                    "temperature": "number",
                    "timestamp": "string",
                    "user_info": {
                        "id": "number",
                        "name": "string",
                        "phone": "string",
                        "department": "string",
                        "position": "string"
                    }
                }
            ],
            "statistics": {
                "heart_rate": {
                    "average": "number",
                    "min": "number",
                    "max": "number",
                    "trend": "string"
                },
                "blood_pressure": {
                    "average": "string",
                    "min": "string",
                    "max": "string",
                    "trend": "string"
                },
                "temperature": {
                    "average": "number",
                    "min": "number",
                    "max": "number",
                    "trend": "string"
                },
                "steps": {
                    "total": "number",
                    "average": "number",
                    "trend": "string"
                }
            }
        },
        "user_info": {
            "total": "number",
            "users": [
                {
                    "id": "number",
                    "user_name": "string",
                    "phone": "string",
                    "email": "string",
                    "department": "string",
                    "position": "string",
                    "status": "string",
                    "device_info": {
                        "device_sn": "string",
                        "device_type": "string",
                        "device_name": "string",
                        "status": "string",
                        "battery_level": "number"
                    }
                }
            ],
            "statistics": {
                "total_users": "number",
                "active_users": "number",
                "inactive_users": "number",
                "department_stats": [
                    {
                        "department": "string",
                        "user_count": "number"
                    }
                ],
                "position_stats": [
                    {
                        "position": "string",
                        "user_count": "number"
                    }
                ]
            }
        }
    }
}
```


## 告警接口

### 4.1 上传告警
- **URL**: `/upload_alerts`
- **Method**: POST
- **Description**: 上传告警信息
- **Request Body**: 告警数据对象
- **Response**: 
```json
{
    "success": true,
    "message": "告警信息已接收并处理"
}
```

### 4.2 获取告警
- **URL**: `/fetch_alerts`
- **Method**: GET
- **Description**: 获取告警信息
- **Parameters**:
  - `deviceSn`: 设备序列号
  - `customerId`: 客户ID
- **Response**: 
```json
{
    "success": true,
    "data": [
        {
            "id": "number",
            "device_sn": "string",
            "alert_type": "string",
            "alert_level": "string",
            "alert_time": "string",
            "alert_message": "string",
            "is_deleted": "boolean",
            "create_time": "string",
            "update_time": "string"
        }
    ]
}
```

### 4.3 获取组织用户告警
- **URL**: `/get_alerts_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的告警信息
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `deviceSn`: 设备序列号（可选）
  - `alertType`: 告警类型（可选）
  - `alertLevel`: 告警等级（可选）
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
  - `status`: 告警状态（可选，如：unhandled, handled）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "alerts": [
            {
                "id": "number",
                "device_sn": "string",
                "alert_type": "string",
                "alert_level": "string",
                "alert_time": "string",
                "alert_message": "string",
                "status": "string",
                "handler": "string",
                "handle_time": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "device_info": {
                    "device_type": "string",
                    "device_name": "string",
                    "status": "string",
                    "battery_level": "number"
                }
            }
        ],
        "statistics": {
            "total_alerts": "number",
            "unhandled_alerts": "number",
            "handled_alerts": "number",
            "alert_types": {
                "type1": "number",
                "type2": "number"
            },
            "alert_levels": {
                "high": "number",
                "medium": "number",
                "low": "number"
            },
            "daily_stats": [
                {
                    "date": "string",
                    "count": "number"
                }
            ]
        }
    }
}
```

### 4.4 获取组织用户消息
- **URL**: `/get_messages_by_orgIdAndUserId`
- **Method**: GET
- **Description**: 获取指定组织用户的消息
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `deviceSn`: 设备序列号（可选）
  - `messageType`: 消息类型（可选）
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
  - `status`: 消息状态（可选，如：unread, read）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "messages": [
            {
                "id": "number",
                "message_type": "string",
                "content": "string",
                "sender": "string",
                "receiver": "string",
                "send_time": "string",
                "status": "string",
                "read_time": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "device_info": {
                    "device_sn": "string",
                    "device_type": "string",
                    "device_name": "string"
                }
            }
        ],
        "statistics": {
            "total_messages": "number",
            "unread_messages": "number",
            "read_messages": "number",
            "message_types": {
                "type1": "number",
                "type2": "number"
            },
            "daily_stats": [
                {
                    "date": "string",
                    "count": "number"
                }
            ]
        }
    }
}
```

## 组织接口

### 5.1 获取部门信息
- **URL**: `/get_departments_by_orgId`
- **Method**: GET
- **Description**: 根据组织ID获取部门信息
- **Parameters**:
  - `orgId`: 组织ID
- **Response**: 
```json
{
    "success": true,
    "data": [
        {
            "id": "string",
            "name": "string",
            "parent_id": "string"
        }
    ]
}
```

## 配置接口

### 6.1 获取配置信息
- **URL**: `/fetch_config`
- **Method**: GET
- **Description**: 获取配置信息
- **Parameters**:
  - `customerId`: 客户ID
- **Response**: 
```json
{
    "customer_name": "string",
    "customer_id": "string",
    "upload_method": "string",
    "health_data": {
        "data_type": "string:number:boolean:number:number:number"
    },
    "is_support_license": "boolean",
    "license_key": "number",
    "interface_data": {
        "interface_name": "string;number;boolean;string;string"
    }
}
```

## 许可证接口

### 7.1 检查许可证
- **URL**: `/checkLicense`
- **Method**: GET
- **Description**: 检查许可证状态
- **Parameters**:
  - `customerId`: 客户ID
- **Response**: 
```json
{
    "success": true,
    "isExceeded": "boolean",
    "license_key": "number"
}
```

## 通用返回格式

所有接口返回数据遵循以下格式：

```json
{
    "success": true/false,
    "data": {
        // 具体数据
    },
    "error": "错误信息" // 仅在失败时返回
}
```

## 错误码说明

- 200: 请求成功
- 400: 请求参数错误
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 500: 服务器内部错误

## 注意事项

1. 所有接口都需要进行身份验证
2. 时间格式统一使用 "YYYY-MM-DD HH:mm:ss"
3. 所有接口都支持跨域请求
4. 建议使用HTTPS进行通信
5. 接口调用频率限制：100次/分钟 

## 移动端接口

### 8.1 手机号登录
- **URL**: `/phone_login`
- **Method**: GET
- **Description**: 使用手机号登录系统
- **Parameters**:
  - `phone`: 手机号
  - `password`: 密码
- **Response**: 
```json
{
    "success": true,
    "data": {
        "token": "string",
        "user_info": {
            "id": "number",
            "name": "string",
            "phone": "string",
            "department": "string",
            "position": "string"
        }
    }
}
```

### 8.2 重置密码
- **URL**: `/phone/reset_password`
- **Method**: POST
- **Description**: 重置用户密码
- **Parameters**:
  - `userId`: 用户ID
- **Response**: 
```json
{
    "success": true,
    "data": {
        "message": "密码重置成功",
        "new_password": "string"
    }
}
```

### 8.3 获取移动端健康数据
- **URL**: `/get_all_health_data_by_orgIdAndUserId_mobile`
- **Method**: GET
- **Description**: 获取移动端健康数据
- **Parameters**:
  - `phone`: 手机号
  - `startDate`: 开始日期
  - `endDate`: 结束日期
- **Response**: 
```json
{
    "success": true,
    "data": {
        "user_info": {
            "name": "string",
            "phone": "string"
        },
        "health_data": [
            {
                "bloodOxygen": "number",
                "heartRate": "number",
                "pressureHigh": "number",
                "pressureLow": "number",
                "stress": "number",
                "step": "number",
                "temperature": "number",
                "timestamp": "string"
            }
        ],
        "statistics": {
            "average_heart_rate": "number",
            "average_blood_pressure": "string",
            "total_steps": "number",
            "average_temperature": "number"
        }
    }
}
``` 

## 数据查询接口

### 10.1 获取所有健康数据
- **URL**: `/health_data/all`
- **Method**: GET
- **Description**: 获取指定组织和用户的所有健康数据，支持按时间范围筛选
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
  - `startDate`: 开始日期，格式：YYYY-MM-DD（可选）
  - `endDate`: 结束日期，格式：YYYY-MM-DD（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "healthData": [
            {
                "deviceSn": "string",
                "userName": "string",
                "deptName": "string",
                "bloodOxygen": "number",
                "heartRate": "number",
                "pressureHigh": "number",
                "pressureLow": "number",
                "stress": "number",
                "step": "string",
                "temperature": "string",
                "timestamp": "string",
                "distance": "number",
                "calorie": "number",
                "latitude": "number",
                "longitude": "number",
                "altitude": "number",
                "sleepData": "string",
                "workoutData": "string",
                "exerciseDailyData": "string",
                "exerciseDailyWeekData": "string",
                "scientificSleepData": "string"
            }
        ],
        "totalRecords": "number",
        "statistics": {
            "totalDevices": "number",
            "devicesWithData": "number",
            "averageStats": {
                "avgTemperature": "number",
                "avgHeartRate": "number",
                "avgBloodOxygen": "number",
                "avgStep": "number",
                "avgDistance": "number",
                "avgCalorie": "number"
            }
        },
        "departmentStats": {
            "department_name": {
                "deviceCount": "number",
                "userCount": "number",
                "averageStats": {
                    "avgTemperature": "number",
                    "avgHeartRate": "number",
                    "avgBloodOxygen": "number",
                    "avgStep": "number",
                    "avgDistance": "number",
                    "avgCalorie": "number"
                }
            }
        },
        "deviceCount": "number",
        "orgId": "string",
        "userId": "string"
    }
}
```

### 10.2 获取所有设备数据
- **URL**: `/device/all`
- **Method**: GET
- **Description**: 获取指定组织和用户的所有设备数据
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "devices": [
            {
                "id": "number",
                "device_sn": "string",
                "device_type": "string",
                "device_name": "string",
                "status": "string",
                "battery_level": "number",
                "firmware_version": "string",
                "last_online": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "organization_info": {
                    "id": "number",
                    "name": "string",
                    "code": "string"
                }
            }
        ],
        "statistics": {
            "total_devices": "number",
            "online_devices": "number",
            "offline_devices": "number",
            "device_types": {
                "type1": "number",
                "type2": "number"
            },
            "battery_status": {
                "high": "number",
                "medium": "number",
                "low": "number"
            }
        }
    }
}
```

### 10.3 获取所有告警数据
- **URL**: `/alert/all`
- **Method**: GET
- **Description**: 获取指定组织和用户的所有告警数据
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "alerts": [
            {
                "id": "number",
                "device_sn": "string",
                "alert_type": "string",
                "alert_level": "string",
                "alert_time": "string",
                "alert_message": "string",
                "status": "string",
                "handler": "string",
                "handle_time": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "device_info": {
                    "device_type": "string",
                    "device_name": "string",
                    "status": "string",
                    "battery_level": "number"
                }
            }
        ],
        "statistics": {
            "total_alerts": "number",
            "unhandled_alerts": "number",
            "handled_alerts": "number",
            "alert_types": {
                "type1": "number",
                "type2": "number"
            },
            "alert_levels": {
                "high": "number",
                "medium": "number",
                "low": "number"
            },
            "daily_stats": [
                {
                    "date": "string",
                    "count": "number"
                }
            ]
        }
    }
}
```

### 10.4 获取所有消息数据
- **URL**: `/message/all`
- **Method**: GET
- **Description**: 获取指定组织和用户的所有消息数据
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "messages": [
            {
                "id": "number",
                "message_type": "string",
                "content": "string",
                "sender": "string",
                "receiver": "string",
                "send_time": "string",
                "status": "string",
                "read_time": "string",
                "user_info": {
                    "id": "number",
                    "name": "string",
                    "phone": "string",
                    "department": "string",
                    "position": "string"
                },
                "device_info": {
                    "device_sn": "string",
                    "device_type": "string",
                    "device_name": "string"
                }
            }
        ],
        "statistics": {
            "total_messages": "number",
            "unread_messages": "number",
            "read_messages": "number",
            "message_types": {
                "type1": "number",
                "type2": "number"
            },
            "daily_stats": [
                {
                    "date": "string",
                    "count": "number"
                }
            ]
        }
    }
}
```

### 10.5 获取所有用户数据
- **URL**: `/user/all`
- **Method**: GET
- **Description**: 获取指定组织的所有用户数据
- **Parameters**:
  - `orgId`: 组织ID（可选）
  - `userId`: 用户ID（可选）
- **Response**: 
```json
{
    "success": true,
    "data": {
        "total": "number",
        "users": [
            {
                "id": "number",
                "user_name": "string",
                "phone": "string",
                "email": "string",
                "department": "string",
                "position": "string",
                "status": "string",
                "create_time": "string",
                "update_time": "string",
                "device_info": {
                    "device_sn": "string",
                    "device_type": "string",
                    "device_name": "string",
                    "status": "string",
                    "battery_level": "number"
                },
                "organization_info": {
                    "id": "number",
                    "name": "string",
                    "code": "string",
                    "parent_id": "number"
                },
                "health_info": {
                    "last_heart_rate": "number",
                    "last_blood_pressure": "string",
                    "last_temperature": "number",
                    "last_update": "string"
                }
            }
        ],
        "statistics": {
            "total_users": "number",
            "active_users": "number",
            "inactive_users": "number",
            "department_stats": [
                {
                    "department": "string",
                    "user_count": "number"
                }
            ],
            "position_stats": [
                {
                    "position": "string",
                    "user_count": "number"
                }
            ]
        }
    }
}
```

### 注意事项

1. 所有 /*/all 接口都支持组织和用户级别的数据过滤
2. 返回的数据包含统计信息和详细记录
3. 建议在数据量较大时使用分页接口
4. 所有时间格式统一使用 "YYYY-MM-DD HH:mm:ss"
5. 接口调用频率限制：50次/分钟 