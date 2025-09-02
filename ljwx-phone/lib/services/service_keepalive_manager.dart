import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'bluetooth_service.dart';
import 'api_service.dart';

/// 服务保活管理器 #服务保活核心
class ServiceKeepaliveManager {
  static final ServiceKeepaliveManager i = ServiceKeepaliveManager._();
  ServiceKeepaliveManager._();

  // 保活配置
  static const Duration bleHeartbeatInterval = Duration(seconds: 30); // 蓝牙心跳间隔
  static const Duration httpHeartbeatInterval = Duration(seconds: 60); // HTTP心跳间隔
  static const Duration serviceCheckInterval = Duration(seconds: 15); // 服务检查间隔
  static const int maxRetryCount = 3; // 最大重试次数
  static const Duration retryDelay = Duration(seconds: 5); // 重试延迟

  // 定时器
  Timer? _bleHeartbeatTimer;
  Timer? _httpHeartbeatTimer;
  Timer? _serviceCheckTimer;

  // 状态管理
  bool _isKeepaliveActive = false;
  int _bleRetryCount = 0;
  int _httpRetryCount = 0;
  DateTime? _lastBleHeartbeat;
  DateTime? _lastHttpHeartbeat;

  // 状态流
  final StreamController<Map<String, dynamic>> _statusController = StreamController.broadcast();
  Stream<Map<String, dynamic>> get serviceStatusStream => _statusController.stream;

  /// 启动服务保活 #启动保活
  void startKeepalive() {
    if (_isKeepaliveActive) return;
    
    _isKeepaliveActive = true;
    _bleRetryCount = 0;
    _httpRetryCount = 0;
    
    _startBleHeartbeat();
    _startHttpHeartbeat();
    _startServiceCheck();
    
    debugPrint('[保活] 🚀 启动服务保活管理器');
  }

  /// 停止服务保活 #停止保活
  void stopKeepalive() {
    _isKeepaliveActive = false;
    
    _bleHeartbeatTimer?.cancel();
    _httpHeartbeatTimer?.cancel();
    _serviceCheckTimer?.cancel();
    
    debugPrint('[保活] 🛑 停止服务保活管理器');
  }

  /// 启动蓝牙心跳 #蓝牙心跳
  void _startBleHeartbeat() {
    _bleHeartbeatTimer?.cancel();
    _bleHeartbeatTimer = Timer.periodic(bleHeartbeatInterval, (timer) async {
      await _performBleHeartbeat();
    });
    debugPrint('[保活] 💙 蓝牙心跳已启动，间隔: ${bleHeartbeatInterval.inSeconds}秒');
  }

  /// 启动HTTP心跳 #HTTP心跳
  void _startHttpHeartbeat() {
    _httpHeartbeatTimer?.cancel();
    _httpHeartbeatTimer = Timer.periodic(httpHeartbeatInterval, (timer) async {
      await _performHttpHeartbeat();
    });
    debugPrint('[保活] 🌐 HTTP心跳已启动，间隔: ${httpHeartbeatInterval.inSeconds}秒');
  }

  /// 启动服务检查 #服务检查
  void _startServiceCheck() {
    _serviceCheckTimer?.cancel();
    _serviceCheckTimer = Timer.periodic(serviceCheckInterval, (timer) {
      _updateServiceStatus();
    });
    debugPrint('[保活] 📊 服务状态检查已启动，间隔: ${serviceCheckInterval.inSeconds}秒');
  }

  /// 执行蓝牙心跳检查 #蓝牙心跳检查
  Future<void> _performBleHeartbeat() async {
    try {
      if (!_isKeepaliveActive) return;
      
      // 检查蓝牙连接状态
      bool connected = BleSvc.i.d?.isConnected ?? false;
      bool hasRecentData = BleSvc.i.lastDataTime != null && 
          DateTime.now().difference(BleSvc.i.lastDataTime!) < const Duration(minutes: 2);
      
      if (connected && hasRecentData) {
        _lastBleHeartbeat = DateTime.now();
        _bleRetryCount = 0;
        debugPrint('[保活] 💙 蓝牙服务正常');
      } else {
        debugPrint('[保活] ⚠️ 蓝牙服务异常，开始恢复');
        await _recoverBleService();
      }
    } catch (e) {
      debugPrint('[保活] ❌ 蓝牙心跳检查异常: $e');
    }
  }

  /// 执行HTTP心跳检查 #HTTP心跳检查
  Future<void> _performHttpHeartbeat() async {
    try {
      if (!_isKeepaliveActive) return;
      
      // 简单的网络连通性检查
      bool networkOk = await _checkNetworkConnectivity();
      
      if (networkOk) {
        _lastHttpHeartbeat = DateTime.now();
        _httpRetryCount = 0;
        debugPrint('[保活] 🌐 HTTP服务正常');
      } else {
        debugPrint('[保活] ⚠️ HTTP服务异常，开始恢复');
        await _recoverHttpService();
      }
    } catch (e) {
      debugPrint('[保活] ❌ HTTP心跳检查异常: $e');
    }
  }

  /// 恢复蓝牙服务 #蓝牙服务恢复
  Future<void> _recoverBleService() async {
    if (_bleRetryCount >= maxRetryCount) {
      debugPrint('[保活] 💙 蓝牙服务恢复达到最大重试次数');
      return;
    }
    
    _bleRetryCount++;
    debugPrint('[保活] 💙 蓝牙服务恢复尝试 $_bleRetryCount/$maxRetryCount');
    
    try {
      // 尝试智能重连
      await BleSvc.i.smartReconnectWithServiceDetection();
      
      // 等待重试延迟
      await Future.delayed(retryDelay);
      
      debugPrint('[保活] 💙 蓝牙服务恢复完成');
    } catch (e) {
      debugPrint('[保活] 💙 蓝牙服务恢复失败: $e');
      await Future.delayed(retryDelay);
    }
  }

  /// 恢复HTTP服务 #HTTP服务恢复
  Future<void> _recoverHttpService() async {
    if (_httpRetryCount >= maxRetryCount) {
      debugPrint('[保活] 🌐 HTTP服务恢复达到最大重试次数');
      return;
    }
    
    _httpRetryCount++;
    debugPrint('[保活] 🌐 HTTP服务恢复尝试 $_httpRetryCount/$maxRetryCount');
    
    try {
      // 重新初始化HTTP客户端
      ApiService.initHttpClient();
      
      // 等待重试延迟
      await Future.delayed(retryDelay);
      
      debugPrint('[保活] 🌐 HTTP服务恢复完成');
    } catch (e) {
      debugPrint('[保活] 🌐 HTTP服务恢复失败: $e');
      await Future.delayed(retryDelay);
    }
  }

  /// 检查网络连通性 #网络检查
  Future<bool> _checkNetworkConnectivity() async {
    try {
      final result = await InternetAddress.lookup('www.baidu.com')
          .timeout(const Duration(seconds: 5));
      return result.isNotEmpty && result[0].rawAddress.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  /// 更新服务状态 #状态更新
  void _updateServiceStatus() {
    final now = DateTime.now();
    final status = {
      'ble_alive': _lastBleHeartbeat != null && 
          now.difference(_lastBleHeartbeat!) < const Duration(minutes: 2),
      'http_alive': _lastHttpHeartbeat != null && 
          now.difference(_lastHttpHeartbeat!) < const Duration(minutes: 3),
      'last_ble_heartbeat': _lastBleHeartbeat?.toIso8601String(),
      'last_http_heartbeat': _lastHttpHeartbeat?.toIso8601String(),
      'ble_retry_count': _bleRetryCount,
      'http_retry_count': _httpRetryCount,
      'overall_health': _bleRetryCount < maxRetryCount && _httpRetryCount < maxRetryCount,
    };
    
    _statusController.add(status);
  }

  /// 获取服务状态 #获取状态
  Map<String, dynamic> getServiceStatus() {
    final now = DateTime.now();
    return {
      'ble_alive': _lastBleHeartbeat != null && 
          now.difference(_lastBleHeartbeat!) < const Duration(minutes: 2),
      'http_alive': _lastHttpHeartbeat != null && 
          now.difference(_lastHttpHeartbeat!) < const Duration(minutes: 3),
      'last_ble_heartbeat': _lastBleHeartbeat?.toIso8601String(),
      'last_http_heartbeat': _lastHttpHeartbeat?.toIso8601String(),
      'ble_retry_count': _bleRetryCount,
      'http_retry_count': _httpRetryCount,
      'overall_health': _bleRetryCount < maxRetryCount && _httpRetryCount < maxRetryCount,
      'is_active': _isKeepaliveActive,
    };
  }

  /// 强制服务恢复 #强制恢复
  Future<void> forceServiceRecovery() async {
    debugPrint('[保活] 🔧 强制服务恢复');
    
    // 重置重试计数
    _bleRetryCount = 0;
    _httpRetryCount = 0;
    
    // 并行恢复服务
    await Future.wait([
      _recoverBleService(),
      _recoverHttpService(),
    ]);
    
    debugPrint('[保活] ✅ 强制服务恢复完成');
  }

  /// 释放资源 #资源释放
  void dispose() {
    stopKeepalive();
    _statusController.close();
    debugPrint('[保活] 🗑️ 服务保活管理器已释放');
  }
} 