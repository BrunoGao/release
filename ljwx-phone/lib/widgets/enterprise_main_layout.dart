import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/widgets/enterprise_app_bar.dart';
import 'package:ljwx_health_new/widgets/bottom_navigation_bar.dart';
import 'package:ljwx_health_new/widgets/enterprise_search_bar.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/theme/app_theme.dart';

class EnterpriseMainLayout extends StatefulWidget {
  final Widget child;
  final String title;
  final login.LoginData loginData;
  final String currentRoute;
  final int? notificationCount;
  final bool showBreadcrumb;
  final List<String>? breadcrumbItems;
  final Widget? floatingActionButton;
  final FloatingActionButtonLocation? floatingActionButtonLocation;
  final bool showBottomNavigation;
  final bool showSearchBar;
  final String? searchHint;
  final ValueChanged<String>? onSearchChanged;

  const EnterpriseMainLayout({
    super.key,
    required this.child,
    required this.title,
    required this.loginData,
    required this.currentRoute,
    this.notificationCount,
    this.showBreadcrumb = false,
    this.breadcrumbItems,
    this.floatingActionButton,
    this.floatingActionButtonLocation,
    this.showBottomNavigation = true,
    this.showSearchBar = false,
    this.searchHint,
    this.onSearchChanged,
  });

  @override
  State<EnterpriseMainLayout> createState() => _EnterpriseMainLayoutState();
}

class _EnterpriseMainLayoutState extends State<EnterpriseMainLayout>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  int _currentNavIndex = 0;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _updateCurrentIndex();
    _animationController.forward();
  }

  @override
  void didUpdateWidget(EnterpriseMainLayout oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentRoute != widget.currentRoute) {
      _updateCurrentIndex();
    }
  }

  void _updateCurrentIndex() {
    _currentNavIndex = _getIndexFromRoute(widget.currentRoute);
  }

  int _getIndexFromRoute(String route) {
    if (widget.loginData.isAdmin) {
      // 管理员导航映射
      switch (route) {
        case '/admin':
        case '/admin/overview':
          return 0;
        case '/admin/monitor':
          return 1;
        case '/admin/management':
          return 2;
        case '/admin/alerts':
          return 3;
        case '/admin/settings':
          return 4;
        default:
          return 0;
      }
    } else {
      // 普通用户导航映射
      switch (route) {
        case '/home':
          return 0;
        case '/health':
        case '/health/analysis':
          return 1;
        case '/device':
        case '/devices':
          return 2;
        case '/alerts':
          return 3;
        case '/messages':
          return 4;
        default:
          return 0;
      }
    }
  }

  void _onNavigation(int index) {
    if (index == _currentNavIndex) return;

    setState(() {
      _currentNavIndex = index;
    });

    String route;
    if (widget.loginData.isAdmin) {
      // 管理员路由
      switch (index) {
        case 0:
          route = '/admin/overview';
          break;
        case 1:
          route = '/admin/monitor';
          break;
        case 2:
          route = '/admin/management';
          break;
        case 3:
          route = '/admin/alerts';
          break;
        case 4:
          route = '/admin/settings';
          break;
        default:
          route = '/admin';
      }
    } else {
      // 普通用户路由
      switch (index) {
        case 0:
          route = '/home';
          break;
        case 1:
          route = '/health';
          break;
        case 2:
          route = '/device';
          break;
        case 3:
          route = '/alerts';
          break;
        case 4:
          route = '/messages';
          break;
        default:
          route = '/home';
      }
    }

    context.go(route, extra: widget.loginData);
  }

  void _onMenuPressed() {
    // 显示侧边菜单
    Scaffold.of(context).openDrawer();
  }

  void _onNotificationPressed() {
    // 跳转到通知页面
    context.push('/notifications', extra: widget.loginData);
  }

  void _onAdminPressed() {
    // 跳转到管理后台
    context.push('/admin-webview', extra: widget.loginData);
  }

  void _onSettingsPressed() {
    // 跳转到设置页面
    context.push('/settings', extra: widget.loginData);
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: EnterpriseAppBar(
        title: widget.title,
        loginData: widget.loginData,
        onMenuPressed: _onMenuPressed,
        onNotificationPressed: _onNotificationPressed,
        onAdminPressed: _onAdminPressed,
        onSettingsPressed: _onSettingsPressed,
        notificationCount: widget.notificationCount,
        showBreadcrumb: widget.showBreadcrumb,
        breadcrumbItems: widget.breadcrumbItems,
      ),
      drawer: _buildSideDrawer(),
      body: Column(
        children: [
          // 搜索栏（可选）
          if (widget.showSearchBar)
            EnterpriseSearchBar(
              hintText: widget.searchHint,
              onChanged: widget.onSearchChanged,
              showFilter: true,
              onFilterPressed: () {
                _showFilterDialog();
              },
            ),
          
          // 主要内容区域
          Expanded(
            child: AnimatedBuilder(
              animation: _animationController,
              builder: (context, child) {
                return FadeTransition(
                  opacity: _animationController,
                  child: widget.child,
                );
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: widget.showBottomNavigation
          ? EnterpriseBottomNavigationBar(
              currentIndex: _currentNavIndex,
              onTap: _onNavigation,
              isAdmin: widget.loginData.isAdmin,
            )
          : null,
      floatingActionButton: widget.floatingActionButton,
      floatingActionButtonLocation: widget.floatingActionButtonLocation,
    );
  }

  Widget _buildSideDrawer() {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Drawer(
      backgroundColor: theme.scaffoldBackgroundColor,
      child: Column(
        children: [
          // 用户信息头部
          _buildDrawerHeader(theme, isDark),
          
          // 菜单项
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                _buildDrawerSection('主要功能', _getMainMenuItems(), theme),
                const Divider(),
                _buildDrawerSection('系统设置', _getSystemMenuItems(), theme),
                const Divider(),
                if (widget.loginData.isAdmin) ...[
                  _buildDrawerSection('管理功能', _getAdminMenuItems(), theme),
                  const Divider(),
                ],
                _buildDrawerSection('其他', _getOtherMenuItems(), theme),
              ],
            ),
          ),
          
          // 底部信息
          _buildDrawerFooter(theme, isDark),
        ],
      ),
    );
  }

  Widget _buildDrawerHeader(ThemeData theme, bool isDark) {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.primaryColor,
            AppTheme.primaryColor.withOpacity(0.8),
          ],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: Colors.white.withOpacity(0.2),
                child: Text(
                  widget.loginData.userName.isNotEmpty 
                      ? widget.loginData.userName[0].toUpperCase()
                      : 'U',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                widget.loginData.userName,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (widget.loginData.companyName?.isNotEmpty == true)
                Text(
                  widget.loginData.companyName!,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),
              if (widget.loginData.isAdmin)
                Container(
                  margin: const EdgeInsets.only(top: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orange.withOpacity(0.5)),
                  ),
                  child: const Text(
                    '管理员',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDrawerSection(String title, List<DrawerMenuItem> items, ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            title,
            style: theme.textTheme.titleSmall?.copyWith(
              color: AppTheme.primaryColor,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        ...items.map((item) => _buildDrawerItem(item, theme)),
      ],
    );
  }

  Widget _buildDrawerItem(DrawerMenuItem item, ThemeData theme) {
    return ListTile(
      leading: Icon(
        item.icon,
        color: AppTheme.primaryColor,
      ),
      title: Text(
        item.title,
        style: theme.textTheme.bodyMedium,
      ),
      onTap: () {
        Navigator.pop(context);
        if (item.onTap != null) {
          item.onTap!();
        }
      },
      trailing: item.badge != null
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                item.badge!,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                ),
              ),
            )
          : const Icon(Icons.chevron_right),
    );
  }

  Widget _buildDrawerFooter(ThemeData theme, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text(
            '版本 1.0.0',
            style: theme.textTheme.bodySmall?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '灵境万象健康管理系统',
            style: theme.textTheme.bodySmall?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  List<DrawerMenuItem> _getMainMenuItems() {
    return [
      DrawerMenuItem(
        icon: Icons.home_rounded,
        title: '首页',
        onTap: () => context.go('/home', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.favorite_rounded,
        title: '健康数据',
        onTap: () => context.go('/health', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.watch_rounded,
        title: '设备管理',
        onTap: () => context.go('/device', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.notification_important_rounded,
        title: '告警中心',
        onTap: () => context.go('/alerts', extra: widget.loginData),
        badge: widget.notificationCount?.toString(),
      ),
      DrawerMenuItem(
        icon: Icons.message_rounded,
        title: '消息中心',
        onTap: () => context.go('/messages', extra: widget.loginData),
      ),
    ];
  }

  List<DrawerMenuItem> _getSystemMenuItems() {
    return [
      DrawerMenuItem(
        icon: Icons.settings_rounded,
        title: '系统设置',
        onTap: () => context.push('/settings', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.bluetooth_rounded,
        title: '蓝牙设置',
        onTap: () => context.push('/bluetooth', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.info_rounded,
        title: '关于我们',
        onTap: () => _showAboutDialog(),
      ),
    ];
  }

  List<DrawerMenuItem> _getAdminMenuItems() {
    return [
      DrawerMenuItem(
        icon: Icons.dashboard_rounded,
        title: '管理后台',
        onTap: () => context.push('/admin-webview', extra: widget.loginData),
      ),
      DrawerMenuItem(
        icon: Icons.admin_panel_settings_rounded,
        title: '系统管理',
        onTap: () => context.go('/admin', extra: widget.loginData),
      ),
    ];
  }

  List<DrawerMenuItem> _getOtherMenuItems() {
    return [
      DrawerMenuItem(
        icon: Icons.help_rounded,
        title: '帮助中心',
        onTap: () => _showHelpDialog(),
      ),
      DrawerMenuItem(
        icon: Icons.logout_rounded,
        title: '退出登录',
        onTap: () => _showLogoutDialog(),
      ),
    ];
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('筛选条件'),
        content: const Text('筛选功能开发中...'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: '灵境万象健康管理系统',
      applicationVersion: '1.0.0',
      applicationLegalese: '© 2025 灵境万象科技有限公司',
      children: const [
        Text('企业级健康监测管理平台'),
      ],
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('帮助中心'),
        content: const Text('如需帮助，请联系技术支持团队。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('退出登录'),
        content: const Text('确定要退出登录吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.go('/login');
            },
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }
}

class DrawerMenuItem {
  final IconData icon;
  final String title;
  final VoidCallback? onTap;
  final String? badge;

  DrawerMenuItem({
    required this.icon,
    required this.title,
    this.onTap,
    this.badge,
  });
}