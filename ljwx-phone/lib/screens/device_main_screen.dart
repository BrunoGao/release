import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/widgets/enterprise_main_layout.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:flutter_animate/flutter_animate.dart';

class DeviceMainScreen extends StatefulWidget {
  final login.LoginData loginData;

  const DeviceMainScreen({
    super.key,
    required this.loginData,
  });

  @override
  State<DeviceMainScreen> createState() => _DeviceMainScreenState();
}

class _DeviceMainScreenState extends State<DeviceMainScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = true;
  String? _error;
  List<Map<String, dynamic>>? _devices;
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fetchDevices();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _fetchDevices() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      // TODO: 实现设备数据获取逻辑
      await Future.delayed(const Duration(seconds: 1)); // 模拟网络请求
      
      // 模拟设备数据
      _devices = [
        {
          'id': 'watch001',
          'name': '健康手表 Pro',
          'type': 'smartwatch',
          'status': 'connected',
          'battery': 85,
          'lastSync': '2分钟前',
          'serialNumber': 'SW2024001',
          'firmwareVersion': '2.1.5',
          'features': ['心率监测', '血氧检测', '运动追踪', 'GPS定位'],
        },
        {
          'id': 'sensor001',
          'name': '环境传感器',
          'type': 'sensor',
          'status': 'connected',
          'battery': 92,
          'lastSync': '5分钟前',
          'serialNumber': 'ES2024001',
          'firmwareVersion': '1.3.2',
          'features': ['温度检测', '湿度检测', '空气质量'],
        },
        {
          'id': 'emergency001',
          'name': 'SOS紧急按钮',
          'type': 'emergency',
          'status': 'standby',
          'battery': 78,
          'lastSync': '1小时前',
          'serialNumber': 'SOS2024001',
          'firmwareVersion': '1.0.8',
          'features': ['一键求救', 'GPS定位', '双向通话'],
        },
      ];

      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        _animationController.forward();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return EnterpriseMainLayout(
      title: '设备管理',
      loginData: widget.loginData,
      currentRoute: '/device',
      showSearchBar: true,
      searchHint: '搜索设备名称、序列号...',
      onSearchChanged: (value) {
        // TODO: 实现设备搜索
        print('搜索设备: $value');
      },
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddDeviceDialog,
        icon: const Icon(Icons.add),
        label: const Text('添加设备'),
        backgroundColor: AppTheme.primaryColor,
      ),
      child: _buildContent(),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('正在加载设备信息...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _fetchDevices,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (_devices?.isEmpty ?? true) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.devices_other,
              size: 80,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            const Text(
              '暂无设备',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              '点击右下角按钮添加设备',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchDevices,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDeviceStats(),
            const SizedBox(height: 24),
            const Text(
              '我的设备',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...(_devices ?? []).asMap().entries.map((entry) {
              final index = entry.key;
              final device = entry.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _buildDeviceCard(device, index),
              );
            }),
            const SizedBox(height: 80), // 为FloatingActionButton留出空间
          ],
        ),
      ),
    );
  }

  Widget _buildDeviceStats() {
    final connectedCount = _devices?.where((d) => d['status'] == 'connected').length ?? 0;
    final totalCount = _devices?.length ?? 0;
    
    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            '在线设备',
            connectedCount.toString(),
            Icons.wifi,
            Colors.green,
            0,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            '设备总数',
            totalCount.toString(),
            Icons.devices,
            AppTheme.primaryColor,
            1,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            '离线设备',
            (totalCount - connectedCount).toString(),
            Icons.wifi_off,
            Colors.orange,
            2,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(
    String title,
    String value,
    IconData icon,
    Color color,
    int index,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              color.withOpacity(0.1),
              color.withOpacity(0.05),
            ],
          ),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              title,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);
  }

  Widget _buildDeviceCard(Map<String, dynamic> device, int index) {
    final statusColor = _getStatusColor(device['status']);
    final statusText = _getStatusText(device['status']);
    final deviceIcon = _getDeviceIcon(device['type']);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _showDeviceDetails(device),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      deviceIcon,
                      color: AppTheme.primaryColor,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          device['name'],
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '序列号: ${device['serialNumber']}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: statusColor.withOpacity(0.3),
                          ),
                        ),
                        child: Text(
                          statusText,
                          style: TextStyle(
                            fontSize: 12,
                            color: statusColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.battery_std,
                            size: 16,
                            color: _getBatteryColor(device['battery']),
                          ),
                          const SizedBox(width: 2),
                          Text(
                            '${device['battery']}%',
                            style: TextStyle(
                              fontSize: 12,
                              color: _getBatteryColor(device['battery']),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '固件版本',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                        Text(
                          device['firmwareVersion'],
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '最后同步',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                        Text(
                          device['lastSync'],
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: (device['features'] as List<String>).map((feature) {
                  return Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      feature,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton.icon(
                    onPressed: () => _showDeviceSettings(device),
                    icon: const Icon(Icons.settings, size: 16),
                    label: const Text('设置'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppTheme.primaryColor,
                      textStyle: const TextStyle(fontSize: 12),
                    ),
                  ),
                  const SizedBox(width: 8),
                  TextButton.icon(
                    onPressed: () => _syncDevice(device),
                    icon: const Icon(Icons.sync, size: 16),
                    label: const Text('同步'),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.blue,
                      textStyle: const TextStyle(fontSize: 12),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    ).animate().fadeIn(duration: 500.ms, delay: ((index + 3) * 100).ms)
     .slideX(begin: 0.1, end: 0, duration: 500.ms, delay: ((index + 3) * 100).ms);
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'connected':
        return Colors.green;
      case 'standby':
        return Colors.orange;
      case 'disconnected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getStatusText(String status) {
    switch (status) {
      case 'connected':
        return '已连接';
      case 'standby':
        return '待机';
      case 'disconnected':
        return '已断开';
      default:
        return '未知';
    }
  }

  IconData _getDeviceIcon(String type) {
    switch (type) {
      case 'smartwatch':
        return Icons.watch;
      case 'sensor':
        return Icons.sensors;
      case 'emergency':
        return Icons.emergency;
      default:
        return Icons.device_unknown;
    }
  }

  Color _getBatteryColor(int battery) {
    if (battery > 60) return Colors.green;
    if (battery > 30) return Colors.orange;
    return Colors.red;
  }

  void _showDeviceDetails(Map<String, dynamic> device) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.8,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        builder: (context, scrollController) => _buildDeviceDetailSheet(
          device,
          scrollController,
        ),
      ),
    );
  }

  Widget _buildDeviceDetailSheet(
    Map<String, dynamic> device,
    ScrollController scrollController,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(
                _getDeviceIcon(device['type']),
                size: 32,
                color: AppTheme.primaryColor,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      device['name'],
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      device['serialNumber'],
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView(
              controller: scrollController,
              children: [
                const Text(
                  '设备信息',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                _buildInfoRow('状态', _getStatusText(device['status'])),
                _buildInfoRow('电池', '${device['battery']}%'),
                _buildInfoRow('固件版本', device['firmwareVersion']),
                _buildInfoRow('最后同步', device['lastSync']),
                const SizedBox(height: 24),
                const Text(
                  '功能特性',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                ...(device['features'] as List<String>).map((feature) {
                  return ListTile(
                    leading: Icon(
                      Icons.check_circle,
                      color: Colors.green,
                      size: 20,
                    ),
                    title: Text(feature),
                    contentPadding: EdgeInsets.zero,
                    minLeadingWidth: 24,
                  );
                }),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      _showDeviceSettings(device);
                    },
                    icon: const Icon(Icons.settings),
                    label: const Text('设备设置'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryColor,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.all(16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  void _showDeviceSettings(Map<String, dynamic> device) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${device['name']} 设置'),
        content: const Text('设备设置功能开发中...'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  void _syncDevice(Map<String, dynamic> device) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('正在同步 ${device['name']}...'),
        duration: const Duration(seconds: 2),
      ),
    );
    // TODO: 实现设备同步逻辑
  }

  void _showAddDeviceDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('添加设备'),
        content: const Text('设备添加功能开发中...'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }
}