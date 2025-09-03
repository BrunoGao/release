import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../design_system.dart';

/// 统计仪表盘组件
/// 用于展示关键指标的概览
class DSStatsDashboard extends StatelessWidget {
  final List<StatItem> stats;
  final String? title;
  final String? subtitle;
  final int columns;
  final VoidCallback? onTap;

  const DSStatsDashboard({
    super.key,
    required this.stats,
    this.title,
    this.subtitle,
    this.columns = 2,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return DSCard.standard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null) ...[
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title!,
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
                if (onTap != null)
                  Icon(
                    Icons.arrow_forward_ios,
                    size: 16,
                    color: theme.textTheme.bodySmall!.color,
                  ),
              ],
            ),
            DSSpacing.vGapLG(),
          ],
          
          // 统计项网格
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: columns,
              childAspectRatio: 1.2,
              crossAxisSpacing: DSSpacing.md,
              mainAxisSpacing: DSSpacing.md,
            ),
            itemCount: stats.length,
            itemBuilder: (context, index) {
              final stat = stats[index];
              return _buildStatItem(context, stat);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(BuildContext context, StatItem stat) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      padding: DSSpacing.allMD,
      decoration: BoxDecoration(
        color: (isDark ? DSColors.containerDark : DSColors.gray50).withOpacity(0.5),
        borderRadius: DSRadius.allMD,
        border: Border.all(
          color: stat.color.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                padding: DSSpacing.allXS,
                decoration: BoxDecoration(
                  color: stat.color.withOpacity(0.1),
                  borderRadius: DSRadius.allSM,
                ),
                child: Icon(
                  stat.icon,
                  color: stat.color,
                  size: 16,
                ),
              ),
              const Spacer(),
              if (stat.trend != null)
                Icon(
                  stat.trend == StatTrend.up ? Icons.trending_up :
                  stat.trend == StatTrend.down ? Icons.trending_down :
                  Icons.trending_flat,
                  color: stat.trend == StatTrend.up ? DSColors.success500 :
                         stat.trend == StatTrend.down ? DSColors.error500 :
                         DSColors.gray500,
                  size: 16,
                ),
            ],
          ),
          
          DSSpacing.vGapSM(),
          
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                stat.value,
                style: DSTypography.numberDisplay(
                  stat.color,
                  fontSize: 20,
                ),
              ),
              DSSpacing.vGapXS(),
              Text(
                stat.label,
                style: DSTypography.caption(
                  theme.textTheme.bodySmall!.color!,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// 圆形进度指示器
class DSCircularProgress extends StatelessWidget {
  final double progress;
  final String? title;
  final String? subtitle;
  final Color progressColor;
  final Color backgroundColor;
  final double size;
  final double strokeWidth;
  final Widget? centerChild;

  const DSCircularProgress({
    super.key,
    required this.progress,
    this.title,
    this.subtitle,
    required this.progressColor,
    required this.backgroundColor,
    this.size = 120,
    this.strokeWidth = 8,
    this.centerChild,
  });

  /// 健康评分进度
  factory DSCircularProgress.healthScore({
    Key? key,
    required double score,
    String? title,
    String? subtitle,
    double size = 120,
  }) {
    final progress = score / 100;
    Color color;
    
    if (score >= 80) {
      color = DSColors.success500;
    } else if (score >= 60) {
      color = DSColors.warning500;
    } else {
      color = DSColors.error500;
    }

    return DSCircularProgress(
      key: key,
      progress: progress,
      title: title ?? '健康评分',
      subtitle: subtitle,
      progressColor: color,
      backgroundColor: color.withOpacity(0.1),
      size: size,
      centerChild: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${score.toInt()}',
            style: DSTypography.numberDisplay(color, fontSize: size * 0.2),
          ),
          Text(
            '分',
            style: DSTypography.unit(DSColors.gray600, fontSize: size * 0.08),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        if (title != null) ...[
          Text(
            title!,
            style: DSTypography.cardTitle(
              theme.textTheme.titleLarge!.color!,
            ),
            textAlign: TextAlign.center,
          ),
          if (subtitle != null) ...[
            DSSpacing.vGapXS(),
            Text(
              subtitle!,
              style: DSTypography.cardSubtitle(
                theme.textTheme.bodyMedium!.color!,
              ),
              textAlign: TextAlign.center,
            ),
          ],
          DSSpacing.vGapMD(),
        ],
        
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // 背景圆环
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator(
                  value: 1.0,
                  strokeWidth: strokeWidth,
                  backgroundColor: backgroundColor,
                  valueColor: AlwaysStoppedAnimation<Color>(backgroundColor),
                ),
              ),
              
              // 进度圆环
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator(
                  value: progress.clamp(0.0, 1.0),
                  strokeWidth: strokeWidth,
                  backgroundColor: Colors.transparent,
                  valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                ),
              ),
              
              // 中心内容
              if (centerChild != null)
                centerChild!,
            ],
          ),
        ),
      ],
    );
  }
}

/// 简单柱状图组件
class DSBarChart extends StatelessWidget {
  final List<BarDataItem> data;
  final String? title;
  final String? subtitle;
  final double maxY;
  final bool showGrid;
  final bool showValues;

  const DSBarChart({
    super.key,
    required this.data,
    this.title,
    this.subtitle,
    required this.maxY,
    this.showGrid = true,
    this.showValues = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return DSChart(
      title: title,
      subtitle: subtitle,
      child: SizedBox(
        height: 200,
        child: BarChart(
          BarChartData(
            alignment: BarChartAlignment.spaceAround,
            maxY: maxY,
            barTouchData: BarTouchData(
              enabled: true,
              touchTooltipData: BarTouchTooltipData(
                tooltipBgColor: isDark ? DSColors.surfaceDark : DSColors.white,
                tooltipBorder: BorderSide(
                  color: theme.dividerColor.withOpacity(0.2),
                ),
                tooltipRoundedRadius: DSRadius.sm,
                getTooltipItem: (group, groupIndex, rod, rodIndex) {
                  final dataItem = data[group.x];
                  return BarTooltipItem(
                    '${dataItem.label}\n${rod.toY.toInt()}',
                    DSTypography.caption(theme.textTheme.bodySmall!.color!),
                  );
                },
              ),
            ),
            titlesData: FlTitlesData(
              show: true,
              rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
              topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  getTitlesWidget: (double value, TitleMeta meta) {
                    if (value.toInt() < data.length) {
                      return Padding(
                        padding: DSSpacing.onlyTop(DSSpacing.xs),
                        child: Text(
                          data[value.toInt()].label,
                          style: DSTypography.caption(theme.textTheme.bodySmall!.color!),
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                  reservedSize: 40,
                ),
              ),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 40,
                  interval: maxY / 5,
                  getTitlesWidget: (double value, TitleMeta meta) {
                    return Padding(
                      padding: DSSpacing.onlyRight(DSSpacing.xs),
                      child: Text(
                        value.toInt().toString(),
                        style: DSTypography.caption(theme.textTheme.bodySmall!.color!),
                        textAlign: TextAlign.right,
                      ),
                    );
                  },
                ),
              ),
            ),
            borderData: FlBorderData(show: false),
            barGroups: data.asMap().entries.map((entry) {
              final index = entry.key;
              final item = entry.value;
              return BarChartGroupData(
                x: index,
                barRods: [
                  BarChartRodData(
                    toY: item.value,
                    color: item.color,
                    width: 20,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(4),
                      topRight: Radius.circular(4),
                    ),
                  ),
                ],
              );
            }).toList(),
            gridData: FlGridData(
              show: showGrid,
              drawVerticalLine: false,
              drawHorizontalLine: true,
              horizontalInterval: maxY / 5,
              getDrawingHorizontalLine: (value) => FlLine(
                color: (isDark ? DSColors.gray600 : DSColors.gray300).withOpacity(0.3),
                strokeWidth: 1,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// 数据模型
class StatItem {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final StatTrend? trend;

  const StatItem({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.trend,
  });
}

class BarDataItem {
  final String label;
  final double value;
  final Color color;

  const BarDataItem({
    required this.label,
    required this.value,
    required this.color,
  });
}

enum StatTrend {
  up,
  down,
  flat,
}