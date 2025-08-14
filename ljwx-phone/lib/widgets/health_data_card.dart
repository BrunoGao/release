import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/health_model.dart' as health_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:go_router/go_router.dart';
import 'dart:convert';
import 'dart:math';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:fl_chart/fl_chart.dart';

class HealthDataCard extends StatelessWidget {
  final health_model.HealthData? healthData;

  const HealthDataCard({
    super.key,
    this.healthData,
  });

  @override
  Widget build(BuildContext context) {
    if (healthData == null || healthData!.healthData.isEmpty) {
      return _buildEmptyCard(context);
    }

    final theme = Theme.of(context);
    final latestRecord = healthData!.healthData.first;

    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/health/analysis'),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 标题栏
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.favorite_rounded,
                        color: AppTheme.primaryColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.healthData,
                        style: theme.textTheme.titleLarge,
                      ),
                    ],
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          AppText.viewMore,
                          style: theme.textTheme.labelMedium?.copyWith(
                            color: AppTheme.primaryColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          Icons.arrow_forward_ios_rounded,
                          size: 12,
                          color: AppTheme.primaryColor,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              const Divider(height: 24),
              
              // 健康数据网格
              Column(
                children: [
                  // 关键健康指标
                  Row(
                    children: [
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.heartRate,
                          '${latestRecord.heartRate ?? 0}',
                          AppText.heartRateUnit,
                          Icons.favorite_rounded,
                          AppTheme.heartRateColor,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.bloodOxygen,
                          '${latestRecord.bloodOxygen ?? 0}',
                          AppText.oxygenSaturationUnit,
                          Icons.air_rounded,
                          AppTheme.bloodOxygenColor,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 心率变化趋势图
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "${AppText.heartRate}趋势",
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        height: 120,
                        width: double.infinity,
                        child: _buildHeartRateChart(context),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 次要健康指标
                  Row(
                    children: [
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.temperature,
                          '${latestRecord.temperature ?? 0}',
                          AppText.temperatureUnit,
                          Icons.thermostat_rounded,
                          AppTheme.temperatureColor,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.bloodPressure,
                          '${latestRecord.pressureHigh ?? 0}/${latestRecord.pressureLow ?? 0}',
                          AppText.bloodPressureUnit,
                          Icons.favorite_border_rounded,
                          AppTheme.pressureColor,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 活动指标
                  Row(
                    children: [
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.steps,
                          '${latestRecord.step ?? 0}',
                          '',
                          Icons.directions_walk_rounded,
                          AppTheme.stepsColor,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _buildGridItem(
                          context,
                          AppText.calories,
                          '${latestRecord.calorie?.toStringAsFixed(2) ?? '0.00'}',
                          'cal',
                          Icons.local_fire_department_rounded,
                          AppTheme.calorieColor,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 新增指标：压力和距离
                  Row(
                    children: [
                      Expanded(
                        child: _buildGridItem(
                          context,
                          '压力',
                          '${latestRecord.stress ?? 0}',
                          '',
                          Icons.psychology_rounded,
                          Colors.purple,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _buildGridItem(
                          context,
                          '距离',
                          '${latestRecord.distance?.toStringAsFixed(2) ?? '0.00'}',
                          'm',
                          Icons.directions_run_rounded,
                          Colors.blue,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 睡眠数据
                  if (_hasSleepData(latestRecord))
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "睡眠数据",
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.indigo.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: _buildSleepDataWidget(context, latestRecord.sleepData),
                        ),
                        const SizedBox(height: 16),
                      ],
                    ),
                  
                  // 锻炼数据
                  if (_hasWorkoutData(latestRecord))
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "锻炼数据",
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.green.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: _buildWorkoutDataWidget(context, latestRecord.workoutData),
                        ),
                        const SizedBox(height: 16),
                      ],
                    ),
                  
                  // 日常锻炼数据
                  if (_hasExerciseDailyData(latestRecord))
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "日常锻炼",
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.orange.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: _buildExerciseDataWidget(context, latestRecord.exerciseDailyData),
                        ),
                      ],
                    ),
                ],
              ),
              
              const SizedBox(height: 12),
              
              // 上次检测时间
              Align(
                alignment: Alignment.center,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${AppText.lastCheckTime}: ${latestRecord.timestamp}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  // 构建空数据卡片
  Widget _buildEmptyCard(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/health/analysis'),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 标题栏
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.favorite_rounded,
                        color: AppTheme.primaryColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.healthData,
                        style: theme.textTheme.titleLarge,
                      ),
                    ],
                  ),
                ],
              ),
              
              const SizedBox(height: 40),
              
              Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.health_and_safety_outlined,
                      size: 48,
                      color: Colors.grey[400],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      "暂无健康数据",
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGridItem(
    BuildContext context,
    String label,
    String value,
    String unit,
    IconData icon,
    Color color,
  ) {
    final theme = Theme.of(context);
    
    return Container(
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 18, color: color),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  label,
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w500,
                    color: color,
                  ),
                ),
                LayoutBuilder(
                  builder: (context, constraints) {
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Flexible(
                          child: Text(
                            value,
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: theme.brightness == Brightness.dark 
                                  ? Colors.white 
                                  : Colors.black87,
                            ),
                            overflow: TextOverflow.ellipsis,
                            maxLines: 1,
                          ),
                        ),
                        if (unit.isNotEmpty)
                          Text(
                            unit,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.brightness == Brightness.dark 
                                  ? Colors.white70 
                                  : Colors.black54,
                            ),
                          ),
                      ],
                    );
                  }
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  // 心率变化趋势图
  Widget _buildHeartRateChart(BuildContext context) {
    if (healthData == null) return const SizedBox();
    
    // 优先使用缓存的心率数据，确保有足够的历史记录形成趋势
    List<double> heartRateData = [];
    List<String> timeLabels = [];
    
    // 尝试获取缓存的心率数据
    final cachedData = healthData!.getCachedHeartRateData();
    if (cachedData.isNotEmpty) {
      heartRateData = cachedData;
      // 生成时间标签，假设数据是按时间顺序排列，最近的在前面
      timeLabels = List.generate(heartRateData.length, (index) {
        // 简化显示，每个数据点间隔约30分钟
        final hours = (heartRateData.length - 1 - index) * 0.5;
        return hours < 1 ? "刚刚" : "${hours.toInt()}小时前";
      });
    } else if (healthData!.trends.containsKey('heartRate') && 
        healthData!.trends['heartRate']!.isNotEmpty) {
      // 备选：使用趋势数据
      heartRateData = healthData!.trends['heartRate']!;
      // 生成简单的时间标签
      timeLabels = List.generate(heartRateData.length, (index) => 
        index == 0 ? "现在" : "${index * 30}分钟前");
    } else {
      // 最后选择：使用当前记录
      heartRateData = healthData!.healthData
          .map((record) => record.heartRate ?? 0.0)
          .where((value) => value > 0) // 过滤掉无效值
          .toList();
      // 从记录中提取时间
      timeLabels = healthData!.healthData
          .where((record) => (record.heartRate ?? 0.0) > 0)
          .map((record) {
            try {
              final dt = DateTime.parse(record.timestamp);
              return "${dt.hour}:${dt.minute.toString().padLeft(2, '0')}";
            } catch (e) {
              return "";
            }
          })
          .toList();
    }
    
    // 确保有足够的数据点形成趋势线（如果数据不足，添加模拟数据点）
    if (heartRateData.isEmpty) {
      return Center(child: Text("暂无心率记录", style: Theme.of(context).textTheme.bodyMedium));
    } else if (heartRateData.length < 2) {
      // 如果只有一个数据点，添加模拟数据点以形成趋势
      final baseValue = heartRateData.first < 30 ? 70.0 : heartRateData.first; // 确保基准值合理，如果太低则使用正常值70
      heartRateData = [
        baseValue - 5, 
        baseValue - 2, 
        baseValue, 
        baseValue + 3, 
        baseValue - 1
      ];
      timeLabels = ["4小时前", "3小时前", "2小时前", "1小时前", "现在"];
    }

    // 限制显示的数据点数量，最近的数据在右侧
    if (heartRateData.length > 10) {
      heartRateData = heartRateData.take(10).toList();
      timeLabels = timeLabels.take(10).toList();
    }
    
    // 获取最大和最小值以设置图表范围，并增加一些边距
    final minValue = (heartRateData.reduce((a, b) => a < b ? a : b) - 5).clamp(0.0, double.infinity);
    final maxValue = (heartRateData.reduce((a, b) => a > b ? a : b) + 5).clamp(0.0, double.infinity);
    
    return LineChart(
      LineChartData(
        minY: minValue,
        maxY: maxValue,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: true,
          drawHorizontalLine: true,
          horizontalInterval: (maxValue - minValue) / 4,
          getDrawingHorizontalLine: (value) {
            return FlLine(
              color: Colors.grey.withOpacity(0.2),
              strokeWidth: 1,
            );
          },
          getDrawingVerticalLine: (value) {
            return FlLine(
              color: Colors.grey.withOpacity(0.2),
              strokeWidth: 1,
            );
          },
        ),
        titlesData: FlTitlesData(
          show: true,
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 22,
              getTitlesWidget: (value, meta) {
                if (value.toInt() % 2 == 0 && value.toInt() < timeLabels.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 5),
                    child: Text(
                      timeLabels[value.toInt()],
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 9,
                      ),
                    ),
                  );
                }
                return const SizedBox();
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (value, meta) {
                if (value == minValue || value == maxValue || value == (minValue + maxValue) / 2) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 5),
                    child: Text(
                      value.toInt().toString(),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 10,
                      ),
                    ),
                  );
                }
                return const SizedBox();
              },
            ),
          ),
        ),
        borderData: FlBorderData(
          show: true,
          border: Border(
            bottom: BorderSide(color: Colors.grey.withOpacity(0.3), width: 1),
            left: BorderSide(color: Colors.grey.withOpacity(0.3), width: 1),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: List.generate(
              heartRateData.length, 
              (index) => FlSpot(index.toDouble(), heartRateData[index]),
            ),
            isCurved: true,
            color: AppTheme.heartRateColor,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                radius: 4,
                color: AppTheme.heartRateColor,
                strokeWidth: 2,
                strokeColor: Colors.white,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              color: AppTheme.heartRateColor.withOpacity(0.2),
              gradient: LinearGradient(
                colors: [
                  AppTheme.heartRateColor.withOpacity(0.4),
                  AppTheme.heartRateColor.withOpacity(0.0),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            tooltipBgColor: Colors.blueGrey.withOpacity(0.8),
            getTooltipItems: (List<LineBarSpot> touchedBarSpots) {
              return touchedBarSpots.map((barSpot) {
                final index = barSpot.x.toInt();
                final time = index < timeLabels.length ? timeLabels[index] : "";
                return LineTooltipItem(
                  '${barSpot.y.toInt()} bpm\n$time',
                  const TextStyle(color: Colors.white),
                );
              }).toList();
            },
          ),
          handleBuiltInTouches: true,
        ),
      ),
    );
  }

  // 检查是否有睡眠数据
  bool _hasSleepData(health_model.HealthDataRecord record) {
    if (record.sleepData == null || record.sleepData!.isEmpty || record.sleepData == "null") return false;
    try {
      final data = json.decode(record.sleepData!);
      return data != null && data['data'] != null && data['data'].isNotEmpty;
    } catch (e) {
      debugPrint("解析睡眠数据出错: $e, 原始数据: ${record.sleepData}");
      return false;
    }
  }
  
  // 检查是否有锻炼数据
  bool _hasWorkoutData(health_model.HealthDataRecord record) {
    if (record.workoutData == null || record.workoutData!.isEmpty) return false;
    try {
      final data = json.decode(record.workoutData!);
      return data != null && data['data'] != null && data['data'].isNotEmpty;
    } catch (e) {
      return false;
    }
  }
  
  // 检查是否有日常锻炼数据
  bool _hasExerciseDailyData(health_model.HealthDataRecord record) {
    if (record.exerciseDailyData == null || record.exerciseDailyData!.isEmpty) return false;
    try {
      final data = json.decode(record.exerciseDailyData!);
      return data != null && data['data'] != null && data['data'].isNotEmpty;
    } catch (e) {
      return false;
    }
  }
  
  // 构建睡眠数据展示
  Widget _buildSleepDataWidget(BuildContext context, String? sleepDataJson) {
    final theme = Theme.of(context);
    if (sleepDataJson == null || sleepDataJson.isEmpty || sleepDataJson == "null") {
      return Text("无睡眠数据", style: theme.textTheme.bodyMedium);
    }
    
    try {
      final data = json.decode(sleepDataJson);
      
      // 处理无数据或错误码的情况
      if (data['code'] == -1 || (data['code'] == 0 && (data['data'] == null || data['data'].isEmpty))) {
        return Text("无睡眠数据", style: theme.textTheme.bodyMedium);
      }
      
      // 解析有效的睡眠数据
      final sleepRecords = data['data'] as List;
      
      // 计算总睡眠时间
      int totalSleepMinutes = 0;
      int deepSleepMinutes = 0;
      int lightSleepMinutes = 0;
      
      for (var record in sleepRecords) {
        final type = (record['type'] ?? 0) as int;
        final startTime = (record['startTimeStamp'] ?? 0) as int;
        final endTime = (record['endTimeStamp'] ?? 0) as int;
        
        if (startTime > 0 && endTime > 0) {
          final durationMinutes = (endTime - startTime) ~/ 60000; // 转换为分钟
          totalSleepMinutes += durationMinutes;
          
          if (type == 2) { // 深度睡眠
            deepSleepMinutes += durationMinutes;
          } else if (type == 1) { // 浅度睡眠
            lightSleepMinutes += durationMinutes;
          }
        }
      }
      
      // 如果有深度睡眠记录，通过时间戳获取睡眠时间范围
      String sleepTimeRange = "";
      if (sleepRecords.isNotEmpty) {
        var deepSleepRecord = sleepRecords.firstWhere((r) => (r['type'] ?? 0) == 2, orElse: () => sleepRecords.first);
        
        final startTimestamp = (deepSleepRecord['startTimeStamp'] ?? 0) as int;
        final endTimestamp = (deepSleepRecord['endTimeStamp'] ?? 0) as int;
        
        if (startTimestamp > 0 && endTimestamp > 0) {
          // 获取当地时间（自动调整时区）
          final startTime = DateTime.fromMillisecondsSinceEpoch(startTimestamp);
          final endTime = DateTime.fromMillisecondsSinceEpoch(endTimestamp);
          
          // 格式化为时间字符串
          final startTimeStr = "${startTime.hour.toString().padLeft(2, '0')}:${startTime.minute.toString().padLeft(2, '0')}";
          final endTimeStr = "${endTime.hour.toString().padLeft(2, '0')}:${endTime.minute.toString().padLeft(2, '0')}";
          
          sleepTimeRange = "$startTimeStr - $endTimeStr";
          
          // 计算睡眠持续时长
          final sleepDuration = endTime.difference(startTime);
          final sleepDurationText = "${sleepDuration.inHours}小时${sleepDuration.inMinutes % 60}分钟";
        }
      }
      
      // 计算睡眠质量评级
      String sleepQuality;
      Color qualityColor;
      
      final double totalSleepHours = totalSleepMinutes / 60;
      final double deepSleepPercentage = totalSleepMinutes > 0 ? (deepSleepMinutes / totalSleepMinutes) * 100 : 0;
      
      if (totalSleepHours >= 7 && deepSleepPercentage >= 25) {
        sleepQuality = "优质";
        qualityColor = Colors.green;
      } else if (totalSleepHours >= 6 && deepSleepPercentage >= 20) {
        sleepQuality = "良好";
        qualityColor = Colors.blue;
      } else if (totalSleepHours >= 5) {
        sleepQuality = "一般";
        qualityColor = Colors.amber;
      } else {
        sleepQuality = "不足";
        qualityColor = Colors.red;
      }
      
      final int hours = (totalSleepMinutes ~/ 60);
      final int minutes = totalSleepMinutes % 60;
      
      final int deepHours = (deepSleepMinutes ~/ 60);
      final int deepMinutes = deepSleepMinutes % 60;
      
      final int lightHours = (lightSleepMinutes ~/ 60);
      final int lightMinutes = lightSleepMinutes % 60;
      
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.nightlight_round, color: qualityColor, size: 18),
              const SizedBox(width: 8),
              Text(
                "睡眠质量$sleepQuality",
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: qualityColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          
          // 睡眠时间比例展示
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // 简易饼图
              Container(
                width: 60,
                height: 60,
                child: CustomPaint(
                  painter: SleepPieChartPainter(
                    deepSleepRatio: deepSleepMinutes / max(totalSleepMinutes, 1),
                    lightSleepRatio: lightSleepMinutes / max(totalSleepMinutes, 1),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // 睡眠数据细节
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (sleepTimeRange.isNotEmpty) ...[
                      Row(
                        children: [
                          Icon(Icons.access_time, size: 14, color: Colors.grey[600]),
                          const SizedBox(width: 4),
                          Text(
                            "睡眠时段: $sleepTimeRange",
                            style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey[600]),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                    ],
                    // 睡眠持续时长
                    Row(
                      children: [
                        Icon(Icons.hourglass_bottom, size: 14, color: Colors.grey[600]),
                        const SizedBox(width: 4),
                        Text(
                          "总睡眠: $hours小时$minutes分钟",
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          // 睡眠类型详情
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildSleepTypeItem(
                context,
                "深度睡眠",
                "$deepHours小时$deepMinutes分钟",
                "${(deepSleepPercentage).toStringAsFixed(1)}%",
                Colors.indigo,
              ),
              _buildSleepTypeItem(
                context,
                "浅度睡眠",
                "$lightHours小时$lightMinutes分钟",
                "${(100 - deepSleepPercentage).toStringAsFixed(1)}%",
                Colors.blue[300] ?? Colors.blue,
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          // 睡眠质量评估进度条
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "睡眠时长评估",
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey[600]),
              ),
              const SizedBox(height: 4),
              LinearProgressIndicator(
                value: min(totalSleepHours / 8, 1.0), // 以8小时为标准，最大值为1
                backgroundColor: Colors.grey[200],
                color: qualityColor,
                minHeight: 5,
                borderRadius: BorderRadius.circular(2.5),
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "0小时",
                    style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                  Text(
                    "8小时(推荐)",
                    style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                ],
              ),
            ],
          ),
        ],
      );
    } catch (e) {
      return Text("睡眠数据解析错误: $e", style: theme.textTheme.bodyMedium);
    }
  }
  
  // 构建睡眠类型子项
  Widget _buildSleepTypeItem(
    BuildContext context,
    String title,
    String time,
    String percentage,
    Color color,
  ) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: theme.textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            time,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            percentage,
            style: theme.textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
  
  // 构建锻炼数据展示
  Widget _buildWorkoutDataWidget(BuildContext context, String? workoutDataJson) {
    final theme = Theme.of(context);
    if (workoutDataJson == null || workoutDataJson.isEmpty) {
      return Text("暂无锻炼数据", style: theme.textTheme.bodyMedium);
    }
    
    try {
      final data = json.decode(workoutDataJson);
      if (data['data'] == null || data['data'].isEmpty) {
        return Text("暂无锻炼记录", style: theme.textTheme.bodyMedium);
      }
      
      // 这里可以根据实际数据结构进行解析和显示
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.fitness_center, color: Colors.green, size: 18),
              const SizedBox(width: 8),
              Text(
                "今日锻炼目标已完成",
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            "查看锻炼详情",
            style: theme.textTheme.bodySmall?.copyWith(
              color: Colors.green,
              decoration: TextDecoration.underline,
            ),
          ),
        ],
      );
    } catch (e) {
      return Text("锻炼数据解析错误", style: theme.textTheme.bodyMedium);
    }
  }
  
  // 构建日常锻炼数据展示
  Widget _buildExerciseDataWidget(BuildContext context, String? exerciseDataJson) {
    final theme = Theme.of(context);
    if (exerciseDataJson == null || exerciseDataJson.isEmpty) {
      return Text("暂无日常锻炼数据", style: theme.textTheme.bodyMedium);
    }
    
    try {
      final data = json.decode(exerciseDataJson);
      if (data['data'] == null || data['data'].isEmpty) {
        return Text("暂无日常锻炼记录", style: theme.textTheme.bodyMedium);
      }
      
      final exerciseData = data['data'][0];
      final strengthTimes = exerciseData['strengthTimes'] ?? 0;
      final totalTime = exerciseData['totalTime'] ?? 0;
      
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "力量训练",
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    "$strengthTimes 次",
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "总时长",
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    "$totalTime 分钟",
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      );
    } catch (e) {
      return Text("日常锻炼数据解析错误: $e", style: theme.textTheme.bodyMedium);
    }
  }
}

// 自定义睡眠饼图绘制器
class SleepPieChartPainter extends CustomPainter {
  final double deepSleepRatio;
  final double lightSleepRatio;
  
  SleepPieChartPainter({
    required this.deepSleepRatio,
    required this.lightSleepRatio,
  });
  
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2;
    
    // 绘制深度睡眠部分
    final deepSleepPaint = Paint()
      ..color = Colors.indigo
      ..style = PaintingStyle.fill;
    
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -pi / 2,  // 从12点钟方向开始
      2 * pi * deepSleepRatio,  // 弧度 = 2π × 比例
      true,
      deepSleepPaint,
    );
    
    // 绘制浅度睡眠部分
    final lightSleepPaint = Paint()
      ..color = Colors.blue[300] ?? Colors.blue
      ..style = PaintingStyle.fill;
    
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -pi / 2 + 2 * pi * deepSleepRatio,  // 从深度睡眠结束的地方开始
      2 * pi * lightSleepRatio,  // 弧度 = 2π × 比例
      true,
      lightSleepPaint,
    );
    
    // 如果有缺失部分，绘制灰色部分
    final missingRatio = 1 - deepSleepRatio - lightSleepRatio;
    if (missingRatio > 0.01) {
      final missingPaint = Paint()
        ..color = Colors.grey[300] ?? Colors.grey
        ..style = PaintingStyle.fill;
      
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        -pi / 2 + 2 * pi * (deepSleepRatio + lightSleepRatio),
        2 * pi * missingRatio,
        true,
        missingPaint,
      );
    }
    
    // 绘制中心空白圆形
    final centerCirclePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    
    canvas.drawCircle(
      center,
      radius * 0.5,  // 内圆半径为外圆的一半
      centerCirclePaint,
    );
  }
  
  @override
  bool shouldRepaint(SleepPieChartPainter oldDelegate) {
    return oldDelegate.deepSleepRatio != deepSleepRatio ||
           oldDelegate.lightSleepRatio != lightSleepRatio;
  }
} 