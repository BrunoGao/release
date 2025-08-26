import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/services/auth_service.dart'; // 添加退出登录服务

/// 管理后台WebView页面 #App内嵌管理后台
class AdminWebViewScreen extends StatefulWidget {
  final String adminUrl;
  final String? webUsername;
  final String? webPassword;
  final String? webPasswordSha; // SHA加密密码 #SHA密码支持

  const AdminWebViewScreen({
    super.key,
    required this.adminUrl,
    this.webUsername,
    this.webPassword,
    this.webPasswordSha, // 添加SHA密码参数
  });

  @override
  State<AdminWebViewScreen> createState() => _AdminWebViewScreenState();
}

class _AdminWebViewScreenState extends State<AdminWebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  String? _currentUrl;
  bool _showAdminHome = true; // 显示管理员首页 #管理员首页状态

  @override
  void initState() {
    super.initState();
    _initializeWebView();
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted) // 启用JavaScript
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (url) {
          setState(() {
            _isLoading = true;
            _currentUrl = url;
          });
        },
        onPageFinished: (url) {
          setState(() {
            _isLoading = false;
          });
          _autoFillLoginForm(); // 页面加载完成后自动填充登录表单
        },
        onWebResourceError: (error) {
          debugPrint('WebView错误: ${error.description}');
        },
      ));
    
    // 不立即加载WebView，等待用户选择
  }

  /// 加载管理端WebView #加载管理端
  void _loadAdminWebView() {
    setState(() {
      _showAdminHome = false;
      _isLoading = true;
    });
    _controller.loadRequest(Uri.parse(widget.adminUrl));
  }

  /// 返回管理员首页 #返回管理员首页
  void _showAdminHomePage() {
    setState(() {
      _showAdminHome = true;
    });
  }

  /// 切换到员工界面 #切换到员工界面
  void _switchToEmployeeView() async {
    try {
      print('尝试切换到员工界面...');
      
      // 使用pushReplacement确保能够正确跳转，避免路由栈问题
      if (mounted) {
        context.pushReplacement('/home');
        print('切换到员工界面成功');
      }
    } catch (e) {
      print('切换到员工界面失败: $e');
      // 如果pushReplacement失败，尝试使用go
      if (mounted) {
        context.go('/home');
      }
    }
  }

  /// 退出登录 #退出登录功能
  void _handleLogout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.logout, color: Colors.red),
            SizedBox(width: 8),
            Text('退出登录'),
          ],
        ),
        content: const Text('确定要退出登录吗？退出后将返回登录界面。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.of(context).pop();
              await _performLogout();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('退出'),
          ),
        ],
      ),
    );
  }

  /// 执行退出登录 #执行退出登录
  Future<void> _performLogout() async {
    try {
      print('执行退出登录...');
      
      // 调用AuthService.logout()清除登录状态
      await AuthService.logout();
      
      if (mounted) {
        // 跳转到登录页面，使用pushReplacement避免返回
        context.pushReplacement('/login');
        print('退出登录成功，已跳转到登录页面');
        
        // 显示退出成功提示
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('已退出登录'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      print('退出登录失败: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('退出登录失败: $e'),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    }
  }

  /// 自动填充登录表单 #自动登录功能
  void _autoFillLoginForm() {
    print('=== 管理端登录调试信息 ===');
    print('webUsername: ${widget.webUsername}');
    print('webPassword: ${widget.webPassword != null ? '***' : 'null'}');
    print('webPasswordSha: ${widget.webPasswordSha != null ? '***' : 'null'}');
    
    if (widget.webUsername != null && widget.webPassword != null) {
      final script = '''
        // 检查是否是管理后台首页，如果是则尝试API登录 #管理后台API登录
        if (window.location.href.includes('/#/home')) {
          // 直接访问首页，尝试通过API登录获取token
          fetch('/proxy-default/auth/user_name', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              userName: '${widget.webUsername}',
              password: '${widget.webPassword}'
            })
          })
          .then(response => response.json())
          .then(data => {
            if (data.code === 200 && data.data && data.data.token) {
              // 登录成功，保存token到localStorage
              localStorage.setItem('token', data.data.token);
              localStorage.setItem('user', JSON.stringify({
                userName: '${widget.webUsername}',
                token: data.data.token
              }));
              console.log('管理后台自动登录成功');
              // 刷新页面以应用登录状态
              setTimeout(() => window.location.reload(), 500);
            } else {
              console.log('管理后台自动登录失败:', data);
            }
          })
          .catch(error => {
            console.log('管理后台API登录异常:', error);
          });
        
          // 传统登录页面自动填充 #传统登录表单填充
          setTimeout(function() {
            // 尝试多种常见的用户名输入框选择器
            var usernameInput = document.querySelector('input[name="username"]') ||
                               document.querySelector('input[name="user"]') ||
                               document.querySelector('input[name="account"]') ||
                               document.querySelector('input[type="text"]') ||
                               document.querySelector('#username') ||
                               document.querySelector('#user') ||
                               document.querySelector('.username') ||
                               document.querySelector('.user-input');
            
            // 尝试多种常见的密码输入框选择器
            var passwordInput = document.querySelector('input[name="password"]') ||
                               document.querySelector('input[name="pwd"]') ||
                               document.querySelector('input[type="password"]') ||
                               document.querySelector('#password') ||
                               document.querySelector('#pwd') ||
                               document.querySelector('.password') ||
                               document.querySelector('.pwd-input');
            
            // 填充用户名
            if (usernameInput) {
              console.log('自动填充用户名: ${widget.webUsername}');
              usernameInput.value = '${widget.webUsername}';
              usernameInput.dispatchEvent(new Event('input', { bubbles: true }));
              usernameInput.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
              console.log('未找到用户名输入框');
            }
            
            // 填充原始密码
            if (passwordInput) {
              console.log('自动填充密码: ***');
              passwordInput.value = '${widget.webPassword}';
              passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
              passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
              console.log('未找到密码输入框');
            }
            
            // 如果URL包含auto_login=true，尝试自动点击登录按钮
            if (window.location.href.includes('auto_login=true')) {
              setTimeout(function() {
                var loginButton = document.querySelector('button[type="submit"]') ||
                                 document.querySelector('input[type="submit"]') ||
                                 document.querySelector('.login-btn') ||
                                 document.querySelector('.btn-login') ||
                                 document.querySelector('#login') ||
                                 document.querySelector('#loginBtn');
                
                if (loginButton && usernameInput && passwordInput && 
                    usernameInput.value && passwordInput.value) {
                  loginButton.click();
                }
              }, 500);
            }
          }, 1000);
        }
      ''';
      
      _controller.runJavaScript(script);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('管理端'),
        backgroundColor: Colors.orange,
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            // 检查是否可以pop，如果不能则返回首页
            if (Navigator.of(context).canPop()) {
              context.pop();
            } else {
              context.go('/home');
            }
          },
        ),
        actions: [
          // 管理员首页按钮 #管理员首页按钮
          if (!_showAdminHome)
            IconButton(
              icon: const Icon(Icons.dashboard),
              onPressed: _showAdminHomePage,
              tooltip: '管理员首页',
            ),
          // 刷新按钮
          if (!_showAdminHome)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () => _controller.reload(),
              tooltip: '刷新',
            ),
          // 更多选项
          PopupMenuButton<String>(
            onSelected: (value) {
              switch (value) {
                case 'reload':
                  _controller.reload();
                  break;
                case 'home':
                  _controller.loadRequest(Uri.parse(widget.adminUrl));
                  break;
                case 'auto_fill':
                  _autoFillLoginForm();
                  break;
                case 'admin_home':
                  _showAdminHomePage();
                  break;
                case 'logout': // 添加退出登录选项
                  _handleLogout();
                  break;
              }
            },
            itemBuilder: (context) => [
              if (!_showAdminHome) ...[
                const PopupMenuItem(
                  value: 'admin_home',
                  child: Row(
                    children: [
                      Icon(Icons.dashboard, size: 20),
                      SizedBox(width: 8),
                      Text('管理员首页'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'reload',
                  child: Row(
                    children: [
                      Icon(Icons.refresh, size: 20),
                      SizedBox(width: 8),
                      Text('刷新页面'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'home',
                  child: Row(
                    children: [
                      Icon(Icons.home, size: 20),
                      SizedBox(width: 8),
                      Text('返回首页'),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'auto_fill',
                  child: Row(
                    children: [
                      Icon(Icons.login, size: 20),
                      SizedBox(width: 8),
                      Text('自动填充'),
                    ],
                  ),
                ),
              ],
              const PopupMenuItem(
                value: 'logout', // 添加退出登录菜单项
                child: Row(
                  children: [
                    Icon(Icons.logout, size: 20, color: Colors.red),
                    SizedBox(width: 8),
                    Text('退出登录', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: _showAdminHome ? _buildAdminHomePage() : _buildWebView(),
      // 底部信息栏
      bottomNavigationBar: Container(
        height: 40,
        color: Colors.grey[100],
        child: Row(
          children: [
            const SizedBox(width: 12),
            Icon(Icons.web, size: 16, color: Colors.grey[600]),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _showAdminHome ? '管理员首页' : (_currentUrl ?? widget.adminUrl),
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                  fontFamily: 'monospace',
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            // 管理员标识 #管理员标识
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                '管理员模式',
                style: TextStyle(fontSize: 10, color: Colors.orange),
              ),
            ),
            const SizedBox(width: 4),
            if (widget.webUsername != null) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${widget.webUsername}',
                  style: const TextStyle(fontSize: 10, color: Colors.green),
                ),
              ),
              const SizedBox(width: 8),
            ],
          ],
        ),
      ),
    );
  }

  /// 构建管理员首页 #管理员首页UI
  Widget _buildAdminHomePage() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.orange.withOpacity(0.1), Colors.white],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 欢迎卡片 #欢迎卡片
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.orange.withOpacity(0.8), Colors.deepOrange.withOpacity(0.6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.admin_panel_settings, color: Colors.white, size: 32),
                      SizedBox(width: 12),
                      Text(
                        '管理员控制面板',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (widget.webUsername != null)
                    Text(
                      '欢迎，${widget.webUsername}！',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          
          // 功能导航 #功能导航
          const Text(
            '管理功能',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.orange,
            ),
          ),
          const SizedBox(height: 12),
          
          // 管理端WebView #管理端WebView入口
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.web, color: Colors.blue),
              ),
              title: const Text('管理端控制台'),
              subtitle: const Text('访问完整的管理端功能'),
              trailing: const Icon(Icons.arrow_forward_ios),
              onTap: _loadAdminWebView,
            ),
          ),
          const SizedBox(height: 8),
          
          
          // 退出登录 #退出登录入口
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.logout, color: Colors.red),
              ),
              title: const Text('退出登录', style: TextStyle(color: Colors.red)),
              subtitle: const Text('退出管理员账户'),
              trailing: const Icon(Icons.arrow_forward_ios, color: Colors.red),
              onTap: _handleLogout, // 添加退出登录功能
            ),
          ),
          const SizedBox(height: 20),
          
          // 快速信息 #快速信息
          const Text(
            '快速信息',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.orange,
            ),
          ),
          const SizedBox(height: 12),
          
          // 管理端地址信息 #管理端地址信息
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.blue),
                      SizedBox(width: 8),
                      Text(
                        '管理端信息',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '地址：${widget.adminUrl}',
                    style: const TextStyle(
                      fontSize: 14,
                      fontFamily: 'monospace',
                    ),
                  ),
                  if (widget.webUsername != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      '用户：${widget.webUsername}',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 构建WebView #WebView构建
  Widget _buildWebView() {
    return Stack(
      children: [
        WebViewWidget(controller: _controller),
        // 加载指示器
        if (_isLoading)
          Container(
            color: Colors.white,
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.orange),
                  SizedBox(height: 16),
                  Text('正在加载管理端...', style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),
          ),
      ],
    );
  }
} 