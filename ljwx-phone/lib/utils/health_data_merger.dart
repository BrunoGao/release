import 'dart:convert';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'json_util.dart';
import 'package:intl/intl.dart';

/// 健康数据合并器
/// 用于接收从手表分片发送的健康数据并重组为完整数据
class HealthDataMerger {
  static final HealthDataMerger i = HealthDataMerger._(); // 单例模式
  HealthDataMerger._();

  // 健康数据类型常量
  static const String TYPE_HEALTH_META = "health_meta"; // 元数据包
  static const String TYPE_HEALTH_SLEEP = "health_sleep"; // 睡眠数据
  static const String TYPE_HEALTH_EXERCISE_DAILY = "health_exercise_daily"; // 日运动数据
  static const String TYPE_HEALTH_EXERCISE_WEEK = "health_exercise_week"; // 周运动数据
  static const String TYPE_HEALTH_SCIENTIFIC_SLEEP = "health_scientific_sleep"; // 科学睡眠
  static const String TYPE_HEALTH_WORKOUT = "health_workout"; // 运动数据
  static const String HEALTH_GROUP_ID_KEY = "health_group_id"; // 健康数据组ID键名
  static const String TYPE_RAW_CHUNK = "raw_chunk"; // 原始分片类型

  // 缓存分片数据的Map，键为健康数据组ID
  final Map<String, HealthDataGroup> _healthDataGroups = {};
  
  // 用于存储原始分片的临时缓存
  final Map<String, RawChunkGroup> _rawChunks = {};
  
  // 数据接收超时时间（毫秒）
  static const int DATA_TIMEOUT = 60000; // 60秒
  
  // 健康数据接收完成流控制器
  final _healthDataController = StreamController<Map<String, dynamic>>.broadcast();
  
  // 健康数据接收完成流
  Stream<Map<String, dynamic>> get healthDataStream => _healthDataController.stream;

  // 调试日志
  void _log(String message) {
    debugPrint('[HealthDataMerger] $message');
  }

  /// 接收健康数据片段
  /// @param jsonData 接收到的JSON数据字符串
  void receiveData(String jsonData) {
    try {
      // 优化：预处理JSON数据，尝试修复可能的格式问题
      String processedData = _preprocessJsonData(jsonData);
      
      final jsonObject = json.decode(processedData);
      if (jsonObject is Map<String, dynamic>) {
        receiveDataMap(jsonObject);
      } else {
        _log('接收到的数据不是有效的JSON对象');
      }
    } catch (e) {
      _log('解析接收数据失败: $e\n数据内容: ${jsonData.substring(0, min(100, jsonData.length))}...');
    }
  }

  /// 预处理JSON数据，修复可能的格式问题
  String _preprocessJsonData(String jsonData) {
    String data = jsonData.trim();
    
    // 检查并修复双花括号开始的情况
    if (data.startsWith("{{")) {
      data = data.substring(1);
      _log('修复了多余的开始{');
    }
    
    // 检查并修复花括号不匹配的情况
    int openCount = 0, closeCount = 0;
    for (int i = 0; i < data.length; i++) {
      if (data[i] == '{') openCount++;
      if (data[i] == '}') closeCount++;
    }
    
    if (openCount > closeCount) {
      _log('花括号不匹配，缺少}');
      data = data + '}' * (openCount - closeCount);
    } else if (closeCount > openCount) {
      _log('花括号不匹配，缺少{');
      data = '{' * (closeCount - openCount) + data;
    }
    
    // 修复可能的转义问题，特别是嵌套JSON字符串中的转义问题
    data = _fixEscapeIssues(data);
    
    return data;
  }

  /// 修复字符串中可能的转义问题
  String _fixEscapeIssues(String data) {
    // 查找形如 \"name\":\"sleede" 的模式，这通常表示JSON字符串被错误地截断
    RegExp pattern = RegExp(r'\"(\w+)\":\"(\w+)(?=[^\\]\"|\Z)');
    var matches = pattern.allMatches(data);
    for (var match in matches) {
      if (match.group(0) != null) {
        String original = match.group(0)!;
        if (!original.endsWith('\"')) {
          String fixed = original + '\"';
          data = data.replaceFirst(original, fixed);
          _log('修复了被截断的JSON键值对: $original -> $fixed');
        }
      }
    }
    return data;
  }

  /// 接收健康数据片段
  /// @param jsonObject 接收到的JSON对象
  void receiveDataMap(Map<String, dynamic> jsonObject) {
    try {
      String type = jsonObject['type'] ?? '';
      
      // 检查是否包含健康数据并打印 - 新增
      if (_isHealthDataType(type) && jsonObject.containsKey('data')) {
        var healthData = jsonObject['data'];
        debugPrint('接收健康数据分片(${type}): $healthData');
        
        // 提取并打印关键字段 - 新增
        if (healthData is Map<String, dynamic>) {
          // 打印心率、血氧等关键字段
          debugPrint('健康数据分片关键字段 - 心率: ${healthData['heart_rate']}, 类型: ${healthData['heart_rate']?.runtimeType}');
          debugPrint('健康数据分片关键字段 - 血氧: ${healthData['blood_oxygen']}, 类型: ${healthData['blood_oxygen']?.runtimeType}');
          debugPrint('健康数据分片关键字段 - 收缩压: ${healthData['blood_pressure_systolic']}, 类型: ${healthData['blood_pressure_systolic']?.runtimeType}');
          debugPrint('健康数据分片关键字段 - 舒张压: ${healthData['blood_pressure_diastolic']}, 类型: ${healthData['blood_pressure_diastolic']?.runtimeType}');
          debugPrint('健康数据分片关键字段 - 创建时间: ${healthData['cjsj']}, 类型: ${healthData['cjsj']?.runtimeType}');
        }
      }
      
      // 处理原始分片
      if (type == TYPE_RAW_CHUNK) {
        _processRawChunk(jsonObject);
        return;
      }
      
      // 处理健康数据分片
      if (_isHealthDataType(type)) {
        _processHealthData(jsonObject);
      }
      
      // 清理超时数据
      _cleanupTimeoutData();
    } catch (e) {
      _log('处理接收数据失败: $e');
    }
  }

  /// 处理原始分片数据
  void _processRawChunk(Map<String, dynamic> data) {
    try {
      String messageId = data['id'] ?? '';
      int total = data['total'] ?? 0;
      int index = data['index'] ?? 0;
      String chunkData = data['data'] ?? '';
      
      if (messageId.isEmpty || total <= 0) {
        _log('原始分片数据无效');
        return;
      }
      
      // 获取或创建原始分片组
      RawChunkGroup? group = _rawChunks[messageId];
      if (group == null) {
        group = RawChunkGroup(messageId, total);
        _rawChunks[messageId] = group;
      }
      
      // 添加分片
      group.addChunk(index, chunkData);
      
      // 检查是否可以合并
      if (group.isComplete()) {
        String completeData = group.merge();
        _rawChunks.remove(messageId);
        
        // 解析合并后的数据
        try {
          var jsonObject = json.decode(completeData);
          if (jsonObject is Map<String, dynamic>) {
            _log('原始分片合并成功，继续处理');
            
            // 如果这是健康数据的原始JSON，直接作为健康数据发送
            if (jsonObject.containsKey('type') && jsonObject['type'] == 'health' && 
                jsonObject.containsKey('data') && jsonObject['data'] != null) {
              _log('检测到完整的健康数据JSON，直接发送');
              
              // 确保数据格式正确
              if (!jsonObject['data'].containsKey('data')) {
                jsonObject['data'] = {'data': jsonObject['data']};
              }
              
              // 添加创建时间
              if (!jsonObject['data']['data'].containsKey('cjsj')) {
                final now = DateTime.now();
                final formatter = DateFormat('yyyy-MM-dd HH:mm:ss');
                jsonObject['data']['data']['cjsj'] = formatter.format(now);
                _log('添加创建时间到健康数据: ${jsonObject['data']['data']['cjsj']}');
              }
              
              // 发送到健康数据流
              _healthDataController.add(jsonObject);
              return;
            }
            
            // 处理其他类型的原始JSON
            receiveDataMap(jsonObject);
          }
        } catch (e) {
          _log('解析原始分片合并后的数据失败: $e');
        }
      }
    } catch (e) {
      _log('处理原始分片数据失败: $e');
    }
  }

  /// 处理健康数据分片
  void _processHealthData(Map<String, dynamic> data) {
    try {
      String type = data['type'] ?? '';
      Map<String, dynamic>? content = data['data'] as Map<String, dynamic>?;
      
      if (content == null) {
        _log('健康数据缺少内容');
        return;
      }
      
      String groupId = content[HEALTH_GROUP_ID_KEY] ?? '';
      if (groupId.isEmpty) {
        _log('健康数据缺少组ID');
        return;
      }
      
      // 获取或创建数据组
      HealthDataGroup? group = _healthDataGroups[groupId];
      if (group == null) {
        group = HealthDataGroup(groupId);
        _healthDataGroups[groupId] = group;
      }
      
      // 添加分片数据
      group.addData(type, content);
      _log('添加了类型为 $type 的健康数据分片，当前组 $groupId 已收到 ${group.dataMap.length} 个分片');
      
      // 检查是否可以合并
      if (group.isReady()) {
        try {
          Map<String, dynamic> mergedData = group.merge();
          _healthDataGroups.remove(groupId); // 移除已处理的组
          
          // 通过流发送合并后的数据
          _healthDataController.add(mergedData);
          _log('健康数据组 $groupId 合并完成');
        } catch (e) {
          _log('合并健康数据组 $groupId 失败: $e');
        }
      }
    } catch (e) {
      _log('处理健康数据分片失败: $e');
    }
  }

  /// 判断是否为健康数据类型
  bool _isHealthDataType(String type) {
    return type == TYPE_HEALTH_META || 
           type == TYPE_HEALTH_SLEEP || 
           type == TYPE_HEALTH_EXERCISE_DAILY || 
           type == TYPE_HEALTH_EXERCISE_WEEK || 
           type == TYPE_HEALTH_SCIENTIFIC_SLEEP || 
           type == TYPE_HEALTH_WORKOUT;
  }

  /// 清理超时的数据组
  void _cleanupTimeoutData() {
    final currentTime = DateTime.now().millisecondsSinceEpoch;
    
    _healthDataGroups.removeWhere((key, group) {
      bool timeout = (currentTime - group.creationTime) > DATA_TIMEOUT;
      if (timeout) _log('健康数据组 $key 超时，已移除');
      return timeout;
    });
    
    _rawChunks.removeWhere((key, group) {
      bool timeout = (currentTime - group.creationTime) > DATA_TIMEOUT;
      if (timeout) _log('原始分片组 $key 超时，已移除');
      return timeout;
    });
  }

  /// 关闭合并器，释放资源
  void dispose() {
    _healthDataGroups.clear();
    _rawChunks.clear();
    _healthDataController.close();
  }

  /// 处理健康数据里可能存在的JSON字符串字段
  void _processJsonStringFields(Map<String, dynamic> data) {
    if (data == null) return;
    
    // 特殊处理的字段列表
    final jsonFields = [
      'sleepData', 'exerciseDailyData', 'exerciseWeekData', 
      'scientificSleepData', 'workoutData'
    ];
    
    for (var field in jsonFields) {
      if (data.containsKey(field) && data[field] is String) {
        String strValue = data[field];
        if (strValue != 'null' && strValue.isNotEmpty) {
          try {
            // 尝试解析字符串为JSON对象
            var jsonObj = json.decode(strValue);
            // 再转回字符串，但是格式化更好
            data[field] = json.encode(jsonObj);
          } catch (e) {
            _log('处理字段 $field 失败: $e');
          }
        }
      }
    }
  }
  
  /// 最小值函数
  int min(int a, int b) => a < b ? a : b;
}

/// 健康数据组，用于管理同一组ID的多个数据片段
class HealthDataGroup {
  final String groupId;
  final int creationTime;
  final Map<String, Map<String, dynamic>> dataMap = {};
  bool hasMeta = false;
  
  HealthDataGroup(this.groupId) : creationTime = DateTime.now().millisecondsSinceEpoch;
  
  /// 添加数据片段
  void addData(String type, Map<String, dynamic> data) {
    dataMap[type] = data;
    
    if (type == HealthDataMerger.TYPE_HEALTH_META) {
      hasMeta = true;
    }
  }
  
  /// 检查是否准备好进行合并（至少包含元数据包）
  bool isReady() {
    return hasMeta && dataMap.isNotEmpty;
  }
  
  /// 获取创建时间
  int get getCreationTime => creationTime;
  
  /// 合并数据片段为完整的健康数据
  Map<String, dynamic> merge() {
    // 创建基础结构
    final result = <String, dynamic>{};
    final dataObj = <String, dynamic>{};
    result['type'] = 'health'; // 设置合并后的类型为health
    result['data'] = dataObj;
    
    // 获取元数据
    final metaData = dataMap[HealthDataMerger.TYPE_HEALTH_META];
    if (metaData == null) {
      throw Exception('缺少元数据包');
    }
    
    // 复制基本字段
    _copyBasicFields(metaData, dataObj);
    
    // 合并嵌套字段
    _tryMergeNestedField(HealthDataMerger.TYPE_HEALTH_SLEEP, 'sleepData', dataObj);
    _tryMergeNestedField(HealthDataMerger.TYPE_HEALTH_EXERCISE_DAILY, 'exerciseDailyData', dataObj);
    _tryMergeNestedField(HealthDataMerger.TYPE_HEALTH_EXERCISE_WEEK, 'exerciseWeekData', dataObj);
    _tryMergeNestedField(HealthDataMerger.TYPE_HEALTH_SCIENTIFIC_SLEEP, 'scientificSleepData', dataObj);
    _tryMergeNestedField(HealthDataMerger.TYPE_HEALTH_WORKOUT, 'workoutData', dataObj);
    
    return result;
  }
  
  /// 尝试合并嵌套字段
  void _tryMergeNestedField(String type, String fieldName, Map<String, dynamic> target) {
    final fieldData = dataMap[type];
    if (fieldData != null) {
      final content = fieldData['content'];
      if (content != null) {
        if (content is Map) {
          // 确保嵌套的JSON被正确编码
          try {
            target[fieldName] = json.encode(content);
          } catch (e) {
            // 如果编码失败，尝试先将Map转为字符串再处理
            target[fieldName] = content.toString();
          }
        } else if (content is String) {
          // 如果内容已经是字符串，验证它是有效的JSON
          try {
            var jsonContent = json.decode(content); // 验证并使用结果
            if (jsonContent == null) {
              // 处理null值情况
              target[fieldName] = '{"code":0,"data":[],"name":"sleep","type":"history"}';
            } else if (jsonContent is Map && !jsonContent.containsKey('data')) {
              // 处理缺少data字段的情况
              jsonContent['data'] = [];
              target[fieldName] = json.encode(jsonContent);
            } else {
              target[fieldName] = content;
            }
          } catch (e) {
            // 如果不是有效的JSON，创建有效的JSON结构
            target[fieldName] = '{"code":0,"data":[],"name":"sleep","type":"history"}';
          }
        } else {
          // 其他类型，直接转字符串
          target[fieldName] = content.toString();
        }
      } else {
        // content为null，创建有效的空数据结构
        if (fieldName == 'sleepData') {
          target[fieldName] = '{"code":0,"data":[],"name":"sleep","type":"history"}';
        } else {
          target[fieldName] = 'null';
        }
      }
    } else {
      // 字段不存在，创建有效的空数据结构
      if (fieldName == 'sleepData') {
        target[fieldName] = '{"code":0,"data":[],"name":"sleep","type":"history"}';
      } else {
        target[fieldName] = 'null';
      }
    }
  }
  
  /// 复制基本字段
  void _copyBasicFields(Map<String, dynamic> source, Map<String, dynamic> target) {
    // 打印源数据中的关键字段
    debugPrint("健康数据合并开始 - 源数据关键字段:");
    debugPrint("源数据心率: ${source['heart_rate']}, 类型: ${source['heart_rate']?.runtimeType}");
    debugPrint("源数据血氧: ${source['blood_oxygen']}, 类型: ${source['blood_oxygen']?.runtimeType}");
    debugPrint("源数据收缩压: ${source['blood_pressure_systolic']}, 类型: ${source['blood_pressure_systolic']?.runtimeType}");
    debugPrint("源数据舒张压: ${source['blood_pressure_diastolic']}, 类型: ${source['blood_pressure_diastolic']?.runtimeType}");
    debugPrint("源数据创建时间: ${source['cjsj']}, 类型: ${source['cjsj']?.runtimeType}");
    
    // 复制元数据中的基本字段到目标对象
    target['id'] = JsonUtil.optString(source, 'id', '');
    target['upload_method'] = JsonUtil.optString(source, 'upload_method', 'bluetooth');
    
    // 直接复制数值型字段，保留原始值
    target['heart_rate'] = source['heart_rate'];
    target['blood_oxygen'] = source['blood_oxygen'];
    target['body_temperature'] = source['body_temperature']?.toString() ?? '0.0';
    target['blood_pressure_systolic'] = source['blood_pressure_systolic'];
    target['blood_pressure_diastolic'] = source['blood_pressure_diastolic'];
    target['step'] = source['step'];
    
    // 使用原始值或默认值
    target['distance'] = source['distance']?.toString() ?? '0.0';
    target['calorie'] = source['calorie']?.toString() ?? '0.0';
    target['latitude'] = source['latitude']?.toString() ?? '0';
    target['longitude'] = source['longitude']?.toString() ?? '0';
    target['altitude'] = source['altitude']?.toString() ?? '0';
    target['stress'] = source['stress'];
    
    // 保留原始创建时间字段cjsj
    if (source.containsKey('cjsj')) {
      target['cjsj'] = source['cjsj'];
      debugPrint("从源数据复制cjsj: ${source['cjsj']}");
    } else {
      // 如果没有cjsj字段，使用当前时间作为默认值
      final now = DateTime.now();
      final formatter = DateFormat('yyyy-MM-dd HH:mm:ss');
      target['cjsj'] = formatter.format(now);
      debugPrint("源数据无cjsj字段，生成默认时间: ${target['cjsj']}");
    }
    
    target['timestamp'] = JsonUtil.optString(source, 'timestamp', '');
    
    // 打印目标数据的关键字段
    debugPrint("健康数据合并完成 - 目标数据关键字段:");
    debugPrint("目标数据心率: ${target['heart_rate']}, 类型: ${target['heart_rate']?.runtimeType}");
    debugPrint("目标数据血氧: ${target['blood_oxygen']}, 类型: ${target['blood_oxygen']?.runtimeType}");
    debugPrint("目标数据收缩压: ${target['blood_pressure_systolic']}, 类型: ${target['blood_pressure_systolic']?.runtimeType}");
    debugPrint("目标数据舒张压: ${target['blood_pressure_diastolic']}, 类型: ${target['blood_pressure_diastolic']?.runtimeType}");
    debugPrint("目标数据创建时间: ${target['cjsj']}, 类型: ${target['cjsj']?.runtimeType}");
    
    // 打印关键字段值以便调试
    debugPrint("数据合并:heart_rate=${source['heart_rate']},blood_oxygen=${source['blood_oxygen']},systolic=${source['blood_pressure_systolic']},diastolic=${source['blood_pressure_diastolic']},cjsj=${target['cjsj']}");
    
    // 添加血压计算 - 如果缺少血压但有心率，根据心率计算血压
    if ((target['blood_pressure_systolic'] == null || target['blood_pressure_diastolic'] == null) && target['heart_rate'] != null) {
      int heartRate = 0;
      if (target['heart_rate'] is String) {
        heartRate = int.tryParse(target['heart_rate']) ?? 0;
      } else if (target['heart_rate'] is int) {
        heartRate = target['heart_rate'];
      }
      
      if (heartRate > 0) {
        // 定义心率到血压的映射范围
        int minSystolic = 40;  // 最低高压
        int maxSystolic = 300; // 最高高压
        int minDiastolic = 30;  // 最低低压
        int maxDiastolic = 200; // 最高低压
        
        // 计算高压和低压
        int systolic = ((heartRate - 0) * (maxSystolic - minSystolic) ~/ 255) + minSystolic;
        int diastolic = ((heartRate - 0) * (maxDiastolic - minDiastolic) ~/ 255) + minDiastolic;
        
        target['blood_pressure_systolic'] = systolic;
        target['blood_pressure_diastolic'] = diastolic;
        debugPrint("根据心率 $heartRate 计算血压: 高压=$systolic, 低压=$diastolic");
      }
    }
    
    // 添加必要的额外字段，如果不存在则使用默认值
    if (!target.containsKey('sleepData') || target['sleepData'] == null) {
      target['sleepData'] = '{"code":0,"data":[],"name":"sleep","type":"history"}';
      debugPrint("添加默认sleepData字段");
    }
    
    if (!target.containsKey('exerciseDailyData') || target['exerciseDailyData'] == null) {
      target['exerciseDailyData'] = '{"code":0,"data":[{"strengthTimes":0,"totalTime":0}],"name":"daily","type":"history"}';
      debugPrint("添加默认exerciseDailyData字段");
    }
    
    if (!target.containsKey('exerciseWeekData') || target['exerciseWeekData'] == null) {
      target['exerciseWeekData'] = 'null';
      debugPrint("添加默认exerciseWeekData字段");
    }
    
    if (!target.containsKey('workoutData') || target['workoutData'] == null) {
      target['workoutData'] = '{"code":0,"data":[],"name":"workout","type":"history"}';
      debugPrint("添加默认workoutData字段");
    }
    
    // 确保上传方法字段存在
    target['upload_method'] = 'bluetooth';
    
    // 移除内部使用的字段
    target.remove(HealthDataMerger.HEALTH_GROUP_ID_KEY);
  }
}

/// 原始分片组，用于管理被分片的大型原始数据
class RawChunkGroup {
  final String messageId;
  final int totalChunks;
  final int creationTime;
  final Map<int, String> chunks = {};
  
  RawChunkGroup(this.messageId, this.totalChunks) 
      : creationTime = DateTime.now().millisecondsSinceEpoch;
  
  /// 添加分片数据
  void addChunk(int index, String data) {
    chunks[index] = data;
  }
  
  /// 检查是否所有分片都已接收
  bool isComplete() {
    return chunks.length == totalChunks;
  }
  
  /// 合并所有分片为完整数据
  String merge() {
    // 按索引排序后合并
    StringBuffer buffer = StringBuffer();
    List<int> indices = chunks.keys.toList()..sort();
    
    for (int i = 0; i < indices.length; i++) {
      buffer.write(chunks[i] ?? '');
    }
    
    return buffer.toString();
  }
} 