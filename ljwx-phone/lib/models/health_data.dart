import 'package:ljwx_health_new/models/health_model.dart' as health_model;

class HealthData {
  final Map<String, DepartmentHealthStats> departmentStats;
  final int deviceCount;
  final List<HealthRecord> healthData;
  final String? orgId;
  final HealthStatistics statistics;
  final int totalRecords;
  final String userId;

  HealthData({
    required this.departmentStats,
    required this.deviceCount,
    required this.healthData,
    this.orgId,
    required this.statistics,
    required this.totalRecords,
    required this.userId,
  });

  // Add conversion method to UI HealthData
  health_model.HealthData toUiHealthData() {
    final vitals = {
      'heartRate': statistics.avgHeartRate,
      'bloodOxygen': statistics.avgBloodOxygen,
      'temperature': statistics.avgTemperature,
      'pressureHigh': statistics.avgPressureHigh,
      'pressureLow': statistics.avgPressureLow,
      'step': statistics.avgStep,
      'distance': statistics.avgDistance,
      'calorie': statistics.avgCalorie
    };

    final trends = {
      'heartRate': healthData.map((e) => e.heartRate.toDouble()).toList(),
      'bloodOxygen': healthData.map((e) => e.bloodOxygen.toDouble()).toList(),
      'temperature': healthData.map((e) => double.tryParse(e.temperature) ?? 0.0).toList(),
      'step': healthData.map((e) => double.tryParse(e.step) ?? 0.0).toList(),
      'distance': healthData.map((e) => e.distance).toList(),
      'calorie': healthData.map((e) => e.calorie).toList(),
    };

    // 创建空的department stats来避免类型问题
    final Map<String, health_model.DepartmentHealthStats> emptyDeptStats = {};

    return health_model.HealthData(
      departmentStats: emptyDeptStats,
      deviceCount: deviceCount,
      healthData: healthData.map((e) => health_model.HealthDataRecord(
        id: e.deviceSn,
        timestamp: e.timestamp,
        heartRate: e.heartRate.toDouble(),
        bloodOxygen: e.bloodOxygen.toDouble(),
        temperature: double.tryParse(e.temperature) ?? 0.0,
        pressureHigh: e.pressureHigh.toDouble(),
        pressureLow: e.pressureLow.toDouble(),
        step: int.tryParse(e.step) ?? 0,
        distance: e.distance,
        calorie: e.calorie,
        latitude: double.tryParse(e.latitude) ?? 0.0,
        longitude: double.tryParse(e.longitude) ?? 0.0,
        altitude: e.altitude,
        stress: e.stress,
        exerciseDailyData: e.exerciseDailyData?.toString(),
        exerciseDailyWeekData: e.exerciseDailyWeekData?.toString(),
        scientificSleepData: e.scientificSleepData?.toString(),
        sleepData: e.sleepData?.toString(),
        workoutData: null,
        deptName: e.deptName,
        userName: e.userName,
      )).toList(),
      orgId: orgId ?? '',
      statistics: health_model.HealthStatistics(
        averageStats: health_model.AverageStats(
          avgBloodOxygen: statistics.avgBloodOxygen,
          avgCalorie: statistics.avgCalorie,
          avgDistance: statistics.avgDistance,
          avgHeartRate: statistics.avgHeartRate,
          avgStep: statistics.avgStep,
          avgTemperature: statistics.avgTemperature,
        ),
        devicesWithData: deviceCount,
        totalDevices: deviceCount,
      ),
      totalRecords: totalRecords,
      userId: userId,
      trends: trends,
      vitals: vitals,
      lastUpdate: DateTime.now().toString(),
    );
  }

  factory HealthData.fromJson(Map<String, dynamic> json) {
    try {
      // Parse department stats
      final Map<String, DepartmentHealthStats> departmentStats = {};
      if (json['departmentStats'] is Map) {
        (json['departmentStats'] as Map).forEach((key, value) {
          if (value is Map<String, dynamic>) {
            departmentStats[key.toString()] = DepartmentHealthStats.fromJson(value);
          }
        });
      }

      // Parse health data list
      final List<HealthRecord> healthData = [];
      if (json['healthData'] is List) {
        healthData.addAll((json['healthData'] as List).map((e) {
          if (e is Map<String, dynamic>) {
            return HealthRecord.fromJson(e);
          }
          return HealthRecord(
            altitude: 0.0,
            bloodOxygen: 0,
            calorie: 0.0,
            deptName: '',
            deviceSn: '',
            distance: 0.0,
            exerciseDailyData: null,
            exerciseDailyWeekData: null,
            heartRate: 0,
            latitude: '0.0',
            longitude: '0.0',
            pressureHigh: 0,
            pressureLow: 0,
            scientificSleepData: null,
            sleepData: null,
            step: '0',
            temperature: '0.0',
            timestamp: '',
            userName: '',
            stress: 0
          );
        }));
      }

      return HealthData(
        departmentStats: departmentStats,
        deviceCount: json['deviceCount'] ?? 0,
        healthData: healthData,
        orgId: json['orgId'],
        statistics: HealthStatistics.fromJson(json['statistics'] ?? {}),
        totalRecords: json['totalRecords'] ?? 0,
        userId: json['userId'] ?? '',
      );
    } catch (e, stackTrace) {
      print('Error parsing HealthData: $e');
      print('Stack trace: $stackTrace');
      rethrow;
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'departmentStats': departmentStats.map((key, value) => MapEntry(key, value.toJson())),
      'deviceCount': deviceCount,
      'healthData': healthData.map((e) => e.toJson()).toList(),
      'orgId': orgId,
      'statistics': statistics.toJson(),
      'totalRecords': totalRecords,
      'userId': userId,
    };
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

  DepartmentHealthStats({
    required this.avgBloodOxygen,
    required this.avgCalorie,
    required this.avgDistance,
    required this.avgHeartRate,
    required this.avgStep,
    required this.avgTemperature,
    required this.deviceCount,
    required this.devices,
  });

  factory DepartmentHealthStats.fromJson(Map<String, dynamic> json) {
    return DepartmentHealthStats(
      // API返回的是下划线字段名，需要同时支持两种命名方式
      avgBloodOxygen: (json['avg_blood_oxygen'] ?? json['avgBloodOxygen'] ?? 0.0).toDouble(),
      avgCalorie: (json['avg_calorie'] ?? json['avgCalorie'] ?? 0.0).toDouble(),
      avgDistance: (json['avg_distance'] ?? json['avgDistance'] ?? 0.0).toDouble(),
      avgHeartRate: (json['avg_heart_rate'] ?? json['avgHeartRate'] ?? 0.0).toDouble(),
      avgStep: (json['avg_step'] ?? json['avgStep'] ?? 0.0).toDouble(),
      avgTemperature: (json['avg_temperature'] ?? json['avgTemperature'] ?? 0.0).toDouble(),
      deviceCount: json['deviceCount'] ?? 0,
      devices: List<String>.from(json['devices'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'avgBloodOxygen': avgBloodOxygen,
      'avgCalorie': avgCalorie,
      'avgDistance': avgDistance,
      'avgHeartRate': avgHeartRate,
      'avgStep': avgStep,
      'avgTemperature': avgTemperature,
      'deviceCount': deviceCount,
      'devices': devices,
    };
  }
}

class HealthRecord {
  final double altitude;
  final int bloodOxygen;
  final double calorie;
  final String deptName;
  final String deviceSn;
  final double distance;
  final int stress;
  final dynamic exerciseDailyData;
  final dynamic exerciseDailyWeekData;
  final int heartRate;
  final String latitude;
  final String longitude;
  final int pressureHigh;
  final int pressureLow;
  final dynamic scientificSleepData;
  final dynamic sleepData;
  final String step;
  final String temperature;
  final String timestamp;
  final String userName;

  HealthRecord({
    required this.altitude,
    required this.bloodOxygen,
    required this.calorie,
    required this.deptName,
    required this.deviceSn,
    required this.distance,
    required this.stress,
    this.exerciseDailyData,
    this.exerciseDailyWeekData,
    required this.heartRate,
    required this.latitude,
    required this.longitude,
    required this.pressureHigh,
    required this.pressureLow,
    this.scientificSleepData,
    this.sleepData,
    required this.step,
    required this.temperature,
    required this.timestamp,
    required this.userName,
  });

  factory HealthRecord.fromJson(Map<String, dynamic> json) {
    return HealthRecord(
      altitude: (json['altitude'] ?? 0.0).toDouble(),
      // API返回的是下划线字段名，需要同时支持两种命名方式
      bloodOxygen: int.tryParse((json['blood_oxygen'] ?? json['bloodOxygen']).toString()) ?? 0,
      calorie: (json['calorie'] ?? 0.0).toDouble(),
      deptName: json['deptName'] ?? '',
      deviceSn: json['deviceSn'] ?? '',
      distance: (json['distance'] ?? 0.0).toDouble(),
      stress: int.tryParse((json['stress']).toString()) ?? 0,
      exerciseDailyData: json['exerciseDailyData'],
      exerciseDailyWeekData: json['exerciseDailyWeekData'],
      heartRate: int.tryParse((json['heart_rate'] ?? json['heartRate']).toString()) ?? 0,
      latitude: json['latitude']?.toString() ?? '0.0',
      longitude: json['longitude']?.toString() ?? '0.0',
      pressureHigh: int.tryParse((json['pressure_high'] ?? json['pressureHigh']).toString()) ?? 0,
      pressureLow: int.tryParse((json['pressure_low'] ?? json['pressureLow']).toString()) ?? 0,
      scientificSleepData: json['scientificSleepData'],
      sleepData: json['sleepData'],
      step: json['step']?.toString() ?? '0',
      temperature: json['temperature']?.toString() ?? '0.0',
      timestamp: json['timestamp'] ?? '',
      userName: json['userName'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'altitude': altitude,
      'bloodOxygen': bloodOxygen,
      'calorie': calorie,
      'deptName': deptName,
      'deviceSn': deviceSn,
      'distance': distance,
      'stress': stress,
      'exerciseDailyData': exerciseDailyData,
      'exerciseDailyWeekData': exerciseDailyWeekData,
      'heartRate': heartRate,
      'latitude': latitude,
      'longitude': longitude,
      'pressureHigh': pressureHigh,
      'pressureLow': pressureLow,
      'scientificSleepData': scientificSleepData,
      'sleepData': sleepData,
      'step': step,
      'temperature': temperature,
      'timestamp': timestamp,
      'userName': userName,
    };
  }
}

class HealthStatistics {
  final double avgHeartRate;
  final double avgBloodOxygen;
  final double avgTemperature;
  final double avgPressureHigh;
  final double avgPressureLow;
  final double avgStep;
  final double avgDistance;
  final double avgCalorie;
  final double avgStress;
  HealthStatistics({
    required this.avgHeartRate,
    required this.avgBloodOxygen,
    required this.avgTemperature,
    required this.avgPressureHigh,
    required this.avgPressureLow,
    required this.avgStep,
    required this.avgDistance,
    required this.avgCalorie,
    required this.avgStress,
  });

  factory HealthStatistics.fromJson(Map<String, dynamic> json) {
    return HealthStatistics(
      // API返回的是下划线字段名，需要同时支持两种命名方式
      avgHeartRate: (json['avg_heart_rate'] ?? json['avgHeartRate'] ?? 0.0).toDouble(),
      avgBloodOxygen: (json['avg_blood_oxygen'] ?? json['avgBloodOxygen'] ?? 0.0).toDouble(),
      avgTemperature: (json['avg_temperature'] ?? json['avgTemperature'] ?? 0.0).toDouble(),
      avgPressureHigh: (json['avg_pressure_high'] ?? json['avgPressureHigh'] ?? 0.0).toDouble(),
      avgPressureLow: (json['avg_pressure_low'] ?? json['avgPressureLow'] ?? 0.0).toDouble(),
      avgStep: (json['avg_step'] ?? json['avgStep'] ?? 0.0).toDouble(),
      avgDistance: (json['avg_distance'] ?? json['avgDistance'] ?? 0.0).toDouble(),
      avgCalorie: (json['avg_calorie'] ?? json['avgCalorie'] ?? 0.0).toDouble(),
      avgStress: (json['avg_stress'] ?? json['avgStress'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'avg_heart_rate': avgHeartRate,
      'avg_blood_oxygen': avgBloodOxygen,
      'avg_temperature': avgTemperature,
      'avg_pressure_high': avgPressureHigh,
      'avg_pressure_low': avgPressureLow,
      'avg_step': avgStep,
      'avg_distance': avgDistance,
      'avg_calorie': avgCalorie,
      'avg_stress': avgStress,
    };
  }
} 