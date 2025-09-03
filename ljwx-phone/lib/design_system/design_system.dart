/// 企业级设计系统 - 统一导出
/// 
/// 使用方式：
/// ```dart
/// import 'package:ljwx_health_new/design_system/design_system.dart';
/// 
/// // 使用设计系统
/// Container(
///   padding: DSSpacing.allLG,
///   decoration: BoxDecoration(
///     color: DSColors.primary500,
///     borderRadius: DSRadius.allMD,
///     boxShadow: DSShadow.md,
///   ),
///   child: Text(
///     '企业级设计',
///     style: DSTypography.cardTitle(DSColors.white),
///   ),
/// )
/// 
/// // 使用组件
/// DSCard.standard(
///   child: DSHealthCard.heartRate(value: '75'),
/// )
/// ```

// Colors
export 'colors.dart';

// Typography
export 'typography.dart';

// Spacing & Layout
export 'spacing.dart';

// Themes
export 'theme.dart';

// Components
export 'components/components.dart';