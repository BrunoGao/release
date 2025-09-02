import 'package:ljwx_health_new/models/device_model.dart' as ui;

class DeviceInfo {
  final int departmentCount;
  final Map<String, DepartmentDeviceDetails> departmentDetails;
  final Map<String, int> departmentDeviceCount;
  final Map<String, int> deviceChargingCount;
  final Map<String, int> deviceStatusCount;
  final Map<String, int> deviceSystemVersionCount;
  final Map<String, int> deviceWearableCount;
  final List<Device> devices;
  final DeviceStatistics statistics;
  final int totalDevices;

  DeviceInfo({
    required this.departmentCount,
    required this.departmentDetails,
    required this.departmentDeviceCount,
    required this.deviceChargingCount,
    required this.deviceStatusCount,
    required this.deviceSystemVersionCount,
    required this.deviceWearableCount,
    required this.devices,
    required this.statistics,
    required this.totalDevices,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    try {
      // Parse department details
      final Map<String, DepartmentDeviceDetails> departmentDetails = {};
      if (json['departmentDetails'] is Map) {
        (json['departmentDetails'] as Map).forEach((key, value) {
          if (value is Map<String, dynamic>) {
            departmentDetails[key.toString()] = DepartmentDeviceDetails.fromJson(value);
          }
        });
      }

      // Parse devices list
      final List<Device> devices = [];
      if (json['devices'] is List) {
        devices.addAll((json['devices'] as List).map((e) {
          if (e is Map<String, dynamic>) {
            return Device.fromJson(e);
          }
          return Device(
            bluetoothAddress: '',
            chargingStatus: '',
            createTime: null,
            departmentName: '',
            id: 0,
            isDeleted: false,
            serialNumber: '',
            status: '',
            systemSoftwareVersion: '',
            updateTime: '',
            userName: '',
            wearableStatus: '',
          );
        }));
      }

      return DeviceInfo(
        departmentCount: json['departmentCount'] ?? 0,
        departmentDetails: departmentDetails,
        departmentDeviceCount: Map<String, int>.from(json['departmentDeviceCount'] ?? {}),
        deviceChargingCount: Map<String, int>.from(json['deviceChargingCount'] ?? {}),
        deviceStatusCount: Map<String, int>.from(json['deviceStatusCount'] ?? {}),
        deviceSystemVersionCount: Map<String, int>.from(json['deviceSystemVersionCount'] ?? {}),
        deviceWearableCount: Map<String, int>.from(json['deviceWearableCount'] ?? {}),
        devices: devices,
        statistics: DeviceStatistics.fromJson(json['statistics'] ?? {}),
        totalDevices: json['totalDevices'] ?? 0,
      );
    } catch (e, stackTrace) {
      print('Error parsing DeviceInfo: $e');
      print('Stack trace: $stackTrace');
      rethrow;
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'departmentCount': departmentCount,
      'departmentDetails': departmentDetails.map((key, value) => MapEntry(key, value.toJson())),
      'departmentDeviceCount': departmentDeviceCount,
      'deviceChargingCount': deviceChargingCount,
      'deviceStatusCount': deviceStatusCount,
      'deviceSystemVersionCount': deviceSystemVersionCount,
      'deviceWearableCount': deviceWearableCount,
      'devices': devices.map((e) => e.toJson()).toList(),
      'statistics': statistics.toJson(),
      'totalDevices': totalDevices,
    };
  }
}

class DepartmentDeviceDetails {
  final Map<String, int> chargingStatus;
  final Map<String, int> status;
  final Map<String, int> systemVersions;
  final int total;
  final int userCount;
  final Map<String, int> wearableStatus;

  DepartmentDeviceDetails({
    required this.chargingStatus,
    required this.status,
    required this.systemVersions,
    required this.total,
    required this.userCount,
    required this.wearableStatus,
  });

  factory DepartmentDeviceDetails.fromJson(Map<String, dynamic> json) {
    return DepartmentDeviceDetails(
      chargingStatus: Map<String, int>.from(json['charging_status'] ?? {}),
      status: Map<String, int>.from(json['status'] ?? {}),
      systemVersions: Map<String, int>.from(json['system_versions'] ?? {}),
      total: json['total'] ?? 0,
      userCount: json['user_count'] ?? 0,
      wearableStatus: Map<String, int>.from(json['wearable_status'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'charging_status': chargingStatus,
      'status': status,
      'system_versions': systemVersions,
      'total': total,
      'user_count': userCount,
      'wearable_status': wearableStatus,
    };
  }
}

class Device {
  final String bluetoothAddress;
  final String chargingStatus;
  final String? createTime;
  final String departmentName;
  final int id;
  final bool isDeleted;
  final String serialNumber;
  final String status;
  final String systemSoftwareVersion;
  final String updateTime;
  final String userName;
  final String wearableStatus;

  Device({
    required this.bluetoothAddress,
    required this.chargingStatus,
    this.createTime,
    required this.departmentName,
    required this.id,
    required this.isDeleted,
    required this.serialNumber,
    required this.status,
    required this.systemSoftwareVersion,
    required this.updateTime,
    required this.userName,
    required this.wearableStatus,
  });



  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      bluetoothAddress: json['bluetooth_address'] ?? '',
      chargingStatus: json['charging_status'] ?? '',
      createTime: json['create_time'],
      departmentName: json['department_name'] ?? '',
      id: json['id'] ?? 0,
      isDeleted: json['is_deleted'] ?? false,
      serialNumber: json['serial_number'] ?? '',
      status: json['status'] ?? '',
      systemSoftwareVersion: json['system_software_version'] ?? '',
      updateTime: json['update_time'] ?? '',
      userName: json['user_name'] ?? '',
      wearableStatus: json['wearable_status'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'bluetooth_address': bluetoothAddress,
      'charging_status': chargingStatus,
      'create_time': createTime,
      'department_name': departmentName,
      'id': id,
      'is_deleted': isDeleted,
      'serial_number': serialNumber,
      'status': status,
      'system_software_version': systemSoftwareVersion,
      'update_time': updateTime,
      'user_name': userName,
      'wearable_status': wearableStatus,
    };
  }
}

class DeviceStatistics {
  final Map<String, int> byChargingStatus;
  final Map<String, int> byDepartment;
  final Map<String, int> byStatus;
  final Map<String, int> bySystemVersion;
  final Map<String, int> byWearableStatus;
  final Map<String, DepartmentDeviceDetails> departmentDetails;
  final int totalDepartments;
  final int totalDevices;

  DeviceStatistics({
    required this.byChargingStatus,
    required this.byDepartment,
    required this.byStatus,
    required this.bySystemVersion,
    required this.byWearableStatus,
    required this.departmentDetails,
    required this.totalDepartments,
    required this.totalDevices,
  });

  factory DeviceStatistics.fromJson(Map<String, dynamic> json) {
    // Parse department details
    final Map<String, DepartmentDeviceDetails> departmentDetails = {};
    if (json['department_details'] is Map) {
      (json['department_details'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          departmentDetails[key.toString()] = DepartmentDeviceDetails.fromJson(value);
        }
      });
    }

    return DeviceStatistics(
      byChargingStatus: Map<String, int>.from(json['by_charging_status'] ?? {}),
      byDepartment: Map<String, int>.from(json['by_department'] ?? {}),
      byStatus: Map<String, int>.from(json['by_status'] ?? {}),
      bySystemVersion: Map<String, int>.from(json['by_system_version'] ?? {}),
      byWearableStatus: Map<String, int>.from(json['by_wearable_status'] ?? {}),
      departmentDetails: departmentDetails,
      totalDepartments: json['total_departments'] ?? 0,
      totalDevices: json['total_devices'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'by_charging_status': byChargingStatus,
      'by_department': byDepartment,
      'by_status': byStatus,
      'by_system_version': bySystemVersion,
      'by_wearable_status': byWearableStatus,
      'department_details': departmentDetails.map((key, value) => MapEntry(key, value.toJson())),
      'total_departments': totalDepartments,
      'total_devices': totalDevices,
    };
  }
} 