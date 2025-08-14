import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/device_model.dart' as device_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

class DeviceInfoCard extends StatelessWidget {
  final device_model.Device device;

  const DeviceInfoCard({
    super.key,
    required this.device,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/devices', extra: device),
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
                        Icons.watch_rounded,
                        color: AppTheme.primaryColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.deviceInfo,
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
              
              // 设备状态概览
              _buildDeviceStatusOverview(context),
              
              const SizedBox(height: 16),
              
              // 设备详细信息
              _buildInfoRow(theme, AppText.deviceNumber, device.serialNumber, Icons.smartphone_rounded),
              _buildInfoRow(theme, AppText.deviceStatus, AppText.translateDeviceStatus(device.status), Icons.info_rounded),
              _buildInfoRow(theme, AppText.chargingStatus, AppText.translateDeviceStatus(device.chargingStatus), Icons.battery_charging_full_rounded),
              _buildInfoRow(theme, AppText.wearableStatus, AppText.translateDeviceStatus(device.wearableStatus), Icons.watch_rounded),
              _buildVersionRow(theme),
              _buildInfoRow(theme, AppText.updateTime, device.updateTime, Icons.update_rounded),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildDeviceStatusOverview(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatusItem(
            context,
            Icons.battery_full_rounded,
            device.batteryLevel,
            "电量",
            _getBatteryColor(device.batteryLevel),
          ),
          _buildDivider(),
          _buildStatusItem(
            context,
            device.status == "ACTIVE" ? Icons.check_circle_rounded : Icons.error_rounded,
            AppText.translateDeviceStatus(device.status),
            "状态",
            device.status == "ACTIVE" ? AppTheme.successColor : AppTheme.warningColor,
          ),
          _buildDivider(),
          _buildStatusItem(
            context,
            device.wearableStatus == "WORN" ? Icons.watch_rounded : Icons.watch_off_rounded,
            AppText.translateDeviceStatus(device.wearableStatus),
            "佩戴",
            device.wearableStatus == "WORN" ? AppTheme.primaryColor : Colors.grey,
          ),
        ],
      ),
    );
  }
  
  Widget _buildDivider() {
    return Container(
      height: 40,
      width: 1,
      color: Colors.grey.withOpacity(0.3),
    );
  }
  
  Widget _buildStatusItem(BuildContext context, IconData icon, String value, String label, Color color) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: Colors.grey,
          ),
        ),
      ],
    );
  }
  
  Color _getBatteryColor(String level) {
    final numericLevel = int.tryParse(level.replaceAll('%', '')) ?? 0;
    if (numericLevel > 50) return AppTheme.successColor;
    if (numericLevel > 20) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }

  Widget _buildInfoRow(ThemeData theme, String label, String value, IconData icon) {
    final bool isNegative = value.contains('未') || value.contains('异常');
    final Color textColor = isNegative ? AppTheme.errorColor : Colors.grey[800]!;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(
            icon,
            size: 18,
            color: AppTheme.primaryColor.withOpacity(0.7),
          ),
          const SizedBox(width: 8),
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
                color: textColor,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVersionRow(ThemeData theme) {
    final version = device.systemSoftwareVersion;
    final parts = version.split('(');
    final mainVersion = parts[0].trim();
    final buildNumber = parts.length > 1 ? '(${parts[1]}' : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.system_update_rounded,
            size: 18,
            color: AppTheme.primaryColor.withOpacity(0.7),
          ),
          const SizedBox(width: 8),
          Expanded(
            flex: 2,
            child: Text(
              AppText.deviceVersion,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  mainVersion,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                if (buildNumber.isNotEmpty)
                  Text(
                    buildNumber,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
} 