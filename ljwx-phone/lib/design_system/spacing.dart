import 'package:flutter/material.dart';

/// 企业级设计系统 - 间距规范
/// 基于8px网格系统的间距设计
class DSSpacing {
  DSSpacing._();

  // ==================== 基础间距单位 ====================
  
  /// 基础单位 - 4px
  static const double xs = 4.0;
  
  /// 小间距 - 8px
  static const double sm = 8.0;
  
  /// 中间距 - 12px
  static const double md = 12.0;
  
  /// 大间距 - 16px
  static const double lg = 16.0;
  
  /// 超大间距 - 20px
  static const double xl = 20.0;
  
  /// 特大间距 - 24px
  static const double xxl = 24.0;
  
  /// 巨大间距 - 32px
  static const double xxxl = 32.0;
  
  /// 超级间距 - 40px
  static const double huge = 40.0;
  
  /// 页面级间距 - 48px
  static const double massive = 48.0;

  // ==================== 特定用途间距 ====================
  
  /// 页面内边距
  static const double pagePadding = lg;
  
  /// 卡片内边距
  static const double cardPadding = lg;
  
  /// 卡片间距
  static const double cardMargin = md;
  
  /// 列表项高度
  static const double listItemHeight = 56.0;
  
  /// 按钮高度
  static const double buttonHeight = 48.0;
  
  /// 输入框高度
  static const double inputHeight = 48.0;
  
  /// 工具栏高度
  static const double toolbarHeight = 56.0;
  
  /// 底部导航高度
  static const double bottomNavHeight = 80.0;

  // ==================== 预定义边距对象 ====================
  
  /// 零边距
  static const EdgeInsets zero = EdgeInsets.zero;
  
  /// 均匀小边距
  static const EdgeInsets allXS = EdgeInsets.all(xs);
  static const EdgeInsets allSM = EdgeInsets.all(sm);
  static const EdgeInsets allMD = EdgeInsets.all(md);
  static const EdgeInsets allLG = EdgeInsets.all(lg);
  static const EdgeInsets allXL = EdgeInsets.all(xl);
  static const EdgeInsets allXXL = EdgeInsets.all(xxl);
  
  /// 水平边距
  static const EdgeInsets horizontalXS = EdgeInsets.symmetric(horizontal: xs);
  static const EdgeInsets horizontalSM = EdgeInsets.symmetric(horizontal: sm);
  static const EdgeInsets horizontalMD = EdgeInsets.symmetric(horizontal: md);
  static const EdgeInsets horizontalLG = EdgeInsets.symmetric(horizontal: lg);
  static const EdgeInsets horizontalXL = EdgeInsets.symmetric(horizontal: xl);
  static const EdgeInsets horizontalXXL = EdgeInsets.symmetric(horizontal: xxl);
  
  /// 垂直边距
  static const EdgeInsets verticalXS = EdgeInsets.symmetric(vertical: xs);
  static const EdgeInsets verticalSM = EdgeInsets.symmetric(vertical: sm);
  static const EdgeInsets verticalMD = EdgeInsets.symmetric(vertical: md);
  static const EdgeInsets verticalLG = EdgeInsets.symmetric(vertical: lg);
  static const EdgeInsets verticalXL = EdgeInsets.symmetric(vertical: xl);
  static const EdgeInsets verticalXXL = EdgeInsets.symmetric(vertical: xxl);
  
  /// 页面边距
  static const EdgeInsets page = EdgeInsets.all(pagePadding);
  static const EdgeInsets pageHorizontal = EdgeInsets.symmetric(horizontal: pagePadding);
  static const EdgeInsets pageVertical = EdgeInsets.symmetric(vertical: pagePadding);
  
  /// 卡片边距
  static const EdgeInsets card = EdgeInsets.all(cardPadding);
  static const EdgeInsets cardHorizontal = EdgeInsets.symmetric(horizontal: cardPadding);
  static const EdgeInsets cardVertical = EdgeInsets.symmetric(vertical: cardPadding);

  // ==================== 特殊边距组合 ====================
  
  /// 顶部边距
  static EdgeInsets onlyTop(double value) => EdgeInsets.only(top: value);
  
  /// 底部边距
  static EdgeInsets onlyBottom(double value) => EdgeInsets.only(bottom: value);
  
  /// 左侧边距
  static EdgeInsets onlyLeft(double value) => EdgeInsets.only(left: value);
  
  /// 右侧边距
  static EdgeInsets onlyRight(double value) => EdgeInsets.only(right: value);
  
  /// 自定义对称边距
  static EdgeInsets symmetric({double? horizontal, double? vertical}) =>
      EdgeInsets.symmetric(
        horizontal: horizontal ?? 0,
        vertical: vertical ?? 0,
      );
  
  /// 自定义边距
  static EdgeInsets fromLTRB(double left, double top, double right, double bottom) =>
      EdgeInsets.fromLTRB(left, top, right, bottom);

  // ==================== 间隙组件 ====================
  
  /// 水平间隙
  static Widget gapXS() => const SizedBox(width: xs);
  static Widget gapSM() => const SizedBox(width: sm);
  static Widget gapMD() => const SizedBox(width: md);
  static Widget gapLG() => const SizedBox(width: lg);
  static Widget gapXL() => const SizedBox(width: xl);
  static Widget gapXXL() => const SizedBox(width: xxl);
  
  /// 垂直间隙
  static Widget vGapXS() => const SizedBox(height: xs);
  static Widget vGapSM() => const SizedBox(height: sm);
  static Widget vGapMD() => const SizedBox(height: md);
  static Widget vGapLG() => const SizedBox(height: lg);
  static Widget vGapXL() => const SizedBox(height: xl);
  static Widget vGapXXL() => const SizedBox(height: xxl);
  
  /// 自定义间隙
  static Widget gap(double size) => SizedBox(width: size);
  static Widget vGap(double size) => SizedBox(height: size);
}

/// 企业级设计系统 - 圆角规范
class DSRadius {
  DSRadius._();

  // ==================== 基础圆角 ====================
  
  /// 无圆角
  static const double none = 0.0;
  
  /// 小圆角 - 4px
  static const double sm = 4.0;
  
  /// 中等圆角 - 8px
  static const double md = 8.0;
  
  /// 大圆角 - 12px
  static const double lg = 12.0;
  
  /// 超大圆角 - 16px
  static const double xl = 16.0;
  
  /// 特大圆角 - 20px
  static const double xxl = 20.0;
  
  /// 全圆角 - 999px
  static const double full = 999.0;

  // ==================== 预定义圆角对象 ====================
  
  /// 无圆角
  static const BorderRadius zero = BorderRadius.zero;
  
  /// 均匀圆角
  static const BorderRadius allSM = BorderRadius.all(Radius.circular(sm));
  static const BorderRadius allMD = BorderRadius.all(Radius.circular(md));
  static const BorderRadius allLG = BorderRadius.all(Radius.circular(lg));
  static const BorderRadius allXL = BorderRadius.all(Radius.circular(xl));
  static const BorderRadius allXXL = BorderRadius.all(Radius.circular(xxl));
  static const BorderRadius allFull = BorderRadius.all(Radius.circular(full));
  
  /// 顶部圆角
  static const BorderRadius topSM = BorderRadius.vertical(top: Radius.circular(sm));
  static const BorderRadius topMD = BorderRadius.vertical(top: Radius.circular(md));
  static const BorderRadius topLG = BorderRadius.vertical(top: Radius.circular(lg));
  static const BorderRadius topXL = BorderRadius.vertical(top: Radius.circular(xl));
  static const BorderRadius topXXL = BorderRadius.vertical(top: Radius.circular(xxl));
  
  /// 底部圆角
  static const BorderRadius bottomSM = BorderRadius.vertical(bottom: Radius.circular(sm));
  static const BorderRadius bottomMD = BorderRadius.vertical(bottom: Radius.circular(md));
  static const BorderRadius bottomLG = BorderRadius.vertical(bottom: Radius.circular(lg));
  static const BorderRadius bottomXL = BorderRadius.vertical(bottom: Radius.circular(xl));
  static const BorderRadius bottomXXL = BorderRadius.vertical(bottom: Radius.circular(xxl));
  
  /// 左侧圆角
  static const BorderRadius leftSM = BorderRadius.horizontal(left: Radius.circular(sm));
  static const BorderRadius leftMD = BorderRadius.horizontal(left: Radius.circular(md));
  static const BorderRadius leftLG = BorderRadius.horizontal(left: Radius.circular(lg));
  static const BorderRadius leftXL = BorderRadius.horizontal(left: Radius.circular(xl));
  static const BorderRadius leftXXL = BorderRadius.horizontal(left: Radius.circular(xxl));
  
  /// 右侧圆角
  static const BorderRadius rightSM = BorderRadius.horizontal(right: Radius.circular(sm));
  static const BorderRadius rightMD = BorderRadius.horizontal(right: Radius.circular(md));
  static const BorderRadius rightLG = BorderRadius.horizontal(right: Radius.circular(lg));
  static const BorderRadius rightXL = BorderRadius.horizontal(right: Radius.circular(xl));
  static const BorderRadius rightXXL = BorderRadius.horizontal(right: Radius.circular(xxl));
  
  /// 自定义圆角
  static BorderRadius custom(double radius) => BorderRadius.all(Radius.circular(radius));
  
  /// 特定位置圆角
  static BorderRadius only({
    double topLeft = 0,
    double topRight = 0,
    double bottomLeft = 0,
    double bottomRight = 0,
  }) => BorderRadius.only(
    topLeft: Radius.circular(topLeft),
    topRight: Radius.circular(topRight),
    bottomLeft: Radius.circular(bottomLeft),
    bottomRight: Radius.circular(bottomRight),
  );
}

/// 企业级设计系统 - 阴影规范
class DSShadow {
  DSShadow._();

  // ==================== 标准阴影 ====================
  
  /// 无阴影
  static const List<BoxShadow> none = [];
  
  /// 轻微阴影 - 1dp
  static const List<BoxShadow> sm = [
    BoxShadow(
      color: Color(0x1A000000),
      offset: Offset(0, 1),
      blurRadius: 3,
      spreadRadius: 0,
    ),
  ];
  
  /// 中等阴影 - 2dp
  static const List<BoxShadow> md = [
    BoxShadow(
      color: Color(0x1F000000),
      offset: Offset(0, 2),
      blurRadius: 6,
      spreadRadius: 0,
    ),
    BoxShadow(
      color: Color(0x0A000000),
      offset: Offset(0, 1),
      blurRadius: 2,
      spreadRadius: 0,
    ),
  ];
  
  /// 大阴影 - 4dp
  static const List<BoxShadow> lg = [
    BoxShadow(
      color: Color(0x1F000000),
      offset: Offset(0, 4),
      blurRadius: 12,
      spreadRadius: 0,
    ),
    BoxShadow(
      color: Color(0x0F000000),
      offset: Offset(0, 2),
      blurRadius: 4,
      spreadRadius: 0,
    ),
  ];
  
  /// 超大阴影 - 8dp
  static const List<BoxShadow> xl = [
    BoxShadow(
      color: Color(0x29000000),
      offset: Offset(0, 8),
      blurRadius: 24,
      spreadRadius: 0,
    ),
    BoxShadow(
      color: Color(0x14000000),
      offset: Offset(0, 4),
      blurRadius: 8,
      spreadRadius: 0,
    ),
  ];
  
  /// 特大阴影 - 16dp
  static const List<BoxShadow> xxl = [
    BoxShadow(
      color: Color(0x3D000000),
      offset: Offset(0, 16),
      blurRadius: 48,
      spreadRadius: 0,
    ),
    BoxShadow(
      color: Color(0x1F000000),
      offset: Offset(0, 8),
      blurRadius: 16,
      spreadRadius: 0,
    ),
  ];

  // ==================== 特殊阴影 ====================
  
  /// 内阴影
  static const List<BoxShadow> inset = [
    BoxShadow(
      color: Color(0x1A000000),
      offset: Offset(0, 1),
      blurRadius: 2,
      spreadRadius: 0,
    ),
  ];
  
  /// 发光效果
  static List<BoxShadow> glow(Color color, {double blur = 8.0}) => [
    BoxShadow(
      color: color.withOpacity(0.3),
      offset: Offset.zero,
      blurRadius: blur,
      spreadRadius: 0,
    ),
  ];
  
  /// 自定义阴影
  static List<BoxShadow> custom({
    required Color color,
    required Offset offset,
    double blurRadius = 0,
    double spreadRadius = 0,
  }) => [
    BoxShadow(
      color: color,
      offset: offset,
      blurRadius: blurRadius,
      spreadRadius: spreadRadius,
    ),
  ];
}