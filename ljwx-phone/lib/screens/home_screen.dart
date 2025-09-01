import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/models/user_model.dart' as user;
import 'package:ljwx_health_new/models/device_model.dart' as device;
import 'package:ljwx_health_new/models/personal_data.dart';
import 'package:ljwx_health_new/models/alert_model.dart' as alert;
import 'package:ljwx_health_new/models/message_model.dart' as message;
import 'package:ljwx_health_new/models/health_model.dart' as health;
import 'package:ljwx_health_new/providers/ble_provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/widgets/device_info_card.dart';
import 'dart:async';
import 'package:ljwx_health_new/routes/app_router.dart';
import 'package:ljwx_health_new/screens/alert_details_screen.dart';
import 'package:ljwx_health_new/screens/device_details_screen.dart';
import 'package:ljwx_health_new/screens/health_details_screen.dart';
import 'package:ljwx_health_new/screens/message_details_screen.dart';
import 'package:ljwx_health_new/screens/user_details_screen.dart';
import 'package:ljwx_health_new/widgets/alert_info_card.dart';
import 'package:ljwx_health_new/widgets/health_data_card.dart';
import 'package:ljwx_health_new/widgets/message_info_card.dart';
import 'package:ljwx_health_new/widgets/user_info_card.dart';
import 'package:ljwx_health_new/widgets/info_card.dart';
import 'package:ljwx_health_new/widgets/bluetooth_status_icon.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/bluetooth_service.dart';
import 'package:ljwx_health_new/config/app_config.dart'; // 引入统一配置管理
import 'package:ljwx_health_new/widgets/enterprise_main_layout.dart';
import '../global.dart';

class HomeScreen extends StatefulWidget {
  final login.LoginData loginData;

  const HomeScreen({
    super.key,
    required this.loginData,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  PersonalData? _personalData;
  bool _isLoading = true;
  String? _error;
  final ApiService _apiService = ApiService();
  Timer? _refreshTimer;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _fetchPersonalInfo();
    // 每60秒自动刷新一次数据，并添加防抖
    _refreshTimer = Timer.periodic(const Duration(seconds: 6000000), (timer) {
      _debounceTimer?.cancel();
      _debounceTimer = Timer(const Duration(seconds: 5), () {
        if (mounted) {
      _fetchPersonalInfo();
        }
      });
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _debounceTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchPersonalInfo() async {
    try {
      // 检查应用是否在后台，如果在后台则跳过数据获取
      if (ApiService.isDataFetchingPaused) {
        print('应用在后台，跳过数据获取');
        return;
      }

      print('Starting to fetch personal info...'); // Debug log
      setState(() {
        _isLoading = true;
        _error = null;
      });

      print('Phone number being used: ${widget.loginData.phone}'); // Debug log
      // 直接调用API服务，不使用isolate，因为isolate无法访问ApiService的状态
      final apiService = ApiService();
      final data = await apiService.getPersonalInfo(widget.loginData.phone.toString());
      
      print('Data fetched successfully: ${data.toJson()}'); // Debug log
      if (data.userInfo?.users == null || data.userInfo!.users.isEmpty) {
        print('Warning: No user data available');
      }

      if (mounted) {  // 确保 widget 还在树中
      setState(() {
        _personalData = data;
        _isLoading = false;
      });
        print('State updated, loading: $_isLoading, has data: ${_personalData != null}'); // Debug log
        
        // 打印各个部分的数据状态
        print('User info: ${_personalData?.userInfo?.users.length ?? 0} users');
        print('Device info: ${_personalData?.deviceInfo?.devices?.length ?? 0} devices');
        print('Alert info: ${_personalData?.alertInfo?.alerts.length ?? 0} alerts');
        print('Message info: ${_personalData?.messageInfo?.messages.length ?? 0} messages');
        print('Health data: ${_personalData?.healthData?.healthData?.length ?? 0} records');
      }
    } catch (e, stackTrace) {
      print('Error fetching personal info: $e'); // Debug log
      print('Stack trace: $stackTrace'); // Debug log
      if (mounted) {
      setState(() {
          _error = null; // 不显示错误信息
        _isLoading = false;
          // 保持之前的数据，如果没有则使用空数据
          if (_personalData == null) {
            _personalData = PersonalData(
              alertInfo: alert.AlertInfo.empty(),
              configInfo: null,
              deviceInfo: null,
              healthData: null,
              userInfo: null,
              messageInfo: message.MessageInfo.empty(),
            );
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // 调试管理员功能显示 #管理员调试日志
    print('=== HomeScreen调试信息 ===');
    print('loginData.isAdmin: ${widget.loginData.isAdmin}');
    print('loginData.adminUrl: ${widget.loginData.adminUrl}');
    print('loginData.roles: ${widget.loginData.roles.map((r) => r.roleName).join(', ')}');
    print('应该显示管理员功能: ${widget.loginData.isAdmin}');
    
    if (_isLoading && _personalData == null) {
      return EnterpriseMainLayout(
        title: '首页',
        loginData: widget.loginData,
        currentRoute: '/home',
        showBottomNavigation: false,
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text(AppText.loading),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return EnterpriseMainLayout(
        title: '首页',
        loginData: widget.loginData,
        currentRoute: '/home',
        showBottomNavigation: false,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchPersonalInfo,
                child: Text(AppText.retry),
              ),
            ],
          ),
        ),
      );
    }

    if (_personalData == null) {
      return EnterpriseMainLayout(
        title: '首页',
        loginData: widget.loginData,
        currentRoute: '/home',
        showBottomNavigation: false,
        child: const Center(
          child: Text(AppText.noData),
        ),
      );
    }

    // 计算通知数量
    int notificationCount = 0;
    if (_personalData?.alertInfo?.alerts.isNotEmpty == true) {
      notificationCount += _personalData!.alertInfo!.alerts.length;
    }
    if (_personalData?.messageInfo?.messages.isNotEmpty == true) {
      notificationCount += _personalData!.messageInfo!.messages.length;
    }

    return EnterpriseMainLayout(
      title: widget.loginData.isAdmin ? '管理总览' : '健康首页',
      loginData: widget.loginData,
      currentRoute: '/home',
      notificationCount: notificationCount > 0 ? notificationCount : null,
      showSearchBar: true,
      searchHint: '搜索健康数据、设备、告警...',
      onSearchChanged: (value) {
        // TODO: 实现搜索功能
        print('搜索: $value');
      },
      child: RefreshIndicator(
        onRefresh: _fetchPersonalInfo,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // 管理员功能卡片 #管理员功能卡片
            if (widget.loginData.isAdmin)
              _buildAnimatedCard(
                _buildAdminCard(),
                0,
                onTap: () => _openAdminPanel(),
              ),
            if (widget.loginData.isAdmin) const SizedBox(height: 16),
            
            if (_personalData?.userInfo?.users.isNotEmpty == true)
              _buildAnimatedCard(
                UserInfoCard(
                  user: _personalData!.userInfo!.users.first,
                  onTap: () => context.push('/users/${_personalData!.userInfo!.users.first.userId}', 
                             extra: _personalData!.userInfo!.users.first),
                ),
                widget.loginData.isAdmin ? 1 : 0,
                onTap: () => context.push('/users/${_personalData!.userInfo!.users.first.userId}', 
                          extra: _personalData!.userInfo!.users.first),
              ),
            const SizedBox(height: 16),
            _buildAnimatedCard(
              HealthDataCard(healthData: _personalData?.healthData),
              widget.loginData.isAdmin ? 2 : 1,
              onTap: () => context.push('/health/analysis', extra: _personalData?.healthData),
            ),
            const SizedBox(height: 16),
            if (_personalData?.alertInfo != null)
              _buildAnimatedCard(
                AlertInfoCard(
                  alertInfo: _personalData!.alertInfo,
                  onTap: () => context.push('/alerts', extra: _personalData!.alertInfo),
                ),
                widget.loginData.isAdmin ? 3 : 2,
                onTap: () => context.push('/alerts', extra: _personalData!.alertInfo),
              ),
            const SizedBox(height: 16),
            _buildAnimatedCard(
              MessageInfoCard(
                messageInfo: _personalData?.messageInfo ?? message.MessageInfo.empty(),
              ),
              widget.loginData.isAdmin ? 4 : 3,
              onTap: () => context.push('/messages', extra: _personalData?.messageInfo),
            ),
            const SizedBox(height: 16),
            if (_personalData?.deviceInfo?.devices.isNotEmpty == true)
              _buildAnimatedCard(
                DeviceInfoCard(
                  device: _personalData!.deviceInfo!.devices.first,
                ),
                widget.loginData.isAdmin ? 5 : 4,
                onTap: () => context.push('/devices', extra: _personalData!.deviceInfo!.devices.first),
              ),
          ],
        ),
      ),
  }

  Widget _buildAnimatedCard(Widget child, int index, {VoidCallback? onTap}) =>
    Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: child,
      ),
    ).animate()
     .fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);

  Widget _buildUserInfoCard(ThemeData theme) {
    if (_personalData?.userInfo?.users.isEmpty ?? true) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppText.userInfo,
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  AppText.noData,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }
    final currentUser = _personalData!.userInfo!.users.first;
    return UserInfoCard(
      user: currentUser,
      onTap: () => context.push('/users/${currentUser.userId}', extra: currentUser),
    );
  }

  Widget _buildDeviceInfoCard(ThemeData theme) {
    if (_personalData?.deviceInfo?.devices?.isEmpty ?? true) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppText.deviceInfo,
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  AppText.noDeviceInfo,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }
    final currentDevice = _personalData!.deviceInfo!.devices!.first;
    return DeviceInfoCard(device: currentDevice);
  }

  Widget _buildHealthDataCard(ThemeData theme) {
    if (_personalData?.healthData?.healthData?.isEmpty ?? true) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppText.healthData,
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  AppText.noData,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }
    return HealthDataCard(healthData: _personalData!.healthData);
  }

  Widget _buildAlertsCard(alert.AlertInfo? alertInfo, ThemeData theme) {
    if (alertInfo == null || alertInfo.alerts.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppText.alerts,
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  AppText.noAlerts,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }
    return AlertInfoCard(
      alertInfo: alertInfo,
      onTap: () => context.push('/alerts', extra: alertInfo),
    );
  }

  Widget _buildMessagesCard(message.MessageInfo? messageInfo, ThemeData theme) {
    if (messageInfo == null || messageInfo.messages.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppText.messages,
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  AppText.noMessages,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }
    return MessageInfoCard(
      messageInfo: messageInfo,
    );
  }

  Widget _buildAlertStatusIcon(String status) {
    IconData iconData;
    Color color;

    switch (status.toLowerCase()) {
      case 'pending':
        iconData = Icons.pending;
        color = Colors.orange;
        break;
      case 'responded':
        iconData = Icons.check_circle;
        color = Colors.green;
        break;
      case 'acknowledged':
        iconData = Icons.done_all;
        color = Colors.blue;
        break;
      default:
        iconData = Icons.help;
        color = Colors.grey;
    }

    return Icon(iconData, color: color);
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

  // 获取客户名称
  String _getCustomerName() {
    try {
      return BleSvc.i.customerName;
    } catch (e) {
      return "未知企业";
    }
  }

  // 构建管理员功能卡片 #管理员卡片
  Widget _buildAdminCard() {
    final adminUrl = widget.loginData.adminUrl ?? 'http://192.168.1.6:3333/';
    
    return Card(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.orange.withOpacity(0.1), Colors.deepOrange.withOpacity(0.05)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.admin_panel_settings, color: Colors.orange, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '管理员功能',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.orange,
                          ),
                        ),
                        Text(
                          '您拥有管理员权限',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios, color: Colors.orange, size: 16),
                ],
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.web, color: Colors.blue, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '管理后台',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                          Text(
                            adminUrl,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.grey,
                              fontFamily: 'monospace',
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.launch, color: Colors.blue, size: 16),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '角色：${widget.loginData.roles.map((r) => r.roleName).join(', ')}',
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _openAdminPanel() {
    // 显示管理员功能对话框 #管理员功能对话框
    final adminUrl = widget.loginData.adminUrl ?? 'http://192.168.1.6:3333/';
    final webUsername = widget.loginData.webUsername ?? '';
    final webPassword = widget.loginData.webPassword ?? '';
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.admin_panel_settings, color: Colors.orange),
            SizedBox(width: 8),
            Text('管理员功能'),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('欢迎，${widget.loginData.userName}！'),
              const SizedBox(height: 8),
              Text('您的角色：${widget.loginData.roles.map((r) => r.roleName).join(', ')}'),
              const SizedBox(height: 16),
              const Text('管理后台登录信息：', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              
              // Web登录用户名 #Web登录信息
              if (webUsername.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.person, color: Colors.green, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('用户名', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Text(webUsername, style: const TextStyle(fontWeight: FontWeight.w600, fontFamily: 'monospace')),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy, size: 18),
                        onPressed: () => _copyToClipboard(webUsername),
                        tooltip: '复制用户名',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
              ],
              
              // Web登录密码
              if (webPassword.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.purple.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.purple.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.lock, color: Colors.purple, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('密码', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            Text('●' * webPassword.length, style: const TextStyle(fontWeight: FontWeight.w600)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy, size: 18),
                        onPressed: () => _copyToClipboard(webPassword),
                        tooltip: '复制密码',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
              ],
              
              // 管理后台地址
              Container(
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.withOpacity(0.3)),
                ),
                child: ListTile(
                  leading: const Icon(Icons.web, color: Colors.blue),
                  title: const Text('管理后台', style: TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text(adminUrl, style: const TextStyle(fontSize: 12)),
                  trailing: const Icon(Icons.launch, color: Colors.blue),
                  onTap: () => _launchAdminUrl(),
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.orange, size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '点击管理后台卡片在App内直接访问，用户名和密码已自动填充',
                        style: TextStyle(fontSize: 12, color: Colors.orange),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  void _launchAdminUrl() async {
    // 直接跳转到WebView页面 #App内嵌管理后台
    if (mounted) {
      Navigator.of(context).pop(); // 关闭对话框
      
      // 跳转到WebView页面，传递登录数据
      context.push('/admin-webview', extra: widget.loginData);
    }
  }

  void _copyToClipboard(String text) {
    // 复制到剪贴板 #复制功能
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('已复制到剪贴板'),
        duration: Duration(seconds: 2),
      ),
    );
  }
} 