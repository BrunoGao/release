import 'package:flutter/material.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/models/alert_model.dart' as alert;
import 'package:ljwx_health_new/models/personal_data.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'dart:async';

class AlertsScreen extends StatefulWidget {
  final login.LoginData loginData;

  const AlertsScreen({
    super.key,
    required this.loginData,
  });

  @override
  _AlertsScreenState createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  Timer? _timer;
  PersonalData? _personalData;
  final _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _fetchPersonalInfo();
    _timer = Timer.periodic(Duration(seconds: 5), (_) => _fetchPersonalInfo());
  }

  Future<void> _fetchPersonalInfo() async {
    try {
      final response = await _apiService.getPersonalInfo(widget.loginData.phone);
      setState(() {
        _personalData = response;
      });
    } catch (e) {
      print('Error fetching personal info: $e');
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_personalData == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final theme = Theme.of(context);
    final alertInfo = _personalData!.alertInfo;

    return Scaffold(
      appBar: AppBar(
        title: Text('告警信息'),
      ),
      body: ListView.builder(
        itemCount: alertInfo.alerts.length,
        itemBuilder: (context, index) {
          final alert = alertInfo.alerts[index];
          return Card(
            child: ListTile(
              leading: _buildAlertStatusIcon(alert.alertStatus),
              title: Text(alert.alertDesc),
              subtitle: Text(alert.deviceSn),
              trailing: Text(alert.alertTimestamp),
              onTap: () {
                showDialog(
                  context: context,
                  builder: (context) => Dialog(
                    child: SingleChildScrollView(
                      child: _buildAlertDetails(alert, theme),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildAlertStatusIcon(String status) {
    IconData iconData;
    Color color;

    switch (status.toLowerCase()) {
      case 'pending':
        iconData = Icons.pending;
        color = Colors.orange;
        break;
      case 'responded':
        iconData = Icons.check_circle;
        color = Colors.green;
        break;
      case 'acknowledged':
        iconData = Icons.done_all;
        color = Colors.blue;
        break;
      default:
        iconData = Icons.help;
        color = Colors.grey;
    }

    return Icon(iconData, color: color);
  }

  Widget _buildAlertDetails(alert.Alert alert, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '告警详情',
                style: theme.textTheme.titleLarge,
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildInfoRow('设备序列号', alert.deviceSn, theme),
          _buildInfoRow('部门', alert.deptName, theme),
          _buildInfoRow('告警类型', alert.alertType, theme),
          _buildInfoRow('当前状态', alert.alertStatus, theme),
          _buildInfoRow('告警时间', alert.alertTimestamp, theme),
          const SizedBox(height: 16),
          Text(
            '告警信息',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              alert.alertDesc,
              style: theme.textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 20),
          // 处理按钮
          if (alert.alertStatus.toLowerCase() != 'processed') ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('取消'),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () => _processAlert(alert),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('标记为已处理'),
                ),
              ],
            ),
          ] else ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green[700]),
                  const SizedBox(width: 8),
                  Text(
                    '此告警已处理',
                    style: TextStyle(
                      color: Colors.green[700],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // 处理告警的方法
  Future<void> _processAlert(alert.Alert alert) async {
    try {
      // 显示加载指示器
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(
          child: CircularProgressIndicator(),
        ),
      );

      // 调用API处理告警
      final success = await _apiService.markAlertAsProcessed(alert.alertId.toString());
      
      // 关闭加载指示器
      Navigator.of(context).pop();
      
      if (success) {
        // 处理成功
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('告警已标记为已处理'),
            backgroundColor: Colors.green,
          ),
        );
        
        // 关闭详情对话框
        Navigator.of(context).pop();
        
        // 刷新数据
        _fetchPersonalInfo();
      } else {
        // 处理失败
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('处理告警信息失败，请重试'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      // 关闭可能存在的加载指示器
      Navigator.of(context).pop();
      
      // 显示错误信息
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('处理告警失败：$e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildInfoRow(String label, String value, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.grey,
            ),
          ),
          Text(
            value,
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
} 