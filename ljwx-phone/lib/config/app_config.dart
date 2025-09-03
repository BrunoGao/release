import 'package:flutter/foundation.dart';

/// 应用配置管理类 #统一配置管理
class AppConfig {
  // 私有构造函数，确保单例
  AppConfig._();
  static final AppConfig _instance = AppConfig._();
  static AppConfig get instance => _instance;

  // 服务器配置 #服务器地址配置
  static const String _defaultApiHost = '192.168.1.200'; // 使用主网络IP，模拟器和真机都可访问
  static const String _defaultApiPort = '5001'; // 默认API端口
  static const String _defaultAdminHost = '192.168.1.200'; // 默认管理端服务器地址
  static const String _defaultAdminPort = '3333'; // 默认管理端端口
  
  // 运行时配置变量
  String _apiHost = _defaultApiHost;
  String _apiPort = _defaultApiPort;
  String _adminHost = _defaultAdminHost;
  String _adminPort = _defaultAdminPort;
  bool _useHttps = false;

  // 应用配置 #应用基础配置
  String _deviceSn = ''; // 全局设备序列号
  String _customerName = '健康管理'; // 全局客户名称
  String _uploadMethod = 'bluetooth'; // 上传方式：bluetooth或wifi
  Map<String, dynamic> _systemConfig = {}; // 系统配置

  // Getters
  String get apiHost => _apiHost;
  String get apiPort => _apiPort;
  String get adminHost => _adminHost;
  String get adminPort => _adminPort;
  bool get useHttps => _useHttps;
  String get deviceSn => _deviceSn;
  String get customerName => _customerName;
  String get uploadMethod => _uploadMethod;
  Map<String, dynamic> get systemConfig => Map.from(_systemConfig);

  // 构建完整的URL #URL构建
  String get apiBaseUrl {
    final protocol = _useHttps ? 'https' : 'http';
    return '$protocol://$_apiHost:$_apiPort';
  }

  String get adminBaseUrl {
    final protocol = _useHttps ? 'https' : 'http';
    return '$protocol://$_adminHost:$_adminPort/';
  }

  // Setters #配置设置方法
  void setApiConfig(String host, String port, {bool useHttps = false}) {
    _apiHost = host.isNotEmpty ? host : _defaultApiHost;
    _apiPort = port.isNotEmpty ? port : _defaultApiPort;
    _useHttps = useHttps;
    debugPrint('API配置已更新: $apiBaseUrl');
  }

  void setAdminConfig(String host, String port) {
    _adminHost = host.isNotEmpty ? host : _defaultAdminHost;
    _adminPort = port.isNotEmpty ? port : _defaultAdminPort;
    debugPrint('管理端配置已更新: $adminBaseUrl');
  }

  void setDeviceSn(String sn) {
    _deviceSn = sn;
    debugPrint('设备序列号已更新: $_deviceSn');
  }

  void setCustomerName(String name) {
    _customerName = name.isNotEmpty ? name : '健康管理';
    debugPrint('客户名称已更新: $_customerName');
  }

  void setUploadMethod(String method) {
    _uploadMethod = ['bluetooth', 'wifi'].contains(method) ? method : 'bluetooth';
    debugPrint('上传方式已更新: $_uploadMethod');
  }

  void updateSystemConfig(Map<String, dynamic> config) {
    _systemConfig = Map<String, dynamic>.from(config);
    
    // 自动更新相关配置 #自动配置更新
    if (config.containsKey('customer_name')) {
      setCustomerName(config['customer_name'].toString());
    }
    if (config.containsKey('upload_method')) {
      setUploadMethod(config['upload_method'].toString());
    }
    
    debugPrint('系统配置已更新，共${_systemConfig.length}项配置');
  }

  // 设置系统配置的别名方法 #系统配置别名
  void setSystemConfig(Map<String, dynamic> config) {
    updateSystemConfig(config);
  }

  // 重置为默认配置 #重置配置
  void resetToDefaults() {
    _apiHost = _defaultApiHost;
    _apiPort = _defaultApiPort;
    _adminHost = _defaultAdminHost;
    _adminPort = _defaultAdminPort;
    _useHttps = false;
    _deviceSn = '';
    _customerName = '健康管理';
    _uploadMethod = 'bluetooth';
    _systemConfig.clear();
    debugPrint('配置已重置为默认值');
  }

  // 获取配置摘要 #配置信息摘要
  Map<String, dynamic> getConfigSummary() {
    return {
      'api_base_url': apiBaseUrl,
      'admin_base_url': adminBaseUrl,
      'device_sn': _deviceSn,
      'customer_name': _customerName,
      'upload_method': _uploadMethod,
      'use_https': _useHttps,
      'system_config_count': _systemConfig.length,
    };
  }

  // 日志文件配置 #日志配置
  static const String bleLogFile = '/storage/emulated/0/ble_log.txt'; // 安卓路径，iOS需适配

  // 常用API端点 #API端点配置
  String get phoneLoginUrl => '$apiBaseUrl/phone_login';
  String get personalInfoUrl => '$apiBaseUrl/phone_get_personal_info';
  String get healthDataConfigUrl => '$apiBaseUrl/fetch_health_data_config';
  String get uploadHealthDataUrl => '$apiBaseUrl/upload_health_data';
  String get uploadDeviceInfoUrl => '$apiBaseUrl/upload_device_info';
  String get uploadCommonEventUrl => '$apiBaseUrl/upload_common_event';
  String get uploadWatchLogUrl => '$apiBaseUrl/upload_watch_log';
  String get healthAnalysisUrl => '$apiBaseUrl/get_all_health_data_by_orgIdAndUserId_mobile';
  String get deviceMessagesUrl => '$apiBaseUrl/DeviceMessage/receive';
  String get resetPasswordUrl => '$apiBaseUrl/phone/reset_password';
  String get resetPasswordByPhoneUrl => '$apiBaseUrl/phone/reset_password_by_phone';
} 