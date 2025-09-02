import 'package:flutter/foundation.dart';
import 'package:ljwx_health_new/models/login_response.dart';

class DepartmentMessageStats {
  final int totalMessages;
  final int personalMessages;
  final int publicMessages;
  final Map<String, int> messageTypeCount;
  final Map<String, int> messageStatusCount;

  DepartmentMessageStats({
    required this.totalMessages,
    required this.personalMessages,
    required this.publicMessages,
    required this.messageTypeCount,
    required this.messageStatusCount,
  });

  factory DepartmentMessageStats.fromJson(Map<String, dynamic> json) {
    return DepartmentMessageStats(
      totalMessages: json['totalMessages'] ?? 0,
      personalMessages: json['personalMessages'] ?? 0,
      publicMessages: json['publicMessages'] ?? 0,
      messageTypeCount: Map<String, int>.from(json['messageTypeCount'] ?? {}),
      messageStatusCount: Map<String, int>.from(json['messageStatusCount'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'totalMessages': totalMessages,
      'personalMessages': personalMessages,
      'publicMessages': publicMessages,
      'messageTypeCount': messageTypeCount,
      'messageStatusCount': messageStatusCount,
    };
  }
}

class Message {
  final String id;
  final String title;
  final String content;
  final String createTime;
  final String department;
  final String messageStatus; // 1:待处理, 2:已响应
  final String messageType; // job:作业指引, task:任务管理, announcement:公告, notification:通知
  final String? imageUrl;

  Message({
    required this.id,
    required this.title,
    required this.content,
    required this.createTime,
    required this.department,
    required this.messageStatus,
    required this.messageType,
    this.imageUrl,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['message_id'] ?? json['id'] ?? '',
      title: json['message_type'] != null 
          ? _getMessageTypeTitle(json['message_type'].toString()) 
          : json['title'] ?? '',
      content: json['message'] ?? json['content'] ?? '',
      createTime: json['sent_time'] ?? json['create_time'] ?? '',
      department: json['department_name'] ?? json['department'] ?? '',
      messageStatus: json['message_status'] ?? '1',
      messageType: json['message_type'] ?? '',
      imageUrl: json['image_url'],
    );
  }

  // 根据消息类型获取标题
  static String _getMessageTypeTitle(String type) {
    switch (type) {
      case 'job':
        return '作业指引';
      case 'task':
        return '任务管理';
      case 'announcement':
        return '系统公告';
      case 'notification':
        return '通知';
      default:
        return '消息';
    }
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'content': content,
    'create_time': createTime,
    'department': department,
    'message_status': messageStatus,
    'message_type': messageType,
    'image_url': imageUrl,
  };
}

class MessageInfo {
  final Map<String, int> departmentMessageCount;
  final List<String> departments;
  final Map<String, int> messageStatusCount;
  final Map<String, int> messageTypeCount;
  final List<Message> messages;

  MessageInfo({
    required this.departmentMessageCount,
    required this.departments,
    required this.messageStatusCount,
    required this.messageTypeCount,
    required this.messages,
  });

  factory MessageInfo.fromJson(Map<String, dynamic> json) {
    return MessageInfo(
      departmentMessageCount: Map<String, int>.from(json['departmentMessageCount'] ?? {}),
      departments: List<String>.from(json['departments'] ?? []),
      messageStatusCount: Map<String, int>.from(json['messageStatusCount'] ?? {}),
      messageTypeCount: Map<String, int>.from(json['messageTypeCount'] ?? {}),
      messages: (json['messages'] as List<dynamic>? ?? [])
          .map((e) => Message.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'departmentMessageCount': departmentMessageCount,
    'departments': departments,
    'messageStatusCount': messageStatusCount,
    'messageTypeCount': messageTypeCount,
    'messages': messages.map((e) => e.toJson()).toList(),
  };

  factory MessageInfo.empty() {
    return MessageInfo(
      departmentMessageCount: {},
      departments: [],
      messageStatusCount: {},
      messageTypeCount: {},
      messages: [],
    );
  }
} 