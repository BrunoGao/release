import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// BLE协议配置管理器 #协议配置管理
class BleProtocolConfig {
  static final BleProtocolConfig i = BleProtocolConfig._();
  BleProtocolConfig._();
  
  // 配置键名
  static const String _KEY_USE_BINARY = 'ble_use_binary_protocol';
  static const String _KEY_PROTOCOL_VERSION = 'ble_protocol_version';
  static const String _KEY_ENABLE_COMPRESSION = 'ble_enable_compression';
  static const String _KEY_MAX_PACKET_SIZE = 'ble_max_packet_size';
  
  // 默认配置(v1.2)
  bool _useBinaryProtocol = true;
  int _protocolVersion = 1; // v1.2协议版本保持为1(内部版本)
  bool _enableCompression = false;
  int _maxPacketSize = 512;
  
  // 配置变更通知
  final List<void Function(BleProtocolConfig)> _listeners = [];
  
  /// 初始化配置 #初始化配置
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    
    _useBinaryProtocol = prefs.getBool(_KEY_USE_BINARY) ?? true;
    _protocolVersion = prefs.getInt(_KEY_PROTOCOL_VERSION) ?? 1;
    _enableCompression = prefs.getBool(_KEY_ENABLE_COMPRESSION) ?? false;
    _maxPacketSize = prefs.getInt(_KEY_MAX_PACKET_SIZE) ?? 512;
  }
  
  /// 启用/禁用二进制协议 #启用二进制协议
  Future<void> enableBinaryProtocol(bool enable) async {
    if (_useBinaryProtocol == enable) return;
    
    _useBinaryProtocol = enable;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_KEY_USE_BINARY, enable);
    
    _notifyListeners();
  }
  
  /// 设置协议版本 #设置协议版本
  Future<void> setProtocolVersion(int version) async {
    if (_protocolVersion == version) return;
    
    _protocolVersion = version;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_KEY_PROTOCOL_VERSION, version);
    
    _notifyListeners();
  }
  
  /// 启用/禁用压缩 #启用压缩
  Future<void> setCompressionEnabled(bool enable) async {
    if (_enableCompression == enable) return;
    
    _enableCompression = enable;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_KEY_ENABLE_COMPRESSION, enable);
    
    _notifyListeners();
  }
  
  /// 设置最大数据包大小 #设置最大包大小
  Future<void> setMaxPacketSize(int size) async {
    if (_maxPacketSize == size) return;
    
    _maxPacketSize = size;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_KEY_MAX_PACKET_SIZE, size);
    
    _notifyListeners();
  }
  
  /// 添加配置变更监听器 #添加监听器
  void addListener(void Function(BleProtocolConfig) listener) {
    _listeners.add(listener);
  }
  
  /// 移除配置变更监听器 #移除监听器
  void removeListener(void Function(BleProtocolConfig) listener) {
    _listeners.remove(listener);
  }
  
  /// 通知监听器 #通知监听器
  void _notifyListeners() {
    for (var listener in _listeners) {
      try {
        listener(this);
      } catch (e) {
        // 忽略监听器错误
      }
    }
  }
  
  /// 重置为默认配置 #重置配置
  Future<void> resetToDefaults() async {
    await enableBinaryProtocol(true);
    await setProtocolVersion(1);
    await setCompressionEnabled(false);
    await setMaxPacketSize(512);
  }
  
  /// 导出配置为JSON #导出配置
  Map<String, dynamic> toJson() {
    return {
      'useBinaryProtocol': _useBinaryProtocol,
      'protocolVersion': _protocolVersion,
      'enableCompression': _enableCompression,
      'maxPacketSize': _maxPacketSize,
    };
  }
  
  /// 从JSON导入配置 #导入配置
  Future<void> fromJson(Map<String, dynamic> json) async {
    if (json.containsKey('useBinaryProtocol')) {
      await enableBinaryProtocol(json['useBinaryProtocol'] ?? true);
    }
    if (json.containsKey('protocolVersion')) {
      await setProtocolVersion(json['protocolVersion'] ?? 1);
    }
    if (json.containsKey('enableCompression')) {
      await setCompressionEnabled(json['enableCompression'] ?? false);
    }
    if (json.containsKey('maxPacketSize')) {
      await setMaxPacketSize(json['maxPacketSize'] ?? 512);
    }
  }
  
  // Getters
  bool get useBinaryProtocol => _useBinaryProtocol;
  int get protocolVersion => _protocolVersion;
  bool get enableCompression => _enableCompression;
  int get maxPacketSize => _maxPacketSize;
} 