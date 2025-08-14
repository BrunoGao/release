import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:flutter/foundation.dart';

class HealthDataRecord {
  final String id;
  final String timestamp;
  final double? heartRate;
  final double? bloodOxygen;
  final double? temperature;
  final double? pressureHigh;
  final double? pressureLow;
  final int? step;
  final double? distance;
  final double? calorie;
  final double? latitude;
  final double? longitude;
  final double? altitude;
  final int? stress;
  final String? exerciseDailyData;
  final String? exerciseDailyWeekData;
  final String? scientificSleepData;
  final String? sleepData;
  final String? workoutData;
  final String? deptName;
  final String? userName;
  
  HealthDataRecord({
    required this.id,
    required this.timestamp,
    this.heartRate,
    this.bloodOxygen,
    this.temperature,
    this.pressureHigh,
    this.pressureLow,
    this.step,
    this.distance,
    this.calorie,
    this.latitude,
    this.longitude,
    this.altitude,
    this.stress,
    this.exerciseDailyData,
    this.exerciseDailyWeekData,
    this.scientificSleepData,
    this.sleepData,
    this.workoutData,
    this.deptName,
    this.userName,
  });

  factory HealthDataRecord.fromJson(Map<String, dynamic> json) {
    return HealthDataRecord(
      id: json['deviceSn'] ?? '',
      timestamp: json['timestamp'] ?? DateTime.now().toString(),
      heartRate: _parseDouble(json['heartRate']),
      bloodOxygen: _parseDouble(json['bloodOxygen']),
      temperature: _parseDouble(json['temperature']),
      pressureHigh: _parseDouble(json['pressureHigh']),
      pressureLow: _parseDouble(json['pressureLow']),
      step: _parseInt(json['step']),
      distance: _parseDouble(json['distance']),
      calorie: _parseDouble(json['calorie']),
      latitude: _parseDouble(json['latitude']),
      longitude: _parseDouble(json['longitude']),
      altitude: _parseDouble(json['altitude']),
      stress: _parseInt(json['stress']),
      exerciseDailyData: json['exerciseDailyData']?.toString(),
      exerciseDailyWeekData: json['exerciseDailyWeekData']?.toString(),
      scientificSleepData: json['scientificSleepData']?.toString(),
      sleepData: json['sleepData']?.toString(),
      workoutData: json['workoutData']?.toString(),
      deptName: json['deptName'],
      userName: json['userName'],
    );
  }

  // 安全的类型转换方法
  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    return double.tryParse(value.toString());
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }

  Map<String, dynamic> toJson() {
    return {
      'deviceSn': id,
      'timestamp': timestamp,
      'heartRate': heartRate,
      'bloodOxygen': bloodOxygen,
      'temperature': temperature,
      'pressureHigh': pressureHigh,
      'pressureLow': pressureLow,
      'step': step,
      'distance': distance,
      'calorie': calorie,
      'latitude': latitude,
      'longitude': longitude,
      'altitude': altitude,
      'stress': stress,
      'exerciseDailyData': exerciseDailyData,
      'exerciseDailyWeekData': exerciseDailyWeekData,
      'scientificSleepData': scientificSleepData,
      'sleepData': sleepData,
      'workoutData': workoutData,
      'deptName': deptName,
      'userName': userName,
    };
  }
}

class UiHealthData {
  final String date;
  final String type;
  final double value;
  final String unit;

  UiHealthData({
    required this.date,
    required this.type,
    required this.value,
    required this.unit,
  });
}

class HealthData {
  final Map<String, DepartmentHealthStats> departmentStats;
  final int deviceCount;
  final List<HealthDataRecord> healthData;
  final String orgId;
  final HealthStatistics statistics;
  final int totalRecords;
  final String userId;
  final Map<String, List<double>> trends;
  final Map<String, dynamic> vitals;
  final String lastUpdate;
  
  // 缓存心率数据以显示完整趋势
  static final Map<String, List<double>> _cachedTrends = {
    'heartRate': [],
    'bloodOxygen': [],
    'temperature': [],
    'pressure': [],
    'stress': [],
  };

  HealthData({
    required this.departmentStats,
    required this.deviceCount,
    required this.healthData,
    required this.orgId,
    required this.statistics,
    required this.totalRecords,
    required this.userId,
    this.trends = const {},
    this.vitals = const {},
    this.lastUpdate = '',
  }) {
    // 将新数据添加到缓存中
    _addDataToCache();
  }

  // 添加数据到全局缓存
  void _addDataToCache() {
    if (healthData.isEmpty) return;
    
    // 处理心率数据
    if (trends.containsKey('heartRate')) {
      final newData = trends['heartRate'] ?? [];
      if (newData.isNotEmpty) {
        // 保持最多30个历史数据点
        _cachedTrends['heartRate'] = [
          ...newData,
          ..._cachedTrends['heartRate'] ?? []
        ].take(30).toList().cast<double>();
      }
    } else {
      // 从当前记录中提取数据并添加到缓存
      final heartRateData = healthData
          .where((e) => e.heartRate != null && e.heartRate! > 0)
          .map((e) => e.heartRate!)
          .toList();
          
      if (heartRateData.isNotEmpty) {
        _cachedTrends['heartRate'] = [
          ...heartRateData,
          ..._cachedTrends['heartRate'] ?? []
        ].take(30).toList().cast<double>();
      }
    }
    
    // 同样处理其他重要指标
    // 血氧
    if (trends.containsKey('bloodOxygen')) {
      final newData = trends['bloodOxygen'] ?? [];
      if (newData.isNotEmpty) {
        _cachedTrends['bloodOxygen'] = [
          ...newData,
          ..._cachedTrends['bloodOxygen'] ?? []
        ].take(30).toList().cast<double>();
      }
    }
    
    // 体温
    if (trends.containsKey('temperature')) {
      final newData = trends['temperature'] ?? [];
      if (newData.isNotEmpty) {
        _cachedTrends['temperature'] = [
          ...newData,
          ..._cachedTrends['temperature'] ?? []
        ].take(30).toList().cast<double>();
      }
    }
    
    // 压力
    final stressData = healthData
        .where((e) => e.stress != null && e.stress! > 0)
        .map((e) => e.stress!.toDouble())
        .toList();
        
    if (stressData.isNotEmpty) {
      _cachedTrends['stress'] = [
        ...stressData,
        ..._cachedTrends['stress'] ?? []
      ].take(30).toList().cast<double>();
    }
  }
  
  // 获取缓存的心率数据
  List<double> getCachedHeartRateData() {
    return _cachedTrends['heartRate'] ?? [];
  }
  
  // 获取缓存的其他指标数据
  List<double> getCachedTrendData(String key) {
    return _cachedTrends[key] ?? [];
  }

  factory HealthData.fromJson(Map<String, dynamic> json) {
    // 解析部门统计数据
    final Map<String, DepartmentHealthStats> departmentStats = {};
    final deptStatsJson = json['departmentStats'] as Map<String, dynamic>?;
    if (deptStatsJson != null) {
      deptStatsJson.forEach((key, value) {
        departmentStats[key] = DepartmentHealthStats.fromJson(value);
      });
    }

    // 解析健康数据列表
    final List<HealthDataRecord> healthDataList = [];
    final healthDataJson = json['healthData'] as List<dynamic>?;
    if (healthDataJson != null) {
      healthDataList.addAll(
        healthDataJson.map((e) => HealthDataRecord.fromJson(e as Map<String, dynamic>))
      );
    }

    // 生成趋势数据
    final Map<String, List<double>> trends = {};
    if (healthDataList.isNotEmpty) {
      trends['heartRate'] = healthDataList
          .where((e) => e.heartRate != null)
          .map((e) => e.heartRate!)
          .toList();
      trends['bloodOxygen'] = healthDataList
          .where((e) => e.bloodOxygen != null)
          .map((e) => e.bloodOxygen!)
          .toList();
      trends['temperature'] = healthDataList
          .where((e) => e.temperature != null)
          .map((e) => e.temperature!)
          .toList();
    }

    // 生成当前健康指标数据
    final Map<String, dynamic> vitals = {};
    if (healthDataList.isNotEmpty) {
      final latest = healthDataList.first;
      vitals['heartRate'] = latest.heartRate;
      vitals['bloodOxygen'] = latest.bloodOxygen;
      vitals['temperature'] = latest.temperature;
      vitals['pressureHigh'] = latest.pressureHigh;
      vitals['pressureLow'] = latest.pressureLow;
      vitals['step'] = latest.step;
      vitals['distance'] = latest.distance;
      vitals['calorie'] = latest.calorie;
      vitals['stress'] = latest.stress;
    }

    return HealthData(
      departmentStats: departmentStats,
      deviceCount: json['deviceCount'] ?? 0,
      healthData: healthDataList,
      orgId: json['orgId']?.toString() ?? '',
      statistics: HealthStatistics.fromJson(json['statistics'] ?? {}),
      totalRecords: json['totalRecords'] ?? 0,
      userId: json['userId']?.toString() ?? '',
      trends: trends,
      vitals: vitals,
      lastUpdate: DateTime.now().toString(),
    );
  }

  Map<String, dynamic> toJson() => {
    'departmentStats': departmentStats.map((key, value) => MapEntry(key, value.toJson())),
    'deviceCount': deviceCount,
    'healthData': healthData.map((e) => e.toJson()).toList(),
    'orgId': orgId,
    'statistics': statistics.toJson(),
    'totalRecords': totalRecords,
    'userId': userId,
    'trends': trends,
    'vitals': vitals,
    'lastUpdate': lastUpdate,
  };

  UiHealthData toUiHealthData() {
    final latestRecord = healthData.isNotEmpty ? healthData.first : null;
    return UiHealthData(
      date: latestRecord?.timestamp ?? DateTime.now().toString(),
      type: 'latest',
      value: latestRecord?.heartRate?.toDouble() ?? 0.0,
      unit: 'bpm',
    );
  }
}

class DepartmentHealthStats {
  final double avgBloodOxygen;
  final double avgCalorie;
  final double avgDistance;
  final double avgHeartRate;
  final double avgStep;
  final double avgTemperature;
  final int deviceCount;
  final List<String> devices;
  final double avgStress;
  DepartmentHealthStats({
    required this.avgBloodOxygen,
    required this.avgCalorie,
    required this.avgDistance,
    required this.avgHeartRate,
    required this.avgStep,
    required this.avgTemperature,
    required this.deviceCount,
    required this.devices,
    required this.avgStress,
  });

  factory DepartmentHealthStats.fromJson(Map<String, dynamic> json) {
    return DepartmentHealthStats(
      avgBloodOxygen: _parseDouble(json['avgBloodOxygen']) ?? 0.0,
      avgCalorie: _parseDouble(json['avgCalorie']) ?? 0.0,
      avgDistance: _parseDouble(json['avgDistance']) ?? 0.0,
      avgHeartRate: _parseDouble(json['avgHeartRate']) ?? 0.0,
      avgStep: _parseDouble(json['avgStep']) ?? 0.0,
      avgTemperature: _parseDouble(json['avgTemperature']) ?? 0.0,
      deviceCount: json['deviceCount'] ?? 0,
      devices: List<String>.from(json['devices'] ?? []),
      avgStress: _parseDouble(json['avgStress']) ?? 0.0,
    );
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    return double.tryParse(value.toString()) ?? 0.0;
  }

  Map<String, dynamic> toJson() => {
    'avgBloodOxygen': avgBloodOxygen,
    'avgCalorie': avgCalorie,
    'avgDistance': avgDistance,
    'avgHeartRate': avgHeartRate,
    'avgStep': avgStep,
    'avgTemperature': avgTemperature,
    'deviceCount': deviceCount,
    'devices': devices,
    'avgStress': avgStress,
  };
}

class HealthRecord {
  final String deviceSn;
  final String timestamp;
  final double? heartRate;
  final double? bloodOxygen;
  final double? temperature;
  final double? pressureHigh;
  final double? pressureLow;
  final int? step;
  final double? distance;
  final double? calorie;
  final String? latitude;
  final String? longitude;
  final double? altitude;
  final String deptName;
  final String userName;
  final dynamic exerciseDailyData;
  final dynamic exerciseDailyWeekData;
  final dynamic scientificSleepData;
  final dynamic sleepData;
  final int stress;
  HealthRecord({
    required this.deviceSn,
    required this.timestamp,
    this.heartRate,
    this.bloodOxygen,
    this.temperature,
    this.pressureHigh,
    this.pressureLow,
    this.step,
    this.distance,
    this.calorie,
    this.latitude,
    this.longitude,
    this.altitude,
    required this.deptName,
    required this.userName,
    this.exerciseDailyData,
    this.exerciseDailyWeekData,
    this.scientificSleepData,
    this.sleepData,
    required this.stress,
  });

  factory HealthRecord.fromJson(Map<String, dynamic> json) {
    print('Parsing HealthRecord from JSON: $json'); // 添加调试日志
    
    return HealthRecord(
      deviceSn: json['deviceSn']?.toString() ?? '',
      timestamp: json['timestamp']?.toString() ?? DateTime.now().toString(),
      heartRate: _parseInt(json['heartRate'])?.toDouble(),
      bloodOxygen: _parseInt(json['bloodOxygen'])?.toDouble(),
      temperature: _parseDouble(json['temperature']),
      pressureHigh: _parseInt(json['pressureHigh'])?.toDouble(),
      pressureLow: _parseInt(json['pressureLow'])?.toDouble(),
      step: _parseInt(json['step']),
      distance: _parseDouble(json['distance']),
      calorie: _parseDouble(json['calorie']),
      latitude: json['latitude']?.toString(),
      longitude: json['longitude']?.toString(),
      altitude: _parseDouble(json['altitude']),
      deptName: json['deptName']?.toString() ?? '',
      userName: json['userName']?.toString() ?? '',
      exerciseDailyData: json['exerciseDailyData'],
      exerciseDailyWeekData: json['exerciseDailyWeekData'],
      scientificSleepData: json['scientificSleepData'],
      sleepData: json['sleepData'],
      stress: json['stress']?.toInt() ?? 0,
    );
  }

  static double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    return double.tryParse(value.toString());
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }

  Map<String, dynamic> toJson() => {
    'deviceSn': deviceSn,
    'timestamp': timestamp,
    'heartRate': heartRate,
    'bloodOxygen': bloodOxygen,
    'temperature': temperature,
    'pressureHigh': pressureHigh,
    'pressureLow': pressureLow,
    'step': step,
    'distance': distance,
    'calorie': calorie,
    'latitude': latitude,
    'longitude': longitude,
    'altitude': altitude,
    'deptName': deptName,
    'userName': userName,
    'exerciseDailyData': exerciseDailyData,
    'exerciseDailyWeekData': exerciseDailyWeekData,
    'scientificSleepData': scientificSleepData,
    'sleepData': sleepData,
    'stress': stress,
  };
}

class HealthStatistics {
  final AverageStats averageStats;
  final int devicesWithData;
  final int totalDevices;

  HealthStatistics({
    required this.averageStats,
    required this.devicesWithData,
    required this.totalDevices,
  });

  factory HealthStatistics.fromJson(Map<String, dynamic> json) {
    return HealthStatistics(
      averageStats: AverageStats.fromJson(json['averageStats'] ?? {}),
      devicesWithData: json['devicesWithData'] ?? 0,
      totalDevices: json['totalDevices'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'averageStats': averageStats.toJson(),
    'devicesWithData': devicesWithData,
    'totalDevices': totalDevices,
  };
}

class AverageStats {
  final double avgBloodOxygen;
  final double avgCalorie;
  final double avgDistance;
  final double avgHeartRate;
  final double avgStep;
  final double avgTemperature;

  AverageStats({
    required this.avgBloodOxygen,
    required this.avgCalorie,
    required this.avgDistance,
    required this.avgHeartRate,
    required this.avgStep,
    required this.avgTemperature,
  });

  factory AverageStats.fromJson(Map<String, dynamic> json) {
    return AverageStats(
      avgBloodOxygen: _parseDouble(json['avgBloodOxygen']) ?? 0.0,
      avgCalorie: _parseDouble(json['avgCalorie']) ?? 0.0,
      avgDistance: _parseDouble(json['avgDistance']) ?? 0.0,
      avgHeartRate: _parseDouble(json['avgHeartRate']) ?? 0.0,
      avgStep: _parseDouble(json['avgStep']) ?? 0.0,
      avgTemperature: _parseDouble(json['avgTemperature']) ?? 0.0,
    );
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    return double.tryParse(value.toString()) ?? 0.0;
  }

  Map<String, dynamic> toJson() => {
    'avgBloodOxygen': avgBloodOxygen,
    'avgCalorie': avgCalorie,
    'avgDistance': avgDistance,
    'avgHeartRate': avgHeartRate,
    'avgStep': avgStep,
    'avgTemperature': avgTemperature,
  };
} 