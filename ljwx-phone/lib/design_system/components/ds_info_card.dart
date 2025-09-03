import 'package:flutter/material.dart';
import '../design_system.dart';
import 'ds_card.dart';

/// 信息展示卡片组件
/// 用于展示各类统计和状态信息
class DSInfoCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final List<InfoItem>? items;
  final VoidCallback? onTap;
  final bool showArrow;
  final Color? accentColor;
  final bool isLoading;
  final InfoCardType type;

  const DSInfoCard({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.items,
    this.onTap,
    this.showArrow = false,
    this.accentColor,
    this.isLoading = false,
    this.type = InfoCardType.standard,
  });

  /// 用户信息卡片
  factory DSInfoCard.user({
    Key? key,
    required String name,
    String? subtitle,
    Widget? avatar,
    List<InfoItem>? details,
    VoidCallback? onTap,
  }) {
    return DSInfoCard(
      key: key,
      title: name,
      subtitle: subtitle,
      leading: avatar ?? const CircleAvatar(
        child: Icon(Icons.person),
      ),
      items: details,
      onTap: onTap,
      showArrow: onTap != null,
      accentColor: DSColors.primary500,
      type: InfoCardType.user,
    );
  }

  /// 设备信息卡片
  factory DSInfoCard.device({
    Key? key,
    required String deviceName,
    String? status,
    List<InfoItem>? specs,
    VoidCallback? onTap,
    bool isConnected = false,
  }) {
    return DSInfoCard(
      key: key,
      title: deviceName,
      subtitle: status,
      leading: Container(
        padding: DSSpacing.allSM,
        decoration: BoxDecoration(
          color: (isConnected ? DSColors.success500 : DSColors.gray400).withOpacity(0.1),
          borderRadius: DSRadius.allSM,
        ),
        child: Icon(
          Icons.watch_sharp,
          color: isConnected ? DSColors.success500 : DSColors.gray400,
          size: 24,
        ),
      ),
      items: specs,
      onTap: onTap,
      showArrow: onTap != null,
      accentColor: isConnected ? DSColors.success500 : DSColors.gray400,
      type: InfoCardType.device,
    );
  }

  /// 告警信息卡片
  factory DSInfoCard.alert({
    Key? key,
    required String title,
    String? description,
    int? alertCount,
    VoidCallback? onTap,
    AlertSeverity severity = AlertSeverity.info,
  }) {
    Color severityColor;
    IconData severityIcon;
    
    switch (severity) {
      case AlertSeverity.critical:
        severityColor = DSColors.error500;
        severityIcon = Icons.error;
        break;
      case AlertSeverity.warning:
        severityColor = DSColors.warning500;
        severityIcon = Icons.warning;
        break;
      case AlertSeverity.info:
        severityColor = DSColors.info500;
        severityIcon = Icons.info;
        break;
    }

    return DSInfoCard(
      key: key,
      title: title,
      subtitle: description,
      leading: Container(
        padding: DSSpacing.allSM,
        decoration: BoxDecoration(
          color: severityColor.withOpacity(0.1),
          borderRadius: DSRadius.allSM,
        ),
        child: Icon(
          severityIcon,
          color: severityColor,
          size: 24,
        ),
      ),
      trailing: alertCount != null ? Container(
        padding: DSSpacing.symmetric(
          horizontal: DSSpacing.sm,
          vertical: DSSpacing.xs,
        ),
        decoration: BoxDecoration(
          color: severityColor,
          borderRadius: DSRadius.allFull,
        ),
        child: Text(
          alertCount.toString(),
          style: DSTypography.caption(DSColors.white).copyWith(
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
        ),
      ) : null,
      onTap: onTap,
      showArrow: onTap != null,
      accentColor: severityColor,
      type: InfoCardType.alert,
    );
  }

  /// 统计信息卡片
  factory DSInfoCard.stats({
    Key? key,
    required String title,
    required List<InfoItem> stats,
    VoidCallback? onTap,
    Color? accentColor,
  }) {
    return DSInfoCard(
      key: key,
      title: title,
      items: stats,
      onTap: onTap,
      showArrow: onTap != null,
      accentColor: accentColor ?? DSColors.primary500,
      type: InfoCardType.stats,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveAccentColor = accentColor ?? DSColors.primary500;

    Widget cardContent = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 标题行
        Row(
          children: [
            if (leading != null) ...[
              leading!,
              DSSpacing.gapMD(),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: DSTypography.cardTitle(
                      theme.textTheme.titleLarge!.color!,
                    ),
                  ),
                  if (subtitle != null) ...[
                    DSSpacing.vGapXS(),
                    Text(
                      subtitle!,
                      style: DSTypography.cardSubtitle(
                        theme.textTheme.bodyMedium!.color!,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (trailing != null) ...[
              DSSpacing.gapMD(),
              trailing!,
            ],
            if (showArrow) ...[
              DSSpacing.gapSM(),
              Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: theme.textTheme.bodySmall!.color,
              ),
            ],
          ],
        ),

        // 详细信息
        if (items != null && items!.isNotEmpty) ...[
          DSSpacing.vGapLG(),
          _buildInfoItems(theme, effectiveAccentColor),
        ],
      ],
    );

    // 根据卡片类型选择样式
    switch (type) {
      case InfoCardType.alert:
        return DSCard.warning(
          onTap: onTap,
          isLoading: isLoading,
          child: cardContent,
        );
      case InfoCardType.user:
      case InfoCardType.device:
      case InfoCardType.stats:
      default:
        return DSCard.standard(
          onTap: onTap,
          isLoading: isLoading,
          child: cardContent,
        );
    }
  }

  Widget _buildInfoItems(ThemeData theme, Color accentColor) {
    return Column(
      children: items!.asMap().entries.map((entry) {
        final index = entry.key;
        final item = entry.value;
        
        return Container(
          margin: index < items!.length - 1 
            ? DSSpacing.onlyBottom(DSSpacing.md)
            : EdgeInsets.zero,
          child: Row(
            children: [
              if (item.icon != null) ...[
                Icon(
                  item.icon,
                  size: 16,
                  color: accentColor,
                ),
                DSSpacing.gapSM(),
              ],
              Expanded(
                child: Text(
                  item.label,
                  style: DSTypography.cardSubtitle(
                    theme.textTheme.bodyMedium!.color!,
                  ),
                ),
              ),
              if (item.value != null)
                Text(
                  item.value!,
                  style: DSTypography.cardTitle(
                    theme.textTheme.bodyLarge!.color!,
                  ).copyWith(fontSize: 14),
                ),
              if (item.status != null)
                Container(
                  padding: DSSpacing.symmetric(
                    horizontal: DSSpacing.sm,
                    vertical: DSSpacing.xs,
                  ),
                  decoration: BoxDecoration(
                    color: _getStatusColor(item.status!).withOpacity(0.1),
                    borderRadius: DSRadius.allSM,
                  ),
                  child: Text(
                    item.status!,
                    style: DSTypography.caption(_getStatusColor(item.status!)).copyWith(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case '正常':
      case 'normal':
      case '在线':
      case 'online':
      case '已连接':
      case 'connected':
        return DSColors.success500;
      case '警告':
      case 'warning':
      case '离线':
      case 'offline':
        return DSColors.warning500;
      case '错误':
      case 'error':
      case '断开':
      case 'disconnected':
        return DSColors.error500;
      default:
        return DSColors.gray500;
    }
  }
}

/// 信息项数据模型
class InfoItem {
  final String label;
  final String? value;
  final String? status;
  final IconData? icon;

  const InfoItem({
    required this.label,
    this.value,
    this.status,
    this.icon,
  });
}

/// 信息卡片类型
enum InfoCardType {
  standard,
  user,
  device,
  alert,
  stats,
}

/// 告警严重程度
enum AlertSeverity {
  info,
  warning,
  critical,
}