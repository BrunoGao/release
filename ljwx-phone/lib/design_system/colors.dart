import 'package:flutter/material.dart';

/// 企业级设计系统颜色定义
/// 基于现代企业设计规范，提供完整的色彩体系
class DSColors {
  // ==================== 主色调系统 ====================
  
  /// 主品牌色 - 蓝色系
  static const Color primary50 = Color(0xFFE3F2FD);
  static const Color primary100 = Color(0xFFBBDEFB);
  static const Color primary200 = Color(0xFF90CAF9);
  static const Color primary300 = Color(0xFF64B5F6);
  static const Color primary400 = Color(0xFF42A5F5);
  static const Color primary500 = Color(0xFF2196F3); // 主色
  static const Color primary600 = Color(0xFF1E88E5);
  static const Color primary700 = Color(0xFF1976D2);
  static const Color primary800 = Color(0xFF1565C0);
  static const Color primary900 = Color(0xFF0D47A1);

  /// 辅助色 - 青色系
  static const Color secondary50 = Color(0xFFE0F2F1);
  static const Color secondary100 = Color(0xFFB2DFDB);
  static const Color secondary200 = Color(0xFF80CBC4);
  static const Color secondary300 = Color(0xFF4DB6AC);
  static const Color secondary400 = Color(0xFF26A69A);
  static const Color secondary500 = Color(0xFF009688); // 辅助色
  static const Color secondary600 = Color(0xFF00897B);
  static const Color secondary700 = Color(0xFF00796B);
  static const Color secondary800 = Color(0xFF00695C);
  static const Color secondary900 = Color(0xFF004D40);

  // ==================== 功能性颜色 ====================
  
  /// 成功色 - 绿色系
  static const Color success50 = Color(0xFFE8F5E8);
  static const Color success100 = Color(0xFFC8E6C9);
  static const Color success200 = Color(0xFFA5D6A7);
  static const Color success300 = Color(0xFF81C784);
  static const Color success400 = Color(0xFF66BB6A);
  static const Color success500 = Color(0xFF4CAF50); // 成功色
  static const Color success600 = Color(0xFF43A047);
  static const Color success700 = Color(0xFF388E3C);
  static const Color success800 = Color(0xFF2E7D32);
  static const Color success900 = Color(0xFF1B5E20);

  /// 警告色 - 橙色系
  static const Color warning50 = Color(0xFFFFF8E1);
  static const Color warning100 = Color(0xFFFFECB3);
  static const Color warning200 = Color(0xFFFFE082);
  static const Color warning300 = Color(0xFFFFD54F);
  static const Color warning400 = Color(0xFFFFCA28);
  static const Color warning500 = Color(0xFFFFC107); // 警告色
  static const Color warning600 = Color(0xFFFFB300);
  static const Color warning700 = Color(0xFFFFA000);
  static const Color warning800 = Color(0xFFFF8F00);
  static const Color warning900 = Color(0xFFFF6F00);

  /// 错误色 - 红色系
  static const Color error50 = Color(0xFFFFEBEE);
  static const Color error100 = Color(0xFFFFCDD2);
  static const Color error200 = Color(0xFFEF9A9A);
  static const Color error300 = Color(0xFFE57373);
  static const Color error400 = Color(0xFFEF5350);
  static const Color error500 = Color(0xFFF44336); // 错误色
  static const Color error600 = Color(0xFFE53935);
  static const Color error700 = Color(0xFFD32F2F);
  static const Color error800 = Color(0xFFC62828);
  static const Color error900 = Color(0xFFB71C1C);

  /// 信息色 - 蓝色系
  static const Color info50 = Color(0xFFE1F5FE);
  static const Color info100 = Color(0xFFB3E5FC);
  static const Color info200 = Color(0xFF81D4FA);
  static const Color info300 = Color(0xFF4FC3F7);
  static const Color info400 = Color(0xFF29B6F6);
  static const Color info500 = Color(0xFF03A9F4); // 信息色
  static const Color info600 = Color(0xFF039BE5);
  static const Color info700 = Color(0xFF0288D1);
  static const Color info800 = Color(0xFF0277BD);
  static const Color info900 = Color(0xFF01579B);

  // ==================== 中性色系统 ====================
  
  /// 灰色系 - 用于文本、边框、背景等
  static const Color gray50 = Color(0xFFFAFAFA);
  static const Color gray100 = Color(0xFFF5F5F5);
  static const Color gray200 = Color(0xFFEEEEEE);
  static const Color gray300 = Color(0xFFE0E0E0);
  static const Color gray400 = Color(0xFFBDBDBD);
  static const Color gray500 = Color(0xFF9E9E9E);
  static const Color gray600 = Color(0xFF757575);
  static const Color gray700 = Color(0xFF616161);
  static const Color gray800 = Color(0xFF424242);
  static const Color gray900 = Color(0xFF212121);

  /// 纯色
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // ==================== 健康数据专用颜色 ====================
  
  /// 心率 - 红色系
  static const Color heartRate = Color(0xFFE53E3E);
  static const Color heartRateLight = Color(0xFFFED7D7);
  
  /// 血氧 - 蓝色系
  static const Color bloodOxygen = Color(0xFF3182CE);
  static const Color bloodOxygenLight = Color(0xFFBEE3F8);
  
  /// 体温 - 橙色系
  static const Color temperature = Color(0xFFDD6B20);
  static const Color temperatureLight = Color(0xFFFEEBC8);
  
  /// 血压 - 紫色系
  static const Color bloodPressure = Color(0xFF805AD5);
  static const Color bloodPressureLight = Color(0xFFE9D8FD);
  
  /// 步数 - 绿色系
  static const Color steps = Color(0xFF38A169);
  static const Color stepsLight = Color(0xFFC6F6D5);
  
  /// 距离 - 青色系
  static const Color distance = Color(0xFF00B5D8);
  static const Color distanceLight = Color(0xFFB8F5FF);
  
  /// 卡路里 - 黄色系
  static const Color calories = Color(0xFFD69E2E);
  static const Color caloriesLight = Color(0xFFFAF089);
  
  /// 压力 - 靛色系
  static const Color stress = Color(0xFF553C9A);
  static const Color stressLight = Color(0xFFDDD6FE);

  // ==================== 状态颜色 ====================
  
  /// 在线状态 - 绿色
  static const Color online = success500;
  static const Color onlineLight = success100;
  
  /// 离线状态 - 灰色
  static const Color offline = gray500;
  static const Color offlineLight = gray100;
  
  /// 待机状态 - 橙色
  static const Color standby = warning500;
  static const Color standbyLight = warning100;
  
  /// 异常状态 - 红色
  static const Color abnormal = error500;
  static const Color abnormalLight = error100;

  // ==================== 背景颜色 ====================
  
  /// 浅色主题背景
  static const Color backgroundLight = white;
  static const Color surfaceLight = white;
  static const Color cardLight = white;
  
  /// 暗色主题背景
  static const Color backgroundDark = Color(0xFF121212);
  static const Color surfaceDark = Color(0xFF1E1E1E);
  static const Color cardDark = Color(0xFF2D2D2D);

  // ==================== 文本颜色 ====================
  
  /// 浅色主题文本
  static const Color textPrimaryLight = gray900;
  static const Color textSecondaryLight = gray600;
  static const Color textTertiaryLight = gray500;
  static const Color textDisabledLight = gray400;
  
  /// 暗色主题文本
  static const Color textPrimaryDark = white;
  static const Color textSecondaryDark = gray300;
  static const Color textTertiaryDark = gray400;
  static const Color textDisabledDark = gray600;

  // ==================== 边框颜色 ====================
  
  /// 浅色主题边框
  static const Color borderLight = gray300;
  static const Color borderFocusLight = primary500;
  
  /// 暗色主题边框
  static const Color borderDark = gray600;
  static const Color borderFocusDark = primary400;

  // ==================== 阴影颜色 ====================
  
  /// 阴影
  static const Color shadowLight = Color(0x1A000000);
  static const Color shadowDark = Color(0x4D000000);
}

/// 颜色工具类
class DSColorUtils {
  /// 获取颜色的透明度变体
  static Color withOpacity(Color color, double opacity) {
    return color.withOpacity(opacity);
  }

  /// 根据亮度获取对比色
  static Color getContrastColor(Color backgroundColor) {
    final luminance = backgroundColor.computeLuminance();
    return luminance > 0.5 ? DSColors.black : DSColors.white;
  }

  /// 获取健康数据颜色
  static Color getHealthDataColor(String type) {
    switch (type.toLowerCase()) {
      case 'heartrate':
      case 'heart_rate':
        return DSColors.heartRate;
      case 'bloodoxygen':
      case 'blood_oxygen':
        return DSColors.bloodOxygen;
      case 'temperature':
      case 'body_temperature':
        return DSColors.temperature;
      case 'bloodpressure':
      case 'blood_pressure':
        return DSColors.bloodPressure;
      case 'steps':
      case 'step':
        return DSColors.steps;
      case 'distance':
        return DSColors.distance;
      case 'calories':
      case 'calorie':
        return DSColors.calories;
      case 'stress':
        return DSColors.stress;
      default:
        return DSColors.primary500;
    }
  }

  /// 获取状态颜色
  static Color getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'online':
      case 'connected':
        return DSColors.online;
      case 'offline':
      case 'disconnected':
        return DSColors.offline;
      case 'standby':
      case 'pending':
        return DSColors.standby;
      case 'abnormal':
      case 'error':
        return DSColors.abnormal;
      default:
        return DSColors.gray500;
    }
  }
}