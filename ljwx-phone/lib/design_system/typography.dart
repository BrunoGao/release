import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// 企业级设计系统 - 文字样式规范
/// 基于8px网格系统的排版设计
class DSTypography {
  DSTypography._();

  // ==================== 字体家族 ====================
  
  /// 主要字体 - 用于标题和重要内容
  static String get primaryFont => GoogleFonts.nunito().fontFamily!;
  
  /// 次要字体 - 用于正文内容
  static String get secondaryFont => GoogleFonts.roboto().fontFamily!;
  
  /// 单等宽字体 - 用于代码和数据展示
  static String get monospaceFont => GoogleFonts.robotoMono().fontFamily!;

  // ==================== 字体大小 ====================
  
  /// 特大标题 - 32px
  static const double displayLarge = 32.0;
  
  /// 大标题 - 28px
  static const double displayMedium = 28.0;
  
  /// 中等标题 - 24px
  static const double displaySmall = 24.0;
  
  /// 主要标题 - 22px
  static const double headlineLarge = 22.0;
  
  /// 次要标题 - 20px
  static const double headlineMedium = 20.0;
  
  /// 小标题 - 18px
  static const double headlineSmall = 18.0;
  
  /// 卡片标题 - 16px
  static const double titleLarge = 16.0;
  
  /// 列表标题 - 14px
  static const double titleMedium = 14.0;
  
  /// 小标题 - 12px
  static const double titleSmall = 12.0;
  
  /// 正文大 - 16px
  static const double bodyLarge = 16.0;
  
  /// 正文中 - 14px
  static const double bodyMedium = 14.0;
  
  /// 正文小 - 12px
  static const double bodySmall = 12.0;
  
  /// 标签大 - 14px
  static const double labelLarge = 14.0;
  
  /// 标签中 - 12px
  static const double labelMedium = 12.0;
  
  /// 标签小 - 10px
  static const double labelSmall = 10.0;

  // ==================== 字重 ====================
  
  static const FontWeight thin = FontWeight.w100;
  static const FontWeight extraLight = FontWeight.w200;
  static const FontWeight light = FontWeight.w300;
  static const FontWeight regular = FontWeight.w400;
  static const FontWeight medium = FontWeight.w500;
  static const FontWeight semiBold = FontWeight.w600;
  static const FontWeight bold = FontWeight.w700;
  static const FontWeight extraBold = FontWeight.w800;
  static const FontWeight black = FontWeight.w900;

  // ==================== 行高比例 ====================
  
  static const double tightHeight = 1.1;
  static const double normalHeight = 1.4;
  static const double relaxedHeight = 1.6;
  static const double looseHeight = 1.8;

  // ==================== 字间距 ====================
  
  static const double tightSpacing = -0.5;
  static const double normalSpacing = 0.0;
  static const double wideSpacing = 0.5;
  static const double extraWideSpacing = 1.0;

  // ==================== 预定义文字样式 ====================
  
  /// 构建完整的文字主题
  static TextTheme buildTextTheme(Color baseColor) {
    return TextTheme(
      // 展示级标题
      displayLarge: GoogleFonts.nunito(
        fontSize: displayLarge,
        fontWeight: bold,
        color: baseColor,
        letterSpacing: tightSpacing,
        height: tightHeight,
      ),
      displayMedium: GoogleFonts.nunito(
        fontSize: displayMedium,
        fontWeight: bold,
        color: baseColor,
        letterSpacing: tightSpacing,
        height: tightHeight,
      ),
      displaySmall: GoogleFonts.nunito(
        fontSize: displaySmall,
        fontWeight: bold,
        color: baseColor,
        letterSpacing: tightSpacing,
        height: normalHeight,
      ),
      
      // 标题级文字
      headlineLarge: GoogleFonts.nunito(
        fontSize: headlineLarge,
        fontWeight: semiBold,
        color: baseColor,
        height: normalHeight,
      ),
      headlineMedium: GoogleFonts.nunito(
        fontSize: headlineMedium,
        fontWeight: semiBold,
        color: baseColor,
        height: normalHeight,
      ),
      headlineSmall: GoogleFonts.nunito(
        fontSize: headlineSmall,
        fontWeight: semiBold,
        color: baseColor,
        height: normalHeight,
      ),
      
      // 标题文字
      titleLarge: GoogleFonts.nunito(
        fontSize: titleLarge,
        fontWeight: medium,
        color: baseColor,
        height: normalHeight,
      ),
      titleMedium: GoogleFonts.nunito(
        fontSize: titleMedium,
        fontWeight: medium,
        color: baseColor,
        height: normalHeight,
      ),
      titleSmall: GoogleFonts.nunito(
        fontSize: titleSmall,
        fontWeight: medium,
        color: baseColor,
        height: normalHeight,
      ),
      
      // 正文文字
      bodyLarge: GoogleFonts.roboto(
        fontSize: bodyLarge,
        fontWeight: regular,
        color: baseColor.withOpacity(0.87),
        height: relaxedHeight,
      ),
      bodyMedium: GoogleFonts.roboto(
        fontSize: bodyMedium,
        fontWeight: regular,
        color: baseColor.withOpacity(0.87),
        height: relaxedHeight,
      ),
      bodySmall: GoogleFonts.roboto(
        fontSize: bodySmall,
        fontWeight: regular,
        color: baseColor.withOpacity(0.6),
        height: normalHeight,
      ),
      
      // 标签文字
      labelLarge: GoogleFonts.roboto(
        fontSize: labelLarge,
        fontWeight: medium,
        color: baseColor,
        height: normalHeight,
      ),
      labelMedium: GoogleFonts.roboto(
        fontSize: labelMedium,
        fontWeight: medium,
        color: baseColor,
        height: normalHeight,
      ),
      labelSmall: GoogleFonts.roboto(
        fontSize: labelSmall,
        fontWeight: medium,
        color: baseColor.withOpacity(0.6),
        height: normalHeight,
        letterSpacing: wideSpacing,
      ),
    );
  }

  // ==================== 特殊用途文字样式 ====================
  
  /// 数值显示样式 - 用于健康数据等数字展示
  static TextStyle numberDisplay(Color color, {double? fontSize}) => GoogleFonts.robotoMono(
    fontSize: fontSize ?? 24.0,
    fontWeight: bold,
    color: color,
    height: tightHeight,
  );
  
  /// 单位样式 - 用于数值单位
  static TextStyle unit(Color color, {double? fontSize}) => GoogleFonts.roboto(
    fontSize: fontSize ?? 12.0,
    fontWeight: regular,
    color: color.withOpacity(0.6),
    height: normalHeight,
  );
  
  /// 卡片标题样式
  static TextStyle cardTitle(Color color) => GoogleFonts.nunito(
    fontSize: titleLarge,
    fontWeight: semiBold,
    color: color,
    height: normalHeight,
  );
  
  /// 卡片副标题样式
  static TextStyle cardSubtitle(Color color) => GoogleFonts.roboto(
    fontSize: bodyMedium,
    fontWeight: regular,
    color: color.withOpacity(0.7),
    height: normalHeight,
  );
  
  /// 按钮文字样式
  static TextStyle button(Color color) => GoogleFonts.nunito(
    fontSize: labelLarge,
    fontWeight: semiBold,
    color: color,
    height: normalHeight,
    letterSpacing: wideSpacing,
  );
  
  /// 标签样式
  static TextStyle chip(Color color) => GoogleFonts.roboto(
    fontSize: labelMedium,
    fontWeight: medium,
    color: color,
    height: normalHeight,
  );
  
  /// 错误信息样式
  static TextStyle error(Color color) => GoogleFonts.roboto(
    fontSize: bodySmall,
    fontWeight: regular,
    color: color,
    height: normalHeight,
  );
  
  /// 提示信息样式
  static TextStyle caption(Color color) => GoogleFonts.roboto(
    fontSize: bodySmall,
    fontWeight: regular,
    color: color.withOpacity(0.6),
    height: normalHeight,
  );
}