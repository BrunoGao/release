#!/usr/bin/env python3
"""健康弹出信息集成脚本"""
import os,re
try:
    from .health_popup_optimizer import health_popup_optimizer
except ImportError:
    from health_popup_optimizer import health_popup_optimizer

class HealthPopupIntegrator:
    """健康弹出信息集成器"""
    
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.backup_suffix = '.backup'
    
    def integrate_popup_optimization(self):
        """集成弹出窗口优化到现有模板"""
        templates_to_update = [
            'bigscreen_main.html',
            'bigscreen_main copy.html', 
            'bigscreen_main_1.html',
            'bigscreen_main copy 6.html'
        ]
        
        for template in templates_to_update:
            template_path = os.path.join(self.template_dir, template)
            if os.path.exists(template_path):
                self._update_template(template_path)
                print(f"✓ 已优化模板: {template}")
            else:
                print(f"✗ 模板不存在: {template}")
    
    def _update_template(self, template_path):
        """更新单个模板文件"""
        # 备份原文件
        backup_path = template_path + self.backup_suffix
        if not os.path.exists(backup_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 读取原文件
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 注入优化样式
        optimized_content = self._inject_optimized_styles(content)
        
        # 注入优化JavaScript
        optimized_content = self._inject_optimized_javascript(optimized_content)
        
        # 替换弹出函数调用
        optimized_content = self._replace_popup_functions(optimized_content)
        
        # 写入优化后的内容
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
    
    def _inject_optimized_styles(self, content):
        """注入优化的CSS样式"""
        styles = health_popup_optimizer.get_popup_styles()
        
        # 查找</head>标签位置
        head_end = content.find('</head>')
        if head_end != -1:
            # 在</head>前插入样式
            content = content[:head_end] + styles + '\n' + content[head_end:]
        else:
            # 如果没有</head>，在文档开头插入
            content = styles + '\n' + content
        
        return content
    
    def _inject_optimized_javascript(self, content):
        """注入优化的JavaScript代码"""
        js_code = """
    <script>
    // 健康弹出信息优化JavaScript - 集成版本
    
    // 健康状态配置
    const healthStatusColors = {
        'excellent': '#00e4ff',
        'good': '#52c41a', 
        'normal': '#faad14',
        'warning': '#ff7a45',
        'danger': '#ff4d4f'
    };
    
    const metricConfigs = {
        'heart_rate': {name: '心率', unit: 'bpm', icon: '💓', normal: [60, 100]},
        'blood_oxygen': {name: '血氧', unit: '%', icon: '🫁', normal: [95, 100]},
        'temperature': {name: '体温', unit: '℃', icon: '🌡️', normal: [36.0, 37.5]},
        'pressure_high': {name: '收缩压', unit: 'mmHg', icon: '💗', normal: [90, 140]},
        'pressure_low': {name: '舒张压', unit: 'mmHg', icon: '💗', normal: [60, 90]},
        'stress': {name: '压力', unit: '分', icon: '😌', normal: [20, 60]},
        'step': {name: '步数', unit: '步', icon: '👣', normal: [8000, 15000]},
        'distance': {name: '距离', unit: '米', icon: '📏', normal: [5000, 12000]},
        'calorie': {name: '卡路里', unit: 'kcal', icon: '🔥', normal: [1800, 2500]}
    };
    
    // 获取健康状态
    function getHealthStatus(value, metricType) {
        if (!value || value === '-') return 'normal';
        
        const config = metricConfigs[metricType];
        if (!config) return 'normal';
        
        const normalRange = config.normal;
        try {
            const val = parseFloat(value);
            const [minVal, maxVal] = normalRange;
            
            if (minVal <= val && val <= maxVal) {
                return (val >= minVal * 1.1 && val <= maxVal * 0.9) ? 'excellent' : 'good';
            } else if (val < minVal) {
                return val >= minVal * 0.8 ? 'warning' : 'danger';
            } else {
                return val <= maxVal * 1.2 ? 'warning' : 'danger';
            }
        } catch (e) {
            return 'normal';
        }
    }
    
    // 格式化睡眠数据
    function formatSleepDataOptimized(sleepData) {
        if (!sleepData || sleepData === '-') return '-';
        
        try {
            if (typeof sleepData === 'string' && sleepData.startsWith('{')) {
                const data = JSON.parse(sleepData);
                const sleepInfo = data.data || [];
                if (sleepInfo.length > 0) {
                    const s = sleepInfo[0];
                    const formatTime = (minutes) => {
                        if (!minutes) return '0h0m';
                        const hours = Math.floor(minutes / 60);
                        const mins = minutes % 60;
                        return `${hours}h${mins}m`;
                    };
                    
                    return `总:${formatTime(s.total)} 深:${formatTime(s.deep)} 浅:${formatTime(s.light)}`;
                }
            }
        } catch (e) {
            console.error('解析睡眠数据失败:', e);
        }
        return '-';
    }
    
    // 生成指标HTML
    function generateMetricsHtmlOptimized(healthData) {
        let metricsHtml = '';
        
        // 主要生理指标
        const primaryMetrics = ['heart_rate', 'blood_oxygen', 'temperature'];
        primaryMetrics.forEach(metric => {
            const value = healthData[metric] || healthData[metric.replace('_', '')];
            if (value && value !== '-') {
                const config = metricConfigs[metric];
                const status = getHealthStatus(value, metric);
                const color = healthStatusColors[status];
                
                metricsHtml += `
                <div class="metric-item primary">
                    <span class="metric-icon">${config.icon}</span>
                    <span class="metric-name">${config.name}</span>
                    <span class="metric-value ${status}" style="color:${color}">${value} ${config.unit}</span>
                    <div class="health-indicator ${status}"></div>
                </div>
                `;
            }
        });
        
        // 血压特殊处理
        const pressureHigh = healthData.pressure_high || healthData.pressureHigh;
        const pressureLow = healthData.pressure_low || healthData.pressureLow;
        if (pressureHigh && pressureLow && pressureHigh !== '-' && pressureLow !== '-') {
            const statusHigh = getHealthStatus(pressureHigh, 'pressure_high');
            const statusLow = getHealthStatus(pressureLow, 'pressure_low');
            const statusLevels = ['excellent', 'good', 'normal', 'warning', 'danger'];
            const worstStatus = [statusHigh, statusLow].reduce((a, b) => 
                statusLevels.indexOf(a) > statusLevels.indexOf(b) ? a : b
            );
            const color = healthStatusColors[worstStatus];
            
            metricsHtml += `
            <div class="metric-item primary">
                <span class="metric-icon">💗</span>
                <span class="metric-name">血压</span>
                <span class="metric-value ${worstStatus}" style="color:${color}">${pressureHigh}/${pressureLow} mmHg</span>
                <div class="health-indicator ${worstStatus}"></div>
            </div>
            `;
        }
        
        // 次要指标
        const secondaryMetrics = ['stress', 'step', 'distance', 'calorie'];
        secondaryMetrics.forEach(metric => {
            const value = healthData[metric] || healthData[metric.replace('_', '')];
            if (value && value !== '-') {
                const config = metricConfigs[metric];
                const status = getHealthStatus(value, metric);
                const color = healthStatusColors[status];
                
                metricsHtml += `
                <div class="metric-item secondary">
                    <span class="metric-icon">${config.icon}</span>
                    <span class="metric-name">${config.name}</span>
                    <span class="metric-value ${status}" style="color:${color}">${value} ${config.unit}</span>
                    <div class="health-indicator ${status}"></div>
                </div>
                `;
            }
        });
        
        return metricsHtml;
    }
    
    // 生成位置信息HTML
    function generateLocationHtmlOptimized(healthData) {
        const longitude = healthData.longitude;
        const latitude = healthData.latitude;
        
        if (longitude && latitude) {
            return `
            <div class="location-info">
                <span class="location-icon">📍</span>
                <span class="location-text">
                    <span id="locationInfo">
                        <span class="loading-spinner"></span> 正在获取位置...
                    </span>
                    <small style="color:#888;display:block;">(${longitude}, ${latitude})</small>
                </span>
            </div>
            `;
        }
        return '<div class="location-info"><span class="location-icon">📍</span><span>位置未知</span></div>';
    }
    
    // 格式化时间戳
    function formatTimestampOptimized(timestamp) {
        if (!timestamp || timestamp === '-') return '-';
        
        try {
            const dt = new Date(timestamp);
            const now = new Date();
            const diff = now - dt;
            
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor(diff / (1000 * 60));
            
            if (days > 0) return `${days}天前`;
            if (hours > 0) return `${hours}小时前`;
            if (minutes > 0) return `${minutes}分钟前`;
            return '刚刚';
        } catch (e) {
            return String(timestamp);
        }
    }
    
    // 生成优化的健康弹出窗口
    function generateOptimizedHealthPopupIntegrated(healthData) {
        const userName = healthData.user_name || healthData.userName || '未知用户';
        const deptName = healthData.dept_name || healthData.deptName || '未知部门';
        const avatar = healthData.avatar || 'static/images/default-avatar.png';
        const timestamp = healthData.timestamp;
        
        const metricsHtml = generateMetricsHtmlOptimized(healthData);
        const locationHtml = generateLocationHtmlOptimized(healthData);
        const sleepData = formatSleepDataOptimized(healthData.sleepData || healthData.scientificSleepData);
        const formattedTime = formatTimestampOptimized(timestamp);
        
        return `
        <div class="health-popup-container">
            <div class="popup-header">
                <div class="user-info">
                    <img src="${avatar}" class="user-avatar" alt="头像" onerror="this.src='static/images/default-avatar.png'">
                    <div class="user-details">
                        <div class="user-name">${userName}</div>
                        <div class="dept-name">${deptName}</div>
                    </div>
                </div>
                <div class="health-status-indicator excellent">
                    <span class="status-dot"></span>
                    <span class="status-text">健康</span>
                </div>
            </div>
            
            <div class="popup-content">
                <div class="metrics-section">
                    <h4 class="section-title">📊 生理指标</h4>
                    <div class="metrics-grid">
                        ${metricsHtml}
                    </div>
                </div>
                
                <div class="additional-info">
                    <div class="info-item">
                        <span class="info-icon">😴</span>
                        <span class="info-label">睡眠:</span>
                        <span class="info-value">${sleepData}</span>
                    </div>
                    
                    ${locationHtml}
                    
                    <div class="info-item">
                        <span class="info-icon">⏰</span>
                        <span class="info-label">采集时间:</span>
                        <span class="info-value">${formattedTime}</span>
                    </div>
                </div>
            </div>
            
            <div class="popup-footer">
                <button class="action-btn detail-btn" onclick="showDetailedHealthAnalysis('${userName}')">
                    📈 详细分析
                </button>
                <button class="action-btn close-btn" onclick="removeCustomMapInfo()">
                    ✕ 关闭
                </button>
            </div>
        </div>
        `;
    }
    
    // 生成优化的告警弹出窗口
    function generateOptimizedAlertPopupIntegrated(healthData) {
        const userName = healthData.user_name || healthData.userName || '未知用户';
        const deptName = healthData.dept_name || healthData.deptName || '未知部门';
        const avatar = healthData.avatar || 'static/images/default-avatar.png';
        const alertType = healthData.alert_type || '-';
        const severityLevel = healthData.severity_level || '-';
        const alertStatus = healthData.alert_status || '-';
        const alertId = healthData.alert_id || '';
        const timestamp = healthData.alert_timestamp || healthData.timestamp;
        
        const severityColors = {
            'critical': '#ff4d4f',
            'high': '#ff7a45',
            'medium': '#faad14',
            'low': '#52c41a'
        };
        
        const severityColor = severityColors[severityLevel] || '#faad14';
        const metricsHtml = generateMetricsHtmlOptimized(healthData);
        const locationHtml = generateLocationHtmlOptimized(healthData);
        const formattedTime = formatTimestampOptimized(timestamp);
        
        return `
        <div class="alert-popup-container">
            <div class="popup-header alert-header">
                <div class="user-info">
                    <img src="${avatar}" class="user-avatar" alt="头像" onerror="this.src='static/images/default-avatar.png'">
                    <div class="user-details">
                        <div class="user-name">${userName}</div>
                        <div class="dept-name">${deptName}</div>
                    </div>
                </div>
                <div class="alert-status-indicator" style="background:${severityColor}">
                    <span class="alert-icon">⚠️</span>
                    <span class="alert-level">${severityLevel.toUpperCase()}</span>
                </div>
            </div>
            
            <div class="popup-content">
                <div class="alert-info-section">
                    <h4 class="section-title">🚨 告警信息</h4>
                    <div class="alert-details">
                        <div class="alert-item">
                            <span class="alert-label">类型:</span>
                            <span class="alert-value">${alertType}</span>
                        </div>
                        <div class="alert-item">
                            <span class="alert-label">级别:</span>
                            <span class="alert-value" style="color:${severityColor}">${severityLevel}</span>
                        </div>
                        <div class="alert-item">
                            <span class="alert-label">状态:</span>
                            <span class="alert-value">${alertStatus}</span>
                        </div>
                    </div>
                </div>
                
                <div class="metrics-section">
                    <h4 class="section-title">📊 健康数据</h4>
                    <div class="metrics-grid">
                        ${metricsHtml}
                    </div>
                </div>
                
                <div class="additional-info">
                    ${locationHtml}
                    
                    <div class="info-item">
                        <span class="info-icon">⏰</span>
                        <span class="info-label">告警时间:</span>
                        <span class="info-value">${formattedTime}</span>
                    </div>
                </div>
            </div>
            
            <div class="popup-footer">
                <button class="action-btn handle-btn" onclick="handleAlert('${alertId}')" style="background:${severityColor}">
                    🔧 一键处理
                </button>
                <button class="action-btn detail-btn" onclick="showHealthProfile('${alertId}')">
                    📋 详情
                </button>
                <button class="action-btn close-btn" onclick="removeCustomMapInfo()">
                    ✕ 关闭
                </button>
            </div>
        </div>
        `;
    }
    
    // 显示优化的自定义地图信息 - 集成版本
    function showOptimizedCustomMapInfoIntegrated(data, isAlert = false) {
        removeCustomMapInfo(); // 移除现有弹窗
        
        const div = document.createElement('div');
        div.className = 'custom-map-info';
        div.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:10000;';
        
        // 生成优化的弹出内容
        const popupHtml = isAlert ? 
            generateOptimizedAlertPopupIntegrated(data) : 
            generateOptimizedHealthPopupIntegrated(data);
        
        div.innerHTML = popupHtml;
        document.body.appendChild(div);
        
        // 获取位置信息
        const longitude = data.longitude;
        const latitude = data.latitude;
        if (longitude && latitude && typeof reverseGeocode === 'function') {
            reverseGeocode(longitude, latitude)
                .then(address => {
                    const locationInfo = document.getElementById('locationInfo');
                    if (locationInfo) {
                        locationInfo.innerHTML = address || '未知位置';
                    }
                })
                .catch(error => {
                    console.error('获取位置信息失败:', error);
                    const locationInfo = document.getElementById('locationInfo');
                    if (locationInfo) {
                        locationInfo.innerHTML = '获取位置信息失败';
                    }
                });
        }
    }
    
    // 显示详细健康分析
    function showDetailedHealthAnalysis(userName) {
        console.log('显示详细健康分析:', userName);
        // 可以在这里添加跳转到详细分析页面的逻辑
        if (typeof showHealthDetail === 'function') {
            showHealthDetail(userName);
        }
    }
    
    // 优化的移除自定义地图信息函数
    function removeCustomMapInfoOptimized() {
        const old = document.querySelector('.custom-map-info');
        if (old) {
            old.style.animation = 'popupFadeOut 0.3s ease-in forwards';
            setTimeout(() => old.remove(), 300);
        }
    }
    
    // 添加淡出动画样式
    if (!document.querySelector('#popup-fade-out-style')) {
        const style = document.createElement('style');
        style.id = 'popup-fade-out-style';
        style.textContent = `
            @keyframes popupFadeOut {
                from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // 重写原有的函数以使用优化版本
    if (typeof window !== 'undefined') {
        // 保存原有函数的引用
        window._originalShowCustomMapInfo = window.showCustomMapInfo;
        window._originalRemoveCustomMapInfo = window.removeCustomMapInfo;
        
        // 替换为优化版本
        window.showCustomMapInfo = showOptimizedCustomMapInfoIntegrated;
        window.removeCustomMapInfo = removeCustomMapInfoOptimized;
        window.showDetailedHealthAnalysis = showDetailedHealthAnalysis;
        
        console.log('✓ 健康弹出信息优化已集成');
    }
    </script>
        """
        
        # 查找</body>标签位置
        body_end = content.find('</body>')
        if body_end != -1:
            # 在</body>前插入JavaScript
            content = content[:body_end] + js_code + '\n' + content[body_end:]
        else:
            # 如果没有</body>，在文档末尾插入
            content = content + js_code
        
        return content
    
    def _replace_popup_functions(self, content):
        """替换弹出函数调用"""
        # 替换showCustomMapInfo调用为优化版本
        patterns = [
            (r'showCustomMapInfo\s*\(', 'showOptimizedCustomMapInfoIntegrated('),
            (r'removeCustomMapInfo\s*\(', 'removeCustomMapInfoOptimized(')
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def restore_original_templates(self):
        """恢复原始模板文件"""
        templates_to_restore = [
            'bigscreen_main.html',
            'bigscreen_main copy.html',
            'bigscreen_main_1.html', 
            'bigscreen_main copy 6.html'
        ]
        
        for template in templates_to_restore:
            template_path = os.path.join(self.template_dir, template)
            backup_path = template_path + self.backup_suffix
            
            if os.path.exists(backup_path):
                with open(backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 已恢复模板: {template}")
            else:
                print(f"✗ 备份文件不存在: {template}")

# 全局实例
health_popup_integrator = HealthPopupIntegrator()

def integrate_health_popup_optimization():
    """集成健康弹出信息优化"""
    health_popup_integrator.integrate_popup_optimization()

def restore_original_health_popup():
    """恢复原始健康弹出信息"""
    health_popup_integrator.restore_original_templates() 