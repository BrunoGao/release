import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'colors.dart';

/// 企业级设计系统字体排版定义
/// 提供完整的字体样式体系，支持多语言和可访问性
class DSTypography {
  // ==================== 字体家族 ====================
  
  /// 主要字体 - 用于中文和英文混排
  static String get primaryFontFamily => 'PingFang SC';
  
  /// 数字字体 - 用于数据展示
  static String get numberFontFamily => 'SF Mono';
  
  /// 代码字体 - 用于代码和技术信息
  static String get codeFontFamily => 'JetBrains Mono';

  // ==================== 字体权重 ====================
  
  static const FontWeight thin = FontWeight.w100;
  static const FontWeight extraLight = FontWeight.w200;
  static const FontWeight light = FontWeight.w300;
  static const FontWeight regular = FontWeight.w400;
  static const FontWeight medium = FontWeight.w500;
  static const FontWeight semiBold = FontWeight.w600;
  static const FontWeight bold = FontWeight.w700;
  static const FontWeight extraBold = FontWeight.w800;
  static const FontWeight black = FontWeight.w900;

  // ==================== 字体大小 ====================
  
  /// 字体大小常量 - 基于8pt网格系统
  static const double fontSize10 = 10.0;
  static const double fontSize12 = 12.0;
  static const double fontSize14 = 14.0;
  static const double fontSize16 = 16.0;
  static const double fontSize18 = 18.0;
  static const double fontSize20 = 20.0;
  static const double fontSize24 = 24.0;
  static const double fontSize28 = 28.0;
  static const double fontSize32 = 32.0;
  static const double fontSize36 = 36.0;
  static const double fontSize40 = 40.0;
  static const double fontSize48 = 48.0;
  static const double fontSize56 = 56.0;
  static const double fontSize64 = 64.0;
  static const double fontSize72 = 72.0;

  // ==================== 行高 ====================
  
  /// 行高常量
  static const double lineHeight1_2 = 1.2; // 紧凑
  static const double lineHeight1_4 = 1.4; // 正常
  static const double lineHeight1_5 = 1.5; // 舒适
  static const double lineHeight1_6 = 1.6; // 宽松
  static const double lineHeight2_0 = 2.0; // 超宽松

  // ==================== 字间距 ====================
  
  /// 字间距常量
  static const double letterSpacingTight = -0.5;
  static const double letterSpacingNormal = 0.0;
  static const double letterSpacingWide = 0.5;
  static const double letterSpacingWider = 1.0;
  static const double letterSpacingWidest = 1.5;

  // ==================== 预定义文本样式 ====================
  
  /// 标题样式
  static TextStyle get displayLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize72,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingTight,
  );

  static TextStyle get displayMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize56,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingTight,
  );

  static TextStyle get displaySmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize48,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get headlineLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize40,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get headlineMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize32,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get headlineSmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize28,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get titleLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize24,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get titleMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize20,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get titleSmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize18,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingNormal,
  );

  /// 正文样式
  static TextStyle get bodyLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize16,
    fontWeight: regular,
    height: lineHeight1_5,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get bodyMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize14,
    fontWeight: regular,
    height: lineHeight1_5,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get bodySmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: regular,
    height: lineHeight1_5,
    letterSpacing: letterSpacingNormal,
  );

  /// 标签样式
  static TextStyle get labelLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize14,
    fontWeight: medium,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWide,
  );

  static TextStyle get labelMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: medium,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWide,
  );

  static TextStyle get labelSmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize10,
    fontWeight: medium,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWider,
  );

  // ==================== 数据展示样式 ====================
  
  /// 数字展示 - 大型数据
  static TextStyle get numberLarge => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize48,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingTight,
  );

  static TextStyle get numberMedium => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize32,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get numberSmall => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize24,
    fontWeight: semiBold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  /// 代码样式
  static TextStyle get codeLarge => GoogleFonts.getFont(
    codeFontFamily,
    fontSize: fontSize16,
    fontWeight: regular,
    height: lineHeight1_6,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get codeMedium => GoogleFonts.getFont(
    codeFontFamily,
    fontSize: fontSize14,
    fontWeight: regular,
    height: lineHeight1_6,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get codeSmall => GoogleFonts.getFont(
    codeFontFamily,
    fontSize: fontSize12,
    fontWeight: regular,
    height: lineHeight1_6,
    letterSpacing: letterSpacingNormal,
  );

  // ==================== 健康数据专用样式 ====================
  
  /// 健康指标数值
  static TextStyle get healthValueLarge => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize36,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingTight,
  );

  static TextStyle get healthValueMedium => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize28,
    fontWeight: bold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get healthValueSmall => GoogleFonts.getFont(
    numberFontFamily,
    fontSize: fontSize20,
    fontWeight: semiBold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  /// 健康指标单位
  static TextStyle get healthUnit => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: regular,
    height: lineHeight1_4,
    letterSpacing: letterSpacingNormal,
  );

  /// 健康指标标签
  static TextStyle get healthLabel => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize14,
    fontWeight: medium,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWide,
  );

  // ==================== 按钮样式 ====================
  
  static TextStyle get buttonLarge => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize16,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWide,
  );

  static TextStyle get buttonMedium => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize14,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWide,
  );

  static TextStyle get buttonSmall => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: semiBold,
    height: lineHeight1_4,
    letterSpacing: letterSpacingWider,
  );

  // ==================== 导航样式 ====================
  
  static TextStyle get navigationActive => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: semiBold,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  static TextStyle get navigationInactive => GoogleFonts.getFont(
    primaryFontFamily,
    fontSize: fontSize12,
    fontWeight: medium,
    height: lineHeight1_2,
    letterSpacing: letterSpacingNormal,
  );

  // ==================== 构建主题方法 ====================
  
  /// 构建文本主题
  static TextTheme buildTextTheme(Color baseColor) {
    return TextTheme(
      // Display styles
      displayLarge: displayLarge.copyWith(color: baseColor),
      displayMedium: displayMedium.copyWith(color: baseColor),
      displaySmall: displaySmall.copyWith(color: baseColor),
      
      // Headline styles
      headlineLarge: headlineLarge.copyWith(color: baseColor),
      headlineMedium: headlineMedium.copyWith(color: baseColor),
      headlineSmall: headlineSmall.copyWith(color: baseColor),
      
      // Title styles
      titleLarge: titleLarge.copyWith(color: baseColor),
      titleMedium: titleMedium.copyWith(color: baseColor),
      titleSmall: titleSmall.copyWith(color: baseColor),
      
      // Body styles
      bodyLarge: bodyLarge.copyWith(color: baseColor),
      bodyMedium: bodyMedium.copyWith(color: baseColor),
      bodySmall: bodySmall.copyWith(color: baseColor),
      
      // Label styles
      labelLarge: labelLarge.copyWith(color: baseColor),
      labelMedium: labelMedium.copyWith(color: baseColor),
      labelSmall: labelSmall.copyWith(color: baseColor),
    );
  }

  /// 应用颜色到文本样式
  static TextStyle applyColor(TextStyle style, Color color) {
    return style.copyWith(color: color);
  }

  /// 应用透明度到文本样式
  static TextStyle applyOpacity(TextStyle style, double opacity) {
    return style.copyWith(color: style.color?.withOpacity(opacity));
  }
}

/// 排版工具类
class DSTypographyUtils {
  /// 获取响应式字体大小
  static double getResponsiveFontSize(BuildContext context, double baseFontSize) {
    final screenWidth = MediaQuery.of(context).size.width;
    if (screenWidth < 360) {
      return baseFontSize * 0.9; // 小屏幕
    } else if (screenWidth > 600) {
      return baseFontSize * 1.1; // 大屏幕
    }
    return baseFontSize; // 标准屏幕
  }

  /// 获取可访问性字体大小
  static double getAccessibleFontSize(BuildContext context, double baseFontSize) {
    final textScaleFactor = MediaQuery.of(context).textScaleFactor;
    return baseFontSize * textScaleFactor;
  }

  /// 计算行高
  static double calculateLineHeight(double fontSize, double lineHeightMultiplier) {
    return fontSize * lineHeightMultiplier;
  }
}