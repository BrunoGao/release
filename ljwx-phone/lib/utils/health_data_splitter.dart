import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import '../services/bluetooth_service.dart';

/// 健康数据分片器
/// 用于将大型健康数据分片以便通过蓝牙传输
class HealthDataSplitter {
  // 健康数据类型常量
  static const String TYPE_HEALTH_META = "health_meta"; // 元数据包
  static const String TYPE_HEALTH_SLEEP = "health_sleep"; // 睡眠数据
  static const String TYPE_HEALTH_EXERCISE_DAILY = "health_exercise_daily"; // 日运动数据
  static const String TYPE_HEALTH_EXERCISE_WEEK = "health_exercise_week"; // 周运动数据
  static const String TYPE_HEALTH_SCIENTIFIC_SLEEP = "health_scientific_sleep"; // 科学睡眠数据
  static const String TYPE_HEALTH_WORKOUT = "health_workout"; // 运动数据
  static const String HEALTH_GROUP_ID_KEY = "health_group_id"; // 健康数据组ID键名

  // 调试日志
  static void _log(String message) {
    debugPrint('[HealthDataSplitter] $message');
  }

  /// 将健康数据拆分为多个可以通过蓝牙发送的小数据包
  /// @param healthData 完整的健康数据
  /// @return 拆分后的数据包列表
  static List<Map<String, dynamic>> splitHealthData(Map<String, dynamic> healthData) {
    try {
      List<Map<String, dynamic>> packets = [];

      // 如果数据不是正确的健康数据结构，直接返回空列表
      if (healthData['type'] != 'health' || healthData['data'] == null) {
        _log('数据不是正确的健康数据结构');
        return packets;
      }

      // 生成健康数据组ID
      String groupId = _generateGroupId();
      _log('为健康数据生成组ID: $groupId');

      // 提取健康数据的内容部分
      Map<String, dynamic> healthContent = healthData['data'];

      // 创建元数据包
      Map<String, dynamic> metaPacket = _createMetaPacket(groupId, healthContent);
      packets.add(metaPacket);

      // 处理特定的复杂字段
      _tryAddNestedField(healthContent, 'sleepData', TYPE_HEALTH_SLEEP, groupId, packets);
      _tryAddNestedField(healthContent, 'exerciseDailyData', TYPE_HEALTH_EXERCISE_DAILY, groupId, packets);
      _tryAddNestedField(healthContent, 'exerciseWeekData', TYPE_HEALTH_EXERCISE_WEEK, groupId, packets);
      _tryAddNestedField(healthContent, 'scientificSleepData', TYPE_HEALTH_SCIENTIFIC_SLEEP, groupId, packets);
      _tryAddNestedField(healthContent, 'workoutData', TYPE_HEALTH_WORKOUT, groupId, packets);

      _log('健康数据拆分完成，共生成 ${packets.length} 个数据包');
      return packets;
    } catch (e) {
      _log('拆分健康数据失败: $e');
      return [];
    }
  }

  /// 尝试添加嵌套字段数据包
  static void _tryAddNestedField(
      Map<String, dynamic> healthContent,
      String fieldName,
      String packetType,
      String groupId,
      List<Map<String, dynamic>> packets) {
    try {
      // 如果字段存在且不为null
      if (healthContent.containsKey(fieldName) && healthContent[fieldName] != null) {
        String fieldValue = healthContent[fieldName].toString();
        
        // 跳过null值字符串
        if (fieldValue == 'null') return;
        
        // 创建嵌套字段的数据包
        Map<String, dynamic> fieldPacket = {
          'type': packetType,
          'data': {
            HEALTH_GROUP_ID_KEY: groupId,
            'content': fieldValue
          }
        };
        
        packets.add(fieldPacket);
        _log('添加 $fieldName 数据包');
      }
    } catch (e) {
      _log('添加 $fieldName 字段失败: $e');
    }
  }

  /// 创建元数据包
  static Map<String, dynamic> _createMetaPacket(String groupId, Map<String, dynamic> healthContent) {
    // 准备元数据
    Map<String, dynamic> metaData = {
      HEALTH_GROUP_ID_KEY: groupId,
    };
    
    // 复制基本字段
    _copyBasicFields(healthContent, metaData);
    
    // 创建元数据包
    return {
      'type': TYPE_HEALTH_META,
      'data': metaData
    };
  }

  /// 复制基本字段
  static void _copyBasicFields(Map<String, dynamic> source, Map<String, dynamic> target) {
    // 复制基本字段到元数据
    // 核心健康指标
    target['id'] = source['id'] ?? '';
    target['upload_method'] = source['upload_method'] ?? 'bluetooth';
    target['heart_rate'] = source['heart_rate'] ?? 0;
    target['blood_oxygen'] = source['blood_oxygen'] ?? 0;
    target['body_temperature'] = source['body_temperature'] ?? '0.0';
    target['blood_pressure_systolic'] = source['blood_pressure_systolic'] ?? 0;
    target['blood_pressure_diastolic'] = source['blood_pressure_diastolic'] ?? 0;
    target['step'] = source['step'] ?? 0;
    target['distance'] = source['distance'] ?? '0.0';
    target['calorie'] = source['calorie'] ?? '0.0';
    
    // 位置数据
    target['latitude'] = source['latitude'] ?? '0';
    target['longitude'] = source['longitude'] ?? '0';
    target['altitude'] = source['altitude'] ?? '0';
    
    // 其他指标
    target['stress'] = source['stress'] ?? 0;
    target['timestamp'] = source['timestamp'] ?? '';
  }

  /// 生成组ID
  static String _generateGroupId() {
    // 不使用Uuid库，改用内置方法生成唯一ID
    final random = Random();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final randomPart = random.nextInt(10000).toString().padLeft(4, '0');
    return 'health_${timestamp}_$randomPart';
  }
  
  /// 使用优化的方式发送健康数据
  /// 避免双重分片问题，使用直接发送方式
  static Future<bool> sendHealthData(Map<String, dynamic> healthData) async {
    try {
      BleSvc bluetoothService = BleSvc.i;
      
      // 验证健康数据格式
      if (healthData['type'] != 'health' || healthData['data'] == null) {
        _log('健康数据格式错误');
        return false;
      }
      
      // 生成健康数据组ID
      String groupId = _generateGroupId();
      _log('为健康数据生成组ID: $groupId');
      
      // 提取健康数据内容
      Map<String, dynamic> healthContent = healthData['data'];
      
      // 发送元数据包
      Map<String, dynamic> metaPacket = _createMetaPacket(groupId, healthContent);
      await bluetoothService.sendDirectPacket(metaPacket);
      
      // 短暂延迟，确保接收端处理完毕
      await Future.delayed(Duration(milliseconds: 100));
      
      // 处理嵌套字段并直接发送
      await _sendNestedField(healthContent, 'sleepData', TYPE_HEALTH_SLEEP, groupId, bluetoothService);
      await _sendNestedField(healthContent, 'exerciseDailyData', TYPE_HEALTH_EXERCISE_DAILY, groupId, bluetoothService);
      await _sendNestedField(healthContent, 'exerciseWeekData', TYPE_HEALTH_EXERCISE_WEEK, groupId, bluetoothService);
      await _sendNestedField(healthContent, 'scientificSleepData', TYPE_HEALTH_SCIENTIFIC_SLEEP, groupId, bluetoothService);
      await _sendNestedField(healthContent, 'workoutData', TYPE_HEALTH_WORKOUT, groupId, bluetoothService);
      
      _log('健康数据发送完成');
      return true;
    } catch (e) {
      _log('发送健康数据失败: $e');
      return false;
    }
  }
  
  /// 发送嵌套字段
  static Future<void> _sendNestedField(
      Map<String, dynamic> healthContent,
      String fieldName,
      String packetType,
      String groupId,
      BleSvc bluetoothService) async {
    try {
      // 检查字段是否存在且不为null
      if (healthContent.containsKey(fieldName) && healthContent[fieldName] != null) {
        String fieldValue = healthContent[fieldName].toString();
        
        // 跳过null值字符串
        if (fieldValue == 'null') return;
        
        // 创建嵌套字段数据包
        Map<String, dynamic> fieldPacket = {
          'type': packetType,
          'data': {
            HEALTH_GROUP_ID_KEY: groupId,
            'content': fieldValue
          }
        };
        
        // 直接发送数据包
        await bluetoothService.sendDirectPacket(fieldPacket);
        
        // 短暂延迟，确保接收端处理完毕
        await Future.delayed(Duration(milliseconds: 80));
        
        _log('发送 $fieldName 数据包成功');
      }
    } catch (e) {
      _log('发送 $fieldName 字段失败: $e');
    }
  }
} 