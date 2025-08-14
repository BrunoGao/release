import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/user_model.dart' as user_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:go_router/go_router.dart';

class UserDetailsScreen extends StatelessWidget {
  final user_model.User user;

  const UserDetailsScreen({
    super.key,
    required this.user,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.userInfo),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: CircleAvatar(
                  radius: 50,
                  backgroundImage: user.avatar != null ? NetworkImage(user.avatar!) : null,
                  onBackgroundImageError: user.avatar != null ? (exception, stackTrace) {
                    print('Error loading avatar: $exception');
                  } : null,
                  child: user.avatar == null ? const Icon(Icons.person, size: 50) : null,
                ),
              ),
              const SizedBox(height: 24),
              _buildInfoTable(theme),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoTable(ThemeData theme) {
    return Table(
      columnWidths: const {
        0: FixedColumnWidth(120),
        1: FlexColumnWidth(),
      },
      children: [
        _buildTableRow(theme, AppText.userName, user.userName),
        _buildTableRow(theme, AppText.userCardNumber, user.userCardNumber ?? AppText.notSet),
        _buildTableRow(theme, AppText.department, user.deptName),
        _buildTableRow(theme, AppText.deviceNumber, user.deviceSn),
        _buildTableRow(theme, AppText.deviceStatus, AppText.translateDeviceStatus(user.deviceStatus)),
        _buildTableRow(theme, AppText.chargingStatus, AppText.translateDeviceStatus(user.chargingStatus)),
        _buildTableRow(theme, AppText.wearableStatus, AppText.translateDeviceStatus(user.wearableStatus)),
        _buildTableRow(theme, AppText.phoneNumber, user.phoneNumber),
        _buildTableRow(theme, AppText.createTime, user.createTime),
        _buildTableRow(theme, AppText.updateTime, user.updateTime),
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
              color: value.startsWith('未') ? Colors.red : null,
            ),
          ),
        ),
      ],
    );
  }
} 