package com.ljwx.modules.health.domain.vo;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class OrgStatisticsVO {
    private AlertInfoVO alertInfo;
    private DeviceInfoVO deviceInfo;
    private Map<String, HealthDataVO> healthData;
    private MessageInfoVO messageInfo;
    private UserInfoVO userInfo;

    @Data
    public static class AlertInfoVO {
        private Map<String, Integer> alertStatusCounts;
        private Map<String, Integer> alertTypeCounts;
        private List<TAlertInfoVO> alerts;
        private Map<String, Integer> severityLevelCounts;
        private Integer totalAlerts;
        private Integer uniqueAlertTypes;
    }

    @Data
    public static class DeviceInfoVO {
        private Map<String, Integer> deviceChargingCounts;
        private Map<String, Integer> deviceOsCounts;
        private Map<String, Integer> deviceStatusCounts;
        private Map<String, Integer> deviceWearableCounts;
        private List<TDeviceInfoVO> devices;
        private Boolean success;
        private Integer totalDevices;
    }

    @Data
    public static class HealthDataVO {
        private String altitude;
        private String bloodOxygen;
        private String calorie;
        private String deviceSn;
        private String distance;
        private String heartRate;
        private String latitude;
        private String longitude;
        private String pressureHigh;
        private String pressureLow;
        private String step;
        private String temperature;
        private String timestamp;
        // 其他健康数据字段...
    }

    @Data
    public static class MessageInfoVO {
        private Map<String, Integer> messageStatusCounts;
        private Map<String, Integer> messageTypeCounts;
        private List<TDeviceMessageVO> messages;
        private Boolean success;
        private Integer totalMessages;
        private Integer uniqueMessageTypes;
    }

    @Data
    public static class UserInfoVO {
        // 用户列表
        private List<UserDetailVO> users;
        // 统计信息
        private Map<String, Integer> deviceBindCounts;  // 设备绑定状态统计
        private Map<String, Integer> userStatusCounts;  // 用户状态统计
        private Integer totalUsers;                     // 总用户数
        private Boolean success;
    }

    @Data
    public static class UserDetailVO {
        private Long orgId;
        private String orgName;
        private String deviceSn;
        private String phone;
        private Long userId;
        private String userName;
        private String status;      // 用户状态
        private String bindStatus;  // 设备绑定状态
    }
} 