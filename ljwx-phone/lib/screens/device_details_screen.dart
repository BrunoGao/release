import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/device_model.dart' as device_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:go_router/go_router.dart';

class DeviceDetailsScreen extends StatelessWidget {
  final device_model.Device device;

  const DeviceDetailsScreen({
    super.key,
    required this.device,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.deviceInfo),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
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
        _buildTableRow(theme, AppText.deviceNumber, device.serialNumber),
        _buildTableRow(theme, AppText.bluetoothAddress, device.bluetoothAddress),
        _buildTableRow(theme, AppText.chargingStatus, device.chargingStatus),
        _buildTableRow(theme, AppText.batteryLevel, device.batteryLevel),
        _buildTableRow(theme, AppText.deviceStatus, device.status),
        _buildTableRow(theme, AppText.deviceVersion, device.systemSoftwareVersion),
        _buildTableRow(theme, AppText.updateTime, device.updateTime),
        _buildTableRow(theme, AppText.wearableStatus, device.wearableStatus),
        if (device.departmentName != null)
          _buildTableRow(theme, AppText.department, device.departmentName!),
        if (device.userName != null)
          _buildTableRow(theme, AppText.userName, device.userName!),
      ],
    );
  }

  TableRow _buildTableRow(ThemeData theme, String label, String value) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Text(
            label,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Text(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: value.startsWith('NOT') ? Colors.red : null,
            ),
          ),
        ),
      ],
    );
  }
} 