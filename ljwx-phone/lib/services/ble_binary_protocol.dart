import 'dart:convert';
import 'dart:typed_data';
import 'dart:math'; // 添加math库导入
import 'package:flutter/foundation.dart';
import '../global.dart';
import '../global.dart' as global; // 添加global别名导入
import 'dart:io';
import 'package:intl/intl.dart'; // 添加时间格式化支持

/// 二进制TLV协议处理器v1.2 #BLE二进制协议核心类
class BleBinaryProtocol {
  static final BleBinaryProtocol i = BleBinaryProtocol._();
  BleBinaryProtocol._();
  
  // 协议版本升级到v1.2
  static const int PROTOCOL_VERSION = 1;
  
  // 数据类型定义(与手表端保持一致)
  static const int TYPE_HEALTH_DATA = 0x01;
  static const int TYPE_DEVICE_INFO = 0x02;
  static const int TYPE_COMMON_EVENT = 0x03;
  static const int TYPE_MESSAGE = 0x04;
  static const int TYPE_CONFIG = 0x05;
  static const int TYPE_BLE_CONTROL = 0x06;
  static const int TYPE_LOG_DATA = 0x07; // 日志数据类型
  static const int TYPE_HEARTBEAT = 0xFE;
  static const int TYPE_DEBUG = 0xFF;
  
  // 数据格式
  static const int FORMAT_BINARY_TLV = 1;
  static const int FORMAT_JSON = 2;
  
  // 健康数据TLV字段ID(与手表端保持一致)
  static const int FIELD_ID = 0x01;
  static const int FIELD_UPLOAD_METHOD = 0x02;
  static const int FIELD_HEART_RATE = 0x03;
  static const int FIELD_BLOOD_OXYGEN = 0x04;
  static const int FIELD_BODY_TEMPERATURE = 0x05;
  static const int FIELD_BLOOD_PRESSURE_SYS = 0x06;
  static const int FIELD_BLOOD_PRESSURE_DIA = 0x07;
  static const int FIELD_STEP = 0x08;
  static const int FIELD_DISTANCE = 0x09;
  static const int FIELD_CALORIE = 0x0A;
  static const int FIELD_LATITUDE = 0x0B;
  static const int FIELD_LONGITUDE = 0x0C;
  static const int FIELD_ALTITUDE = 0x0D;
  static const int FIELD_STRESS = 0x0E;
  static const int FIELD_TIMESTAMP = 0x0F;
  static const int FIELD_SLEEP_DATA = 0x10; // 睡眠数据字段
  
  // 设备信息TLV字段ID(与手表端字段名保持一致)
  static const int DEV_SYSTEM_VERSION = 0x01; // "System Software Version"
  static const int DEV_WIFI_ADDRESS = 0x02; // "Wifi Address"
  static const int DEV_BLUETOOTH_ADDRESS = 0x03; // "Bluetooth Address"
  static const int DEV_IP_ADDRESS = 0x04; // "IP Address"
  static const int DEV_NETWORK_MODE = 0x05; // "Network Access Mode"
  static const int DEV_SERIAL_NUMBER = 0x06; // "SerialNumber"
  static const int DEV_DEVICE_NAME = 0x07; // "Device Name"
  static const int DEV_IMEI = 0x08; // "IMEI"
  static const int DEV_BATTERY_LEVEL = 0x09; // "batteryLevel"
  static const int DEV_VOLTAGE = 0x0A; // "voltage"
  static const int DEV_CHARGING_STATUS = 0x0B; // "chargingStatus"
  static const int DEV_WEAR_STATE = 0x0D; // "wearState"
  static const int DEV_TIMESTAMP = 0x0E; // "timestamp"
  
  // 通用事件TLV字段ID
  static const int EVENT_ACTION = 0x01;
  static const int EVENT_VALUE = 0x02;
  static const int EVENT_DEVICE_SN = 0x03;
  static const int EVENT_TIMESTAMP = 0x04;
  
  // 心跳包TLV字段ID
  static const int HB_TIMESTAMP = 0x01; // uint32时间戳
  static const int HB_BATTERY = 0x02; // uint8电量
  static const int HB_WEAR_STATE = 0x03; // uint8佩戴状态
  
  // 日志数据TLV字段ID
  static const int LOG_DEVICE_SN = 0x01; // 设备序列号
  static const int LOG_TIMESTAMP = 0x02; // 时间戳
  static const int LOG_LEVEL = 0x03; // 日志级别
  static const int LOG_CONTENT = 0x04; // 日志内容

  void log(String msg) {
    debugPrint("[BleBinaryProtocol] $msg");
    try { File(bleLogFile).writeAsStringSync("[BleBinaryProtocol] $msg\n", mode: FileMode.append); } catch (_) {}
  }

  /// 生成北京时间戳字符串 #生成北京时间戳
  String _generateBeijingTimestamp() {
    var now = DateTime.now().toUtc().add(Duration(hours: 8)); // 转换为北京时间
    return DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
  }
  
  /// 编码协议包 #编码协议包
  Uint8List encodeProtocolPacket(int type, int format, Uint8List payload) {
    var buffer = ByteData(5 + payload.length);
    int offset = 0;
    
    buffer.setUint8(offset++, PROTOCOL_VERSION); // version
    buffer.setUint8(offset++, type); // type
    buffer.setUint8(offset++, format); // format
    buffer.setUint16(offset, payload.length, Endian.big); // payloadLength (大端序)
    offset += 2;
    
    // 复制payload
    var result = Uint8List(5 + payload.length);
    result.setRange(0, 5, buffer.buffer.asUint8List());
    result.setRange(5, 5 + payload.length, payload);
    
    return result;
  }
  
  /// 解码协议包 #解码协议包
  Map<String, dynamic>? decodeProtocolPacket(Uint8List data) {
    if (data.length < 5) {
      log('协议包长度不足，需要至少5字节，实际: ${data.length}字节');
      return null;
    }
    
    try {
      var buffer = ByteData.sublistView(data);
      int offset = 0;
      
      int version = buffer.getUint8(offset++);
      int type = buffer.getUint8(offset++);
      int format = buffer.getUint8(offset++);
      int payloadLength = buffer.getUint16(offset, Endian.big);
      offset += 2;
      
      log('协议包解码 - 版本: $version, 类型: $type, 格式: $format, payload长度: $payloadLength');
      log('数据包总长度: ${data.length}, 包头长度: 5, 期望payload长度: $payloadLength');
      
      if (data.length < 5 + payloadLength) {
        log('payload长度不匹配，需要: ${5 + payloadLength}, 实际: ${data.length}');
        return null;
      }
      
      Uint8List payload = data.sublist(5, 5 + payloadLength);
      log('成功提取payload，实际长度: ${payload.length}');
      log('payload前20字节: ${payload.take(20).toList()}');
      
      return {
        'version': version,
        'type': type,
        'format': format,
        'payload': payload
      };
    } catch (e) {
      log('解码协议包失败: $e');
      return null;
    }
  }
  
  /// 编码健康数据为TLV格式(v1.2自动添加timestamp) #编码健康数据
  Uint8List encodeHealthDataTLV(Map<String, dynamic> healthData) {
    var buffer = <int>[];
    
    // 编码字符串字段
    _encodeTLVString(buffer, FIELD_ID, healthData['id'] ?? '');
    _encodeTLVString(buffer, FIELD_UPLOAD_METHOD, healthData['upload_method'] ?? 'bluetooth');
    _encodeTLVString(buffer, FIELD_BODY_TEMPERATURE, healthData['body_temperature'] ?? '');
    _encodeTLVString(buffer, FIELD_DISTANCE, healthData['distance'] ?? '');
    _encodeTLVString(buffer, FIELD_CALORIE, healthData['calorie'] ?? '');
    _encodeTLVString(buffer, FIELD_LATITUDE, healthData['latitude'] ?? '');
    _encodeTLVString(buffer, FIELD_LONGITUDE, healthData['longitude'] ?? '');
    _encodeTLVString(buffer, FIELD_ALTITUDE, healthData['altitude'] ?? '');
    
    // 编码整数字段
    _encodeTLVUint8(buffer, FIELD_HEART_RATE, _parseIntSafe(healthData['heart_rate'], 0));
    _encodeTLVUint8(buffer, FIELD_BLOOD_OXYGEN, _parseIntSafe(healthData['blood_oxygen'], 0));
    _encodeTLVUint8(buffer, FIELD_BLOOD_PRESSURE_SYS, _parseIntSafe(healthData['blood_pressure_systolic'], 0));
    _encodeTLVUint8(buffer, FIELD_BLOOD_PRESSURE_DIA, _parseIntSafe(healthData['blood_pressure_diastolic'], 0));
    _encodeTLVUint8(buffer, FIELD_STRESS, _parseIntSafe(healthData['stress'], 0));
    _encodeTLVUint16(buffer, FIELD_STEP, _parseIntSafe(healthData['step'], 0));
    
    // 编码睡眠数据字段
    _encodeTLVString(buffer, FIELD_SLEEP_DATA, healthData['sleepData'] ?? '');
    
    // v1.2自动添加北京时间戳
    String timestamp = healthData['timestamp']?.toString() ?? _generateBeijingTimestamp();
    _encodeTLVString(buffer, FIELD_TIMESTAMP, timestamp);
    
    return Uint8List.fromList(buffer);
  }
  
  /// 解码健康数据TLV格式(v1.2支持timestamp) #解码健康数据
  Map<String, dynamic> decodeHealthDataTLV(Uint8List data) {
    var result = <String, dynamic>{};
    int offset = 0;
    
    log('开始解码健康数据TLV，总数据长度: ${data.length}');
    
    while (offset < data.length) {
      if (offset + 2 > data.length) {
        log('数据不足，剩余字节: ${data.length - offset}，需要至少2字节');
        break;
      }
      
      int id = data[offset++];
      int length = data[offset++]; // 修改：改为1字节长度
      
      log('解码字段 ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 长度: $length, 当前偏移: ${offset - 2}');
      
      if (offset + length > data.length) {
        log('字段数据长度超出范围，需要: $length, 可用: ${data.length - offset}');
        break;
      }
      
      try {
        switch (id) {
          case FIELD_ID:
            result['id'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码ID字段: ${result['id']}');
            break;
          case FIELD_UPLOAD_METHOD:
            result['upload_method'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码上传方法: ${result['upload_method']}');
            break;
          case FIELD_HEART_RATE:
            result['heart_rate'] = data[offset].toString();
            log('解码心率: ${result['heart_rate']}');
            break;
          case FIELD_BLOOD_OXYGEN:
            result['blood_oxygen'] = data[offset].toString();
            log('解码血氧: ${result['blood_oxygen']}');
            break;
          case FIELD_BODY_TEMPERATURE:
            result['body_temperature'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码体温: ${result['body_temperature']}');
            break;
          case FIELD_BLOOD_PRESSURE_SYS:
            result['blood_pressure_systolic'] = data[offset].toString();
            log('解码收缩压: ${result['blood_pressure_systolic']}');
            break;
          case FIELD_BLOOD_PRESSURE_DIA:
            result['blood_pressure_diastolic'] = data[offset].toString();
            log('解码舒张压: ${result['blood_pressure_diastolic']}');
            break;
          case FIELD_STEP:
            result['step'] = ((data[offset] << 8) | data[offset + 1]).toString();
            log('解码步数: ${result['step']}');
            break;
          case FIELD_DISTANCE:
            result['distance'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码距离: ${result['distance']}');
            break;
          case FIELD_CALORIE:
            result['calorie'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码卡路里: ${result['calorie']}');
            break;
          case FIELD_LATITUDE:
            result['latitude'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码纬度: ${result['latitude']}');
            break;
          case FIELD_LONGITUDE:
            result['longitude'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码经度: ${result['longitude']}');
            break;
          case FIELD_ALTITUDE:
            result['altitude'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码海拔: ${result['altitude']}');
            break;
          case FIELD_STRESS:
            result['stress'] = data[offset].toString();
            log('解码压力: ${result['stress']}');
            break;
          case FIELD_TIMESTAMP: // v1.2新增timestamp字段解码
            result['timestamp'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码时间戳: ${result['timestamp']}');
            break;
          case FIELD_SLEEP_DATA: // 睡眠数据字段解码
            String sleepDataStr = utf8.decode(data.sublist(offset, offset + length));
            result['sleepData'] = _decodeSleepData(sleepDataStr);
            log('解码睡眠数据: ${result['sleepData']}');
            break;
          default:
            log('未知字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 跳过 $length 字节');
            break;
        }
      } catch (e) {
        log('解码字段ID 0x${id.toRadixString(16).padLeft(2, '0')} 时出错: $e');
      }
      
      offset += length;
    }
    
    log('健康数据TLV解码完成，共解码 ${result.length} 个字段: ${result.keys.toList()}');
    return result;
  }
  
  /// 编码设备信息为TLV格式(v1.2自动添加timestamp) #编码设备信息
  Uint8List encodeDeviceInfoTLV(Map<String, dynamic> deviceData) {
    var buffer = <int>[];
    
    _encodeTLVString(buffer, DEV_SYSTEM_VERSION, deviceData['system_version'] ?? '');
    _encodeTLVString(buffer, DEV_WIFI_ADDRESS, deviceData['wifi_address'] ?? '');
    _encodeTLVString(buffer, DEV_BLUETOOTH_ADDRESS, deviceData['bluetooth_address'] ?? '');
    _encodeTLVString(buffer, DEV_IP_ADDRESS, deviceData['ip_address'] ?? '');
    _encodeTLVString(buffer, DEV_SERIAL_NUMBER, deviceData['serial_number'] ?? '');
    _encodeTLVString(buffer, DEV_DEVICE_NAME, deviceData['device_name'] ?? '');
    _encodeTLVString(buffer, DEV_IMEI, deviceData['imei'] ?? '');
    _encodeTLVString(buffer, DEV_CHARGING_STATUS, deviceData['charging_status'] ?? '');
    // 注意：上传方法字段不在手表端设备信息协议中，已移除
    
    _encodeTLVUint8(buffer, DEV_NETWORK_MODE, _parseIntSafe(deviceData['network_mode'], 1));
    _encodeTLVUint8(buffer, DEV_BATTERY_LEVEL, _parseIntSafe(deviceData['battery_level'], 0));
    _encodeTLVUint8(buffer, DEV_WEAR_STATE, _parseIntSafe(deviceData['wear_state'], 0));
    _encodeTLVUint16(buffer, DEV_VOLTAGE, _parseIntSafe(deviceData['voltage'], 0));
    
    // v1.2自动添加北京时间戳
    String timestamp = deviceData['timestamp']?.toString() ?? _generateBeijingTimestamp();
    _encodeTLVString(buffer, DEV_TIMESTAMP, timestamp);
    
    return Uint8List.fromList(buffer);
  }
  
  /// 解码设备信息TLV格式(与手表端字段名保持一致) #解码设备信息
  Map<String, dynamic> decodeDeviceInfoTLV(Uint8List data) {
    var result = <String, dynamic>{};
    int offset = 0;
    
    log('开始解码设备信息TLV，总数据长度: ${data.length}');
    log('原始数据(前50字节): ${data.take(50).toList()}');
    
    // 检查数据是否以有效字段ID开始
    if (data.isNotEmpty) {
      int firstByte = data[0];
      log('第一个字节: 0x${firstByte.toRadixString(16).padLeft(2, '0')} (${firstByte})');
      
      // 如果第一个字节不是有效的设备信息字段ID，尝试修复数据
      if (firstByte < 0x01 || firstByte > 0x0E) {
        log('第一个字节不是有效字段ID，尝试解析为错误格式数据');
        
        // 尝试解析为部分UTF-8字符串格式(可能是SerialNumber等数据)
        try {
          String dataStr = utf8.decode(data);
          log('原始数据作为字符串: $dataStr');
          
          // 如果数据看起来像序列号
          if (dataStr.length > 5 && dataStr.contains(RegExp(r'^[A-Z0-9]+$'))) {
            result['SerialNumber'] = dataStr;
            log('从原始数据中提取序列号: $dataStr');
            return result;
          }
        } catch (e) {
          log('无法解析为UTF-8字符串: $e');
        }
        
        // 尝试寻找有效起始点
        for (int i = 0; i < data.length - 1; i++) {
          int id = data[i];
          if (id >= 0x01 && id <= 0x0E) {
            log('在偏移$i处找到可能的有效字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}');
            offset = i;
            break;
          }
        }
        
        // 如果仍未找到有效起始点，尝试作为原始数据处理
        if (offset == 0 && (firstByte < 0x01 || firstByte > 0x0E)) {
          log('无法找到有效TLV起始点，尝试作为原始数据解析');
          return _parseRawDeviceData(data);
        }
      }
    }
    
    while (offset < data.length) {
      if (offset + 2 > data.length) {
        log('数据不足，剩余字节: ${data.length - offset}，需要至少2字节');
        break;
      }
      
      int id = data[offset++];
      int length = data[offset++];
      
      log('解码字段 ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 长度: $length, 当前偏移: ${offset - 2}');
      
      if (offset + length > data.length) {
        log('字段数据长度超出范围，需要: $length, 可用: ${data.length - offset}');
        break;
      }
      
      try {
        switch (id) {
          case 0x01: // "System Software Version"
            result['system_version'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码系统版本: ${result['system_version']}');
            break;
          case 0x02: // "Wifi Address"
            result['Wifi Address'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码WiFi地址: ${result['Wifi Address']}');
            break;
          case 0x03: // "Bluetooth Address"
            result['Bluetooth Address'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码蓝牙地址: ${result['Bluetooth Address']}');
            break;
          case 0x04: // "IP Address"
            result['IP Address'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码IP地址: ${result['IP Address']}');
            break;
          case 0x05: // "Network Access Mode" (uint8)
            result['Network Access Mode'] = data[offset];
            log('解码网络模式: ${result['Network Access Mode']}');
            break;
          case 0x06: // "SerialNumber"
            result['SerialNumber'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码序列号: ${result['SerialNumber']}');
            break;
          case 0x07: // "Device Name"
            result['Device Name'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码设备名称: ${result['Device Name']}');
            break;
          case 0x08: // "IMEI"
            result['IMEI'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码IMEI: ${result['IMEI']}');
            break;
          case 0x09: // "batteryLevel" (uint8)
            result['batteryLevel'] = data[offset];
            log('解码电量: ${result['batteryLevel']}');
            break;
          case 0x0A: // "voltage" (uint16, 大端序)
            if (length >= 2) {
              result['voltage'] = (data[offset] << 8) | data[offset + 1];
            } else {
              result['voltage'] = data[offset];
            }
            log('解码电压: ${result['voltage']}');
            break;
          case 0x0B: // "chargingStatus"
            result['chargingStatus'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码充电状态: ${result['chargingStatus']}');
            break;
          case 0x0D: // "wearState" (uint8)
            result['wearState'] = data[offset];
            log('解码佩戴状态: ${result['wearState']}');
            break;
          case 0x0E: // "timestamp"
            result['timestamp'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码时间戳: ${result['timestamp']}');
            break;
          default:
            log('未知字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 跳过 $length 字节');
            // 输出未知字段的数据内容用于调试
            if (length <= 50) {
              var unknownData = data.sublist(offset, offset + length);
              if (_isUtf8Valid(unknownData)) {
                try {
                  String str = utf8.decode(unknownData);
                  log('未知字段内容(字符串): "$str"');
                } catch (_) {
                  log('未知字段内容(字节): ${unknownData.toList()}');
                }
              } else {
                log('未知字段内容(字节): ${unknownData.toList()}');
              }
            }
            break;
        }
      } catch (e) {
        log('解码字段ID 0x${id.toRadixString(16).padLeft(2, '0')} 时出错: $e');
      }
      
      offset += length;
    }
    
    log('设备信息TLV解码完成，共解码 ${result.length} 个字段: ${result.keys.toList()}');
    return result;
  }
  
  /// 解析原始设备数据(非TLV格式) #解析原始设备数据
  Map<String, dynamic> _parseRawDeviceData(Uint8List data) {
    var result = <String, dynamic>{};
    
    try {
      // 尝试解析为连续的字符串数据
      String dataStr = utf8.decode(data);
      log('原始设备数据字符串: $dataStr');
      
      // 根据常见的设备信息格式进行解析
      List<String> parts = dataStr.split('\x00'); // 尝试NULL分隔符
      if (parts.length == 1) {
        parts = dataStr.split('|'); // 尝试管道分隔符
      }
      
      if (parts.length > 1) {
        for (int i = 0; i < parts.length && i < 10; i++) {
          String part = parts[i].trim();
          if (part.isNotEmpty) {
            switch (i) {
              case 0:
                if (part.length > 5) result['serial_number'] = part;
                break;
              case 1:
                if (part.contains('.')) result['system_version'] = part;
                break;
              case 2:
                if (part.contains(':')) result['bluetooth_address'] = part;
                break;
              case 3:
                if (part.contains('.')) result['ip_address'] = part;
                break;
            }
          }
        }
      } else {
        // 单个字符串，可能是序列号
        if (dataStr.length > 5 && dataStr.contains(RegExp(r'^[A-Z0-9]+$'))) {
          result['serial_number'] = dataStr;
        }
      }
      
      log('从原始数据解析出字段: ${result.keys.toList()}');
    } catch (e) {
      log('解析原始设备数据失败: $e');
    }
    
    return result;
  }
  
  /// 检查字节数组是否为有效UTF-8 #检查UTF8
  bool _isUtf8Valid(Uint8List bytes) {
    try {
      utf8.decode(bytes);
      return true;
    } catch (_) {
      return false;
    }
  }
  
  /// 编码心跳包为TLV格式(v1.2新增) #编码心跳包
  Uint8List encodeHeartbeatTLV(Map<String, dynamic> heartbeatData) {
    var buffer = <int>[];
    
    // 秒级时间戳
    int timestamp = heartbeatData['timestamp'] ?? (DateTime.now().millisecondsSinceEpoch ~/ 1000);
    _encodeTLVUint32(buffer, HB_TIMESTAMP, timestamp);
    
    // 电量状态
    _encodeTLVUint8(buffer, HB_BATTERY, _parseIntSafe(heartbeatData['battery'], 0));
    
    // 佩戴状态
    _encodeTLVUint8(buffer, HB_WEAR_STATE, _parseIntSafe(heartbeatData['wear_state'], 0));
    
    return Uint8List.fromList(buffer);
  }
  
  /// 解码通用事件TLV格式(与手表端一致) #解码通用事件
  Map<String, dynamic> decodeCommonEventTLV(Uint8List data) {
    var result = <String, dynamic>{};
    int offset = 0;
    
    log('开始解码通用事件TLV，总数据长度: ${data.length}');
    
    while (offset < data.length) {
      if (offset + 2 > data.length) {
        log('数据不足，剩余字节: ${data.length - offset}，需要至少2字节');
        break;
      }
      
      int id = data[offset++];
      int length = data[offset++];
      
      log('解码字段 ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 长度: $length, 当前偏移: ${offset - 2}');
      
      if (offset + length > data.length) {
        log('字段数据长度超出范围，需要: $length, 可用: ${data.length - offset}');
        break;
      }
      
      try {
        switch (id) {
          case EVENT_ACTION: // 0x01
            result['action'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码事件动作: ${result['action']}');
            break;
          case EVENT_VALUE: // 0x02
            result['value'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码事件值: ${result['value']}');
            break;
          case EVENT_DEVICE_SN: // 0x03
            result['device_sn'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码设备序列号: ${result['device_sn']}');
            break;
          case EVENT_TIMESTAMP: // 0x04
            result['timestamp'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码时间戳: ${result['timestamp']}');
            break;
          default:
            log('未知事件字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 跳过 $length 字节');
            break;
        }
      } catch (e) {
        log('解码事件字段ID 0x${id.toRadixString(16).padLeft(2, '0')} 时出错: $e');
      }
      
      offset += length;
    }
    
    log('通用事件TLV解码完成，共解码 ${result.length} 个字段: ${result.keys.toList()}');
    return result;
  }
  
  /// 解码心跳包TLV格式(支持uint32时间戳) #解码心跳包
  Map<String, dynamic> decodeHeartbeatTLV(Uint8List data) {
    var result = <String, dynamic>{};
    int offset = 0;
    
    log('开始解码心跳包TLV，总数据长度: ${data.length}');
    
    while (offset < data.length) {
      if (offset + 2 > data.length) break;
      
      int id = data[offset++];
      int length = data[offset++];
      
      log('解码心跳字段 ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 长度: $length');
      
      if (offset + length > data.length) break;
      
      try {
        switch (id) {
          case HB_TIMESTAMP: // 0x01 - uint32秒级时间戳
            if (length == 4) {
              result['timestamp'] = (data[offset] << 24) | (data[offset + 1] << 16) | (data[offset + 2] << 8) | data[offset + 3];
              log('解码心跳时间戳(uint32): ${result['timestamp']}');
            } else {
              log('心跳时间戳长度异常，期望4字节，实际${length}字节');
            }
            break;
          case HB_BATTERY: // 0x02 - uint8电量
            result['battery'] = data[offset];
            log('解码心跳电量: ${result['battery']}%');
            break;
          case HB_WEAR_STATE: // 0x03 - uint8佩戴状态
            result['wear_state'] = data[offset];
            log('解码心跳佩戴状态: ${result['wear_state'] == 1 ? "已佩戴" : "未佩戴"}');
            break;
          default:
            log('未知心跳字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 跳过 $length 字节');
            break;
        }
      } catch (e) {
        log('解码心跳字段ID 0x${id.toRadixString(16).padLeft(2, '0')} 时出错: $e');
      }
      
      offset += length;
    }
    
    log('心跳包TLV解码完成，共解码 ${result.length} 个字段: ${result.keys.toList()}');
    return result;
  }
  
  /// 解码日志数据TLV格式 #解码日志数据
  Map<String, dynamic> decodeLogDataTLV(Uint8List data) {
    var result = <String, dynamic>{};
    int offset = 0;
    
    log('开始解码日志数据TLV，总数据长度: ${data.length}');
    
    while (offset < data.length) {
      if (offset + 2 > data.length) break;
      
      int id = data[offset++];
      int length = data[offset++];
      
      log('解码日志字段 ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 长度: $length');
      
      if (offset + length > data.length) break;
      
      try {
        switch (id) {
          case LOG_DEVICE_SN: // 0x01 - 设备序列号
            result['deviceSn'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码设备序列号: ${result['deviceSn']}');
            break;
          case LOG_TIMESTAMP: // 0x02 - uint32时间戳
            if (length == 4) {
              result['timestamp'] = (data[offset] << 24) | (data[offset + 1] << 16) | (data[offset + 2] << 8) | data[offset + 3];
              log('解码日志时间戳(uint32): ${result['timestamp']}');
            } else {
              log('日志时间戳长度异常，期望4字节，实际${length}字节');
            }
            break;
          case LOG_LEVEL: // 0x03 - 日志级别
            result['level'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码日志级别: ${result['level']}');
            break;
          case LOG_CONTENT: // 0x04 - 日志内容
            result['content'] = utf8.decode(data.sublist(offset, offset + length));
            log('解码日志内容: ${result['content'].substring(0, min<int>(50, result['content'].length))}...');
            break;
          default:
            log('未知日志字段ID: 0x${id.toRadixString(16).padLeft(2, '0')}, 跳过 $length 字节');
            break;
        }
      } catch (e) {
        log('解码日志字段ID 0x${id.toRadixString(16).padLeft(2, '0')} 时出错: $e');
      }
      
      offset += length;
    }
    
    log('日志数据TLV解码完成，共解码 ${result.length} 个字段: ${result.keys.toList()}');
    return result;
  }
  
  /// 分包数据 #分包处理
  List<Uint8List> splitPackets(Uint8List data, int mtu) {
    int headerSize = 5; // 协议头大小
    int maxPayloadSize = mtu - headerSize - 3; // 减去ATT开销
    
    if (data.length <= maxPayloadSize) {
      return [data]; // 无需分包
    }
    
    List<Uint8List> packets = [];
    int offset = 0;
    
    while (offset < data.length) {
      int remainingBytes = data.length - offset;
      int chunkSize = remainingBytes > maxPayloadSize ? maxPayloadSize : remainingBytes;
      
      packets.add(data.sublist(offset, offset + chunkSize));
      offset += chunkSize;
    }
    
    return packets;
  }
  
  /// 编码字符串TLV #编码字符串TLV
  void _encodeTLVString(List<int> buffer, int id, String value) {
    if (value.isEmpty) return;
    
    var bytes = utf8.encode(value);
    if (bytes.length > 255) {
      log('警告：字符串长度超过255字节，将被截断');
      bytes = Uint8List.fromList(bytes.take(255).toList());
    }
    
    buffer.add(id);
    buffer.add(bytes.length); // 修改：改为1字节长度
    buffer.addAll(bytes);
  }
  
  /// 编码8位整数TLV #编码8位整数TLV
  void _encodeTLVUint8(List<int> buffer, int id, int value) {
    buffer.add(id);
    buffer.add(1); // 修改：改为1字节长度
    buffer.add(value & 0xFF);
  }
  
  /// 编码16位整数TLV #编码16位整数TLV
  void _encodeTLVUint16(List<int> buffer, int id, int value) {
    buffer.add(id);
    buffer.add(2); // 修改：改为1字节长度
    buffer.add((value >> 8) & 0xFF); // 高字节
    buffer.add(value & 0xFF); // 低字节
  }
  
  /// 编码32位整数TLV(v1.2新增) #编码32位整数TLV
  void _encodeTLVUint32(List<int> buffer, int id, int value) {
    buffer.add(id);
    buffer.add(4); // 修改：改为1字节长度
    buffer.add((value >> 24) & 0xFF);
    buffer.add((value >> 16) & 0xFF);
    buffer.add((value >> 8) & 0xFF);
    buffer.add(value & 0xFF);
  }
  
  /// 安全解析整数 #安全解析整数
  int _parseIntSafe(dynamic value, int defaultValue) {
    if (value == null) return defaultValue;
    if (value is int) return value;
    if (value is String) {
      try {
        return int.parse(value);
      } catch (e) {
        return defaultValue;
      }
    }
    return defaultValue;
  }

  /// 修复损坏的Common Event JSON #修复事件JSON
  Map<String, dynamic> repairCommonEventJson(String jsonStr) {
    try {
      log('尝试修复损坏的Common Event JSON');
      log('原始JSON字符串: ${jsonStr.substring(0, min(200, jsonStr.length))}...');
      
      // 尝试直接解析，如果成功则无需修复
      try {
        var parsed = json.decode(jsonStr);
        if (parsed is Map) {
          log('JSON直接解析成功，无需修复');
          return Map<String, dynamic>.from(parsed);
        }
      } catch (e) {
        log('JSON直接解析失败: $e，开始修复');
      }
      
      // 智能提取字段值
      Map<String, dynamic> result = {};
      
             // 提取action字段 - 查找 "action":"值" 模式
       String? action = _extractJsonField(jsonStr, 'action');
      if (action != null) {
        // 清理action中的错误转义字符
        action = action.replaceAll(r'\"', '"').replaceAll(r'{', '').replaceAll(r'}', '');
        if (action.trim().isNotEmpty && action != 'action') {
          result['action'] = action.trim();
          log('成功提取action: ${result['action']}');
        }
      }
      
      // 提取value字段 - 特殊处理长字符串
      String? value = _extractJsonField(jsonStr, 'value');
      if (value != null) {
        value = value.replaceAll(r'\"', '"');
        // 移除尾部的 ",\"value\"" 模式
        if (value.contains('",')) {
          value = value.split('",')[0];
        }
        if (value.trim().isNotEmpty) {
          result['value'] = value.trim();
          log('成功提取value: ${result['value']}');
        }
      }
      
      // 提取device_sn字段
      String? deviceSn = _extractJsonField(jsonStr, 'device_sn');
      if (deviceSn != null) {
        deviceSn = deviceSn.replaceAll(r'\"', '"').replaceAll(',', '');
        // 提取纯数字部分
        RegExp numberPattern = RegExp(r'\d+');
        var match = numberPattern.firstMatch(deviceSn);
        if (match != null) {
          result['device_sn'] = match.group(0)!;
          log('成功提取device_sn: ${result['device_sn']}');
        }
      }
      
      // 提取timestamp字段
      String? timestamp = _extractJsonField(jsonStr, 'timestamp');
      if (timestamp != null) {
        timestamp = timestamp.replaceAll(r'\"', '"');
        if (timestamp.contains('-') && timestamp.contains(':')) {
          result['timestamp'] = timestamp.trim();
          log('成功提取timestamp: ${result['timestamp']}');
        }
      }
      
      // 如果没有timestamp，自动添加当前北京时间
      if (!result.containsKey('timestamp')) {
        var now = DateTime.now().toUtc().add(Duration(hours: 8));
        result['timestamp'] = DateFormat('yyyy-MM-dd HH:mm:ss').format(now);
        log('自动添加timestamp: ${result['timestamp']}');
      }
      
      // 确保必要字段有默认值
      result['action'] ??= 'unknown_action';
      result['value'] ??= 'malformed_data';
      result['device_sn'] ??= global.deviceSn.isNotEmpty ? global.deviceSn : 'unknown';
      
      log('JSON修复完成，提取字段: ${result.keys.toList()}');
      log('修复后数据: $result');
      
      return result;
    } catch (e) {
      log('JSON修复失败: $e');
      // 返回最基本的有效数据
      var now = DateTime.now().toUtc().add(Duration(hours: 8));
      return {
        'action': 'parse_error',
        'value': 'json_repair_failed',
        'device_sn': global.deviceSn.isNotEmpty ? global.deviceSn : 'unknown',
        'timestamp': DateFormat('yyyy-MM-dd HH:mm:ss').format(now)
      };
    }
  }
  
  /// 从损坏的JSON中提取特定字段值 #提取JSON字段
  String? _extractJsonField(String jsonStr, String fieldName) {
    try {
      // 查找字段模式: "fieldName":"value" 或 "fieldName":value
      String pattern = '"$fieldName"\\s*:\\s*"?([^",}]+)"?';
      RegExp regex = RegExp(pattern);
      var match = regex.firstMatch(jsonStr);
      
      if (match != null) {
        String value = match.group(1)!;
        log('提取字段$fieldName: $value');
        return value;
      }
      
      // 尝试更宽松的匹配模式
      int fieldIndex = jsonStr.indexOf('"$fieldName"');
      if (fieldIndex != -1) {
        int colonIndex = jsonStr.indexOf(':', fieldIndex);
        if (colonIndex != -1) {
          int startIndex = colonIndex + 1;
          
          // 跳过空格和引号
          while (startIndex < jsonStr.length && 
                 (jsonStr[startIndex] == ' ' || jsonStr[startIndex] == '"')) {
            startIndex++;
          }
          
          if (startIndex < jsonStr.length) {
            // 查找值的结束位置
            int endIndex = startIndex;
            bool inQuotes = false;
            
            while (endIndex < jsonStr.length) {
              String char = jsonStr[endIndex];
              
              if (char == '"' && (endIndex == startIndex || jsonStr[endIndex - 1] != '\\')) {
                if (inQuotes) break;
                inQuotes = true;
              } else if (!inQuotes && (char == ',' || char == '}')) {
                break;
              }
              endIndex++;
            }
            
            if (endIndex > startIndex) {
              String value = jsonStr.substring(startIndex, endIndex);
              // 移除尾部引号
              if (value.endsWith('"')) {
                value = value.substring(0, value.length - 1);
              }
              log('宽松匹配提取字段$fieldName: $value');
              return value.trim();
            }
          }
        }
      }
      
      log('未找到字段: $fieldName');
      return null;
    } catch (e) {
      log('提取字段$fieldName失败: $e');
      return null;
    }
  }

  /// 解码睡眠数据 #解码睡眠数据
  String _decodeSleepData(String sleepDataStr) {
    try {
      // 如果是空值或错误数据，返回默认JSON
      if (sleepDataStr.isEmpty || sleepDataStr == '0:0:0') {
        return '{"code":0,"data":[],"name":"sleep","type":"history"}';
      }
      
      // 解析睡眠数据格式：endTimeStamp:startTimeStamp:type 或多组用分号分隔
      List<String> groups = sleepDataStr.split(';');
      List<Map<String, dynamic>> dataList = [];
      
      for (String group in groups) {
        if (group.trim().isEmpty) continue;
        
        List<String> parts = group.split(':');
        if (parts.length == 3) {
          try {
            int endTimeStamp = int.parse(parts[0]);
            int startTimeStamp = int.parse(parts[1]);
            int type = int.parse(parts[2]);
            
            dataList.add({
              'endTimeStamp': endTimeStamp,
              'startTimeStamp': startTimeStamp,
              'type': type
            });
          } catch (e) {
            log('解析睡眠数据组失败: $group, 错误: $e');
          }
        }
      }
      
      // 构建JSON格式
      Map<String, dynamic> result = {
        'code': 0,
        'data': dataList,
        'name': 'sleep',
        'type': 'history'
      };
      
      return json.encode(result);
    } catch (e) {
      log('解码睡眠数据失败: $e');
      return '{"code":0,"data":[],"name":"sleep","type":"history"}';
    }
  }
} 