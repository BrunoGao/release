import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'colors.dart';
import 'typography.dart';

/// 企业级设计系统主题构建器
/// 提供完整的主题配置，包括颜色、字体、组件样式等
class DSTheme {
  // ==================== 主题构建方法 ====================
  
  /// 构建浅色主题
  static ThemeData buildLightTheme() {
    return ThemeData(
      // 基础设置
      useMaterial3: true,
      brightness: Brightness.light,
      
      // 颜色方案
      colorScheme: _buildLightColorScheme(),
      
      // 字体主题
      textTheme: DSTypography.buildTextTheme(DSColors.textPrimaryLight),
      
      // AppBar主题
      appBarTheme: _buildAppBarTheme(true),
      
      // 卡片主题
      cardTheme: _buildCardTheme(true),
      
      // 按钮主题
      elevatedButtonTheme: _buildElevatedButtonTheme(true),
      textButtonTheme: _buildTextButtonTheme(true),
      outlinedButtonTheme: _buildOutlinedButtonTheme(true),
      
      // 输入框主题
      inputDecorationTheme: _buildInputDecorationTheme(true),
      
      // 底部导航主题
      bottomNavigationBarTheme: _buildBottomNavigationBarTheme(true),
      
      // 对话框主题
      dialogTheme: _buildDialogTheme(true),
      
      // 列表主题
      listTileTheme: _buildListTileTheme(true),
      
      // 分隔符主题
      dividerTheme: _buildDividerTheme(true),
      
      // Chip主题
      chipTheme: _buildChipTheme(true),
      
      // Switch主题
      switchTheme: _buildSwitchTheme(true),
      
      // 进度条主题
      progressIndicatorTheme: _buildProgressIndicatorTheme(true),
      
      // 浮动按钮主题
      floatingActionButtonTheme: _buildFloatingActionButtonTheme(true),
      
      // 抽屉主题
      drawerTheme: _buildDrawerTheme(true),
      
      // SnackBar主题
      snackBarTheme: _buildSnackBarTheme(true),
      
      // 其他设置
      scaffoldBackgroundColor: DSColors.backgroundLight,
      canvasColor: DSColors.surfaceLight,
      shadowColor: DSColors.shadowLight,
      splashColor: DSColors.primary500.withOpacity(0.1),
      highlightColor: DSColors.primary500.withOpacity(0.05),
      
      // 系统UI设置
      systemOverlayStyle: SystemUiOverlayStyle.dark,
    );
  }

  /// 构建暗色主题
  static ThemeData buildDarkTheme() {
    return ThemeData(
      // 基础设置
      useMaterial3: true,
      brightness: Brightness.dark,
      
      // 颜色方案
      colorScheme: _buildDarkColorScheme(),
      
      // 字体主题
      textTheme: DSTypography.buildTextTheme(DSColors.textPrimaryDark),
      
      // AppBar主题
      appBarTheme: _buildAppBarTheme(false),
      
      // 卡片主题
      cardTheme: _buildCardTheme(false),
      
      // 按钮主题
      elevatedButtonTheme: _buildElevatedButtonTheme(false),
      textButtonTheme: _buildTextButtonTheme(false),
      outlinedButtonTheme: _buildOutlinedButtonTheme(false),
      
      // 输入框主题
      inputDecorationTheme: _buildInputDecorationTheme(false),
      
      // 底部导航主题
      bottomNavigationBarTheme: _buildBottomNavigationBarTheme(false),
      
      // 对话框主题
      dialogTheme: _buildDialogTheme(false),
      
      // 列表主题
      listTileTheme: _buildListTileTheme(false),
      
      // 分隔符主题
      dividerTheme: _buildDividerTheme(false),
      
      // Chip主题
      chipTheme: _buildChipTheme(false),
      
      // Switch主题
      switchTheme: _buildSwitchTheme(false),
      
      // 进度条主题
      progressIndicatorTheme: _buildProgressIndicatorTheme(false),
      
      // 浮动按钮主题
      floatingActionButtonTheme: _buildFloatingActionButtonTheme(false),
      
      // 抽屉主题
      drawerTheme: _buildDrawerTheme(false),
      
      // SnackBar主题
      snackBarTheme: _buildSnackBarTheme(false),
      
      // 其他设置
      scaffoldBackgroundColor: DSColors.backgroundDark,
      canvasColor: DSColors.surfaceDark,
      shadowColor: DSColors.shadowDark,
      splashColor: DSColors.primary400.withOpacity(0.1),
      highlightColor: DSColors.primary400.withOpacity(0.05),
      
      // 系统UI设置
      systemOverlayStyle: SystemUiOverlayStyle.light,
    );
  }

  // ==================== 颜色方案构建 ====================
  
  static ColorScheme _buildLightColorScheme() {
    return ColorScheme.fromSeed(
      seedColor: DSColors.primary500,
      brightness: Brightness.light,
      primary: DSColors.primary500,
      primaryContainer: DSColors.primary100,
      secondary: DSColors.secondary500,
      secondaryContainer: DSColors.secondary100,
      tertiary: DSColors.info500,
      tertiaryContainer: DSColors.info100,
      error: DSColors.error500,
      errorContainer: DSColors.error100,
      surface: DSColors.surfaceLight,
      background: DSColors.backgroundLight,
      onPrimary: DSColors.white,
      onSecondary: DSColors.white,
      onTertiary: DSColors.white,
      onError: DSColors.white,
      onSurface: DSColors.textPrimaryLight,
      onBackground: DSColors.textPrimaryLight,
      outline: DSColors.borderLight,
      shadow: DSColors.shadowLight,
    );
  }

  static ColorScheme _buildDarkColorScheme() {
    return ColorScheme.fromSeed(
      seedColor: DSColors.primary500,
      brightness: Brightness.dark,
      primary: DSColors.primary400,
      primaryContainer: DSColors.primary800,
      secondary: DSColors.secondary400,
      secondaryContainer: DSColors.secondary800,
      tertiary: DSColors.info400,
      tertiaryContainer: DSColors.info800,
      error: DSColors.error400,
      errorContainer: DSColors.error800,
      surface: DSColors.surfaceDark,
      background: DSColors.backgroundDark,
      onPrimary: DSColors.black,
      onSecondary: DSColors.black,
      onTertiary: DSColors.black,
      onError: DSColors.black,
      onSurface: DSColors.textPrimaryDark,
      onBackground: DSColors.textPrimaryDark,
      outline: DSColors.borderDark,
      shadow: DSColors.shadowDark,
    );
  }

  // ==================== 组件主题构建 ====================
  
  static AppBarTheme _buildAppBarTheme(bool isLight) {
    return AppBarTheme(
      elevation: 0,
      scrolledUnderElevation: 4,
      backgroundColor: isLight ? DSColors.backgroundLight : DSColors.backgroundDark,
      foregroundColor: isLight ? DSColors.textPrimaryLight : DSColors.textPrimaryDark,
      titleTextStyle: DSTypography.titleLarge.copyWith(
        color: isLight ? DSColors.textPrimaryLight : DSColors.textPrimaryDark,
      ),
      centerTitle: true,
      iconTheme: IconThemeData(
        color: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
        size: 24,
      ),
      actionsIconTheme: IconThemeData(
        color: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
        size: 24,
      ),
      systemOverlayStyle: isLight 
          ? SystemUiOverlayStyle.dark 
          : SystemUiOverlayStyle.light,
    );
  }

  static CardTheme _buildCardTheme(bool isLight) {
    return CardTheme(
      elevation: 2,
      shadowColor: isLight ? DSColors.shadowLight : DSColors.shadowDark,
      surfaceTintColor: Colors.transparent,
      color: isLight ? DSColors.cardLight : DSColors.cardDark,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      margin: const EdgeInsets.all(8),
    );
  }

  static ElevatedButtonThemeData _buildElevatedButtonTheme(bool isLight) {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: DSColors.primary500,
        foregroundColor: DSColors.white,
        disabledBackgroundColor: isLight ? DSColors.gray300 : DSColors.gray600,
        disabledForegroundColor: isLight ? DSColors.gray500 : DSColors.gray400,
        elevation: 2,
        shadowColor: isLight ? DSColors.shadowLight : DSColors.shadowDark,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        textStyle: DSTypography.buttonMedium,
        minimumSize: const Size(64, 48),
      ),
    );
  }

  static TextButtonThemeData _buildTextButtonTheme(bool isLight) {
    return TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: DSColors.primary500,
        disabledForegroundColor: isLight ? DSColors.gray500 : DSColors.gray400,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        textStyle: DSTypography.buttonMedium,
        minimumSize: const Size(64, 40),
      ),
    );
  }

  static OutlinedButtonThemeData _buildOutlinedButtonTheme(bool isLight) {
    return OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: DSColors.primary500,
        disabledForegroundColor: isLight ? DSColors.gray500 : DSColors.gray400,
        side: BorderSide(
          color: DSColors.primary500,
          width: 1.5,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        textStyle: DSTypography.buttonMedium,
        minimumSize: const Size(64, 48),
      ),
    );
  }

  static InputDecorationTheme _buildInputDecorationTheme(bool isLight) {
    return InputDecorationTheme(
      filled: true,
      fillColor: isLight ? DSColors.gray100 : DSColors.gray800,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: isLight ? DSColors.borderLight : DSColors.borderDark,
        ),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: isLight ? DSColors.borderLight : DSColors.borderDark,
        ),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: DSColors.primary500,
          width: 2,
        ),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: DSColors.error500,
        ),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: DSColors.error500,
          width: 2,
        ),
      ),
      labelStyle: DSTypography.bodyMedium.copyWith(
        color: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
      ),
      hintStyle: DSTypography.bodyMedium.copyWith(
        color: isLight ? DSColors.textTertiaryLight : DSColors.textTertiaryDark,
      ),
      errorStyle: DSTypography.bodySmall.copyWith(
        color: DSColors.error500,
      ),
    );
  }

  static BottomNavigationBarThemeData _buildBottomNavigationBarTheme(bool isLight) {
    return BottomNavigationBarThemeData(
      type: BottomNavigationBarType.fixed,
      backgroundColor: isLight ? DSColors.surfaceLight : DSColors.surfaceDark,
      selectedItemColor: DSColors.primary500,
      unselectedItemColor: isLight ? DSColors.textTertiaryLight : DSColors.textTertiaryDark,
      selectedLabelStyle: DSTypography.navigationActive,
      unselectedLabelStyle: DSTypography.navigationInactive,
      elevation: 8,
      showSelectedLabels: true,
      showUnselectedLabels: true,
    );
  }

  static DialogTheme _buildDialogTheme(bool isLight) {
    return DialogTheme(
      backgroundColor: isLight ? DSColors.surfaceLight : DSColors.surfaceDark,
      surfaceTintColor: Colors.transparent,
      elevation: 8,
      shadowColor: isLight ? DSColors.shadowLight : DSColors.shadowDark,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      titleTextStyle: DSTypography.titleLarge.copyWith(
        color: isLight ? DSColors.textPrimaryLight : DSColors.textPrimaryDark,
      ),
      contentTextStyle: DSTypography.bodyMedium.copyWith(
        color: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
      ),
    );
  }

  static ListTileThemeData _buildListTileTheme(bool isLight) {
    return ListTileThemeData(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      titleTextStyle: DSTypography.bodyMedium.copyWith(
        color: isLight ? DSColors.textPrimaryLight : DSColors.textPrimaryDark,
      ),
      subtitleTextStyle: DSTypography.bodySmall.copyWith(
        color: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
      ),
      iconColor: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    );
  }

  static DividerThemeData _buildDividerTheme(bool isLight) {
    return DividerThemeData(
      color: isLight ? DSColors.borderLight : DSColors.borderDark,
      thickness: 1,
      space: 1,
    );
  }

  static ChipThemeData _buildChipTheme(bool isLight) {
    return ChipThemeData(
      backgroundColor: isLight ? DSColors.gray100 : DSColors.gray800,
      selectedColor: DSColors.primary100,
      deleteIconColor: isLight ? DSColors.textSecondaryLight : DSColors.textSecondaryDark,
      disabledColor: isLight ? DSColors.gray200 : DSColors.gray700,
      labelStyle: DSTypography.labelSmall.copyWith(
        color: isLight ? DSColors.textPrimaryLight : DSColors.textPrimaryDark,
      ),
      secondaryLabelStyle: DSTypography.labelSmall.copyWith(
        color: DSColors.primary500,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      elevation: 0,
      pressElevation: 2,
    );
  }

  static SwitchThemeData _buildSwitchTheme(bool isLight) {
    return SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return DSColors.white;
        }
        return isLight ? DSColors.gray500 : DSColors.gray400;
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return DSColors.primary500;
        }
        return isLight ? DSColors.gray300 : DSColors.gray600;
      }),
    );
  }

  static ProgressIndicatorThemeData _buildProgressIndicatorTheme(bool isLight) {
    return ProgressIndicatorThemeData(
      color: DSColors.primary500,
      linearTrackColor: isLight ? DSColors.gray200 : DSColors.gray700,
      circularTrackColor: isLight ? DSColors.gray200 : DSColors.gray700,
    );
  }

  static FloatingActionButtonThemeData _buildFloatingActionButtonTheme(bool isLight) {
    return FloatingActionButtonThemeData(
      backgroundColor: DSColors.primary500,
      foregroundColor: DSColors.white,
      elevation: 4,
      focusElevation: 6,
      hoverElevation: 8,
      highlightElevation: 12,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    );
  }

  static DrawerThemeData _buildDrawerTheme(bool isLight) {
    return DrawerThemeData(
      backgroundColor: isLight ? DSColors.surfaceLight : DSColors.surfaceDark,
      surfaceTintColor: Colors.transparent,
      elevation: 8,
      shadowColor: isLight ? DSColors.shadowLight : DSColors.shadowDark,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topRight: Radius.circular(16),
          bottomRight: Radius.circular(16),
        ),
      ),
    );
  }

  static SnackBarThemeData _buildSnackBarTheme(bool isLight) {
    return SnackBarThemeData(
      backgroundColor: isLight ? DSColors.gray800 : DSColors.gray200,
      contentTextStyle: DSTypography.bodyMedium.copyWith(
        color: isLight ? DSColors.white : DSColors.black,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      behavior: SnackBarBehavior.floating,
      elevation: 4,
    );
  }
}