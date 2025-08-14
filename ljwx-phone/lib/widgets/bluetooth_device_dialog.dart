import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:ljwx_health_new/services/bluetooth_service.dart';

class BluetoothDeviceDialog extends StatefulWidget {
  const BluetoothDeviceDialog({super.key});

  @override
  State<BluetoothDeviceDialog> createState() => _BluetoothDeviceDialogState();
}

class _BluetoothDeviceDialogState extends State<BluetoothDeviceDialog> {
  final BluetoothService _bluetoothService = BluetoothService();
  List<BluetoothDevice> _devices = [];
  bool _isScanning = false;

  @override
  void initState() {
    super.initState();
    _startScanning();
  }

  @override
  void dispose() {
    _bluetoothService.stopScanning();
    super.dispose();
  }

  Future<void> _startScanning() async {
    setState(() {
      _isScanning = true;
      _devices.clear();
    });

    final devices = await _bluetoothService.scanForDevices();
    setState(() {
      _devices = devices;
      _isScanning = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('选择蓝牙设备'),
      content: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_isScanning)
              const Center(
                child: CircularProgressIndicator(),
              )
            else if (_devices.isEmpty)
              const Center(
                child: Text('未发现设备'),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                itemCount: _devices.length,
                itemBuilder: (context, index) {
                  final device = _devices[index];
                  return ListTile(
                    leading: const Icon(Icons.bluetooth),
                    title: Text(device.name ?? '未知设备'),
                    subtitle: Text(device.address),
                    onTap: () {
                      Navigator.of(context).pop(device);
                    },
                  );
                },
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _startScanning,
          child: const Text('重新扫描'),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
      ],
    );
  }
} 