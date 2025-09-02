import 'package:flutter/material.dart';
import 'health_factor.dart';

class HealthAnalysis {
  final List<HealthAlert> alerts;
  final List<HealthStatus> healthStatus;
  final Map<String, MetricInfo> metrics;
  final Map<String, dynamic> summary;
  final TimelineEntry timeline;
  final Map<String, dynamic> healthScores;
  final List<HealthFactor> healthFactors;
  final Map<String, List<double>> metricsData;
  final List<String> timestamps;

  HealthAnalysis({
    required this.alerts,
    required this.healthStatus,
    required this.metrics,
    required this.summary,
    required this.timeline,
    required this.healthScores,
    required this.healthFactors,
    required this.metricsData,
    required this.timestamps,
  });

  factory HealthAnalysis.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? {};
    final healthScoresData = data['healthScores'] ?? {};
    final factorsMap = healthScoresData['factors'] as Map<String, dynamic>? ?? {};
    
    return HealthAnalysis(
      alerts: ((data['alerts'] as List?) ?? [])
          .map((e) => HealthAlert.fromJson(e))
          .toList(),
      healthStatus: ((data['healthStatus'] as List?) ?? [])
          .map((e) => HealthStatus.fromJson(e))
          .toList(),
      metrics: Map.fromEntries(((data['metrics'] as Map<String, dynamic>?) ?? {})
          .entries
          .map((e) => MapEntry(e.key, MetricInfo.fromJson(e.value)))),
      summary: data['summary'] ?? {},
      timeline: TimelineEntry.fromJson(data['timeline'] ?? {}),
      healthScores: healthScoresData,
      healthFactors: factorsMap.entries
          .map((e) => HealthFactor.fromJson(e.value as Map<String, dynamic>))
          .toList(),
      metricsData: _parseMetricsData(data['timeline']?['data'] ?? {}),
      timestamps: List<String>.from(data['timeline']?['timestamps'] ?? []),
    );
  }

  static Map<String, List<double>> _parseMetricsData(Map<String, dynamic> metricsData) {
    final result = <String, List<double>>{};
    metricsData.forEach((key, value) {
      if (value is List) {
        result[key] = value.map((e) => (e as num).toDouble()).toList();
      }
    });
    return result;
  }

  Map<String, dynamic> toJson() {
    return {
      'data': {
        'healthScores': healthScores,
        'summary': summary,
      },
    };
  }
}

class HealthAlert {
  final String message;
  final String metric;
  final String name;
  final String time;
  final String type;

  HealthAlert({
    required this.message,
    required this.metric,
    required this.name,
    required this.time,
    required this.type,
  });

  factory HealthAlert.fromJson(Map<String, dynamic> json) {
    return HealthAlert(
      message: json['message'] ?? '',
      metric: json['metric'] ?? '',
      name: json['name'] ?? '',
      time: json['time'] ?? '',
      type: json['type'] ?? '',
    );
  }
}

class HealthStatus {
  final double changeRate;
  final double currentValue;
  final String metric;
  final String name;
  final String status;
  final String trend;

  HealthStatus({
    required this.changeRate,
    required this.currentValue,
    required this.metric,
    required this.name,
    required this.status,
    required this.trend,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      changeRate: (json['changeRate'] ?? 0).toDouble(),
      currentValue: (json['currentValue'] ?? 0).toDouble(),
      metric: json['metric'] ?? '',
      name: json['name'] ?? '',
      status: json['status'] ?? '',
      trend: json['trend'] ?? '',
    );
  }

  Color getStatusColor() {
    switch (status) {
      case 'normal':
        return Colors.green;
      case 'low':
        return Colors.orange;
      case 'high':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData getTrendIcon() {
    switch (trend) {
      case '上升':
        return Icons.trending_up;
      case '下降':
        return Icons.trending_down;
      default:
        return Icons.trending_flat;
    }
  }
}

class MetricInfo {
  final String name;
  final double normalMax;
  final double normalMin;
  final String unit;

  MetricInfo({
    required this.name,
    required this.normalMax,
    required this.normalMin,
    required this.unit,
  });

  factory MetricInfo.fromJson(Map<String, dynamic> json) {
    return MetricInfo(
      name: json['name'] ?? '',
      normalMax: (json['normalMax'] ?? 0).toDouble(),
      normalMin: (json['normalMin'] ?? 0).toDouble(),
      unit: json['unit'] ?? '',
    );
  }
}

class AnalysisSummary {
  final String endTime;
  final String startTime;
  final int totalRecords;

  AnalysisSummary({
    required this.endTime,
    required this.startTime,
    required this.totalRecords,
  });

  factory AnalysisSummary.fromJson(Map<String, dynamic> json) {
    return AnalysisSummary(
      endTime: json['endTime'] ?? '',
      startTime: json['startTime'] ?? '',
      totalRecords: json['totalRecords'] ?? 0,
    );
  }
}

class TimelineEntry {
  final String time;
  final Map<String, List<Map<String, dynamic>>> anomalies;
  final Map<String, List<double>> metrics;
  final List<String> timestamps;

  TimelineEntry({
    required this.time,
    required this.anomalies,
    required this.metrics,
    required this.timestamps,
  });

  factory TimelineEntry.fromJson(Map<String, dynamic> json) {
    final anomaliesMap = <String, List<Map<String, dynamic>>>{};
    if (json['anomalies'] is Map) {
      (json['anomalies'] as Map).forEach((key, value) {
        if (value is List) {
          anomaliesMap[key.toString()] = value.map((e) => Map<String, dynamic>.from(e)).toList();
        }
      });
    }

    final metricsMap = <String, List<double>>{};
    if (json['metrics'] is Map) {
      (json['metrics'] as Map).forEach((key, value) {
        if (value is List) {
          metricsMap[key.toString()] = value.map((e) => (e as num).toDouble()).toList();
        }
      });
    }

    return TimelineEntry(
      time: json['time'] ?? '',
      anomalies: anomaliesMap,
      metrics: metricsMap,
      timestamps: (json['timestamps'] as List?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
} 