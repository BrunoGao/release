import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // 添加剪贴板支持
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/routes/app_router.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/services/auth_service.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/widgets/info_card.dart';
import '../global.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _apiService = ApiService();
  bool _isLoading = false;
  bool _isInitialized = false;
  bool _isResettingPassword = false; // 重置密码状态

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    try {
      print('Initializing app...'); // Debug log
      setState(() {
        _isLoading = true;
      });

      // 总是尝试获取保存的手机号和密码用于自动填充 #自动填充保存的信息
      final phone = await AuthService.getPhone();
      final password = await AuthService.getPassword();
      
      if (phone != null && password != null && mounted) {
        _phoneController.text = phone;
        _passwordController.text = password;
        print('Auto-filled credentials - Phone: $phone'); // Debug log
      }

      // 检查是否已经登录（只有在isLoggedIn为true时才自动登录）
      final isLoggedIn = await AuthService.isLoggedIn();
      print('Is logged in: $isLoggedIn'); // Debug log

      if (isLoggedIn && phone != null && password != null && mounted) {
        print('User is logged in, attempting auto login'); // Debug log
        await _handleLogin();
      } else {
        print('User not logged in or missing credentials, showing login form'); // Debug log
      }
    } catch (e) {
      print('Error during initialization: $e'); // Debug log
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _isInitialized = true;
        });
      }
    }
  }

  Future<void> _handleLogin() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        print('Attempting login with phone: ${_phoneController.text}'); // Debug log
        final response = await _apiService.login(
          _phoneController.text,
          _passwordController.text,
        );

        if (mounted) {
          setState(() {
            _isLoading = false;
          });

          if (response.success && response.data != null) {
            await _onLoginSuccess(response.data!);
          } else {
            print('Login failed: ${response.success}'); // Debug log
            // 清除登录状态
            await AuthService.clearLoginInfo();
            if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(response.error ?? AppText.loginFailed),
                  backgroundColor: Theme.of(context).colorScheme.error,
                  behavior: SnackBarBehavior.floating,
                  margin: const EdgeInsets.all(16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
            );
            }
          }
        }
      } catch (e) {
        print('Login error: $e'); // Debug log
        // 清除登录状态
        await AuthService.clearLoginInfo();
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('${AppText.error}: $e'),
              backgroundColor: Theme.of(context).colorScheme.error,
              behavior: SnackBarBehavior.floating,
              margin: const EdgeInsets.all(16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          );
        }
      }
    }
  }

  Future<void> _onLoginSuccess(login.LoginData loginData) async {
    // 保存登录信息
    await AuthService.saveLoginInfo(
      _phoneController.text,
      _passwordController.text,
    );
    
    // 保存登录数据
    await AppRouter.setLoginData(loginData);
    
    // 添加调试日志 #登录成功调试
    print('=== 登录成功，准备跳转 ===');
    print('loginData.isAdmin: ${loginData.isAdmin}');
    print('loginData.adminUrl: ${loginData.adminUrl}');
    print('loginData.roles: ${loginData.roles.map((r) => r.roleName).join(', ')}');
    
    if (mounted) {
      // 根据用户类型跳转到不同界面 #管理员登录跳转
      if (loginData.isAdmin) {
        print('管理员用户，跳转到管理端界面');
        context.go('/admin', extra: loginData);
      } else {
        print('普通用户，跳转到员工界面');
        context.go('/home', extra: loginData);
      }
    }
  }

  /// 重置密码功能 #重置密码
  Future<void> _resetPassword() async {
    if (_phoneController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('请先输入手机号'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isResettingPassword = true;
    });

    try {
      final result = await _apiService.resetPasswordByPhone(_phoneController.text);
      
      if (mounted) {
        setState(() {
          _isResettingPassword = false;
        });

        if (result['success'] == true) {
          final newPassword = result['data']['password'];
          _showPasswordResetDialog(newPassword);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? '重置密码失败'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isResettingPassword = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('重置密码失败：$e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// 显示重置密码成功对话框 #重置密码对话框
  void _showPasswordResetDialog(String newPassword) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green),
            SizedBox(width: 8),
            Text('密码重置成功'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('您的新密码是：'),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
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
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.copy),
                    onPressed: () => _copyToClipboard(newPassword),
                    tooltip: '复制密码',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '请保存好新密码，然后使用新密码登录。',
              style: TextStyle(color: Colors.orange),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _passwordController.text = newPassword; // 自动填入新密码
            },
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }

  /// 复制密码到剪贴板 #复制功能
  void _copyToClipboard(String password) {
    Clipboard.setData(ClipboardData(text: password));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('密码已复制到剪贴板'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    InfoCard(
                      icon: Icons.lock,
                      title: customerName,
                      subtitle: '',
                      onTap: null,
                    ),
                    const SizedBox(height: 24),
                    Card(
                      elevation: 4,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            TextFormField(
                              controller: _phoneController,
                              decoration: const InputDecoration(
                                labelText: '手机号',
                                border: OutlineInputBorder(),
                              ),
                              keyboardType: TextInputType.phone,
                              validator: (value) => value == null || value.isEmpty ? '请输入手机号' : null,
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _passwordController,
                              decoration: const InputDecoration(
                                labelText: '密码',
                                border: OutlineInputBorder(),
                              ),
                              obscureText: true,
                              validator: (value) => value == null || value.isEmpty ? '请输入密码' : null,
                            ),
                            const SizedBox(height: 24),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : _handleLogin,
                                child: _isLoading
                                    ? const SizedBox(
                                        width: 24,
                                        height: 24,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    : const Text('登录'),
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: TextButton(
                                onPressed: _isResettingPassword ? null : _resetPassword,
                                child: _isResettingPassword
                                    ? const SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    : const Text('忘记密码？重置密码'),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
} 