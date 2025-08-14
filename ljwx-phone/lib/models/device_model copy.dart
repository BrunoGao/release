import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:flutter/foundation.dart';

class Device {
  final String deviceSn;
  final String bluetoothAddress;
  final String chargingStatus;
  final String status;
  final String softwareVersion;
  final String updateTime;
  final String wearableStatus;

  Device({
    required this.deviceSn,
    required this.bluetoothAddress,
    required this.chargingStatus,
    required this.status,
    required this.softwareVersion,
    required this.updateTime,
    required this.wearableStatus,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      deviceSn: json['device_sn']?.toString() ?? '',
      bluetoothAddress: json['bluetooth_address']?.toString() ?? '',
      chargingStatus: json['charging_status']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      softwareVersion: json['software_version']?.toString() ?? '',
      updateTime: json['update_time']?.toString() ?? '',
      wearableStatus: json['wearable_status']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'device_sn': deviceSn,
    'bluetooth_address': bluetoothAddress,
    'charging_status': chargingStatus,
    'status': status,
    'software_version': softwareVersion,
    'update_time': updateTime,
    'wearable_status': wearableStatus,
  };
}

class DeviceInfo {
  final List<Device> devices;

  DeviceInfo({
    required this.devices,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    final devicesList = json['devices'] as List<dynamic>;
    return DeviceInfo(
      devices: devicesList.map((deviceJson) => Device.fromJson(deviceJson as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'devices': devices.map((device) => device.toJson()).toList(),
  };
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