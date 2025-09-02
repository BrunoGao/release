import 'package:flutter/material.dart';
import 'package:ljwx_health_new/services/bluetooth_service.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:provider/provider.dart';
import '../global.dart';

class BluetoothStatusIcon extends StatelessWidget {
  final double size;
  final VoidCallback? onTap;

  const BluetoothStatusIcon({
    Key? key,
    this.size = 24.0,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // 如果上传方式为wifi，显示不可用状态
    if (uploadMethod == 'wifi') {
      return Tooltip(
        message: '蓝牙未激活 (使用WiFi模式)',
        child: Container(
          padding: const EdgeInsets.all(8.0),
          child: Icon(
            Icons.bluetooth_disabled_rounded,
            color: Colors.grey,
            size: size,
          ),
        ),
      );
    }
    
    return StreamBuilder<String>(
      stream: BleSvc.i.bluetoothIconStateStream,
      builder: (context, snapshot) {
        final bluetoothState = snapshot.data ?? 'disconnected';
        return InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.all(8.0),
            child: _buildBluetoothIcon(context, bluetoothState),
          ),
        );
      },
    );
  }

  Widget _buildBluetoothIcon(BuildContext context, String state) {
    // 根据状态选择图标和颜色
    IconData iconData;
    Color iconColor = BleSvc.i.getBluetoothIconColor(context);
    String tooltipText;
    
    switch (state) {
      case 'disconnected':
        iconData = Icons.bluetooth_disabled_rounded;
        tooltipText = '蓝牙已断开';
        break;
      case 'inactive':
        iconData = Icons.bluetooth_rounded;
        tooltipText = '蓝牙未激活 (使用WiFi模式)';
        break;
      case 'connected':
        iconData = Icons.bluetooth_connected_rounded;
        tooltipText = '蓝牙已连接，等待数据';
        break;
      case 'transmitting':
        iconData = Icons.bluetooth_connected_rounded;
        tooltipText = '蓝牙数据传输中';
        break;
      default:
        iconData = Icons.bluetooth_rounded;
        tooltipText = '蓝牙状态未知';
        iconColor = Colors.amber;
    }

    return Tooltip(
      message: tooltipText,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        transitionBuilder: (Widget child, Animation<double> animation) {
          return ScaleTransition(scale: animation, child: child);
        },
        child: Icon(
          iconData,
          key: ValueKey<String>(state),
          color: iconColor,
          size: size,
        ),
      ),
    );
  }
} 