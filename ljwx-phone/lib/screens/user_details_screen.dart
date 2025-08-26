import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/user_model.dart' as user_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';

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
      backgroundColor: theme.colorScheme.surface,
      appBar: AppBar(
        title: Text(AppText.userInfo),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              // 用户头像和基本信息卡片
              _buildUserProfileCard(theme).animate()
                .fadeIn(duration: 600.ms, delay: 100.ms)
                .slideY(begin: 0.2, end: 0),
              
              const SizedBox(height: 16),
              
              // 个人信息卡片
              _buildInfoCard(theme, '个人信息', Icons.person, [
                _buildInfoRow(AppText.userName, user.userName),
                _buildInfoRow(AppText.userCardNumber, user.userCardNumber ?? AppText.notSet),
                _buildInfoRow(AppText.phoneNumber, user.phoneNumber),
                _buildInfoRow(AppText.department, user.deptName),
              ]).animate()
                .fadeIn(duration: 600.ms, delay: 200.ms)
                .slideY(begin: 0.2, end: 0),
              
              const SizedBox(height: 16),
              
              // 设备信息卡片
              _buildInfoCard(theme, AppText.deviceInfo, Icons.watch, [
                _buildInfoRow(AppText.deviceNumber, user.deviceSn),
                _buildInfoRow(AppText.deviceStatus, AppText.translateDeviceStatus(user.deviceStatus)),
                _buildInfoRow(AppText.chargingStatus, AppText.translateDeviceStatus(user.chargingStatus)),
                _buildInfoRow(AppText.wearableStatus, AppText.translateDeviceStatus(user.wearableStatus)),
              ]).animate()
                .fadeIn(duration: 600.ms, delay: 300.ms)
                .slideY(begin: 0.2, end: 0),
              
              const SizedBox(height: 16),
              
              // 时间信息卡片
              _buildInfoCard(theme, '时间信息', Icons.schedule, [
                _buildInfoRow(AppText.createTime, user.createTime),
                _buildInfoRow(AppText.updateTime, user.updateTime),
              ]).animate()
                .fadeIn(duration: 600.ms, delay: 400.ms)
                .slideY(begin: 0.2, end: 0),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUserProfileCard(ThemeData theme) {
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
                backgroundImage: user.avatar != null ? NetworkImage(user.avatar!) : null,
                onBackgroundImageError: user.avatar != null ? (exception, stackTrace) {
                  print('Error loading avatar: $exception');
                } : null,
                child: user.avatar == null 
                  ? Icon(Icons.person, size: 50, color: theme.colorScheme.primary) 
                  : null,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              user.userName,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                user.deptName,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onPrimaryContainer,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
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
                  color: value.contains('未') || value.contains('UNKNOWN') ? Colors.red : Colors.black87,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
} 