/**
 * Statistics Service
 * 统计数据服务
 */

class StatisticsService {
    constructor(apiClient) {
        this.api = apiClient || window.bigscreenAPI;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
    }

    /**
     * 获取缓存键
     */
    getCacheKey(method, params) {
        return `${method}_${JSON.stringify(params)}`;
    }

    /**
     * 检查缓存是否有效
     */
    isCacheValid(cacheEntry) {
        return cacheEntry && (Date.now() - cacheEntry.timestamp < this.cacheTimeout);
    }

    /**
     * 获取带缓存的数据
     */
    async getCachedData(method, params = {}) {
        const cacheKey = this.getCacheKey(method, params);
        const cached = this.cache.get(cacheKey);

        if (this.isCacheValid(cached)) {
            return cached.data;
        }

        const data = await this.api[method](params);
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });

        return data;
    }

    /**
     * 清除缓存
     */
    clearCache(pattern = null) {
        if (pattern) {
            Array.from(this.cache.keys()).forEach(key => {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            });
        } else {
            this.cache.clear();
        }
    }

    /**
     * 获取实时统计概览
     */
    async getRealtimeOverview(customerId = 'default') {
        try {
            const [overview, realtimeStats] = await Promise.all([
                this.api.getStatisticsOverview(customerId),
                this.api.getRealtimeStats()
            ]);

            return {
                total_users: overview.total_users || 0,
                active_devices: overview.active_devices || 0,
                health_score_avg: overview.health_score_avg || 0,
                today_alerts: overview.today_alerts || 0,
                org_count: overview.org_count || 0,
                department_count: overview.department_count || 0,
                device_online_rate: overview.device_online_rate || 0,
                data_upload_rate: overview.data_upload_rate || 0,
                current_online: realtimeStats.current_online || 0,
                growth_rate: realtimeStats.growth_rate || 0,
                alert_trend: realtimeStats.alert_trend || [],
                device_status: realtimeStats.device_status || {}
            };
        } catch (error) {
            console.error('获取实时统计概览失败:', error);
            throw error;
        }
    }

    /**
     * 获取健康统计分析
     */
    async getHealthStatistics(options = {}) {
        try {
            const healthData = await this.api.getHealthScore('default', {
                days: options.days || 7,
                includeDeviceBreakdown: true
            });

            return {
                overall_score: healthData.overall_score || 0,
                heart_rate_score: healthData.heart_rate_score || 0,
                blood_oxygen_score: healthData.blood_oxygen_score || 0,
                temperature_score: healthData.temperature_score || 0,
                pressure_score: healthData.pressure_score || 0,
                stress_score: healthData.stress_score || 0,
                exercise_score: healthData.exercise_score || 0,
                sleep_score: healthData.sleep_score || 0,
                trend: healthData.trend || 'stable',
                risk_level: healthData.risk_level || 'low',
                device_breakdown: healthData.device_breakdown || []
            };
        } catch (error) {
            console.error('获取健康统计失败:', error);
            throw error;
        }
    }

    /**
     * 获取告警统计
     */
    async getAlertStatistics(filters = {}) {
        try {
            const alertData = await this.api.getAlerts(filters);

            const alerts = alertData.alerts || [];
            const severityCount = {
                critical: 0,
                warning: 0,
                info: 0
            };

            const timeDistribution = {};
            
            alerts.forEach(alert => {
                // 统计严重程度
                if (severityCount.hasOwnProperty(alert.severity)) {
                    severityCount[alert.severity]++;
                }

                // 统计时间分布
                const hour = new Date(alert.created_time).getHours();
                const timeKey = `${hour}:00`;
                timeDistribution[timeKey] = (timeDistribution[timeKey] || 0) + 1;
            });

            return {
                total_alerts: alertData.total_count || 0,
                unread_alerts: alertData.unread_count || 0,
                severity_distribution: severityCount,
                time_distribution: timeDistribution,
                latest_alerts: alerts.slice(0, 10) // 最近10条
            };
        } catch (error) {
            console.error('获取告警统计失败:', error);
            throw error;
        }
    }

    /**
     * 获取设备统计
     */
    async getDeviceStatistics(filters = {}) {
        try {
            const deviceData = await this.api.getDevices(filters);

            const devices = deviceData.devices || [];
            const statusCount = {
                online: 0,
                offline: 0,
                maintenance: 0
            };

            const batteryLevels = {
                high: 0,    // >80%
                medium: 0,  // 20-80%
                low: 0      // <20%
            };

            devices.forEach(device => {
                // 统计状态
                if (statusCount.hasOwnProperty(device.status)) {
                    statusCount[device.status]++;
                }

                // 统计电池电量
                const battery = device.battery_level || 0;
                if (battery > 80) {
                    batteryLevels.high++;
                } else if (battery > 20) {
                    batteryLevels.medium++;
                } else {
                    batteryLevels.low++;
                }
            });

            return {
                total_devices: deviceData.total_count || 0,
                online_devices: deviceData.online_count || 0,
                offline_devices: deviceData.offline_count || 0,
                status_distribution: statusCount,
                battery_distribution: batteryLevels,
                devices: devices
            };
        } catch (error) {
            console.error('获取设备统计失败:', error);
            throw error;
        }
    }

    /**
     * 获取消息统计
     */
    async getMessageStatistics(filters = {}) {
        try {
            const messageData = await this.api.getMessages(filters);

            const messages = messageData.messages || [];
            const typeCount = {};
            const unreadCount = messages.filter(msg => !msg.read).length;

            messages.forEach(message => {
                const type = message.type || 'unknown';
                typeCount[type] = (typeCount[type] || 0) + 1;
            });

            return {
                total_messages: messageData.total_count || 0,
                unread_messages: messageData.unread_count || unreadCount,
                type_distribution: typeCount,
                latest_messages: messages.slice(0, 10)
            };
        } catch (error) {
            console.error('获取消息统计失败:', error);
            throw error;
        }
    }

    /**
     * 获取组合统计数据
     */
    async getCombinedStatistics(customerId = 'default') {
        try {
            const [overview, health, alerts, devices, messages] = await Promise.all([
                this.getRealtimeOverview(customerId),
                this.getHealthStatistics(),
                this.getAlertStatistics(),
                this.getDeviceStatistics(),
                this.getMessageStatistics()
            ]);

            return {
                overview,
                health,
                alerts,
                devices,
                messages,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('获取组合统计数据失败:', error);
            throw error;
        }
    }

    /**
     * 计算趋势指标
     */
    calculateTrend(current, previous) {
        if (!previous || previous === 0) {
            return { value: 0, direction: 'stable' };
        }

        const change = ((current - previous) / previous) * 100;
        
        return {
            value: Math.abs(change),
            direction: change > 0 ? 'up' : (change < 0 ? 'down' : 'stable'),
            percentage: change.toFixed(1)
        };
    }

    /**
     * 格式化统计数据用于显示
     */
    formatStatisticsForDisplay(stats) {
        return {
            // 概览数据
            overview: {
                totalUsers: this.formatNumber(stats.overview.total_users),
                activeDevices: this.formatNumber(stats.overview.active_devices),
                healthScore: this.formatDecimal(stats.overview.health_score_avg, 1),
                todayAlerts: this.formatNumber(stats.overview.today_alerts),
                onlineRate: this.formatPercentage(stats.overview.device_online_rate),
                uploadRate: this.formatPercentage(stats.overview.data_upload_rate)
            },

            // 健康数据
            health: {
                overallScore: this.formatDecimal(stats.health.overall_score, 1),
                trend: stats.health.trend,
                riskLevel: stats.health.risk_level,
                categories: {
                    cardiovascular: this.formatDecimal(stats.health.heart_rate_score, 1),
                    respiratory: this.formatDecimal(stats.health.blood_oxygen_score, 1),
                    metabolic: this.formatDecimal(stats.health.exercise_score, 1),
                    sleep: this.formatDecimal(stats.health.sleep_score, 1)
                }
            },

            // 告警数据
            alerts: {
                total: this.formatNumber(stats.alerts.total_alerts),
                unread: this.formatNumber(stats.alerts.unread_alerts),
                severity: stats.alerts.severity_distribution,
                latest: stats.alerts.latest_alerts
            },

            // 设备数据
            devices: {
                total: this.formatNumber(stats.devices.total_devices),
                online: this.formatNumber(stats.devices.online_devices),
                offline: this.formatNumber(stats.devices.offline_devices),
                onlineRate: this.formatPercentage((stats.devices.online_devices / stats.devices.total_devices) * 100)
            },

            // 消息数据
            messages: {
                total: this.formatNumber(stats.messages.total_messages),
                unread: this.formatNumber(stats.messages.unread_messages),
                latest: stats.messages.latest_messages
            }
        };
    }

    /**
     * 数字格式化
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * 小数格式化
     */
    formatDecimal(num, decimals = 2) {
        return parseFloat(num || 0).toFixed(decimals);
    }

    /**
     * 百分比格式化
     */
    formatPercentage(num) {
        return this.formatDecimal(num, 1) + '%';
    }
}

// 导出统计服务
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatisticsService;
} else {
    window.StatisticsService = StatisticsService;
}

// 创建全局实例
window.statisticsService = new StatisticsService();

console.log('📊 Statistics Service 已加载');