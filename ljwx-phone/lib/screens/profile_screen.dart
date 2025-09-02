import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:ljwx_health_new/providers/ble_provider.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('个人资料'),
      ),
      body: Consumer<BLEProvider>(
        builder: (context, bleProvider, child) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const CircleAvatar(
                radius: 50,
                child: Icon(Icons.person, size: 50),
              ),
              const SizedBox(height: 16),
              const Text(
                '用户名',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 32),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.devices),
                  title: const Text('已连接设备'),
                  subtitle: Text(
                    bleProvider.connectedDevice?.name ?? '未连接',
                  ),
                  trailing: bleProvider.connectedDevice != null
                      ? IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: bleProvider.disconnectDevice,
                        )
                      : null,
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.settings),
                  title: const Text('设置'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: 实现设置功能
                  },
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.help),
                  title: const Text('帮助与反馈'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: 实现帮助功能
                  },
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.info),
                  title: const Text('关于'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: 实现关于功能
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