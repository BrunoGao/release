import 'dart:async';
import 'dart:convert';
import 'dart:math'; // 添加math库导入，提供min和max函数
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:intl/intl.dart'; // 添加intl包导入，用于格式化日期时间
import 'package:flutter/services.dart'; // 添加services导入，用于MethodChannel
import 'api_service.dart';
import '../global.dart' as global; //引入全局变量
import '../global.dart'; //引入全局变量
import 'dart:io'; //加在顶部
import 'package:permission_handler/permission_handler.dart'; //顶部引入
import '../utils/global_events.dart' as events; //导入全局事件管理类
import '../utils/health_data_merger.dart'; //导入健康数据合并器
import 'dart:typed_data'; // 添加typed_data支持
import 'ble_binary_protocol.dart'; // 导入二进制TLV协议处理器
import 'ble_protocol_config.dart'; // 导入协议配置管理器
import 'mac_address_util.dart'; // 导入MAC地址工具类
import 'service_keepalive_manager.dart'; // 导入服务保活管理器
import 'package:flutter/foundation.dart';

// 字符串构建器类简化实现 #字符串构建器
class StringBuilder {
  final StringBuffer _buffer = StringBuffer();
  
  void write(String str) {
    _buffer.write(str);
  }
  
  @override
  String toString() {
    return _buffer.toString();
  }
}

class BleSvc { //极简BLE服务
  static final BleSvc i = BleSvc._();
  BleSvc._() {
    // 初始化协议配置
    _initProtocolConfig();
    
    // 🔧 关键：设置原生事件桥接
    _setupNativeEventBridge();
    
    // 加载上次保存的MAC地址
    String savedMac = MacAddressUtil.i.loadLastConnectedMAC();
    if (savedMac.isNotEmpty) {
      _lastConnectedDeviceId = savedMac;
      log('从文件加载上次连接的MAC地址: $_lastConnectedDeviceId');
    }
    
    // 添加健康数据合并器处理结果的监听
    _healthMergerSubscription = HealthDataMerger.i.healthDataStream.listen((mergedData) {
      log('接收到健康数据合并器合并后的完整数据');
      try {
        // 判断数据类型并处理
        var type = mergedData['type'];
        if (type == 'health') {
          // 检测设备重启
          bool deviceRestarted = _detectDeviceRestart(mergedData);
          
          // 生成数据摘要用于判断重复
          String digest = _generateHealthDataDigest(mergedData);
          
          // 如果数据已经处理过且设备未重启，跳过重复数据
          if (_healthDataCache.contains(digest) && !deviceRestarted) {
            log('跳过重复的健康数据');
            return;
          }
          
          // 如果检测到设备重启，记录日志
          if (deviceRestarted) {
            log('检测到设备重启，强制处理合并器健康数据');
          }
          
          // 添加到缓存并限制缓存大小
          _healthDataCache.add(digest);
          if (_healthDataCache.length > _maxCacheSize) {
            _healthDataCache.remove(_healthDataCache.first);
          }
          
          // 预处理健康数据：确保结构正确，添加必要字段
          Map<String, dynamic> processedData = _prepareHealthDataForUpload(mergedData);
          
          h.add(processedData); // 发送到健康数据流
          log('健康数据上传前最终结构: ${json.encode(processedData).substring(0, min(100, json.encode(processedData).length))}...');
          ApiService().uploadHealthData(processedData).then((ok) {
            log('health上传${ok ? "成功" : "失败"}');
          });
        }
      } catch (e) {
        log('处理合并后的健康数据时出错: $e');
      }
    });
  }

  BluetoothDevice? d;
  BluetoothCharacteristic? dc, cc; //设备/数据/命令特征
  final l = StreamController<String>.broadcast();
  Stream<String> get logStream => l.stream;
  final s = StreamController<bool>.broadcast();
  Stream<bool> get connectionStateStream => s.stream;
  final h = StreamController<Map>.broadcast();
  Stream<Map> get healthDataStream => h.stream;
  final v = StreamController<Map>.broadcast();
  Stream<Map> get deviceInfoStream => v.stream;
  final _b = Map<String, List<String?>>(); //分包缓存
  List<int> _db = [];
  List<int> _hb = [];
  bool _c = false;
  int _r = 0;
  Timer? _t, _rt, _monitorTimer, _serviceCheckTimer; //扫描/重连/自动重连/服务检查定时器
  bool _isConnecting = false; //是否正在连接
  DateTime? _lastDataTime; //最后数据时间
  final Duration RECONNECT_INTERVAL = Duration(seconds: 30); //自动重连间隔
  final Duration DATA_TIMEOUT = Duration(minutes: 5); //数据超时时间
  final Duration MONITOR_INTERVAL = Duration(seconds: 6);
  final Duration SERVICE_CHECK_INTERVAL = Duration(seconds: 5); //服务检查间隔
  final _uploadedIds = <String>{}; //已上传分包id
  final _dataCache = <String, DateTime>{}; //数据缓存，key为数据内容，value为接收时间
  final Duration CACHE_TIMEOUT = Duration(seconds: 5); //缓存超时时间
  bool _isReconnecting = false;
  int _reconnectAttempts = 0;
  final int MAX_RECONNECT_ATTEMPTS = 6;
  final Duration RECONNECT_DELAY = Duration(seconds: 10);
  bool _healthServiceAvailable = false; //健康服务是否可用
  bool _wasHealthServiceAvailable = false; //健康服务之前是否可用

  // UUID常量
  final String S_UUID = "1887"; // 服务UUID
  final String D_UUID = "fd10"; // 数据特征
  final String C_UUID = "fd11"; // 命令特征
  final String CCCD = "2902"; // notify描述符

  // 类型常量
  final String T_HEALTH = "health";
  final String T_DEVICE = "device";
  final String T_EVENT = "commonEvent";
  final String T_MSG = "message_response";
  final String T_MTU = "mtu_notification";
  final String T_PROBE = "probe_response"; // 添加探针响应类型
  final String CMD_MSG = "message";
  final String CMD_CFG = "config";
  final String CMD_DISC = "disconnect";
  final String CMD_MTU = "mtu";
  final String CMD_PROBE = "protocol_probe"; // 探针命令

  // 添加数据包类型常量
  final String TYPE_RAW_CHUNK = "raw_chunk"; // 原始分片数据包类型
  final String TYPE_DEVICE_CHUNK = "device_chunk"; // 设备信息分片数据包类型

  // 添加系统配置相关属性
  Map<String, dynamic> _systemConfig = {}; // 系统配置
  DateTime? _lastConfigFetchTime; // 上次获取配置时间
  final int CONFIG_FETCH_INTERVAL = 36000; // 配置获取间隔(秒)
  final int DEFAULT_MESSAGE_FETCH_INTERVAL = 60; // 默认消息获取间隔(秒)
  
  // 蓝牙图标状态
  final _bluetoothIconState = StreamController<String>.broadcast();
  Stream<String> get bluetoothIconStateStream => _bluetoothIconState.stream;
  String _currentBluetoothState = "disconnected"; // disconnected, connected, transmitting, inactive
  
  // 系统配置和接口信息
  Map<String, String> _interfaceUrls = {};
  Map<String, int> _interfaceIntervals = {};
  String _customerName = "未知";
  String _uploadMethod = "bluetooth";
  bool _isFetchingConfig = false;
  Timer? _messageFetchTimer;
  Timer? _configFetchTimer;
  
  // Getter for customer name
  String get customerName => global.customerName;
  
  // Getter for upload method
  String get uploadMethod => _uploadMethod;

  // 添加健康合并器处理结果的订阅对象
  StreamSubscription? _healthMergerSubscription;

  // 添加是否使用新版二进制协议的标志 
  bool _useBinaryProtocol = true; // 强制使用二进制TLV协议

  // 追加成员变量到BleSvc类
  String _lastConnectedDeviceId = ''; // 最后一次成功连接的设备ID
  int _reconnectDelay = 2; // 初始重连延迟(秒)
  final int MAX_RECONNECT_DELAY = 30; // 最大重连延迟(秒)
  final String LAST_MAC_KEY = 'last_connected_mac'; // 存储MAC地址的键名

  // 添加监听订阅对象
  StreamSubscription? _dataCharacteristicSubscription;

  // 添加缺失的成员变量到类定义部分
  bool _dataTransmitting = false; // 是否正在传输数据
  int _currentMtu = 512; // 当前MTU大小
  String _protocolVersion = '1.2'; // 协议版本升级到v1.2

  // 添加设备信息缓存相关
  final Set<String> _deviceInfoCache = <String>{}; // 设备信息摘要缓存
  final Set<String> _eventDataCache = <String>{}; // 事件数据摘要缓存

  // 添加写入队列机制
  final List<Function> _writeQueue = []; // 写入队列
  bool _isWriting = false; // 是否正在写入
  Timer? _writeQueueTimer; // 队列处理定时器

  // 添加连接状态监听相关
  StreamSubscription? _connectionStateSubscription; // 连接状态监听
  bool _serviceChanged = false; // 服务是否变化
  Timer? _serviceChangeTimer; // 服务变化处理定时器

  // 健康数据缓存相关
  final Set<String> _healthDataCache = <String>{}; // 健康数据摘要缓存
  final int _maxCacheSize = 1000; // 最大缓存大小
  
  // 添加设备重启检测相关
  DateTime? _lastDeviceTimestamp; // 上次设备时间戳
  String _lastDeviceId = ''; // 上次设备ID
  bool _deviceRestarted = false; // 设备是否重启

  // 添加notify状态标志防止重复设置
  bool _isNotifyEnabled = false; // 是否已启用notify
  bool _isSettingNotify = false; // 是否正在设置notify

  // GATT操作状态管理(新增) #GATT状态管理
  bool _isGattOperationInProgress = false; // GATT操作进行中
  DateTime? _lastGattOperationTime; // 上次GATT操作时间
  final Duration GATT_OPERATION_INTERVAL = Duration(milliseconds: 1500); // GATT操作最小间隔
  final Duration GATT_OPERATION_TIMEOUT = Duration(seconds: 8); // GATT操作超时时间

  // 智能服务变化检测相关(新增) #智能服务变化检测
  Timer? _serviceChangedTimer; // 服务变化检测定时器
  Timer? _connectionUpdatedTimer; // 连接更新检测定时器
  StreamSubscription? _mtuSubscription; // MTU变化监听
  bool _isHandlingServiceChange = false; // 是否正在处理服务变化
  int _serviceChangeCount = 0; // 服务变化计数
  int _connectionUpdateCount = 0; // 连接更新计数
  DateTime? _lastServiceChangeTime; // 上次服务变化时间
  DateTime? _lastConnectionUpdateTime; // 上次连接更新时间
  Timer? _periodicServiceCheckTimer; // 定期服务检查定时器(新增)
  int _consecutiveNotifyFailures = 0; // 连续notify失败计数(新增)
  DateTime? _lastSuccessfulDataTime; // 最后一次成功接收数据时间(新增)

  // 🔧 原生事件桥接相关(新增)
  static const MethodChannel _nativeEventChannel = MethodChannel('com.ljwx.health/native_events');
  bool _nativeEventBridgeSetup = false;
  
  // 数据监控定时器(新增) #数据监控定时器
  Timer? _dataMonitorTimer;

  void log(x) {
    var t = DateTime.now().toString().split('.')[0];
    debugPrint("[$t] $x");
    l.add("[$t] $x");
    try { File(bleLogFile).writeAsStringSync("[$t] $x\n", mode: FileMode.append); } catch (_) {}
  }

  /// 销毁资源 #资源清理
  void dispose() {
    try {
      _t?.cancel();
      _rt?.cancel();
      _monitorTimer?.cancel();
      _messageFetchTimer?.cancel();
      _configFetchTimer?.cancel();
      _writeQueueTimer?.cancel(); // 取消写入队列定时器
      _serviceChangeTimer?.cancel(); // 取消服务变化处理定时器
      _serviceChangedTimer?.cancel(); // 取消服务变化检测定时器
      _connectionUpdatedTimer?.cancel(); // 取消连接更新检测定时器
      _periodicServiceCheckTimer?.cancel(); // 取消定期服务检查定时器(新增)
      _mtuSubscription?.cancel(); // 取消MTU变化监听
      _dataMonitorTimer?.cancel(); // 取消数据监控定时器(新增)
      _healthMergerSubscription?.cancel();
      _dataCharacteristicSubscription?.cancel();
      _connectionStateSubscription?.cancel(); // 取消连接状态监听
      l.close();
      s.close();
      h.close();
      v.close();
      _bluetoothIconState.close();
    } catch (e) {
      log('销毁资源时出错: $e');
    }
  }

  /// 生成健康数据摘要 #数据摘要生成
  String _generateHealthDataDigest(Map<String, dynamic> data) {
    try {
      // 提取关键字段生成摘要，加入时间戳避免重启后误判
      var healthData = data['data']?['data'] ?? {};
      
      // 获取时间戳，如果没有则使用当前时间
      String timestamp = healthData['timestamp']?.toString() ?? 
                        DateTime.now().millisecondsSinceEpoch.toString();
      
      // 构建更完整的摘要，包含时间戳和更多字段
      String key = '${healthData['id']}_${healthData['heart_rate']}_${healthData['blood_oxygen']}_${healthData['step']}_${healthData['body_temperature']}_${timestamp}';
      
      // 如果时间戳相同但其他关键字段不同，也视为不同数据
      String deviceId = healthData['id']?.toString() ?? 'unknown';
      int heartRate = int.tryParse(healthData['heart_rate']?.toString() ?? '0') ?? 0;
      int bloodOxygen = int.tryParse(healthData['blood_oxygen']?.toString() ?? '0') ?? 0;
      int step = int.tryParse(healthData['step']?.toString() ?? '0') ?? 0;
      
      // 添加接收时间因子，确保即使相同数据在不同时间接收也有不同摘要
      String receiveTime = DateTime.now().millisecondsSinceEpoch.toString();
      String receiveTimeHash = (receiveTime.hashCode % 10000).toString(); // 取后4位作为时间因子
      
      // 生成基于内容、时间戳和接收时间的复合摘要
      String contentDigest = '$deviceId-$heartRate-$bloodOxygen-$step-$timestamp-$receiveTimeHash';
      
      String finalDigest = contentDigest.hashCode.toString();
      log('生成健康数据摘要: $finalDigest (心率:$heartRate, 血氧:$bloodOxygen, 步数:$step, 时间:$timestamp)');
      return finalDigest;
    } catch (e) {
      // 发生错误时使用时间戳确保唯一性
      String errorDigest = DateTime.now().millisecondsSinceEpoch.toString();
      log('生成健康数据摘要出错，使用时间戳: $errorDigest');
      return errorDigest;
    }
  }

  /// 生成设备信息摘要 #生成设备信息摘要
  String _generateDeviceInfoDigest(Map<String, dynamic> data) {
    try {
      var deviceData = data['data'] ?? {};
      String key = '${deviceData['serial_number']}_${deviceData['battery_level']}_${deviceData['wear_state']}';
      return key.hashCode.toString();
    } catch (e) {
      return DateTime.now().millisecondsSinceEpoch.toString();
    }
  }

  /// 生成事件数据摘要 #生成事件数据摘要
  String _generateEventDataDigest(Map<String, dynamic> data) {
    try {
      var eventData = data['data'] ?? {};
      String key = '${eventData['action']}_${eventData['timestamp']}_${eventData['device_sn']}';
      return key.hashCode.toString();
    } catch (e) {
      return DateTime.now().millisecondsSinceEpoch.toString();
    }
  }

  /// 处理数据特征接收到的数据 #数据处理核心
  void _handleDataCharacteristic(List<int> value) async {
    if (value.isEmpty) return;
    
    try {
      log('接收到${value.length}字节数据');
      Uint8List data = Uint8List.fromList(value);
      
      // 🔧 记录成功接收数据的时间
      _lastSuccessfulDataTime = DateTime.now();
      _consecutiveNotifyFailures = 0; // 重置失败计数
      
      // 只使用二进制TLV协议处理数据
      var decoded = BleBinaryProtocol.i.decodeProtocolPacket(data);
      if (decoded == null) {
        log('二进制TLV协议解码失败');
        _consecutiveNotifyFailures++; // 增加失败计数
        return;
      }
      
      // 处理解码后的数据
      Map<String, dynamic>? result = await _processNewBinaryTLVData(decoded);
      if (result == null) {
        _consecutiveNotifyFailures++; // 增加失败计数
        return;
      }
      
      // 根据数据类型处理
      String type = result['type'] ?? '';
      
      // 检测设备重启并清理缓存
      _detectDeviceRestart(result);
      
      // 处理健康数据
      if (type == T_HEALTH) {
        try {
          // 发送到健康数据合并器
          HealthDataMerger.i.receiveDataMap(result);
          log('健康数据已发送到合并器');
        } catch (e) {
          log('发送健康数据到合并器失败: $e');
          _consecutiveNotifyFailures++; // 增加失败计数
        }
      } else if (type == T_DEVICE) {
        _handleDeviceInfo(result);
      } else if (type == T_EVENT) {
        _handleCommonEvent(result);
      } else if (type == T_PROBE) {
        _handleProbeResponse(result);
      } else if (type == BleBinaryProtocol.TYPE_LOG_DATA) {
        _handleLogData(result);
      } else {
        log('未处理的数据包类型: $type');
      }
    } catch (e) {
      log('处理数据包异常: $e');
      _consecutiveNotifyFailures++; // 增加失败计数
    }
  }

  /// 初始化协议配置 #初始化协议配置
  Future<void> _initProtocolConfig() async {
    try {
      await BleProtocolConfig.i.init();
      _useBinaryProtocol = BleProtocolConfig.i.useBinaryProtocol;
      log('协议配置初始化完成，使用二进制协议: $_useBinaryProtocol');
    } catch (e) {
      log('初始化协议配置失败: $e');
    }
  }

  /// 处理新的二进制TLV数据(v1.2增强timestamp支持并直接上传) #处理二进制TLV数据
  Future<Map<String, dynamic>?> _processNewBinaryTLVData(Map<String, dynamic> decoded) async {
    try {
      int type = decoded['type'];
      int format = decoded['format'];
      Uint8List payload = decoded['payload'];
      
      log('TLV数据处理 - 类型: $type, 格式: $format, payload大小: ${payload.length}字节');
      log('TLV原始payload: ${payload.take(50).toList()}...');
      
      Map<String, dynamic> result = {};
      
      // 支持JSON格式数据处理(v1.2新增)
      if (format == BleBinaryProtocol.FORMAT_JSON) {
        try {
          String jsonStr = utf8.decode(payload);
          log('JSON格式数据: ${jsonStr.substring(0, min(100, jsonStr.length))}...');
          var jsonData = json.decode(jsonStr);
          
          // 根据类型处理JSON数据
          switch (type) {
            case BleBinaryProtocol.TYPE_HEALTH_DATA:
              result = {
                'type': 'health',
                'data': {'data': jsonData}
              };
              _uploadHealthDataDirectly(result);
              break;
            case BleBinaryProtocol.TYPE_DEVICE_INFO:
              result = {
                'type': 'device',
                'data': jsonData
              };
              // 添加设备信息去重检查
              String digest = _generateDeviceInfoDigest(result);
              if (!_deviceInfoCache.contains(digest)) {
                _deviceInfoCache.add(digest);
                if (_deviceInfoCache.length > _maxCacheSize) {
                  _deviceInfoCache.remove(_deviceInfoCache.first);
                }
                _uploadDeviceInfoDirectly(result);
              } else {
                log('跳过重复的设备信息');
              }
              break;
            case BleBinaryProtocol.TYPE_COMMON_EVENT:
              // 使用修复机制处理可能损坏的JSON
              Map<String, dynamic> repairedData = BleBinaryProtocol.i.repairCommonEventJson(jsonStr);
              
              result = {
                'type': 'commonEvent',
                'data': repairedData
              };
              
              log('修复后的Common Event数据: $repairedData');
              
              // 添加事件数据去重检查
              String digest = _generateEventDataDigest(result);
              if (!_eventDataCache.contains(digest)) {
                _eventDataCache.add(digest);
                if (_eventDataCache.length > _maxCacheSize) {
                  _eventDataCache.remove(_eventDataCache.first);
                }
                _uploadCommonEventDirectly(result);
              } else {
                log('跳过重复的事件数据');
              }
              break;
            case BleBinaryProtocol.TYPE_LOG_DATA:
              log('开始解码日志数据TLV，payload大小: ${payload.length}');
              try {
                var logData = BleBinaryProtocol.i.decodeLogDataTLV(payload);
                log('日志数据TLV解码完成，字段数量: ${logData.length}');
                log('解码后日志字段: ${logData.keys.toList()}');
                log('日志数据详细内容: $logData');
                
                // 转换时间戳格式
                if (logData.containsKey('timestamp') && logData['timestamp'] is int) {
                  var timestamp = DateTime.fromMillisecondsSinceEpoch(logData['timestamp'] * 1000);
                  logData['timestamp'] = DateFormat('yyyy-MM-dd HH:mm:ss').format(timestamp);
                }
                
                result = {
                  'type': 'watch_log',
                  'data': logData
                };
                
                // 直接上传日志数据
                _uploadWatchLogDirectly(result);
              } catch (e) {
                log('解码日志数据TLV失败: $e');
                return null;
              }
              break;
            default:
              log('JSON格式暂不支持类型: $type');
              return null;
          }
          return result;
        } catch (e) {
          log('解析JSON格式数据失败: $e');
          return null;
        }
      }
      
      if (format != BleBinaryProtocol.FORMAT_BINARY_TLV) {
        log('不支持的数据格式: $format');
        return null;
      }
      
      switch (type) {
        case BleBinaryProtocol.TYPE_HEALTH_DATA:
          log('开始解码健康数据TLV，payload大小: ${payload.length}');
          var healthData = BleBinaryProtocol.i.decodeHealthDataTLV(payload);
          log('健康数据TLV解码完成，字段数量: ${healthData.length}');
          log('解码后健康数据字段: ${healthData.keys.toList()}');
          log('健康数据详细内容: $healthData');
          
          // v1.2确保包含timestamp
          if (!healthData.containsKey('timestamp')) {
            healthData['timestamp'] = DateTime.now().toUtc().add(Duration(hours: 8)).toString().substring(0, 19).replaceFirst('T', ' ');
            log('自动添加timestamp字段');
          }
          
          // 确保包含设备ID
          if (!healthData.containsKey('id') || healthData['id'] == null || healthData['id'].toString().isEmpty) {
            if (global.deviceSn.isNotEmpty) {
              healthData['id'] = global.deviceSn;
              log('自动添加设备ID: ${global.deviceSn}');
            }
          }
          
          result = {
            'type': 'health',
            'data': {'data': healthData}
          };
          
          log('健康数据最终结构字段数: ${result['data']['data'].length}');
          
          // 直接上传健康数据，不再依赖合并器
          _uploadHealthDataDirectly(result);
          break;
        
        case BleBinaryProtocol.TYPE_DEVICE_INFO:
          log('开始解码设备信息TLV，payload大小: ${payload.length}');
          var deviceData = BleBinaryProtocol.i.decodeDeviceInfoTLV(payload);
          log('设备信息TLV解码完成，字段数量: ${deviceData.length}');
          log('解码后设备信息字段: ${deviceData.keys.toList()}');
          log('设备信息详细内容: $deviceData');
          
          // v1.2确保包含timestamp
          if (!deviceData.containsKey('timestamp')) {
            deviceData['timestamp'] = DateTime.now().toUtc().add(Duration(hours: 8)).toString().substring(0, 19).replaceFirst('T', ' ');
            log('自动添加timestamp字段');
          }
          
          result = {
            'type': 'device',
            'data': deviceData
          };
          
          log('设备信息最终结构字段数: ${result['data'].length}');
          
          // 添加设备信息去重检查
          String digest = _generateDeviceInfoDigest(result);
          if (!_deviceInfoCache.contains(digest)) {
            _deviceInfoCache.add(digest);
            if (_deviceInfoCache.length > _maxCacheSize) {
              _deviceInfoCache.remove(_deviceInfoCache.first);
            }
            _uploadDeviceInfoDirectly(result);
          } else {
            log('跳过重复的设备信息');
          }
          break;
        
        case BleBinaryProtocol.TYPE_HEARTBEAT:
          log('开始解码心跳包TLV，payload大小: ${payload.length}');
          var heartbeatData = BleBinaryProtocol.i.decodeHeartbeatTLV(payload);
          log('心跳包TLV解码完成，字段数量: ${heartbeatData.length}');
          log('心跳包详细内容: $heartbeatData');
          
          result = {
            'type': 'probe_response',
            'probe_type': 'heartbeat',
            'status': 'ok',
            'timestamp': heartbeatData['timestamp'] ?? DateTime.now().millisecondsSinceEpoch,
            'battery': heartbeatData['battery'],
            'wear_state': heartbeatData['wear_state']
          };
          break;
        
        case BleBinaryProtocol.TYPE_COMMON_EVENT:
          log('开始解码通用事件，payload大小: ${payload.length}');
          // 通用事件使用TLV格式，改为调用TLV解码方法
          try {
            var eventData = BleBinaryProtocol.i.decodeCommonEventTLV(payload);
            log('通用事件TLV解码完成，字段数量: ${eventData.length}');
            log('解码后事件字段: ${eventData.keys.toList()}');
            log('通用事件详细内容: $eventData');
            
            // 确保包含时间戳
            if (!eventData.containsKey('timestamp')) {
              eventData['timestamp'] = DateTime.now().toUtc().add(Duration(hours: 8)).toString().substring(0, 19).replaceFirst('T', ' ');
              log('自动添加timestamp字段');
            }
            
            result = {
              'type': 'commonEvent',
              'data': eventData
            };
            
            // 添加事件数据去重检查
            String digest = _generateEventDataDigest(result);
            if (!_eventDataCache.contains(digest)) {
              _eventDataCache.add(digest);
              if (_eventDataCache.length > _maxCacheSize) {
                _eventDataCache.remove(_eventDataCache.first);
              }
              _uploadCommonEventDirectly(result);
            } else {
              log('跳过重复的事件数据');
            }
          } catch (e) {
            log('解码通用事件TLV失败: $e');
            return null;
          }
          break;
        
        case BleBinaryProtocol.TYPE_LOG_DATA:
          log('开始解码日志数据TLV，payload大小: ${payload.length}');
          try {
            var logData = BleBinaryProtocol.i.decodeLogDataTLV(payload);
            log('日志数据TLV解码完成，字段数量: ${logData.length}');
            log('解码后日志字段: ${logData.keys.toList()}');
            log('日志数据详细内容: $logData');
            
            // 转换时间戳格式
            if (logData.containsKey('timestamp') && logData['timestamp'] is int) {
              var timestamp = DateTime.fromMillisecondsSinceEpoch(logData['timestamp'] * 1000);
              logData['timestamp'] = DateFormat('yyyy-MM-dd HH:mm:ss').format(timestamp);
            }
            
            result = {
              'type': 'watch_log',
              'data': logData
            };
            
            // 直接上传日志数据
            _uploadWatchLogDirectly(result);
          } catch (e) {
            log('解码日志数据TLV失败: $e');
            return null;
          }
          break;
        
        default:
          log('不支持的数据类型: $type');
          return null;
      }
      
      return result;
    } catch (e) {
      log('处理二进制TLV数据失败: $e');
      return null;
    }
  }

  /// 直接上传健康数据(v1.2) #直接上传健康数据
  void _uploadHealthDataDirectly(Map<String, dynamic> healthData) async {
    try {
      // 添加处理节流，避免过快处理
      await Future.delayed(Duration(milliseconds: 50));
      
      // 检测设备重启
      bool deviceRestarted = _detectDeviceRestart(healthData);
      
      // 生成数据摘要用于判断重复
      String digest = _generateHealthDataDigest(healthData);
      
      // 如果数据已经处理过且设备未重启，跳过重复数据
      if (_healthDataCache.contains(digest) && !deviceRestarted) {
        log('跳过重复的健康数据');
        return;
      }
      
      // 如果检测到设备重启，记录日志
      if (deviceRestarted) {
        log('检测到设备重启，强制处理健康数据');
      }
      
      // 添加到缓存并限制缓存大小
      _healthDataCache.add(digest);
      if (_healthDataCache.length > _maxCacheSize) {
        _healthDataCache.remove(_healthDataCache.first);
      }
      
      // 预处理健康数据：确保结构正确，添加必要字段
      Map<String, dynamic> processedData = _prepareHealthDataForUpload(healthData);
      
      // 添加设备序列号
      if (processedData['data'] != null) {
        var healthFields = processedData['data'];
        if (!healthFields.containsKey('id') || healthFields['id'] == null || healthFields['id'].toString().isEmpty) {
          if (global.deviceSn.isNotEmpty) {
            healthFields['id'] = global.deviceSn;
            log('添加全局设备序列号到健康数据: ${global.deviceSn}');
          }
        }
        
        // 为缺失的关键字段提供默认值
        healthFields['heart_rate'] ??= '0';
        healthFields['blood_oxygen'] ??= '0';
        healthFields['body_temperature'] ??= '0.0';
        healthFields['blood_pressure_systolic'] ??= '0';
        healthFields['blood_pressure_diastolic'] ??= '0';
        healthFields['step'] ??= '0';
        healthFields['distance'] ??= '0.0';
        healthFields['calorie'] ??= '0.0';
        healthFields['latitude'] ??= '0.0';
        healthFields['longitude'] ??= '0.0';
        healthFields['altitude'] ??= '0.0';
        healthFields['stress'] ??= '0';
        healthFields['upload_method'] ??= 'bluetooth';
        
        // 确保时间戳存在
        if (!healthFields.containsKey('timestamp') || healthFields['timestamp'] == null) {
          var now = DateTime.now().toUtc().add(Duration(hours: 8));
          healthFields['timestamp'] = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
        }
        
        log('健康数据补全后字段数: ${healthFields.length}');
        log('关键字段检查 - 心率: ${healthFields['heart_rate']}, 血氧: ${healthFields['blood_oxygen']}, ID: ${healthFields['id']}');
      }
      
      h.add(processedData); // 发送到健康数据流
      log('健康数据上传前最终结构: ${json.encode(processedData).substring(0, min(300, json.encode(processedData).length))}...');
      
        ApiService().uploadHealthData(processedData).then((ok) {
        log('health上传${ok ? "成功" : "失败"}');
        });
    } catch (e) {
      log('直接上传健康数据失败: $e');
    }
  }

  /// 直接上传设备信息(v1.2) #直接上传设备信息
  void _uploadDeviceInfoDirectly(Map<String, dynamic> deviceInfo) async {
    try {
      log('处理设备信息并直接上传');
        
      // 保存设备序列号(支持新旧字段名)
      if (deviceInfo['data'] != null) {
        String serialNumber = '';
        // 尝试从新字段名获取
        if (deviceInfo['data']['SerialNumber'] != null) {
          serialNumber = deviceInfo['data']['SerialNumber'].toString();
        }
        // 如果新字段名没有，尝试旧字段名
        else if (deviceInfo['data']['serial_number'] != null) {
          serialNumber = deviceInfo['data']['serial_number'].toString();
        }
        
        if (serialNumber.isNotEmpty && !serialNumber.contains(':')) {
          global.deviceSn = serialNumber;
          log('从设备信息更新全局设备序列号: $serialNumber');
        }
      }
      
      // 清理和标准化设备信息字段
      if (deviceInfo['data'] != null) {
        var deviceData = deviceInfo['data'];
        Map<String, dynamic> cleanedData = {};
        
        // 🔧 标准化字段映射和数据清理
        cleanedData['System Software Version'] = _getCleanDeviceField(deviceData, ['System Software Version', 'system_version'], '未知版本');
        cleanedData['Wifi Address'] = _getCleanDeviceField(deviceData, ['Wifi Address', 'wifi_address'], '未知');
        cleanedData['Bluetooth Address'] = _getCleanDeviceField(deviceData, ['Bluetooth Address', 'bluetooth_address'], '未知');
        cleanedData['IP Address'] = _cleanIpAddress(_getCleanDeviceField(deviceData, ['IP Address', 'ip_address'], '192.168.1.6'));
        cleanedData['Network Access Mode'] = _parseIntSafe(_getCleanDeviceField(deviceData, ['Network Access Mode', 'network_mode'], 1), 1);
        cleanedData['SerialNumber'] = _getCleanDeviceField(deviceData, ['SerialNumber', 'serial_number'], global.deviceSn.isNotEmpty ? global.deviceSn : '未知');
        cleanedData['Device Name'] = _getCleanDeviceField(deviceData, ['Device Name', 'device_name'], '未知设备');
        cleanedData['IMEI'] = _getCleanDeviceField(deviceData, ['IMEI', 'imei'], '未知');
        cleanedData['batteryLevel'] = _parseIntSafe(_getCleanDeviceField(deviceData, ['batteryLevel', 'battery_level'], 0), 0);
        cleanedData['voltage'] = _parseIntSafe(_getCleanDeviceField(deviceData, ['voltage'], 0), 0);
        cleanedData['chargingStatus'] = _getCleanDeviceField(deviceData, ['chargingStatus', 'charging_status'], '未知');
        cleanedData['wearState'] = _parseIntSafe(_getCleanDeviceField(deviceData, ['wearState', 'wear_state'], 0), 0);
        
        // 添加上传方法和时间戳
        cleanedData['upload_method'] = 'bluetooth';
        cleanedData['timestamp'] = _getCleanDeviceField(deviceData, ['timestamp'], _generateBeijingTimestamp());
        
        // 🔧 验证关键字段的有效性
        if (cleanedData['SerialNumber'].toString().isEmpty || cleanedData['SerialNumber'] == '未知') {
          cleanedData['SerialNumber'] = global.deviceSn.isNotEmpty ? global.deviceSn : 'UNKNOWN_DEVICE';
        }
        
        // 替换原始数据
        deviceInfo['data'] = cleanedData;
        
        log('设备信息清理后字段数: ${cleanedData.length}');
        log('关键字段验证 - 序列号: ${cleanedData['SerialNumber']}, 系统版本: ${cleanedData['System Software Version']}, 电量: ${cleanedData['batteryLevel']}');
        log('网络信息 - IP: ${cleanedData['IP Address']}, 蓝牙: ${cleanedData['Bluetooth Address']}, WiFi: ${cleanedData['Wifi Address']}');
      }
      
      // 添加流到设备信息流
      v.add(deviceInfo);
        _lastDataTime = DateTime.now();
      
      log('设备信息上传前最终结构: ${json.encode(deviceInfo).substring(0, min(300, json.encode(deviceInfo).length))}...');
      
        ApiService().uploadDeviceInfo(deviceInfo).then((ok) {
        log('device上传${ok ? "成功" : "失败"}');
        });
    } catch (e) {
      log('直接上传设备信息失败: $e');
    }
  }

  /// 获取清理后的设备字段值(新增) #获取清理设备字段
  dynamic _getCleanDeviceField(Map<String, dynamic> data, List<String> fieldNames, dynamic defaultValue) {
    for (String fieldName in fieldNames) {
      if (data.containsKey(fieldName) && data[fieldName] != null) {
        var value = data[fieldName];
        // 清理字符串类型的空值和默认值
        if (value is String) {
          value = value.trim();
          if (value.isNotEmpty && value != '未知' && value != 'unknown' && value != 'null') {
            return value;
          }
        } else if (value != null && value != 0) {
          return value;
        }
      }
    }
    return defaultValue;
  }

  /// 清理IP地址信息(新增) #清理IP地址
  String _cleanIpAddress(dynamic ipData) {
    if (ipData == null) return '192.168.1.6';
    
    String ipStr = ipData.toString().trim();
    if (ipStr.isEmpty) return '192.168.1.6';
    
    // 处理多行IP地址，提取主要IP
    List<String> ips = ipStr.split('\n').where((ip) => ip.trim().isNotEmpty).toList();
    
    if (ips.isEmpty) return '192.168.1.6';
    
    // 优先返回IPv4地址
    for (String ip in ips) {
      ip = ip.trim();
      if (ip.contains('.') && !ip.startsWith('fe80') && !ip.startsWith('240e')) {
        return ip;
      }
    }
    
    // 如果没有IPv4，返回第一个有效IP
    return ips.first.trim();
  }

  /// 生成北京时间戳字符串 #生成北京时间戳
  String _generateBeijingTimestamp() {
    var now = DateTime.now().toUtc().add(Duration(hours: 8)); // 转换为北京时间
    return DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
  }

  /// 安全解析整数值(新增) #安全整数解析
  int _parseIntSafe(dynamic value, int defaultValue) {
    if (value == null) return defaultValue;
    
    if (value is int) return value;
    
    if (value is String) {
      try {
        return int.parse(value.trim());
      } catch (e) {
        return defaultValue;
      }
    }
    
    if (value is double) {
      return value.round();
    }
    
    return defaultValue;
  }

  /// 直接上传通用事件(v1.2) #直接上传通用事件
  void _uploadCommonEventDirectly(Map<String, dynamic> eventData) async {
    try {
      log('处理通用事件并直接上传');
      
      // 确保包含设备SN
      if (eventData['data'] != null && !eventData['data'].containsKey('device_sn')) {
        if (global.deviceSn.isNotEmpty) {
          eventData['data']['device_sn'] = global.deviceSn;
          log('添加设备序列号到事件数据: ${global.deviceSn}');
        }
      }
      
      _lastDataTime = DateTime.now();
      
      log('通用事件上传前结构: ${json.encode(eventData).substring(0, min(200, json.encode(eventData).length))}...');
      
        ApiService().uploadCommonEvent(eventData).then((ok) {
        log('event上传${ok ? "成功" : "失败"}');
        });
    } catch (e) {
      log('直接上传通用事件失败: $e');
    }
  }

  /// 处理设备信息 #设备信息处理
  void _handleDeviceInfo(Map<String, dynamic> data) {
    try {
      log('处理设备信息');
      v.add(data);
      _lastDataTime = DateTime.now();
    } catch (e) {
      log('处理设备信息失败: $e');
    }
  }

  /// 处理通用事件 #通用事件处理
  void _handleCommonEvent(Map<String, dynamic> data) {
    try {
      log('处理通用事件');
      s.add(true);
      _lastDataTime = DateTime.now();
    } catch (e) {
      log('处理通用事件失败: $e');
    }
  }

  /// 处理探测响应(v1.2增强心跳包支持) #探测响应处理
  void _handleProbeResponse(Map<String, dynamic> data) {
    try {
      log('收到探测响应消息: ${data.toString()}');
      
      // 提取探测类型
      String probeType = data['probe_type']?.toString() ?? 'unknown';
      
      // 更新服务状态
      _healthServiceAvailable = data['status'] == 'ok';
      _lastDataTime = DateTime.now();
      
      // v1.2处理心跳包特有字段
      if (probeType == 'heartbeat') {
        // 更新电量状态
        if (data.containsKey('battery')) {
          int battery = data['battery'] ?? 0;
          log('心跳包电量状态: $battery%');
        }
        
        // 更新佩戴状态
        if (data.containsKey('wear_state')) {
          int wearState = data['wear_state'] ?? 0;
          log('心跳包佩戴状态: ${wearState == 1 ? "已佩戴" : "未佩戴"}');
        }
        
        // 更新蓝牙图标状态为连接状态
        _currentBluetoothState = "connected";
        _updateBluetoothIconState();
      }
      
      // 通知服务状态变化
      if (_healthServiceAvailable != _wasHealthServiceAvailable) {
        _wasHealthServiceAvailable = _healthServiceAvailable;
        String status = _healthServiceAvailable ? "服务可用" : "服务不可用";
        log('健康服务状态变化: $status');
        
        // 发送状态变化事件
        if (_healthServiceAvailable) {
          events.GlobalEvents.i.showSuccess('健康服务已就绪');
        } else {
          events.GlobalEvents.i.showWarning('健康服务不可用');
        }
      }
    } catch (e) {
      log('处理探测响应失败: $e');
    }
  }
  
  /// 更新蓝牙图标状态(v1.2) #更新蓝牙图标状态
  void _updateBluetoothIconState() {
    if (d == null) {
      _currentBluetoothState = "disconnected";
    } else if (uploadMethod == "wifi") {
      _currentBluetoothState = "inactive";
    } else if (_lastDataTime != null && 
              DateTime.now().difference(_lastDataTime!) < Duration(seconds: 30)) {
      _currentBluetoothState = "transmitting";
    } else {
      _currentBluetoothState = "connected";
    }
    
    _bluetoothIconState.add(_currentBluetoothState);
    log('蓝牙图标状态更新: $_currentBluetoothState');
  }
  
  /// 准备健康数据上传(v1.2自动添加timestamp) #准备健康数据上传
  Map<String, dynamic> _prepareHealthDataForUpload(Map<String, dynamic> data) {
    try {
      // 直接使用健康数据，不添加额外的data层级包装
      Map<String, dynamic> healthData;
      
      // 从嵌套结构中提取健康数据
      if (data.containsKey('data')) {
        if (data['data'] is Map && data['data'].containsKey('data')) {
          healthData = Map<String, dynamic>.from(data['data']['data']);
        } else if (data['data'] is Map) {
          healthData = Map<String, dynamic>.from(data['data']);
        } else {
          healthData = {};
        }
      } else {
        healthData = Map<String, dynamic>.from(data);
      }
      
      healthData['upload_method'] = 'bluetooth';
      
      // v1.2确保包含北京时间戳
      if (!healthData.containsKey('timestamp')) {
        var now = DateTime.now().toUtc().add(Duration(hours: 8)); // 转换为北京时间
        healthData['timestamp'] = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
      }
      
      // 计算血压等处理
      if ((healthData['blood_pressure_systolic'] == null || 
           healthData['blood_pressure_systolic'] == 0) && 
          healthData['heart_rate'] != null) {
        
        int heartRate = int.tryParse(healthData['heart_rate'].toString()) ?? 0;
        if (heartRate > 0) {
          healthData['blood_pressure_systolic'] = (heartRate * 1.2).round();
          healthData['blood_pressure_diastolic'] = (heartRate * 0.8).round();
        }
      }
      
      // 返回扁平化的健康数据结构，与手表上传格式一致
      return {
        'type': 'health',
        'data': healthData
      };
    } catch (e) {
      log('准备健康数据上传时出错: $e');
      return data;
    }
  }

  /// 发送二进制TLV命令 #发送TLV命令  
  Future<bool> sendTLVCommand(int type, Map<String, dynamic> data) async {
    if (cc == null) return false;
    
    try {
      Uint8List payload = BleBinaryProtocol.i.encodeDeviceInfoTLV(data);
      Uint8List packet = BleBinaryProtocol.i.encodeProtocolPacket(
        type, 
        BleBinaryProtocol.FORMAT_BINARY_TLV, 
        payload
      );
      
      await cc!.write(packet);
      log('发送TLV命令成功，类型: $type');
      return true;
    } catch (e) {
      log('发送TLV命令失败: $e');
      return false;
    }
  }
  
  /// 连接蓝牙设备 #设备连接
  Future<bool> connect(String deviceId) async {
    try {
      log('开始连接设备: $deviceId');
      
      // 先清理之前的连接状态和notify设置
      await _cleanupPreviousNotifications();
      
      // 使用正确的扫描方式
      FlutterBluePlus.startScan(timeout: Duration(seconds: 10));
      
      // 监听扫描结果
      StreamSubscription? scanSubscription;
      bool connected = false;
      
      scanSubscription = FlutterBluePlus.scanResults.listen((results) async {
        for (ScanResult result in results) {
          if (result.device.remoteId.toString() == deviceId) {
            await FlutterBluePlus.stopScan();
            scanSubscription?.cancel();
            
            await result.device.connect();
            d = result.device;
            log('设备连接成功');
            
            // 发现服务并设置特征
            List<BluetoothService> services = await d!.discoverServices();
            bool success = await _setupServicesAndCharacteristics(services);
            
            if (success) {
              _c = true;
              s.add(true);
              
              // 启动连接状态监听以处理服务变化
              _startConnectionStateMonitoring();
              
              // 🔥 关键：启动数据监控和自动恢复机制
              startDataMonitoringAndAutoRecover();
              
              // 启动服务保活管理器
              ServiceKeepaliveManager.i.startKeepalive();
              
              connected = true;
              log('设备连接和服务设置完成，数据监控和服务保活已启动');
            } else {
              log('服务设置失败，连接无效');
              await result.device.disconnect();
              d = null;
            }
            break;
          }
        }
      });
      
      // 等待扫描完成
      await Future.delayed(Duration(seconds: 10));
      scanSubscription?.cancel();
      
      return connected;
    } catch (e) {
      log('连接失败: $e');
      return false;
    }
  }

  /// 连接设备（别名方法） #连接设备别名
  Future<bool> conn(String deviceId) async {
    return await connect(deviceId);
  }

  /// 获取蓝牙图标颜色 #获取蓝牙图标颜色
  Color getBluetoothIconColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    switch (_currentBluetoothState) {
      case "disconnected":
        return isDark ? Colors.grey[400]! : Colors.grey;
      case "inactive":
        return isDark ? Colors.grey[400]! : Colors.grey[600]!;
      case "connected":
        return Colors.red;
      case "transmitting":
        return Colors.green;
      default:
        return Colors.amber;
    }
  }

  /// 断开连接 #断开连接
  void disconnect() {
    try {
      // 先清理notify设置
      _cleanupPreviousNotifications();
      
      // 停止数据监控
      stopDataMonitoring();
      
      // 停止服务保活管理器
      ServiceKeepaliveManager.i.stopKeepalive();
      
      // 断开设备连接
      d?.disconnect();
      
      _c = false;
      s.add(false);
      log('设备已断开连接，数据监控和服务保活已停止');
    } catch (e) {
      log('断开连接失败: $e');
    }
  }

  /// 添加写入任务到队列 #写入队列管理
  void _addToWriteQueue(Function writeTask) {
    _writeQueue.add(writeTask);
    _processWriteQueue();
  }

  /// 处理写入队列 #处理写入队列
  void _processWriteQueue() {
    if (_isWriting || _writeQueue.isEmpty) return;
    
    // 检查GATT操作间隔，避免频繁操作 #GATT间隔检查
    if (_lastGattOperationTime != null && 
        DateTime.now().difference(_lastGattOperationTime!) < GATT_OPERATION_INTERVAL) {
      _writeQueueTimer = Timer(GATT_OPERATION_INTERVAL, () {
        _processWriteQueue();
      });
      return;
    }
    
    _isWriting = true;
    _isGattOperationInProgress = true;
    _lastGattOperationTime = DateTime.now();
    
    var task = _writeQueue.removeAt(0);
    
    try {
      task().then((_) {
        _isWriting = false;
        _isGattOperationInProgress = false;
        // 延迟处理下一个任务，避免频繁写入
        _writeQueueTimer = Timer(Duration(milliseconds: 100), () {
          _processWriteQueue();
        });
      }).catchError((e) {
        _isWriting = false;
        _isGattOperationInProgress = false;
        log('写入队列任务执行失败: $e');
        // 继续处理下一个任务
        _writeQueueTimer = Timer(Duration(milliseconds: 200), () {
          _processWriteQueue();
        });
      });
    } catch (e) {
      _isWriting = false;
      _isGattOperationInProgress = false;
      log('写入队列任务异常: $e');
      _writeQueueTimer = Timer(Duration(milliseconds: 200), () {
        _processWriteQueue();
      });
    }
  }

  /// 检测设备是否重启 #设备重启检测
  bool _detectDeviceRestart(Map<String, dynamic> data) {
    try {
      String currentDeviceId = '';
      DateTime? currentTimestamp;
      
      // 从不同类型数据中提取设备ID和时间戳
      if (data['type'] == 'health' && data['data']?['data'] != null) {
        var healthData = data['data']['data'];
        currentDeviceId = healthData['id']?.toString() ?? '';
        String timestampStr = healthData['timestamp']?.toString() ?? '';
        if (timestampStr.isNotEmpty) {
          try {
            currentTimestamp = DateTime.parse(timestampStr.replaceFirst(' ', 'T'));
          } catch (e) {
            log('解析健康数据时间戳失败: $e');
          }
        }
      } else if (data['type'] == 'device' && data['data'] != null) {
        var deviceData = data['data'];
        currentDeviceId = deviceData['serial_number']?.toString() ?? '';
        String timestampStr = deviceData['timestamp']?.toString() ?? '';
        if (timestampStr.isNotEmpty) {
          try {
            currentTimestamp = DateTime.parse(timestampStr.replaceFirst(' ', 'T'));
          } catch (e) {
            log('解析设备信息时间戳失败: $e');
          }
        }
      }
      
      // 检测重启条件
      bool deviceRestarted = false;
      
      // 条件1：设备ID改变
      if (_lastDeviceId.isNotEmpty && currentDeviceId.isNotEmpty && _lastDeviceId != currentDeviceId) {
        log('检测到设备ID变化: $_lastDeviceId -> $currentDeviceId');
        deviceRestarted = true;
      }
      
      // 条件2：时间戳倒退(重启导致时间重置)
      if (_lastDeviceTimestamp != null && currentTimestamp != null) {
        if (currentTimestamp.isBefore(_lastDeviceTimestamp!)) {
          log('检测到时间戳倒退: ${_lastDeviceTimestamp} -> $currentTimestamp，可能设备重启');
          deviceRestarted = true;
        }
      }
      
      // 更新记录
      if (currentDeviceId.isNotEmpty) {
        _lastDeviceId = currentDeviceId;
      }
      if (currentTimestamp != null) {
        _lastDeviceTimestamp = currentTimestamp;
      }
      
      // 如果检测到重启，清理缓存
      if (deviceRestarted) {
        log('检测到设备重启，清理数据缓存');
        _clearDataCaches();
        _deviceRestarted = true;
      }
      
      return deviceRestarted;
    } catch (e) {
      log('设备重启检测异常: $e');
      return false;
    }
  }

  /// 清理数据缓存 #清理数据缓存
  void _clearDataCaches() {
    try {
      int oldHealthCacheSize = _healthDataCache.length;
      int oldDeviceCacheSize = _deviceInfoCache.length;
      int oldEventCacheSize = _eventDataCache.length;
      
      _healthDataCache.clear();
      _deviceInfoCache.clear();
      _eventDataCache.clear();
      
      log('数据缓存已清理 - 健康数据: $oldHealthCacheSize, 设备信息: $oldDeviceCacheSize, 事件数据: $oldEventCacheSize');
    } catch (e) {
      log('清理数据缓存失败: $e');
    }
  }

  /// 开始监听连接状态变化 #连接状态监听
  void _startConnectionStateMonitoring() {
    if (d == null) return;
    
    try {
      // 取消之前的监听
      _connectionStateSubscription?.cancel();
      _mtuSubscription?.cancel();
      
      // 监听连接状态变化
      _connectionStateSubscription = d!.connectionState.listen((state) {
        log('连接状态变化: $state');
        
        switch (state) {
          case BluetoothConnectionState.connected:
            log('设备已连接，检查服务状态');
            _handleConnectionEstablished();
            break;
          case BluetoothConnectionState.disconnected:
            log('设备已断开连接');
            _handleConnectionLost();
            break;
          default:
            log('连接状态: $state');
        }
      }, onError: (e) {
        log('连接状态监听错误: $e');
      });
      
      // 智能监听MTU变化(作为连接参数更新的补充检测) #智能MTU监听
      _mtuSubscription = d!.mtu.listen((newMtu) {
        if (newMtu != _currentMtu) {
          _currentMtu = newMtu;
          log('MTU变化检测: $newMtu，触发服务变化检查');
          _handleMtuOrConnectionParameterChange('MTU变化');
        }
      }, onError: (e) {
        log('MTU监听错误: $e');
      });
      
      log('连接状态监听和MTU监听已启动，等待原生事件触发');
    } catch (e) {
      log('启动连接状态监听失败: $e');
    }
  }

  /// 处理MTU或连接参数变化(新增) #处理连接参数变化
  void _handleMtuOrConnectionParameterChange(String changeType) {
    try {
      DateTime now = DateTime.now();
      
      // 记录变化事件
      if (changeType.contains('MTU')) {
        _lastConnectionUpdateTime = now;
        _connectionUpdateCount++;
        log('$changeType 事件 #${_connectionUpdateCount}，时间: ${now.toString().substring(11, 19)}');
      } else {
        _lastServiceChangeTime = now;
        _serviceChangeCount++;
        log('$changeType 事件 #${_serviceChangeCount}，时间: ${now.toString().substring(11, 19)}');
      }
      
      // 🔧 关键：onServiceChanged必须强制重新discover，不能跳过
      bool isServiceChanged = changeType.toLowerCase().contains('service') || 
                             changeType.toLowerCase().contains('changed');
      
      if (isServiceChanged) {
        log('检测到服务变化事件，启动简单强制重连');
        // 🚀 使用最简单的重连方法
        simpleForceReconnect().then((success) {
          if (success) {
            log('✅ 服务变化后简单重连成功');
            events.GlobalEvents.i.showSuccess('蓝牙服务已自动恢复');
          } else {
            log('❌ 服务变化后简单重连失败，尝试完整恢复');
            _forceServiceRediscoveryAndNotify(changeType);
          }
        });
        return;
      }
      
      // 对于其他变化，延迟后触发简单重连
      log('$changeType 变化，2秒后触发简单重连');
      Timer(Duration(seconds: 2), () {
        simpleForceReconnect().then((success) {
          log('延迟简单重连结果: ${success ? "成功" : "失败"}');
        });
      });
      
    } catch (e) {
      log('处理$changeType失败: $e');
    }
  }

  /// 强制服务重新发现和notify设置(新增) #强制服务重新发现
  Future<void> _forceServiceRediscoveryAndNotify(String reason) async {
    if (d == null || !d!.isConnected) {
      log('设备未连接，跳过强制服务重新发现');
      return;
    }
    
    if (_isHandlingServiceChange) {
      log('已在处理服务变化，跳过重复强制操作');
      return;
    }
    
    try {
      _isHandlingServiceChange = true;
      log('🔧 开始强制服务重新发现流程，原因: $reason');
      
      // 步骤1：清理旧的notify设置和监听
      log('步骤1: 清理旧的notify设置');
      await _cleanupPreviousNotifications();
      await Future.delayed(Duration(milliseconds: 500));
      
      // 步骤2：强制重新发现服务
      log('步骤2: 强制重新发现服务');
      List<BluetoothService> services = [];
      int maxRetries = 3;
      
      for (int retry = 0; retry < maxRetries; retry++) {
        try {
          services = await d!.discoverServices();
          log('服务重新发现成功，找到${services.length}个服务');
          break;
        } catch (e) {
          log('服务发现失败 (第${retry + 1}次): $e');
          if (retry < maxRetries - 1) {
            await Future.delayed(Duration(milliseconds: 1000 * (retry + 1)));
          } else {
            throw e;
          }
        }
      }
      
      if (services.isEmpty) {
        log('强制服务发现失败，未找到任何服务');
        return;
      }
      
      // 步骤3：重新设置特征和notify
      log('步骤3: 重新设置特征和notify');
      bool setupSuccess = await _setupServicesAndCharacteristics(services);
      
      if (setupSuccess) {
        log('🎉 强制服务重新发现和notify设置成功');
        
        // 步骤4：验证notify状态
        if (dc != null && dc!.isNotifying) {
          log('✅ notify状态验证成功: ${dc!.isNotifying}');
          
          // 更新连接状态
          s.add(true);
          _updateBluetoothIconState();
          
          // 发送成功通知
          events.GlobalEvents.i.showSuccess('服务变化后自动恢复成功');
        } else {
          log('❌ notify状态验证失败');
          throw Exception('notify设置验证失败');
        }
      } else {
        log('❌ 强制服务重新设置失败');
        throw Exception('服务重新设置失败');
      }
      
    } catch (e) {
      log('🚨 强制服务重新发现过程失败: $e');
      
      // 失败时延迟重试
      _serviceChangedTimer = Timer(Duration(seconds: 5), () {
        log('强制服务重新发现失败，5秒后重试');
        _forceServiceRediscoveryAndNotify('重试: $reason');
      });
    } finally {
      _isHandlingServiceChange = false;
    }
  }

  /// 延迟处理服务检查(新增) #延迟服务检查
  void _handleDelayedServiceCheck(String changeType) async {
    if (d == null || !d!.isConnected) {
      log('设备未连接，跳过$changeType后的服务检查');
      return;
    }
    
    try {
      _isHandlingServiceChange = true;
      log('开始处理$changeType后的服务检查');
      
      // 再次检查notify状态是否正常 #二次状态确认
      if (dc != null && dc!.isNotifying && _dataCharacteristicSubscription != null) {
        log('二次检查发现notify状态已恢复正常，无需重新设置');
        _isHandlingServiceChange = false;
        return;
      }
      
      log('确认需要重新设置notify，开始重新配置服务');
      await _recheckServicesAndNotify();
      
    } catch (e) {
      log('处理$changeType后的服务检查失败: $e');
    } finally {
      _isHandlingServiceChange = false;
    }
  }

  /// 处理连接建立 #连接建立处理
  void _handleConnectionEstablished() {
    try {
      log('处理连接建立事件');
      
      // 添加防抖机制，避免频繁服务检查 #防抖处理
      if (_serviceChangeTimer != null && _serviceChangeTimer!.isActive) {
        log('服务检查定时器已激活，跳过重复检查');
        return;
      }
      
      // 使用FlutterBluePlus原生属性检查服务状态 #原生状态检查
      if (dc != null && cc != null && dc!.isNotifying) {
        log('服务已正确设置(notify: ${dc!.isNotifying})，跳过重新检查');
        return;
      }
      
      // 触发智能服务变化检测
      _handleMtuOrConnectionParameterChange('连接建立');
    } catch (e) {
      log('处理连接建立失败: $e');
    }
  }

  /// 处理连接丢失 #连接丢失处理
  void _handleConnectionLost() {
    try {
      log('处理连接丢失事件');
      
      // 清理状态
      _clearConnectionState();
      
      // 取消所有智能检测定时器
      _serviceChangedTimer?.cancel();
      _connectionUpdatedTimer?.cancel();
      _periodicServiceCheckTimer?.cancel(); // 取消定期服务检查(新增)
      _isHandlingServiceChange = false;
      
      // 重置计数器
      _consecutiveNotifyFailures = 0;
      _lastSuccessfulDataTime = null;
      
      // 简化处理：仅清理状态，不强制重连
      log('连接已丢失，状态已清理');
    } catch (e) {
      log('处理连接丢失失败: $e');
    }
  }

  /// 重新检查服务并设置notify #重新检查服务
  Future<void> _recheckServicesAndNotify() async {
    if (d == null || !d!.isConnected) {
      log('设备未连接，跳过服务重检');
      return;
    }
    
    // 防止重复检查 #重复检查防护
    if (_isSettingNotify) {
      log('正在设置服务，跳过重复检查');
      return;
    }
    
    // 使用FlutterBluePlus原生属性检查服务状态 #原生状态检查
    if (dc != null && cc != null && dc!.isNotifying && _dataCharacteristicSubscription != null) {
      log('服务状态正常(notify: ${dc!.isNotifying})，无需重新检查');
      return;
    }
    
    try {
      log('重新检查服务并设置notify');
      
      // 重新发现服务(减少重试次数)
      List<BluetoothService> services = [];
      int retryCount = 0;
      const maxRetries = 2;
      
      while (retryCount < maxRetries) {
        try {
          services = await d!.discoverServices();
          log('重新发现了 ${services.length} 个服务');
          break;
        } catch (e) {
          retryCount++;
          log('发现服务失败 (尝试 $retryCount/$maxRetries): $e');
          if (retryCount < maxRetries) {
            await Future.delayed(Duration(milliseconds: 1000));
          } else {
            throw e;
          }
        }
      }
      
      if (services.isEmpty) {
        log('未发现任何服务，稍后重试');
        _serviceChangeTimer = Timer(Duration(seconds: 8), () {
          _recheckServicesAndNotify();
        });
        return;
      }
      
      // 检查目标服务是否存在
      bool targetServiceFound = false;
      for (var service in services) {
        log('发现服务: ${service.uuid}');
        if (service.uuid.toString().toLowerCase().contains(S_UUID)) {
          targetServiceFound = true;
          break;
        }
      }
      
      if (!targetServiceFound) {
        log('目标服务 $S_UUID 未找到，稍后重试');
        _serviceChangeTimer = Timer(Duration(seconds: 6), () {
          _recheckServicesAndNotify();
        });
        return;
      }
      
      // 仅在需要时清理之前的notify设置 #条件清理
      if (dc != null && (dc!.isNotifying || _dataCharacteristicSubscription != null)) {
        await _cleanupPreviousNotifications();
        await Future.delayed(Duration(milliseconds: 500));
      }
      
      // 重新设置服务和特征
      bool success = await _setupServicesAndCharacteristics(services);
      
      if (success) {
        log('服务重新设置成功，notify已重新启用');
        _serviceChanged = false;
        
        // 更新连接状态
        s.add(true);
        _updateBluetoothIconState();
        
        // 发送成功通知
        events.GlobalEvents.i.showSuccess('蓝牙服务已重新连接');
      } else {
        log('服务重新设置失败，等待后再次重试');
        _serviceChangeTimer = Timer(Duration(seconds: 8), () {
          _recheckServicesAndNotify();
        });
      }
    } catch (e) {
      log('重新检查服务失败: $e');
      
      // 失败时延迟重试
      _serviceChangeTimer = Timer(Duration(seconds: 10), () {
        _recheckServicesAndNotify();
      });
    }
  }

  /// 设置服务和特征 #设置服务和特征
  Future<bool> _setupServicesAndCharacteristics(List<BluetoothService> services) async {
    try {
      // 防止重复设置
      if (_isSettingNotify) {
        log('正在设置notify，跳过重复操作');
        return false;
      }
      
      _isSettingNotify = true;
      bool foundDataCharacteristic = false;
      bool foundCommandCharacteristic = false;
      
      for (var service in services) {
        if (service.uuid.toString().toLowerCase().contains(S_UUID)) {
          log('找到目标服务: ${service.uuid}');
          
          for (var characteristic in service.characteristics) {
            String uuid = characteristic.uuid.toString().toLowerCase();
            
            if (uuid.contains(D_UUID)) {
              log('找到数据特征: $uuid');
              dc = characteristic;
              foundDataCharacteristic = true;
              
              // 🔧 增强的notify状态检查和设置逻辑
              await _setupNotifyForCharacteristic(characteristic);
            }
            
            if (uuid.contains(C_UUID)) {
              log('找到命令特征: $uuid');
              cc = characteristic;
              foundCommandCharacteristic = true;
            }
          }
        }
      }
      
      bool success = foundDataCharacteristic && foundCommandCharacteristic && (dc?.isNotifying ?? false);
      log('服务设置${success ? "成功" : "失败"} - 数据特征: $foundDataCharacteristic, 命令特征: $foundCommandCharacteristic, notify状态: ${dc?.isNotifying ?? false}');
      
      _isSettingNotify = false;
      return success;
    } catch (e) {
      log('设置服务和特征失败: $e');
      _isSettingNotify = false;
      return false;
    }
  }

  /// 为特征设置notify(新增) #设置特征notify
  Future<void> _setupNotifyForCharacteristic(BluetoothCharacteristic characteristic) async {
    try {
      // 检查特征是否支持notify或indicate
      if (!characteristic.properties.notify && !characteristic.properties.indicate) {
        log('特征不支持notify/indicate功能');
        return;
      }
      
      // 🔧 notify状态锁：检查是否已经启用
      if (characteristic.isNotifying) {
        log('特征已启用notify (${characteristic.isNotifying})，检查监听状态');
        _isNotifyEnabled = true;
        
        // 如果notify已启用但监听丢失，重新设置监听
        if (_dataCharacteristicSubscription == null) {
          _dataCharacteristicSubscription = characteristic.lastValueStream.listen(
            _handleDataCharacteristic,
            onError: (e) => log('数据特征监听错误: $e')
          );
          log('重新设置数据监听');
        }
        return;
      }
      
      // 🔧 设置notify前的预检查
      if (_isNotifyEnabled && dc == characteristic) {
        log('该特征的notify状态锁已设置，跳过重复设置');
        return;
      }
      
      log('开始为特征设置notify');
      
      // 设置notify
      await characteristic.setNotifyValue(true);
      await Future.delayed(Duration(milliseconds: 300));
      
      // 🔧 关键：验证notify是否设置成功
      if (characteristic.isNotifying) {
        log('✅ 数据特征notify设置成功，状态: ${characteristic.isNotifying}');
        _isNotifyEnabled = true;
        
        // 设置数据监听
        _dataCharacteristicSubscription = characteristic.lastValueStream.listen(
          _handleDataCharacteristic,
          onError: (e) => log('数据特征监听错误: $e')
        );
        log('数据监听已建立');
      } else {
        log('❌ 数据特征notify设置失败，状态仍为: ${characteristic.isNotifying}');
        throw Exception('notify设置失败，状态验证不通过');
      }
      
    } catch (e) {
      log('设置特征notify失败: $e');
      _isNotifyEnabled = false;
      throw e;
    }
  }

  /// 清理之前的通知设置 #清理通知设置
  Future<void> _cleanupPreviousNotifications() async {
    try {
      // 取消数据特征的订阅
      if (_dataCharacteristicSubscription != null) {
        log('取消之前的数据特征订阅');
        await _dataCharacteristicSubscription!.cancel();
        _dataCharacteristicSubscription = null;
      }
      
      // 使用FlutterBluePlus原生属性检查并关闭notify #原生notify检查
      if (dc != null && dc!.isNotifying) {
        try {
          log('关闭数据特征的notify(当前状态: ${dc!.isNotifying})');
          
          // 检查特征是否仍然有效
          if (dc!.serviceUuid.toString().isNotEmpty) {
            await dc!.setNotifyValue(false);
            await Future.delayed(Duration(milliseconds: 300));
            
            // 验证notify是否关闭成功 #关闭验证
            if (!dc!.isNotifying) {
              log('数据特征notify关闭成功，状态: ${dc!.isNotifying}');
            } else {
              log('数据特征notify关闭失败，状态仍为: ${dc!.isNotifying}');
            }
          } else {
            log('数据特征已失效，跳过notify关闭');
          }
        } catch (e) {
          log('关闭数据特征notify失败: $e');
          // 不抛出异常，继续清理其他资源
        }
      } else if (dc != null) {
        log('数据特征notify未启用(${dc!.isNotifying})，跳过关闭');
      }
      
      // 重置状态标志
      _isNotifyEnabled = false;
      _isSettingNotify = false;
      
      // 清理特征引用
      dc = null;
      cc = null;
      
      log('之前的通知设置已清理，状态已重置');
    } catch (e) {
      log('清理通知设置失败: $e');
      // 即使清理失败也要确保引用和状态被重置
      _isNotifyEnabled = false;
      _isSettingNotify = false;
      dc = null;
      cc = null;
    }
  }

  /// 清理连接状态 #清理连接状态
  void _clearConnectionState() {
    try {
      _c = false;
      _healthServiceAvailable = false;
      _wasHealthServiceAvailable = false;
      
      // 重置notify状态标志
      _isNotifyEnabled = false;
      _isSettingNotify = false;
      
      // 重置智能检测状态
      _isHandlingServiceChange = false;
      _serviceChangeCount = 0;
      _connectionUpdateCount = 0;
      
      s.add(false);
      _updateBluetoothIconState();
      
      log('连接状态已清理，notify状态已重置');
    } catch (e) {
      log('清理连接状态失败: $e');
    }
  }

  /// 手动触发服务变化检测(新增公共方法) #手动触发服务变化检测
  void triggerServiceChangeDetection({String reason = '外部触发'}) {
    if (d == null || !d!.isConnected) {
      log('设备未连接，跳过服务变化检测');
      return;
    }
    
    log('收到$reason，使用简单重连方式处理');
    
    // 🚀 优先使用最简单的重连方法
    simpleForceReconnect().then((success) {
      if (success) {
        log('✅ $reason 简单重连成功');
      } else {
        log('❌ $reason 简单重连失败，使用智能检测');
        _handleMtuOrConnectionParameterChange(reason);
      }
    });
  }

  /// 智能重连机制(新增) #智能重连机制
  Future<void> smartReconnectWithServiceDetection() async {
    if (d == null) {
      log('设备为空，无法执行智能重连');
      return;
    }
    
    try {
      log('开始智能重连流程');
      
      // 清理当前状态
      await _cleanupPreviousNotifications();
      
      // 检查设备连接状态
      bool isConnected = false;
      try {
        isConnected = d!.isConnected;
      } catch (e) {
        log('检查连接状态失败: $e');
      }
      
      if (!isConnected) {
        log('设备未连接，需要重新建立连接');
        // 这里可以触发重新扫描连接流程
        _clearConnectionState();
        return;
      }
      
      log('设备已连接，重新配置服务');
      // 延迟执行，给设备稳定时间
      await Future.delayed(Duration(seconds: 1));
      
      List<BluetoothService> services = await d!.discoverServices();
      bool success = await _setupServicesAndCharacteristics(services);
      
      if (success) {
        log('智能重连成功，服务已重新配置');
        s.add(true);
        _updateBluetoothIconState();
        
        // 重新启动监听
        _startConnectionStateMonitoring();
      } else {
        log('智能重连失败，服务配置不成功');
      }
    } catch (e) {
      log('智能重连过程出错: $e');
    }
  }

  /// 修复公共事件JSON格式 #修复JSON格式
  String _fixCommonEventJson(String jsonStr) {
    if (jsonStr.isEmpty) return jsonStr;
    
    try {
      // 尝试直接解析，如果成功则无需修复
      json.decode(jsonStr);
      return jsonStr;
    } catch (e) {
      log('JSON格式异常，尝试修复: $e');
    }
    
    // 修复常见的JSON格式问题
    String fixed = jsonStr;
    
    // 修复双重转义的引号
    fixed = fixed.replaceAll('\\"', '"');
    
    // 修复转义的大括号
    fixed = fixed.replaceAll('\\{', '{');
    fixed = fixed.replaceAll('\\}', '}');
    
    // 修复可能的字段值包含引号的问题
    // 检查是否存在类似 "action":"{\"action" 的模式
    RegExp pattern = RegExp(r'"([^"]+)":"(\{[^}]*)"');
    if (pattern.hasMatch(fixed)) {
      log('检测到嵌套JSON字符串，尝试重新构造');
      
      // 尝试从原始字符串中提取有效信息
      try {
        // 查找action、value、device_sn等关键字段
        String? action = _extractFieldFromMalformedJson(fixed, 'action');
        String? value = _extractFieldFromMalformedJson(fixed, 'value');  
        String? deviceSn = _extractFieldFromMalformedJson(fixed, 'device_sn');
        
        if (action != null || value != null) {
          Map<String, dynamic> rebuiltJson = {};
          if (action != null) rebuiltJson['action'] = action;
          if (value != null) rebuiltJson['value'] = value;
          if (deviceSn != null) rebuiltJson['device_sn'] = deviceSn;
          
          // 添加时间戳
          rebuiltJson['timestamp'] = DateTime.now().toUtc().add(Duration(hours: 8)).toString().substring(0, 19).replaceFirst('T', ' ');
          
          fixed = json.encode(rebuiltJson);
          log('重新构造的JSON: $fixed');
        }
      } catch (e) {
        log('重新构造JSON失败: $e');
      }
    }
    
    // 再次验证修复后的JSON
    try {
      json.decode(fixed);
      log('JSON修复成功');
      return fixed;
    } catch (e) {
      log('JSON修复后仍无法解析: $e');
      // 返回一个最基本的有效JSON
      return '{"action":"unknown","value":"malformed_data","timestamp":"${DateTime.now().toUtc().add(Duration(hours: 8)).toString().substring(0, 19).replaceFirst('T', ' ')}"}';
    }
  }

  /// 从格式错误的JSON中提取字段值 #提取字段值
  String? _extractFieldFromMalformedJson(String malformedJson, String fieldName) {
    try {
      // 查找字段名称的位置
      String pattern = '"$fieldName"';
      int fieldIndex = malformedJson.indexOf(pattern);
      if (fieldIndex == -1) return null;
      
      // 查找冒号位置
      int colonIndex = malformedJson.indexOf(':', fieldIndex);
      if (colonIndex == -1) return null;
      
      // 跳过冒号和可能的空格、引号
      int startIndex = colonIndex + 1;
      while (startIndex < malformedJson.length && 
             (malformedJson[startIndex] == ' ' || malformedJson[startIndex] == '"')) {
        startIndex++;
      }
      
      if (startIndex >= malformedJson.length) return null;
      
      // 查找字段值的结束位置
      int endIndex = startIndex;
      bool inQuotes = false;
      int braceLevel = 0;
      
      while (endIndex < malformedJson.length) {
        String char = malformedJson[endIndex];
        
        if (char == '"' && (endIndex == startIndex || malformedJson[endIndex - 1] != '\\')) {
          inQuotes = !inQuotes;
        } else if (!inQuotes) {
          if (char == '{') {
            braceLevel++;
          } else if (char == '}') {
            braceLevel--;
          } else if ((char == ',' || char == '}') && braceLevel == 0) {
            break;
          }
        }
        
        endIndex++;
      }
      
      if (endIndex > startIndex) {
        String value = malformedJson.substring(startIndex, endIndex).trim();
        // 移除可能的尾部引号
        if (value.endsWith('"')) {
          value = value.substring(0, value.length - 1);
        }
        return value.isEmpty ? null : value;
      }
      
      return null;
    } catch (e) {
      log('提取字段 $fieldName 失败: $e');
      return null;
    }
  }

  /// 获取智能检测状态信息(新增) #获取检测状态信息
  Map<String, dynamic> get intelligentDetectionStatus {
    return {
      'isHandlingServiceChange': _isHandlingServiceChange,
      'serviceChangeCount': _serviceChangeCount,
      'connectionUpdateCount': _connectionUpdateCount,
      'lastServiceChangeTime': _lastServiceChangeTime?.toString(),
      'lastConnectionUpdateTime': _lastConnectionUpdateTime?.toString(),
      'notifyEnabled': _isNotifyEnabled,
      'currentMtu': _currentMtu,
      'deviceConnected': d?.isConnected ?? false,
      'healthServiceAvailable': _healthServiceAvailable,
    };
  }

  /// 重置智能检测统计信息(新增) #重置检测统计
  void resetIntelligentDetectionStats() {
    _serviceChangeCount = 0;
    _connectionUpdateCount = 0;
    _lastServiceChangeTime = null;
    _lastConnectionUpdateTime = null;
    log('智能检测统计信息已重置');
  }

  /// 测试智能重连机制(新增测试方法) #测试智能重连
  Future<Map<String, dynamic>> testIntelligentReconnection() async {
    var testResult = <String, dynamic>{};
    var startTime = DateTime.now();
    
    try {
      log('🧪 开始测试智能重连机制');
      testResult['test_start_time'] = startTime.toString();
      
      // 测试1: 检查当前连接状态
      testResult['step1_connection_check'] = d?.isConnected ?? false;
      testResult['step1_notify_state'] = dc?.isNotifying ?? false;
      testResult['step1_subscription'] = _dataCharacteristicSubscription != null;
      
      // 测试2: 模拟服务变化事件
      log('步骤2: 模拟onServiceChanged事件');
      triggerServiceChangeDetection(reason: '测试_onServiceChanged');
      await Future.delayed(Duration(seconds: 1));
      testResult['step2_service_change_triggered'] = true;
      
      // 测试3: 检查notify状态恢复
      log('步骤3: 检查notify状态恢复');
      bool notifyRecovered = await checkAndRecoverNotifyState();
      testResult['step3_notify_recovered'] = notifyRecovered;
      
      // 测试4: 验证数据传输
      log('步骤4: 验证数据传输能力');
      testResult['step4_data_characteristic'] = dc != null;
      testResult['step4_command_characteristic'] = cc != null;
      testResult['step4_final_notify_state'] = dc?.isNotifying ?? false;
      
      // 计算测试总时间
      var endTime = DateTime.now();
      testResult['total_test_time_ms'] = endTime.difference(startTime).inMilliseconds;
      testResult['test_success'] = notifyRecovered && (dc?.isNotifying ?? false);
      
      // 获取智能检测状态
      testResult['intelligent_status'] = intelligentDetectionStatus;
      
      log('🎉 智能重连机制测试完成');
      log('测试结果: ${testResult['test_success'] ? "成功" : "失败"}');
      log('总耗时: ${testResult['total_test_time_ms']}ms');
      
    } catch (e) {
      log('🚨 智能重连机制测试异常: $e');
      testResult['test_error'] = e.toString();
      testResult['test_success'] = false;
    }
    
    return testResult;
  }

  /// 获取完整状态报告(新增诊断方法) #获取状态报告
  Map<String, dynamic> getFullStatusReport() {
    return {
      'timestamp': DateTime.now().toString(),
      'device_info': {
        'connected': d?.isConnected ?? false,
        'device_id': d?.remoteId.toString() ?? 'null',
        'mtu': _currentMtu,
      },
      'characteristics': {
        'data_char_exists': dc != null,
        'command_char_exists': cc != null,
        'notify_enabled': dc?.isNotifying ?? false,
        'subscription_exists': _dataCharacteristicSubscription != null,
      },
      'internal_states': {
        'notify_enabled_flag': _isNotifyEnabled,
        'setting_notify_flag': _isSettingNotify,
        'handling_service_change': _isHandlingServiceChange,
        'gatt_operation_in_progress': _isGattOperationInProgress,
      },
      'intelligent_detection': intelligentDetectionStatus,
      'service_status': {
        'health_service_available': _healthServiceAvailable,
        'last_data_time': _lastDataTime?.toString(),
      }
    };
  }

  /// 检查并恢复notify状态(新增公共方法) #检查恢复notify状态
  Future<bool> checkAndRecoverNotifyState() async {
    if (d == null || !d!.isConnected) {
      log('设备未连接，无法检查notify状态');
      return false;
    }
    
    try {
      log('开始检查notify状态');
      
      // 检查当前notify状态
      bool notifyOk = dc != null && 
                     dc!.isNotifying && 
                     _dataCharacteristicSubscription != null &&
                     _isNotifyEnabled;
      
      log('当前notify状态检查: 特征存在=${dc != null}, notify启用=${dc?.isNotifying ?? false}, 监听存在=${_dataCharacteristicSubscription != null}, 状态锁=${_isNotifyEnabled}');
      
      if (notifyOk) {
        log('✅ notify状态正常，无需恢复');
        return true;
      }
      
      log('❌ notify状态异常，开始自动恢复');
      await _forceServiceRediscoveryAndNotify('notify状态检查');
      
      // 重新检查恢复结果
      notifyOk = dc != null && dc!.isNotifying && _isNotifyEnabled;
      log('恢复后notify状态: ${notifyOk ? "正常" : "仍异常"}');
      
      return notifyOk;
    } catch (e) {
      log('检查并恢复notify状态失败: $e');
      return false;
    }
  }

  /// 模拟原生onServiceChanged事件检测(新增) #模拟原生事件检测
  Future<void> simulateNativeServiceChangeEvents() async {
    if (d == null || !d!.isConnected) {
      log('设备未连接，无法模拟原生事件');
      return;
    }
    
    try {
      log('🔍 开始模拟原生onServiceChanged和onConnectionUpdated事件检测');
      
      // 检测1: 尝试重新发现服务，模拟onServiceChanged
      log('检测1: 模拟onServiceChanged - 重新发现服务');
      try {
        var services = await d!.discoverServices();
        log('服务重新发现成功，找到${services.length}个服务');
        
        // 检查目标服务是否存在
        bool targetServiceExists = false;
        for (var service in services) {
          if (service.uuid.toString().toLowerCase().contains(S_UUID)) {
            targetServiceExists = true;
            break;
          }
        }
        
        if (!targetServiceExists) {
          log('❌ 目标服务丢失，触发onServiceChanged处理');
          triggerServiceChangeDetection(reason: '模拟_onServiceChanged_服务丢失');
        } else {
          log('✅ 目标服务正常存在');
        }
      } catch (e) {
        log('❌ 服务发现异常，可能服务变化: $e');
        triggerServiceChangeDetection(reason: '模拟_onServiceChanged_异常');
      }
      
      // 检测2: 检查MTU变化，模拟onConnectionUpdated
      log('检测2: 模拟onConnectionUpdated - 检查连接参数');
      try {
        int currentMtu = await d!.mtu.first.timeout(Duration(seconds: 2));
        if (currentMtu != _currentMtu) {
          log('❌ MTU变化检测: $_currentMtu -> $currentMtu');
          _handleMtuOrConnectionParameterChange('模拟_onConnectionUpdated_MTU变化');
        } else {
          log('✅ MTU状态正常: $currentMtu');
        }
      } catch (e) {
        log('❌ MTU检查异常，可能连接参数变化: $e');
        triggerServiceChangeDetection(reason: '模拟_onConnectionUpdated_异常');
      }
      
      // 检测3: 深度notify状态检查
      log('检测3: 深度notify状态检查');
      if (dc != null) {
        try {
          // 尝试访问特征属性，如果失败说明可能服务已变化
          var properties = dc!.properties;
          var uuid = dc!.uuid.toString();
          log('特征属性检查成功: UUID=$uuid, 支持notify=${properties.notify}');
          
          if (!dc!.isNotifying) {
            log('❌ Notify未启用，可能需要重新设置');
            triggerServiceChangeDetection(reason: '模拟_notify状态异常');
          }
        } catch (e) {
          log('❌ 特征访问异常，服务可能已变化: $e');
          triggerServiceChangeDetection(reason: '模拟_特征访问异常');
        }
      } else {
        log('❌ 数据特征丢失');
        triggerServiceChangeDetection(reason: '模拟_特征丢失');
      }
      
      log('🎯 原生事件模拟检测完成');
    } catch (e) {
      log('🚨 模拟原生事件检测异常: $e');
    }
  }

  /// 强制触发服务变化检测(增强版) #强制触发服务变化检测
  Future<void> forceServiceChangeDetection() async {
    log('🔧 强制触发完整服务变化检测流程');
    
    // 方式1: 直接触发
    triggerServiceChangeDetection(reason: '手动强制触发');
    
    // 等待1秒
    await Future.delayed(Duration(seconds: 1));
    
    // 方式2: 模拟原生事件
    await simulateNativeServiceChangeEvents();
    
    // 等待2秒
    await Future.delayed(Duration(seconds: 2));
    
    // 方式3: 强制notify检查
    await checkAndRecoverNotifyState();
    
    log('🎉 强制服务变化检测流程完成');
  }

  /// 设置原生事件桥接(新增) #原生事件桥接
  void _setupNativeEventBridge() {
    if (_nativeEventBridgeSetup) return;
    
    try {
      _nativeEventChannel.setMethodCallHandler((call) async {
        switch (call.method) {
          case 'onServiceChanged':
            String deviceId = call.arguments?['deviceId'] ?? 'unknown';
            log('🔥 收到原生onServiceChanged事件: $deviceId');
            // 🚀 立即强制重新设置notify，不做任何检查
            await _immediateForceNotifyResetup(deviceId, 'onServiceChanged');
            break;
            
          case 'onConnectionUpdated':
            var args = call.arguments as Map<dynamic, dynamic>? ?? {};
            String deviceId = args['deviceId'] ?? 'unknown';
            int interval = args['interval'] ?? 0;
            int latency = args['latency'] ?? 0;
            int timeout = args['timeout'] ?? 0;
            int status = args['status'] ?? 0;
            
            log('🔥 收到原生onConnectionUpdated事件: $deviceId (interval=$interval, latency=$latency, timeout=$timeout, status=$status)');
            // 连接参数变化也需要重新设置notify
            await _immediateForceNotifyResetup(deviceId, 'onConnectionUpdated');
            break;
            
          case 'onMtuChanged':
            var args = call.arguments as Map<dynamic, dynamic>? ?? {};
            String deviceId = args['deviceId'] ?? 'unknown';
            int mtu = args['mtu'] ?? 0;
            int status = args['status'] ?? 0;
            
            log('🔥 收到原生onMtuChanged事件: $deviceId (mtu=$mtu, status=$status)');
            if (status == 0) { // GATT_SUCCESS
              _currentMtu = mtu;
              await _immediateForceNotifyResetup(deviceId, 'onMtuChanged');
            }
            break;
            
          default:
            log('未知的原生事件: ${call.method}');
        }
      });
      
      _nativeEventBridgeSetup = true;
      log('✅ 原生事件桥接设置成功');
      
      // 通知Android端Flutter已准备好接收事件
      _nativeEventChannel.invokeMethod('flutterReady');
    } catch (e) {
      log('❌ 设置原生事件桥接失败: $e');
    }
  }

  /// 立即强制重新设置notify(新增) #立即强制重设notify
  Future<void> _immediateForceNotifyResetup(String deviceId, String reason) async {
    if (d == null) {
      log('设备为空，跳过$reason处理');
      return;
    }
    
    try {
      log('🚨 立即强制重新设置notify - 原因: $reason');
      
      // 步骤1: 强制清理所有状态，不管当前状态
      log('步骤1: 强制清理状态');
      try {
        _dataCharacteristicSubscription?.cancel();
        _dataCharacteristicSubscription = null;
      } catch (e) {
        log('清理监听异常(忽略): $e');
      }
      
      // 重置所有标志
      _isNotifyEnabled = false;
      _isSettingNotify = false;
      _isHandlingServiceChange = false;
      
      // 步骤2: 立即重新发现服务，不等待
      log('步骤2: 立即重新发现服务');
      List<BluetoothService> services = await d!.discoverServices().timeout(Duration(seconds: 5));
      log('重新发现了 ${services.length} 个服务');
      
      // 步骤3: 查找并强制重新设置notify
      bool notifySetupSuccess = false;
      for (var service in services) {
        if (service.uuid.toString().toLowerCase().contains(S_UUID)) {
          log('找到目标服务: ${service.uuid}');
          
          for (var characteristic in service.characteristics) {
            String uuid = characteristic.uuid.toString().toLowerCase();
            
            if (uuid.contains(D_UUID)) {
              log('找到数据特征: $uuid');
              dc = characteristic;
              
              // 🔥 关键：强制设置notify，完全忽略当前状态
              log('强制设置notify - 当前状态: ${characteristic.isNotifying}');
              
              // 如果已经是true，先设置为false再设置为true
              if (characteristic.isNotifying) {
                log('先关闭notify再重新启用');
                await characteristic.setNotifyValue(false);
                await Future.delayed(Duration(milliseconds: 200));
              }
              
              // 强制启用notify
              await characteristic.setNotifyValue(true);
              await Future.delayed(Duration(milliseconds: 300));
              
              // 验证设置结果
              if (characteristic.isNotifying) {
                log('✅ notify强制设置成功: ${characteristic.isNotifying}');
                
                // 重新建立监听
                _dataCharacteristicSubscription = characteristic.lastValueStream.listen(
                  _handleDataCharacteristic,
                  onError: (e) => log('数据监听错误: $e')
                );
                
                _isNotifyEnabled = true;
                notifySetupSuccess = true;
                log('✅ 数据监听已重新建立');
              } else {
                log('❌ notify强制设置失败: ${characteristic.isNotifying}');
              }
              break;
            }
            
            if (uuid.contains(C_UUID)) {
              cc = characteristic;
            }
          }
          break;
        }
      }
      
      if (notifySetupSuccess) {
        log('🎉 $reason 后notify重新设置成功');
        s.add(true);
        _updateBluetoothIconState();
        events.GlobalEvents.i.showSuccess('蓝牙服务已自动恢复');
      } else {
        log('🚨 $reason 后notify重新设置失败');
        events.GlobalEvents.i.showError('蓝牙服务恢复失败');
      }
      
    } catch (e) {
      log('🚨 立即强制重新设置notify异常: $e');
      // 如果失败，尝试简单重连作为备用方案
      log('使用简单重连作为备用方案');
      await simpleForceReconnect();
    }
  }

  /// 最简单的强制重连方法(新增) #简单强制重连
  Future<bool> simpleForceReconnect() async {
    if (d == null) {
      log('设备为空，无法重连');
      return false;
    }
    
    try {
      log('🔧 开始简单强制重连流程');
      
      // 步骤1: 强制清理所有监听，不管状态如何
      log('步骤1: 强制清理所有监听');
      try {
        _dataCharacteristicSubscription?.cancel();
        _dataCharacteristicSubscription = null;
      } catch (e) {
        log('清理监听异常(忽略): $e');
      }
      
      // 步骤2: 重置所有状态标志
      _isNotifyEnabled = false;
      _isSettingNotify = false;
      dc = null;
      cc = null;
      
      // 步骤3: 等待一下让系统稳定
      await Future.delayed(Duration(milliseconds: 500));
      
      // 步骤4: 强制重新发现服务
      log('步骤2: 强制重新发现服务');
      List<BluetoothService> services = await d!.discoverServices();
      log('发现 ${services.length} 个服务');
      
      // 步骤5: 重新查找并设置特征
      bool found = false;
      for (var service in services) {
        if (service.uuid.toString().toLowerCase().contains(S_UUID)) {
          log('找到目标服务: ${service.uuid}');
          
          for (var characteristic in service.characteristics) {
            String uuid = characteristic.uuid.toString().toLowerCase();
            
            if (uuid.contains(D_UUID)) {
              log('找到数据特征: $uuid');
              dc = characteristic;
              
              // 🔧 关键：不检查isNotifying状态，直接强制设置
              log('强制设置notify，不检查当前状态');
              await characteristic.setNotifyValue(true);
              await Future.delayed(Duration(milliseconds: 300));
              
              // 设置监听
              _dataCharacteristicSubscription = characteristic.lastValueStream.listen(
                _handleDataCharacteristic,
                onError: (e) => log('数据监听错误: $e')
              );
              
              log('数据特征notify设置完成');
            }
            
            if (uuid.contains(C_UUID)) {
              log('找到命令特征: $uuid');
              cc = characteristic;
            }
          }
          
          found = true;
          break;
        }
      }
      
      if (found && dc != null && cc != null) {
        _isNotifyEnabled = true;
        s.add(true);
        log('✅ 简单强制重连成功');
        return true;
      } else {
        log('❌ 简单强制重连失败：未找到必要特征');
        return false;
      }
      
    } catch (e) {
      log('❌ 简单强制重连异常: $e');
      return false;
    }
  }

  /// 超简单的手动重连API(新增) #超简单重连API
  Future<void> easyReconnect() async {
    log('🚀 启动超简单重连');
    
    // 方式1: 尝试简单强制重连
    bool success = await simpleForceReconnect();
    
    if (!success) {
      log('简单重连失败，尝试完整重连');
      // 方式2: 如果失败，尝试完整的强制检测
      await forceServiceChangeDetection();
    }
    
    log('🎯 超简单重连流程完成，成功: $success');
  }

  /// 测试原生事件桥接(新增调试方法) #测试原生事件桥接
  Future<Map<String, dynamic>> testNativeEventBridge() async {
    var testResult = <String, dynamic>{};
    var startTime = DateTime.now();
    
    try {
      log('🧪 开始测试原生事件桥接');
      testResult['test_start_time'] = startTime.toString();
      testResult['native_bridge_setup'] = _nativeEventBridgeSetup;
      
      // 测试1: 检查MethodChannel是否设置
      log('步骤1: 检查MethodChannel设置状态');
      testResult['method_channel_setup'] = _nativeEventBridgeSetup;
      
      // 测试2: 尝试调用Android端方法
      log('步骤2: 尝试调用Android端flutterReady方法');
      try {
        var result = await _nativeEventChannel.invokeMethod('flutterReady');
        testResult['flutter_ready_call'] = result;
        log('flutterReady调用成功: $result');
      } catch (e) {
        testResult['flutter_ready_error'] = e.toString();
        log('flutterReady调用失败: $e');
      }
      
      // 测试3: 模拟等待原生事件
      log('步骤3: 等待5秒观察是否有原生事件到达');
      int eventCount = 0;
      
      // 设置临时事件计数器
      _nativeEventChannel.setMethodCallHandler((call) async {
        eventCount++;
        log('🎯 测试期间收到原生事件: ${call.method}');
        testResult['received_events'] = eventCount;
        
        // 恢复原来的处理器
        _setupNativeEventBridge();
      });
      
      await Future.delayed(Duration(seconds: 5));
      testResult['events_received_count'] = eventCount;
      
      // 恢复原来的事件处理器
      _setupNativeEventBridge();
      
      // 测试4: 检查设备连接状态
      testResult['device_connected'] = d?.isConnected ?? false;
      testResult['device_id'] = d?.remoteId.toString() ?? 'null';
      
      // 计算测试总时间
      var endTime = DateTime.now();
      testResult['total_test_time_ms'] = endTime.difference(startTime).inMilliseconds;
      testResult['test_success'] = _nativeEventBridgeSetup;
      
      log('🎉 原生事件桥接测试完成');
      log('桥接设置状态: ${_nativeEventBridgeSetup}');
      log('收到事件数量: $eventCount');
      
    } catch (e) {
      log('🚨 原生事件桥接测试异常: $e');
      testResult['test_error'] = e.toString();
      testResult['test_success'] = false;
    }
    
    return testResult;
  }

  /// 手动触发原生事件测试(新增) #手动触发原生事件测试
  Future<void> manualTriggerNativeEventTest() async {
    log('🔧 手动触发原生事件测试');
    
    if (d == null || !d!.isConnected) {
      log('设备未连接，无法进行原生事件测试');
      return;
    }
    
    try {
      // 模拟onServiceChanged事件
      log('模拟onServiceChanged事件');
      await _immediateForceNotifyResetup(d!.remoteId.toString(), '手动测试_onServiceChanged');
      
      await Future.delayed(Duration(seconds: 2));
      
      // 模拟onConnectionUpdated事件
      log('模拟onConnectionUpdated事件');
      await _immediateForceNotifyResetup(d!.remoteId.toString(), '手动测试_onConnectionUpdated');
      
      log('✅ 手动原生事件测试完成');
    } catch (e) {
      log('❌ 手动原生事件测试失败: $e');
    }
  }

  /// 启动数据监控和自动恢复(新增) #数据监控恢复
  void startDataMonitoringAndAutoRecover() {
    // 取消之前的定时器
    _dataMonitorTimer?.cancel();
    
    log('🔍 启动数据监控和自动恢复机制');
    
    _dataMonitorTimer = Timer.periodic(Duration(seconds: 8), (timer) async {
      if (d == null || !d!.isConnected) {
        log('设备未连接，跳过数据监控');
        return;
      }
      
      // 检查数据中断
      bool needRecover = checkIfDataInterrupted();
      
      if (needRecover) {
        log('🚨 检测到数据中断，启动自动恢复');
        try {
          bool recovered = await simpleForceReconnect();
          if (recovered) {
            log('✅ 自动恢复成功');
            events.GlobalEvents.i.showSuccess('数据传输已恢复');
          } else {
            log('❌ 自动恢复失败');
            events.GlobalEvents.i.showWarning('数据传输恢复失败');
          }
        } catch (e) {
          log('自动恢复异常: $e');
        }
      }
    });
  }

  /// 检查数据是否中断(公共方法) #检查数据中断
  bool checkIfDataInterrupted() {
    DateTime now = DateTime.now();
    
    // 检查1: 最后数据时间超过30秒
    if (_lastDataTime != null) {
      int timeSinceLastData = now.difference(_lastDataTime!).inSeconds;
      if (timeSinceLastData > 300) {
        log('数据中断检查: 超过30秒未收到数据 (${timeSinceLastData}秒)');
        return true;
      }
    }
    
    // 检查2: notify状态异常
    if (dc != null && !dc!.isNotifying) {
      log('数据中断检查: notify状态异常 (${dc!.isNotifying})');
      return true;
    }
    
    // 检查3: 监听订阅丢失
    if (_dataCharacteristicSubscription == null) {
      log('数据中断检查: 数据监听订阅丢失');
      return true;
    }
    
    return false;
  }
  
  /// 获取最后数据时间(公共getter) #获取最后数据时间
  DateTime? get lastDataTime => _lastDataTime;

  /// 停止数据监控(新增) #停止数据监控
  void stopDataMonitoring() {
    _dataMonitorTimer?.cancel();
    _dataMonitorTimer = null;
    log('数据监控已停止');
  }

  /// 直接上传手表日志数据 #直接上传手表日志
  void _uploadWatchLogDirectly(Map<String, dynamic> logData) async {
    try {
      log('处理手表日志并直接上传');
      
      // 确保包含设备SN
      if (logData['data'] != null && !logData['data'].containsKey('deviceSn')) {
        if (global.deviceSn.isNotEmpty) {
          logData['data']['deviceSn'] = global.deviceSn;
          log('添加设备序列号到日志数据: ${global.deviceSn}');
        }
      }
      
      _lastDataTime = DateTime.now();
      
      log('手表日志上传前结构: ${json.encode(logData).substring(0, min(300, json.encode(logData).length))}...');
      
      // 调用API上传日志
      ApiService().uploadWatchLog(logData).then((ok) {
        log('watch_log上传${ok ? "成功" : "失败"}');
      });
      
      // 同时在蓝牙调试页面显示日志
      _addLogToDebugPage(logData['data']);
      
    } catch (e) {
      log('直接上传手表日志失败: $e');
    }
  }
  
  /// 添加日志到蓝牙调试页面 #添加日志到调试页面
  void _addLogToDebugPage(Map<String, dynamic> logData) {
    try {
      if (logData != null) {
        String logLevel = logData['level'] ?? 'INFO';
        String logContent = logData['content'] ?? '';
        String timestamp = logData['timestamp'] ?? '';
        String deviceSn = logData['deviceSn'] ?? '';
        
        String formattedLog = '[$timestamp] [$logLevel] [$deviceSn] $logContent';
        
        // 这里可以添加到调试页面的日志显示
        // 暂时通过log输出
        log('蓝牙调试页面日志: $formattedLog');
      }
    } catch (e) {
      log('添加日志到调试页面失败: $e');
    }
  }

  /// 处理日志数据 #处理日志数据
  void _handleLogData(Map<String, dynamic> logData) {
    try {
      log('处理手表日志数据: $logData');
      
      String deviceSn = logData['deviceSn']?.toString() ?? '';
      String timestamp = logData['timestamp']?.toString() ?? '';
      String level = logData['level']?.toString() ?? 'INFO';
      String content = logData['content']?.toString() ?? '';
      
      // 添加到调试页面显示
      _addLogToDebugPage(logData);
      
      // 记录到控制台
      log('[$timestamp][$level][$deviceSn] $content');
    } catch (e) {
      log('处理日志数据失败: $e');
    }
  }
}
  
  