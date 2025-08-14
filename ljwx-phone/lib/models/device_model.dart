import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:flutter/foundation.dart';

class Device {
  final int id;
  final String serialNumber;
  final String bluetoothAddress;
  final String chargingStatus;
  final String batteryLevel;
  final String status;
  final String systemSoftwareVersion;
  final String? createTime;
  final String updateTime;
  final String wearableStatus;
  final bool isDeleted;
  final String? departmentName;
  final String? userName;

  Device({
    required this.id,
    required this.serialNumber,
    required this.bluetoothAddress,
    required this.chargingStatus,
    required this.batteryLevel,
    required this.status,
    required this.systemSoftwareVersion,
    this.createTime,
    required this.updateTime,
    required this.wearableStatus,
    required this.isDeleted,
    this.departmentName,
    this.userName,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      serialNumber: json['serial_number']?.toString() ?? '',
      bluetoothAddress: json['bluetooth_address']?.toString() ?? '',
      chargingStatus: json['charging_status']?.toString() ?? '',
      batteryLevel: json['battery_level']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      systemSoftwareVersion: json['system_software_version']?.toString() ?? '',
      createTime: json['create_time']?.toString(),
      updateTime: json['update_time']?.toString() ?? '',
      wearableStatus: json['wearable_status']?.toString() ?? '',
      isDeleted: json['is_deleted'] is bool ? json['is_deleted'] : (json['is_deleted']?.toString() == 'true'),
      departmentName: json['department_name']?.toString(),
      userName: json['user_name']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'serial_number': serialNumber,
      'bluetooth_address': bluetoothAddress,
      'charging_status': chargingStatus,
      'battery_level': batteryLevel,
      'status': status,
      'system_software_version': systemSoftwareVersion,
      'create_time': createTime,
      'update_time': updateTime,
      'wearable_status': wearableStatus,
      'is_deleted': isDeleted,
      'department_name': departmentName,
      'user_name': userName,
    };
  }
}

class DeviceInfo {
  final List<Device> devices;

  DeviceInfo({
    required this.devices,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    final devicesList = json['devices'] is List ? json['devices'] as List : [];
    return DeviceInfo(
      devices: devicesList.map((e) => Device.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'devices': devices.map((e) => e.toJson()).toList(),
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

class HealthData {
  final String date;
  final String type;
  final double value;
  final String unit;

  HealthData({
    required this.date,
    required this.type,
    required this.value,
    required this.unit,
  });

  factory HealthData.fromJson(Map<String, dynamic> json) {
    return HealthData(
      date: json['date'] as String,
      type: json['type'] as String,
      value: json['value'] as double,
      unit: json['unit'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'type': type,
      'value': value,
      'unit': unit,
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