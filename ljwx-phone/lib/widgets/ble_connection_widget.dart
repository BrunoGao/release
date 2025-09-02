import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ble_provider.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'dart:async';
import 'info_card.dart';
import '../services/bluetooth_service.dart';

class BleConnectionWidget extends StatefulWidget {
  const BleConnectionWidget({Key? key}) : super(key: key);

  @override
  State<BleConnectionWidget> createState() => _BleConnectionWidgetState();
}

class _BleConnectionWidgetState extends State<BleConnectionWidget> with WidgetsBindingObserver {
  Timer? _reconnectTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startReconnectTimer();
  }

  @override
  void dispose() {
    _reconnectTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startReconnectTimer();
    } else {
      _reconnectTimer?.cancel();
    }
  }

  void _startReconnectTimer() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      final bleProvider = Provider.of<BleProvider>(context, listen: false);
      bleProvider.autoReconnect();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<BleProvider>(
      builder: (context, bleProvider, child) {
        return Padding(
          padding: const EdgeInsets.all(12),
          child: ListView(
            children: [
              _buildDeviceStatus(bleProvider),
              const SizedBox(height: 16),
              if (bleProvider.isConnected) _buildHealthOverview(bleProvider),
              const SizedBox(height: 16),
              ..._buildDeviceList(bleProvider),
              const SizedBox(height: 16),
              _buildLogSection(bleProvider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDeviceStatus(BleProvider bleProvider) {
    return InfoCard(
      icon: Icons.bluetooth,
      title: '蓝牙设备',
      subtitle: bleProvider.isConnected
          ? '已连接: ${bleProvider.connectedDevice?.name ?? "未知设备"}'
          : '未连接',
      color: bleProvider.isConnected ? Colors.green.shade50 : Colors.grey.shade50,
      onTap: bleProvider.isConnected
          ? () => bleProvider.disconnect()
          : () => bleProvider.startScan(),
    );
  }

  Widget _buildHealthOverview(BleProvider bleProvider) {
    final data = bleProvider.lastHealthData;
    if (data.isEmpty) return const SizedBox.shrink();

    return SizedBox(
      height: 150,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          const SizedBox(width: 8),
          InfoCard(
            color: Colors.red.shade50,
            icon: Icons.favorite,
            title: '心率',
            subtitle: '${data['heart_rate'] ?? 0} bpm',
          ),
          const SizedBox(width: 8),
          InfoCard(
            color: Colors.blue.shade50,
            icon: Icons.bloodtype,
            title: '血氧',
            subtitle: '${data['blood_oxygen'] ?? 0}%',
          ),
          const SizedBox(width: 8),
          InfoCard(
            color: Colors.orange.shade50,
            icon: Icons.thermostat,
            title: '体温',
            subtitle: '${data['body_temperature'] ?? 0}°C',
          ),
          const SizedBox(width: 8),
          InfoCard(
            color: Colors.green.shade50,
            icon: Icons.directions_walk,
            title: '步数',
            subtitle: '${data['step'] ?? 0}',
          ),
          const SizedBox(width: 8),
        ],
      ),
    );
  }

  List<Widget> _buildDeviceList(BleProvider bleProvider) {
    if (bleProvider.scanResults.isEmpty) {
      return [const Center(child: Text('未发现设备，请点击扫描按钮'))];
    }
    return bleProvider.scanResults
      .where((r) => r.device.name.startsWith('HUAWEI WATCH'))
      .map((result) {
        final device = result.device;
        return InfoCard(
          icon: Icons.watch,
          title: device.name.isNotEmpty ? device.name : '未知设备',
          subtitle: device.id.toString(),
          onTap: () => bleProvider.connectToDevice(device),
        );
      }).toList();
  }

  Widget _buildLogSection(BleProvider bleProvider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          child: Text(
            '蓝牙日志',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        Container(
          height: 150,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: ListView.builder(
            reverse: true,
            itemCount: bleProvider.bleLogs.length,
            itemBuilder: (context, index) {
              final log = bleProvider.bleLogs[bleProvider.bleLogs.length - 1 - index];
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text(
                  log,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              );
            },
          ),
        ),
        SizedBox(
          height: 120,
          child: StreamBuilder<String>(
            stream: BleSvc.i.logStream,
            builder: (context, snapshot) {
              if (!snapshot.hasData) return const SizedBox();
              return SingleChildScrollView(
                child: Text(
                  snapshot.data!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.blue),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
} 