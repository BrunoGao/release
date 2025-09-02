import 'package:ljwx_health_new/models/login_response.dart';
import 'package:flutter/foundation.dart';

class Alert {
  final String alertId;
  final String alertDesc;
  final String alertStatus;
  final String alertTimestamp;
  final String alertType;
  final double? altitude;
  final List<String> deptHierarchy;
  final String deptId;
  final String deptName;
  final String deviceSn;
  final String healthId;
  final double latitude;
  final double longitude;
  final String severityLevel;
  final String userId;
  final String userName;

  Alert({
    required this.alertId,
    required this.alertDesc,
    required this.alertStatus,
    required this.alertTimestamp,
    required this.alertType,
    this.altitude,
    required this.deptHierarchy,
    required this.deptId,
    required this.deptName,
    required this.deviceSn,
    required this.healthId,
    required this.latitude,
    required this.longitude,
    required this.severityLevel,
    required this.userId,
    required this.userName,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      alertId: json['alert_id']?.toString() ?? '',
      alertDesc: json['alert_desc']?.toString() ?? '',
      alertStatus: json['alert_status']?.toString() ?? '',
      alertTimestamp: json['alert_timestamp']?.toString() ?? '',
      alertType: json['alert_type']?.toString() ?? '',
      altitude: json['altitude'] == null ? null : double.tryParse(json['altitude'].toString()),
      deptHierarchy: (json['dept_hierarchy'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      deptId: json['dept_id']?.toString() ?? '',
      deptName: json['dept_name']?.toString() ?? '',
      deviceSn: json['device_sn']?.toString() ?? '',
      healthId: json['health_id']?.toString() ?? '',
      latitude: double.tryParse(json['latitude']?.toString() ?? '0') ?? 0.0,
      longitude: double.tryParse(json['longitude']?.toString() ?? '0') ?? 0.0,
      severityLevel: json['severity_level']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      userName: json['user_name']?.toString() ?? '',
    );
  }

  factory Alert.fromLoginData(Alert loginAlert) {
    return Alert(
      alertId: loginAlert.alertId,
      alertDesc: loginAlert.alertDesc,
      alertStatus: loginAlert.alertStatus,
      alertTimestamp: loginAlert.alertTimestamp,
      alertType: loginAlert.alertType,
      altitude: loginAlert.altitude,
      deptHierarchy: loginAlert.deptHierarchy,
      deptId: loginAlert.deptId,
      deptName: loginAlert.deptName,
      deviceSn: loginAlert.deviceSn,
      healthId: loginAlert.healthId,
      latitude: loginAlert.latitude,
      longitude: loginAlert.longitude,
      severityLevel: loginAlert.severityLevel,
      userId: loginAlert.userId,
      userName: loginAlert.userName,
    );
  }

  String get id => alertId;

  Alert copyWith({
    String? alertId,
    String? alertDesc,
    String? alertStatus,
    String? alertTimestamp,
    String? alertType,
    double? altitude,
    List<String>? deptHierarchy,
    String? deptId,
    String? deptName,
    String? deviceSn,
    String? healthId,
    double? latitude,
    double? longitude,
    String? severityLevel,
    String? userId,
    String? userName,
  }) {
    return Alert(
      alertId: alertId ?? this.alertId,
      alertDesc: alertDesc ?? this.alertDesc,
      alertStatus: alertStatus ?? this.alertStatus,
      alertTimestamp: alertTimestamp ?? this.alertTimestamp,
      alertType: alertType ?? this.alertType,
      altitude: altitude ?? this.altitude,
      deptHierarchy: deptHierarchy ?? this.deptHierarchy,
      deptId: deptId ?? this.deptId,
      deptName: deptName ?? this.deptName,
      deviceSn: deviceSn ?? this.deviceSn,
      healthId: healthId ?? this.healthId,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      severityLevel: severityLevel ?? this.severityLevel,
      userId: userId ?? this.userId,
      userName: userName ?? this.userName,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'alert_id': alertId,
      'alert_desc': alertDesc,
      'alert_status': alertStatus,
      'alert_timestamp': alertTimestamp,
      'alert_type': alertType,
      'altitude': altitude,
      'dept_hierarchy': deptHierarchy,
      'dept_id': deptId,
      'dept_name': deptName,
      'device_sn': deviceSn,
      'health_id': healthId,
      'latitude': latitude,
      'longitude': longitude,
      'severity_level': severityLevel,
      'user_id': userId,
      'user_name': userName,
    };
  }
}

class AlertInfo {
  final Map<String, int> alertLevelCount;
  final Map<String, int> alertStatusCount;
  final Map<String, int> alertTypeCount;
  final List<Alert> alerts;

  AlertInfo({
    required this.alertLevelCount,
    required this.alertStatusCount,
    required this.alertTypeCount,
    required this.alerts,
  });

  factory AlertInfo.fromJson(Map<String, dynamic> json) {
    return AlertInfo(
      alertLevelCount: Map<String, int>.from(json['alertLevelCount'] ?? {}),
      alertStatusCount: Map<String, int>.from(json['alertStatusCount'] ?? {}),
      alertTypeCount: Map<String, int>.from(json['alertTypeCount'] ?? {}),
      alerts: (json['alerts'] as List<dynamic>? ?? [])
          .map((e) => Alert.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'alertLevelCount': alertLevelCount,
    'alertStatusCount': alertStatusCount,
    'alertTypeCount': alertTypeCount,
    'alerts': alerts.map((e) => e.toJson()).toList(),
  };

  factory AlertInfo.empty() {
    return AlertInfo(
      alertLevelCount: {},
      alertStatusCount: {},
      alertTypeCount: {},
      alerts: [],
    );
  }
}

class DepartmentAlertStats {
  final String name;
  final Map<String, int> severityStats;
  final Map<String, int> statusStats;
  final int totalAlerts;
  final int totalDevices;
  final int totalUsers;
  final Map<String, int> typeStats;

  DepartmentAlertStats({
    required this.name,
    required this.severityStats,
    required this.statusStats,
    required this.totalAlerts,
    required this.totalDevices,
    required this.totalUsers,
    required this.typeStats,
  });

  factory DepartmentAlertStats.fromJson(Map<String, dynamic> json) {
    return DepartmentAlertStats(
      name: json['name'] ?? '',
      severityStats: Map<String, int>.from(json['severity_stats'] ?? {}),
      statusStats: Map<String, int>.from(json['status_stats'] ?? {}),
      totalAlerts: json['total_alerts'] ?? 0,
      totalDevices: json['total_devices'] ?? 0,
      totalUsers: json['total_users'] ?? 0,
      typeStats: Map<String, int>.from(json['type_stats'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'severity_stats': severityStats,
      'status_stats': statusStats,
      'total_alerts': totalAlerts,
      'total_devices': totalDevices,
      'total_users': totalUsers,
      'type_stats': typeStats,
    };
  }
} 