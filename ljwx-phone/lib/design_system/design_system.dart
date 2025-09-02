/// 企业级设计系统
/// 
/// 这是灵境万象健康管理系统的企业级设计系统，提供：
/// - 完整的颜色体系
/// - 标准化的字体排版
/// - 统一的主题配置
/// - 组件样式规范
/// 
/// 使用说明：
/// ```dart
/// import 'package:ljwx_health_new/design_system/design_system.dart';
/// 
/// // 使用颜色
/// Container(color: DSColors.primary500);
/// 
/// // 使用字体样式
/// Text('标题', style: DSTypography.titleLarge);
/// 
/// // 应用主题
/// MaterialApp(theme: DSTheme.buildLightTheme());
/// ```

library design_system;

// 导出所有设计系统组件
export 'colors.dart';
export 'typography.dart';
export 'theme.dart';