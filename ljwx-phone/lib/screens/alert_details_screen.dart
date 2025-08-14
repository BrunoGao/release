import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/alert_model.dart' as alert_model;
import 'package:fl_chart/fl_chart.dart';
import 'package:ljwx_health_new/constants/app_text.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/api_service.dart';

class AlertDetailsScreen extends StatefulWidget {
  final alert_model.AlertInfo alertInfo;

  const AlertDetailsScreen({
    super.key,
    required this.alertInfo,
  });

  @override
  State<AlertDetailsScreen> createState() => _AlertDetailsScreenState();
}

class _AlertDetailsScreenState extends State<AlertDetailsScreen> {
  final ScrollController _scrollController = ScrollController();
  late List<alert_model.Alert> _filteredAlerts;
  String? _selectedStatus;
  String? _selectedType;
  String? _selectedLevel;
  bool _showScrollButtons = false;

  @override
  void initState() {
    super.initState();
    _filteredAlerts = List.from(widget.alertInfo.alerts);
    _scrollController.addListener(_scrollListener);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_scrollListener);
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollListener() {
    if (_scrollController.position.pixels > 300 && !_showScrollButtons) {
      setState(() {
        _showScrollButtons = true;
      });
    } else if (_scrollController.position.pixels <= 300 && _showScrollButtons) {
      setState(() {
        _showScrollButtons = false;
      });
    }
  }

  void _scrollToTop() {
    _scrollController.animateTo(
      0,
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeInOut,
    );
  }

  void _scrollToBottom() {
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeInOut,
    );
  }

  void _applyFilters() {
    setState(() {
      _filteredAlerts = widget.alertInfo.alerts.where((alert) {
        bool matchesStatus = _selectedStatus == null || alert.alertStatus == _selectedStatus;
        bool matchesType = _selectedType == null || alert.alertType == _selectedType;
        bool matchesLevel = _selectedLevel == null || alert.severityLevel == _selectedLevel;
        return matchesStatus && matchesType && matchesLevel;
      }).toList();
    });
  }

  void _resetFilters() {
    setState(() {
      _selectedStatus = null;
      _selectedType = null;
      _selectedLevel = null;
      _filteredAlerts = List.from(widget.alertInfo.alerts);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(AppText.alerts),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () => _showFilterDialog(context),
          ),
        ],
      ),
      body: Column(
        children: [
          // 告警总数和过滤器指示器
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Row(
              children: [
                Text(
                  AppText.totalAlerts(_filteredAlerts.length),
                  style: theme.textTheme.titleMedium,
                ),
                const Spacer(),
                if (_selectedStatus != null || _selectedType != null || _selectedLevel != null)
                  _buildFilterChip(),
              ],
            ),
          ),
          
          // 水平过滤器选择
          if (widget.alertInfo.alerts.isNotEmpty)
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  _buildFilterDropdown(
                    '状态',
                    _selectedStatus,
                    widget.alertInfo.alertStatusCount.keys.toList(),
                    (value) {
                      setState(() {
                        _selectedStatus = value;
                        _applyFilters();
                      });
                    },
                    labelBuilder: (val) => AppText.translateAlertStatus(val),
                  ),
                  const SizedBox(width: 8),
                  _buildFilterDropdown(
                    '类型',
                    _selectedType,
                    widget.alertInfo.alertTypeCount.keys.toList(),
                    (value) {
                      setState(() {
                        _selectedType = value;
                        _applyFilters();
                      });
                    },
                    labelBuilder: (val) => AppText.translateAlertType(val),
                  ),
                  const SizedBox(width: 8),
                  _buildFilterDropdown(
                    '等级',
                    _selectedLevel,
                    widget.alertInfo.alertLevelCount.keys.toList(),
                    (value) {
                      setState(() {
                        _selectedLevel = value;
                        _applyFilters();
                      });
                    },
                    labelBuilder: (val) => AppText.translateAlertLevel(val),
                  ),
                  if (_selectedStatus != null || _selectedType != null || _selectedLevel != null)
                    TextButton.icon(
                      onPressed: _resetFilters,
                      icon: const Icon(Icons.clear, size: 16),
                      label: const Text('清除'),
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.grey[600],
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                      ),
                    ),
                ],
              ),
            ),
          
          // 告警列表
          Expanded(
            child: _filteredAlerts.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.info_outline, size: 48, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        Text(
                          "没有找到匹配的告警",
                          style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
                        ),
                        if (_selectedStatus != null || _selectedType != null || _selectedLevel != null)
                          TextButton(
                            onPressed: _resetFilters,
                            child: const Text("清除筛选条件"),
                          ),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _filteredAlerts.length,
                    itemBuilder: (context, index) => _buildAlertCard(context, _filteredAlerts[index], index % 2 == 0),
                  ),
          ),
        ],
      ),
      floatingActionButton: _showScrollButtons
          ? Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                FloatingActionButton(
                  heroTag: "btnTop",
                  mini: true,
                  onPressed: _scrollToTop,
                  backgroundColor: AppTheme.primaryColor,
                  foregroundColor: Colors.white,
                  child: const Icon(Icons.arrow_upward),
                ),
                const SizedBox(height: 8),
                FloatingActionButton(
                  heroTag: "btnBottom",
                  mini: true,
                  onPressed: _scrollToBottom,
                  backgroundColor: AppTheme.primaryColor,
                  foregroundColor: Colors.white,
                  child: const Icon(Icons.arrow_downward),
                ),
              ],
            )
          : null,
    );
  }

  Widget _buildFilterChip() {
    return InkWell(
      onTap: () => _showFilterDialog(context),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.primaryColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppTheme.primaryColor.withOpacity(0.5),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.filter_list,
              size: 16,
              color: AppTheme.primaryColor,
            ),
            const SizedBox(width: 4),
            Text(
              "已筛选",
              style: TextStyle(
                color: AppTheme.primaryColor,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterDropdown(
    String label,
    String? selectedValue,
    List<String> items,
    Function(String?) onChanged,
    {String Function(String)? labelBuilder}
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: selectedValue,
          hint: Text(label),
          icon: const Icon(Icons.arrow_drop_down, size: 18),
          style: TextStyle(
            color: Colors.grey[800],
            fontSize: 14,
          ),
          onChanged: onChanged,
          items: items.map((item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(
                labelBuilder != null ? labelBuilder(item) : item,
                style: TextStyle(
                  color: selectedValue == item ? AppTheme.primaryColor : Colors.grey[800],
                  fontWeight: selectedValue == item ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showFilterDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text("筛选告警"),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("告警状态"),
                _buildFilterOptions(
                  "alertStatus",
                  widget.alertInfo.alertStatusCount,
                  _selectedStatus,
                  (val) {
                    setState(() {
                      _selectedStatus = val;
                      _applyFilters();
                    });
                    Navigator.pop(context);
                  },
                  labelBuilder: (val) => AppText.translateAlertStatus(val),
                ),
                const SizedBox(height: 16),
                const Text("告警类型"),
                _buildFilterOptions(
                  "alertType",
                  widget.alertInfo.alertTypeCount,
                  _selectedType,
                  (val) {
                    setState(() {
                      _selectedType = val;
                      _applyFilters();
                    });
                    Navigator.pop(context);
                  },
                  labelBuilder: (val) => AppText.translateAlertType(val),
                ),
                const SizedBox(height: 16),
                const Text("告警等级"),
                _buildFilterOptions(
                  "alertLevel",
                  widget.alertInfo.alertLevelCount,
                  _selectedLevel,
                  (val) {
                    setState(() {
                      _selectedLevel = val;
                      _applyFilters();
                    });
                    Navigator.pop(context);
                  },
                  labelBuilder: (val) => AppText.translateAlertLevel(val),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text("取消"),
            ),
            TextButton(
              onPressed: () {
                _resetFilters();
                Navigator.pop(context);
              },
              child: const Text("清除筛选"),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFilterOptions(
    String groupName,
    Map<String, int> options,
    String? selectedValue,
    Function(String?) onChanged,
    {String Function(String)? labelBuilder}
  ) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: options.entries.map((entry) {
        final selected = selectedValue == entry.key;
        return FilterChip(
          label: Text(
            labelBuilder != null 
                ? "${labelBuilder(entry.key)} (${entry.value})" 
                : "${entry.key} (${entry.value})"
          ),
          selected: selected,
          onSelected: (isSelected) {
            onChanged(isSelected ? entry.key : null);
          },
          backgroundColor: Colors.grey[200],
          selectedColor: AppTheme.primaryColor.withOpacity(0.2),
          checkmarkColor: AppTheme.primaryColor,
          labelStyle: TextStyle(
            color: selected ? AppTheme.primaryColor : Colors.grey[800],
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
          ),
        );
      }).toList(),
    );
  }

  Widget _buildAlertCard(BuildContext context, alert_model.Alert alert, bool isEven) {
    final theme = Theme.of(context);
    
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 2,
      color: isEven ? Colors.grey[50] : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: alert.alertStatus == 'pending' 
            ? BorderSide(color: Colors.orange.withOpacity(0.5), width: 1.5)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: () => _showAlertDetailDialog(context, alert),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: _getSeverityColor(alert.severityLevel).withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      _getAlertTypeIcon(alert.alertType),
                      color: _getSeverityColor(alert.severityLevel),
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          AppText.translateAlertType(alert.alertType),
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          alert.alertDesc,
                          style: theme.textTheme.bodyMedium,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  _buildStatusChip(theme, alert.alertStatus),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    alert.alertTimestamp,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    "${alert.userName} - ${alert.deptName}",
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showAlertDetailDialog(BuildContext context, alert_model.Alert alert) {
    final theme = Theme.of(context);
    final apiService = ApiService();
    bool isLoading = false;
    String? address;
    Map<String, dynamic>? healthData;
    
    // 创建一个状态控制器
    final stateNotifier = ValueNotifier<bool>(false);
    
    // 获取地址信息
    Future<void> _loadAddress() async {
      if (alert.latitude != 0 && alert.longitude != 0) {
        address = await apiService.getAddressFromCoordinates(
          alert.latitude, 
          alert.longitude
        );
      }
    }
    
    // 加载健康数据
    Future<void> _loadHealthData() async {
      if (alert.healthId != null && alert.healthId!.isNotEmpty) {
        healthData = await apiService.fetchHealthDataById(alert.healthId!);
      }
    }
    
    // 处理告警
    Future<void> _handleAlert() async {
      if (alert.alertStatus == 'pending') {
        stateNotifier.value = true;
        final success = await apiService.dealAlert(alert.id);
        stateNotifier.value = false;
        
        if (success) {
          // 关闭对话框并返回成功状态
          Navigator.of(context).pop(true);
        } else {
          // 显示错误提示
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('处理告警失败，请稍后重试'))
          );
        }
      }
    }
    
    // 预加载数据
    _loadAddress();
    _loadHealthData();
    
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return ValueListenableBuilder<bool>(
          valueListenable: stateNotifier,
          builder: (context, isProcessing, _) {
            return AlertDialog(
              title: Text(AppText.translateAlertType(alert.alertType)),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      alert.alertDesc,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildInfoRow("告警时间", alert.alertTimestamp),
                    _buildInfoRow("告警等级", AppText.translateAlertLevel(alert.severityLevel)),
                    _buildInfoRow("处理状态", AppText.translateAlertStatus(alert.alertStatus)),
                    _buildInfoRow("用户", alert.userName),
                    _buildInfoRow("部门", alert.deptName),
                    _buildInfoRow("设备", alert.deviceSn),
                    if (alert.latitude != 0 && alert.longitude != 0)
                      FutureBuilder<String>(
                        future: apiService.getAddressFromCoordinates(alert.latitude, alert.longitude),
                        builder: (context, snapshot) {
                          return _buildInfoRow(
                            "位置", 
                            snapshot.hasData 
                                ? snapshot.data! 
                                : "${alert.latitude}, ${alert.longitude}"
                          );
                        },
                      ),
                    if (alert.healthId != null && alert.healthId!.isNotEmpty)
                      FutureBuilder<Map<String, dynamic>?>(
                        future: apiService.fetchHealthDataById(alert.healthId!),
                        builder: (context, snapshot) {
                          if (snapshot.connectionState == ConnectionState.waiting) {
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 8.0),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 80,
                                    child: Text(
                                      "健康数据",
                                      style: TextStyle(
                                        color: Colors.grey[600],
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                ],
                              ),
                            );
                          }
                          
                          if (snapshot.hasData && snapshot.data != null) {
                            final data = snapshot.data!;
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Divider(),
                                Text(
                                  "健康数据",
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    color: AppTheme.primaryColor,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                if (data['heart_rate'] != null)
                                  _buildInfoRow("心率", "${data['heart_rate']} 次/分"),
                                if (data['blood_oxygen'] != null)
                                  _buildInfoRow("血氧", "${data['blood_oxygen']} %"),
                                if (data['body_temperature'] != null)
                                  _buildInfoRow("体温", "${data['body_temperature']} °C"),
                                if (data['blood_pressure_systolic'] != null)
                                  _buildInfoRow("血压", "${data['blood_pressure_systolic']}/${data['blood_pressure_diastolic']} mmHg"),
                                if (data['step'] != null)
                                  _buildInfoRow("步数", "${data['step']} 步"),
                              ],
                            );
                          }
                          
                          return _buildInfoRow("健康ID", alert.healthId ?? "无");
                        },
                      ),
                  ],
                ),
              ),
              actions: [
                if (alert.alertStatus == 'pending')
                  TextButton(
                    onPressed: isProcessing ? null : _handleAlert,
                    child: isProcessing 
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text("标记为已处理"),
                  ),
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                  child: const Text("关闭"),
                ),
              ],
            );
          }
        );
      },
    ).then((result) {
      // 如果告警被处理，刷新列表
      if (result == true) {
        setState(() {
          // 更新当前告警状态
          final index = _filteredAlerts.indexWhere((a) => a.id == alert.id);
          if (index != -1) {
            _filteredAlerts[index] = _filteredAlerts[index].copyWith(alertStatus: 'responded');
          }
          
          // 更新原始告警列表
          final originalIndex = widget.alertInfo.alerts.indexWhere((a) => a.id == alert.id);
          if (originalIndex != -1) {
            widget.alertInfo.alerts[originalIndex] = 
                widget.alertInfo.alerts[originalIndex].copyWith(alertStatus: 'responded');
          }
          
          // 重新应用过滤器
          _applyFilters();
        });
      }
    });
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w400,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusChip(ThemeData theme, String status) {
    Color chipColor;
    String statusText = AppText.translateAlertStatus(status);

    switch (status.toLowerCase()) {
      case 'pending':
        chipColor = Colors.orange;
        break;
      case 'responded':
        chipColor = Colors.green;
        break;
      default:
        chipColor = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: chipColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: chipColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Text(
        statusText,
        style: theme.textTheme.bodySmall?.copyWith(
          color: chipColor,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Color _getSeverityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.amber;
      case 'low':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  IconData _getAlertTypeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'fall_down':
        return Icons.person_off_outlined;
      case 'one_key_alarm':
        return Icons.emergency;
      case 'heart_rate':
        return Icons.favorite;
      case 'blood_oxygen':
        return Icons.air;
      case 'temperature':
        return Icons.thermostat;
      case 'blood_pressure':
        return Icons.favorite_border;
      case 'activity':
        return Icons.directions_run;
      case 'sleep':
        return Icons.nightlight_round;
      default:
        return Icons.warning;
    }
  }
} 