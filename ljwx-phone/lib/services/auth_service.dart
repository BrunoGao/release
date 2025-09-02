import 'package:shared_preferences/shared_preferences.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/routes/app_router.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;

class AuthService {
  static const String _phoneKey = 'phone';
  static const String _passwordKey = 'password';
  static const String _isLoggedInKey = 'is_logged_in';

  static Future<void> saveLoginInfo(String phone, String password) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_phoneKey, phone);
    await prefs.setString(_passwordKey, password);
    await prefs.setBool(_isLoggedInKey, true);
  }

  static Future<void> clearLoginInfo() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_phoneKey);
    await prefs.remove(_passwordKey);
    await prefs.remove(_isLoggedInKey);
  }

  static Future<String?> getPhone() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_phoneKey);
  }

  static Future<String?> getPassword() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_passwordKey);
  }

  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_isLoggedInKey) ?? false;
  }

  static Future<login.LoginData?> getLoginData() async {
    try {
      final loginData = AppRouter.loginData;
      if (loginData != null) {
        return loginData;
      }
      
      return await AppRouter.loadLoginData();
    } catch (e) {
      print('获取登录数据失败: $e');
      return null;
    }
  }

  static Future<void> logout() async {
    try {
      print('Logging out...'); // Debug log
    final prefs = await SharedPreferences.getInstance();
      
      // 保留手机号和密码，只清除登录状态 #保留登录信息
      // await prefs.remove(_phoneKey); // 不删除手机号
      // await prefs.remove(_passwordKey); // 不删除密码
      await prefs.remove(_isLoggedInKey); // 只删除登录状态
    await prefs.remove('token');
    await prefs.remove('user_data');
      await prefs.remove('login_data');
    
    // 清除 API 服务中的认证信息
    ApiService.clearAuth();
    
    // 清除AppRouter中的登录数据
    await AppRouter.clearLoginData();
      
      print('Logout completed successfully, credentials preserved'); // Debug log
    } catch (e) {
      print('Error during logout: $e'); // Debug log
      // 即使发生错误，也要尝试清除 API 服务的认证信息
      ApiService.clearAuth();
    }
  }
} 