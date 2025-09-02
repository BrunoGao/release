import 'package:flutter/foundation.dart';
import 'package:ljwx_health_new/models/device_model.dart' as device;

class UserInfo {
  final Map<String, int> departmentCount;
  final Map<String, DepartmentStats> departmentStats;
  final Map<String, int> deviceCount;
  final String? orgId;
  final Map<String, int> statusCount;
  final int totalDevices;
  final int totalUsers;
  final List<User> users;

  UserInfo({
    required this.departmentCount,
    required this.departmentStats,
    required this.deviceCount,
    this.orgId,
    required this.statusCount,
    required this.totalDevices,
    required this.totalUsers,
    required this.users,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    return UserInfo(
      departmentCount: Map<String, int>.from(json['departmentCount'] ?? {}),
      departmentStats: (json['departmentStats'] as Map<String, dynamic>? ?? {}).map(
        (key, value) => MapEntry(key, DepartmentStats.fromJson(value)),
      ),
      deviceCount: Map<String, int>.from(json['deviceCount'] ?? {}),
      orgId: json['orgId'] as String?,
      statusCount: Map<String, int>.from(json['statusCount'] ?? {}),
      totalDevices: json['totalDevices'] as int? ?? 0,
      totalUsers: json['totalUsers'] as int? ?? 0,
      users: (json['users'] as List<dynamic>? ?? [])
          .map((e) => User.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'departmentCount': departmentCount,
    'departmentStats': departmentStats.map((key, value) => MapEntry(key, value.toJson())),
    'deviceCount': deviceCount,
    'orgId': orgId,
    'statusCount': statusCount,
    'totalDevices': totalDevices,
    'totalUsers': totalUsers,
      'users': users.map((e) => e.toJson()).toList(),
    };
}

class User {
  final String? avatar;
  final String chargingStatus;
  final String createTime;
  final List<String> deptHierarchy;
  final String deptId;
  final String deptName;
  final String deviceSn;
  final String deviceStatus;
  final String phoneNumber;
  final String position;
  final String status;
  final String updateTime;
  final String? userCardNumber;
  final String userId;
  final String userName;
  final String wearableStatus;
  final int workingYears;

  User({
    this.avatar,
    required this.chargingStatus,
    required this.createTime,
    required this.deptHierarchy,
    required this.deptId,
    required this.deptName,
    required this.deviceSn,
    required this.deviceStatus,
    required this.phoneNumber,
    required this.position,
    required this.status,
    required this.updateTime,
    this.userCardNumber,
    required this.userId,
    required this.userName,
    required this.wearableStatus,
    required this.workingYears,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      avatar: json['avatar'] as String?,
      chargingStatus: json['charging_status'] as String? ?? '',
      createTime: json['create_time'] as String? ?? '',
      deptHierarchy: (json['dept_hierarchy'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
      deptId: json['dept_id'] as String? ?? '',
      deptName: json['dept_name'] as String? ?? '',
      deviceSn: json['device_sn'] as String? ?? '',
      deviceStatus: json['device_status'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      position: json['position'] as String? ?? '',
      status: json['status'] as String? ?? '',
      updateTime: json['update_time'] as String? ?? '',
      userCardNumber: json['user_card_number'] as String?,
      userId: json['user_id'] as String? ?? '',
      userName: json['user_name'] as String? ?? '',
      wearableStatus: json['wearable_status'] as String? ?? '',
      workingYears: json['working_years'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
      'avatar': avatar,
      'charging_status': chargingStatus,
      'create_time': createTime,
    'dept_hierarchy': deptHierarchy,
      'dept_id': deptId,
      'dept_name': deptName,
      'device_sn': deviceSn,
      'device_status': deviceStatus,
      'phone_number': phoneNumber,
      'position': position,
      'status': status,
      'update_time': updateTime,
      'user_card_number': userCardNumber,
      'user_id': userId,
      'user_name': userName,
      'wearable_status': wearableStatus,
      'working_years': workingYears,
    };

  factory User.empty() {
    return User(
      avatar: null,
      chargingStatus: '',
      createTime: '',
      deptHierarchy: [],
      deptId: '',
      deptName: '',
      deviceSn: '',
      deviceStatus: '',
      phoneNumber: '',
      position: '',
      status: '',
      updateTime: '',
      userCardNumber: null,
      userId: '',
      userName: '',
      wearableStatus: '',
      workingYears: 0,
    );
  }
}

class DepartmentStats {
  final DeviceStats deviceStats;
  final String name;
  final Map<String, int> statusStats;
  final int totalUsers;

  DepartmentStats({
    required this.deviceStats,
    required this.name,
    required this.statusStats,
    required this.totalUsers,
  });

  factory DepartmentStats.fromJson(Map<String, dynamic> json) {
    return DepartmentStats(
      deviceStats: DeviceStats.fromJson(json['device_stats'] ?? {}),
      name: json['name'] ?? '',
      statusStats: Map<String, int>.from(json['status_stats'] ?? {}),
      totalUsers: json['total_users'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
      'device_stats': deviceStats.toJson(),
      'name': name,
      'status_stats': statusStats,
      'total_users': totalUsers,
    };
}

class DeviceStats {
  final Map<String, int> charging;
  final Map<String, int> status;
  final int total;
  final Map<String, int> wearing;

  DeviceStats({
    required this.charging,
    required this.status,
    required this.total,
    required this.wearing,
  });

  factory DeviceStats.fromJson(Map<String, dynamic> json) {
    return DeviceStats(
      charging: Map<String, int>.from(json['charging'] ?? {}),
      status: Map<String, int>.from(json['status'] ?? {}),
      total: json['total'] ?? 0,
      wearing: Map<String, int>.from(json['wearing'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() => {
      'charging': charging,
      'status': status,
      'total': total,
      'wearing': wearing,
    };
} 