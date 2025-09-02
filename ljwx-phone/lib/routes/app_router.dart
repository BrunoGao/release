import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/models/alert_model.dart' as alert;
import 'package:ljwx_health_new/models/message_model.dart' as message;
import 'package:ljwx_health_new/models/device_model.dart' as device;
import 'package:ljwx_health_new/models/health_model.dart' as health;
import 'package:ljwx_health_new/models/user_model.dart' as user;
import 'package:ljwx_health_new/screens/login_screen.dart';
import 'package:ljwx_health_new/screens/home_screen.dart';
import 'package:ljwx_health_new/screens/health_main_screen.dart';
import 'package:ljwx_health_new/screens/device_main_screen.dart';
import 'package:ljwx_health_new/screens/alert_details_screen.dart';
import 'package:ljwx_health_new/screens/message_details_screen.dart';
import 'package:ljwx_health_new/screens/device_details_screen.dart';
import 'package:ljwx_health_new/screens/health_analysis_screen.dart';
import 'package:ljwx_health_new/screens/user_details_screen.dart';
import 'package:ljwx_health_new/screens/settings_screen.dart';
import 'package:ljwx_health_new/screens/bluetooth_settings_screen.dart';
import 'package:ljwx_health_new/screens/admin_webview_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:ljwx_health_new/providers/ble_provider.dart';
import 'package:ljwx_health_new/config/app_config.dart'; // 引入统一配置管理

class AppRouter {
  static login.LoginData? _loginData;
  static login.LoginData? get loginData => _loginData;

  static Future<void> setLoginData(login.LoginData data) async {
    _loginData = data;
    // 保存到本地存储
    final prefs = await SharedPreferences.getInstance();
    final jsonData = data.toJson();
    final jsonString = jsonEncode(jsonData);
    print('Saving login data: $jsonString'); // Add debug print
    await prefs.setString('login_data', jsonString);
  }

  static Future<login.LoginData?> loadLoginData() async {
    if (_loginData != null) return _loginData;
    
    final prefs = await SharedPreferences.getInstance();
    final savedData = prefs.getString('login_data');
    if (savedData != null) {
      try {
        print('Loading saved login data: $savedData'); // Add debug print
        final jsonData = jsonDecode(savedData);
        print('Decoded JSON data: $jsonData'); // Add debug print
        _loginData = login.LoginData.fromJson(jsonData);
        return _loginData;
      } catch (e, stackTrace) {
        print('Error loading login data: $e');
        print('Stack trace: $stackTrace'); // Add stack trace
      }
    }
    return null;
  }

  static Future<void> clearLoginData() async {
    _loginData = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('login_data');
  }

  static login.LoginData _getLoginData(BuildContext context, GoRouterState state) {
    final data = state.extra as login.LoginData? ?? _loginData;
    if (data == null) {
      context.go('/');
      throw Exception('Login data is required but not available');
    }
    return data;
  }

  // 获取BleProvider中定义的全局navigatorKey
  static GlobalKey<NavigatorState> _getNavigatorKey() {
    return BleProvider.navigatorKey;
  }

  static final router = GoRouter(
    initialLocation: '/login',
    debugLogDiagnostics: true, // 启用路由日志
    navigatorKey: _getNavigatorKey(),
    redirect: (context, state) async {
      print('Router redirect - current path: ${state.matchedLocation}'); // Debug log
      
      // 如果已经在登录页面，不需要重定向
      if (state.matchedLocation == '/login') {
        print('Already on login page, no redirect needed'); // Debug log
        return null;
      }
      
      try {
        // 检查登录状态
        final loginData = await loadLoginData();
        print('Login data loaded: ${loginData != null}'); // Debug log
        
        if (loginData == null) {
          print('No login data found, redirecting to login'); // Debug log
          return '/login';
        }
        
        // 如果有登录数据且在根路径，根据用户类型重定向 #管理员重定向逻辑
        if (state.matchedLocation == '/' && loginData != null) {
          print('Root path with login data, checking user type'); // Debug log
          if (loginData.isAdmin) {
            print('Admin user, redirecting to admin panel'); // Debug log
            return '/admin';
          } else {
            print('Regular user, redirecting to home'); // Debug log
            return '/home';
          }
        }
        
        print('No redirect needed'); // Debug log
        return null;
      } catch (e) {
        print('Error in redirect: $e'); // Debug log
        return '/login';
      }
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/',
        redirect: (context, state) async {
          // 根据用户类型重定向 #根路径重定向
          final loginData = await loadLoginData();
          if (loginData?.isAdmin == true) {
            return '/admin';
          } else {
            return '/home';
          }
        },
      ),
      // 管理员主界面路由 #管理员主界面
      GoRoute(
        path: '/admin',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          
          print('=== /admin路由调试 ===');
          print('loginData: ${loginData != null}');
          print('loginData.isAdmin: ${loginData?.isAdmin}');
          print('loginData.adminUrl: ${loginData?.adminUrl}');
          
          if (loginData == null) {
            print('No login data available for admin screen, redirecting to login');
            return const LoginScreen();
          }
          
          if (!loginData.isAdmin) {
            print('Non-admin user trying to access admin panel, redirecting to home');
            WidgetsBinding.instance.addPostFrameCallback((_) {
              context.go('/home', extra: loginData);
            });
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          
          print('Creating AdminWebViewScreen');
          return AdminWebViewScreen(
            adminUrl: AppConfig.instance.adminBaseUrl, // 使用统一配置的管理端地址
            webUsername: loginData.webUsername,
            webPassword: loginData.webPassword,
            webPasswordSha: loginData.webPasswordSha,
          );
        },
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) {
          // 优先使用extra传递的数据，然后使用缓存的数据 #HomeScreen数据传递
          final loginData = state.extra as login.LoginData? ?? _loginData;
          
          print('=== /home路由调试 ===');
          print('state.extra: ${state.extra != null}');
          print('_loginData: ${_loginData != null}');
          print('final loginData: ${loginData != null}');
          
          if (loginData != null) {
            print('loginData.isAdmin: ${loginData.isAdmin}');
            print('loginData.adminUrl: ${loginData.adminUrl}');
            print('loginData.roles: ${loginData.roles.map((r) => r.roleName).join(', ')}');
            
            // 如果是管理员，重定向到管理员界面 #管理员重定向检查
            if (loginData.isAdmin) {
              print('Admin user accessing home, redirecting to admin panel');
              WidgetsBinding.instance.addPostFrameCallback((_) {
                context.go('/admin', extra: loginData);
              });
              return const Scaffold(body: Center(child: CircularProgressIndicator()));
            }
          }
          
          if (loginData == null) {
            print('No login data available for home screen, redirecting to login');
            return const LoginScreen();
          }
          
          print('Creating HomeScreen with loginData');
          return HomeScreen(loginData: loginData);
        },
      ),
      // 新的健康数据主页面
      GoRoute(
        path: '/health',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null) {
            return const LoginScreen();
          }
          return HealthMainScreen(loginData: loginData);
        },
      ),
      // 新的设备管理主页面
      GoRoute(
        path: '/device',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null) {
            return const LoginScreen();
          }
          return DeviceMainScreen(loginData: loginData);
        },
      ),
      GoRoute(
        path: '/alerts',
        builder: (context, state) {
          final alertInfo = state.extra as alert.AlertInfo;
          return AlertDetailsScreen(alertInfo: alertInfo);
        },
      ),
      GoRoute(
        path: '/messages',
        builder: (context, state) {
          final messageInfo = state.extra as message.MessageInfo;
          return MessageDetailsScreen(messageInfo: messageInfo);
        },
      ),
      GoRoute(
        path: '/devices',
        builder: (context, state) {
          final deviceData = state.extra as device.Device;
          return DeviceDetailsScreen(device: deviceData);
        },
      ),
      GoRoute(
        path: '/health/analysis',
        builder: (context, state) {
          final loginData = _getLoginData(context, state);
          return HealthAnalysisScreen(
            healthData: const {},
            phoneNumber: loginData?.phone ?? '',
          );
        },
      ),
      GoRoute(
        path: '/users/:userId',
        builder: (context, state) {
          final userData = state.extra as user.User;
          return UserDetailsScreen(user: userData);
        },
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/bluetooth',
        builder: (context, state) => const BluetoothSettingsScreen(),
      ),
      GoRoute(
        path: '/admin-webview',
        builder: (context, state) {
          // 从extra中获取管理员登录信息 #管理后台WebView路由
          final loginData = state.extra as login.LoginData;
          return AdminWebViewScreen(
            adminUrl: loginData.adminUrl ?? AppConfig.instance.adminBaseUrl, // 使用统一配置
            webUsername: loginData.webUsername,
            webPassword: loginData.webPassword,
            webPasswordSha: loginData.webPasswordSha, // 传递SHA密码 #SHA密码传递
          );
        },
      ),
      // 通知页面
      GoRoute(
        path: '/notifications',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null) {
            return const LoginScreen();
          }
          // TODO: 创建通知页面
          return Scaffold(
            appBar: AppBar(title: const Text('通知中心')),
            body: const Center(
              child: Text('通知页面开发中...'),
            ),
          );
        },
      ),
      // 管理员各个功能页面路由
      GoRoute(
        path: '/admin/overview',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null || !loginData.isAdmin) {
            return const LoginScreen();
          }
          return HomeScreen(loginData: loginData); // 使用HomeScreen作为管理员总览
        },
      ),
      GoRoute(
        path: '/admin/monitor',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null || !loginData.isAdmin) {
            return const LoginScreen();
          }
          // TODO: 创建管理员监控页面
          return HealthMainScreen(loginData: loginData); // 临时使用健康页面
        },
      ),
      GoRoute(
        path: '/admin/management',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null || !loginData.isAdmin) {
            return const LoginScreen();
          }
          // TODO: 创建管理员管理页面
          return DeviceMainScreen(loginData: loginData); // 临时使用设备页面
        },
      ),
      GoRoute(
        path: '/admin/alerts',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null || !loginData.isAdmin) {
            return const LoginScreen();
          }
          // TODO: 创建管理员告警页面
          return const Scaffold(
            body: Center(
              child: Text('管理员告警管理页面\n(开发中)'),
            ),
          );
        },
      ),
      GoRoute(
        path: '/admin/settings',
        builder: (context, state) {
          final loginData = state.extra as login.LoginData? ?? _loginData;
          if (loginData == null || !loginData.isAdmin) {
            return const LoginScreen();
          }
          return const SettingsScreen(); // 使用现有设置页面
        },
      ),
    ],
    errorBuilder: (context, state) {
      print('Router error: ${state.error}'); // Debug log
      return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            Text(
              '页面加载失败: ${state.error}',
              style: const TextStyle(color: Colors.red),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
                onPressed: () => context.go('/login'),
                child: const Text('返回登录'),
            ),
          ],
        ),
      ),
      );
    },
  );
} 