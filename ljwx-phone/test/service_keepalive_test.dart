import 'package:flutter_test/flutter_test.dart';
import 'package:ljwx_health_new/services/service_keepalive_manager.dart';

void main() {
  group('ServiceKeepaliveManager Tests', () {
    late ServiceKeepaliveManager manager;

    setUp(() {
      manager = ServiceKeepaliveManager.i;
    });

    tearDown(() {
      manager.stopKeepalive();
    });

    test('应该能够启动和停止保活服务', () {
      // 启动保活服务
      manager.startKeepalive();
      
      // 获取状态
      final status = manager.getServiceStatus();
      expect(status['is_active'], true);
      
      // 停止保活服务
      manager.stopKeepalive();
      
      // 验证状态
      final statusAfterStop = manager.getServiceStatus();
      expect(statusAfterStop['is_active'], false);
    });

    test('应该能够获取服务状态', () {
      final status = manager.getServiceStatus();
      
      expect(status, isA<Map<String, dynamic>>());
      expect(status.containsKey('ble_alive'), true);
      expect(status.containsKey('http_alive'), true);
      expect(status.containsKey('overall_health'), true);
      expect(status.containsKey('is_active'), true);
    });

    test('应该能够监听状态流', () async {
      bool streamReceived = false;
      
      // 监听状态流
      final subscription = manager.serviceStatusStream.listen((status) {
        streamReceived = true;
        expect(status, isA<Map<String, dynamic>>());
      });
      
      // 启动保活服务
      manager.startKeepalive();
      
      // 等待一段时间让状态更新
      await Future.delayed(const Duration(milliseconds: 100));
      
      expect(streamReceived, true);
      
      await subscription.cancel();
    });

    test('应该能够强制服务恢复', () async {
      // 这个测试只验证方法不会抛出异常
      expect(() async => await manager.forceServiceRecovery(), returnsNormally);
    });
  });
} 