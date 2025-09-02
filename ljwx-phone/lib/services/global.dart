import 'dart:async';
import 'package:flutter/material.dart';

String deviceSn=''; //全局设备序列号 
String globalDeviceSn = ''; //全局设备序列号
String customerName = '灵境万象健康管理'; //全局客户名称
String uploadMethod = 'bluetooth'; //上传方式：bluetooth或wifi
Map<String, dynamic> systemConfig = {}; //系统配置
const String bleLogFile = '/storage/emulated/0/ble_log.txt'; //安卓路径，iOS需适配 

class GlobalEvents { //全局事件管理
  static final GlobalEvents i = GlobalEvents._(); //单例
  GlobalEvents._();
  
  final _errors = StreamController<Map<String,String>>.broadcast(); //错误事件流
  Stream<Map<String,String>> get errorStream => _errors.stream; //提供错误事件流
  
  void addError(String title, String message) { //添加错误
    _errors.add({'title': title, 'message': message});
    debugPrint('全局错误: $title - $message');
  }
  
  void dispose() { //释放资源
    _errors.close();
  }
} 