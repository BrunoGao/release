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
        private List<AlertDetailVO> alerts;
        private Map<String, Integer> severityLevelCounts;
        private Integer totalAlerts;
        private Integer uniqueAlertTypes;
    }
    
    @Data
    public static class AlertDetailVO {
        private Long id;
        private String userName;
        private Long orgId;
        private String alertType;
        private String deviceSn;
        private String alertStatus;
        private String severityLevel;
        private Long healthId;
        private java.time.LocalDateTime alertTimestamp;
        private String alertDesc;
        private String createUser;
        private java.time.LocalDateTime createTime;
    }

    @Data
    public static class DeviceInfoVO {
        private Map<String, Integer> deviceChargingCounts;
        private Map<String, Integer> deviceOsCounts;
        private Map<String, Integer> deviceStatusCounts;
        private Map<String, Integer> deviceWearableCounts;
        private List<DeviceDetailVO> devices;
        private Boolean success;
        private Integer totalDevices;
    }
    
    @Data
    public static class DeviceDetailVO {
        private String chargingStatus;
        private String serialNumber;
        private String status;
        private String systemSoftwareVersion;
        private String wearableStatus;
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
        private List<MessageDetailVO> messages;
        private Boolean success;
        private Integer totalMessages;
        private Integer uniqueMessageTypes;
    }
    
    @Data
    public static class MessageDetailVO {
        private String deviceSn;
        private Long id;
        private String message;
        private String messageStatus;
        private String messageType;
        private java.time.LocalDateTime receivedTime;
        private java.time.LocalDateTime sentTime;
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