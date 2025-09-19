/**
 * BigScreen API Client
 * 连接到 FastAPI 仪表板数据 API
 */

class BigscreenAPI {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('access_token');
        this.retryCount = 3;
        this.retryDelay = 1000;
    }

    /**
     * 通用 API 请求方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
                ...options.headers
            },
            ...options
        };

        for (let attempt = 0; attempt < this.retryCount; attempt++) {
            try {
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    if (response.status === 401) {
                        // Token 可能过期，尝试刷新
                        await this.refreshToken();
                        continue;
                    }
                    throw new Error(`API Error: ${response.status} ${response.statusText}`);
                }

                const data = await response.json();
                return data;
            } catch (error) {
                console.error(`API Request failed (attempt ${attempt + 1}):`, error);
                
                if (attempt === this.retryCount - 1) {
                    throw error;
                }
                
                // 指数退避重试
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt)));
            }
        }
    }

    /**
     * GET 请求
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                searchParams.append(key, value);
            }
        });

        const queryString = searchParams.toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, { method: 'GET' });
    }

    /**
     * POST 请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * 刷新认证 Token
     */
    async refreshToken() {
        try {
            const response = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('access_token', this.token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        // 刷新失败，清除 token 并重定向到登录页
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return false;
    }

    // ============================================================================
    // 统计数据相关 API
    // ============================================================================

    /**
     * 获取统计概览
     */
    async getStatisticsOverview(customerId = 'default', date = null) {
        const params = { customer_id: customerId };
        if (date) params.date = date;
        
        return this.get('/statistics/overview', params);
    }

    /**
     * 获取实时统计
     */
    async getRealtimeStats(date = null) {
        const params = {};
        if (date) params.date = date;
        
        return this.get('/statistics/realtime', params);
    }

    // ============================================================================
    // 健康数据相关 API
    // ============================================================================

    /**
     * 获取综合健康评分
     */
    async getHealthScore(customerId = 'default', options = {}) {
        const params = {
            customer_id: customerId,
            include_device_breakdown: options.includeDeviceBreakdown || false,
            days: options.days || 7,
            ...options
        };
        
        return this.get('/health/score/comprehensive', params);
    }

    /**
     * 获取健康基线图表数据
     */
    async getHealthBaseline(orgId, startDate, endDate) {
        return this.get('/health/charts/baseline', {
            org_id: orgId,
            start_date: startDate,
            end_date: endDate
        });
    }

    /**
     * 获取健康建议
     */
    async getHealthRecommendations(analysisType = 'comprehensive', deviceSn = null) {
        const params = { analysis_type: analysisType };
        if (deviceSn) params.device_sn = deviceSn;
        
        return this.get('/health/recommendations', params);
    }

    /**
     * 获取健康趋势分析
     */
    async getHealthTrends(deviceSn, timeRange = '24h') {
        return this.get('/health/trends/analysis', {
            device_sn: deviceSn,
            time_range: timeRange
        });
    }

    /**
     * 获取综合健康分析
     */
    async getHealthAnalysis(deviceSn = null, days = 30) {
        const params = { days };
        if (deviceSn) params.device_sn = deviceSn;
        
        return this.get('/health/analysis/comprehensive', params);
    }

    /**
     * 生成健康基线
     */
    async generateHealthBaseline(targetDate) {
        return this.post('/health/baseline/generate', {
            target_date: targetDate
        });
    }

    /**
     * 获取健康基线状态
     */
    async getHealthBaselineStatus() {
        return this.get('/health/baseline/status');
    }

    // ============================================================================
    // 个人信息相关 API
    // ============================================================================

    /**
     * 获取个人实时健康数据
     */
    async getPersonalRealtimeHealth(userId, cardType, deviceSn) {
        return this.get('/personal/realtime-health', {
            user_id: userId,
            card_type: cardType,
            device_sn: deviceSn
        });
    }

    /**
     * 获取个人历史健康数据
     */
    async getPersonalHistoryHealth(userId, cardType, days = 7) {
        return this.get('/personal/history-health', {
            user_id: userId,
            card_type: cardType,
            days: days
        });
    }

    /**
     * 获取个人AI分析
     */
    async getPersonalAIAnalysis(userId, cardType, analysisType = 'comprehensive') {
        return this.get('/personal/ai-analysis', {
            user_id: userId,
            card_type: cardType,
            analysis_type: analysisType
        });
    }

    /**
     * 获取个人信息
     */
    async getPersonalInfo(deviceSn) {
        return this.get('/personal/info', { device_sn: deviceSn });
    }

    /**
     * 获取个人告警
     */
    async getPersonalAlerts(deviceSn) {
        return this.get('/personal/alerts', { device_sn: deviceSn });
    }

    // ============================================================================
    // 设备相关 API
    // ============================================================================

    /**
     * 获取设备信息
     */
    async getDeviceInfo(deviceSn) {
        return this.get('/device/info', { device_sn: deviceSn });
    }

    /**
     * 获取设备关联的用户和组织
     */
    async getDeviceUserOrg(deviceSn) {
        return this.get('/device/user_org', { device_sn: deviceSn });
    }

    /**
     * 获取设备列表
     */
    async getDevices(filters = {}) {
        return this.get('/devices', filters);
    }

    /**
     * 获取最新健康数据
     */
    async getLatestHealthData(deviceSn) {
        return this.get('/health_data/latest', { device_sn: deviceSn });
    }

    // ============================================================================
    // 用户和组织相关 API
    // ============================================================================

    /**
     * 获取用户列表
     */
    async getUsersList(orgId) {
        return this.get('/users/list', { org_id: orgId });
    }

    /**
     * 获取用户信息
     */
    async getUserInfo(deviceSn) {
        return this.get('/users/info', { device_sn: deviceSn });
    }

    /**
     * 获取部门列表
     */
    async getDepartments(orgId, customerId) {
        return this.get('/departments', {
            org_id: orgId,
            customer_id: customerId
        });
    }

    // ============================================================================
    // 告警相关 API
    // ============================================================================

    /**
     * 获取告警列表
     */
    async getAlerts(filters = {}) {
        return this.get('/alerts', filters);
    }

    /**
     * 处理告警
     */
    async handleAlert(alertId) {
        return this.get('/alerts/handle', { alert_id: alertId });
    }

    /**
     * 确认告警
     */
    async acknowledgeAlert(alertData) {
        return this.post('/alerts/acknowledge', alertData);
    }

    // ============================================================================
    // 消息相关 API
    // ============================================================================

    /**
     * 获取消息列表
     */
    async getMessages(filters = {}) {
        return this.get('/messages', filters);
    }

    // ============================================================================
    // 兼容旧版本的快捷方法
    // ============================================================================

    /**
     * 快捷方法：获取当前统计数据
     */
    async getCurrentStats() {
        const [overview, realtime] = await Promise.all([
            this.getStatisticsOverview(),
            this.getRealtimeStats()
        ]);

        return {
            total_users: overview.total_users,
            active_devices: overview.active_devices,
            health_score_avg: overview.health_score_avg,
            today_alerts: overview.today_alerts,
            current_online: realtime.current_online,
            growth_rate: realtime.growth_rate,
            org_count: overview.org_count,
            department_count: overview.department_count
        };
    }

    /**
     * 快捷方法：获取告警和消息统计
     */
    async getAlertsAndMessages() {
        const [alerts, messages] = await Promise.all([
            this.getAlerts(),
            this.getMessages()
        ]);

        return {
            alerts: alerts.alerts || [],
            total_alerts: alerts.total_count || 0,
            unread_alerts: alerts.unread_count || 0,
            messages: messages.messages || [],
            total_messages: messages.total_count || 0,
            unread_messages: messages.unread_count || 0
        };
    }

    /**
     * 快捷方法：获取设备和健康概览
     */
    async getDevicesAndHealth() {
        const [devices, healthScore] = await Promise.all([
            this.getDevices(),
            this.getHealthScore()
        ]);

        return {
            devices: devices.devices || [],
            online_devices: devices.online_count || 0,
            offline_devices: devices.offline_count || 0,
            total_devices: devices.total_count || 0,
            overall_health_score: healthScore.overall_score || 0,
            health_trends: healthScore.trend || 'stable'
        };
    }
}

// 导出 API 客户端
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BigscreenAPI;
} else {
    window.BigscreenAPI = BigscreenAPI;
}

// 创建全局实例
window.bigscreenAPI = new BigscreenAPI();

console.log('📡 BigScreen API Client 已加载');