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

  // ==================== 企业级特色样式 ====================
  
  /// 健康数据卡片装饰
  static BoxDecoration healthCardDecoration(Color color, {bool isDark = false}) {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          color.withOpacity(0.1),
          color.withOpacity(0.05),
        ],
      ),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(
        color: color.withOpacity(0.2),
        width: 1,
      ),
      boxShadow: [
        BoxShadow(
          color: (isDark ? DSColors.shadowDark : DSColors.shadowLight).withOpacity(0.1),
          offset: const Offset(0, 2),
          blurRadius: 8,
          spreadRadius: 0,
        ),
      ],
    );
  }

  /// 状态指示器装饰
  static BoxDecoration statusIndicatorDecoration(String status, {bool isDark = false}) {
    final color = DSColorUtils.getStatusColor(status);
    return BoxDecoration(
      color: color.withOpacity(0.1),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(
        color: color.withOpacity(0.3),
        width: 1,
      ),
    );
  }

  /// 企业级按钮样式
  static ButtonStyle enterpriseButtonStyle({
    Color? backgroundColor,
    Color? foregroundColor,
    double? elevation,
    EdgeInsetsGeometry? padding,
  }) {
    return ElevatedButton.styleFrom(
      backgroundColor: backgroundColor ?? DSColors.primary500,
      foregroundColor: foregroundColor ?? DSColors.white,
      elevation: elevation ?? 2,
      shadowColor: DSColors.shadowLight,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      padding: padding ?? const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      textStyle: DSTypography.buttonMedium,
      minimumSize: const Size(64, 48),
    );
  }

  /// 企业级卡片样式
  static BoxDecoration enterpriseCardDecoration({bool isDark = false}) {
    return BoxDecoration(
      color: isDark ? DSColors.cardDark : DSColors.cardLight,
      borderRadius: BorderRadius.circular(16),
      boxShadow: [
        BoxShadow(
          color: (isDark ? DSColors.shadowDark : DSColors.shadowLight).withOpacity(0.1),
          offset: const Offset(0, 2),
          blurRadius: 8,
          spreadRadius: 0,
        ),
      ],
    );
  }

  /// 渐变背景装饰
  static BoxDecoration gradientDecoration(List<Color> colors) {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: colors,
      ),
    );
  }

  // ==================== 兼容性方法 ====================
  
  /// 构建文字主题 - 保持向后兼容
  /// 现在委托给设计系统
  static TextTheme _buildTextTheme(Brightness brightness) {
    final baseColor = brightness == Brightness.dark ? DSColors.white : DSColors.gray900;
    return DSTypography.buildTextTheme(baseColor);
  }

  // ==================== 实用方法 ====================
  
  /// 获取健康指标颜色
  static Color getHealthDataColor(String type) {
    return DSColorUtils.getHealthDataColor(type);
  }

  /// 获取状态颜色
  static Color getStatusColor(String status) {
    return DSColorUtils.getStatusColor(status);
  }

  /// 获取对比色
  static Color getContrastColor(Color backgroundColor) {
    return DSColorUtils.getContrastColor(backgroundColor);
  }
} 