import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/message_model.dart' as message_model;
import 'package:ljwx_health_new/screens/message_details_screen.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

class MessageInfoCard extends StatelessWidget {
  final message_model.MessageInfo messageInfo;

  const MessageInfoCard({
    super.key,
    required this.messageInfo,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final latestMessages = messageInfo.messages.take(3).toList();
    final unreadMessages = messageInfo.messages.where((msg) => msg.messageStatus == 1).toList();

    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => MessageDetailsScreen(messageInfo: messageInfo),
            ),
          );
        },
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
                        Icons.notifications_rounded,
                        color: AppTheme.primaryColor,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        AppText.messages,
                        style: theme.textTheme.titleLarge,
                      ),
                      if (unreadMessages.isNotEmpty)
                        Container(
                          margin: const EdgeInsets.only(left: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            "${unreadMessages.length}",
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
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          AppText.seeAll,
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
              
              // 消息统计信息
              if (messageInfo.messages.isNotEmpty)
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
                        "消息统计",
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      
                      // 消息类型统计
                      _buildStatisticsRow(
                        context, 
                        "消息类型", 
                        {
                          "job": messageInfo.messages.where((msg) => msg.messageType == 'job').length,
                          "task": messageInfo.messages.where((msg) => msg.messageType == 'task').length,
                          "announcement": messageInfo.messages.where((msg) => msg.messageType == 'announcement').length,
                          "notification": messageInfo.messages.where((msg) => msg.messageType == 'notification').length,
                        },
                        {
                          "job": "工作通知",
                          "task": "任务消息",
                          "announcement": "系统公告",
                          "notification": "普通通知",
                        },
                        {
                          "job": Colors.teal,
                          "task": Colors.blue,
                          "announcement": Colors.purple,
                          "notification": Colors.amber,
                        },
                      ),
                      
                      const SizedBox(height: 8),
                      
                      // 消息状态统计
                      _buildStatisticsRow(
                        context, 
                        "消息状态", 
                        {
                          "1": unreadMessages.length,
                          "2": messageInfo.messages.length - unreadMessages.length,
                        },
                        {
                          "1": "未读",
                          "2": "已读",
                        },
                        {
                          "1": Colors.red,
                          "2": Colors.green,
                        },
                      ),
                      
                      // 部门消息统计（如果有）
                      if (messageInfo.departments.isNotEmpty)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 8),
                            _buildStatisticsRow(
                              context, 
                              "部门统计", 
                              messageInfo.departmentMessageCount,
                              {},
                              {"default": Colors.blueGrey},
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              
              const SizedBox(height: 16),
              
              // 消息列表
              if (latestMessages.isEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.mark_email_read_rounded, 
                            color: AppTheme.successColor.withOpacity(0.7), 
                            size: 48),
                        const SizedBox(height: 8),
                        Text(
                          AppText.noMessages,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  )
                )
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: latestMessages.length,
                  itemBuilder: (context, index) {
                    final message = latestMessages[index];
                    final color = _getMessageTypeColor(message.messageType);
                    final isUnread = message.messageStatus == '1';
                    
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: color.withOpacity(isUnread ? 0.1 : 0.05),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: color.withOpacity(isUnread ? 0.3 : 0.2),
                          width: isUnread ? 1.5 : 1,
                        ),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Stack(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: color.withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  _getMessageTypeIcon(message.messageType),
                                  color: color,
                                  size: 18,
                                ),
                              ),
                              if (isUnread)
                                Positioned(
                                  right: 0,
                                  top: 0,
                                  child: Container(
                                    width: 8,
                                    height: 8,
                                    decoration: BoxDecoration(
                                      color: AppTheme.primaryColor,
                                      shape: BoxShape.circle,
                                      border: Border.all(color: Colors.white, width: 1),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: color.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        _translateMessageType(message.messageType),
                                        style: theme.textTheme.bodySmall?.copyWith(
                                          color: color,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  message.title,
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    fontWeight: isUnread ? FontWeight.bold : FontWeight.w500,
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  message.content,
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: Colors.grey[700],
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      message.createTime,
                                      style: theme.textTheme.bodySmall?.copyWith(
                                        color: Colors.grey[600],
                                      ),
                                    ),
                                    if (isUnread)
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryColor.withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(10),
                                        ),
                                        child: Text(
                                          "未读",
                                          style: theme.textTheme.bodySmall?.copyWith(
                                            color: AppTheme.primaryColor,
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                          ),
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
                
              // 消息总数
              if (messageInfo.messages.isNotEmpty)
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
                        "共 ${messageInfo.messages.length} 条消息，${unreadMessages.length} 条未读",
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
            final color = colorMap[key] ?? colorMap["default"] ?? Colors.grey;
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

  // 翻译消息类型
  String _translateMessageType(String type) {
    return AppText.translateMessageType(type);
  }

  IconData _getMessageTypeIcon(String messageType) {
    switch (messageType.toLowerCase()) {
      case 'announcement':
        return Icons.campaign_rounded;
      case 'alert':
        return Icons.warning_amber_rounded;
      case 'notification':
        return Icons.notifications_rounded;
      default:
        return Icons.message_rounded;
    }
  }

  Color _getMessageTypeColor(String messageType) {
    switch (messageType.toLowerCase()) {
      case 'announcement':
        return AppTheme.primaryColor;
      case 'alert':
        return AppTheme.errorColor;
      case 'notification':
        return AppTheme.warningColor;
      default:
        return AppTheme.secondaryColor;
    }
  }
} 