import 'package:flutter/material.dart';
import 'package:ljwx_health_new/widgets/ble_connection_widget.dart';
import '../global.dart';

class BluetoothSettingsScreen extends StatelessWidget {
  const BluetoothSettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // 如果上传方式为wifi，显示不可用提示
    if (uploadMethod == 'wifi') {
      return Scaffold(
        appBar: AppBar(
          title: const Text('蓝牙设置'),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.bluetooth_disabled, size: 80, color: Colors.grey),
              SizedBox(height: 16),
              Text(
                '蓝牙功能不可用',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text(
                '当前配置使用WiFi作为数据上传方式',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        ),
      );
    }
    
    // 正常显示蓝牙设置
    return Scaffold(
      appBar: AppBar(
        title: const Text('蓝牙设置'),
      ),
      body: const BleConnectionWidget(),
    );
  }
} 