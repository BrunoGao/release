import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:ljwx_health_new/services/auth_service.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:provider/provider.dart';
import 'package:ljwx_health_new/providers/theme_provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificationsEnabled = true;
  String _language = '中文';
  bool _isResettingPassword = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _notificationsEnabled = prefs.getBool('notifications_enabled') ?? true;
      _language = prefs.getString('language') ?? '中文';
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notifications_enabled', _notificationsEnabled);
    await prefs.setString('language', _language);
  }

  Future<void> _handleResetPassword() async {
    try {
      setState(() {
        _isResettingPassword = true;
      });

      final loginData = await AuthService.getLoginData();
      if (loginData == null) {
        _showErrorDialog('获取用户信息失败，请重新登录');
        return;
      }

      final apiService = ApiService();
      final response = await apiService.resetPassword(loginData.userId.toString());

      if (response['success'] == true) {
        final newPassword = response['data']['password'];
        _showPasswordResetDialog(newPassword);
      } else {
        _showErrorDialog(response['error'] ?? '密码重置失败');
      }
    } catch (e) {
      _showErrorDialog('密码重置失败：$e');
    } finally {
      setState(() {
        _isResettingPassword = false;
      });
    }
  }

  void _showPasswordResetDialog(String newPassword) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 24),
            SizedBox(width: 8),
            Text('密码重置成功'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('您的新密码是：', style: TextStyle(fontSize: 16)),
            SizedBox(height: 12),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: SelectableText(
                      newPassword,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'monospace',
                        color: Colors.blue[800],
                      ),
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.copy, color: Colors.blue),
                    onPressed: () => _copyToClipboard(newPassword),
                    tooltip: '复制密码',
                  ),
                ],
              ),
            ),
            SizedBox(height: 16),
            Text(
              '请妥善保存新密码，建议立即复制并保存到安全位置。',
              style: TextStyle(
                color: Colors.orange[700],
                fontSize: 14,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => _copyToClipboard(newPassword),
            child: Text('复制密码'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _handleLogout();
            },
            child: Text('确定并重新登录'),
          ),
        ],
      ),
    );
  }

  void _copyToClipboard(String password) {
    Clipboard.setData(ClipboardData(text: password));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.white, size: 20),
            SizedBox(width: 8),
            Text('密码已复制到剪贴板'),
          ],
        ),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.error, color: Colors.red, size: 24),
            SizedBox(width: 8),
            Text('错误'),
          ],
        ),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('确定'),
          ),
        ],
      ),
    );
  }

  Future<void> _handleLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(AppText.logout),
        content: Text(AppText.logoutConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(AppText.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(AppText.confirm),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await AuthService.logout();
      if (mounted) {
        context.go('/login');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.settings),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        children: [
          _buildSection(
            AppText.notificationSettings,
            [
              SwitchListTile(
                title: Text(AppText.enableNotifications),
                subtitle: Text(AppText.notificationDescription),
                value: _notificationsEnabled,
                onChanged: (value) {
                  setState(() {
                    _notificationsEnabled = value;
                  });
                  _saveSettings();
                },
              ),
            ],
          ),
          _buildSection(
            AppText.displaySettings,
            [
              SwitchListTile(
                title: Text(AppText.darkMode),
                subtitle: Text(AppText.darkModeDescription),
                value: themeProvider.isDarkMode,
                onChanged: (value) {
                  themeProvider.setDarkMode(value);
                },
              ),
              ListTile(
                title: Text(AppText.language),
                subtitle: Text(_language),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: Text(AppText.selectLanguage),
                      content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          ListTile(
                            title: const Text('中文'),
                            onTap: () {
                              setState(() {
                                _language = '中文';
                              });
                              _saveSettings();
                              Navigator.pop(context);
                            },
                          ),
                          ListTile(
                            title: const Text('English'),
                            onTap: () {
                              setState(() {
                                _language = 'English';
                              });
                              _saveSettings();
                              Navigator.pop(context);
                            },
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
          _buildSection(
            AppText.accountSettings,
            [
              ListTile(
                leading: Icon(Icons.lock_reset, color: Colors.orange),
                title: Text('重置密码'),
                subtitle: Text('重置密码并获取新的随机密码'),
                trailing: _isResettingPassword 
                    ? SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(Icons.chevron_right),
                onTap: _isResettingPassword ? null : _handleResetPassword,
              ),
              ListTile(
                leading: Icon(Icons.logout, color: Colors.red),
                title: Text(AppText.logout, style: TextStyle(color: Colors.red)),
                onTap: _handleLogout,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ),
        Card(
          margin: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            children: children,
          ),
        ),
      ],
    );
  }
} 