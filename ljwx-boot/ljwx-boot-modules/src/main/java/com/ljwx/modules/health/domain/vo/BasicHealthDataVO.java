/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 基础健康数据VO - 仅包含快字段用于表格展示
 * 不包含daily/weekly慢字段，避免复杂查询影响性能
 * 
 * @author Claude Code
 */
@Data
public class BasicHealthDataVO {
    
    // ========== 基础信息 ==========
    
    /**
     * 主键ID
     */
    private Long id;
    
    /**
     * 用户ID
     */
    private String userId;
    
    /**
     * 用户名称
     */
    private String userName;
    
    /**
     * 客户ID
     */
    private Long customerId;
    
    /**
     * 组织ID
     */
    private Long orgId;
    
    /**
     * 组织名称
     */
    private String orgName;
    
    /**
     * 设备序列号
     */
    private String deviceSn;
    
    /**
     * 时间戳
     */
    private LocalDateTime timestamp;
    
    // ========== 基础生理指标（快字段） ==========
    
    /**
     * 心率 (bpm)
     */
    private Integer heartRate;
    
    /**
     * 血氧饱和度 (%)
     */
    private Integer bloodOxygen;
    
    /**
     * 体温 (°C)
     */
    private Double temperature;
    
    /**
     * 收缩压 (mmHg)
     */
    private Integer pressureHigh;
    
    /**
     * 舒张压 (mmHg)
     */
    private Integer pressureLow;
    
    /**
     * 压力指数
     */
    private Integer stress;
    
    /**
     * 步数
     */
    private Integer step;
    
    /**
     * 卡路里 (kcal)
     */
    private Double calorie;
    
    /**
     * 距离 (km)
     */
    private Double distance;
    
    // ========== 位置信息 ==========
    
    /**
     * 纬度
     */
    private Double latitude;
    
    /**
     * 经度
     */
    private Double longitude;
    
    /**
     * 海拔高度 (m)
     */
    private Double altitude;
    
    // ========== 辅助方法 ==========
    
    /**
     * 获取坐标字符串（用于前端显示）
     */
    public String getCoordinates() {
        if (latitude != null && longitude != null) {
            return String.format("%.6f, %.6f", latitude, longitude);
        }
        return "-";
    }
    
    /**
     * 获取血压字符串（用于前端显示）
     */
    public String getBloodPressure() {
        if (pressureHigh != null && pressureLow != null) {
            return pressureHigh + "/" + pressureLow;
        }
        return "-";
    }
    
    /**
     * 判断生理指标是否完整
     */
    public boolean isVitalSignsComplete() {
        return heartRate != null && bloodOxygen != null && 
               pressureHigh != null && pressureLow != null && 
               temperature != null;
    }
    
    /**
     * 判断活动数据是否完整
     */
    public boolean isActivityDataComplete() {
        return step != null && calorie != null && distance != null;
    }
}