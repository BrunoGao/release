import 'dart:async';
import 'dart:convert';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class WatchBluetoothService {
  final _bluetoothLogStream = StreamController<String>.broadcast();
  Stream<String> get bluetoothLogStream => _bluetoothLogStream.stream;
  
  BluetoothCharacteristic? _dataCharacteristic;
  BluetoothCharacteristic? _commandCharacteristic;
  
  void _log(String message) {
    final timestamp = DateTime.now().toString().split('.')[0];
    _bluetoothLogStream.add('[$timestamp] $message');
  }
  
  Future<bool> setNotifyValue(BluetoothCharacteristic characteristic, bool enable) async {
    try {
      if (!characteristic.properties.notify && !characteristic.properties.indicate) {
        _log('特征不支持notify/indicate: ${characteristic.uuid}');
        return false;
      }
      
      int retryCount = 0;
      while (retryCount < 3) {
        try {
          await characteristic.setNotifyValue(enable);
          _log('特征notify配置成功: ${characteristic.uuid}, enable=$enable');
          return true;
        } catch (e) {
          retryCount++;
          _log('特征notify配置失败(第$retryCount次): ${characteristic.uuid}, $e');
          if (retryCount < 3) {
            await Future.delayed(Duration(milliseconds: 500)); 
          }
        }
      }
      return false;
    } catch (e) {
      _log('setNotifyValue异常: $e');
      return false;
    }
  }

  Future<bool> _configureCharacteristics(BluetoothDevice device) async {
    try {
      _log('开始配置特征...');
      bool dataConfigured = false;
      bool commandConfigured = false;
      
      for (var service in device.services) {
        if (service.uuid.toString().toUpperCase() == '1887') {
          _log('找到目标服务: ${service.uuid}');
          for (var characteristic in service.characteristics) {
            _log('特征: ${characteristic.uuid}');
            _log('属性: ${characteristic.properties}');
            
            if (characteristic.uuid.toString().toUpperCase() == 'FD10') {
              _log('找到数据特征: ${characteristic.uuid}');
              if (await setNotifyValue(characteristic, true)) {
                dataConfigured = true;
                _dataCharacteristic = characteristic;
                _log('数据特征notify配置成功');
              }
            } else if (characteristic.uuid.toString().toUpperCase() == 'FD11') {
              _log('找到命令特征: ${characteristic.uuid}');
              commandConfigured = true;
              _commandCharacteristic = characteristic;
            }
          }
        }
      }
      
      if (!dataConfigured || !commandConfigured) {
        _log('特征配置不完整: data=$dataConfigured, command=$commandConfigured');
        return false;
      }
      
      _log('所有特征配置完成');
      return true;
    } catch (e) {
      _log('特征配置异常: $e');
      return false;
    }
  }

  Future<bool> connectToDevice(BluetoothDevice device) async {
    try {
      _log('开始连接设备: ${device.remoteId}');
      int retryCount = 0;
      while (retryCount < 3) {
        try {
          await device.connect(autoConnect: false);
          _log('设备连接成功');
          
          await Future.delayed(Duration(milliseconds: 1000)); 
          await device.discoverServices();
          _log('服务发现完成');
          
          await Future.delayed(Duration(milliseconds: 500)); 
          if (await _configureCharacteristics(device)) {
            _log('特征配置成功，连接完成');
            return true;
          }
          
          retryCount++;
          _log('特征配置失败，准备重试(第$retryCount次)');
          await device.disconnect();
          await Future.delayed(Duration(seconds: 1));
        } catch (e) {
          retryCount++;
          _log('连接异常(第$retryCount次): $e');
          if (retryCount < 3) {
            await Future.delayed(Duration(seconds: 1));
          }
        }
      }
      _log('连接失败，已重试3次');
      return false;
    } catch (e) {
      _log('连接流程异常: $e');
      return false;
    }
  }

  Map<String, dynamic> _parseDeviceData(Map<String, dynamic> data) {
    final result = data['data'] as Map<String, dynamic>;
    _log('设备数据解析结果: $result');
    return result;
  }

  Map<String, dynamic> _parseHealthData(Map<String, dynamic> data) {
    final result = {'data': data['data']['data'] as Map<String, dynamic>};
    _log('健康数据解析结果: $result');
    return result;
  }

  void _processReceivedData(List<int> data) {
    try {
      final jsonStr = String.fromCharCodes(data);
      final jsonData = json.decode(jsonStr);
      final type = jsonData['type'] as String;
      
      _log('收到原始数据: $jsonData');
      
      if (type == 'device') {
        final deviceData = _parseDeviceData(jsonData);
        _log('准备上传设备数据: $deviceData');
        _uploadToServer(deviceData);
      } else if (type == 'health') {
        final healthData = _parseHealthData(jsonData);
        _log('准备上传健康数据: $healthData');
        _uploadToServer(healthData);
      }
    } catch (e) {
      _log('数据解析异常: $e');
    }
  }

  Future<void> _uploadToServer(Map<String, dynamic> data) async {
    try {
      _log('开始上传数据: $data');
      // TODO: 实现服务器上传逻辑
      _log('数据上传完成');
    } catch (e) {
      _log('数据上传异常: $e');
    }
  }
} 