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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '告警详情',
          style: theme.textTheme.titleLarge,
        ),
        const SizedBox(height: 16),
        _buildInfoRow('设备名称', alert.deviceSn, theme),
        _buildInfoRow('部门', alert.deptName, theme),
        _buildInfoRow('状态', alert.alertStatus, theme),
        _buildInfoRow('时间', alert.alertTimestamp, theme),
        const SizedBox(height: 16),
        Text(
          '告警信息',
          style: theme.textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Text(alert.alertDesc),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            TextButton(
              onPressed: () {
                // TODO: 处理告警
              },
              child: Text('处理'),
            ),
          ],
        ),
      ],
    );
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