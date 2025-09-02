import 'package:flutter/foundation.dart';
import 'package:ljwx_health_new/models/alert_model.dart' as alert_model;
import 'package:ljwx_health_new/models/config_model.dart' as config_model;
import 'package:ljwx_health_new/models/device_model.dart' as device_model;
import 'package:ljwx_health_new/models/health_model.dart' as health_model;
import 'package:ljwx_health_new/models/user_model.dart' as user_model;
import 'package:ljwx_health_new/models/message_model.dart' as message_model;

class PersonalData {
  final user_model.UserInfo? userInfo;
  final device_model.DeviceInfo? deviceInfo;
  final alert_model.AlertInfo alertInfo;
  final health_model.HealthData? healthData;
  final config_model.ConfigInfo? configInfo;
  final message_model.MessageInfo messageInfo;

  PersonalData({
    this.userInfo,
    this.deviceInfo,
    required this.alertInfo,
    this.healthData,
    this.configInfo,
    required this.messageInfo,
  });

  factory PersonalData.fromJson(Map<String, dynamic> json) {
    debugPrint('Creating PersonalData from JSON');
    final data = json['data'] ?? {};
    debugPrint('Data field extracted: ${data.keys}');
    
    try {
      // 逐步解析每个模块，添加详细调试信息
      debugPrint('Parsing user_info...');
      final userInfo = data['user_info']?['data'] != null 
          ? user_model.UserInfo.fromJson(Map<String, dynamic>.from(data['user_info']['data'])) 
          : null;
      debugPrint('User info parsed: ${userInfo != null}');
      
      debugPrint('Parsing device_info...');
      final deviceInfo = data['device_info']?['data'] != null 
          ? device_model.DeviceInfo.fromJson(Map<String, dynamic>.from(data['device_info']['data'])) 
          : null;
      debugPrint('Device info parsed: ${deviceInfo != null}');
      
      debugPrint('Parsing alert_info...');
      debugPrint('Alert info data exists: ${data['alert_info']?['data'] != null}');
      if (data['alert_info']?['data'] != null) {
        debugPrint('Alert info data: ${data['alert_info']['data']}');
      }
      final alertInfo = data['alert_info']?['data'] != null 
          ? alert_model.AlertInfo.fromJson(Map<String, dynamic>.from(data['alert_info']['data'])) 
          : alert_model.AlertInfo.empty();
      debugPrint('Alert info parsed: ${alertInfo.alerts.length} alerts');
      
      debugPrint('Parsing health_data...');
      final healthData = data['health_data']?['data'] != null 
          ? health_model.HealthData.fromJson(Map<String, dynamic>.from(data['health_data']['data'])) 
          : null;
      debugPrint('Health data parsed: ${healthData != null}');
      
      debugPrint('Parsing config_info...');
      final configInfo = data['config_info']?['data'] != null 
          ? config_model.ConfigInfo.fromJson(Map<String, dynamic>.from(data['config_info']['data'])) 
          : null;
      debugPrint('Config info parsed: ${configInfo != null}');
      
      debugPrint('Parsing message_info...');
      final messageInfo = data['message_info']?['data'] != null 
          ? message_model.MessageInfo.fromJson(Map<String, dynamic>.from(data['message_info']['data'])) 
          : message_model.MessageInfo.empty();
      debugPrint('Message info parsed: ${messageInfo.messages.length} messages');
      
      return PersonalData(
        userInfo: userInfo,
        deviceInfo: deviceInfo,
        alertInfo: alertInfo,
        healthData: healthData,
        configInfo: configInfo,
        messageInfo: messageInfo,
      );
    } catch (e, stackTrace) {
      debugPrint('Error in PersonalData.fromJson: ${e}');
      debugPrint('Stack trace: ${stackTrace}');
      debugPrint('Raw JSON data: ${json}');
      return PersonalData(
        alertInfo: alert_model.AlertInfo.empty(),
        messageInfo: message_model.MessageInfo.empty(),
      );
    }
  }

  Map<String, dynamic> toJson() => {
    'user_info': userInfo?.toJson(),
    'device_info': deviceInfo?.toJson(),
    'alert_info': alertInfo.toJson(),
    'health_data': healthData?.toJson(),
    'config_info': configInfo?.toJson(),
    'message_info': messageInfo.toJson(),
  };
} 