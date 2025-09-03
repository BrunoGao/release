import 'package:flutter/material.dart';
import '../design_system.dart';
import 'ds_card.dart';

/// 健康数据卡片组件
/// 专门用于展示健康监测数据
class DSHealthCard extends StatelessWidget {
  final String title;
  final String value;
  final String unit;
  final String? subtitle;
  final IconData icon;
  final Color iconColor;
  final Color? valueColor;
  final VoidCallback? onTap;
  final Widget? trend;
  final String? status;
  final bool isLoading;
  final double? progress;
  
  const DSHealthCard({
    super.key,
    required this.title,
    required this.value,
    required this.unit,
    required this.icon,
    required this.iconColor,
    this.subtitle,
    this.valueColor,
    this.onTap,
    this.trend,
    this.status,
    this.isLoading = false,
    this.progress,
  });

  /// 心率卡片
  factory DSHealthCard.heartRate({
    Key? key,
    required String value,
    String? subtitle,
    VoidCallback? onTap,
    Widget? trend,
    String? status,
    bool isLoading = false,
  }) {
    return DSHealthCard(
      key: key,
      title: '心率',
      value: value,
      unit: 'BPM',
      icon: Icons.favorite,
      iconColor: DSColors.heartRate,
      valueColor: DSColors.heartRate,
      subtitle: subtitle,
      onTap: onTap,
      trend: trend,
      status: status,
      isLoading: isLoading,
    );
  }

  /// 血氧卡片
  factory DSHealthCard.bloodOxygen({
    Key? key,
    required String value,
    String? subtitle,
    VoidCallback? onTap,
    Widget? trend,
    String? status,
    bool isLoading = false,
    double? progress,
  }) {
    return DSHealthCard(
      key: key,
      title: '血氧',
      value: value,
      unit: '%',
      icon: Icons.air,
      iconColor: DSColors.bloodOxygen,
      valueColor: DSColors.bloodOxygen,
      subtitle: subtitle,
      onTap: onTap,
      trend: trend,
      status: status,
      isLoading: isLoading,
      progress: progress,
    );
  }

  /// 体温卡片
  factory DSHealthCard.temperature({
    Key? key,
    required String value,
    String? subtitle,
    VoidCallback? onTap,
    Widget? trend,
    String? status,
    bool isLoading = false,
  }) {
    return DSHealthCard(
      key: key,
      title: '体温',
      value: value,
      unit: '°C',
      icon: Icons.thermostat,
      iconColor: DSColors.temperature,
      valueColor: DSColors.temperature,
      subtitle: subtitle,
      onTap: onTap,
      trend: trend,
      status: status,
      isLoading: isLoading,
    );
  }

  /// 血压卡片
  factory DSHealthCard.bloodPressure({
    Key? key,
    required String value,
    String? subtitle,
    VoidCallback? onTap,
    Widget? trend,
    String? status,
    bool isLoading = false,
  }) {
    return DSHealthCard(
      key: key,
      title: '血压',
      value: value,
      unit: 'mmHg',
      icon: Icons.monitor_heart,
      iconColor: DSColors.bloodPressure,
      valueColor: DSColors.bloodPressure,
      subtitle: subtitle,
      onTap: onTap,
      trend: trend,
      status: status,
      isLoading: isLoading,
    );
  }

  /// 步数卡片
  factory DSHealthCard.steps({
    Key? key,
    required String value,
    String? subtitle,
    VoidCallback? onTap,
    Widget? trend,
    String? status,
    bool isLoading = false,
    double? progress,
  }) {
    return DSHealthCard(
      key: key,
      title: '步数',
      value: value,
      unit: '步',
      icon: Icons.directions_walk,
      iconColor: DSColors.steps,
      valueColor: DSColors.steps,
      subtitle: subtitle,
      onTap: onTap,
      trend: trend,
      status: status,
      isLoading: isLoading,
      progress: progress,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return DSCard.standard(
      onTap: onTap,
      isLoading: isLoading,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 标题行
          Row(
            children: [
              Container(
                padding: DSSpacing.allSM,
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: DSRadius.allSM,
                ),
                child: Icon(
                  icon,
                  color: iconColor,
                  size: 20,
                ),
              ),
              DSSpacing.gapMD(),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: DSTypography.cardTitle(
                        theme.textTheme.bodyLarge!.color!,
                      ),
                    ),
                    if (status != null)
                      Container(
                        margin: DSSpacing.onlyTop(DSSpacing.xs),
                        child: _buildStatusChip(status!),
                      ),
                  ],
                ),
              ),
              if (trend != null) trend!,
            ],
          ),
          
          DSSpacing.vGapMD(),
          
          // 数值行
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                value,
                style: DSTypography.numberDisplay(
                  valueColor ?? theme.textTheme.headlineLarge!.color!,
                  fontSize: 32,
                ),
              ),
              DSSpacing.gapXS(),
              Text(
                unit,
                style: DSTypography.unit(
                  theme.textTheme.bodyMedium!.color!,
                  fontSize: 14,
                ),
              ),
            ],
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
          
          // 进度条（如果有）
          if (progress != null) ...[
            DSSpacing.vGapMD(),
            LinearProgressIndicator(
              value: progress! / 100,
              backgroundColor: iconColor.withOpacity(0.1),
              valueColor: AlwaysStoppedAnimation<Color>(iconColor),
              borderRadius: DSRadius.allSM,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color chipColor;
    Color textColor;
    
    switch (status.toLowerCase()) {
      case '正常':
      case 'normal':
        chipColor = DSColors.success500;
        textColor = DSColors.white;
        break;
      case '偏高':
      case 'high':
        chipColor = DSColors.warning500;
        textColor = DSColors.white;
        break;
      case '偏低':
      case 'low':
        chipColor = DSColors.info500;
        textColor = DSColors.white;
        break;
      case '异常':
      case 'abnormal':
        chipColor = DSColors.error500;
        textColor = DSColors.white;
        break;
      default:
        chipColor = DSColors.gray400;
        textColor = DSColors.white;
    }

    return Container(
      padding: DSSpacing.symmetric(
        horizontal: DSSpacing.sm, 
        vertical: DSSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: DSRadius.allSM,
      ),
      child: Text(
        status,
        style: DSTypography.caption(textColor).copyWith(
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}