import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'dart:async';
import 'dart:convert';
import '../services/bluetooth_service.dart'; // 导入BleSvc

class BleProvider with ChangeNotifier {
  static final BleProvider _instance = BleProvider._internal();
  factory BleProvider() => _instance;
  BleProvider._internal();

  // 添加全局导航键，用于路由使用
  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  final FlutterBluePlus flutterBlue = FlutterBluePlus();
  BluetoothDevice? _connectedDevice;
  bool _isConnected = false;
  List<ScanResult> _scanResults = [];
  bool isScanning = false;
  String? targetBluetoothAddress;
  List<String> _bleLogs = [];
  StreamSubscription? _connectionSubscription;
  StreamSubscription? _dataSubscription;
  Map<String, dynamic> _lastHealthData = {};
  
  // 分包处理相关变量
  final Map<String, Set<int>> _processedPackets = {}; // 已处理的分包索引
  final Map<String, Map<int, String>> _packetBuffers = {}; // 分包缓冲区
  int _packetTimeout = 10; // 分包超时时间(秒)
  final Map<String, DateTime> _packetTimestamps = {}; // 分包接收时间戳

  BluetoothDevice? get connectedDevice => _connectedDevice;
  bool get isConnected => _isConnected;
  List<ScanResult> get scanResults => _scanResults;
  List<String> get bleLogs => _bleLogs;
  Map<String, dynamic> get lastHealthData => _lastHealthData;

  void _addLog(String message) {
    _bleLogs.add('${DateTime.now().toString().substring(11, 19)}: $message');
    if (_bleLogs.length > 100) _bleLogs.removeAt(0);
    notifyListeners();
  }

  // 清理过期分包缓存
  void _cleanupStalePackets() {
    final now = DateTime.now();
    final stalePacketIds = _packetTimestamps.entries
        .where((entry) => now.difference(entry.value).inSeconds > _packetTimeout)
        .map((entry) => entry.key)
        .toList();
    
    for (final packetId in stalePacketIds) {
      _processedPackets.remove(packetId);
      _packetBuffers.remove(packetId);
      _packetTimestamps.remove(packetId);
      _addLog('清理过期分包: $packetId');
    }
  }

  Future<bool> isBluetoothEnabled() async {
    try {
      return await FlutterBluePlus.isOn;
    } catch (e) {
      _addLog('检查蓝牙状态失败: $e');
      return false;
    }
  }

  Future<List<ScanResult>> startScan() async {
    try {
      await stopScan();
      _addLog('开始扫描蓝牙设备');
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 4));
      
      FlutterBluePlus.scanResults.listen((results) {
        _scanResults = results;
        notifyListeners();
      });

      return _scanResults;
    } catch (e) {
      _addLog('扫描失败: $e');
      return [];
    }
  }

  Future<void> stopScan() async {
    try {
      await FlutterBluePlus.stopScan();
      _addLog('停止扫描');
    } catch (e) {
      _addLog('停止扫描失败: $e');
    }
  }

  Future<void> connectToDevice(BluetoothDevice device) async {
    try {
      await disconnect();
      _addLog('正在连接设备: ${device.name}');
      await BleSvc.i.conn(device.remoteId.toString());
      _connectedDevice = device;
      _isConnected = true;
      
      // 连接成功后清空分包缓存
      _processedPackets.clear();
      _packetBuffers.clear();
      _packetTimestamps.clear();
      
      notifyListeners();
    } catch (e) {
      _addLog('连接设备失败: $e');
      rethrow;
    }
  }

  Future<void> disconnect() async {
    try {
      if (_connectedDevice != null) {
        await _connectedDevice!.disconnect();
        _connectedDevice = null;
        _isConnected = false;
        _addLog('已断开设备连接');
        
        // 断开连接时清空分包缓存
        _processedPackets.clear();
        _packetBuffers.clear();
        _packetTimestamps.clear();
        
        notifyListeners();
      }
    } catch (e) {
      _addLog('断开连接失败: $e');
    }
  }

  @override
  void dispose() {
    _connectionSubscription?.cancel();
    _dataSubscription?.cancel();
    disconnect();
    stopScan();
    super.dispose();
  }

  Future<void> connectToDeviceByAddress(String address) async {
    try {
      targetBluetoothAddress = address;
      _addLog('正在通过地址连接设备: $address');
      await startScan();
      
      await Future.delayed(const Duration(seconds: 4));
      
      final device = scanResults.firstWhere(
        (result) => result.device.id.toString() == address,
        orElse: () => throw Exception('未找到指定设备'),
      );
      
      await connectToDevice(device.device);
    } catch (e) {
      _addLog('通过地址连接设备出错: $e');
      rethrow;
    }
  }

  // 自动重连功能
  Future<void> autoReconnect() async {
    if (_connectedDevice != null && !_isConnected) {
      _addLog('尝试自动重连...');
      try {
        await connectToDevice(_connectedDevice!);
      } catch (e) {
        _addLog('自动重连失败: $e');
      }
    }
  }
  
  // 处理分包数据
  bool processPacketData(String rawData) {
    try {
      // 定期清理过期分包
      _cleanupStalePackets();
      
      final packetData = json.decode(rawData);
      if (packetData['packet'] == null) return false;
      
      final String packetId = packetData['packet']['id'];
      final int total = packetData['packet']['total'];
      final int index = packetData['packet']['index'];
      final String body = packetData['packet']['body'];
      final String packetKey = '$packetId-$index';
      
      // 如果这个分包已经处理过，直接返回
      if (_processedPackets[packetId]?.contains(index) ?? false) {
        return false;
      }
      
      // 更新时间戳
      _packetTimestamps[packetId] = DateTime.now();
      
      // 初始化集合
      _processedPackets.putIfAbsent(packetId, () => {});
      _packetBuffers.putIfAbsent(packetId, () => {});
      
      // 添加到已处理集合
      _processedPackets[packetId]!.add(index);
      
      // 存储分包
      _packetBuffers[packetId]![index] = body;
      
      // 检查是否所有分包都已接收
      if (_processedPackets[packetId]!.length == total) {
        // 所有分包都已接收，组装完整数据
        return true;
      }
      
      return false;
    } catch (e) {
      _addLog('处理分包数据出错: $e');
      return false;
    }
  }
  
  // 组装完整数据
  String? assembleCompleteData(String packetId) {
    try {
      if (!_packetBuffers.containsKey(packetId)) return null;
      
      final parts = _packetBuffers[packetId]!;
      final buffer = StringBuffer();
      
      for (int i = 0; i < parts.length; i++) {
        if (parts.containsKey(i)) {
          buffer.write(parts[i]);
        } else {
          // 缺少某个分包
          return null;
        }
      }
      
      // 清理这个包的缓存
      _processedPackets.remove(packetId);
      _packetBuffers.remove(packetId);
      _packetTimestamps.remove(packetId);
      
      return buffer.toString();
    } catch (e) {
      _addLog('组装数据出错: $e');
      return null;
    }
  }
} 