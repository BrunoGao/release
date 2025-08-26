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
      backgroundColor: theme.colorScheme.surface,
      appBar: AppBar(
        title: Text(AppText.deviceInfo),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // 设备图标和基本信息卡片
            _buildDeviceHeaderCard(theme).animate()
              .fadeIn(duration: 600.ms, delay: 100.ms)
              .slideY(begin: 0.2, end: 0),
            
            const SizedBox(height: 16),
            
            // 设备状态卡片
            _buildStatusCard(theme).animate()
              .fadeIn(duration: 600.ms, delay: 200.ms)
              .slideY(begin: 0.2, end: 0),
            
            const SizedBox(height: 16),
            
            // 设备规格信息卡片
            _buildSpecsCard(theme).animate()
              .fadeIn(duration: 600.ms, delay: 300.ms)
              .slideY(begin: 0.2, end: 0),
            
            const SizedBox(height: 16),
            
            // 用户绑定信息卡片
            if (device.userName != null)
              _buildUserBindingCard(theme).animate()
                .fadeIn(duration: 600.ms, delay: 400.ms)
                .slideY(begin: 0.2, end: 0),
          ],
        ),
      ),
    );
  }

  Widget _buildDeviceHeaderCard(ThemeData theme) {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        padding: const EdgeInsets.all(24.0),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.primary.withOpacity(0.1),
              theme.colorScheme.secondary.withOpacity(0.1),
            ],
          ),
        ),
        child: Column(
          children: [
            Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: theme.colorScheme.primary.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: CircleAvatar(
                radius: 50,
                backgroundColor: theme.colorScheme.primary.withOpacity(0.2),
                child: Icon(
                  Icons.watch,
                  size: 50,
                  color: theme.colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              device.serialNumber,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getStatusColor(device.status).withOpacity(0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _getStatusColor(device.status),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _translateStatus(device.status),
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: _getStatusColor(device.status),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(ThemeData theme) {
    return _buildInfoCard(theme, '设备状态', Icons.assignment_turned_in, [
      _buildStatusRow(
        icon: Icons.battery_std,
        label: AppText.batteryLevel,
        value: device.batteryLevel,
        color: _getBatteryColor(device.batteryLevel),
      ),
      _buildStatusRow(
        icon: Icons.power,
        label: AppText.chargingStatus,
        value: _translateStatus(device.chargingStatus),
        color: _getChargingColor(device.chargingStatus),
      ),
      _buildStatusRow(
        icon: Icons.accessibility,
        label: AppText.wearableStatus,
        value: _translateStatus(device.wearableStatus),
        color: _getWearableColor(device.wearableStatus),
      ),
    ]);
  }

  Widget _buildSpecsCard(ThemeData theme) {
    return _buildInfoCard(theme, '设备规格', Icons.info_outline, [
      _buildInfoRow(AppText.deviceNumber, device.serialNumber),
      _buildInfoRow(AppText.bluetoothAddress, device.bluetoothAddress),
      _buildInfoRow(AppText.deviceVersion, device.systemSoftwareVersion),
      _buildInfoRow(AppText.updateTime, device.updateTime),
    ]);
  }

  Widget _buildUserBindingCard(ThemeData theme) {
    return _buildInfoCard(theme, '用户绑定', Icons.person_pin, [
      _buildInfoRow(AppText.userName, device.userName ?? '未绑定'),
      if (device.departmentName != null)
        _buildInfoRow(AppText.department, device.departmentName!),
    ]);
  }

  Widget _buildInfoCard(ThemeData theme, String title, IconData icon, List<Widget> children) {
    return Card(
      elevation: 6,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    icon,
                    color: theme.colorScheme.onPrimaryContainer,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildStatusRow({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 12),
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: color.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    value,
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[200]!),
              ),
              child: Text(
                value,
                style: TextStyle(
                  color: value.contains('NOT') || value.contains('未') ? Colors.red : Colors.black87,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'ONLINE':
      case 'CONNECTED':
        return Colors.green;
      case 'OFFLINE':
      case 'DISCONNECTED':
        return Colors.red;
      case 'CHARGING':
        return Colors.blue;
      default:
        return Colors.orange;
    }
  }

  Color _getBatteryColor(String batteryLevel) {
    if (batteryLevel.contains('%')) {
      final level = int.tryParse(batteryLevel.replaceAll('%', '')) ?? 0;
      if (level > 60) return Colors.green;
      if (level > 30) return Colors.orange;
      return Colors.red;
    }
    return Colors.grey;
  }

  Color _getChargingColor(String chargingStatus) {
    switch (chargingStatus.toUpperCase()) {
      case 'CHARGING':
        return Colors.green;
      case 'CHARGED':
        return Colors.blue;
      case 'NOT_CHARGING':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  Color _getWearableColor(String wearableStatus) {
    switch (wearableStatus.toUpperCase()) {
      case 'WEARING':
        return Colors.green;
      case 'NOT_WEARING':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _translateStatus(String status) {
    switch (status.toUpperCase()) {
      case 'ONLINE':
        return '在线';
      case 'OFFLINE':
        return '离线';
      case 'CHARGING':
        return '充电中';
      case 'NOT_CHARGING':
        return '未充电';
      case 'CHARGED':
        return '已充满';
      case 'WEARING':
        return '佩戴中';
      case 'NOT_WEARING':
        return '未佩戴';
      case 'CONNECTED':
        return '已连接';
      case 'DISCONNECTED':
        return '已断开';
      default:
        return status;
    }
  }
} 