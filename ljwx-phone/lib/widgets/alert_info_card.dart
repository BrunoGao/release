import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/alert_model.dart' as alert_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

class AlertInfoCard extends StatelessWidget {
  final alert_model.AlertInfo alertInfo;
  final VoidCallback onTap;

  const AlertInfoCard({
    super.key,
    required this.alertInfo,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final latestAlerts = alertInfo.alerts.take(3).toList();
    final pendingAlerts = alertInfo.alerts.where((alert) => alert.alertStatus == 'pending').toList();

    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
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
                        Icons.warning_amber_rounded,
                        color: AppTheme.warningColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.alerts,
                        style: theme.textTheme.titleLarge,
                      ),
                      if (pendingAlerts.isNotEmpty)
                        Container(
                          margin: const EdgeInsets.only(left: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.errorColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            "${pendingAlerts.length}",
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.warningColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          AppText.seeAll,
                          style: theme.textTheme.labelMedium?.copyWith(
                            color: AppTheme.warningColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          Icons.arrow_forward_ios_rounded,
                          size: 12,
                          color: AppTheme.warningColor,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              const Divider(height: 24),
              
              // 告警统计信息
              if (alertInfo.alerts.isNotEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.grey.withOpacity(0.2),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "告警统计",
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      _buildStatisticsRow(
                        context, 
                        "严重级别", 
                        alertInfo.alertLevelCount,
                        {
                          "critical": "紧急",
                          "high": "高危",
                          "medium": "中危",
                        },
                        {
                          "critical": AppTheme.errorColor,
                          "high": AppTheme.warningColor,
                          "medium": Colors.amber,
                        },
                      ),
                      const SizedBox(height: 8),
                      _buildStatisticsRow(
                        context, 
                        "告警类型", 
                        alertInfo.alertTypeCount,
                        {
                          "fall_down": "跌倒告警",
                          "one_key_alarm": "一键告警",
                          "sleep": "睡眠告警",
                          "heart_rate": "心率告警",
                          "blood_oxygen": "血氧告警",
                          "temperature": "体温告警",
                          "blood_pressure": "血压告警",
                          "activity": "活动告警",
                        },
                        {
                          "fall_down": Colors.indigo,
                          "one_key_alarm": Colors.deepPurple,
                          "sleep": Colors.teal,
                          "heart_rate": Colors.red,
                          "blood_oxygen": Colors.lightBlue,
                          "temperature": Colors.orange,
                          "blood_pressure": Colors.purple,
                          "activity": Colors.green,
                        },
                      ),
                      const SizedBox(height: 8),
                      _buildStatisticsRow(
                        context, 
                        "处理状态", 
                        alertInfo.alertStatusCount,
                        {
                          "pending": "待处理",
                          "responded": "已处理",
                        },
                        {
                          "pending": AppTheme.errorColor,
                          "responded": AppTheme.successColor,
                        },
                      ),
                    ],
                  ),
                ),
              
              const SizedBox(height: 16),
              
              // 告警列表
              if (latestAlerts.isEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.check_circle_outline, 
                            color: AppTheme.successColor.withOpacity(0.7), 
                            size: 48),
                        const SizedBox(height: 8),
                        Text(
                          AppText.noAlerts,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  )
                )
              else
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "最近告警",
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: latestAlerts.length,
                      itemBuilder: (context, index) {
                        final alert = latestAlerts[index];
                        return Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: _getAlertColor(alert.severityLevel).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: alert.alertStatus == 'pending' 
                                ? Border.all(color: AppTheme.errorColor.withOpacity(0.5), width: 1.5)
                                : null,
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: _getAlertColor(alert.severityLevel).withOpacity(0.2),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  _getAlertIcon(alert.severityLevel),
                                  color: _getAlertColor(alert.severityLevel),
                                  size: 16,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Text(
                                            _translateAlertType(alert.alertType),
                                            style: theme.textTheme.titleSmall?.copyWith(
                                              fontWeight: FontWeight.bold,
                                              color: _getAlertColor(alert.severityLevel),
                                            ),
                                          ),
                                        ),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: _getAlertColor(alert.severityLevel).withOpacity(0.2),
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                          child: Text(
                                            _translateAlertLevel(alert.severityLevel),
                                            style: theme.textTheme.bodySmall?.copyWith(
                                              color: _getAlertColor(alert.severityLevel),
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      alert.alertDesc,
                                      style: theme.textTheme.bodyMedium,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          alert.alertTimestamp,
                                          style: theme.textTheme.bodySmall?.copyWith(
                                            color: Colors.grey[600],
                                          ),
                                        ),
                                        if (alert.alertStatus == 'pending')
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: AppTheme.errorColor.withOpacity(0.1),
                                              borderRadius: BorderRadius.circular(10),
                                              border: Border.all(
                                                color: AppTheme.errorColor.withOpacity(0.3),
                                                width: 1,
                                              ),
                                            ),
                                            child: Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                Icon(
                                                  Icons.warning_amber_rounded,
                                                  size: 10,
                                                  color: AppTheme.errorColor,
                                                ),
                                                const SizedBox(width: 2),
                                                Text(
                                                  "待处理",
                                                  style: theme.textTheme.bodySmall?.copyWith(
                                                    color: AppTheme.errorColor,
                                                    fontSize: 10,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ],
                ),
                
              // 告警总数
              if (alertInfo.alerts.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.grey.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(
                        "共 ${alertInfo.alerts.length} 条告警，${pendingAlerts.length} 条待处理",
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
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

  // 构建统计信息行
  Widget _buildStatisticsRow(
    BuildContext context, 
    String title, 
    Map<String, int> countMap,
    Map<String, String> translations,
    Map<String, Color> colorMap,
  ) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: countMap.entries.map((entry) {
            final key = entry.key;
            final count = entry.value;
            final color = colorMap[key] ?? Colors.grey;
            final label = translations[key] ?? key;
            
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: color.withOpacity(0.2),
                  width: 1,
                ),
              ),
              child: Text(
                "$label: $count",
                style: theme.textTheme.bodySmall?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // 翻译告警级别
  String _translateAlertLevel(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return '紧急';
      case 'high':
        return '高危';
      case 'medium':
        return '中危';
      default:
        return level;
    }
  }
  
  // 翻译告警类型
  String _translateAlertType(String type) {
    switch (type.toLowerCase()) {
      case 'fall_down':
        return '跌倒告警';
      case 'one_key_alarm':
        return '一键告警';
      case 'sleep':
        return '睡眠告警';
      case 'heart_rate':
        return '心率告警';
      case 'blood_oxygen':
        return '血氧告警';
      case 'temperature':
        return '体温告警';
      case 'blood_pressure':
        return '血压告警';
      case 'activity':
        return '活动告警';
      default:
        return type;
    }
  }

  Color _getAlertColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return AppTheme.errorColor;
      case 'warning':
        return AppTheme.warningColor;
      case 'info':
        return AppTheme.primaryColor;
      default:
        return Colors.grey;
    }
  }
  
  IconData _getAlertIcon(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return Icons.error_outline_rounded;
      case 'warning':
        return Icons.warning_amber_rounded;
      case 'info':
        return Icons.info_outline_rounded;
      default:
        return Icons.notifications_none_rounded;
    }
  }
} 