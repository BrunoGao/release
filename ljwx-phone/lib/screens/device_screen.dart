import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/device_model.dart' as device;
import 'package:flutter_animate/flutter_animate.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:go_router/go_router.dart';

class DeviceScreen extends StatelessWidget {
  final device.Device device;

  const DeviceScreen({
    Key? key,
    required this.device,
  }) : super(key: key);

  String _getStatusText(String status) {
    switch (status.toUpperCase()) {
      case 'ACTIVE':
        return '在线';
      case 'INACTIVE':
        return '离线';
      default:
        return '未知';
    }
  }

  String _getChargingStatusText(String status) {
    switch (status.toUpperCase()) {
      case 'CHARGING':
        return '充电中';
      case 'NOT_CHARGING':
        return '未充电';
      default:
        return '未知';
    }
  }

  String _getWearableStatusText(String status) {
    switch (status.toUpperCase()) {
      case 'WORN':
        return '已佩戴';
      case 'NOT_WORN':
        return '未佩戴';
      default:
        return '未知';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('设备信息'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ListTile(
                      title: const Text('设备序列号'),
                      subtitle: Text(device.serialNumber),
                    ),
                    ListTile(
                      title: const Text('蓝牙地址'),
                      subtitle: Text(device.bluetoothAddress),
                    ),
                    ListTile(
                      title: const Text('电池电量'),
                      subtitle: Text(device.batteryLevel),
                    ),
                    ListTile(
                      title: const Text('设备状态'),
                      subtitle: Text(_getStatusText(device.status)),
                    ),
                    ListTile(
                      title: const Text('充电状态'),
                      subtitle: Text(_getChargingStatusText(device.chargingStatus)),
                    ),
                    ListTile(
                      title: const Text('佩戴状态'),
                      subtitle: Text(_getWearableStatusText(device.wearableStatus)),
                    ),
                    ListTile(
                      title: const Text('系统版本'),
                      subtitle: Text(device.systemSoftwareVersion),
                    ),
                    ListTile(
                      title: const Text('最后更新时间'),
                      subtitle: Text(device.updateTime),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
} 