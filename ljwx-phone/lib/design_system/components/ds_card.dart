import 'package:flutter/material.dart';
import '../design_system.dart';

/// 企业级卡片组件基类
/// 提供统一的卡片样式和交互行为
class DSCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final EdgeInsets? margin;
  final double? elevation;
  final BorderRadius? borderRadius;
  final Color? backgroundColor;
  final Color? shadowColor;
  final VoidCallback? onTap;
  final bool isLoading;
  final bool isDisabled;
  final Widget? loadingWidget;
  final List<BoxShadow>? customShadows;
  final Gradient? gradient;
  final Border? border;

  const DSCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.elevation,
    this.borderRadius,
    this.backgroundColor,
    this.shadowColor,
    this.onTap,
    this.isLoading = false,
    this.isDisabled = false,
    this.loadingWidget,
    this.customShadows,
    this.gradient,
    this.border,
  });

  /// 标准卡片 - 默认样式
  factory DSCard.standard({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 2,
      borderRadius: DSRadius.allLG,
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 信息卡片 - 用于显示重要信息
  factory DSCard.info({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 4,
      borderRadius: DSRadius.allLG,
      customShadows: DSShadow.lg,
      border: Border.all(color: DSColors.info500.withOpacity(0.2), width: 1),
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 警告卡片 - 用于警告信息
  factory DSCard.warning({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 4,
      borderRadius: DSRadius.allLG,
      customShadows: DSShadow.glow(DSColors.warning500),
      border: Border.all(color: DSColors.warning500.withOpacity(0.3), width: 1),
      backgroundColor: DSColors.warning50,
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 错误卡片 - 用于错误信息
  factory DSCard.error({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 4,
      borderRadius: DSRadius.allLG,
      customShadows: DSShadow.glow(DSColors.error500),
      border: Border.all(color: DSColors.error500.withOpacity(0.3), width: 1),
      backgroundColor: DSColors.error50,
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 成功卡片 - 用于成功信息
  factory DSCard.success({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 4,
      borderRadius: DSRadius.allLG,
      customShadows: DSShadow.glow(DSColors.success500),
      border: Border.all(color: DSColors.success500.withOpacity(0.3), width: 1),
      backgroundColor: DSColors.success50,
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 渐变卡片 - 用于突出显示
  factory DSCard.gradient({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
    Gradient? gradient,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 6,
      borderRadius: DSRadius.allLG,
      gradient: gradient ?? DSColors.primaryGradient,
      customShadows: DSShadow.xl,
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  /// 扁平卡片 - 无阴影
  factory DSCard.flat({
    Key? key,
    required Widget child,
    EdgeInsets? padding,
    EdgeInsets? margin,
    VoidCallback? onTap,
    bool isLoading = false,
    bool isDisabled = false,
    Color? backgroundColor,
  }) {
    return DSCard(
      key: key,
      padding: padding ?? DSSpacing.allLG,
      margin: margin ?? DSSpacing.verticalMD,
      elevation: 0,
      borderRadius: DSRadius.allLG,
      backgroundColor: backgroundColor,
      border: Border.all(color: DSColors.gray200, width: 1),
      onTap: onTap,
      isLoading: isLoading,
      isDisabled: isDisabled,
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // 确定背景颜色
    Color? cardBackgroundColor = backgroundColor;
    if (cardBackgroundColor == null) {
      cardBackgroundColor = isDark ? DSColors.surfaceDark : DSColors.surfaceLight;
    }

    // 构建装饰
    BoxDecoration decoration = BoxDecoration(
      color: gradient == null ? cardBackgroundColor : null,
      gradient: gradient,
      borderRadius: borderRadius ?? DSRadius.allLG,
      border: border,
      boxShadow: customShadows ?? (elevation != null && elevation! > 0 
        ? (elevation! <= 2 ? DSShadow.sm : 
           elevation! <= 4 ? DSShadow.md :
           elevation! <= 8 ? DSShadow.lg : DSShadow.xl)
        : null),
    );

    // 构建内容
    Widget content = Container(
      padding: padding ?? DSSpacing.allLG,
      margin: margin,
      decoration: decoration,
      child: isLoading 
        ? _buildLoadingContent()
        : child,
    );

    // 添加交互
    if (onTap != null && !isDisabled && !isLoading) {
      content = Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          borderRadius: borderRadius ?? DSRadius.allLG,
          splashColor: DSColors.primary500.withOpacity(0.1),
          highlightColor: DSColors.primary500.withOpacity(0.05),
          child: content,
        ),
      );
    }

    // 禁用状态
    if (isDisabled) {
      content = Opacity(
        opacity: 0.6,
        child: content,
      );
    }

    return content;
  }

  Widget _buildLoadingContent() {
    return Stack(
      children: [
        Opacity(
          opacity: 0.3,
          child: child,
        ),
        Positioned.fill(
          child: Center(
            child: loadingWidget ?? 
              Container(
                padding: DSSpacing.allMD,
                decoration: BoxDecoration(
                  color: DSColors.white.withOpacity(0.9),
                  borderRadius: DSRadius.allMD,
                ),
                child: const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                  ),
                ),
              ),
          ),
        ),
      ],
    );
  }
}