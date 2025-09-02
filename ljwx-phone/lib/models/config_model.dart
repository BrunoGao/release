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
      customerId: json['customer_id']?.toString() ?? '',
      customerName: json['customer_name']?.toString() ?? '',
      healthData: HealthDataConfig.fromJson(json['health_data'] as Map<String, dynamic>? ?? {}),
      interfaceData: InterfaceData.fromJson(json['interface_data'] as Map<String, dynamic>? ?? {}),
      isSupportLicense: json['is_support_license'] as int? ?? 0,
      licenseKey: json['license_key'] as int? ?? 0,
      uploadMethod: json['upload_method']?.toString() ?? '',
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
      bloodOxygen: json['blood_oxygen']?.toString() ?? '',
      calorie: json['calorie']?.toString() ?? '',
      distance: json['distance']?.toString() ?? '',
      heartRate: json['heart_rate']?.toString() ?? '',
      location: json['location']?.toString() ?? '',
      sleep: json['sleep']?.toString() ?? '',
      step: json['step']?.toString() ?? '',
      stress: json['stress']?.toString() ?? '',
      temperature: json['temperature']?.toString() ?? '',
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
      fetchConfig: json['fetch_config']?.toString() ?? '',
      fetchMessage: json['fetch_message']?.toString() ?? '',
      uploadCommonEvent: json['upload_common_event']?.toString() ?? '',
      uploadDeviceInfo: json['upload_device_info']?.toString() ?? '',
      uploadHealthData: json['upload_health_data']?.toString() ?? '',
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