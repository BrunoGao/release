import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/health_model.dart' as health_model;

class HealthDetailsScreen extends StatelessWidget {
  final health_model.HealthRecord healthData;

  const HealthDetailsScreen({
    super.key,
    required this.healthData,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('健康数据'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildInfoTable(theme),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoTable(ThemeData theme) {
    return Table(
      columnWidths: const {
        0: FlexColumnWidth(1),
        1: FlexColumnWidth(2),
      },
      children: [
        _buildTableRow('时间', healthData.timestamp),
        _buildTableRow('用户', healthData.userName),
        _buildTableRow('部门', healthData.deptName),
        _buildTableRow('设备号', healthData.deviceSn),
        _buildTableRow('心率', '${healthData.heartRate ?? 0} bpm'),
        _buildTableRow('血氧', '${healthData.bloodOxygen ?? 0}%'),
        _buildTableRow('压力', '${healthData.stress ?? 0}'),
        _buildTableRow('体温', '${healthData.temperature ?? '0'}°C'),
        _buildTableRow('高压', '${healthData.pressureHigh ?? 0} mmHg'),
        _buildTableRow('低压', '${healthData.pressureLow ?? 0} mmHg'),
        _buildTableRow('步数', '${healthData.step ?? '0'} 步'),
        _buildTableRow('距离', '${healthData.distance?.toStringAsFixed(2) ?? '0'} km'),
        _buildTableRow('卡路里', '${healthData.calorie?.toStringAsFixed(2) ?? '0'} kcal'),
        if (healthData.latitude != null && healthData.longitude != null)
          _buildTableRow('位置', '${healthData.latitude}, ${healthData.longitude}'),
        if (healthData.altitude != null)
          _buildTableRow('海拔', '${healthData.altitude?.toStringAsFixed(2) ?? '0'} m'),
      ],
    );
  }

  TableRow _buildTableRow(String label, String value) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Text(value),
        ),
      ],
    );
  }
} 