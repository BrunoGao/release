import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

class EnterpriseBottomNavigationBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final bool isAdmin;

  const EnterpriseBottomNavigationBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
    this.isAdmin = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // 根据用户类型定义导航项
    final List<NavigationItem> items = isAdmin 
        ? _adminNavigationItems 
        : _userNavigationItems;

    return Container(
      decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor,
        boxShadow: [
          BoxShadow(
            color: theme.shadowColor.withOpacity(0.1),
            offset: const Offset(0, -2),
            blurRadius: 8,
          ),
        ],
      ),
      child: SafeArea(
        child: Container(
          height: 65,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: items.asMap().entries.map((entry) {
              final index = entry.key;
              final item = entry.value;
              final isSelected = index == currentIndex;
              
              return Expanded(
                child: GestureDetector(
                  onTap: () => onTap(index),
                  behavior: HitTestBehavior.opaque,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    curve: Curves.easeInOut,
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    decoration: BoxDecoration(
                      color: isSelected 
                          ? AppTheme.primaryColor.withOpacity(0.1)
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.all(2),
                          child: Icon(
                            isSelected ? item.activeIcon : item.icon,
                            color: isSelected 
                                ? AppTheme.primaryColor 
                                : (isDark ? Colors.grey[400] : Colors.grey[600]),
                            size: isSelected ? 24 : 22,
                          ),
                        ),
                        const SizedBox(height: 2),
                        AnimatedDefaultTextStyle(
                          duration: const Duration(milliseconds: 200),
                          style: TextStyle(
                            color: isSelected 
                                ? AppTheme.primaryColor 
                                : (isDark ? Colors.grey[400] : Colors.grey[600]),
                            fontSize: isSelected ? 11 : 10,
                            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                          ),
                          child: Text(
                            item.label,
                            textAlign: TextAlign.center,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ),
    );
  }

  // 普通用户导航项
  static const List<NavigationItem> _userNavigationItems = [
    NavigationItem(
      label: '首页',
      icon: Icons.home_outlined,
      activeIcon: Icons.home_rounded,
      route: '/home',
    ),
    NavigationItem(
      label: '健康',
      icon: Icons.favorite_outline_rounded,
      activeIcon: Icons.favorite_rounded,
      route: '/health',
    ),
    NavigationItem(
      label: '设备',
      icon: Icons.watch_outlined,
      activeIcon: Icons.watch_rounded,
      route: '/device',
    ),
    NavigationItem(
      label: '告警',
      icon: Icons.notification_important_outlined,
      activeIcon: Icons.notification_important_rounded,
      route: '/alerts',
    ),
    NavigationItem(
      label: '消息',
      icon: Icons.message_outlined,
      activeIcon: Icons.message_rounded,
      route: '/messages',
    ),
  ];

  // 管理员用户导航项
  static const List<NavigationItem> _adminNavigationItems = [
    NavigationItem(
      label: '总览',
      icon: Icons.dashboard_outlined,
      activeIcon: Icons.dashboard_rounded,
      route: '/admin/overview',
    ),
    NavigationItem(
      label: '监控',
      icon: Icons.monitor_heart_outlined,
      activeIcon: Icons.monitor_heart_rounded,
      route: '/admin/monitor',
    ),
    NavigationItem(
      label: '管理',
      icon: Icons.admin_panel_settings_outlined,
      activeIcon: Icons.admin_panel_settings_rounded,
      route: '/admin/management',
    ),
    NavigationItem(
      label: '告警',
      icon: Icons.warning_amber_outlined,
      activeIcon: Icons.warning_amber_rounded,
      route: '/admin/alerts',
    ),
    NavigationItem(
      label: '设置',
      icon: Icons.settings_outlined,
      activeIcon: Icons.settings_rounded,
      route: '/admin/settings',
    ),
  ];
}

class NavigationItem {
  final String label;
  final IconData icon;
  final IconData activeIcon;
  final String route;

  const NavigationItem({
    required this.label,
    required this.icon,
    required this.activeIcon,
    required this.route,
  });
}