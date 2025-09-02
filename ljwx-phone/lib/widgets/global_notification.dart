import 'dart:async';
import 'package:flutter/material.dart';
import '../utils/global_events.dart';
import '../theme/app_theme.dart';

class GlobalNotification extends StatelessWidget {
  final Widget child;
  
  const GlobalNotification({Key? key, required this.child}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          child: _NotificationListener(),
        ),
      ],
    );
  }
}

class _NotificationListener extends StatefulWidget {
  @override
  _NotificationListenerState createState() => _NotificationListenerState();
}

class _NotificationListenerState extends State<_NotificationListener> with SingleTickerProviderStateMixin {
  EventMessage? _currentMessage;
  late AnimationController _animController;
  late Animation<Offset> _offsetAnimation;
  Timer? _dismissTimer;
  
  @override
  void initState() {
    super.initState();
    
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    
    _offsetAnimation = Tween<Offset>(
      begin: const Offset(0.0, -1.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animController,
      curve: Curves.easeOut,
    ));
    
    // 监听全局事件
    GlobalEvents.i.eventStream.listen(_handleEventMessage);
  }
  
  void _handleEventMessage(EventMessage message) {
    // 取消已有定时器
    _dismissTimer?.cancel();
    
    setState(() {
      _currentMessage = message;
    });
    
    // 显示通知
    _animController.forward(from: 0.0);
    
    // 设置自动关闭定时器
    _dismissTimer = Timer(message.duration, () {
      _animController.reverse().then((_) {
        setState(() {
          _currentMessage = null;
        });
      });
    });
  }
  
  @override
  void dispose() {
    _dismissTimer?.cancel();
    _animController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    if (_currentMessage == null) {
      return const SizedBox.shrink();
    }
    
    Color backgroundColor;
    IconData iconData;
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    
    switch (_currentMessage!.type) {
      case EventType.info:
        backgroundColor = isDarkMode 
            ? AppTheme.primaryColor.withOpacity(0.9) 
            : AppTheme.primaryColor.withOpacity(0.95);
        iconData = Icons.info_outline_rounded;
        break;
      case EventType.warning:
        backgroundColor = isDarkMode 
            ? AppTheme.warningColor.withOpacity(0.9) 
            : AppTheme.warningColor.withOpacity(0.95);
        iconData = Icons.warning_amber_rounded;
        break;
      case EventType.error:
        backgroundColor = isDarkMode 
            ? AppTheme.errorColor.withOpacity(0.9) 
            : AppTheme.errorColor.withOpacity(0.95);
        iconData = Icons.error_outline_rounded;
        break;
      case EventType.success:
        backgroundColor = isDarkMode 
            ? AppTheme.successColor.withOpacity(0.9) 
            : AppTheme.successColor.withOpacity(0.95);
        iconData = Icons.check_circle_outline_rounded;
        break;
    }
    
    return SlideTransition(
      position: _offsetAnimation,
      child: Material(
        elevation: 4,
        child: Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: backgroundColor,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(iconData, color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      _currentMessage!.message,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  GestureDetector(
                    onTap: () {
                      _animController.reverse().then((_) {
                        setState(() {
                          _currentMessage = null;
                        });
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.close_rounded, 
                        color: Colors.white, 
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
} 