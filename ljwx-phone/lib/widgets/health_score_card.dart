import 'package:flutter/material.dart';

class HealthScoreCard extends StatelessWidget {
  final double score;
  final Map<String, dynamic> status;
  final String lastUpdateTime;

  const HealthScoreCard({
    super.key,
    required this.score,
    required this.status,
    required this.lastUpdateTime,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final level = status['level'] as String? ?? 'unknown';
    final message = status['message'] as String? ?? '';
    final color = _getStatusColor(level);
    final statusText = _getStatusText(score);
    final badgeIcon = _getBadgeIcon(score);
    
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 左侧：环形进度条和分数
                SizedBox(
                  width: 80,
                  height: 80,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox(
                        width: 80,
                        height: 80,
                        child: CircularProgressIndicator(
                          value: score.clamp(0, 100) / 100,
                          strokeWidth: 8,
                          backgroundColor: Colors.grey[200],
                          valueColor: AlwaysStoppedAnimation<Color>(color),
                        ),
                      ),
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            score.clamp(0, 100).toStringAsFixed(1),
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: color,
                            ),
                          ),
                          Text(
                            '分',
                            style: TextStyle(
                              fontSize: 12,
                              color: color,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                // 右侧：状态和说明
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        children: [
                          const Text(
                            '总体健康评分',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(width: 8),
                          // 健康徽章
                          Icon(
                            badgeIcon,
                            color: color,
                            size: 20,
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: color.withOpacity(0.3),
                            width: 1,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              badgeIcon,
                              color: color,
                              size: 16,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              statusText,
                              style: TextStyle(
                                fontSize: 14,
                                color: color,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // 分数范围指示器
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '健康评分范围',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  height: 8,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    gradient: const LinearGradient(
                      colors: [Colors.red, Colors.orange, Colors.green],
                      stops: [0.0, 0.6, 0.8],
                    ),
                  ),
                  child: Stack(
                    children: [
                      // 当前分数指示器
                      Positioned(
                        left: (score / 100 * MediaQuery.of(context).size.width * 0.7).clamp(0, MediaQuery.of(context).size.width * 0.7 - 4),
                        top: -2,
                        child: Container(
                          width: 4,
                          height: 12,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(2),
                            border: Border.all(color: color, width: 2),
                            boxShadow: [
                              BoxShadow(
                                color: color.withOpacity(0.3),
                                blurRadius: 4,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '0',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey[600],
                      ),
                    ),
                    Text(
                      '60',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey[600],
                      ),
                    ),
                    Text(
                      '80',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey[600],
                      ),
                    ),
                    Text(
                      '100',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            if (message.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: color.withOpacity(0.2),
                    width: 1,
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.info_outline,
                      color: color,
                      size: 16,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        message,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.black87,
                          height: 1.3,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String level) {
    // 基于分数的颜色系统：80+绿色，60-80橙色，<60红色
    if (score >= 80) {
      return Colors.green;
    } else if (score >= 60) {
      return Colors.orange;
    } else {
      return Colors.red;
    }
  }

  String _getStatusText(double score) {
    if (score >= 80) {
      return '正常';
    } else if (score >= 60) {
      return '一般';
    } else {
      return '较差';
    }
  }

  IconData _getBadgeIcon(double score) {
    if (score >= 80) {
      return Icons.verified;
    } else if (score >= 60) {
      return Icons.warning_outlined;
    } else {
      return Icons.error_outline;
    }
  }
} 