import 'dart:async';
import 'package:flutter/material.dart';

enum EventType {
  info,
  warning,
  error,
  success
}

class EventMessage {
  final String message;
  final EventType type;
  final Duration duration;
  
  EventMessage(this.message, this.type, {this.duration = const Duration(seconds: 3)});
}

class GlobalEvents {
  static final GlobalEvents _instance = GlobalEvents._internal();
  factory GlobalEvents() => _instance;
  GlobalEvents._internal();
  
  static GlobalEvents get i => _instance;
  
  // 事件流
  final _eventController = StreamController<EventMessage>.broadcast();
  Stream<EventMessage> get eventStream => _eventController.stream;
  
  // 显示服务未找到提示
  void showHealthServiceNotFound() {
    _eventController.add(
      EventMessage(
        '未找到健康服务(1887)，请确保手表端健康应用已打开',
        EventType.warning,
        duration: const Duration(seconds: 5)
      )
    );
  }
  
  // 显示普通信息
  void showInfo(String message) {
    _eventController.add(EventMessage(message, EventType.info));
  }
  
  // 显示警告
  void showWarning(String message) {
    _eventController.add(EventMessage(message, EventType.warning));
  }
  
  // 显示错误
  void showError(String message) {
    _eventController.add(EventMessage(message, EventType.error));
  }
  
  // 显示成功
  void showSuccess(String message) {
    _eventController.add(EventMessage(message, EventType.success));
  }
  
  // 释放资源
  void dispose() {
    _eventController.close();
  }
} 