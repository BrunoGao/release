import 'package:flutter/material.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;

class EnterpriseAppBar extends StatefulWidget implements PreferredSizeWidget {
  final String title;
  final login.LoginData loginData;
  final VoidCallback? onMenuPressed;
  final VoidCallback? onNotificationPressed;
  final VoidCallback? onAdminPressed;
  final VoidCallback? onSettingsPressed;
  final List<Widget>? customActions;
  final bool showBackButton;
  final int? notificationCount;
  final bool showBreadcrumb;
  final List<String>? breadcrumbItems;

  const EnterpriseAppBar({
    super.key,
    required this.title,
    required this.loginData,
    this.onMenuPressed,
    this.onNotificationPressed,
    this.onAdminPressed,
    this.onSettingsPressed,
    this.customActions,
    this.showBackButton = false,
    this.notificationCount,
    this.showBreadcrumb = false,
    this.breadcrumbItems,
  });

  @override
  Size get preferredSize => Size.fromHeight(showBreadcrumb ? 120.0 : 80.0);

  @override
  State<EnterpriseAppBar> createState() => _EnterpriseAppBarState();
}

class _EnterpriseAppBarState extends State<EnterpriseAppBar>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, -0.5),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOutQuart),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return SlideTransition(
          position: _slideAnimation,
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: _buildAppBar(context, theme, isDark),
          ),
        );
      },
    );
  }

  Widget _buildAppBar(BuildContext context, ThemeData theme, bool isDark) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? [
                  const Color(0xFF1E1E1E),
                  const Color(0xFF2D2D2D),
                ]
              : [
                  Colors.white,
                  Colors.grey[50]!,
                ],
        ),
        boxShadow: [
          BoxShadow(
            color: theme.shadowColor.withOpacity(0.1),
            offset: const Offset(0, 2),
            blurRadius: 8,
            spreadRadius: 0,
          ),
        ],
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildMainAppBar(context, theme, isDark),
            if (widget.showBreadcrumb) _buildBreadcrumb(context, theme, isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildMainAppBar(BuildContext context, ThemeData theme, bool isDark) {
    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          // 左侧：返回按钮或菜单按钮
          if (widget.showBackButton)
            _buildIconButton(
              icon: Icons.arrow_back_ios_new_rounded,
              onPressed: () => Navigator.of(context).pop(),
              tooltip: '返回',
              theme: theme,
            )
          else
            _buildIconButton(
              icon: Icons.menu_rounded,
              onPressed: widget.onMenuPressed,
              tooltip: '菜单',
              theme: theme,
            ),
          
          const SizedBox(width: 16),
          
          // 中间：标题和企业信息
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  widget.title,
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 20,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (widget.loginData.companyName?.isNotEmpty == true)
                  Text(
                    widget.loginData.companyName!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: isDark ? Colors.grey[400] : Colors.grey[600],
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          
          // 右侧：功能按钮组
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // 通知按钮
              _buildNotificationButton(theme),
              
              const SizedBox(width: 8),
              
              // 管理员按钮（如果是管理员）
              if (widget.loginData.isAdmin) ...[
                _buildIconButton(
                  icon: Icons.admin_panel_settings_rounded,
                  onPressed: widget.onAdminPressed,
                  tooltip: '管理后台',
                  theme: theme,
                  color: Colors.orange[700],
                ),
                const SizedBox(width: 8),
              ],
              
              // 设置按钮
              _buildIconButton(
                icon: Icons.settings_rounded,
                onPressed: widget.onSettingsPressed,
                tooltip: '设置',
                theme: theme,
              ),
              
              // 自定义动作按钮
              if (widget.customActions != null) ...widget.customActions!,
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBreadcrumb(BuildContext context, ThemeData theme, bool isDark) {
    if (widget.breadcrumbItems == null || widget.breadcrumbItems!.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(
            Icons.location_on_outlined,
            size: 16,
            color: isDark ? Colors.grey[400] : Colors.grey[600],
          ),
          const SizedBox(width: 8),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _buildBreadcrumbItems(theme, isDark),
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildBreadcrumbItems(ThemeData theme, bool isDark) {
    final items = <Widget>[];
    
    for (int i = 0; i < widget.breadcrumbItems!.length; i++) {
      final isLast = i == widget.breadcrumbItems!.length - 1;
      
      items.add(
        Text(
          widget.breadcrumbItems![i],
          style: theme.textTheme.bodySmall?.copyWith(
            color: isLast 
                ? AppTheme.primaryColor
                : (isDark ? Colors.grey[400] : Colors.grey[600]),
            fontWeight: isLast ? FontWeight.w600 : FontWeight.normal,
            fontSize: 12,
          ),
        ),
      );
      
      if (!isLast) {
        items.addAll([
          const SizedBox(width: 8),
          Icon(
            Icons.chevron_right_rounded,
            size: 14,
            color: isDark ? Colors.grey[500] : Colors.grey[500],
          ),
          const SizedBox(width: 8),
        ]);
      }
    }
    
    return items;
  }

  Widget _buildIconButton({
    required IconData icon,
    required VoidCallback? onPressed,
    required String tooltip,
    required ThemeData theme,
    Color? color,
  }) {
    final isDark = theme.brightness == Brightness.dark;
    
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.transparent,
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onPressed,
          child: Container(
            padding: const EdgeInsets.all(8),
            child: Icon(
              icon,
              size: 24,
              color: color ?? (isDark ? Colors.white70 : Colors.grey[700]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNotificationButton(ThemeData theme) {
    final isDark = theme.brightness == Brightness.dark;
    final hasNotifications = widget.notificationCount != null && widget.notificationCount! > 0;
    
    return Stack(
      children: [
        _buildIconButton(
          icon: Icons.notifications_outlined,
          onPressed: widget.onNotificationPressed,
          tooltip: '通知',
          theme: theme,
        ),
        if (hasNotifications)
          Positioned(
            right: 4,
            top: 4,
            child: Container(
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: theme.scaffoldBackgroundColor,
                  width: 1,
                ),
              ),
              constraints: const BoxConstraints(
                minWidth: 18,
                minHeight: 18,
              ),
              child: Text(
                widget.notificationCount! > 99 
                    ? '99+' 
                    : widget.notificationCount.toString(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
      ],
    );
  }
}

// 企业级搜索栏组件
class EnterpriseSearchBar extends StatefulWidget {
  final String? hintText;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onFilterPressed;
  final bool showFilter;
  final TextEditingController? controller;

  const EnterpriseSearchBar({
    super.key,
    this.hintText,
    this.onChanged,
    this.onSubmitted,
    this.onFilterPressed,
    this.showFilter = false,
    this.controller,
  });

  @override
  State<EnterpriseSearchBar> createState() => _EnterpriseSearchBarState();
}

class _EnterpriseSearchBarState extends State<EnterpriseSearchBar> {
  late TextEditingController _controller;
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[800] : Colors.grey[100],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: _focusNode.hasFocus 
              ? AppTheme.primaryColor.withOpacity(0.5)
              : Colors.transparent,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              focusNode: _focusNode,
              style: TextStyle(
                color: isDark ? Colors.white : Colors.black87,
                fontSize: 16,
              ),
              decoration: InputDecoration(
                hintText: widget.hintText ?? '搜索...',
                hintStyle: TextStyle(
                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                ),
                prefixIcon: Icon(
                  Icons.search_rounded,
                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                ),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
              onChanged: widget.onChanged,
              onSubmitted: widget.onSubmitted,
            ),
          ),
          if (widget.showFilter)
            Container(
              margin: const EdgeInsets.only(right: 8),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: IconButton(
                icon: Icon(
                  Icons.tune_rounded,
                  color: AppTheme.primaryColor,
                ),
                onPressed: widget.onFilterPressed,
                tooltip: '筛选',
              ),
            ),
        ],
      ),
    );
  }
}