import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../models/health_analysis.dart';
import '../models/health_factor.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/widgets/health_score_card.dart';
import 'package:ljwx_health_new/widgets/health_metric_card.dart';
import 'package:ljwx_health_new/widgets/health_suggestion_card.dart';
import 'package:flutter_radar_chart/flutter_radar_chart.dart' as radar;

class HealthAnalysisScreen extends StatefulWidget {
  final Map<String, dynamic> healthData;
  final String phoneNumber;

  const HealthAnalysisScreen({
    super.key,
    required this.healthData,
    required this.phoneNumber,
  });

  @override
  State<HealthAnalysisScreen> createState() => _HealthAnalysisScreenState();
}

class _HealthAnalysisScreenState extends State<HealthAnalysisScreen> {
  DateTime _startDate = DateTime.now().subtract(const Duration(days: 7));
  DateTime _endDate = DateTime.now();
  late Map<String, dynamic> _currentHealthData;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _currentHealthData = widget.healthData;
    _fetchHealthData();
  }

  Future<void> _fetchHealthData() async {
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = ApiService();
      final startDateStr = DateFormat('yyyy-MM-dd').format(_startDate);
      final endDateStr = DateFormat('yyyy-MM-dd').format(_endDate);
      
      final response = await apiService.getHealthDataByDateRange(
        widget.phoneNumber,
        startDateStr,
        endDateStr,
      );

      if (response['success'] == true) {
        setState(() {
          _currentHealthData = response;
          _isLoading = false;
        });
      } else {
        throw Exception('Failed to load health data');
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _selectDateRange() async {
    final ThemeData theme = Theme.of(context);
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(
        start: _startDate,
        end: _endDate,
      ),
      builder: (context, child) {
        return Theme(
          data: theme.copyWith(
            colorScheme: theme.colorScheme.copyWith(
              primary: theme.primaryColor,
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: Colors.black87,
            ),
            dialogBackgroundColor: Colors.white,
            textButtonTheme: TextButtonThemeData(
              style: TextButton.styleFrom(
                foregroundColor: theme.primaryColor,
              ),
            ),
          ),
          child: Container(
            height: 500,
            width: 360,
            child: child!,
          ),
        );
      },
      helpText: '选择日期范围',
      cancelText: '取消',
      confirmText: '确定',
      saveText: '确定',
      errorFormatText: '日期格式错误',
      errorInvalidText: '日期无效',
      errorInvalidRangeText: '日期范围无效',
      fieldStartHintText: '开始日期',
      fieldEndHintText: '结束日期',
      fieldStartLabelText: '开始日期',
      fieldEndLabelText: '结束日期',
    );

    if (picked != null) {
      setState(() {
        _startDate = picked.start;
        _endDate = picked.end;
      });
      await _fetchHealthData();
    }
  }

  Widget _buildDateRangeDisplay() {
    return Card(
      elevation: 0,
      color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
      child: InkWell(
        onTap: _selectDateRange,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Icon(
                Icons.calendar_today_outlined,
                size: 20,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(width: 12),
              Text(
                '${DateFormat('yyyy年MM月dd日').format(_startDate)} - ${DateFormat('yyyy年MM月dd日').format(_endDate)}',
                style: TextStyle(
                  fontSize: 14,
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
              const Spacer(),
              Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    print('Received healthData: ${json.encode(_currentHealthData)}');
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('健康分析'),
        actions: [
          IconButton(
            icon: const Icon(Icons.calendar_today),
            onPressed: _selectDateRange,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : _currentHealthData.isEmpty
              ? const Center(
                  child: Text('暂无数据，请检查网络连接或者重新选择日期范围'),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildDateRangeDisplay(),
                      const SizedBox(height: 16),
                      _buildSummarySection(),
                      const SizedBox(height: 24),
                      _buildHealthMetricsSection(),
                      const SizedBox(height: 24),
                      _buildHealthSuggestionsSection(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildHealthMetricsSection() {
    final healthData = _currentHealthData;
    final data = healthData['data'] as Map<String, dynamic>? ?? {};
    final healthScores = data['healthScores'] as Map<String, dynamic>? ?? {};
    final factors = healthScores['factors'] as Map<String, dynamic>? ?? {};
    final details = healthScores['details'] as Map<String, dynamic>? ?? {};
    
    if (factors.isEmpty) {
      return const Center(
        child: Text('暂无健康指标数据'),
      );
    }

    // 准备雷达图数据 - 使用评分作为雷达图的值
    final metrics = <String>[];
    final scores = <double>[];
    final statuses = <String>[];
    final messages = <String>[];
    final suggestions = <List<String>>[];

    // 按照权重排序指标
    final sortedFactors = factors.entries.toList()
      ..sort((a, b) => (b.value['weight'] as double).compareTo(a.value['weight'] as double));

    for (var factor in sortedFactors) {
      final factorData = factor.value as Map<String, dynamic>;
      final detail = details[factor.key] as Map<String, dynamic>? ?? {};
      
      metrics.add(factorData['name'] as String);
      scores.add(factorData['score'] as double);
      statuses.add(factorData['status'] as String);
      messages.add(detail['message'] as String? ?? '');
      suggestions.add((detail['suggestions'] as List<dynamic>? ?? []).cast<String>());
    }

    // 确保至少有3个数据点用于雷达图
    if (scores.length < 3) {
      // 如果数据点不足3个，添加默认数据点
      while (scores.length < 3) {
        switch (scores.length) {
          case 1:
            metrics.add('心率');
            scores.add(80.0); // 默认心率评分
            statuses.add('normal');
            messages.add('心率数据暂无记录');
            suggestions.add(['建议定期监测心率']);
            break;
          case 2:
            metrics.add('血氧');
            scores.add(85.0); // 默认血氧评分
            statuses.add('normal');
            messages.add('血氧数据暂无记录');
            suggestions.add(['建议定期监测血氧']);
            break;
        }
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '健康指标',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 300,
          child: RadarChart(
            RadarChartData(
              titleTextStyle: const TextStyle(
                color: Colors.black,
                fontSize: 12,
              ),
              tickCount: 5,
              ticksTextStyle: const TextStyle(
                color: Colors.black,
                fontSize: 10,
              ),
              gridBorderData: const BorderSide(
                color: Colors.grey,
                width: 1,
              ),
              tickBorderData: const BorderSide(
                color: Colors.grey,
                width: 1,
              ),
              getTitle: (index, angle) => RadarChartTitle(
                text: metrics[index],
                angle: angle,
              ),
              titlePositionPercentageOffset: 0.2,
              dataSets: [
                RadarDataSet(
                  fillColor: Colors.blue.withOpacity(0.2),
                  borderColor: Colors.blue,
                  entryRadius: 3,
                  dataEntries: scores
                      .map((score) => RadarEntry(value: score))
                      .toList(),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: sortedFactors.length, // 只显示真实数据
          itemBuilder: (context, index) {
            final factor = sortedFactors[index].value as Map<String, dynamic>;
            final detail = details[sortedFactors[index].key] as Map<String, dynamic>? ?? {};
            final metricName = factor['name'] as String;
            final score = factor['score'] as double;
            final status = factor['status'] as String;
            final message = detail['message'] as String? ?? '';
            final suggestionsList = (detail['suggestions'] as List<dynamic>? ?? []).cast<String>();
            
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          metricName,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getStatusColor(status).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            _getStatusText(status),
                            style: TextStyle(
                              color: _getStatusColor(status),
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      message,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Colors.black87,
                      ),
                    ),
                    if (suggestionsList.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      const Text(
                        '建议：',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 4),
                      ...suggestionsList.map((suggestion) => Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('• ', style: TextStyle(fontSize: 14)),
                            Expanded(
                              child: Text(
                                suggestion,
                                style: const TextStyle(fontSize: 14),
                              ),
                            ),
                          ],
                        ),
                      )),
                    ],
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'excellent':
        return Colors.green;
      case 'good':
        return Colors.blue;
      case 'normal':
        return Colors.blue;
      case 'fair':
        return Colors.orange;
      case 'warning':
        return Colors.orange;
      case 'danger':
        return Colors.red;
      case 'low':
        return Colors.orange;
      case 'high':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _getStatusText(String status) {
    switch (status) {
      case 'excellent':
        return '优秀';
      case 'good':
        return '良好';
      case 'normal':
        return '正常';
      case 'fair':
        return '一般';
      case 'warning':
        return '警告';
      case 'danger':
        return '危险';
      case 'low':
        return '偏低';
      case 'high':
        return '偏高';
      default:
        return '未知';
    }
  }

  Widget _buildHealthSuggestionsSection() {
    final healthData = _currentHealthData;
    final suggestions = <Map<String, dynamic>>[];
    
    // 根据各项指标生成建议
    final stats = healthData['statistics'] as Map<String, dynamic>? ?? {};
    final averageStats = stats['averageStats'] as Map<String, dynamic>? ?? {};
    
    if (averageStats['avgHeartRate'] != null) {
      final heartRate = (averageStats['avgHeartRate'] as num).toDouble();
      if (heartRate < 60) {
        suggestions.add({
          'title': '心率',
          'suggestion': '您的心率偏低，建议适当进行有氧运动，如散步、慢跑等。',
          'status': {'level': 'fair', 'text': '需要关注'},
        });
      } else if (heartRate > 100) {
        suggestions.add({
          'title': '心率',
          'suggestion': '您的心率偏高，建议放松心情，避免剧烈运动。',
          'status': {'level': 'fair', 'text': '需要关注'},
        });
      }
    }
    
    if (averageStats['avgBloodOxygen'] != null) {
      final bloodOxygen = (averageStats['avgBloodOxygen'] as num).toDouble();
      if (bloodOxygen < 95) {
        suggestions.add({
          'title': '血氧',
          'suggestion': '您的血氧饱和度偏低，建议保持良好的呼吸，必要时就医检查。',
          'status': {'level': 'fair', 'text': '需要关注'},
        });
      }
    }
    
    if (averageStats['avgStep'] != null) {
      final steps = (averageStats['avgStep'] as num).toDouble();
      if (steps < 6000) {
        suggestions.add({
          'title': '运动量',
          'suggestion': '您的日均步数偏低，建议每天保持适度运动，目标8000-10000步。',
          'status': {'level': 'fair', 'text': '需要关注'},
        });
      }
    }

    if (suggestions.isEmpty) {
      suggestions.add({
        'title': '综合建议',
        'suggestion': '您的各项健康指标良好，请继续保持健康的生活方式。',
        'status': {'level': 'excellent', 'text': '优秀'},
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '健康建议',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        ...suggestions.map((suggestion) => Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: HealthSuggestionCard(
            title: suggestion['title'] as String,
            suggestion: suggestion['suggestion'] as String,
            status: suggestion['status'] as Map<String, dynamic>,
          ),
        )),
      ],
    );
  }

  Widget _buildSummarySection() {
    final healthData = _currentHealthData;
    final data = healthData['data'] as Map<String, dynamic>? ?? {};
    final summary = data['summary'] as Map<String, dynamic>? ?? {};
    final healthScores = data['healthScores'] as Map<String, dynamic>? ?? {};
    
    // 打印解析的数据
    print('Data: $data');
    print('Summary: $summary');
    print('HealthScores: $healthScores');
    
    final totalRecords = summary['totalRecords'] as int? ?? 0;
    final startTime = summary['startTime'] as String? ?? '';
    final endTime = summary['endTime'] as String? ?? '';
    final healthScore = summary['healthScore'] as double? ?? 0.0;
    final healthStatus = summary['healthStatus'] as Map<String, dynamic>? ?? {};
    
    // 打印解析后的具体值
    print('Total Records: $totalRecords');
    print('Start Time: $startTime');
    print('End Time: $endTime');
    print('Health Score: $healthScore');
    print('Health Status: $healthStatus');
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        HealthScoreCard(
          score: healthScore,
          status: {
            'level': healthStatus['level'] ?? 'unknown',
            'text': _getStatusText(healthStatus['level'] ?? 'unknown'),
            'message': healthStatus['message'] ?? '暂无健康建议',
          },
          lastUpdateTime: summary['lastUpdateTime'] ?? '',
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '数据统计',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '总记录数：$totalRecords 条',
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.black87,
                  ),
                ),
                if (startTime.isNotEmpty && endTime.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    '记录时间：${startTime.split(' ')[0]} 至 ${endTime.split(' ')[0]}',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '最后更新：${summary['lastUpdateTime']?.split(' ')[1] ?? ''}',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  double _calculateHealthScore(Map<String, dynamic> averageStats) {
    if (averageStats.isEmpty) return 0.0;
    
    double totalScore = 0.0;
    int validMetrics = 0;
    
    // 心率评分 (60-100为正常)
    if (averageStats['avgHeartRate'] != null) {
      final heartRate = (averageStats['avgHeartRate'] as num).toDouble();
      totalScore += _calculateMetricScore(heartRate, 60, 100);
      validMetrics++;
    }
    
    // 血氧评分 (95-100为正常)
    if (averageStats['avgBloodOxygen'] != null) {
      final bloodOxygen = (averageStats['avgBloodOxygen'] as num).toDouble();
      totalScore += _calculateMetricScore(bloodOxygen, 95, 100);
      validMetrics++;
    }
    
    // 体温评分 (35-37.5为正常)
    if (averageStats['avgTemperature'] != null) {
      final temperature = (averageStats['avgTemperature'] as num).toDouble();
      totalScore += _calculateMetricScore(temperature, 35, 37.5);
      validMetrics++;
    }
    
    // 步数评分 (以8000步为标准)
    if (averageStats['avgStep'] != null) {
      final steps = (averageStats['avgStep'] as num).toDouble();
      totalScore += (steps / 8000 * 100).clamp(0, 100);
      validMetrics++;
    }
    
    return validMetrics > 0 ? (totalScore / validMetrics).clamp(0, 100) : 0.0;
  }

  double _calculateMetricScore(double value, double min, double max) {
    if (value < min) {
      return (value / min * 100).clamp(0, 100);
    } else if (value > max) {
      return (100 - (value - max) / max * 100).clamp(0, 100);
    } else {
      return 100 - (((value - (min + max) / 2).abs() / ((max - min) / 2)) * 20);
    }
  }

  Map<String, dynamic> _getOverallStatus(double score) {
    if (score >= 90) {
      return {'level': 'excellent', 'text': '优秀', 'message': '您的健康状况非常好，请继续保持！'};
    } else if (score >= 75) {
      return {'level': 'good', 'text': '良好', 'message': '您的健康状况良好，建议继续保持健康的生活方式。'};
    } else if (score >= 60) {
      return {'level': 'fair', 'text': '一般', 'message': '您的部分健康指标需要关注，建议适当调整生活习惯。'};
    } else {
      return {'level': 'poor', 'text': '较差', 'message': '您的健康状况需要改善，建议及时就医检查。'};
    }
  }
}

// 定义图表主题类
class ChartTheme {
  final Color primaryColor;
  final List<Color> gradientColors;

  ChartTheme({
    required this.primaryColor,
    required this.gradientColors,
  });
}

class _TimeSeriesData {
  final DateTime time;
  final double value;

  _TimeSeriesData(this.time, this.value);
} 