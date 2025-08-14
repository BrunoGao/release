import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'package:provider/provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:ljwx_health_new/providers/ble_provider.dart';
import 'package:ljwx_health_new/routes/app_router.dart';
import 'package:ljwx_health_new/providers/theme_provider.dart';
import 'package:ljwx_health_new/services/bluetooth_service.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/global.dart';
import 'package:ljwx_health_new/widgets/global_notification.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 设置系统UI
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarBrightness: Brightness.light,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);
  
  try {
    print('Requesting permissions...'); // Debug log
    final permissionsGranted = await requestPermissions();
    print('Permissions granted: $permissionsGranted'); // Debug log
    
    if (!permissionsGranted) {
      print('Some permissions were denied'); // Debug log
    }
  } catch (e) {
    print('Error requesting permissions: $e'); // Debug log
  }
  
  runApp(const MyApp());
}

Future<bool> requestPermissions() async {
  try {
  // 请求蓝牙权限
    final bluetoothStatus = await Permission.bluetooth.request();
    final bluetoothScanStatus = await Permission.bluetoothScan.request();
    final bluetoothConnectStatus = await Permission.bluetoothConnect.request();
    final bluetoothAdvertiseStatus = await Permission.bluetoothAdvertise.request();
  
    // 请求位置权限
    final locationStatus = await Permission.location.request();
    final locationWhenInUseStatus = await Permission.locationWhenInUse.request();
  
    // 请求通知权限
    final notificationStatus = await Permission.notification.request();
    
    // 检查所有权限是否都已授予
    final allGranted = [
      bluetoothStatus,
      bluetoothScanStatus,
      bluetoothConnectStatus,
      bluetoothAdvertiseStatus,
      locationStatus,
      locationWhenInUseStatus,
      notificationStatus,
    ].every((status) => status.isGranted);
    
    print('Permission status:'); // Debug log
    print('- Bluetooth: $bluetoothStatus');
    print('- Bluetooth Scan: $bluetoothScanStatus');
    print('- Bluetooth Connect: $bluetoothConnectStatus');
    print('- Bluetooth Advertise: $bluetoothAdvertiseStatus');
    print('- Location: $locationStatus');
    print('- Location When In Use: $locationWhenInUseStatus');
    print('- Notification: $notificationStatus');
    
    return allGranted;
  } catch (e) {
    print('Error requesting permissions: $e'); // Debug log
    return false;
  }
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> with WidgetsBindingObserver {
  static bool _isInBackground = false; // 应用后台状态标记
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    switch (state) {
      case AppLifecycleState.resumed:
        print('应用进入前台');
        _isInBackground = false;
        // 应用回到前台，恢复数据获取
        AppLifecycleManager.onAppResumed();
        break;
      case AppLifecycleState.paused:
        print('应用进入后台');
        _isInBackground = true;
        // 应用进入后台，暂停数据获取但保持蓝牙服务
        AppLifecycleManager.onAppPaused();
        break;
      case AppLifecycleState.inactive:
        print('应用变为非活跃状态');
        break;
      case AppLifecycleState.detached:
        print('应用即将终止');
        AppLifecycleManager.onAppDetached();
        break;
      case AppLifecycleState.hidden:
        print('应用被隐藏');
        break;
    }
  }

  // 静态方法供其他组件检查应用状态
  static bool get isInBackground => _isInBackground;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => BleProvider()),
        Provider<BleSvc>.value(value: BleSvc.i),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, child) {
          return MaterialApp.router(
            title: customerName,
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: themeProvider.isDarkMode ? ThemeMode.dark : ThemeMode.light,
            routerConfig: AppRouter.router,
            builder: (context, child) {
              return GlobalNotification(
                child: ErrorListener(child: child!),
              );
            },
          );
        },
      ),
    );
  }
}

// 全局错误监听组件
class ErrorListener extends StatefulWidget {
  final Widget child;
  
  const ErrorListener({super.key, required this.child});
  
  @override
  State<ErrorListener> createState() => _ErrorListenerState();
}

class _ErrorListenerState extends State<ErrorListener> {
  late final StreamSubscription _errorSubscription;
  
  @override
  void initState() {
    super.initState();
    // 订阅全局错误流
    _errorSubscription = GlobalEvents.i.errorStream.listen(_showErrorDialog);
  }
  
  void _showErrorDialog(Map<String, String> error) {
    final scaffold = ScaffoldMessenger.of(context);
    scaffold.showSnackBar(
      SnackBar(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.error_outline_rounded, 
                    color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Text(error['title'] ?? '错误', 
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  )),
              ],
            ),
            const SizedBox(height: 4),
            Text(error['message'] ?? '发生未知错误',
              style: const TextStyle(fontSize: 14)),
          ],
        ),
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppTheme.errorColor,
        margin: const EdgeInsets.all(12),
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: '了解',
          textColor: Colors.white,
          onPressed: () => scaffold.hideCurrentSnackBar(),
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    _errorSubscription.cancel();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}

// 应用生命周期管理器 #后台状态管理
class AppLifecycleManager {
  static void onAppResumed() {
    print('恢复数据获取');
    ApiService.resumeDataFetching(); // 恢复API数据获取
  }

  static void onAppPaused() {
    print('暂停数据获取，保持蓝牙服务');
    ApiService.pauseDataFetching(); // 暂停API数据获取以节省电量和流量
    // 蓝牙服务会自动保持运行
  }

  static void onAppDetached() {
    print('应用即将终止');
    // 应用终止时的清理工作
  }
}
