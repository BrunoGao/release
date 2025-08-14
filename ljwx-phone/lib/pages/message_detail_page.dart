import 'package:flutter/material.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/models/message_model.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import '../global.dart';

class MessageDetailPage extends StatefulWidget {
  final Message message;
  final Function(String messageId) onMarkAsRead;
  final Function(String messageId) onDelete;

  const MessageDetailPage({
    super.key,
    required this.message,
    required this.onMarkAsRead,
    required this.onDelete,
  });

  @override
  State<MessageDetailPage> createState() => _MessageDetailPageState();
}

class _MessageDetailPageState extends State<MessageDetailPage> {
  final ApiService _apiService = ApiService();
  bool _isProcessing = false;

  // 标记消息为已读
  Future<void> _handleMarkAsRead() async {
    setState(() => _isProcessing = true);
    
    // 获取有效的设备序列号
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
    
    // 构建原始消息格式
    final originalMessage = {
      'device_sn': targetDeviceSn,
      'message_id': widget.message.id,
      'department_id': widget.message.department.isNotEmpty ? widget.message.department : '', 
      'department_name': widget.message.department,
      'is_public': false,
      'message': widget.message.content,
      'message_type': widget.message.messageType,
      'sent_time': widget.message.createTime,
      'user_id': '',
      'user_name': '',
    };
    
    // 调用API标记为已读，设置received_time为当前时间
    final success = await _apiService.markMessageAsRead(
      targetDeviceSn,
      receivedTime: DateTime.now(),
      messageId: widget.message.id,
      originalMessage: originalMessage,
    );
    
    setState(() => _isProcessing = false);
    
    if (success) {
      widget.onMarkAsRead(widget.message.id);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('消息已标记为已读')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('标记消息已读失败，请稍后重试')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.messages),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 消息标题
            Text(
              widget.message.title,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            
            const SizedBox(height: 8),
            
            // 消息元数据
            Row(
              children: [
                _buildChip(
                  context,
                  AppText.translateMessageType(widget.message.messageType),
                  _getTypeColor(widget.message.messageType),
                ),
                const SizedBox(width: 8),
                _buildChip(
                  context,
                  AppText.translateMessageStatus(widget.message.messageStatus),
                  _getStatusColor(widget.message.messageStatus),
                ),
              ],
            ),
            
            // 时间和部门信息
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "创建时间: ${widget.message.createTime}",
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    "部门: ${widget.message.department}",
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
            
            const Divider(height: 24),
            
            // 消息内容
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: widget.message.messageStatus == '1' 
                      ? AppTheme.primaryColor.withOpacity(0.3) 
                      : Colors.grey.withOpacity(0.2),
                  width: widget.message.messageStatus == '1' ? 2 : 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        "消息内容",
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                      if (widget.message.messageStatus == '1')
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.mark_email_unread,
                                size: 12,
                                color: AppTheme.primaryColor,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                "未读",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: AppTheme.primaryColor,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  widget.message.content.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 20),
                            child: Column(
                              children: [
                                Icon(
                                  Icons.description_outlined,
                                  size: 48,
                                  color: Colors.grey[400],
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  "暂无消息内容",
                                  style: theme.textTheme.bodyLarge?.copyWith(
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                      : Text(
                          widget.message.content,
                          style: theme.textTheme.bodyLarge,
                        ),
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            
            // 图片（如果有）
            if (widget.message.imageUrl != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  widget.message.imageUrl!,
                  fit: BoxFit.cover,
                  width: double.infinity,
                  height: 200,
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      width: double.infinity,
                      height: 200,
                      color: Colors.grey[200],
                      child: const Center(
                        child: Icon(
                          Icons.broken_image,
                          color: Colors.grey,
                          size: 48,
                        ),
                      ),
                    );
                  },
                ),
              ),
            
            const SizedBox(height: 32),
            
            // 操作按钮
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // 已读确认按钮
                if (widget.message.messageStatus == '1')
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isProcessing 
                          ? null 
                          : () {
                              _showConfirmationDialog(
                                context,
                                "确认标记为已读？",
                                _handleMarkAsRead,
                              );
                            },
                      icon: _isProcessing 
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            )
                          : const Icon(Icons.check_circle_outline),
                      label: Text(_isProcessing ? "处理中..." : AppText.markAsRead),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        disabledBackgroundColor: Colors.green.withOpacity(0.6),
                      ),
                    ),
                  ),
                
                if (widget.message.messageStatus == '1')
                  const SizedBox(width: 16),
                
                // 删除按钮
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      _showConfirmationDialog(
                        context,
                        "确认删除这条消息？",
                        () => widget.onDelete(widget.message.id),
                      );
                    },
                    icon: const Icon(Icons.delete_outline),
                    label: const Text(AppText.delete),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  // 构建标签
  Widget _buildChip(BuildContext context, String label, Color backgroundColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: backgroundColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: backgroundColor.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: backgroundColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
  
  // 根据消息类型获取颜色
  Color _getTypeColor(String type) {
    switch (type) {
      case 'job':
        return Colors.blue;
      case 'task':
        return Colors.purple;
      case 'announcement':
        return Colors.teal;
      case 'notification':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }
  
  // 根据消息状态获取颜色
  Color _getStatusColor(String status) {
    switch (status) {
      case '1':
        return Colors.orange;
      case '2':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
  
  // 显示确认对话框
  void _showConfirmationDialog(
    BuildContext context,
    String message,
    VoidCallback onConfirm,
  ) {
    showDialog(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: Text(AppText.confirm),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
              },
              child: Text(AppText.cancel),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                onConfirm();
              },
              child: Text(AppText.confirm),
              style: TextButton.styleFrom(
                foregroundColor: Colors.red,
              ),
            ),
          ],
        );
      },
    );
  }
} 