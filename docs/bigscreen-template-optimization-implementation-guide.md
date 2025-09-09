# BigScreen 大屏模板优化实施指南

## 概述

本文档基于对 ljwx-bigscreen 系统中 `main.html` 和 `personal.html` 两个核心大屏模板的深入分析，结合现有 API 接口分析文档和重构建议，提供完整的优化实施方案。在不改变当前 UI 的前提下，全面提升模板的响应速度和可维护性。

## 当前状况分析

### 模板文件规模
- **main.html**: 10,003 行，约 368KB
- **personal.html**: 9,792 行，主要个人健康大屏

### 识别的主要问题

#### 1. 代码结构问题
- **巨型单文件**: 两个文件都超过 9000 行，难以维护
- **重复代码**: 大量相似的样式定义和 JavaScript 函数
- **内联样式**: 大量 CSS 直接写在 HTML 文件中
- **混杂职责**: UI、业务逻辑、样式混合在一起

#### 2. 性能瓶颈
- **阻塞式加载**: 所有资源顺序加载，影响首屏渲染
- **无缓存策略**: 重复请求相同的 API 接口
- **DOM 操作频繁**: 大量直接 DOM 操作影响性能
- **资源冗余**: 未使用的 CSS 和 JavaScript 代码

#### 3. 维护困难
- **查找困难**: 在万行文件中定位问题极其困难
- **调试复杂**: 错误定位和修复成本高
- **扩展限制**: 添加新功能需要修改核心文件
- **团队协作**: 多人同时修改容易产生冲突

## 优化实施方案

### 阶段一：文件结构重构（第 1-2 周）

#### 1.1 模块化拆分策略

##### 主要目录结构设计
```
ljwx-bigscreen/bigscreen/bigScreen/
├── templates/
│   ├── layouts/                    # 布局模板
│   │   ├── base.html              # 基础布局
│   │   ├── dashboard_layout.html   # 大屏布局
│   │   └── personal_layout.html    # 个人页面布局
│   ├── components/                 # 组件模板
│   │   ├── charts/                # 图表组件
│   │   │   ├── health_score_chart.html
│   │   │   ├── trend_chart.html
│   │   │   └── radar_chart.html
│   │   ├── panels/                # 面板组件
│   │   │   ├── device_info_panel.html
│   │   │   ├── message_panel.html
│   │   │   └── alert_panel.html
│   │   └── widgets/               # 小组件
│   │       ├── loading_spinner.html
│   │       ├── status_indicator.html
│   │       └── metric_card.html
│   ├── pages/                     # 页面模板
│   │   ├── main_optimized.html    # 优化后的主页面
│   │   └── personal_optimized.html # 优化后的个人页面
│   └── partials/                  # 页面片段
│       ├── header.html
│       ├── sidebar.html
│       └── footer.html
├── static/
│   ├── css/                       # 样式文件
│   │   ├── base/                  # 基础样式
│   │   │   ├── reset.css          # 重置样式
│   │   │   ├── variables.css      # CSS 变量
│   │   │   └── animations.css     # 动画样式
│   │   ├── components/            # 组件样式
│   │   │   ├── charts.css
│   │   │   ├── panels.css
│   │   │   └── widgets.css
│   │   ├── pages/                 # 页面样式
│   │   │   ├── main.css
│   │   │   └── personal.css
│   │   └── themes/                # 主题样式
│   │       ├── default.css
│   │       ├── dark.css
│   │       └── high_contrast.css
│   └── js/                        # JavaScript 文件
│       ├── core/                  # 核心库
│       │   ├── api-client.js      # API 客户端
│       │   ├── cache-manager.js   # 缓存管理
│       │   └── event-bus.js       # 事件总线
│       ├── components/            # 组件脚本
│       │   ├── health-chart.js
│       │   ├── device-panel.js
│       │   └── message-panel.js
│       ├── pages/                 # 页面脚本
│       │   ├── main-page.js
│       │   └── personal-page.js
│       └── utils/                 # 工具函数
│           ├── formatters.js
│           ├── validators.js
│           └── helpers.js
```

#### 1.2 基础布局模板设计

##### base.html - 基础模板
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}智能健康数据分析平台{% endblock %}</title>
    
    <!-- 基础样式 -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base/reset.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base/variables.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base/animations.css') }}">
    
    <!-- 页面特定样式 -->
    {% block stylesheets %}{% endblock %}
    
    <!-- 预加载关键资源 -->
    <link rel="preload" href="{{ url_for('static', filename='js/core/api-client.js') }}" as="script">
    <link rel="preload" href="{{ url_for('static', filename='fonts/num.otf') }}" as="font" type="font/otf" crossorigin>
</head>
<body class="{% block body_class %}{% endblock %}">
    <!-- 全局加载指示器 -->
    <div id="global-loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">数据加载中...</div>
    </div>
    
    <!-- 主要内容区域 -->
    <main id="main-content" class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <!-- 全局错误提示 -->
    <div id="error-toast" class="error-toast hidden">
        <div class="error-content">
            <span class="error-icon">⚠️</span>
            <span class="error-message"></span>
            <button class="error-close">×</button>
        </div>
    </div>
    
    <!-- 核心脚本 -->
    <script src="{{ url_for('static', filename='js/core/api-client.js') }}"></script>
    <script src="{{ url_for('static', filename='js/core/cache-manager.js') }}"></script>
    <script src="{{ url_for('static', filename='js/core/event-bus.js') }}"></script>
    
    <!-- 页面特定脚本 -->
    {% block scripts %}{% endblock %}
    
    <!-- 全局初始化脚本 -->
    <script>
        // 全局错误处理
        window.addEventListener('error', function(e) {
            console.error('Global error:', e.error);
            showErrorToast('系统错误：' + e.message);
        });
        
        // 全局配置
        window.APP_CONFIG = {
            customerId: {{ customer_id|default('null') }},
            apiBaseUrl: '/api/v1',
            refreshInterval: {{ refresh_interval|default(5000) }},
            debug: {{ 'true' if debug else 'false' }}
        };
    </script>
</body>
</html>
```

#### 1.3 组件化架构实现

##### 图表组件示例 (health-score-chart.js)
```javascript
/**
 * 健康评分图表组件
 */
class HealthScoreChart {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: 400,
            height: 300,
            theme: 'default',
            autoRefresh: true,
            refreshInterval: 5000,
            ...options
        };
        
        this.chart = null;
        this.data = null;
        this.refreshTimer = null;
        
        this.init();
    }
    
    init() {
        this.createChart();
        this.bindEvents();
        
        if (this.options.autoRefresh) {
            this.startAutoRefresh();
        }
    }
    
    createChart() {
        // 使用 ECharts 创建图表
        this.chart = echarts.init(this.container);
        
        const defaultOption = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}%'
            },
            series: [{
                type: 'gauge',
                min: 0,
                max: 100,
                radius: '80%',
                axisLine: {
                    lineStyle: {
                        width: 8,
                        color: [
                            [0.2, '#ff4757'],
                            [0.4, '#ffa726'],
                            [0.6, '#66bb6a'],
                            [0.8, '#42a5f5'],
                            [1, '#00ff9d']
                        ]
                    }
                },
                pointer: {
                    itemStyle: {
                        color: '#00e4ff'
                    }
                },
                axisTick: {
                    distance: -8,
                    length: 4,
                    lineStyle: {
                        color: '#fff',
                        width: 1
                    }
                },
                splitLine: {
                    distance: -15,
                    length: 8,
                    lineStyle: {
                        color: '#fff',
                        width: 2
                    }
                },
                axisLabel: {
                    color: '#fff',
                    distance: 20,
                    fontSize: 10
                },
                detail: {
                    valueAnimation: true,
                    formatter: '{value}%',
                    color: '#00e4ff',
                    fontSize: 20,
                    fontWeight: 'bold',
                    offsetCenter: [0, '70%']
                },
                data: [{
                    value: 0,
                    name: '健康评分'
                }]
            }]
        };
        
        this.chart.setOption(defaultOption);
        this.handleResize();
    }
    
    updateData(newData) {
        if (!this.chart || !newData) return;
        
        this.data = newData;
        
        const option = {
            series: [{
                data: [{
                    value: newData.score,
                    name: newData.title || '健康评分'
                }]
            }]
        };
        
        this.chart.setOption(option, false, true);
        this.emitEvent('data-updated', newData);
    }
    
    async loadData(params = {}) {
        try {
            this.showLoading();
            
            const cacheKey = `health-score-${JSON.stringify(params)}`;
            let data = CacheManager.get(cacheKey);
            
            if (!data) {
                data = await ApiClient.get('/health/score/comprehensive', params);
                CacheManager.set(cacheKey, data, 60000); // 缓存1分钟
            }
            
            this.updateData(data);
            this.hideLoading();
            
        } catch (error) {
            this.hideLoading();
            this.showError('健康评分数据加载失败');
            console.error('Health score load error:', error);
        }
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        this.refreshTimer = setInterval(() => {
            if (this.isVisible()) {
                this.refresh();
            }
        }, this.options.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
    
    refresh() {
        return this.loadData(this.lastParams);
    }
    
    showLoading() {
        this.container.classList.add('loading');
    }
    
    hideLoading() {
        this.container.classList.remove('loading');
    }
    
    showError(message) {
        console.error('Chart error:', message);
        this.emitEvent('error', { message });
    }
    
    isVisible() {
        const rect = this.container.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }
    
    handleResize() {
        if (this.chart) {
            this.chart.resize();
        }
    }
    
    bindEvents() {
        // 窗口大小调整
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else if (this.options.autoRefresh) {
                this.startAutoRefresh();
            }
        });
    }
    
    emitEvent(eventName, data) {
        EventBus.emit(`chart:${eventName}`, {
            component: this,
            data
        });
    }
    
    destroy() {
        this.stopAutoRefresh();
        
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
        
        window.removeEventListener('resize', this.handleResize.bind(this));
    }
}
```

### 阶段二：性能优化实施（第 3-4 周）

#### 2.1 API 客户端优化

##### 统一 API 客户端 (api-client.js)
```javascript
/**
 * 统一 API 客户端 - 支持批处理、缓存、重试
 */
class ApiClient {
    constructor() {
        this.baseURL = window.APP_CONFIG?.apiBaseUrl || '/api/v1';
        this.timeout = 10000;
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: [1000, 2000, 4000],
            retryConditions: [
                error => error.status >= 500,
                error => error.code === 'NETWORK_ERROR',
                error => error.code === 'TIMEOUT_ERROR'
            ]
        };
        
        this.batchQueue = new Map();
        this.batchTimeout = 100;
        this.pendingRequests = new Map();
    }
    
    /**
     * 通用请求方法
     */
    async request(endpoint, options = {}) {
        const requestKey = this.generateRequestKey(endpoint, options);
        
        // 防止重复请求
        if (this.pendingRequests.has(requestKey)) {
            return this.pendingRequests.get(requestKey);
        }
        
        const requestPromise = this._executeRequest(endpoint, options);
        this.pendingRequests.set(requestKey, requestPromise);
        
        try {
            const result = await requestPromise;
            return result;
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }
    
    async _executeRequest(endpoint, options = {}) {
        const fullURL = this.buildURL(endpoint, options.params);
        let lastError;
        
        for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                const response = await fetch(fullURL, {
                    method: options.method || 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Request-ID': this.generateRequestId(),
                        'X-Customer-ID': window.APP_CONFIG?.customerId || '',
                        ...options.headers
                    },
                    body: options.body ? JSON.stringify(options.body) : undefined,
                    signal: controller.signal,
                    ...options.fetchOptions
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new ApiError(response.status, await response.json());
                }
                
                const data = await response.json();
                this.logRequest(endpoint, options, data, attempt);
                
                return data;
                
            } catch (error) {
                lastError = this.normalizeError(error);
                
                if (attempt < this.retryConfig.maxRetries && this.shouldRetry(lastError)) {
                    await this.delay(this.retryConfig.retryDelay[attempt]);
                    console.warn(`API请求重试 ${attempt + 1}/${this.retryConfig.maxRetries}:`, endpoint);
                    continue;
                }
                
                break;
            }
        }
        
        this.logError(endpoint, options, lastError);
        throw lastError;
    }
    
    /**
     * GET 请求
     */
    async get(endpoint, params = {}) {
        return this.request(endpoint, { params });
    }
    
    /**
     * POST 请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, { 
            method: 'POST', 
            body: data 
        });
    }
    
    /**
     * PUT 请求
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, { 
            method: 'PUT', 
            body: data 
        });
    }
    
    /**
     * DELETE 请求
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
    
    /**
     * 批量请求
     */
    async batch(requests) {
        const promises = requests.map(req => {
            return this.request(req.endpoint, req.options);
        });
        
        const results = await Promise.allSettled(promises);
        
        return results.map((result, index) => ({
            request: requests[index],
            success: result.status === 'fulfilled',
            data: result.status === 'fulfilled' ? result.value : null,
            error: result.status === 'rejected' ? result.reason : null
        }));
    }
    
    /**
     * 并行请求
     */
    async parallel(requests) {
        const batchResults = await this.batch(requests);
        const results = {};
        
        batchResults.forEach((result, index) => {
            const key = requests[index].key || `request_${index}`;
            results[key] = result;
        });
        
        return results;
    }
    
    /**
     * 缓存请求
     */
    async cached(endpoint, params = {}, cacheTime = 60000) {
        const cacheKey = this.generateCacheKey(endpoint, params);
        let data = CacheManager.get(cacheKey);
        
        if (!data) {
            data = await this.get(endpoint, params);
            CacheManager.set(cacheKey, data, cacheTime);
        }
        
        return data;
    }
    
    // 辅助方法
    buildURL(endpoint, params = {}) {
        let url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`;
        
        if (Object.keys(params).length > 0) {
            const searchParams = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    searchParams.append(key, value);
                }
            });
            url += '?' + searchParams.toString();
        }
        
        return url;
    }
    
    generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    generateRequestKey(endpoint, options) {
        return `${endpoint}_${JSON.stringify(options)}`;
    }
    
    generateCacheKey(endpoint, params) {
        return `api_${endpoint}_${JSON.stringify(params)}`;
    }
    
    shouldRetry(error) {
        return this.retryConfig.retryConditions.some(condition => condition(error));
    }
    
    normalizeError(error) {
        if (error.name === 'AbortError') {
            return new ApiError(408, { message: '请求超时' });
        }
        if (error instanceof ApiError) {
            return error;
        }
        return new ApiError(500, { message: error.message || '网络错误' });
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    logRequest(endpoint, options, data, attempts) {
        if (window.APP_CONFIG?.debug) {
            console.log(`✓ API Success [${attempts ? attempts + 1 : 1}次]:`, {
                endpoint,
                options,
                dataSize: JSON.stringify(data).length,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    logError(endpoint, options, error) {
        console.error('✗ API Error:', {
            endpoint,
            options,
            error: error.message,
            status: error.status,
            timestamp: new Date().toISOString()
        });
    }
}

/**
 * API 错误类
 */
class ApiError extends Error {
    constructor(status, data) {
        super(data.message || 'API请求失败');
        this.name = 'ApiError';
        this.status = status;
        this.code = data.code || 'API_ERROR';
        this.details = data.errors || [];
    }
}

// 全局实例
window.ApiClient = new ApiClient();
```

#### 2.2 缓存管理系统

##### 智能缓存管理 (cache-manager.js)
```javascript
/**
 * 多层缓存管理系统
 */
class CacheManager {
    constructor() {
        this.memoryCache = new Map();
        this.storageCache = this.getStorageEngine();
        this.maxMemorySize = 50; // 最大内存缓存条目数
        this.defaultTTL = 60000; // 默认TTL: 1分钟
        
        this.cacheStats = {
            hits: 0,
            misses: 0,
            sets: 0,
            deletes: 0
        };
        
        this.init();
    }
    
    init() {
        // 清理过期缓存
        this.startCleanupTimer();
        
        // 监听存储变化
        this.bindStorageEvents();
        
        // 页面关闭时清理
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    /**
     * 获取缓存
     */
    get(key) {
        // 先检查内存缓存
        const memoryItem = this.memoryCache.get(key);
        if (memoryItem && !this.isExpired(memoryItem)) {
            this.cacheStats.hits++;
            return memoryItem.data;
        }
        
        // 再检查存储缓存
        try {
            const storageData = this.storageCache.getItem(this.getStorageKey(key));
            if (storageData) {
                const item = JSON.parse(storageData);
                if (!this.isExpired(item)) {
                    // 提升到内存缓存
                    this.setMemoryCache(key, item.data, item.expires);
                    this.cacheStats.hits++;
                    return item.data;
                }
            }
        } catch (error) {
            console.warn('Storage cache error:', error);
        }
        
        this.cacheStats.misses++;
        return null;
    }
    
    /**
     * 设置缓存
     */
    set(key, data, ttl = this.defaultTTL) {
        const expires = Date.now() + ttl;
        const item = { data, expires, timestamp: Date.now() };
        
        // 设置内存缓存
        this.setMemoryCache(key, data, expires);
        
        // 设置存储缓存
        try {
            this.storageCache.setItem(
                this.getStorageKey(key), 
                JSON.stringify(item)
            );
        } catch (error) {
            console.warn('Storage cache set error:', error);
            // 存储失败时清理一些旧缓存
            this.cleanupStorage();
        }
        
        this.cacheStats.sets++;
    }
    
    /**
     * 删除缓存
     */
    delete(key) {
        this.memoryCache.delete(key);
        
        try {
            this.storageCache.removeItem(this.getStorageKey(key));
        } catch (error) {
            console.warn('Storage cache delete error:', error);
        }
        
        this.cacheStats.deletes++;
    }
    
    /**
     * 清空所有缓存
     */
    clear() {
        this.memoryCache.clear();
        
        try {
            const keys = Object.keys(this.storageCache);
            keys.forEach(key => {
                if (key.startsWith('cache_')) {
                    this.storageCache.removeItem(key);
                }
            });
        } catch (error) {
            console.warn('Storage cache clear error:', error);
        }
    }
    
    /**
     * 批量设置
     */
    setMultiple(items, ttl = this.defaultTTL) {
        Object.entries(items).forEach(([key, data]) => {
            this.set(key, data, ttl);
        });
    }
    
    /**
     * 批量获取
     */
    getMultiple(keys) {
        const results = {};
        keys.forEach(key => {
            results[key] = this.get(key);
        });
        return results;
    }
    
    /**
     * 检查键是否存在
     */
    has(key) {
        return this.get(key) !== null;
    }
    
    /**
     * 获取缓存统计
     */
    getStats() {
        const hitRate = this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) * 100;
        
        return {
            ...this.cacheStats,
            hitRate: isNaN(hitRate) ? 0 : Math.round(hitRate * 100) / 100,
            memorySize: this.memoryCache.size,
            timestamp: Date.now()
        };
    }
    
    // 私有方法
    setMemoryCache(key, data, expires) {
        // 检查内存限制
        if (this.memoryCache.size >= this.maxMemorySize) {
            this.evictOldest();
        }
        
        this.memoryCache.set(key, {
            data,
            expires,
            timestamp: Date.now()
        });
    }
    
    evictOldest() {
        let oldestKey = null;
        let oldestTime = Date.now();
        
        for (const [key, item] of this.memoryCache) {
            if (item.timestamp < oldestTime) {
                oldestTime = item.timestamp;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.memoryCache.delete(oldestKey);
        }
    }
    
    isExpired(item) {
        return Date.now() > item.expires;
    }
    
    getStorageKey(key) {
        return `cache_${key}`;
    }
    
    getStorageEngine() {
        try {
            // 测试 localStorage 可用性
            const testKey = 'cache_test';
            localStorage.setItem(testKey, 'test');
            localStorage.removeItem(testKey);
            return localStorage;
        } catch (error) {
            // 回退到内存存储
            console.warn('localStorage not available, using memory storage');
            return new Map();
        }
    }
    
    startCleanupTimer() {
        // 每5分钟清理一次过期缓存
        setInterval(() => {
            this.cleanupExpired();
        }, 5 * 60 * 1000);
    }
    
    cleanupExpired() {
        // 清理内存缓存
        for (const [key, item] of this.memoryCache) {
            if (this.isExpired(item)) {
                this.memoryCache.delete(key);
            }
        }
        
        // 清理存储缓存
        this.cleanupStorage();
    }
    
    cleanupStorage() {
        if (this.storageCache instanceof Map) return;
        
        try {
            const keys = Object.keys(this.storageCache);
            keys.forEach(key => {
                if (key.startsWith('cache_')) {
                    try {
                        const data = JSON.parse(this.storageCache.getItem(key));
                        if (this.isExpired(data)) {
                            this.storageCache.removeItem(key);
                        }
                    } catch (error) {
                        // 数据损坏，删除
                        this.storageCache.removeItem(key);
                    }
                }
            });
        } catch (error) {
            console.warn('Storage cleanup error:', error);
        }
    }
    
    bindStorageEvents() {
        if (this.storageCache instanceof Map) return;
        
        window.addEventListener('storage', (e) => {
            if (e.key && e.key.startsWith('cache_')) {
                const cacheKey = e.key.substring(6); // 移除 'cache_' 前缀
                this.memoryCache.delete(cacheKey);
            }
        });
    }
    
    cleanup() {
        this.cleanupExpired();
    }
}

// 全局实例
window.CacheManager = new CacheManager();
```

### 阶段三：组件系统建设（第 5-6 周）

#### 3.1 主页面重构示例

##### main_optimized.html
```html
{% extends "layouts/dashboard_layout.html" %}

{% block title %}智能健康数据分析平台 - 主页{% endblock %}

{% block stylesheets %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/main.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/components/charts.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/components/panels.css') }}">
{% endblock %}

{% block body_class %}main-dashboard{% endblock %}

{% block content %}
<div class="dashboard-container" id="dashboard-container">
    <!-- 顶部状态栏 -->
    <header class="dashboard-header">
        {% include 'components/widgets/status_indicator.html' %}
        {% include 'components/widgets/refresh_controls.html' %}
    </header>
    
    <!-- 主要内容区域 -->
    <div class="dashboard-content">
        <!-- 左侧面板 -->
        <aside class="left-panel">
            {% include 'components/panels/summary_panel.html' %}
            {% include 'components/panels/alert_panel.html' %}
        </aside>
        
        <!-- 中央图表区 -->
        <section class="center-panel">
            <div class="chart-grid">
                {% include 'components/charts/health_score_chart.html' %}
                {% include 'components/charts/trend_chart.html' %}
                {% include 'components/charts/distribution_chart.html' %}
            </div>
        </section>
        
        <!-- 右侧面板 -->
        <aside class="right-panel">
            {% include 'components/panels/device_info_panel.html' %}
            {% include 'components/panels/message_panel.html' %}
        </aside>
    </div>
    
    <!-- 底部工具栏 -->
    <footer class="dashboard-footer">
        {% include 'components/widgets/pagination_controls.html' %}
        {% include 'components/widgets/export_controls.html' %}
    </footer>
</div>

<!-- 模态对话框 -->
<div id="modal-container"></div>
{% endblock %}

{% block scripts %}
<!-- ECharts 库 -->
<script src="{{ url_for('static', filename='js/lib/echarts-5.4.0.min.js') }}"></script>

<!-- 页面组件 -->
<script src="{{ url_for('static', filename='js/components/health-chart.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/device-panel.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/message-panel.js') }}"></script>
<script src="{{ url_for('static', filename='js/components/alert-panel.js') }}"></script>

<!-- 页面主脚本 -->
<script src="{{ url_for('static', filename='js/pages/main-page.js') }}"></script>

<script>
// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    const mainPage = new MainPage({
        container: '#dashboard-container',
        refreshInterval: 5000,
        autoRefresh: true,
        customerId: {{ customer_id|default('null') }}
    });
    
    mainPage.init();
    
    // 全局引用，便于调试
    window.mainPage = mainPage;
});
</script>
{% endblock %}
```

#### 3.2 页面控制器实现

##### main-page.js - 主页控制器
```javascript
/**
 * 主页面控制器
 */
class MainPage {
    constructor(options = {}) {
        this.options = {
            container: '#dashboard-container',
            refreshInterval: 5000,
            autoRefresh: true,
            customerId: null,
            ...options
        };
        
        this.container = document.querySelector(this.options.container);
        this.components = new Map();
        this.isInitialized = false;
        this.refreshTimer = null;
        this.lastRefreshTime = null;
    }
    
    async init() {
        if (this.isInitialized) return;
        
        try {
            this.showLoading();
            
            // 初始化组件
            await this.initComponents();
            
            // 绑定事件
            this.bindEvents();
            
            // 加载初始数据
            await this.loadInitialData();
            
            // 启动自动刷新
            if (this.options.autoRefresh) {
                this.startAutoRefresh();
            }
            
            this.isInitialized = true;
            this.hideLoading();
            
            console.log('主页面初始化完成');
            
        } catch (error) {
            this.hideLoading();
            this.showError('页面初始化失败: ' + error.message);
            console.error('Main page init error:', error);
        }
    }
    
    async initComponents() {
        const componentConfigs = [
            {
                name: 'healthChart',
                class: HealthScoreChart,
                container: '#health-score-chart',
                options: {
                    autoRefresh: false // 由页面控制刷新
                }
            },
            {
                name: 'trendChart',
                class: TrendChart,
                container: '#trend-chart',
                options: {
                    timeRange: '24h'
                }
            },
            {
                name: 'devicePanel',
                class: DevicePanel,
                container: '#device-panel',
                options: {}
            },
            {
                name: 'messagePanel',
                class: MessagePanel,
                container: '#message-panel',
                options: {
                    maxMessages: 10
                }
            },
            {
                name: 'alertPanel',
                class: AlertPanel,
                container: '#alert-panel',
                options: {
                    maxAlerts: 5
                }
            }
        ];
        
        // 并行初始化组件
        const initPromises = componentConfigs.map(async (config) => {
            try {
                const container = document.querySelector(config.container);
                if (!container) {
                    console.warn(`组件容器不存在: ${config.container}`);
                    return;
                }
                
                const component = new config.class(container, config.options);
                await component.init?.();
                
                this.components.set(config.name, component);
                console.log(`组件初始化完成: ${config.name}`);
                
            } catch (error) {
                console.error(`组件初始化失败 ${config.name}:`, error);
            }
        });
        
        await Promise.all(initPromises);
    }
    
    async loadInitialData() {
        const loadTasks = [];
        
        // 准备所有数据加载任务
        if (this.components.has('healthChart')) {
            loadTasks.push({
                name: 'healthScore',
                task: () => this.loadHealthScore()
            });
        }
        
        if (this.components.has('trendChart')) {
            loadTasks.push({
                name: 'trendData',
                task: () => this.loadTrendData()
            });
        }
        
        if (this.components.has('devicePanel')) {
            loadTasks.push({
                name: 'deviceInfo',
                task: () => this.loadDeviceInfo()
            });
        }
        
        if (this.components.has('messagePanel')) {
            loadTasks.push({
                name: 'messages',
                task: () => this.loadMessages()
            });
        }
        
        if (this.components.has('alertPanel')) {
            loadTasks.push({
                name: 'alerts',
                task: () => this.loadAlerts()
            });
        }
        
        // 并行执行所有加载任务
        const results = await Promise.allSettled(
            loadTasks.map(task => task.task())
        );
        
        // 记录加载结果
        results.forEach((result, index) => {
            const taskName = loadTasks[index].name;
            if (result.status === 'fulfilled') {
                console.log(`数据加载成功: ${taskName}`);
            } else {
                console.error(`数据加载失败 ${taskName}:`, result.reason);
            }
        });
        
        this.lastRefreshTime = Date.now();
    }
    
    async loadHealthScore() {
        const params = {
            orgId: this.options.customerId,
            days: 7,
            includeFactors: true
        };
        
        const data = await ApiClient.cached('/health/score/comprehensive', params, 60000);
        
        const healthChart = this.components.get('healthChart');
        if (healthChart) {
            healthChart.updateData(data);
        }
        
        return data;
    }
    
    async loadTrendData() {
        const params = {
            orgId: this.options.customerId,
            timeRange: '24h',
            metrics: ['health_score', 'device_count', 'alert_count']
        };
        
        const data = await ApiClient.cached('/health/trends/analysis', params, 300000); // 缓存5分钟
        
        const trendChart = this.components.get('trendChart');
        if (trendChart) {
            trendChart.updateData(data);
        }
        
        return data;
    }
    
    async loadDeviceInfo() {
        const params = {
            orgId: this.options.customerId,
            includeOffline: true
        };
        
        const data = await ApiClient.cached('/organization/devices/summary', params, 30000); // 缓存30秒
        
        const devicePanel = this.components.get('devicePanel');
        if (devicePanel) {
            devicePanel.updateData(data);
        }
        
        return data;
    }
    
    async loadMessages() {
        const params = {
            orgId: this.options.customerId,
            limit: 10,
            type: 'SYSTEM,ALERT'
        };
        
        const data = await ApiClient.get('/messages/recent', params);
        
        const messagePanel = this.components.get('messagePanel');
        if (messagePanel) {
            messagePanel.updateData(data);
        }
        
        return data;
    }
    
    async loadAlerts() {
        const params = {
            orgId: this.options.customerId,
            status: 'ACTIVE',
            limit: 5
        };
        
        const data = await ApiClient.get('/alerts/active', params);
        
        const alertPanel = this.components.get('alertPanel');
        if (alertPanel) {
            alertPanel.updateData(data);
        }
        
        return data;
    }
    
    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refresh());
        }
        
        // 自动刷新切换
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else if (this.options.autoRefresh) {
                this.startAutoRefresh();
            }
        });
        
        // 组件事件
        EventBus.on('component:error', (data) => {
            console.error('组件错误:', data);
            this.showError(`组件错误: ${data.message}`);
        });
        
        EventBus.on('alert:new', (data) => {
            this.handleNewAlert(data);
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refresh();
                        break;
                }
            }
        });
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        this.refreshTimer = setInterval(() => {
            if (this.isPageVisible() && this.isInitialized) {
                this.refresh();
            }
        }, this.options.refreshInterval);
        
        console.log(`自动刷新启动，间隔: ${this.options.refreshInterval}ms`);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('自动刷新停止');
        }
    }
    
    async refresh() {
        if (!this.isInitialized) return;
        
        try {
            console.log('开始刷新页面数据...');
            const startTime = Date.now();
            
            this.showRefreshing();
            
            // 清理相关缓存
            this.clearRelevantCache();
            
            // 重新加载数据
            await this.loadInitialData();
            
            const duration = Date.now() - startTime;
            console.log(`页面刷新完成，耗时: ${duration}ms`);
            
            this.hideRefreshing();
            this.showSuccess('数据刷新成功');
            
        } catch (error) {
            this.hideRefreshing();
            this.showError('数据刷新失败: ' + error.message);
            console.error('Refresh error:', error);
        }
    }
    
    clearRelevantCache() {
        const keysToDelete = [
            'health-score',
            'trend-data', 
            'device-info',
            'messages',
            'alerts'
        ];
        
        keysToDelete.forEach(key => {
            // 清理相关的缓存项
            for (const cacheKey of CacheManager.memoryCache.keys()) {
                if (cacheKey.includes(key)) {
                    CacheManager.delete(cacheKey);
                }
            }
        });
    }
    
    handleNewAlert(alertData) {
        // 播放提示音
        this.playNotificationSound();
        
        // 更新告警面板
        const alertPanel = this.components.get('alertPanel');
        if (alertPanel) {
            alertPanel.addNewAlert(alertData);
        }
        
        // 显示通知
        this.showNotification('新告警', alertData.message, 'warning');
    }
    
    isPageVisible() {
        return !document.hidden;
    }
    
    showLoading() {
        document.getElementById('global-loading')?.classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('global-loading')?.classList.add('hidden');
    }
    
    showRefreshing() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('refreshing');
            refreshBtn.disabled = true;
        }
    }
    
    hideRefreshing() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.remove('refreshing');
            refreshBtn.disabled = false;
        }
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    showToast(message, type = 'info') {
        // 简单的 toast 实现
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    showNotification(title, message, type = 'info') {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/images/icon.png'
            });
        }
    }
    
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.wav');
            audio.volume = 0.3;
            audio.play().catch(e => {
                console.warn('无法播放提示音:', e);
            });
        } catch (error) {
            console.warn('提示音播放失败:', error);
        }
    }
    
    destroy() {
        this.stopAutoRefresh();
        
        // 销毁所有组件
        this.components.forEach((component, name) => {
            try {
                if (component.destroy) {
                    component.destroy();
                }
            } catch (error) {
                console.error(`组件销毁失败 ${name}:`, error);
            }
        });
        
        this.components.clear();
        this.isInitialized = false;
        
        console.log('主页面已销毁');
    }
}
```

### 阶段四：样式系统优化（第 7-8 周）

#### 4.1 CSS 架构重构

##### 变量系统 (variables.css)
```css
/**
 * CSS 变量系统 - 主题和设计令牌
 */

:root {
    /* ============= 颜色系统 ============= */
    
    /* 主色调 */
    --primary-color: #00ff9d;
    --primary-light: #33ffb5;
    --primary-dark: #00cc7d;
    --primary-rgb: 0, 255, 157;
    
    /* 次要色调 */
    --secondary-color: #00e4ff;
    --secondary-light: #33e9ff;
    --secondary-dark: #00b7cc;
    --secondary-rgb: 0, 228, 255;
    
    /* 强调色 */
    --accent-color: #ff6b6b;
    --accent-light: #ff8a8a;
    --accent-dark: #ff4757;
    --accent-rgb: 255, 107, 107;
    
    /* 警告色系 */
    --warning-color: #ffa726;
    --warning-light: #ffb74d;
    --warning-dark: #f57c00;
    
    /* 成功色系 */
    --success-color: #66bb6a;
    --success-light: #81c784;
    --success-dark: #4caf50;
    
    /* 错误色系 */
    --error-color: #ef5350;
    --error-light: #f48fb1;
    --error-dark: #c62828;
    
    /* 信息色系 */
    --info-color: #42a5f5;
    --info-light: #64b5f6;
    --info-dark: #1976d2;
    
    /* ============= 背景色系统 ============= */
    
    /* 主背景 */
    --bg-primary: #0a1525;
    --bg-primary-rgb: 10, 21, 37;
    
    /* 次要背景 */
    --bg-secondary: rgba(13, 20, 33, 0.95);
    --bg-secondary-rgb: 13, 20, 33;
    
    /* 卡片背景 */
    --bg-card: rgba(6, 18, 25, 0.9);
    --bg-card-hover: rgba(0, 21, 41, 0.95);
    
    /* 面板背景 */
    --bg-panel: linear-gradient(145deg, rgba(13, 20, 33, 0.95), rgba(6, 18, 25, 0.95));
    
    /* 覆盖层背景 */
    --bg-overlay: rgba(0, 0, 0, 0.8);
    --bg-modal: rgba(0, 0, 0, 0.9);
    
    /* ============= 文字色系统 ============= */
    
    /* 主要文字 */
    --text-primary: #ffffff;
    --text-primary-rgb: 255, 255, 255;
    
    /* 次要文字 */
    --text-secondary: rgba(255, 255, 255, 0.8);
    --text-secondary-rgb: 255, 255, 255;
    
    /* 禁用文字 */
    --text-disabled: rgba(255, 255, 255, 0.4);
    
    /* 链接文字 */
    --text-link: var(--secondary-color);
    --text-link-hover: var(--secondary-light);
    
    /* ============= 边框色系统 ============= */
    
    /* 主边框 */
    --border-primary: rgba(0, 255, 157, 0.3);
    --border-secondary: rgba(0, 228, 255, 0.2);
    
    /* 输入框边框 */
    --border-input: rgba(255, 255, 255, 0.2);
    --border-input-focus: var(--primary-color);
    --border-input-error: var(--error-color);
    
    /* 分割线 */
    --border-divider: rgba(255, 255, 255, 0.1);
    
    /* ============= 阴影系统 ============= */
    
    /* 基础阴影 */
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.15);
    --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.2);
    --shadow-xl: 0 16px 32px rgba(0, 0, 0, 0.25);
    
    /* 彩色阴影 */
    --shadow-primary: 0 4px 15px rgba(var(--primary-rgb), 0.3);
    --shadow-secondary: 0 4px 15px rgba(var(--secondary-rgb), 0.3);
    --shadow-accent: 0 4px 15px rgba(var(--accent-rgb), 0.3);
    
    /* 发光效果 */
    --glow-primary: 0 0 20px rgba(var(--primary-rgb), 0.5);
    --glow-secondary: 0 0 20px rgba(var(--secondary-rgb), 0.5);
    --glow-accent: 0 0 20px rgba(var(--accent-rgb), 0.5);
    
    /* ============= 尺寸系统 ============= */
    
    /* 间距 */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-2xl: 48px;
    --spacing-3xl: 64px;
    
    /* 圆角 */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 50%;
    
    /* 边框宽度 */
    --border-width: 1px;
    --border-width-thick: 2px;
    
    /* ============= 字体系统 ============= */
    
    /* 字体族 */
    --font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
    --font-mono: 'Courier New', Monaco, Consolas, monospace;
    --font-number: 'NumFont', var(--font-mono);
    
    /* 字体大小 */
    --font-xs: 10px;
    --font-sm: 12px;
    --font-md: 14px;
    --font-lg: 16px;
    --font-xl: 18px;
    --font-2xl: 24px;
    --font-3xl: 32px;
    --font-4xl: 48px;
    
    /* 字体重量 */
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;
    
    /* 行高 */
    --line-height-tight: 1.2;
    --line-height-normal: 1.5;
    --line-height-relaxed: 1.7;
    
    /* ============= 层级系统 ============= */
    
    --z-dropdown: 1000;
    --z-sticky: 1010;
    --z-fixed: 1020;
    --z-modal-backdrop: 1030;
    --z-modal: 1040;
    --z-popover: 1050;
    --z-tooltip: 1060;
    --z-toast: 1070;
    
    /* ============= 动画系统 ============= */
    
    /* 过渡时长 */
    --transition-fast: 150ms;
    --transition-normal: 300ms;
    --transition-slow: 500ms;
    
    /* 缓动函数 */
    --ease-out: cubic-bezier(0.4, 0, 0.2, 1);
    --ease-in: cubic-bezier(0.4, 0, 1, 1);
    --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
    
    /* ============= 断点系统 ============= */
    
    --breakpoint-sm: 640px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 1024px;
    --breakpoint-xl: 1280px;
    --breakpoint-2xl: 1536px;
    
    /* ============= 大屏特定变量 ============= */
    
    /* 大屏布局 */
    --dashboard-sidebar-width: 280px;
    --dashboard-header-height: 80px;
    --dashboard-footer-height: 60px;
    
    /* 图表尺寸 */
    --chart-height-sm: 200px;
    --chart-height-md: 300px;
    --chart-height-lg: 400px;
    
    /* 面板尺寸 */
    --panel-width-sm: 300px;
    --panel-width-md: 400px;
    --panel-width-lg: 500px;
    
    /* 卡片尺寸 */
    --card-min-height: 120px;
    --card-max-width: 400px;
}

/* ============= 主题变体 ============= */

/* 深蓝主题 */
[data-theme="deep-blue"] {
    --primary-color: #1890ff;
    --primary-light: #40a9ff;
    --primary-dark: #0c7cd5;
    --primary-rgb: 24, 144, 255;
    
    --bg-primary: #001529;
    --bg-primary-rgb: 0, 21, 41;
    
    --border-primary: rgba(24, 144, 255, 0.3);
    --shadow-primary: 0 4px 15px rgba(24, 144, 255, 0.3);
    --glow-primary: 0 0 20px rgba(24, 144, 255, 0.5);
}

/* 紫罗兰主题 */
[data-theme="purple"] {
    --primary-color: #722ed1;
    --primary-light: #9254de;
    --primary-dark: #531dab;
    --primary-rgb: 114, 46, 209;
    
    --bg-primary: #1a0d2e;
    --bg-primary-rgb: 26, 13, 46;
    
    --border-primary: rgba(114, 46, 209, 0.3);
    --shadow-primary: 0 4px 15px rgba(114, 46, 209, 0.3);
    --glow-primary: 0 0 20px rgba(114, 46, 209, 0.5);
}

/* 绿色生态主题 */
[data-theme="eco-green"] {
    --primary-color: #52c41a;
    --primary-light: #73d13d;
    --primary-dark: #389e0d;
    --primary-rgb: 82, 196, 26;
    
    --bg-primary: #162312;
    --bg-primary-rgb: 22, 35, 18;
    
    --border-primary: rgba(82, 196, 26, 0.3);
    --shadow-primary: 0 4px 15px rgba(82, 196, 26, 0.3);
    --glow-primary: 0 0 20px rgba(82, 196, 26, 0.5);
}

/* ============= 响应式变量 ============= */

@media (max-width: 768px) {
    :root {
        /* 移动端调整 */
        --dashboard-sidebar-width: 100%;
        --panel-width-md: 100%;
        --font-sm: 11px;
        --font-md: 13px;
        --spacing-md: 12px;
        --spacing-lg: 20px;
    }
}

@media (min-width: 1440px) {
    :root {
        /* 大屏调整 */
        --font-md: 15px;
        --font-lg: 17px;
        --spacing-lg: 28px;
        --spacing-xl: 36px;
    }
}

/* ============= 高对比度主题 ============= */
@media (prefers-contrast: high) {
    :root {
        --text-primary: #ffffff;
        --text-secondary: #e0e0e0;
        --border-primary: rgba(255, 255, 255, 0.5);
        --border-secondary: rgba(255, 255, 255, 0.3);
    }
}

/* ============= 减少动画主题 ============= */
@media (prefers-reduced-motion: reduce) {
    :root {
        --transition-fast: 0ms;
        --transition-normal: 0ms;
        --transition-slow: 0ms;
    }
}
```

#### 4.2 组件样式系统

##### 图表组件样式 (charts.css)
```css
/**
 * 图表组件样式
 */

/* ============= 基础图表容器 ============= */
.chart-container {
    position: relative;
    background: var(--bg-card);
    border: var(--border-width) solid var(--border-secondary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    backdrop-filter: blur(10px);
    transition: all var(--transition-normal) var(--ease-out);
    overflow: hidden;
}

.chart-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, 
        var(--primary-color), 
        var(--secondary-color), 
        var(--primary-color)
    );
    opacity: 0.6;
}

.chart-container:hover {
    border-color: var(--border-primary);
    box-shadow: var(--shadow-primary);
    transform: translateY(-2px);
}

/* ============= 图表标题 ============= */
.chart-title {
    color: var(--text-primary);
    font-size: var(--font-lg);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--spacing-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.chart-title-text {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.chart-title-icon {
    width: 20px;
    height: 20px;
    color: var(--primary-color);
    filter: drop-shadow(0 0 4px rgba(var(--primary-rgb), 0.5));
}

.chart-subtitle {
    color: var(--text-secondary);
    font-size: var(--font-sm);
    font-weight: var(--font-weight-normal);
    margin-top: var(--spacing-xs);
}

/* ============= 图表工具栏 ============= */
.chart-toolbar {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.chart-toolbar-btn {
    width: 32px;
    height: 32px;
    border: var(--border-width) solid var(--border-input);
    border-radius: var(--radius-md);
    background: rgba(var(--bg-primary-rgb), 0.5);
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast) var(--ease-out);
}

.chart-toolbar-btn:hover {
    background: rgba(var(--primary-rgb), 0.1);
    border-color: var(--primary-color);
    color: var(--primary-color);
}

.chart-toolbar-btn:active {
    transform: scale(0.95);
}

.chart-toolbar-btn.active {
    background: rgba(var(--primary-rgb), 0.2);
    border-color: var(--primary-color);
    color: var(--primary-color);
    box-shadow: inset 0 2px 4px rgba(var(--primary-rgb), 0.2);
}

/* ============= 图表内容区域 ============= */
.chart-content {
    position: relative;
    width: 100%;
    min-height: var(--chart-height-md);
}

.chart-canvas {
    width: 100% !important;
    height: 100% !important;
}

/* ============= 图表加载状态 ============= */
.chart-loading {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(var(--bg-primary-rgb), 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    backdrop-filter: blur(4px);
    z-index: 10;
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-normal) var(--ease-out);
}

.chart-container.loading .chart-loading {
    opacity: 1;
    visibility: visible;
}

.chart-loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(var(--primary-rgb), 0.2);
    border-top: 3px solid var(--primary-color);
    border-radius: var(--radius-full);
    animation: chart-spin 1s linear infinite;
}

.chart-loading-text {
    color: var(--text-secondary);
    font-size: var(--font-sm);
    font-weight: var(--font-weight-medium);
}

@keyframes chart-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ============= 图表错误状态 ============= */
.chart-error {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(var(--bg-primary-rgb), 0.9);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    backdrop-filter: blur(4px);
    z-index: 10;
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-normal) var(--ease-out);
}

.chart-container.error .chart-error {
    opacity: 1;
    visibility: visible;
}

.chart-error-icon {
    width: 48px;
    height: 48px;
    color: var(--error-color);
    filter: drop-shadow(0 0 8px rgba(239, 83, 80, 0.3));
}

.chart-error-text {
    color: var(--text-primary);
    font-size: var(--font-md);
    font-weight: var(--font-weight-medium);
    text-align: center;
}

.chart-error-detail {
    color: var(--text-secondary);
    font-size: var(--font-sm);
    text-align: center;
    max-width: 80%;
}

.chart-error-retry {
    margin-top: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--error-color);
    color: var(--text-primary);
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: all var(--transition-fast) var(--ease-out);
}

.chart-error-retry:hover {
    background: var(--error-light);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

/* ============= 健康评分图表特定样式 ============= */
.health-score-chart {
    --chart-primary: var(--primary-color);
    --chart-secondary: var(--secondary-color);
}

.health-score-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: var(--spacing-lg) 0;
}

.health-score-number {
    color: var(--primary-color);
    font-size: var(--font-4xl);
    font-weight: var(--font-weight-bold);
    font-family: var(--font-number);
    text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.5);
    animation: health-score-pulse 2s ease-in-out infinite alternate;
}

.health-score-label {
    color: var(--text-secondary);
    font-size: var(--font-sm);
    font-weight: var(--font-weight-medium);
    margin-top: var(--spacing-sm);
    letter-spacing: 1px;
}

.health-score-status {
    margin-top: var(--spacing-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    font-size: var(--font-xs);
    font-weight: var(--font-weight-semibold);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.health-score-status.excellent {
    background: rgba(102, 187, 106, 0.2);
    color: var(--success-color);
    border: 1px solid rgba(102, 187, 106, 0.3);
}

.health-score-status.good {
    background: rgba(66, 165, 245, 0.2);
    color: var(--info-color);
    border: 1px solid rgba(66, 165, 245, 0.3);
}

.health-score-status.average {
    background: rgba(255, 167, 38, 0.2);
    color: var(--warning-color);
    border: 1px solid rgba(255, 167, 38, 0.3);
}

.health-score-status.poor {
    background: rgba(255, 107, 107, 0.2);
    color: var(--accent-color);
    border: 1px solid rgba(255, 107, 107, 0.3);
}

@keyframes health-score-pulse {
    0% { 
        transform: scale(1);
        text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.5);
    }
    100% { 
        transform: scale(1.05);
        text-shadow: 0 0 30px rgba(var(--primary-rgb), 0.8);
    }
}

/* ============= 趋势图表特定样式 ============= */
.trend-chart {
    --chart-line-color: var(--secondary-color);
    --chart-area-color: rgba(var(--secondary-rgb), 0.1);
}

.trend-stats {
    display: flex;
    justify-content: space-around;
    margin-top: var(--spacing-md);
    padding: var(--spacing-md);
    background: rgba(var(--bg-secondary-rgb), 0.5);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-divider);
}

.trend-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-xs);
}

.trend-stat-value {
    color: var(--text-primary);
    font-size: var(--font-xl);
    font-weight: var(--font-weight-bold);
    font-family: var(--font-number);
}

.trend-stat-label {
    color: var(--text-secondary);
    font-size: var(--font-xs);
    font-weight: var(--font-weight-medium);
}

.trend-stat-change {
    font-size: var(--font-xs);
    font-weight: var(--font-weight-semibold);
    display: flex;
    align-items: center;
    gap: 2px;
}

.trend-stat-change.positive {
    color: var(--success-color);
}

.trend-stat-change.negative {
    color: var(--error-color);
}

.trend-stat-change.neutral {
    color: var(--text-secondary);
}

/* ============= 雷达图特定样式 ============= */
.radar-chart {
    --chart-radar-color: var(--primary-color);
    --chart-radar-fill: rgba(var(--primary-rgb), 0.1);
}

.radar-legend {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    justify-content: center;
}

.radar-legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: rgba(var(--bg-secondary-rgb), 0.5);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-divider);
}

.radar-legend-color {
    width: 12px;
    height: 12px;
    border-radius: var(--radius-sm);
}

.radar-legend-text {
    color: var(--text-secondary);
    font-size: var(--font-xs);
    font-weight: var(--font-weight-medium);
}

/* ============= 响应式设计 ============= */
@media (max-width: 768px) {
    .chart-container {
        padding: var(--spacing-md);
    }
    
    .chart-title {
        font-size: var(--font-md);
        flex-direction: column;
        align-items: flex-start;
        gap: var(--spacing-sm);
    }
    
    .chart-toolbar {
        order: -1;
        align-self: flex-end;
    }
    
    .chart-content {
        min-height: var(--chart-height-sm);
    }
    
    .trend-stats {
        flex-direction: column;
        gap: var(--spacing-sm);
    }
    
    .radar-legend {
        flex-direction: column;
        align-items: center;
    }
}

@media (max-width: 480px) {
    .chart-container {
        padding: var(--spacing-sm);
    }
    
    .health-score-number {
        font-size: var(--font-3xl);
    }
    
    .chart-loading-spinner {
        width: 32px;
        height: 32px;
    }
    
    .chart-error-icon {
        width: 40px;
        height: 40px;
    }
}

/* ============= 打印样式 ============= */
@media print {
    .chart-container {
        background: white !important;
        color: black !important;
        border: 1px solid #ccc !important;
        box-shadow: none !important;
    }
    
    .chart-toolbar {
        display: none !important;
    }
    
    .chart-loading,
    .chart-error {
        display: none !important;
    }
}
```

### 阶段五：测试与部署（第 9-10 周）

#### 5.1 性能测试方案

##### 前端性能测试脚本
```javascript
/**
 * 前端性能测试套件
 */
class PerformanceTestSuite {
    constructor() {
        this.tests = [];
        this.results = [];
        this.observer = null;
    }
    
    // 页面加载性能测试
    async testPageLoad() {
        const test = {
            name: '页面加载性能',
            startTime: performance.now()
        };
        
        // 监听页面加载完成
        await new Promise(resolve => {
            if (document.readyState === 'complete') {
                resolve();
            } else {
                window.addEventListener('load', resolve);
            }
        });
        
        const loadTime = performance.now() - test.startTime;
        const navigation = performance.getEntriesByType('navigation')[0];
        
        return {
            ...test,
            endTime: performance.now(),
            metrics: {
                totalLoadTime: Math.round(loadTime),
                domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart),
                firstPaint: this.getFirstPaint(),
                firstContentfulPaint: this.getFirstContentfulPaint(),
                largestContentfulPaint: await this.getLargestContentfulPaint()
            }
        };
    }
    
    // API 请求性能测试
    async testApiPerformance() {
        const apiTests = [
            { name: '健康评分API', endpoint: '/api/v1/health/score/comprehensive', params: { days: 7 } },
            { name: '设备信息API', endpoint: '/api/v1/organization/devices/summary', params: {} },
            { name: '消息列表API', endpoint: '/api/v1/messages/recent', params: { limit: 10 } },
            { name: '告警列表API', endpoint: '/api/v1/alerts/active', params: { limit: 5 } }
        ];
        
        const results = [];
        
        for (const apiTest of apiTests) {
            const startTime = performance.now();
            
            try {
                await ApiClient.get(apiTest.endpoint, apiTest.params);
                const endTime = performance.now();
                
                results.push({
                    name: apiTest.name,
                    success: true,
                    responseTime: Math.round(endTime - startTime),
                    endpoint: apiTest.endpoint
                });
            } catch (error) {
                results.push({
                    name: apiTest.name,
                    success: false,
                    error: error.message,
                    endpoint: apiTest.endpoint
                });
            }
        }
        
        return {
            name: 'API请求性能测试',
            results,
            averageResponseTime: results
                .filter(r => r.success)
                .reduce((sum, r) => sum + r.responseTime, 0) / results.filter(r => r.success).length
        };
    }
    
    // 内存使用测试
    testMemoryUsage() {
        if (!performance.memory) {
            return { name: '内存使用测试', error: '浏览器不支持内存监控' };
        }
        
        return {
            name: '内存使用测试',
            metrics: {
                usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024), // MB
                totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024), // MB
                jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024), // MB
                memoryUsagePercent: Math.round((performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100)
            }
        };
    }
    
    // 渲染性能测试
    async testRenderingPerformance() {
        const frameData = [];
        let startTime = performance.now();
        let frameCount = 0;
        
        // 监控60帧
        const monitorFrames = () => {
            return new Promise(resolve => {
                const collectFrame = () => {
                    const currentTime = performance.now();
                    frameData.push(currentTime);
                    frameCount++;
                    
                    if (frameCount < 60) {
                        requestAnimationFrame(collectFrame);
                    } else {
                        resolve();
                    }
                };
                
                requestAnimationFrame(collectFrame);
            });
        };
        
        await monitorFrames();
        
        // 计算帧率
        const totalTime = frameData[frameData.length - 1] - frameData[0];
        const averageFPS = Math.round((frameCount - 1) * 1000 / totalTime);
        
        // 计算帧时间变化
        const frameTimes = [];
        for (let i = 1; i < frameData.length; i++) {
            frameTimes.push(frameData[i] - frameData[i - 1]);
        }
        
        const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
        const maxFrameTime = Math.max(...frameTimes);
        
        return {
            name: '渲染性能测试',
            metrics: {
                averageFPS,
                averageFrameTime: Math.round(avgFrameTime),
                maxFrameTime: Math.round(maxFrameTime),
                frameCount,
                totalTime: Math.round(totalTime)
            }
        };
    }
    
    // 缓存性能测试
    async testCachePerformance() {
        const testKey = 'performance_test';
        const testData = { timestamp: Date.now(), data: 'test data' };
        
        // 测试缓存写入
        const writeStartTime = performance.now();
        CacheManager.set(testKey, testData, 60000);
        const writeTime = performance.now() - writeStartTime;
        
        // 测试缓存读取
        const readStartTime = performance.now();
        const cachedData = CacheManager.get(testKey);
        const readTime = performance.now() - readStartTime;
        
        // 清理测试数据
        CacheManager.delete(testKey);
        
        const cacheStats = CacheManager.getStats();
        
        return {
            name: '缓存性能测试',
            metrics: {
                writeTime: Math.round(writeTime * 100) / 100, // 精确到小数点后2位
                readTime: Math.round(readTime * 100) / 100,
                cacheHitRate: cacheStats.hitRate,
                memorySize: cacheStats.memorySize,
                success: cachedData && cachedData.timestamp === testData.timestamp
            }
        };
    }
    
    // 运行所有测试
    async runAllTests() {
        console.log('🚀 开始性能测试...');
        
        this.results = [];
        
        try {
            // 页面加载测试
            const pageLoadTest = await this.testPageLoad();
            this.results.push(pageLoadTest);
            console.log('✅ 页面加载测试完成');
            
            // API性能测试
            const apiTest = await this.testApiPerformance();
            this.results.push(apiTest);
            console.log('✅ API性能测试完成');
            
            // 内存使用测试
            const memoryTest = this.testMemoryUsage();
            this.results.push(memoryTest);
            console.log('✅ 内存使用测试完成');
            
            // 渲染性能测试
            const renderTest = await this.testRenderingPerformance();
            this.results.push(renderTest);
            console.log('✅ 渲染性能测试完成');
            
            // 缓存性能测试
            const cacheTest = await this.testCachePerformance();
            this.results.push(cacheTest);
            console.log('✅ 缓存性能测试完成');
            
            // 生成报告
            this.generateReport();
            
        } catch (error) {
            console.error('❌ 性能测试失败:', error);
        }
    }
    
    // 生成测试报告
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            results: this.results,
            summary: this.generateSummary()
        };
        
        console.log('📊 性能测试报告:', report);
        
        // 显示报告到页面
        this.displayReport(report);
        
        return report;
    }
    
    // 生成测试摘要
    generateSummary() {
        const pageLoadResult = this.results.find(r => r.name === '页面加载性能');
        const apiResult = this.results.find(r => r.name === 'API请求性能测试');
        const memoryResult = this.results.find(r => r.name === '内存使用测试');
        const renderResult = this.results.find(r => r.name === '渲染性能测试');
        const cacheResult = this.results.find(r => r.name === '缓存性能测试');
        
        return {
            pageLoadTime: pageLoadResult?.metrics?.totalLoadTime || 0,
            averageApiResponseTime: apiResult?.averageResponseTime || 0,
            memoryUsage: memoryResult?.metrics?.memoryUsagePercent || 0,
            averageFPS: renderResult?.metrics?.averageFPS || 0,
            cacheHitRate: cacheResult?.metrics?.cacheHitRate || 0,
            overallScore: this.calculateOverallScore()
        };
    }
    
    // 计算总体评分
    calculateOverallScore() {
        let score = 100;
        
        const pageLoadResult = this.results.find(r => r.name === '页面加载性能');
        if (pageLoadResult?.metrics?.totalLoadTime > 3000) score -= 20;
        else if (pageLoadResult?.metrics?.totalLoadTime > 2000) score -= 10;
        
        const apiResult = this.results.find(r => r.name === 'API请求性能测试');
        if (apiResult?.averageResponseTime > 1000) score -= 20;
        else if (apiResult?.averageResponseTime > 500) score -= 10;
        
        const memoryResult = this.results.find(r => r.name === '内存使用测试');
        if (memoryResult?.metrics?.memoryUsagePercent > 80) score -= 15;
        else if (memoryResult?.metrics?.memoryUsagePercent > 60) score -= 8;
        
        const renderResult = this.results.find(r => r.name === '渲染性能测试');
        if (renderResult?.metrics?.averageFPS < 30) score -= 20;
        else if (renderResult?.metrics?.averageFPS < 50) score -= 10;
        
        const cacheResult = this.results.find(r => r.name === '缓存性能测试');
        if (cacheResult?.metrics?.cacheHitRate < 50) score -= 15;
        else if (cacheResult?.metrics?.cacheHitRate < 70) score -= 8;
        
        return Math.max(0, score);
    }
    
    // 显示测试报告
    displayReport(report) {
        // 创建报告界面
        const reportModal = document.createElement('div');
        reportModal.className = 'performance-report-modal';
        reportModal.innerHTML = `
            <div class="report-overlay">
                <div class="report-container">
                    <div class="report-header">
                        <h2>性能测试报告</h2>
                        <button class="report-close">&times;</button>
                    </div>
                    <div class="report-content">
                        ${this.renderReportContent(report)}
                    </div>
                    <div class="report-footer">
                        <button class="btn-export">导出报告</button>
                        <button class="btn-close">关闭</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(reportModal);
        
        // 绑定事件
        reportModal.querySelector('.report-close').onclick = () => document.body.removeChild(reportModal);
        reportModal.querySelector('.btn-close').onclick = () => document.body.removeChild(reportModal);
        reportModal.querySelector('.btn-export').onclick = () => this.exportReport(report);
    }
    
    renderReportContent(report) {
        const summary = report.summary;
        
        return `
            <div class="report-summary">
                <div class="summary-score">
                    <div class="score-circle">
                        <span class="score-number">${summary.overallScore}</span>
                    </div>
                    <div class="score-label">综合评分</div>
                </div>
                <div class="summary-metrics">
                    <div class="metric">
                        <div class="metric-value">${summary.pageLoadTime}ms</div>
                        <div class="metric-label">页面加载时间</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${Math.round(summary.averageApiResponseTime)}ms</div>
                        <div class="metric-label">平均API响应</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${summary.memoryUsage}%</div>
                        <div class="metric-label">内存使用率</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${summary.averageFPS}</div>
                        <div class="metric-label">平均帧率</div>
                    </div>
                </div>
            </div>
            <div class="report-details">
                ${report.results.map(result => this.renderTestResult(result)).join('')}
            </div>
        `;
    }
    
    renderTestResult(result) {
        return `
            <div class="test-result">
                <h3>${result.name}</h3>
                <div class="test-metrics">
                    ${result.metrics ? Object.entries(result.metrics).map(([key, value]) => 
                        `<div class="test-metric">
                            <span class="metric-key">${key}:</span>
                            <span class="metric-value">${value}</span>
                        </div>`
                    ).join('') : ''}
                </div>
            </div>
        `;
    }
    
    // 导出报告
    exportReport(report) {
        const dataStr = JSON.stringify(report, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `performance-report-${Date.now()}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
    }
    
    // 辅助方法
    getFirstPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
        return firstPaint ? Math.round(firstPaint.startTime) : null;
    }
    
    getFirstContentfulPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstContentfulPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
        return firstContentfulPaint ? Math.round(firstContentfulPaint.startTime) : null;
    }
    
    async getLargestContentfulPaint() {
        return new Promise(resolve => {
            if ('PerformanceObserver' in window) {
                const observer = new PerformanceObserver(list => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    resolve(lastEntry ? Math.round(lastEntry.startTime) : null);
                });
                observer.observe({ entryTypes: ['largest-contentful-paint'] });
                
                // 超时处理
                setTimeout(() => {
                    observer.disconnect();
                    resolve(null);
                }, 5000);
            } else {
                resolve(null);
            }
        });
    }
}

// 全局实例
window.PerformanceTestSuite = new PerformanceTestSuite();
```

## 预期效果与评估指标

### 性能提升指标

1. **首屏加载时间**: 从当前 5-8 秒优化到 2-3 秒
2. **API 响应时间**: 平均响应时间减少 40-60%
3. **内存使用**: 页面内存占用减少 30-50%
4. **渲染性能**: 页面流畅度提升，帧率稳定在 50+ FPS

### 维护性改进

1. **代码行数减少**: 单文件行数从 9000+ 减少到 300-500 行
2. **组件复用性**: 组件复用率提升到 80%
3. **开发效率**: 新功能开发时间减少 50%
4. **错误定位**: 问题定位时间减少 70%

### 用户体验提升

1. **加载体验**: 提供清晰的加载状态指示
2. **交互响应**: 所有操作响应时间小于 200ms
3. **错误处理**: 友好的错误提示和恢复机制
4. **离线支持**: 基础功能支持离线访问

## 实施建议与注意事项

### 实施顺序

1. **第 1-2 周**: 建立基础架构和模块化结构
2. **第 3-4 周**: 重构核心组件和 API 客户端
3. **第 5-6 周**: 完成组件系统和页面重构
4. **第 7-8 周**: 样式系统优化和主题系统
5. **第 9-10 周**: 性能测试、调优和部署

### 风险控制

1. **渐进式迁移**: 新旧系统并行运行，逐步切换
2. **功能对等**: 确保优化后功能完全对等
3. **性能监控**: 实时监控性能指标变化
4. **回滚方案**: 准备完整的回滚机制

### 团队协作

1. **代码审查**: 所有重构代码必须经过审查
2. **文档更新**: 同步更新开发和用户文档
3. **培训支持**: 为团队提供新架构培训
4. **沟通协调**: 建立定期沟通机制

---

**文档版本**: v1.0  
**制定时间**: 2025-09-09  
**预计实施周期**: 10 周  
**预期性能提升**: 50-70%  
**维护效率提升**: 60-80%

此优化方案将显著提升 BigScreen 大屏系统的性能和可维护性，为用户提供更好的使用体验，为开发团队提供更高效的开发环境。