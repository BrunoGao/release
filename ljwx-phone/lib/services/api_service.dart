import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:ljwx_health_new/models/login_response.dart';
import 'package:ljwx_health_new/models/personal_data.dart';
import 'package:ljwx_health_new/models/health_analysis.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/models/alert_model.dart' as alert_model;
import 'package:ljwx_health_new/models/message_model.dart' as message_model;
import 'package:intl/intl.dart';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import '../config/app_config.dart'; // 引入统一配置管理

class ApiService {
  static String? _token;
  static Map<String, String> _headers = {
    'Content-Type': 'application/json',
  };
  static LoginData? _loginData;
  static const Duration _timeout = Duration(seconds: 30); // 增加超时时间用于调试
  
  // HTTP连接池管理
  static HttpClient? _httpClient;
  static Timer? _keepAliveTimer;
  static const Duration keepAliveInterval = Duration(seconds: 30);
  
  // 获取配置实例 #配置实例获取
  static AppConfig get _config => AppConfig.instance;

  static void setToken(String token) {
    _token = token;
    _headers['Authorization'] = 'Bearer $token';
  }

  static void clearAuth() {
    _token = null;
    _headers = {
      'Content-Type': 'application/json',
    };
  }

  /// 初始化HTTP客户端和保活机制 #HTTP客户端初始化
  static void initHttpClient() {
    _httpClient?.close(force: true);
    _httpClient = HttpClient();
    _httpClient!.connectionTimeout = _timeout;
    _httpClient!.idleTimeout = Duration(seconds: 60);
    
    // 启动保活定时器
    _startKeepAlive();
    debugPrint('HTTP客户端已初始化，保活机制已启动');
  }

  /// 启动HTTP保活机制 #HTTP保活
  static void _startKeepAlive() {
    _keepAliveTimer?.cancel();
    _keepAliveTimer = Timer.periodic(keepAliveInterval, (timer) async {
      await _performKeepAlive();
    });
  }

  /// 执行HTTP保活检查 #HTTP保活检查
  static Future<void> _performKeepAlive() async {
    try {
      if (_httpClient == null) {
        initHttpClient();
        return;
      }
      
      // 发送简单的健康检查请求
      final request = await _httpClient!.getUrl(Uri.parse('${_config.apiBaseUrl}/health'))
          .timeout(Duration(seconds: 5));
      final response = await request.close().timeout(Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        debugPrint('HTTP保活检查成功');
      } else {
        debugPrint('HTTP保活检查失败，状态码: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('HTTP保活检查异常: $e');
      // 重新初始化客户端
      initHttpClient();
    }
  }

  /// 停止HTTP保活机制 #停止HTTP保活
  static void stopKeepAlive() {
    _keepAliveTimer?.cancel();
    _httpClient?.close(force: true);
    _httpClient = null;
    debugPrint('HTTP保活机制已停止');
  }

  static void setLoginData(LoginData data) {
    _loginData = data;
    _headers['Authorization'] = 'Bearer ${data.token}';
  }

  Future<LoginResponse> login(String phone, String password) async {
    try {
      print('Attempting to connect to: ${_config.apiBaseUrl}');
      final response = await http.get(
        Uri.parse('${_config.phoneLoginUrl}?phone=$phone&password=$password'),
      ).timeout(_timeout);
      
      print('Login response: [38;5;2m${response.body}[0m');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        print('Parsed JSON: $jsonData');
        
        // 检查响应格式
        if (!jsonData.containsKey('success')) {
          return LoginResponse(
            success: false,
            data: null,
            error: '服务器响应格式错误：缺少 success 字段',
          );
        }

        if (!jsonData['success']) {
          return LoginResponse(
            success: false,
            data: null,
            error: jsonData['error'] ?? '登录失败',
          );
        }

        if (!jsonData.containsKey('data')) {
          return LoginResponse(
            success: false,
            data: null,
            error: '服务器响应格式错误：缺少 data 字段',
          );
        }

        final data = jsonData['data'];
        
        // 检查必要字段
        if (!data.containsKey('user_id') || 
            !data.containsKey('user_name') || 
            !data.containsKey('device_sn') || 
            !data.containsKey('phone')) {
          return LoginResponse(
            success: false,
            data: null,
            error: '服务器响应格式错误：缺少必要字段',
          );
        }

        // 创建登录数据，使用设备序列号作为临时token
        final loginData = LoginData(
          deviceSn: data['device_sn'],
          phone: data['phone'],
          userId: data['user_id'],
          userName: data['user_name'],
          token: data['device_sn'], // 使用设备序列号作为临时token
          isAdmin: data['is_admin'] ?? false, // 添加管理员标识 #管理员字段解析
          roles: (data['roles'] as List<dynamic>?)
              ?.map((role) => UserRole.fromJson(role))
              .toList() ?? [], // 添加角色列表
          adminUrl: data['adminUrl'] as String?, // 添加管理后台地址
          webUsername: data['is_admin'] == true ? data['user_name'] : null, // 管理员使用自己的用户名
          webPassword: data['is_admin'] == true ? password : null, // 管理员使用自己的密码
          webPasswordSha: data['is_admin'] == true ? _generateShaPassword(password) : null, // 生成SHA密码
        );

        // 调试信息 - 查看管理员登录数据
        if (data['is_admin'] == true) {
          print('=== API服务 - 管理员登录数据调试 ===');
          print('is_admin: ${data['is_admin']}');
          print('user_name: ${data['user_name']}');
          print('phone: $phone');
          print('设置的webUsername: ${data['user_name']}');
          print('设置的webPassword: ${password != null ? '***' : 'null'}');
        }

        setLoginData(loginData);
        _config.setDeviceSn(data['device_sn']); // 更新配置中的设备序列号
        
        // 登录成功后初始化HTTP客户端保活
        initHttpClient();
        
        return LoginResponse(
          success: true,
          data: loginData,
        );
      } else {
        return LoginResponse(
          success: false,
          data: null,
          error: '登录失败，状态码：${response.statusCode}',
      );
      }
    } catch (e) {
      return LoginResponse(
        success: false,
        data: null,
        error: '登录异常：$e',
      );
    }
  }

  // 添加缓存相关变量
  PersonalData? _cachedPersonalData;
  DateTime? _lastCacheTime;
  static const Duration CACHE_DURATION = Duration(minutes: 5); // 缓存有效期5分钟
  
  // 添加加载状态控制器
  final StreamController<bool> _loadingStateController = StreamController<bool>.broadcast();
  Stream<bool> get loadingStateStream => _loadingStateController.stream;

  // 添加错误状态控制器
  final StreamController<String> _errorStateController = StreamController<String>.broadcast();
  Stream<String> get errorStateStream => _errorStateController.stream;

  // 检查缓存是否有效
  bool _isCacheValid() {
    if (_cachedPersonalData == null || _lastCacheTime == null) return false;
    return DateTime.now().difference(_lastCacheTime!) < CACHE_DURATION;
  }

  // 获取缓存的个人数据
  PersonalData? getCachedPersonalData() {
    return _isCacheValid() ? _cachedPersonalData : null;
  }

  // 更新缓存
  void _updateCache(PersonalData data) {
    _cachedPersonalData = data;
    _lastCacheTime = DateTime.now();
  }

  // 清除缓存
  void clearCache() {
    _cachedPersonalData = null;
    _lastCacheTime = null;
  }

  Future<PersonalData> getPersonalInfo(String phone) async {
    try {
      // 先返回缓存数据（如果有）
      if (_isCacheValid()) {
        debugPrint('使用缓存数据');
        return _cachedPersonalData!;
      }

      _loadingStateController.add(true);
      debugPrint('Fetching personal info for phone: $phone');
      debugPrint('Headers: $_headers');

      final response = await http.get(
        Uri.parse('${_config.apiBaseUrl}/phone_get_personal_info?phone=$phone'),
        headers: _headers,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw TimeoutException('请求超时');
        },
      );
      
      debugPrint('Request URL: ${_config.apiBaseUrl}/phone_get_personal_info?phone=$phone');
      debugPrint('Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        if (response.body.isEmpty) {
          debugPrint('Empty response received from server');
          _errorStateController.add('服务器返回空数据');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }

        Map<String, dynamic> jsonData;
        try {
          jsonData = jsonDecode(response.body) as Map<String, dynamic>;
          debugPrint('Parsed JSON: $jsonData');
        } catch (e) {
          debugPrint('JSON decode error: $e');
          debugPrint('Raw response: ${response.body}');
          _errorStateController.add('数据解析失败');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }

        // 检查是否有错误信息
        if (jsonData.containsKey('error')) {
          debugPrint('Server returned error: ${jsonData['error']}');
          _errorStateController.add(jsonData['error'] ?? '服务器返回错误');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }

        // 检查成功状态
        if (jsonData['success'] == false) {
          debugPrint('Request failed: ${jsonData['error'] ?? 'Unknown error'}');
          _errorStateController.add(jsonData['error'] ?? '请求失败');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }

        if (!jsonData.containsKey('data')) {
          debugPrint('Response missing data field: $jsonData');
          _errorStateController.add('数据格式错误');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }

        final data = jsonData['data'] as Map<String, dynamic>;
        
        // 不要覆盖服务器返回的数据，只在完全缺失时初始化
        debugPrint('Server data keys: ${data.keys}');
        debugPrint('Alert info exists: ${data.containsKey('alert_info')}');
        debugPrint('Message info exists: ${data.containsKey('message_info')}');

        // Use login data if no user info available - 安全检查
        if (_loginData != null && 
            data['user_info']?['data'] != null && 
            (data['user_info']['data']['users'] as List? ?? []).isEmpty) {
          data['user_info']['data']['users'] = [
            {
              'user_id': _loginData!.userId.toString(),
              'user_name': _loginData!.userName,
              'phone_number': _loginData!.phone,
              'device_sn': _loginData!.deviceSn,
              'dept_id': '',
              'dept_name': '',
              'device_status': '',
              'charging_status': '',
              'wearable_status': '',
              'status': '',
              'create_time': '',
              'update_time': '',
            }
          ];
        }

        try {
          final personalData = PersonalData.fromJson(jsonData);
          debugPrint('PersonalData created successfully');
          // 更新缓存
          _updateCache(personalData);
          _loadingStateController.add(false);
          return personalData;
        } catch (e, stackTrace) {
          debugPrint('Error creating PersonalData: $e');
          debugPrint('Stack trace: $stackTrace');
          _errorStateController.add('数据转换失败');
          _loadingStateController.add(false);
          return _cachedPersonalData ?? PersonalData(
            alertInfo: alert_model.AlertInfo.empty(),
            configInfo: null,
            deviceInfo: null,
            healthData: null,
            userInfo: null,
            messageInfo: message_model.MessageInfo.empty(),
          );
        }
      } else {
        debugPrint('Server error: ${response.statusCode}');
        debugPrint('Error body: ${response.body}');
        _errorStateController.add('服务器错误: ${response.statusCode}');
        _loadingStateController.add(false);
        return _cachedPersonalData ?? PersonalData(
          alertInfo: alert_model.AlertInfo.empty(),
          configInfo: null,
          deviceInfo: null,
          healthData: null,
          userInfo: null,
          messageInfo: message_model.MessageInfo.empty(),
        );
      }
    } catch (e, stackTrace) {
      debugPrint('Error in getPersonalInfo: $e');
      debugPrint('Stack trace: $stackTrace');
      _errorStateController.add('网络请求失败: $e');
      _loadingStateController.add(false);
      return _cachedPersonalData ?? PersonalData(
        alertInfo: alert_model.AlertInfo.empty(),
        configInfo: null,
        deviceInfo: null,
        healthData: null,
        userInfo: null,
        messageInfo: message_model.MessageInfo.empty(),
      );
    }
  }

  Future<HealthAnalysis> getHealthAnalysis(String phone, DateTime startDate, DateTime endDate) async {
    try {
      final dateFormat = DateFormat('yyyy-MM-dd');
      final formattedStartDate = dateFormat.format(startDate);
      final formattedEndDate = dateFormat.format(endDate);

      print('Fetching health analysis for phone: $phone');
      print('Date range: $formattedStartDate to $formattedEndDate');

      final response = await http.get(
        Uri.parse(
          '${_config.apiBaseUrl}/get_all_health_data_by_orgIdAndUserId_mobile'
          '?phone=$phone'
          '&startDate=$formattedStartDate'
          '&endDate=$formattedEndDate'
        ),
      ).timeout(_timeout);

      print('Response status code: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        if (jsonData['success'] == true) {
          return HealthAnalysis.fromJson(jsonData);
        } else {
          throw Exception(jsonData['error'] ?? '获取健康数据失败');
        }
      } else {
        throw Exception('服务器错误 (${response.statusCode}): ${response.body}');
      }
    } on SocketException catch (e) {
      print('Network error: $e');
      String errorMessage = '网络连接失败';
      if (e.message.contains('No route to host')) {
        errorMessage = '无法连接到服务器，请检查：\n1. 服务器地址是否正确\n2. 设备是否与服务器在同一网络\n3. 服务器是否正在运行';
      } else if (e.message.contains('Connection refused')) {
        errorMessage = '服务器拒绝连接，请检查服务器是否正在运行';
      }
      throw Exception(errorMessage);
    } on TimeoutException catch (e) {
      print('Request timeout: $e');
      throw Exception('请求超时，请检查网络连接');
    } on FormatException catch (e) {
      print('Data format error: $e');
      throw Exception('数据格式错误');
    } catch (e) {
      print('Health analysis error: $e');
      throw Exception('获取健康数据失败：$e');
    }
  }

  Future<Map<String, dynamic>> getHealthDataByDateRange(String phone, String startDate, String endDate) async {
    final url = Uri.parse('${_config.apiBaseUrl}/get_all_health_data_by_orgIdAndUserId_mobile?phone=$phone&startDate=$startDate&endDate=$endDate');
    
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load health data');
      }
    } catch (e) {
      throw Exception('Error fetching health data: $e');
    }
  }

  Future<Map<String, dynamic>> fetchData() async {
    try {
      final response = await http.get(
        Uri.parse('${_config.apiBaseUrl}/api/v1/dashboard'),
        headers: _headers,
      );
      debugPrint('Parsed JSON: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // 检查响应中是否包含 data 字段
        if (data is Map<String, dynamic> && data.containsKey('data')) {
          if (data['data'] is Map<String, dynamic> && data['data'].containsKey('data')) {
            return data['data']['data'];
          }
          return data['data'];
        } else {
          debugPrint('Response missing data field: $data');
          return data;
        }
      } else {
        throw Exception('Failed to fetch data: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error fetching data: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> fetchDataInIsolate(Map<String, dynamic> params) async {
    try {
      final uri = Uri.parse('${_config.apiBaseUrl}/api/v1/dashboard').replace(queryParameters: params);
      final response = await http.get(
        uri,
        headers: _headers,
      );
      debugPrint('Data fetched in isolate successfully');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        debugPrint('Data fetched successfully: $data');
        
        // 检查响应中是否包含 data 字段
        if (data is Map<String, dynamic> && data.containsKey('data')) {
          if (data['data'] is Map<String, dynamic> && data['data'].containsKey('data')) {
            return data['data']['data'];
          }
          return data['data'];
        } else {
          return data;
        }
      } else {
        throw Exception('Failed to fetch data: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error fetching data in isolate: $e');
      rethrow;
    }
  }

  /// 上传健康数据(v1.2简化版本) #简化健康数据上传
  Future<bool> uploadHealthData(Map<String, dynamic> healthData) async {
    try {
      log('准备上传健康数据: ${json.encode(healthData).substring(0, min(200, json.encode(healthData).length))}...');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/upload_health_data'),
        headers: _headers,
        body: jsonEncode(healthData),
      );

      log('健康数据上传响应状态: ${response.statusCode}');
      log('健康数据上传响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        try {
          final result = jsonDecode(response.body);
          if (result is Map<String, dynamic>) {
            if (result.containsKey('success')) {
              return result['success'] == true;
            } else if (result.containsKey('status') && result['status'] == 'success') {
              return true;
            }
          }
          return true; // 如果响应是200但没有明确的success字段，也认为是成功的
        } catch (e) {
          log('解析健康数据上传响应失败: $e');
          return true; // 如果解析失败但状态码是200，也认为是成功的
        }
      }
      return false;
    } catch (e) {
      log('上传健康数据出错: $e');
      return false;
    }
  }

  /// 上传设备信息(v1.2简化版本) #简化设备信息上传
  Future<bool> uploadDeviceInfo(Map<String, dynamic> deviceInfo) async {
    try {
      log('准备上传设备信息: ${json.encode(deviceInfo).substring(0, min(200, json.encode(deviceInfo).length))}...');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/upload_device_info'),
        headers: _headers,
        body: jsonEncode(deviceInfo),
      );

      log('设备信息上传响应状态: ${response.statusCode}');
      log('设备信息上传响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        try {
          final result = jsonDecode(response.body);
          if (result is Map<String, dynamic>) {
            if (result.containsKey('success')) {
              return result['success'] == true;
            } else if (result.containsKey('status') && result['status'] == 'success') {
              return true;
            }
          }
          return true; // 如果响应是200但没有明确的success字段，也认为是成功的
        } catch (e) {
          log('解析设备信息上传响应失败: $e');
          return true; // 如果解析失败但状态码是200，也认为是成功的
        }
      }
      return false;
    } catch (e) {
      log('上传设备信息出错: $e');
      return false;
    }
  }

  /// 上传通用事件(v1.2简化版本) #简化通用事件上传
  Future<bool> uploadCommonEvent(Map<String, dynamic> event) async {
    try {
      log('准备上传通用事件: ${json.encode(event).substring(0, min(200, json.encode(event).length))}...');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/upload_common_event'),
        headers: _headers,
        body: jsonEncode(event),
      );
      
      log('通用事件上传响应状态: ${response.statusCode}');
      log('通用事件上传响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        try {
          final result = jsonDecode(response.body);
          if (result is Map<String, dynamic>) {
            if (result.containsKey('success')) {
              return result['success'] == true;
            } else if (result.containsKey('status') && result['status'] == 'success') {
              return true;
            }
          }
          return true;
        } catch (e) {
          log('解析通用事件上传响应失败: $e');
          return true;
        }
      }
      return false;
    } catch (e) {
      log('上传通用事件出错: $e');
      return false;
    }
  }

  /// 上传手表日志数据 #上传手表日志
  Future<bool> uploadWatchLog(Map<String, dynamic> logData) async {
    try {
      log('准备上传手表日志: ${json.encode(logData).substring(0, min(300, json.encode(logData).length))}...');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/upload_watch_log'),
        headers: _headers,
        body: jsonEncode(logData),
      );
      
      log('手表日志上传响应状态: ${response.statusCode}');
      log('手表日志上传响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        try {
          final result = jsonDecode(response.body);
          if (result is Map<String, dynamic>) {
            if (result.containsKey('success')) {
              return result['success'] == true;
            } else if (result.containsKey('status') && result['status'] == 'success') {
              return true;
            }
          }
          return true;
        } catch (e) {
          log('解析手表日志上传响应失败: $e');
          return true;
        }
      }
      return false;
    } catch (e) {
      log('上传手表日志出错: $e');
      return false;
    }
  }

  // 获取设备消息
  Future<List<Map<String, dynamic>>> getDeviceMessages(String deviceSn) async {
    try {
      var url = '${_config.apiBaseUrl}/message/receive?deviceSn=$deviceSn';
      log('获取设备消息: $url');
      
      var response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        var jsonResponse = jsonDecode(response.body);
        if (jsonResponse['code'] == 200) {
          var data = jsonResponse['data'];
          if (data == null) {
            log('设备消息数据为null');
            return [];
          }
          
          if (data is List) {
            return List<Map<String, dynamic>>.from(
              data.map((item) => item as Map<String, dynamic>)
            );
          } else {
            log('设备消息数据不是List格式: ${data.runtimeType}');
            return [];
          }
        } else {
          log('获取设备消息失败: ${jsonResponse['msg']}');
          return [];
        }
      } else {
        log('获取设备消息HTTP错误: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      log('获取消息失败: $e');
      return [];
    }
  }

  // 获取健康数据配置
  Future<Map<String, dynamic>> getHealthDataConfig(String deviceSn) async {
    try {
      var url = '${_config.apiBaseUrl}/fetch_health_data_config?customer_id=9&deviceSn=$deviceSn';
      log('获取健康数据配置: $url');
      
      var response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        var jsonResponse = jsonDecode(response.body);
        
        if (jsonResponse['code'] == 200) {
          var data = jsonResponse['data'];
          if (data == null) {
            log('健康配置数据为null，返回默认配置');
            return _getDefaultConfig();
          }
          
          // 处理类型转换问题
          try {
            // 确保返回的是Map<String, dynamic>类型
            if (data is Map) {
              // 显式进行类型转换
              Map<String, dynamic> typedData = {};
              data.forEach((key, value) {
                if (key is String) {
                  typedData[key] = value;
                }
              });
              
              // 保存到全局变量
              _config.setSystemConfig(typedData);
              
              // 更新客户名称
              if (typedData.containsKey('customer_name') && typedData['customer_name'] != null) {
                _config.setCustomerName(typedData['customer_name'].toString());
                log('更新客户名称: ${_config.customerName}');
              }
              
              // 更新上传方式
              if (typedData.containsKey('upload_method') && typedData['upload_method'] != null) {
                _config.setUploadMethod(typedData['upload_method'].toString());
                log('更新上传方式: ${_config.uploadMethod}');
              }
              
              return typedData;
            } else {
              log('健康配置数据格式不正确: ${data.runtimeType}');
              return _getDefaultConfig();
            }
          } catch (e) {
            log('处理健康配置数据时出错: $e');
            return _getDefaultConfig();
          }
        } else {
          log('获取健康配置失败: ${jsonResponse['msg']}');
          return _getDefaultConfig();
        }
      } else {
        log('获取健康配置HTTP错误: ${response.statusCode}');
        return _getDefaultConfig();
      }
    } catch (e) {
      log('获取健康数据配置异常: $e');
      return _getDefaultConfig();
    }
  }
  
  // 获取默认配置
  Map<String, dynamic> _getDefaultConfig() {
    Map<String, dynamic> defaultConfig = {
      'customer_name': _config.customerName,
      'upload_method': _config.uploadMethod,
      'interface_data': {},
      'mtu': 512,
      'cache_max_count': 100,
      'upload_retry_count': 3,
      'upload_retry_interval': 5
    };
    
    // 更新全局变量
    _config.setSystemConfig(Map<String, dynamic>.from(defaultConfig));
    
    return defaultConfig;
  }

  // 根据经纬度获取地址信息
  Future<String> getAddressFromCoordinates(double latitude, double longitude) async {
    try {
      final response = await http.get(
        Uri.parse('${_config.apiBaseUrl}/geolocation/reverse?lat=$latitude&lng=$longitude'),
        headers: _headers,
      ).timeout(_timeout);
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        if (jsonData['success'] == true && jsonData['data'] != null) {
          return jsonData['data']['address'] ?? '未知地址';
        }
      }
      return '${latitude.toStringAsFixed(6)}, ${longitude.toStringAsFixed(6)}';
    } catch (e) {
      debugPrint('获取地址信息失败: $e');
      return '${latitude.toStringAsFixed(6)}, ${longitude.toStringAsFixed(6)}';
    }
  }

  // 处理告警
  Future<bool> dealAlert(String alertId) async {
    try {
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/dealAlert'),
        headers: _headers,
        body: jsonEncode({'alert_id': alertId}),
      ).timeout(_timeout);
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData['success'] == true;
      }
      return false;
    } catch (e) {
      debugPrint('处理告警失败: $e');
      return false;
    }
  }

  // 根据健康ID获取健康数据
  Future<Map<String, dynamic>?> fetchHealthDataById(String healthId) async {
    try {
      final response = await http.get(
        Uri.parse('${_config.apiBaseUrl}/fetchHealthDataById?id=$healthId'),
        headers: _headers,
      ).timeout(_timeout);
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        if (jsonData['success'] == true && jsonData['data'] != null) {
          return jsonData['data'];
        }
      }
      return null;
    } catch (e) {
      debugPrint('获取健康数据失败: $e');
      return null;
    }
  }

  // 标记消息已读
  Future<bool> markMessageAsRead(String deviceSn, {DateTime? receivedTime, String? messageId, Map<String, dynamic>? originalMessage}) async {
    try {
      // 构建响应消息对象-V4.0使用新接口
      final Map<String, dynamic> responseData = {
        'message_id': messageId,
        'device_sn': deviceSn,
        'message': '已读', // 响应内容
        'received_time': receivedTime?.toIso8601String() ?? DateTime.now().toIso8601String(),
      };
      
      // 打印详细请求信息用于调试
      debugPrint('标记消息已读请求: ${Uri.parse('${_config.apiBaseUrl}/DeviceMessage/send')}');
      debugPrint('请求体: ${jsonEncode(responseData)}');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/DeviceMessage/send'),
        headers: _headers,
        body: jsonEncode(responseData),
      ).timeout(_timeout);
      
      // 打印响应信息
      debugPrint('标记消息已读响应码: ${response.statusCode}');
      debugPrint('标记消息已读响应体: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        // 兼容新接口响应格式
        if (jsonData['success'] == true) {
          debugPrint('标记消息已读成功');
          return true;
        } else {
          debugPrint('标记消息已读失败: ${jsonData['message'] ?? "未知错误"}');
          return false;
        }
      }
      return false;
    } catch (e) {
      debugPrint('标记消息已读失败: $e');
      return false;
    }
  }

  void dispose() {
    _loadingStateController.close();
    _errorStateController.close();
  }

  // 添加日志方法
  void log(String message) {
    debugPrint(message);
  }

  // 后台状态管理
  static bool _isDataFetchingPaused = false;
  static Timer? _dataFetchingTimer;

  /// 暂停数据获取 #后台状态管理
  static void pauseDataFetching() {
    _isDataFetchingPaused = true;
    _dataFetchingTimer?.cancel();
    debugPrint('数据获取已暂停（应用在后台）');
  }

  /// 恢复数据获取 #后台状态管理
  static void resumeDataFetching() {
    _isDataFetchingPaused = false;
    debugPrint('数据获取已恢复（应用回到前台）');
  }

  /// 检查是否应该暂停数据获取 #后台状态管理
  static bool get isDataFetchingPaused => _isDataFetchingPaused;

  /// 重置密码 #重置密码功能
  Future<Map<String, dynamic>> resetPassword(String userId) async {
    try {
      debugPrint('重置密码请求，用户ID: $userId');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/phone/reset_password'),
        headers: _headers,
        body: jsonEncode({'userId': userId}),
      ).timeout(_timeout);
      
      debugPrint('重置密码响应状态: ${response.statusCode}');
      debugPrint('重置密码响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData;
      } else {
        return {
          'success': false,
          'error': '服务器错误 (${response.statusCode}): ${response.body}'
        };
      }
    } catch (e) {
      debugPrint('重置密码失败: $e');
      return {
        'success': false,
        'error': '重置密码失败：$e'
      };
    }
  }

  /// 通过手机号重置密码 #手机号重置密码
  Future<Map<String, dynamic>> resetPasswordByPhone(String phone) async {
    try {
      debugPrint('通过手机号重置密码请求，手机号: $phone');
      debugPrint('请求URL: ${_config.apiBaseUrl}/phone/reset_password_by_phone');
      debugPrint('请求headers: $_headers');
      debugPrint('请求body: ${jsonEncode({'phone': phone})}');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/phone/reset_password_by_phone'),
        headers: _headers,
        body: jsonEncode({'phone': phone}),
      ).timeout(_timeout);
      
      debugPrint('重置密码响应状态: ${response.statusCode}');
      debugPrint('重置密码响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData;
      } else {
        return {
          'success': false,
          'error': '服务器错误 (${response.statusCode}): ${response.body}'
        };
      }
    } catch (e) {
      debugPrint('通过手机号重置密码失败: $e');
      return {
        'success': false,
        'error': '重置密码失败：$e'
      };
    }
  }

  /// 生成SHA加密密码 #SHA密码生成
  String _generateShaPassword(String password) {
    try {
      var bytes = utf8.encode(password);
      var digest = sha256.convert(bytes);
      return digest.toString();
    } catch (e) {
      debugPrint('生成SHA密码失败: $e');
      return password; // 如果SHA加密失败，返回原密码
    }
  }

  /// 检查设备绑定状态 #检查设备绑定
  Future<Map<String, dynamic>> checkDeviceBinding({
    required String serialNumber,
    required String phoneNumber,
    int retryCount = 3
  }) async {
    for (int i = 0; i < retryCount; i++) {
      try {
        debugPrint('检查设备绑定状态请求 - 设备序列号: $serialNumber, 手机号: $phoneNumber');
        
        final response = await http.post(
          Uri.parse('${_config.apiBaseUrl}/api/device/check_binding'),
          headers: _headers,
          body: jsonEncode({
            'serial_number': serialNumber,
            'phone_number': phoneNumber
          }),
        ).timeout(_timeout);
        
        debugPrint('检查绑定状态响应状态: ${response.statusCode}');
        debugPrint('检查绑定状态响应内容: ${response.body}');
        
        if (response.statusCode == 200) {
          final jsonData = jsonDecode(response.body);
          return jsonData;
        } else {
          throw Exception('服务器错误 (${response.statusCode}): ${response.body}');
        }
      } catch (e) {
        debugPrint('检查设备绑定状态失败 (第${i+1}次): $e');
        if (i == retryCount - 1) rethrow;
        await Future.delayed(Duration(seconds: 2 * (i + 1)));
      }
    }
    throw Exception('网络请求失败');
  }

  /// 提交设备绑定申请 #提交设备绑定申请
  Future<Map<String, dynamic>> submitDeviceBindingApplication(Map<String, dynamic> applicationData) async {
    try {
      debugPrint('提交设备绑定申请请求: $applicationData');
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/api/device/binding_application'),
        headers: _headers,
        body: jsonEncode(applicationData),
      ).timeout(_timeout);
      
      debugPrint('提交绑定申请响应状态: ${response.statusCode}');
      debugPrint('提交绑定申请响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData;
      } else {
        return {
          'success': false,
          'error': '服务器错误 (${response.statusCode}): ${response.body}'
        };
      }
    } catch (e) {
      debugPrint('提交设备绑定申请失败: $e');
      return {
        'success': false,
        'error': '提交申请失败：$e'
      };
    }
  }

  /// 获取用户设备绑定状态列表 #获取绑定状态列表
  Future<Map<String, dynamic>> getUserBindingStatus(String userId) async {
    try {
      debugPrint('获取用户绑定状态请求，用户ID: $userId');
      
      final response = await http.get(
        Uri.parse('${_config.apiBaseUrl}/api/device/user_bindings?user_id=$userId'),
        headers: _headers,
      ).timeout(_timeout);
      
      debugPrint('获取绑定状态响应状态: ${response.statusCode}');
      debugPrint('获取绑定状态响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData;
      } else {
        return {
          'success': false,
          'error': '服务器错误 (${response.statusCode}): ${response.body}'
        };
      }
    } catch (e) {
      debugPrint('获取用户绑定状态失败: $e');
      return {
        'success': false,
        'error': '获取绑定状态失败：$e'
      };
    }
  }

  /// 处理告警信息 #处理告警API
  Future<Map<String, dynamic>> processAlert(String alertId, String status) async {
    try {
      debugPrint('处理告警请求，告警ID: $alertId，状态: $status');
      
      final requestBody = {
        'alert_id': alertId,
        'status': status,
        'processed_time': DateTime.now().toIso8601String(),
      };
      
      final response = await http.post(
        Uri.parse('${_config.apiBaseUrl}/api/alerts/process'),
        headers: _headers,
        body: jsonEncode(requestBody),
      ).timeout(_timeout);
      
      debugPrint('处理告警响应状态: ${response.statusCode}');
      debugPrint('处理告警响应内容: ${response.body}');
      
      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return jsonData;
      } else {
        return {
          'success': false,
          'error': '服务器错误 (${response.statusCode}): ${response.body}'
        };
      }
    } catch (e) {
      debugPrint('处理告警失败: $e');
      return {
        'success': false,
        'error': '处理告警失败：$e'
      };
    }
  }

  /// 标记告警为已处理 #标记告警已处理
  Future<bool> markAlertAsProcessed(String alertId) async {
    try {
      final result = await processAlert(alertId, 'processed');
      return result['success'] == true;
    } catch (e) {
      debugPrint('标记告警已处理失败: $e');
      return false;
    }
  }
} 