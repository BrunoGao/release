/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 健康数据事件模型
 * 用于告警规则引擎的数据输入
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataEvent
 * @CreateTime 2025-09-23
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthDataEvent {
    
    /**
     * 设备序列号
     */
    private String deviceSn;
    
    /**
     * 用户ID
     */
    private Long userId;
    
    /**
     * 组织ID
     */
    private Long orgId;
    
    /**
     * 客户ID
     */
    private Long customerId;
    
    /**
     * 健康数据映射表
     */
    @Builder.Default
    private Map<String, Object> healthData = new HashMap<>();
    
    /**
     * 数据时间戳
     */
    private LocalDateTime timestamp;
    
    /**
     * 原始数据
     */
    private Map<String, Object> rawData;
    
    /**
     * 获取指定健康指标的值
     */
    public Object getValue(String physicalSign) {
        if (physicalSign == null) {
            return null;
        }
        
        // 支持多种字段名映射
        switch (physicalSign.toLowerCase()) {
            case "heart_rate":
                return healthData.getOrDefault("heart_rate", healthData.get("heartRate"));
            case "blood_oxygen":
                return healthData.getOrDefault("blood_oxygen", healthData.get("bloodOxygen"));
            case "body_temperature":
            case "temperature":
                return healthData.getOrDefault("body_temperature", 
                       healthData.getOrDefault("temperature", healthData.get("bodyTemperature")));
            case "blood_pressure_systolic":
            case "pressure_high":
                return healthData.getOrDefault("blood_pressure_systolic", 
                       healthData.getOrDefault("pressure_high", healthData.get("pressureHigh")));
            case "blood_pressure_diastolic":
            case "pressure_low":
                return healthData.getOrDefault("blood_pressure_diastolic", 
                       healthData.getOrDefault("pressure_low", healthData.get("pressureLow")));
            case "step":
                return healthData.get("step");
            case "distance":
                return healthData.get("distance");
            case "calorie":
                return healthData.get("calorie");
            case "stress":
                return healthData.get("stress");
            case "latitude":
                return healthData.get("latitude");
            case "longitude":
                return healthData.get("longitude");
            case "altitude":
                return healthData.get("altitude");
            default:
                return healthData.get(physicalSign);
        }
    }
    
    /**
     * 设置健康指标值
     */
    public void setValue(String physicalSign, Object value) {
        if (physicalSign != null && value != null) {
            healthData.put(physicalSign, value);
        }
    }
    
    /**
     * 从Map构建HealthDataEvent
     */
    public static HealthDataEvent fromMap(Map<String, Object> data) {
        if (data == null) {
            return null;
        }
        
        HealthDataEvent event = HealthDataEvent.builder()
            .deviceSn(getStringValue(data, "deviceSn", "device_sn", "device_id"))
            .userId(getLongValue(data, "userId", "user_id"))
            .orgId(getLongValue(data, "orgId", "org_id"))
            .customerId(getLongValue(data, "customerId", "customer_id"))
            .rawData(data)
            .timestamp(LocalDateTime.now())
            .build();
        
        // 复制所有健康数据字段
        Map<String, Object> healthData = new HashMap<>();
        
        // 标准字段映射
        putIfPresent(healthData, "heart_rate", data.get("heart_rate"));
        putIfPresent(healthData, "blood_oxygen", data.get("blood_oxygen"));
        putIfPresent(healthData, "body_temperature", data.get("body_temperature"));
        putIfPresent(healthData, "blood_pressure_systolic", data.get("blood_pressure_systolic"));
        putIfPresent(healthData, "blood_pressure_diastolic", data.get("blood_pressure_diastolic"));
        putIfPresent(healthData, "step", data.get("step"));
        putIfPresent(healthData, "distance", data.get("distance"));
        putIfPresent(healthData, "calorie", data.get("calorie"));
        putIfPresent(healthData, "stress", data.get("stress"));
        putIfPresent(healthData, "latitude", data.get("latitude"));
        putIfPresent(healthData, "longitude", data.get("longitude"));
        putIfPresent(healthData, "altitude", data.get("altitude"));
        
        event.setHealthData(healthData);
        return event;
    }
    
    private static String getStringValue(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object value = data.get(key);
            if (value != null) {
                return value.toString();
            }
        }
        return null;
    }
    
    private static Long getLongValue(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object value = data.get(key);
            if (value != null) {
                try {
                    if (value instanceof Number) {
                        return ((Number) value).longValue();
                    } else {
                        return Long.parseLong(value.toString());
                    }
                } catch (NumberFormatException e) {
                    // 继续尝试下一个key
                }
            }
        }
        return null;
    }
    
    private static void putIfPresent(Map<String, Object> target, String key, Object value) {
        if (value != null) {
            target.put(key, value);
        }
    }
}