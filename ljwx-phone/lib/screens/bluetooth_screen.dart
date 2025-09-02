import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:ljwx_health_new/providers/ble_provider.dart';

class DeviceScreen extends StatelessWidget {
  const DeviceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('设备连接'),
      ),
      body: Consumer<BLEProvider>(
        builder: (context, bleProvider, child) {
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: ElevatedButton(
                  onPressed: bleProvider.isScanning
                      ? bleProvider.stopScan
                      : bleProvider.startScan,
                  child: Text(
                    bleProvider.isScanning ? '停止扫描' : '开始扫描',
                  ),
                ),
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: bleProvider.scanResults.length,
                  itemBuilder: (context, index) {
                    final result = bleProvider.scanResults[index];
                    return ListTile(
                      title: Text(result.device.name.isEmpty
                          ? '未知设备'
                          : result.device.name),
                      subtitle: Text(result.device.id.toString()),
                      trailing: ElevatedButton(
                        onPressed: () {
                          bleProvider.connectToDevice(result.device);
                        },
                        child: const Text('连接'),
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
} 