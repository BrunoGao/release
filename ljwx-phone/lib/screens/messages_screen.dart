import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/models/message_model.dart' as message;
import 'package:ljwx_health_new/models/personal_data.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'dart:async';

class MessagesScreen extends StatefulWidget {
  final login.LoginData loginData;

  const MessagesScreen({
    super.key,
    required this.loginData,
  });

  @override
  _MessagesScreenState createState() => _MessagesScreenState();
}

class _MessagesScreenState extends State<MessagesScreen> {
  Timer? _timer;
  PersonalData? _personalData;
  final _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _fetchPersonalInfo();
    _timer = Timer.periodic(Duration(seconds: 5), (_) => _fetchPersonalInfo());
  }

  Future<void> _fetchPersonalInfo() async {
    try {
      final response = await _apiService.getPersonalInfo(widget.loginData.phone);
      setState(() {
        _personalData = response;
      });
    } catch (e) {
      print('Error fetching personal info: $e');
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_personalData == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final theme = Theme.of(context);
    final messageInfo = _personalData!.messageInfo;

    return Scaffold(
      appBar: AppBar(
        title: const Text('消息中心'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () {
              // TODO: Implement message filtering
            },
          ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: _buildMessageStats(messageInfo, theme),
            ).animate().fadeIn().slideX(),
          ),
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final message = messageInfo.messages[index];
                return _buildMessageCard(message, theme)
                    .animate()
                    .fadeIn(delay: (50 * index).ms)
                    .slideX();
              },
              childCount: messageInfo.messages.length,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageStats(message.MessageInfo messageInfo, ThemeData theme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem('总消息数', messageInfo.totalMessages.toString()),
            _buildStatItem('未读消息', messageInfo.messageStatusCount['unread']?.toString() ?? '0'),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            color: Colors.grey,
          ),
        ),
      ],
    );
  }

  Widget _buildMessageCard(message.Message message, ThemeData theme) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: ListTile(
        leading: _buildMessageTypeIcon(message.type),
        title: Text(message.title),
        subtitle: Text(message.content),
        trailing: Text(message.timestamp),
        onTap: () {
          showDialog(
            context: context,
            builder: (context) => Dialog(
              child: SingleChildScrollView(
                child: _buildMessageDetails(message, theme),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildMessageTypeIcon(String type) {
    IconData iconData;
    Color color;

    switch (type.toLowerCase()) {
      case 'system':
        iconData = Icons.computer;
        color = Colors.blue;
        break;
      case 'device':
        iconData = Icons.watch;
        color = Colors.green;
        break;
      case 'health':
        iconData = Icons.favorite;
        color = Colors.red;
        break;
      default:
        iconData = Icons.message;
        color = Colors.grey;
    }

    return Icon(iconData, color: color);
  }

  Widget _buildMessageDetails(message.Message message, ThemeData theme) {
    // Implementation of _buildMessageDetails method
    return Container(); // Placeholder return, actual implementation needed
  }
} 