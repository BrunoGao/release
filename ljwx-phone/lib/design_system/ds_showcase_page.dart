import 'package:flutter/material.dart';
import '../design_system/design_system.dart';

/// 企业级设计系统展示页面
/// 用于测试和演示所有设计系统组件
class DSShowcasePage extends StatelessWidget {
  const DSShowcasePage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          '企业级设计系统',
          style: DSTypography.cardTitle(theme.appBarTheme.foregroundColor!),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: DSSpacing.page,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 色彩展示
            _buildSectionTitle('色彩系统'),
            _buildColorPalette(),
            DSSpacing.vGapXXL(),

            // 卡片组件展示
            _buildSectionTitle('卡片组件'),
            _buildCardShowcase(),
            DSSpacing.vGapXXL(),

            // 健康数据卡片展示
            _buildSectionTitle('健康数据卡片'),
            _buildHealthCardShowcase(),
            DSSpacing.vGapXXL(),

            // 信息卡片展示
            _buildSectionTitle('信息卡片'),
            _buildInfoCardShowcase(),
            DSSpacing.vGapXXL(),

            // 统计组件展示
            _buildSectionTitle('统计组件'),
            _buildStatsShowcase(),
            DSSpacing.vGapXXL(),

            // 图表组件展示
            _buildSectionTitle('图表组件'),
            _buildChartShowcase(),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: DSTypography.buildTextTheme(DSColors.gray900).headlineMedium,
    );
  }

  Widget _buildColorPalette() {
    return Column(
      children: [
        // 主色系
        _buildColorRow('主色系', [
          _ColorItem('Primary 500', DSColors.primary500),
          _ColorItem('Primary 300', DSColors.primary300),
          _ColorItem('Primary 700', DSColors.primary700),
        ]),
        DSSpacing.vGapMD(),

        // 语义色彩
        _buildColorRow('语义色彩', [
          _ColorItem('Success', DSColors.success500),
          _ColorItem('Warning', DSColors.warning500),
          _ColorItem('Error', DSColors.error500),
          _ColorItem('Info', DSColors.info500),
        ]),
        DSSpacing.vGapMD(),

        // 健康数据色彩
        _buildColorRow('健康数据', [
          _ColorItem('心率', DSColors.heartRate),
          _ColorItem('血氧', DSColors.bloodOxygen),
          _ColorItem('体温', DSColors.temperature),
          _ColorItem('血压', DSColors.bloodPressure),
        ]),
      ],
    );
  }

  Widget _buildColorRow(String title, List<_ColorItem> colors) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: DSTypography.cardTitle(DSColors.gray700),
        ),
        DSSpacing.vGapSM(),
        Row(
          children: colors.map((colorItem) => Expanded(
            child: Container(
              margin: DSSpacing.onlyRight(DSSpacing.sm),
              child: Column(
                children: [
                  Container(
                    height: 60,
                    decoration: BoxDecoration(
                      color: colorItem.color,
                      borderRadius: DSRadius.allMD,
                      boxShadow: DSShadow.sm,
                    ),
                  ),
                  DSSpacing.vGapSM(),
                  Text(
                    colorItem.name,
                    style: DSTypography.caption(DSColors.gray600),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          )).toList(),
        ),
      ],
    );
  }

  Widget _buildCardShowcase() {
    return Column(
      children: [
        // 标准卡片
        DSCard.standard(
          child: Text(
            '标准卡片\n这是一个标准样式的卡片组件，具有统一的内边距、圆角和阴影效果。',
            style: DSTypography.cardSubtitle(DSColors.gray700),
          ),
        ),

        // 信息卡片
        DSCard.info(
          child: Text(
            '信息卡片\n用于显示重要信息，具有蓝色边框和增强的阴影效果。',
            style: DSTypography.cardSubtitle(DSColors.gray700),
          ),
        ),

        // 警告卡片
        DSCard.warning(
          child: Text(
            '警告卡片\n用于显示警告信息，具有橙色背景和边框。',
            style: DSTypography.cardSubtitle(DSColors.gray700),
          ),
        ),

        // 渐变卡片
        DSCard.gradient(
          child: Text(
            '渐变卡片\n具有渐变背景的卡片，用于突出显示重要内容。',
            style: DSTypography.cardSubtitle(DSColors.white),
          ),
        ),
      ],
    );
  }

  Widget _buildHealthCardShowcase() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DSHealthCard.heartRate(
                value: '75',
                subtitle: '正常范围',
                status: '正常',
              ),
            ),
            DSSpacing.gapMD(),
            Expanded(
              child: DSHealthCard.bloodOxygen(
                value: '98.0',
                subtitle: '血氧饱和度',
                status: '正常',
                progress: 98,
              ),
            ),
          ],
        ),
        
        DSSpacing.vGapMD(),
        
        Row(
          children: [
            Expanded(
              child: DSHealthCard.temperature(
                value: '36.5',
                subtitle: '体温正常',
                status: '正常',
              ),
            ),
            DSSpacing.gapMD(),
            Expanded(
              child: DSHealthCard.steps(
                value: '8,543',
                subtitle: '今日步数',
                status: '良好',
                progress: 85,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildInfoCardShowcase() {
    return Column(
      children: [
        // 用户信息卡片
        DSInfoCard.user(
          name: '张三',
          subtitle: '工号：1-005 | 部门：研发部',
          details: const [
            InfoItem(
              label: '工作年限',
              value: '5年',
              icon: Icons.work,
            ),
            InfoItem(
              label: '设备序列号',
              value: 'CRFTQ23409001890',
              icon: Icons.device_hub,
            ),
          ],
        ),

        // 设备信息卡片
        DSInfoCard.device(
          deviceName: '健康手环 Pro',
          status: '已连接',
          isConnected: true,
          specs: const [
            InfoItem(label: '电量', value: '85%', icon: Icons.battery_full),
            InfoItem(label: '信号', value: '强', icon: Icons.signal_cellular_4_bar),
            InfoItem(label: '版本', value: 'v3.0.0.900', icon: Icons.info),
          ],
        ),

        // 告警信息卡片
        DSInfoCard.alert(
          title: '健康告警',
          description: '检测到异常心率数据',
          alertCount: 3,
          severity: AlertSeverity.warning,
        ),
      ],
    );
  }

  Widget _buildStatsShowcase() {
    return Column(
      children: [
        // 统计仪表盘
        DSStatsDashboard(
          title: '今日统计',
          subtitle: '健康数据概览',
          stats: const [
            StatItem(
              label: '心率平均',
              value: '75',
              icon: Icons.favorite,
              color: DSColors.heartRate,
              trend: StatTrend.flat,
            ),
            StatItem(
              label: '步数',
              value: '8.5K',
              icon: Icons.directions_walk,
              color: DSColors.steps,
              trend: StatTrend.up,
            ),
            StatItem(
              label: '卡路里',
              value: '420',
              icon: Icons.local_fire_department,
              color: DSColors.calories,
              trend: StatTrend.up,
            ),
            StatItem(
              label: '活跃时间',
              value: '3.2h',
              icon: Icons.access_time,
              color: DSColors.info500,
              trend: StatTrend.down,
            ),
          ],
        ),

        DSSpacing.vGapLG(),

        // 圆形进度
        Row(
          children: [
            Expanded(
              child: DSCircularProgress.healthScore(
                score: 85,
                title: '健康评分',
                subtitle: '综合评估',
              ),
            ),
            DSSpacing.gapXL(),
            Expanded(
              child: DSCircularProgress(
                progress: 0.68,
                title: '目标达成',
                progressColor: DSColors.steps,
                backgroundColor: DSColors.steps.withOpacity(0.1),
                centerChild: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '68%',
                      style: DSTypography.numberDisplay(DSColors.steps, fontSize: 24),
                    ),
                    Text(
                      '完成度',
                      style: DSTypography.unit(DSColors.gray600, fontSize: 10),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildChartShowcase() {
    // 模拟数据
    final heartRateData = List.generate(12, (index) {
      return HealthDataPoint(
        timestamp: DateTime.now().subtract(Duration(hours: 11 - index)),
        value: 70 + (index * 2) + (index % 3 * 5).toDouble(),
      );
    });

    final barData = [
      const BarDataItem(label: '周一', value: 6500, color: DSColors.steps),
      const BarDataItem(label: '周二', value: 8200, color: DSColors.steps),
      const BarDataItem(label: '周三', value: 7800, color: DSColors.steps),
      const BarDataItem(label: '周四', value: 9200, color: DSColors.steps),
      const BarDataItem(label: '周五', value: 10500, color: DSColors.steps),
      const BarDataItem(label: '周六', value: 12000, color: DSColors.steps),
      const BarDataItem(label: '周日', value: 9800, color: DSColors.steps),
    ];

    return Column(
      children: [
        // 趋势图
        DSHealthTrendChart.heartRate(
          data: heartRateData,
          subtitle: '过去12小时心率变化',
        ),

        DSSpacing.vGapLG(),

        // 柱状图
        DSBarChart(
          title: '每周步数统计',
          subtitle: '近7天步数变化趋势',
          data: barData,
          maxY: 15000,
        ),
      ],
    );
  }
}

class _ColorItem {
  final String name;
  final Color color;

  const _ColorItem(this.name, this.color);
}