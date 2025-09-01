import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:ljwx_health_new/models/login_response.dart' as login;
import 'package:ljwx_health_new/widgets/enterprise_main_layout.dart';
import 'package:ljwx_health_new/theme/app_theme.dart';
import 'package:ljwx_health_new/services/api_service.dart';
import 'package:ljwx_health_new/models/health_model.dart' as health;
import 'package:flutter_animate/flutter_animate.dart';

class HealthMainScreen extends StatefulWidget {
  final login.LoginData loginData;

  const HealthMainScreen({
    super.key,
    required this.loginData,
  });

  @override
  State<HealthMainScreen> createState() => _HealthMainScreenState();
}

class _HealthMainScreenState extends State<HealthMainScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = true;
  String? _error;
  Map<String, dynamic>? _healthData;
  late AnimationController _animationController;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fetchHealthData();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _fetchHealthData() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      // TODO: 实现健康数据获取逻辑
      await Future.delayed(const Duration(seconds: 1)); // 模拟网络请求
      
      // 模拟健康数据
      _healthData = {
        'heart_rate': 75,
        'blood_oxygen': 98,
        'body_temperature': 36.5,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'step': 8500,
        'distance': 6.2,
        'calorie': 320,
        'sleep_hours': 7.5,
        'exercise_minutes': 45,
      };

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
      title: '健康数据',
      loginData: widget.loginData,
      currentRoute: '/health',
      showSearchBar: true,
      searchHint: '搜索健康指标...',
      onSearchChanged: (value) {
        // TODO: 实现健康数据搜索
        print('搜索健康数据: $value');
      },
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
            Text('正在加载健康数据...'),
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
              onPressed: _fetchHealthData,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchHealthData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildQuickStats(),
            const SizedBox(height: 24),
            _buildVitalSigns(),
            const SizedBox(height: 24),
            _buildActivityData(),
            const SizedBox(height: 24),
            _buildHealthTrends(),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickStats() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '今日概览',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                '步数',
                '${_healthData!['step']}',
                '步',
                Icons.directions_walk,
                Colors.green,
                0,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                '距离',
                '${_healthData!['distance']}',
                'km',
                Icons.route,
                Colors.blue,
                1,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                '卡路里',
                '${_healthData!['calorie']}',
                'kcal',
                Icons.local_fire_department,
                Colors.orange,
                2,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildVitalSigns() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '生命体征',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        _buildVitalSignCard(
          '心率',
          '${_healthData!['heart_rate']} bpm',
          Icons.favorite,
          Colors.red,
          _getHeartRateStatus(_healthData!['heart_rate']),
          3,
        ),
        const SizedBox(height: 12),
        _buildVitalSignCard(
          '血氧',
          '${_healthData!['blood_oxygen']}%',
          Icons.air,
          Colors.blue,
          _getBloodOxygenStatus(_healthData!['blood_oxygen']),
          4,
        ),
        const SizedBox(height: 12),
        _buildVitalSignCard(
          '体温',
          '${_healthData!['body_temperature']}°C',
          Icons.thermostat,
          Colors.orange,
          _getTemperatureStatus(_healthData!['body_temperature']),
          5,
        ),
        const SizedBox(height: 12),
        _buildVitalSignCard(
          '血压',
          '${_healthData!['blood_pressure_systolic']}/${_healthData!['blood_pressure_diastolic']} mmHg',
          Icons.monitor_heart,
          Colors.purple,
          _getBloodPressureStatus(
            _healthData!['blood_pressure_systolic'],
            _healthData!['blood_pressure_diastolic'],
          ),
          6,
        ),
      ],
    );
  }

  Widget _buildActivityData() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '活动数据',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildActivityCard(
                '睡眠时长',
                '${_healthData!['sleep_hours']}',
                '小时',
                Icons.bedtime,
                Colors.indigo,
                7,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActivityCard(
                '运动时长',
                '${_healthData!['exercise_minutes']}',
                '分钟',
                Icons.fitness_center,
                Colors.green,
                8,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildHealthTrends() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              '健康趋势',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            TextButton(
              onPressed: () {
                context.push('/health/trends', extra: widget.loginData);
              },
              child: const Text('查看更多'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        _buildTrendCard(9),
      ],
    );
  }

  Widget _buildStatCard(
    String title,
    String value,
    String unit,
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
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 12),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              unit,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);
  }

  Widget _buildVitalSignCard(
    String title,
    String value,
    IconData icon,
    Color color,
    String status,
    int index,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
        subtitle: Text(status),
        trailing: Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        onTap: () {
          context.push('/health/detail/$title', extra: {
            'loginData': widget.loginData,
            'data': _healthData,
          });
        },
      ),
    ).animate().fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideX(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);
  }

  Widget _buildActivityCard(
    String title,
    String value,
    String unit,
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
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 24),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            RichText(
              text: TextSpan(
                style: DefaultTextStyle.of(context).style,
                children: [
                  TextSpan(
                    text: value,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                  TextSpan(
                    text: ' $unit',
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
      ),
    ).animate().fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);
  }

  Widget _buildTrendCard(int index) {
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
              AppTheme.primaryColor.withOpacity(0.1),
              AppTheme.primaryColor.withOpacity(0.05),
            ],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.trending_up, color: Colors.green, size: 24),
                SizedBox(width: 8),
                Text(
                  '7天健康趋势',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              height: 100,
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Center(
                child: Text(
                  '趋势图表\n(开发中)',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.grey,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '整体健康状况良好，建议保持规律作息',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 500.ms, delay: (index * 100).ms)
     .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: (index * 100).ms);
  }

  String _getHeartRateStatus(int heartRate) {
    if (heartRate < 60) return '心率偏低';
    if (heartRate > 100) return '心率偏高';
    return '心率正常';
  }

  String _getBloodOxygenStatus(int bloodOxygen) {
    if (bloodOxygen < 95) return '血氧偏低';
    return '血氧正常';
  }

  String _getTemperatureStatus(double temperature) {
    if (temperature < 36.0) return '体温偏低';
    if (temperature > 37.5) return '体温偏高';
    return '体温正常';
  }

  String _getBloodPressureStatus(int systolic, int diastolic) {
    if (systolic > 140 || diastolic > 90) return '血压偏高';
    if (systolic < 90 || diastolic < 60) return '血压偏低';
    return '血压正常';
  }
}