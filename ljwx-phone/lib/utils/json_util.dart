/// JSON工具类，提供JSON操作的辅助方法
class JsonUtil {
  /// 安全获取JSON对象中的字符串值
  /// 如果字段不存在或为null，返回默认值
  static String optString(dynamic json, String key, String defaultValue) {
    if (json == null || json is! Map || !json.containsKey(key)) {
      return defaultValue;
    }
    
    final value = json[key];
    if (value == null) {
      return defaultValue;
    }
    
    return value.toString();
  }
  
  /// 安全获取JSON对象中的整数值
  /// 如果字段不存在或为null，返回默认值
  static int optInt(dynamic json, String key, int defaultValue) {
    if (json == null || json is! Map || !json.containsKey(key)) {
      return defaultValue;
    }
    
    final value = json[key];
    if (value == null) {
      return defaultValue;
    }
    
    if (value is int) {
      return value;
    }
    
    try {
      return int.parse(value.toString());
    } catch (e) {
      return defaultValue;
    }
  }
  
  /// 安全获取JSON对象中的双精度浮点值
  /// 如果字段不存在或为null，返回默认值
  static double optDouble(dynamic json, String key, double defaultValue) {
    if (json == null || json is! Map || !json.containsKey(key)) {
      return defaultValue;
    }
    
    final value = json[key];
    if (value == null) {
      return defaultValue;
    }
    
    if (value is double) {
      return value;
    }
    
    if (value is int) {
      return value.toDouble();
    }
    
    try {
      return double.parse(value.toString());
    } catch (e) {
      return defaultValue;
    }
  }
  
  /// 安全获取JSON对象中的布尔值
  /// 如果字段不存在或为null，返回默认值
  static bool optBool(dynamic json, String key, bool defaultValue) {
    if (json == null || json is! Map || !json.containsKey(key)) {
      return defaultValue;
    }
    
    final value = json[key];
    if (value == null) {
      return defaultValue;
    }
    
    if (value is bool) {
      return value;
    }
    
    if (value is String) {
      return value.toLowerCase() == 'true';
    }
    
    if (value is num) {
      return value != 0;
    }
    
    return defaultValue;
  }
} 