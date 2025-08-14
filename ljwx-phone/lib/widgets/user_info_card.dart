import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/user_model.dart' as user_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

class UserInfoCard extends StatelessWidget {
  final user_model.User user;
  final VoidCallback onTap;

  const UserInfoCard({
    super.key,
    required this.user,
    required this.onTap,
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
                        Icons.person_rounded,
                        color: AppTheme.primaryColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.userInfo,
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
              
              // 用户信息内容
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 用户名和头像
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        user.userName,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      // 头像
                      Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: CircleAvatar(
                          radius: 30,
                          backgroundColor: AppTheme.primaryColor.withOpacity(0.1),
                          backgroundImage: user.avatar != null ? NetworkImage(user.avatar!) : null,
                          onBackgroundImageError: user.avatar != null ? (exception, stackTrace) {
                            print('Error loading avatar: $exception');
                          } : null,
                          child: user.avatar == null 
                              ? Icon(Icons.person, size: 28, color: AppTheme.primaryColor) 
                              : null,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 10),
                  
                  // 用户详细信息
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 工号
                      _buildInfoRow(
                        context,
                        AppText.userCardNumber,
                        user.userCardNumber == null || user.userCardNumber!.isEmpty ? "-" : user.userCardNumber!,
                        Icons.badge_rounded,
                      ),
                      
                      // 职位
                      _buildInfoRow(
                        context,
                        AppText.position,
                        user.position,
                        Icons.work_rounded,
                      ),
                      
                      // 工作年限
                      _buildInfoRow(
                        context,
                        AppText.workingYears,
                        "${user.workingYears}年",
                        Icons.calendar_month_rounded,
                      ),
                      
                      // 部门
                      _buildInfoRow(
                        context,
                        AppText.department,
                        user.deptHierarchy.isEmpty ? AppText.noDepartment : user.deptHierarchy.join('-'),
                        Icons.business_rounded,
                      ),
                      
                      // 设备序列号
                      _buildInfoRow(
                        context,
                        AppText.deviceSn,
                        user.deviceSn.isEmpty ? "-" : user.deviceSn,
                        Icons.devices_rounded,
                      ),
                      
                      // 创建时间
                      _buildInfoRow(
                        context,
                        AppText.createTime,
                        user.createTime,
                        Icons.calendar_today_rounded,
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildInfoRow(BuildContext context, String label, String value, IconData icon) {
    final theme = Theme.of(context);
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            icon,
            size: 16,
            color: AppTheme.primaryColor.withOpacity(0.7),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: RichText(
              text: TextSpan(
                children: [
                  TextSpan(
                    text: '$label: ',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  TextSpan(
                    text: value,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w500,
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
} 