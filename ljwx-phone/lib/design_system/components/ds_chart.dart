import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../design_system.dart';

/// 企业级图表组件基类
/// 提供统一的图表样式和配置
class DSChart extends StatelessWidget {
  final Widget child;
  final String? title;
  final String? subtitle;
  final EdgeInsets? padding;
  final Color? backgroundColor;
  final bool showBorder;
  final List<ChartLegend>? legends;

  const DSChart({
    super.key,
    required this.child,
    this.title,
    this.subtitle,
    this.padding,
    this.backgroundColor,
    this.showBorder = false,
    this.legends,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    return DSCard.flat(
      backgroundColor: backgroundColor ?? (isDark ? DSColors.surfaceDark : DSColors.surfaceLight),
      padding: padding ?? DSSpacing.allLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 标题区域
          if (title != null) ...[
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
            DSSpacing.vGapLG(),
          ],
          
          // 图表内容
          Container(
            decoration: showBorder ? BoxDecoration(
              border: Border.all(
                color: theme.dividerColor.withOpacity(0.1),
                width: 1,
              ),
              borderRadius: DSRadius.allSM,
            ) : null,
            child: child,
          ),
          
          // 图例
          if (legends != null && legends!.isNotEmpty) ...[
            DSSpacing.vGapMD(),
            Wrap(
              spacing: DSSpacing.md,
              runSpacing: DSSpacing.sm,
              children: legends!.map((legend) => _buildLegendItem(legend)).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildLegendItem(ChartLegend legend) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: legend.color,
            shape: BoxShape.circle,
          ),
        ),
        DSSpacing.gapSM(),
        Text(
          legend.label,
          style: DSTypography.caption(DSColors.gray600),
        ),
      ],
    );
  }
}

/// 健康趋势线图
class DSHealthTrendChart extends StatelessWidget {
  final List<HealthDataPoint> data;
  final String title;
  final String? subtitle;
  final Color lineColor;
  final bool showDots;
  final bool showGrid;
  final double? minY;
  final double? maxY;
  final String? unit;

  const DSHealthTrendChart({
    super.key,
    required this.data,
    required this.title,
    required this.lineColor,
    this.subtitle,
    this.showDots = true,
    this.showGrid = true,
    this.minY,
    this.maxY,
    this.unit,
  });

  /// 心率趋势图
  factory DSHealthTrendChart.heartRate({
    Key? key,
    required List<HealthDataPoint> data,
    String? subtitle,
    bool showDots = true,
    bool showGrid = true,
  }) {
    return DSHealthTrendChart(
      key: key,
      data: data,
      title: '心率趋势',
      subtitle: subtitle,
      lineColor: DSColors.heartRate,
      showDots: showDots,
      showGrid: showGrid,
      minY: 40,
      maxY: 180,
      unit: 'BPM',
    );
  }

  /// 血氧趋势图
  factory DSHealthTrendChart.bloodOxygen({
    Key? key,
    required List<HealthDataPoint> data,
    String? subtitle,
    bool showDots = true,
    bool showGrid = true,
  }) {
    return DSHealthTrendChart(
      key: key,
      data: data,
      title: '血氧趋势',
      subtitle: subtitle,
      lineColor: DSColors.bloodOxygen,
      showDots: showDots,
      showGrid: showGrid,
      minY: 90,
      maxY: 100,
      unit: '%',
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    if (data.isEmpty) {
      return DSChart(
        title: title,
        subtitle: subtitle,
        child: Container(
          height: 200,
          alignment: Alignment.center,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.show_chart,
                size: 48,
                color: theme.disabledColor,
              ),
              DSSpacing.vGapMD(),
              Text(
                '暂无数据',
                style: DSTypography.cardSubtitle(theme.disabledColor),
              ),
            ],
          ),
        ),
      );
    }

    return DSChart(
      title: title,
      subtitle: subtitle,
      child: SizedBox(
        height: 200,
        child: LineChart(
          LineChartData(
            gridData: FlGridData(
              show: showGrid,
              drawVerticalLine: true,
              drawHorizontalLine: true,
              verticalInterval: 1,
              horizontalInterval: (maxY! - minY!) / 5,
              getDrawingVerticalLine: (value) => FlLine(
                color: (isDark ? DSColors.gray600 : DSColors.gray300).withOpacity(0.3),
                strokeWidth: 1,
              ),
              getDrawingHorizontalLine: (value) => FlLine(
                color: (isDark ? DSColors.gray600 : DSColors.gray300).withOpacity(0.3),
                strokeWidth: 1,
              ),
            ),
            titlesData: FlTitlesData(
              show: true,
              rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
              topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 30,
                  interval: 1,
                  getTitlesWidget: (value, meta) {
                    if (value.toInt() >= 0 && value.toInt() < data.length) {
                      return Padding(
                        padding: DSSpacing.onlyTop(DSSpacing.xs),
                        child: Text(
                          _formatTime(data[value.toInt()].timestamp),
                          style: DSTypography.caption(theme.textTheme.bodySmall!.color!),
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                ),
              ),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 40,
                  interval: (maxY! - minY!) / 4,
                  getTitlesWidget: (value, meta) {
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
            borderData: FlBorderData(
              show: false,
            ),
            minX: 0,
            maxX: (data.length - 1).toDouble(),
            minY: minY,
            maxY: maxY,
            lineBarsData: [
              LineChartBarData(
                spots: data.asMap().entries.map((entry) {
                  return FlSpot(entry.key.toDouble(), entry.value.value);
                }).toList(),
                isCurved: true,
                curveSmoothness: 0.3,
                gradient: LinearGradient(
                  colors: [
                    lineColor,
                    lineColor.withOpacity(0.3),
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                barWidth: 3,
                isStrokeCapRound: true,
                dotData: FlDotData(
                  show: showDots,
                  getDotPainter: (spot, percent, barData, index) =>
                      FlDotCirclePainter(
                        radius: 4,
                        color: lineColor,
                        strokeWidth: 2,
                        strokeColor: DSColors.white,
                      ),
                ),
                belowBarData: BarAreaData(
                  show: true,
                  gradient: LinearGradient(
                    colors: [
                      lineColor.withOpacity(0.1),
                      lineColor.withOpacity(0.0),
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
              ),
            ],
            lineTouchData: LineTouchData(
              enabled: true,
              touchTooltipData: LineTouchTooltipData(
                tooltipBgColor: isDark ? DSColors.surfaceDark : DSColors.white,
                tooltipBorder: BorderSide(
                  color: theme.dividerColor.withOpacity(0.2),
                ),
                tooltipRoundedRadius: DSRadius.sm,
                getTooltipItems: (List<LineBarSpot> touchedBarSpots) {
                  return touchedBarSpots.map((barSpot) {
                    final flSpot = barSpot;
                    final dataPoint = data[flSpot.x.toInt()];
                    return LineTooltipItem(
                      '${flSpot.y.toInt()}${unit ?? ''}\n${_formatDateTime(dataPoint.timestamp)}',
                      DSTypography.caption(theme.textTheme.bodySmall!.color!),
                    );
                  }).toList();
                },
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime dateTime) {
    return '${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.month}/${dateTime.day} ${_formatTime(dateTime)}';
  }
}

/// 健康评分雷达图
class DSHealthRadarChart extends StatelessWidget {
  final List<DSRadarDataSet> dataSets;
  final String title;
  final String? subtitle;
  final List<String> labels;

  const DSHealthRadarChart({
    super.key,
    required this.dataSets,
    required this.title,
    required this.labels,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return DSChart(
      title: title,
      subtitle: subtitle,
      child: SizedBox(
        height: 250,
        child: RadarChart(
          RadarChartData(
            dataSets: dataSets.map((dataSet) {
              return RadarDataSet(
                fillColor: dataSet.fillColor.withOpacity(0.1),
                borderColor: dataSet.borderColor,
                dataEntries: dataSet.dataEntries,
              );
            }).toList(),
            radarBorderData: BorderSide(
              color: theme.dividerColor.withOpacity(0.2),
              width: 1,
            ),
            titleTextStyle: DSTypography.caption(theme.textTheme.bodySmall!.color!),
            titlePositionPercentageOffset: 0.15,
            getTitle: (index, angle) {
              if (index < labels.length) {
                return RadarChartTitle(text: labels[index]);
              }
              return const RadarChartTitle(text: '');
            },
            tickCount: 5,
            ticksTextStyle: DSTypography.caption(theme.textTheme.bodySmall!.color!),
            tickBorderData: BorderSide(
              color: theme.dividerColor.withOpacity(0.1),
              width: 1,
            ),
          ),
        ),
      ),
    );
  }
}

/// 数据模型
class HealthDataPoint {
  final DateTime timestamp;
  final double value;
  final String? status;

  const HealthDataPoint({
    required this.timestamp,
    required this.value,
    this.status,
  });
}

/// 图例数据模型
class ChartLegend {
  final String label;
  final Color color;

  const ChartLegend({
    required this.label,
    required this.color,
  });
}

/// 雷达图数据集
class DSRadarDataSet {
  final Color fillColor;
  final Color borderColor;
  final List<RadarEntry> dataEntries;

  const DSRadarDataSet({
    required this.fillColor,
    required this.borderColor,
    required this.dataEntries,
  });
}