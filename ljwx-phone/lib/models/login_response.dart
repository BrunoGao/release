import 'device_model.dart';
import 'alert_model.dart';
import 'message_model.dart';
import 'health_model.dart';
import 'user_model.dart';

class LoginResponse {
  final bool success;
  final LoginData? data;
  final String? error;

  LoginResponse({
    required this.success,
    this.data,
    this.error,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      success: json['success'] ?? false,
      data: json['data'] != null ? LoginData.fromJson(json['data']) : null,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'data': data?.toJson(),
      'error': error,
    };
  }
}

class LoginData {
  final String deviceSn;
  final String phone;
  final int userId;
  final String userName;
  final String token;
  final bool isAdmin;
  final List<UserRole> roles;
  final String? adminUrl;
  final String? webUsername;
  final String? webPassword;
  final String? webPasswordSha;

  LoginData({
    required this.deviceSn,
    required this.phone,
    required this.userId,
    required this.userName,
    required this.token,
    this.isAdmin = false,
    this.roles = const [],
    this.adminUrl,
    this.webUsername,
    this.webPassword,
    this.webPasswordSha,
  });

  factory LoginData.fromJson(Map<String, dynamic> json) {
    return LoginData(
      deviceSn: json['device_sn'] ?? '',
      phone: json['phone'] ?? '',
      userId: json['user_id'] ?? 0,
      userName: json['user_name'] ?? '',
      token: json['token'] ?? '',
      isAdmin: json['isAdmin'] ?? false,
      roles: (json['roles'] as List<dynamic>?)
          ?.map((role) => UserRole.fromJson(role))
          .toList() ?? [],
      adminUrl: json['adminUrl'] as String?,
      webUsername: json['webUsername'] as String?,
      webPassword: json['webPassword'] as String?,
      webPasswordSha: json['webPasswordSha'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'device_sn': deviceSn,
      'phone': phone,
      'user_id': userId,
      'user_name': userName,
      'token': token,
      'isAdmin': isAdmin,
      'roles': roles.map((role) => role.toJson()).toList(),
      'adminUrl': adminUrl,
      'webUsername': webUsername,
      'webPassword': webPassword,
      'webPasswordSha': webPasswordSha,
    };
  }
}

class UserRole {
  final int roleId;
  final String roleName;
  final String roleCode;
  final String? description;

  UserRole({
    required this.roleId,
    required this.roleName,
    required this.roleCode,
    this.description,
  });

  factory UserRole.fromJson(Map<String, dynamic> json) {
    return UserRole(
      roleId: json['role_id'] ?? 0,
      roleName: json['role_name'] ?? '',
      roleCode: json['role_code'] ?? '',
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'role_id': roleId,
      'role_name': roleName,
      'role_code': roleCode,
      'description': description,
    };
  }
}

class ConfigInfo {
  final String customerId;
  final String customerName;
  final HealthDataConfig healthData;
  final InterfaceData interfaceData;
  final int isSupportLicense;
  final int licenseKey;
  final String uploadMethod;

  ConfigInfo({
    required this.customerId,
    required this.customerName,
    required this.healthData,
    required this.interfaceData,
    required this.isSupportLicense,
    required this.licenseKey,
    required this.uploadMethod,
  });

  factory ConfigInfo.fromJson(Map<String, dynamic> json) {
    return ConfigInfo(
      customerId: json['customer_id'] ?? '',
      customerName: json['customer_name'] ?? '',
      healthData: HealthDataConfig.fromJson(json['health_data'] ?? {}),
      interfaceData: InterfaceData.fromJson(json['interface_data'] ?? {}),
      isSupportLicense: json['is_support_license'] ?? 0,
      licenseKey: json['license_key'] ?? 0,
      uploadMethod: json['upload_method'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'customer_id': customerId,
      'customer_name': customerName,
      'health_data': healthData.toJson(),
      'interface_data': interfaceData.toJson(),
      'is_support_license': isSupportLicense,
      'license_key': licenseKey,
      'upload_method': uploadMethod,
    };
  }
}

class HealthDataConfig {
  final String bloodOxygen;
  final String calorie;
  final String distance;
  final String heartRate;
  final String location;
  final String sleep;
  final String step;
  final String stress;
  final String temperature;

  HealthDataConfig({
    required this.bloodOxygen,
    required this.calorie,
    required this.distance,
    required this.heartRate,
    required this.location,
    required this.sleep,
    required this.step,
    required this.stress,
    required this.temperature,
  });

  factory HealthDataConfig.fromJson(Map<String, dynamic> json) {
    return HealthDataConfig(
      bloodOxygen: json['blood_oxygen'] ?? '',
      calorie: json['calorie'] ?? '',
      distance: json['distance'] ?? '',
      heartRate: json['heart_rate'] ?? '',
      location: json['location'] ?? '',
      sleep: json['sleep'] ?? '',
      step: json['step'] ?? '',
      stress: json['stress'] ?? '',
      temperature: json['temperature'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'blood_oxygen': bloodOxygen,
      'calorie': calorie,
      'distance': distance,
      'heart_rate': heartRate,
      'location': location,
      'sleep': sleep,
      'step': step,
      'stress': stress,
      'temperature': temperature,
    };
  }
}

class InterfaceData {
  final String fetchConfig;
  final String fetchMessage;
  final String uploadCommonEvent;
  final String uploadDeviceInfo;
  final String uploadHealthData;

  InterfaceData({
    required this.fetchConfig,
    required this.fetchMessage,
    required this.uploadCommonEvent,
    required this.uploadDeviceInfo,
    required this.uploadHealthData,
  });

  factory InterfaceData.fromJson(Map<String, dynamic> json) {
    return InterfaceData(
      fetchConfig: json['fetch_config'] ?? '',
      fetchMessage: json['fetch_message'] ?? '',
      uploadCommonEvent: json['upload_common_event'] ?? '',
      uploadDeviceInfo: json['upload_device_info'] ?? '',
      uploadHealthData: json['upload_health_data'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'fetch_config': fetchConfig,
      'fetch_message': fetchMessage,
      'upload_common_event': uploadCommonEvent,
      'upload_device_info': uploadDeviceInfo,
      'upload_health_data': uploadHealthData,
    };
  }
}

class UserInfo {
  final String id;
  final String name;
  final String department;
  final String role;
  final String email;
  final String phone;
  final String avatar;
  final DepartmentUserStats stats;

  UserInfo({
    required this.id,
    required this.name,
    required this.department,
    required this.role,
    required this.email,
    required this.phone,
    required this.avatar,
    required this.stats,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    return UserInfo(
      id: json['id'] as String,
      name: json['name'] as String,
      department: json['department'] as String,
      role: json['role'] as String,
      email: json['email'] as String,
      phone: json['phone'] as String,
      avatar: json['avatar'] as String,
      stats: DepartmentUserStats.fromJson(json['stats']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'department': department,
      'role': role,
      'email': email,
      'phone': phone,
      'avatar': avatar,
      'stats': stats.toJson(),
    };
  }
}

class DepartmentUserStats {
  final int totalUsers;
  final int activeUsers;
  final int inactiveUsers;
  final int totalDevices;
  final int activeDevices;
  final int inactiveDevices;

  DepartmentUserStats({
    required this.totalUsers,
    required this.activeUsers,
    required this.inactiveUsers,
    required this.totalDevices,
    required this.activeDevices,
    required this.inactiveDevices,
  });

  factory DepartmentUserStats.fromJson(Map<String, dynamic> json) {
    return DepartmentUserStats(
      totalUsers: json['totalUsers'] as int,
      activeUsers: json['activeUsers'] as int,
      inactiveUsers: json['inactiveUsers'] as int,
      totalDevices: json['totalDevices'] as int,
      activeDevices: json['activeDevices'] as int,
      inactiveDevices: json['inactiveDevices'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'totalUsers': totalUsers,
      'activeUsers': activeUsers,
      'inactiveUsers': inactiveUsers,
      'totalDevices': totalDevices,
      'activeDevices': activeDevices,
      'inactiveDevices': inactiveDevices,
    };
  }
}

class HealthData {
  final Map<String, double> vitals;
  final Map<String, List<double>> trends;
  final Map<String, Map<String, dynamic>> stats;
  final String lastUpdate;

  HealthData({
    required this.vitals,
    required this.trends,
    required this.stats,
    required this.lastUpdate,
  });

  factory HealthData.fromJson(Map<String, dynamic> json) {
    return HealthData(
      vitals: Map<String, double>.from(json['vitals']),
      trends: Map<String, List<double>>.from(
        json['trends'].map((key, value) => MapEntry(
          key,
          (value as List).map((e) => (e as num).toDouble()).toList(),
        )),
      ),
      stats: Map<String, Map<String, dynamic>>.from(json['stats']),
      lastUpdate: json['lastUpdate'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'vitals': vitals,
      'trends': trends,
      'stats': stats,
      'lastUpdate': lastUpdate,
    };
  }
}

class AlertInfo {
  final List<Alert> alerts;
  final int criticalCount;
  final int highCount;
  final int mediumCount;
  final int lowCount;

  AlertInfo({
    required this.alerts,
    required this.criticalCount,
    required this.highCount,
    required this.mediumCount,
    required this.lowCount,
  });

  factory AlertInfo.fromJson(Map<String, dynamic> json) {
    return AlertInfo(
      alerts: (json['alerts'] as List<dynamic>)
          .map((e) => Alert.fromJson(e as Map<String, dynamic>))
          .toList(),
      criticalCount: json['critical_count'] as int,
      highCount: json['high_count'] as int,
      mediumCount: json['medium_count'] as int,
      lowCount: json['low_count'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'alerts': alerts.map((e) => e.toJson()).toList(),
      'critical_count': criticalCount,
      'high_count': highCount,
      'medium_count': mediumCount,
      'low_count': lowCount,
    };
  }
}

class Alert {
  final String id;
  final String title;
  final String description;
  final String severity;
  final String severityLevel;
  final String timestamp;
  final bool isAcknowledged;
  final String type;
  final String deptName;
  final String userName;
  final String deviceName;
  final double value;
  final double threshold;
  final String alertStatus;

  Alert({
    required this.id,
    required this.title,
    required this.description,
    required this.severity,
    required this.severityLevel,
    required this.timestamp,
    required this.isAcknowledged,
    required this.type,
    required this.deptName,
    required this.userName,
    required this.deviceName,
    required this.value,
    required this.threshold,
    required this.alertStatus,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      severity: json['severity'] as String,
      severityLevel: json['severityLevel'] as String,
      timestamp: json['timestamp'] as String,
      isAcknowledged: json['is_acknowledged'] as bool,
      type: json['type'] as String,
      deptName: json['deptName'] as String,
      userName: json['userName'] as String,
      deviceName: json['deviceName'] as String,
      value: (json['value'] as num).toDouble(),
      threshold: (json['threshold'] as num).toDouble(),
      alertStatus: json['alertStatus'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'severity': severity,
      'severityLevel': severityLevel,
      'timestamp': timestamp,
      'is_acknowledged': isAcknowledged,
      'type': type,
      'deptName': deptName,
      'userName': userName,
      'deviceName': deviceName,
      'value': value,
      'threshold': threshold,
      'alertStatus': alertStatus,
    };
  }
}

class Message {
  final String id;
  final String title;
  final String content;
  final String message;
  final String timestamp;
  final String sentTime;
  final String sender;
  final String type;
  final String messageType;
  final bool isRead;

  Message({
    required this.id,
    required this.title,
    required this.content,
    required this.message,
    required this.timestamp,
    required this.sentTime,
    required this.sender,
    required this.type,
    required this.messageType,
    required this.isRead,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      title: json['title'] as String,
      content: json['content'] as String,
      message: json['message'] as String,
      timestamp: json['timestamp'] as String,
      sentTime: json['sentTime'] as String,
      sender: json['sender'] as String,
      type: json['type'] as String,
      messageType: json['messageType'] as String,
      isRead: json['isRead'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'message': message,
      'timestamp': timestamp,
      'sentTime': sentTime,
      'sender': sender,
      'type': type,
      'messageType': messageType,
      'isRead': isRead,
    };
  }
}

class MessageInfo {
  final List<Message> messages;
  final int unreadCount;
  final int totalCount;

  MessageInfo({
    required this.messages,
    required this.unreadCount,
    required this.totalCount,
  });

  factory MessageInfo.fromJson(Map<String, dynamic> json) {
    return MessageInfo(
      messages: (json['messages'] as List)
          .map((message) => Message.fromJson(message))
          .toList(),
      unreadCount: json['unreadCount'] as int,
      totalCount: json['totalCount'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'messages': messages.map((message) => message.toJson()).toList(),
      'unreadCount': unreadCount,
      'totalCount': totalCount,
    };
  }
}

class DeviceInfo {
  final String id;
  final String name;
  final String type;
  final String status;
  final String lastConnection;
  final String macAddress;
  final String firmwareVersion;
  final int batteryLevel;
  final bool isConnected;
  final String lastSync;
  final Map<String, dynamic> stats;
  final Map<String, List<double>> trends;
  final List<UsageData> usageData;
  final List<HealthData> healthData;
  final List<BatteryData> batteryData;
  final DeviceStatistics statistics;

  DeviceInfo({
    required this.id,
    required this.name,
    required this.type,
    required this.status,
    required this.lastConnection,
    required this.macAddress,
    required this.firmwareVersion,
    required this.batteryLevel,
    required this.isConnected,
    required this.lastSync,
    required this.stats,
    required this.trends,
    required this.usageData,
    required this.healthData,
    required this.batteryData,
    required this.statistics,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    return DeviceInfo(
      id: json['id'] as String,
      name: json['name'] as String,
      type: json['type'] as String,
      status: json['status'] as String,
      lastConnection: json['lastConnection'] as String,
      macAddress: json['macAddress'] as String,
      firmwareVersion: json['firmwareVersion'] as String,
      batteryLevel: json['batteryLevel'] as int,
      isConnected: json['isConnected'] as bool,
      lastSync: json['lastSync'] as String,
      stats: json['stats'] as Map<String, dynamic>,
      trends: Map<String, List<double>>.from(
        json['trends'].map((key, value) => MapEntry(
          key,
          (value as List).map((e) => (e as num).toDouble()).toList(),
        )),
      ),
      usageData: (json['usageData'] as List)
          .map((e) => UsageData.fromJson(e as Map<String, dynamic>))
          .toList(),
      healthData: (json['healthData'] as List)
          .map((e) => HealthData.fromJson(e as Map<String, dynamic>))
          .toList(),
      batteryData: (json['batteryData'] as List)
          .map((e) => BatteryData.fromJson(e as Map<String, dynamic>))
          .toList(),
      statistics: DeviceStatistics.fromJson(json['statistics'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'status': status,
      'lastConnection': lastConnection,
      'macAddress': macAddress,
      'firmwareVersion': firmwareVersion,
      'batteryLevel': batteryLevel,
      'isConnected': isConnected,
      'lastSync': lastSync,
      'stats': stats,
      'trends': trends,
      'usageData': usageData.map((e) => e.toJson()).toList(),
      'healthData': healthData.map((e) => e.toJson()).toList(),
      'batteryData': batteryData.map((e) => e.toJson()).toList(),
      'statistics': statistics.toJson(),
    };
  }
}

class UsageData {
  final String date;
  final int hours;
  final int minutes;

  UsageData({
    required this.date,
    required this.hours,
    required this.minutes,
  });

  factory UsageData.fromJson(Map<String, dynamic> json) {
    return UsageData(
      date: json['date'] as String,
      hours: json['hours'] as int,
      minutes: json['minutes'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'hours': hours,
      'minutes': minutes,
    };
  }
}

class BatteryData {
  final String date;
  final int level;
  final bool isCharging;

  BatteryData({
    required this.date,
    required this.level,
    required this.isCharging,
  });

  factory BatteryData.fromJson(Map<String, dynamic> json) {
    return BatteryData(
      date: json['date'] as String,
      level: json['level'] as int,
      isCharging: json['is_charging'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'level': level,
      'is_charging': isCharging,
    };
  }
}

class DeviceStatistics {
  final int totalDays;
  final int totalRecords;
  final int syncCount;

  DeviceStatistics({
    required this.totalDays,
    required this.totalRecords,
    required this.syncCount,
  });

  factory DeviceStatistics.fromJson(Map<String, dynamic> json) {
    return DeviceStatistics(
      totalDays: json['total_days'] as int,
      totalRecords: json['total_records'] as int,
      syncCount: json['sync_count'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_days': totalDays,
      'total_records': totalRecords,
      'sync_count': syncCount,
    };
  }
} 