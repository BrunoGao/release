import 'package:flutter/material.dart';
import 'lib/services/bluetooth_service.dart';
import 'dart:async';

/// 原生事件桥接测试工具 #测试工具
class NativeEventBridgeTest {
  static final BleSvc _ble = BleSvc.i;

  /// 完整测试流程 #完整测试
  static Future<void> runFullTest() async {
    print('🧪 开始原生事件桥接完整测试');
    
    try {
      // 测试1: 基础桥接功能
      print('\n📱 测试1: 基础桥接功能');
      var bridgeResult = await _ble.testNativeEventBridge();
      _printTestResult('桥接功能', bridgeResult);
      
      // 测试2: 手动触发事件
      print('\n🔧 测试2: 手动触发事件处理');
      await _ble.manualTriggerNativeEventTest();
      
      // 测试3: 简单重连功能
      print('\n🚀 测试3: 简单重连功能');
      bool simpleResult = await _ble.simpleForceReconnect();
      print('简单重连结果: ${simpleResult ? "成功" : "失败"}');
      
      // 测试4: 超简单重连API
      print('\n⚡ 测试4: 超简单重连API');
      await _ble.easyReconnect();
      
      // 测试5: 智能检测状态
      print('\n📊 测试5: 智能检测状态');
      var status = _ble.intelligentDetectionStatus;
      _printStatus(status);
      
      // 测试6: 完整状态报告
      print('\n📋 测试6: 完整状态报告');
      var fullReport = _ble.getFullStatusReport();
      _printFullReport(fullReport);
      
      print('\n✅ 原生事件桥接完整测试完成');
      
    } catch (e) {
      print('❌ 测试过程异常: $e');
    }
  }
  
  /// 打印测试结果 #打印结果
  static void _printTestResult(String testName, Map<String, dynamic> result) {
    print('--- $testName 测试结果 ---');
    result.forEach((key, value) {
      print('  $key: $value');
    });
  }
  
  /// 打印智能检测状态 #打印状态
  static void _printStatus(Map<String, dynamic> status) {
    print('--- 智能检测状态 ---');
    print('  服务变化处理中: ${status['isHandlingServiceChange']}');
    print('  服务变化次数: ${status['serviceChangeCount']}');
    print('  连接更新次数: ${status['connectionUpdateCount']}');
    print('  上次服务变化: ${status['lastServiceChangeTime'] ?? "无"}');
    print('  notify启用: ${status['notifyEnabled']}');
    print('  当前MTU: ${status['currentMtu']}');
    print('  设备连接: ${status['deviceConnected']}');
    print('  健康服务可用: ${status['healthServiceAvailable']}');
  }
  
  /// 打印完整状态报告 #打印报告
  static void _printFullReport(Map<String, dynamic> report) {
    print('--- 完整状态报告 ---');
    print('时间戳: ${report['timestamp']}');
    
    var deviceInfo = report['device_info'];
    print('设备信息:');
    print('  连接状态: ${deviceInfo['connected']}');
    print('  设备ID: ${deviceInfo['device_id']}');
    print('  MTU大小: ${deviceInfo['mtu']}');
    
    var characteristics = report['characteristics'];
    print('特征状态:');
    print('  数据特征存在: ${characteristics['data_char_exists']}');
    print('  命令特征存在: ${characteristics['command_char_exists']}');
    print('  notify启用: ${characteristics['notify_enabled']}');
    print('  订阅存在: ${characteristics['subscription_exists']}');
    
    var internalStates = report['internal_states'];
    print('内部状态:');
    print('  notify标志: ${internalStates['notify_enabled_flag']}');
    print('  设置中标志: ${internalStates['setting_notify_flag']}');
    print('  处理服务变化: ${internalStates['handling_service_change']}');
    print('  GATT操作中: ${internalStates['gatt_operation_in_progress']}');
  }
  
  /// 快速连接测试 #快速测试
  static Future<bool> quickConnectTest(String deviceId) async {
    print('🔗 开始快速连接测试: $deviceId');
    
    try {
      // 连接设备
      bool connected = await _ble.connect(deviceId);
      if (!connected) {
        print('❌ 设备连接失败');
        return false;
      }
      
      print('✅ 设备连接成功');
      
      // 等待2秒让服务稳定
      await Future.delayed(Duration(seconds: 2));
      
      // 检查notify状态
      bool notifyOk = await _ble.checkAndRecoverNotifyState();
      print('Notify状态检查: ${notifyOk ? "正常" : "异常"}');
      
      return notifyOk;
    } catch (e) {
      print('❌ 快速连接测试异常: $e');
      return false;
    }
  }
  
  /// 监听连接事件 #监听事件
  static void startEventMonitoring() {
    print('👂 开始监听连接事件');
    
    // 监听连接状态变化
    _ble.connectionStateStream.listen((connected) {
      print('🔗 连接状态变化: ${connected ? "已连接" : "已断开"}');
    });
    
    // 监听健康数据
    _ble.healthDataStream.listen((data) {
      print('❤️ 收到健康数据: ${data['type']}');
    });
    
    // 监听设备信息
    _ble.deviceInfoStream.listen((data) {
      print('📱 收到设备信息: ${data['type']}');
    });
    
    // 监听日志
    _ble.logStream.listen((log) {
      if (log.contains('onServiceChanged') || 
          log.contains('notify') || 
          log.contains('重连')) {
        print('📝 重要日志: $log');
      }
    });
  }
}

/// 测试用的Widget #测试Widget
class NativeEventTestPage extends StatefulWidget {
  @override
  _NativeEventTestPageState createState() => _NativeEventTestPageState();
}

class _NativeEventTestPageState extends State<NativeEventTestPage> {
  String _testResult = '准备测试...';
  bool _testing = false;
  
  @override
  void initState() {
    super.initState();
    NativeEventBridgeTest.startEventMonitoring();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('原生事件桥接测试')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('测试结果:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 10),
            Expanded(
              child: Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SingleChildScrollView(
                  child: Text(_testResult, style: TextStyle(fontFamily: 'monospace')),
                ),
              ),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _testing ? null : _runFullTest,
              child: Text(_testing ? '测试中...' : '运行完整测试'),
            ),
            SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _testing ? null : _testBridge,
                    child: Text('测试桥接'),
                  ),
                ),
                SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _testing ? null : _testReconnect,
                    child: Text('测试重连'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  void _runFullTest() async {
    setState(() {
      _testing = true;
      _testResult = '开始完整测试...\n';
    });
    
    try {
      await NativeEventBridgeTest.runFullTest();
      setState(() {
        _testResult += '✅ 完整测试完成\n';
      });
    } catch (e) {
      setState(() {
        _testResult += '❌ 测试失败: $e\n';
      });
    } finally {
      setState(() => _testing = false);
    }
  }
  
  void _testBridge() async {
    setState(() {
      _testing = true;
      _testResult = '测试原生事件桥接...\n';
    });
    
    try {
      var result = await BleSvc.i.testNativeEventBridge();
      setState(() {
        _testResult += '桥接测试结果: ${result['test_success']}\n';
        _testResult += 'MethodChannel设置: ${result['method_channel_setup']}\n';
        _testResult += '接收事件数: ${result['events_received_count']}\n';
      });
    } catch (e) {
      setState(() {
        _testResult += '❌ 桥接测试失败: $e\n';
      });
    } finally {
      setState(() => _testing = false);
    }
  }
  
  void _testReconnect() async {
    setState(() {
      _testing = true;
      _testResult = '测试简单重连...\n';
    });
    
    try {
      await BleSvc.i.easyReconnect();
      setState(() {
        _testResult += '✅ 简单重连完成\n';
      });
    } catch (e) {
      setState(() {
        _testResult += '❌ 重连测试失败: $e\n';
      });
    } finally {
      setState(() => _testing = false);
    }
  }
}

/// 简化的数据监控测试工具 #简化测试工具
class DataMonitoringTest {
  static final BleSvc _ble = BleSvc.i;

  /// 测试数据监控和自动恢复 #测试数据监控
  static Future<Map<String, dynamic>> testDataMonitoring() async {
    var testResult = <String, dynamic>{};
    var startTime = DateTime.now();
    
    try {
      print('🧪 开始测试数据监控和自动恢复');
      testResult['test_start_time'] = startTime.toString();
      
      // 测试1: 检查设备连接状态
      bool deviceConnected = _ble.d?.isConnected ?? false;
      testResult['device_connected'] = deviceConnected;
      print('设备连接状态: $deviceConnected');
      
      if (!deviceConnected) {
        testResult['error'] = '设备未连接，无法测试';
        testResult['test_success'] = false;
        return testResult;
      }
      
      // 测试2: 手动触发简单重连
      print('测试简单重连功能');
      bool reconnectResult = await _ble.simpleForceReconnect();
      testResult['simple_reconnect_success'] = reconnectResult;
      print('简单重连结果: $reconnectResult');
      
      // 测试3: 测试超简单重连API
      print('测试超简单重连API');
      await _ble.easyReconnect();
      testResult['easy_reconnect_completed'] = true;
      print('超简单重连完成');
      
      // 测试4: 启动数据监控
      print('启动数据监控');
      _ble.startDataMonitoringAndAutoRecover();
      testResult['monitoring_started'] = true;
      
      // 等待几秒观察监控效果
      await Future.delayed(Duration(seconds: 10));
      
      // 测试5: 最终状态检查
      bool finalConnected = _ble.d?.isConnected ?? false;
      bool finalNotifyEnabled = _ble.dc?.isNotifying ?? false;
      testResult['final_connected'] = finalConnected;
      testResult['final_notify_enabled'] = finalNotifyEnabled;
      
      // 计算测试总时间
      var endTime = DateTime.now();
      testResult['total_test_time_ms'] = endTime.difference(startTime).inMilliseconds;
      testResult['test_success'] = reconnectResult && finalConnected && finalNotifyEnabled;
      
      print('🎉 数据监控测试完成');
      print('最终结果: ${testResult['test_success'] ? "成功" : "失败"}');
      
    } catch (e) {
      print('🚨 数据监控测试异常: $e');
      testResult['test_error'] = e.toString();
      testResult['test_success'] = false;
    }
    
    return testResult;
  }
  
  /// 持续监控数据传输状态 #持续监控
  static void startContinuousMonitoring() {
    print('👂 开始持续监控数据传输状态');
    
    Timer.periodic(Duration(seconds: 5), (timer) {
      if (_ble.d == null || !_ble.d!.isConnected) {
        print('设备未连接，停止监控');
        timer.cancel();
        return;
      }
      
      DateTime now = DateTime.now();
      String status = '';
      
      // 检查连接状态
      status += '连接: ${_ble.d!.isConnected ? "✅" : "❌"}';
      
      // 检查notify状态
      if (_ble.dc != null) {
        status += ', Notify: ${_ble.dc!.isNotifying ? "✅" : "❌"}';
      } else {
        status += ', Notify: ❌(特征未找到)';
      }
      
      // 检查数据接收
      if (_ble.lastDataTime != null) {
        int secondsSinceLastData = now.difference(_ble.lastDataTime!).inSeconds;
        status += ', 上次数据: ${secondsSinceLastData}秒前';
        
        if (secondsSinceLastData > 30) {
          status += ' ⚠️数据中断';
        }
      } else {
        status += ', 上次数据: 无';
      }
      
      print('📊 状态监控: $status');
      
      // 如果检测到问题，自动尝试恢复
      if (_ble.checkIfDataInterrupted()) {
        print('🔧 检测到问题，触发自动恢复');
        _ble.easyReconnect().then((_) {
          print('自动恢复尝试完成');
        });
      }
    });
  }
} 