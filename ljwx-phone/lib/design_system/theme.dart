import 'package:flutter/material.dart';
import 'colors.dart';
import 'typography.dart';
import 'spacing.dart';

/// 企业级设计系统 - 主题配置
/// 整合色彩、文字、间距等设计元素的完整主题
class DSTheme {
  DSTheme._();

  // ==================== 主题构建器 ====================
  
  /// 构建浅色主题
  static ThemeData buildLightTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      
      // 基础色彩方案
      colorScheme: ColorScheme.fromSeed(
        seedColor: DSColors.primary500,
        brightness: Brightness.light,
        primary: DSColors.primary500,
        onPrimary: DSColors.white,
        secondary: DSColors.secondary500,
        onSecondary: DSColors.white,
        error: DSColors.error500,
        onError: DSColors.white,
        surface: DSColors.surfaceLight,
        onSurface: DSColors.gray900,
        background: DSColors.backgroundLight,
        onBackground: DSColors.gray900,
      ),
      
      // 脚手架背景
      scaffoldBackgroundColor: DSColors.backgroundLight,
      
      // 文字主题
      textTheme: DSTypography.buildTextTheme(DSColors.gray900),
      
      // AppBar 主题
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 1,
        backgroundColor: DSColors.surfaceLight,
        foregroundColor: DSColors.gray900,
        titleTextStyle: DSTypography.cardTitle(DSColors.gray900),
        toolbarHeight: DSSpacing.toolbarHeight,
        shape: const Border(
          bottom: BorderSide(
            color: DSColors.gray200,
            width: 0.5,
          ),
        ),
      ),
      
      // 卡片主题
      cardTheme: CardThemeData(
        elevation: 2,
        shadowColor: DSColors.shadowLight,
        clipBehavior: Clip.antiAlias,
        margin: DSSpacing.verticalMD,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allLG,
        ),
        color: DSColors.surfaceLight,
      ),
      
      // 按钮主题
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          shadowColor: DSColors.shadowLight,
          padding: DSSpacing.symmetric(horizontal: DSSpacing.xl, vertical: DSSpacing.md),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allMD,
          ),
          backgroundColor: DSColors.primary500,
          foregroundColor: DSColors.white,
          textStyle: DSTypography.button(DSColors.white),
        ),
      ),
      
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: DSSpacing.symmetric(horizontal: DSSpacing.xl, vertical: DSSpacing.md),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allMD,
          ),
          side: const BorderSide(color: DSColors.primary500, width: 1.5),
          foregroundColor: DSColors.primary500,
          textStyle: DSTypography.button(DSColors.primary500),
        ),
      ),
      
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          padding: DSSpacing.symmetric(horizontal: DSSpacing.lg, vertical: DSSpacing.sm),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allSM,
          ),
          foregroundColor: DSColors.primary500,
          textStyle: DSTypography.button(DSColors.primary500),
        ),
      ),
      
      // 图标主题
      iconTheme: const IconThemeData(
        color: DSColors.primary500,
        size: 24,
      ),
      
      // 输入框主题
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DSColors.gray50,
        contentPadding: DSSpacing.allLG,
        border: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.gray300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.gray300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.primary500, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.error500),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.error500, width: 2),
        ),
      ),
      
      // 标签主题
      chipTheme: ChipThemeData(
        backgroundColor: DSColors.gray100,
        labelStyle: DSTypography.chip(DSColors.gray700),
        padding: DSSpacing.symmetric(horizontal: DSSpacing.md),
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allFull,
        ),
        side: BorderSide.none,
      ),
      
      // 提示条主题
      snackBarTheme: SnackBarThemeData(
        backgroundColor: DSColors.gray800,
        contentTextStyle: DSTypography.button(DSColors.white),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allMD,
        ),
        elevation: 8,
      ),
      
      // 底部导航主题
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        type: BottomNavigationBarType.fixed,
        backgroundColor: DSColors.surfaceLight,
        selectedItemColor: DSColors.primary500,
        unselectedItemColor: DSColors.gray500,
        selectedLabelStyle: DSTypography.caption(DSColors.primary500),
        unselectedLabelStyle: DSTypography.caption(DSColors.gray500),
        elevation: 8,
      ),
      
      // 对话框主题
      dialogTheme: DialogThemeData(
        backgroundColor: DSColors.surfaceLight,
        elevation: 24,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allXL,
        ),
        titleTextStyle: DSTypography.cardTitle(DSColors.gray900),
        contentTextStyle: DSTypography.cardSubtitle(DSColors.gray700),
      ),
      
      // 底部模态框主题
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: DSColors.surfaceLight,
        elevation: 16,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        clipBehavior: Clip.antiAlias,
      ),
    );
  }
  
  /// 构建深色主题
  static ThemeData buildDarkTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      
      // 基础色彩方案
      colorScheme: ColorScheme.fromSeed(
        seedColor: DSColors.primary500,
        brightness: Brightness.dark,
        primary: DSColors.primary400,
        onPrimary: DSColors.gray900,
        secondary: DSColors.secondary400,
        onSecondary: DSColors.gray900,
        error: DSColors.error500,
        onError: DSColors.white,
        surface: DSColors.surfaceDark,
        onSurface: DSColors.white,
        background: DSColors.backgroundDark,
        onBackground: DSColors.white,
      ),
      
      // 脚手架背景
      scaffoldBackgroundColor: DSColors.backgroundDark,
      
      // 文字主题
      textTheme: DSTypography.buildTextTheme(DSColors.white),
      
      // AppBar 主题
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 1,
        backgroundColor: DSColors.surfaceDark,
        foregroundColor: DSColors.white,
        titleTextStyle: DSTypography.cardTitle(DSColors.white),
        toolbarHeight: DSSpacing.toolbarHeight,
        shape: const Border(
          bottom: BorderSide(
            color: DSColors.dark200,
            width: 0.5,
          ),
        ),
      ),
      
      // 卡片主题
      cardTheme: CardThemeData(
        elevation: 3,
        shadowColor: DSColors.shadowDark,
        clipBehavior: Clip.antiAlias,
        margin: DSSpacing.verticalMD,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allLG,
        ),
        color: DSColors.surfaceDark,
      ),
      
      // 按钮主题
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          shadowColor: DSColors.shadowDark,
          padding: DSSpacing.symmetric(horizontal: DSSpacing.xl, vertical: DSSpacing.md),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allMD,
          ),
          backgroundColor: DSColors.primary500,
          foregroundColor: DSColors.white,
          textStyle: DSTypography.button(DSColors.white),
        ),
      ),
      
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: DSSpacing.symmetric(horizontal: DSSpacing.xl, vertical: DSSpacing.md),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allMD,
          ),
          side: const BorderSide(color: DSColors.primary400, width: 1.5),
          foregroundColor: DSColors.primary400,
          textStyle: DSTypography.button(DSColors.primary400),
        ),
      ),
      
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          padding: DSSpacing.symmetric(horizontal: DSSpacing.lg, vertical: DSSpacing.sm),
          minimumSize: Size(0, DSSpacing.buttonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: DSRadius.allSM,
          ),
          foregroundColor: DSColors.primary400,
          textStyle: DSTypography.button(DSColors.primary400),
        ),
      ),
      
      // 图标主题
      iconTheme: const IconThemeData(
        color: DSColors.primary400,
        size: 24,
      ),
      
      // 输入框主题
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DSColors.containerDark,
        contentPadding: DSSpacing.allLG,
        border: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.dark200),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.dark200),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.primary400, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.error500),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: DSRadius.allMD,
          borderSide: const BorderSide(color: DSColors.error500, width: 2),
        ),
      ),
      
      // 标签主题
      chipTheme: ChipThemeData(
        backgroundColor: DSColors.containerDark,
        labelStyle: DSTypography.chip(DSColors.white),
        padding: DSSpacing.symmetric(horizontal: DSSpacing.md),
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allFull,
        ),
        side: BorderSide.none,
      ),
      
      // 提示条主题
      snackBarTheme: SnackBarThemeData(
        backgroundColor: DSColors.gray200,
        contentTextStyle: DSTypography.button(DSColors.gray900),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allMD,
        ),
        elevation: 8,
      ),
      
      // 底部导航主题
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        type: BottomNavigationBarType.fixed,
        backgroundColor: DSColors.surfaceDark,
        selectedItemColor: DSColors.primary400,
        unselectedItemColor: DSColors.gray400,
        selectedLabelStyle: DSTypography.caption(DSColors.primary400),
        unselectedLabelStyle: DSTypography.caption(DSColors.gray400),
        elevation: 8,
      ),
      
      // 对话框主题
      dialogTheme: DialogThemeData(
        backgroundColor: DSColors.surfaceDark,
        elevation: 24,
        shape: RoundedRectangleBorder(
          borderRadius: DSRadius.allXL,
        ),
        titleTextStyle: DSTypography.cardTitle(DSColors.white),
        contentTextStyle: DSTypography.cardSubtitle(DSColors.gray300),
      ),
      
      // 底部模态框主题
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: DSColors.surfaceDark,
        elevation: 16,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        clipBehavior: Clip.antiAlias,
      ),
    );
  }
}