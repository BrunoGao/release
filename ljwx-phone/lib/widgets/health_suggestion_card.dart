import 'package:flutter/material.dart';

class HealthSuggestionCard extends StatelessWidget {
  final String title;
  final String suggestion;
  final Map<String, dynamic> status;

  const HealthSuggestionCard({
    super.key,
    required this.title,
    required this.suggestion,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    final level = status['level'] as String? ?? 'unknown';
    final text = status['text'] as String? ?? '未知';
    final color = _getStatusColor(level);

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 14,
                      color: color,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              suggestion,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.black87,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String level) {
    switch (level.toLowerCase()) {
      case 'excellent':
        return Colors.green;
      case 'good':
        return Colors.blue;
      case 'fair':
        return Colors.orange;
      case 'poor':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
} 