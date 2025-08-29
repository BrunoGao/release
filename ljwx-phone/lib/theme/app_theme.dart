import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../design_system/design_system.dart';

class AppTheme {
  // ==================== 兼容性别名 ====================
  // 为了兼容现有代码，保留旧的颜色别名
  static const Color primaryColor = DSColors.primary500;
  static const Color accentColor = DSColors.success500;
  static const Color secondaryColor = DSColors.secondary500;
  static const Color errorColor = DSColors.error500;
  static const Color warningColor = DSColors.warning500;
  static const Color successColor = DSColors.success500;

  // 健康数据相关颜色 - 使用设计系统色彩
  static const Color heartRateColor = DSColors.heartRate;
  static const Color bloodOxygenColor = DSColors.bloodOxygen;
  static const Color temperatureColor = DSColors.temperature;
  static const Color pressureColor = DSColors.bloodPressure;
  static const Color stepsColor = DSColors.steps;
  static const Color distanceColor = DSColors.distance;
  static const Color calorieColor = DSColors.calories;
  static const Color stressColor = DSColors.stress;

  // ==================== 主题数据 ====================
  
  /// 浅色主题 - 使用企业级设计系统
  static ThemeData lightTheme = DSTheme.buildLightTheme();

  /// 暗色主题 - 使用企业级设计系统  
  static ThemeData darkTheme = DSTheme.buildDarkTheme();

  // ==================== 兼容性方法 ====================
  
  /// 构建文字主题 - 保持向后兼容
  /// 现在委托给设计系统
  static TextTheme _buildTextTheme(Brightness brightness) {
    final baseColor = brightness == Brightness.dark ? DSColors.white : DSColors.gray900;
    return DSTypography.buildTextTheme(baseColor);
  }
} 