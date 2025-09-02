import 'package:flutter/material.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/models/alert_model.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/api_service.dart';

class AlertDetailPage extends StatefulWidget {
  final Alert alert;
  final Function(String alertId) onMarkAsResponded;
  final Function(String alertId) onDelete;

  const AlertDetailPage({
    super.key,
    required this.alert,
    required this.onMarkAsResponded,
    required this.onDelete,
  });

  @override
  State<AlertDetailPage> createState() => _AlertDetailPageState();
}

class _AlertDetailPageState extends State<AlertDetailPage> {
  final ApiService _apiService = ApiService();
  String _physicalAddress = '';
  Map<String, dynamic>? _healthData;
  bool _isLoading = true;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    // 获取物理地址
    if (widget.alert.latitude != 0 && widget.alert.longitude != 0) {
      final address = await _apiService.getAddressFromCoordinates(
        widget.alert.latitude, 
        widget.alert.longitude
      );
      setState(() => _physicalAddress = address);
    }
    
    // 获取健康数据
    if (widget.alert.healthId.isNotEmpty) {
      final healthData = await _apiService.fetchHealthDataById(widget.alert.healthId);
      setState(() => _healthData = healthData);
    }
    
    setState(() => _isLoading = false);
  }

  // 处理告警
  Future<void> _handleMarkAsResponded() async {
    setState(() => _isProcessing = true);
    
    final success = await _apiService.dealAlert(widget.alert.alertId);
    
    setState(() => _isProcessing = false);
    
    if (success) {
      widget.onMarkAsResponded(widget.alert.alertId);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('标记告警失败，请稍后重试')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.alerts),
        elevation: 0,
        actions: [
          if (widget.alert.alertStatus == 'pending')
            IconButton(
              icon: const Icon(Icons.done_all),
              tooltip: "一键处理",
              onPressed: _isProcessing 
                ? null 
                : () {
                    _showConfirmationDialog(
                      context,
                      "确认已处理此告警？",
                      _handleMarkAsResponded,
                    );
                  },
            ),
          IconButton(
            icon: const Icon(Icons.delete),
            tooltip: AppText.delete,
            onPressed: () {
              _showConfirmationDialog(
                context,
                "确认删除这条告警？",
                () => widget.onDelete(widget.alert.alertId),
              );
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 告警标题
                  Text(
                    widget.alert.alertDesc,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // 告警元数据
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _buildChip(
                        context,
                        AppText.translateAlertLevel(widget.alert.severityLevel),
                        _getLevelColor(widget.alert.severityLevel),
                      ),
                      _buildChip(
                        context,
                        AppText.translateAlertType(widget.alert.alertType),
                        _getTypeColor(widget.alert.alertType),
                      ),
                      _buildChip(
                        context,
                        AppText.translateAlertStatus(widget.alert.alertStatus),
                        _getStatusColor(widget.alert.alertStatus),
                      ),
                    ],
                  ),
                  
                  // 时间和用户信息
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                "时间: ${widget.alert.alertTimestamp}",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: Colors.grey[600],
                                ),
                              ),
                            ),
                            Expanded(
                              child: Text(
                                "部门: ${widget.alert.deptName}",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: Colors.grey[600],
                                ),
                                textAlign: TextAlign.right,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                "用户: ${widget.alert.userName}",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: Colors.grey[600],
                                ),
                              ),
                            ),
                            Expanded(
                              child: Text(
                                "设备: ${widget.alert.deviceSn}",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: Colors.grey[600],
                                ),
                                textAlign: TextAlign.right,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        InkWell(
                          onTap: () {
                            // 健康ID点击处理
                            _openHealthDetail(context, widget.alert.healthId);
                          },
                          child: Row(
                            children: [
                              Text(
                                "健康ID: ",
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: Colors.grey[600],
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryColor.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: AppTheme.primaryColor.withOpacity(0.3),
                                    width: 1,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      widget.alert.healthId,
                                      style: theme.textTheme.bodySmall?.copyWith(
                                        color: AppTheme.primaryColor,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(width: 4),
                                    Icon(
                                      Icons.open_in_new,
                                      size: 12,
                                      color: AppTheme.primaryColor,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const Divider(height: 24),
                  
                  // 告警内容
                  Text(
                    widget.alert.alertDesc,
                    style: theme.textTheme.bodyLarge,
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 健康数据信息
                  if (_healthData != null)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 16),
                        Text(
                          "健康数据",
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Colors.blue.withOpacity(0.2),
                              width: 1,
                            ),
                          ),
                          child: _buildHealthDataContent(),
                        ),
                      ],
                    ),
                  
                  // 告警位置信息
                  if (widget.alert.latitude != 0 && widget.alert.longitude != 0)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 16),
                        Text(
                          "告警位置",
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.grey[200],
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Colors.grey[300]!,
                              width: 1,
                            ),
                          ),
                          child: Column(
                            children: [
                              Center(
                                child: Container(
                                  width: 300,
                                  height: 150,
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(16),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.1),
                                        blurRadius: 4,
                                        offset: const Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                  child: Stack(
                                    children: [
                                      Center(
                                        child: Icon(
                                          Icons.map,
                                          size: 50,
                                          color: Colors.grey[300],
                                        ),
                                      ),
                                      Center(
                                        child: Container(
                                          padding: const EdgeInsets.all(12),
                                          decoration: BoxDecoration(
                                            color: Colors.white,
                                            shape: BoxShape.circle,
                                            boxShadow: [
                                              BoxShadow(
                                                color: Colors.black.withOpacity(0.1),
                                                blurRadius: 4,
                                                offset: const Offset(0, 2),
                                              ),
                                            ],
                                          ),
                                          child: const Icon(
                                            Icons.location_on,
                                            color: Colors.red,
                                            size: 36,
                                          ),
                                        ),
                                      ),
                                      Positioned(
                                        bottom: 8,
                                        right: 8,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: AppTheme.primaryColor.withOpacity(0.1),
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                          child: Text(
                                            "查看地图",
                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                              color: AppTheme.primaryColor,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // 物理地址显示
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: Colors.grey[300]!,
                                    width: 1,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Icon(
                                      Icons.location_on_outlined,
                                      size: 18,
                                      color: Colors.red[400],
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        _physicalAddress.isNotEmpty 
                                            ? _physicalAddress 
                                            : "获取地址中...",
                                        style: theme.textTheme.bodyMedium?.copyWith(
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              
                              const SizedBox(height: 16),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  _buildLocationInfoItem(
                                    context, 
                                    Icons.place, 
                                    "纬度", 
                                    widget.alert.latitude.toStringAsFixed(6)
                                  ),
                                  const SizedBox(width: 24),
                                  _buildLocationInfoItem(
                                    context, 
                                    Icons.map, 
                                    "经度", 
                                    widget.alert.longitude.toStringAsFixed(6)
                                  ),
                                ],
                              ),
                              if (widget.alert.altitude != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 12),
                                  child: _buildLocationInfoItem(
                                    context, 
                                    Icons.height, 
                                    "海拔", 
                                    "${widget.alert.altitude!.toStringAsFixed(2)}米"
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  
                  const SizedBox(height: 32),
                  
                  // 处理按钮 - 底部固定
                  if (widget.alert.alertStatus == 'pending')
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.only(bottom: 24),
                      child: ElevatedButton.icon(
                        icon: _isProcessing 
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.check_circle),
                        label: Text(_isProcessing ? "处理中..." : "标记为已处理"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          disabledBackgroundColor: Colors.green.withOpacity(0.6),
                        ),
                        onPressed: _isProcessing 
                            ? null 
                            : () => _showConfirmationDialog(
                                context, 
                                "确认已处理此告警？", 
                                _handleMarkAsResponded
                              ),
                      ),
                    ),
                ],
              ),
            ),
    );
  }

  // 构建健康数据内容
  Widget _buildHealthDataContent() {
    if (_healthData == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 20),
          child: Text('暂无健康数据'),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_healthData!['heartRate'] != null)
          _buildHealthItem('心率', '${_healthData!['heartRate']} BPM', Icons.favorite, Colors.red),
        if (_healthData!['bloodOxygen'] != null)
          _buildHealthItem('血氧', '${_healthData!['bloodOxygen']}%', Icons.opacity, Colors.blue),
        if (_healthData!['temperature'] != null)
          _buildHealthItem('体温', '${_healthData!['temperature']}°C', Icons.thermostat, Colors.orange),
        if (_healthData!['pressureHigh'] != null && _healthData!['pressureLow'] != null)
          _buildHealthItem(
            '血压', 
            '${_healthData!['pressureHigh']}/${_healthData!['pressureLow']} mmHg', 
            Icons.speed, 
            Colors.purple
          ),
        if (_healthData!['step'] != null)
          _buildHealthItem('步数', '${_healthData!['step']} 步', Icons.directions_walk, Colors.green),
      ],
    );
  }

  // 构建健康数据项
  Widget _buildHealthItem(String label, String value, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              icon,
              size: 20,
              color: color,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  // 打开健康详情
  void _openHealthDetail(BuildContext context, String healthId) {
    Navigator.of(context).pushNamed('/health/detail', arguments: {'healthId': healthId});
  }
  
  // 构建标签
  Widget _buildChip(BuildContext context, String label, Color backgroundColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: backgroundColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: backgroundColor.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: backgroundColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
  
  // 根据告警级别获取颜色
  Color _getLevelColor(String level) {
    switch (level) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }
  
  // 根据告警类型获取颜色
  Color _getTypeColor(String type) {
    switch (type) {
      case 'fall_down':
        return Colors.indigo;
      case 'one_key_alarm':
        return Colors.deepPurple;
      case 'sleep':
        return Colors.teal;
      case 'heart_rate':
        return Colors.red;
      case 'blood_oxygen':
        return Colors.lightBlue;
      case 'temperature':
        return Colors.orange;
      case 'blood_pressure':
        return Colors.purple;
      case 'activity':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
  
  // 根据告警状态获取颜色
  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'responded':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
  
  // 显示确认对话框
  void _showConfirmationDialog(
    BuildContext context,
    String message,
    VoidCallback onConfirm,
  ) {
    showDialog(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: Text(AppText.confirm),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
              },
              child: Text(AppText.cancel),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                onConfirm();
              },
              child: Text(AppText.confirm),
              style: TextButton.styleFrom(
                foregroundColor: Colors.red,
              ),
            ),
          ],
        );
      },
    );
  }

  // 构建位置信息项
  Widget _buildLocationInfoItem(
    BuildContext context, 
    IconData icon, 
    String label, 
    String value
  ) {
    return Column(
      children: [
        Icon(
          icon,
          size: 18,
          color: Colors.grey[600],
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
} 