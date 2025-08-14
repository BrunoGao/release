import 'dart:async';
import 'package:flutter/material.dart';
import 'package:ljwx_health_new/config/app_config.dart';

// 为了向后兼容，保留全局变量但从AppConfig获取值 #向后兼容全局变量
String get deviceSn => AppConfig.instance.deviceSn; // 全局设备序列号
String get globalDeviceSn => AppConfig.instance.deviceSn; // 全局设备序列号
String get customerName => AppConfig.instance.customerName; // 全局客户名称  
String get uploadMethod => AppConfig.instance.uploadMethod; // 上传方式：bluetooth或wifi
Map<String, dynamic> get systemConfig => AppConfig.instance.systemConfig; // 系统配置

// setter方法用于向后兼容 #向后兼容setter
set deviceSn(String value) => AppConfig.instance.setDeviceSn(value);
set globalDeviceSn(String value) => AppConfig.instance.setDeviceSn(value);
set customerName(String value) => AppConfig.instance.setCustomerName(value);
set uploadMethod(String value) => AppConfig.instance.setUploadMethod(value);
set systemConfig(Map<String, dynamic> value) => AppConfig.instance.setSystemConfig(value);

const String bleLogFile = '/storage/emulated/0/ble_log.txt'; // 安卓路径，iOS需适配 

class GlobalEvents { // 全局事件管理
  static final GlobalEvents i = GlobalEvents._(); // 单例
  GlobalEvents._();
  
  final _errors = StreamController<Map<String,String>>.broadcast(); // 错误事件流
  Stream<Map<String,String>> get errorStream => _errors.stream; // 提供错误事件流
  
  void addError(String title, String message) { // 添加错误
    _errors.add({'title': title, 'message': message});
    debugPrint('全局错误: $title - $message');
  }
  
  void dispose() { // 释放资源
    _errors.close();
  }
} 