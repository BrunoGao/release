import 'package:flutter/material.dart';

/// 企业级设计系统 - 色彩规范
/// 专业医疗健康应用配色方案
class DSColors {
  DSColors._();

  // ==================== 基础色彩 ====================
  
  /// 主品牌色 - 专业蓝色系
  static const Color primary50 = Color(0xFFE3F2FD);
  static const Color primary100 = Color(0xFFBBDEFB);
  static const Color primary200 = Color(0xFF90CAF9);
  static const Color primary300 = Color(0xFF64B5F6);
  static const Color primary400 = Color(0xFF42A5F5);
  static const Color primary500 = Color(0xFF1976D2); // 主色
  static const Color primary600 = Color(0xFF1565C0);
  static const Color primary700 = Color(0xFF0D47A1);
  static const Color primary800 = Color(0xFF0A3D91);
  static const Color primary900 = Color(0xFF073282);

  /// 辅助色 - 青绿色系
  static const Color secondary50 = Color(0xFFE0F2F1);
  static const Color secondary100 = Color(0xFFB2DFDB);
  static const Color secondary200 = Color(0xFF80CBC4);
  static const Color secondary300 = Color(0xFF4DB6AC);
  static const Color secondary400 = Color(0xFF26A69A);
  static const Color secondary500 = Color(0xFF009688);
  static const Color secondary600 = Color(0xFF00897B);
  static const Color secondary700 = Color(0xFF00796B);
  static const Color secondary800 = Color(0xFF00695C);
  static const Color secondary900 = Color(0xFF004D40);

  // ==================== 语义化色彩 ====================
  
  /// 成功色 - 绿色系
  static const Color success50 = Color(0xFFE8F5E8);
  static const Color success100 = Color(0xFFC8E6C9);
  static const Color success500 = Color(0xFF4CAF50);
  static const Color success700 = Color(0xFF388E3C);
  static const Color success900 = Color(0xFF1B5E20);

  /// 警告色 - 橙色系
  static const Color warning50 = Color(0xFFFFF3E0);
  static const Color warning100 = Color(0xFFFFE0B2);
  static const Color warning500 = Color(0xFFFF9800);
  static const Color warning700 = Color(0xFFF57C00);
  static const Color warning900 = Color(0xFFE65100);

  /// 错误色 - 红色系
  static const Color error50 = Color(0xFFFFEBEE);
  static const Color error100 = Color(0xFFFFCDD2);
  static const Color error400 = Color(0xFFEF5350);
  static const Color error500 = Color(0xFFF44336);
  static const Color error700 = Color(0xFFD32F2F);
  static const Color error900 = Color(0xFFB71C1C);

  /// 信息色 - 蓝色系
  static const Color info50 = Color(0xFFE3F2FD);
  static const Color info100 = Color(0xFFBBDEFB);
  static const Color info500 = Color(0xFF2196F3);
  static const Color info700 = Color(0xFF1976D2);
  static const Color info900 = Color(0xFF0D47A1);

  // ==================== 中性色彩 ====================
  
  /// 纯白
  static const Color white = Color(0xFFFFFFFF);
  
  /// 浅灰色系
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

  /// 深色系
  static const Color dark50 = Color(0xFF37474F);
  static const Color dark100 = Color(0xFF2E3B47);
  static const Color dark200 = Color(0xFF263238);
  static const Color dark300 = Color(0xFF1E272E);
  static const Color dark400 = Color(0xFF15202B);

  // ==================== 健康数据专用色彩 ====================
  
  /// 心率 - 红色
  static const Color heartRate = Color(0xFFE53935);
  static const Color heartRateLight = Color(0xFFFFEBEE);
  
  /// 血氧 - 蓝色
  static const Color bloodOxygen = Color(0xFF1976D2);
  static const Color bloodOxygenLight = Color(0xFFE3F2FD);
  
  /// 体温 - 橙色
  static const Color temperature = Color(0xFFFF9800);
  static const Color temperatureLight = Color(0xFFFFF3E0);
  
  /// 血压 - 紫色
  static const Color bloodPressure = Color(0xFF8E24AA);
  static const Color bloodPressureLight = Color(0xFFF3E5F5);
  
  /// 步数 - 绿色
  static const Color steps = Color(0xFF4CAF50);
  static const Color stepsLight = Color(0xFFE8F5E8);
  
  /// 距离 - 青色
  static const Color distance = Color(0xFF00ACC1);
  static const Color distanceLight = Color(0xFFE0F7FA);
  
  /// 卡路里 - 深橙色
  static const Color calories = Color(0xFFFF7043);
  static const Color caloriesLight = Color(0xFFFBE9E7);
  
  /// 压力 - 红橙色
  static const Color stress = Color(0xFFFF5722);
  static const Color stressLight = Color(0xFFFBE9E7);

  // ==================== 表面色彩 ====================
  
  /// 浅色模式表面色
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color backgroundLight = Color(0xFFFAFAFA);
  static const Color containerLight = Color(0xFFF5F5F5);
  
  /// 深色模式表面色
  static const Color surfaceDark = Color(0xFF1E2839);
  static const Color backgroundDark = Color(0xFF15202B);
  static const Color containerDark = Color(0xFF263545);

  // ==================== 渐变色彩 ====================
  
  /// 主要渐变
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary400, primary600],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  /// 次要渐变  
  static const LinearGradient secondaryGradient = LinearGradient(
    colors: [secondary400, secondary600],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  /// 背景渐变 - 浅色
  static const LinearGradient backgroundGradientLight = LinearGradient(
    colors: [Color(0xFFFAFAFA), Color(0xFFFFFFFF)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );
  
  /// 背景渐变 - 深色
  static const LinearGradient backgroundGradientDark = LinearGradient(
    colors: [Color(0xFF15202B), Color(0xFF1E2839)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // ==================== 阴影色彩 ====================
  
  /// 浅色阴影
  static const Color shadowLight = Color(0x1F000000);
  
  /// 深色阴影
  static const Color shadowDark = Color(0x3F000000);
}