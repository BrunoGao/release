import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/message_model.dart' as message_model;
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/pages/message_detail_page.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import '../global.dart';

class MessageDetailsScreen extends StatefulWidget {
  final message_model.MessageInfo messageInfo;

  const MessageDetailsScreen({
    super.key,
    required this.messageInfo,
  });

  @override
  State<MessageDetailsScreen> createState() => _MessageDetailsScreenState();
}

class _MessageDetailsScreenState extends State<MessageDetailsScreen> {
  final ApiService _apiService = ApiService();
  bool _isProcessing = false;
  List<message_model.Message> _messages = [];

  @override
  void initState() {
    super.initState();
    _messages = List.from(widget.messageInfo.messages);
  }

  // 标记所有消息为已读
  Future<void> _markAllAsRead(BuildContext context) async {
    if (_isProcessing) return;
    
    setState(() => _isProcessing = true);
    
    // 获取所有未读消息
    final unreadMessages = _messages.where((msg) => msg.messageStatus == '1').toList();
    
    if (unreadMessages.isEmpty) {
      setState(() => _isProcessing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('没有未读消息需要处理')),
      );
      return;
    }
    
    int successCount = 0;
    String targetDeviceSn = deviceSn;
    
    // 确保设备序列号不是MAC地址格式
    if (targetDeviceSn.contains(':')) {
      debugPrint('警告: 设备序列号是MAC地址格式，尝试从系统配置获取正确格式');
      // 从系统配置获取正确的设备序列号
      if (systemConfig.containsKey('device_sn') && systemConfig['device_sn'] != null) {
        targetDeviceSn = systemConfig['device_sn'].toString();
        debugPrint('从系统配置获取设备序列号: $targetDeviceSn');
      }
    }
    
    debugPrint('使用设备序列号标记消息已读: $targetDeviceSn');
    
    // 逐个标记消息为已读
    for (var message in unreadMessages) {
      // 构建完整的原始消息格式
      final originalMessage = {
        'device_sn': targetDeviceSn,
        'message_id': message.id,
        'department_id': message.department.isNotEmpty ? message.department : '', 
        'department_name': message.department,
        'is_public': false,
        'message': message.content,
        'message_type': message.messageType,
        'sent_time': message.createTime,
        'user_id': '',
        'user_name': '',
      };
      
      final success = await _apiService.markMessageAsRead(
        targetDeviceSn,
        messageId: message.id,
        receivedTime: DateTime.now(),
        originalMessage: originalMessage,
      );
      
      if (success) {
        successCount++;
        // 更新本地消息状态
        final index = _messages.indexWhere((m) => m.id == message.id);
        if (index != -1) {
          setState(() {
            final updatedMessage = message_model.Message(
              id: message.id,
              title: message.title,
              content: message.content,
              createTime: message.createTime,
              department: message.department,
              messageStatus: '2', // 更新为已读状态
              messageType: message.messageType,
              imageUrl: message.imageUrl,
            );
            _messages[index] = updatedMessage;
          });
        }
      }
    }
    
    setState(() => _isProcessing = false);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('成功标记 $successCount/${unreadMessages.length} 条消息为已读')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final unreadMessages = _messages.where((msg) => msg.messageStatus == '1').toList();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Text('消息详情'),
            if (unreadMessages.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(left: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.teal,
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
        actions: [
          if (unreadMessages.isNotEmpty)
            _isProcessing
              ? Center(
                  child: Container(
                    width: 24,
                    height: 24,
                    margin: const EdgeInsets.only(right: 16),
                    child: const CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  ),
                )
              : TextButton.icon(
                  onPressed: () => _markAllAsRead(context),
                  icon: const Icon(Icons.done_all, color: Colors.white),
                  label: const Text('全部已读', style: TextStyle(color: Colors.white)),
                ),
        ],
      ),
      body: _messages.isEmpty 
          ? _buildEmptyState(context)
          : ListView.builder(
              padding: const EdgeInsets.all(16.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageItem(context, message);
              },
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.mark_email_read_rounded,
            size: 64,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            "暂无消息",
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "您当前没有任何消息通知",
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageItem(BuildContext context, message_model.Message message) {
    final theme = Theme.of(context);
    final bool isUnread = message.messageStatus == '1';
    final color = _getMessageTypeColor(message.messageType);
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isUnread ? color.withOpacity(0.3) : Colors.transparent,
          width: isUnread ? 1.5 : 0,
        ),
      ),
      elevation: isUnread ? 2 : 1,
      child: InkWell(
        onTap: () {
          // 打开消息详情
          _openMessageDetail(context, message);
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildMessageIcon(message.messageType, isUnread),
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
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                AppText.translateMessageType(message.messageType),
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: color,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                            if (isUnread)
                              Container(
                                margin: const EdgeInsets.only(left: 6),
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: Colors.teal.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  "未读",
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: Colors.teal,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          message.title,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: isUnread ? FontWeight.bold : FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          message.content,
                          style: theme.textTheme.bodyMedium,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Divider(height: 1),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    message.createTime,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  Row(
                    children: [
                      const Icon(Icons.business, size: 14, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        message.department,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
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

  // 构建消息图标
  Widget _buildMessageIcon(String type, bool isUnread) {
    final color = _getMessageTypeColor(type);
    
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(
            _getMessageTypeIcon(type),
            color: color,
            size: 22,
          ),
        ),
        if (isUnread)
          Positioned(
            top: -2,
            right: -2,
            child: Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 1),
              ),
            ),
          ),
      ],
    );
  }

  void _openMessageDetail(BuildContext context, message_model.Message message) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => MessageDetailPage(
          message: message,
          onMarkAsRead: (id) {
            // 构建完整的原始消息格式
            final originalMessage = {
              'device_sn': deviceSn,
              'message_id': message.id,
              'department_id': '', // 尽可能填写有效值
              'department_name': message.department,
              'is_public': false,
              'message': message.content,
              'message_type': message.messageType,
              'sent_time': message.createTime,
              'user_id': '',
              'user_name': '',
            };
            
            // 调用API标记消息已读
            _apiService.markMessageAsRead(
              deviceSn,
              messageId: message.id,
              receivedTime: DateTime.now(),
              originalMessage: originalMessage,
            );
            
            // 更新本地消息状态
            final index = _messages.indexWhere((m) => m.id == id);
            if (index != -1) {
              setState(() {
                final updatedMessage = message_model.Message(
                  id: message.id,
                  title: message.title,
                  content: message.content,
                  createTime: message.createTime,
                  department: message.department,
                  messageStatus: '2', // 更新为已读状态
                  messageType: message.messageType,
                  imageUrl: message.imageUrl,
                );
                _messages[index] = updatedMessage;
              });
            }
          },
          onDelete: (id) {
            // 删除消息
            setState(() {
              _messages.removeWhere((m) => m.id == id);
            });
            Navigator.pop(context); // 返回列表页
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('消息已删除')),
            );
          },
        ),
      ),
    );
  }

  IconData _getMessageTypeIcon(String messageType) {
    switch (messageType.toLowerCase()) {
      case 'job':
        return Icons.work_rounded;
      case 'task':
        return Icons.assignment_rounded;
      case 'announcement':
        return Icons.campaign_rounded;
      case 'notification':
        return Icons.notifications_rounded;
      default:
        return Icons.message_rounded;
    }
  }

  Color _getMessageTypeColor(String messageType) {
    switch (messageType.toLowerCase()) {
      case 'job':
        return Colors.teal;
      case 'task':
        return Colors.blue;
      case 'announcement':
        return Colors.purple;
      case 'notification':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }
} 