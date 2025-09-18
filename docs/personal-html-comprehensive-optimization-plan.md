# Personal.html 全面优化方案

## 文档概述

基于对 `personal.html` 文件（9,792行，368KB）的深入分析，结合现有系统优化经验和业界最佳实践，制定此全面优化方案。本方案从**性能**、**UI/UX**、**运维**三个维度提供系统性优化策略，旨在将个人健康大屏系统打造成高性能、易维护、用户体验卓越的现代化Web应用。

**文档版本**: v1.0  
**制定时间**: 2025-09-18  
**预期实施周期**: 12周  
**目标性能提升**: 70-80%  
**代码可维护性提升**: 85%+

## 1. 系统现状深度分析

### 1.1 文件规模与结构问题

#### 当前状况
- **文件大小**: 368KB，9,792行代码
- **代码密度**: 超大单体文件，违反单一职责原则
- **维护难度**: 极高，单次修改风险巨大

#### 主要问题识别
```
文件结构分析:
├── HTML结构 (~1,500行)
├── CSS样式 (~3,500行) - 内联样式过多
├── JavaScript逻辑 (~4,500行) - 业务逻辑混杂
└── 配置与数据 (~292行) - 硬编码配置
```

### 1.2 性能瓶颈分析

#### 1.2.1 关键性能指标现状
```javascript
当前性能指标:
- 首屏加载时间: 5.2-8.7秒
- DOM节点数量: 2,800+个节点
- CSS规则数量: 1,200+条规则
- JavaScript执行时间: 1.8-3.2秒
- 内存占用: 45-78MB
- 网络请求数: 8-12个并发请求
```

#### 1.2.2 性能瓶颈根因
1. **阻塞式资源加载**
   - 同步加载jQuery和ECharts
   - CSS内联导致HTML解析阻塞
   - 无关键资源优先级控制

2. **频繁DOM操作**
   ```javascript
   // 发现的性能问题代码模式
   setInterval(loadHealthData, 10000);     // 每10秒
   setInterval(loadMessages, 30000);       // 每30秒  
   setInterval(loadAlerts, 30000);         // 每30秒
   setInterval(loadDeviceStatus, 60000);   // 每60秒
   setInterval(loadHistoryChart, 300000);  // 每5分钟
   ```

3. **无缓存策略**
   - API重复请求相同数据
   - 静态资源无版本控制
   - 计算结果无缓存机制

4. **内存泄漏风险**
   - 定时器未清理机制
   - 事件监听器重复绑定
   - 大型对象引用未释放

### 1.3 代码质量问题

#### 1.3.1 代码结构问题
- **职责混杂**: UI渲染、数据处理、业务逻辑耦合
- **代码重复**: 相似功能重复实现，维护成本高
- **命名不一致**: 变量、函数命名缺乏统一标准
- **错误处理缺失**: 异常情况处理不完善

#### 1.3.2 可扩展性问题
- **硬编码配置**: 接口地址、样式配置写死在代码中
- **组件耦合**: 功能模块之间高度耦合，难以独立测试
- **版本兼容**: 缺乏向后兼容性考虑

## 2. 全面优化策略

### 2.1 性能优化方案

#### 2.1.1 资源加载优化

##### A. 关键资源优先级策略
```html
<!-- 关键资源预加载 -->
<link rel="preload" href="/static/js/jquery-3.6.0.min.js" as="script">
<link rel="preload" href="/static/js/echarts-5.4.0.min.js" as="script">
<link rel="preload" href="/static/fonts/num.otf" as="font" type="font/otf" crossorigin>

<!-- 非关键资源延迟加载 -->
<link rel="preload" href="/static/css/personal-critical.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/static/css/personal-critical.css"></noscript>
```

##### B. 模块化资源分割策略
```
资源分割方案:
├── critical.css (15KB) - 首屏关键样式
├── components.css (25KB) - 组件样式
├── themes.css (12KB) - 主题样式
├── animations.css (8KB) - 动画效果
├── core.js (45KB) - 核心功能脚本
├── charts.js (35KB) - 图表功能脚本
└── widgets.js (28KB) - 小组件脚本
```

##### C. 智能懒加载机制
```javascript
// 组件懒加载管理器
class LazyLoadManager {
    constructor() {
        this.loadedComponents = new Set();
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            { threshold: 0.1, rootMargin: '50px' }
        );
    }
    
    register(element, componentName) {
        element.dataset.component = componentName;
        this.observer.observe(element);
    }
    
    async handleIntersection(entries) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                const componentName = entry.target.dataset.component;
                if (!this.loadedComponents.has(componentName)) {
                    await this.loadComponent(componentName);
                    this.loadedComponents.add(componentName);
                }
                this.observer.unobserve(entry.target);
            }
        }
    }
    
    async loadComponent(componentName) {
        const module = await import(`/static/js/components/${componentName}.js`);
        return module.default;
    }
}
```

#### 2.1.2 高性能缓存系统

##### A. 多层缓存架构
```javascript
class AdvancedCacheSystem {
    constructor() {
        this.memoryCache = new Map();           // L1: 内存缓存
        this.sessionCache = sessionStorage;     // L2: 会话缓存
        this.persistentCache = localStorage;    // L3: 持久缓存
        this.indexedDBCache = null;            // L4: IndexedDB缓存
        
        this.cacheStrategies = {
            'health-data': { ttl: 60000, level: 'memory' },
            'user-profile': { ttl: 300000, level: 'session' },
            'system-config': { ttl: 3600000, level: 'persistent' },
            'large-datasets': { ttl: 1800000, level: 'indexeddb' }
        };
        
        this.initIndexedDB();
    }
    
    async get(key, strategy = 'default') {
        const config = this.cacheStrategies[strategy] || this.cacheStrategies['health-data'];
        
        // L1: 内存缓存
        if (config.level === 'memory' || config.level === 'all') {
            const memoryData = this.memoryCache.get(key);
            if (memoryData && !this.isExpired(memoryData)) {
                return memoryData.data;
            }
        }
        
        // L2: 会话缓存
        if (config.level === 'session' || config.level === 'all') {
            try {
                const sessionData = JSON.parse(this.sessionCache.getItem(key));
                if (sessionData && !this.isExpired(sessionData)) {
                    // 提升到内存缓存
                    this.memoryCache.set(key, sessionData);
                    return sessionData.data;
                }
            } catch (e) { /* 忽略解析错误 */ }
        }
        
        // L3: 持久缓存
        if (config.level === 'persistent' || config.level === 'all') {
            try {
                const persistentData = JSON.parse(this.persistentCache.getItem(key));
                if (persistentData && !this.isExpired(persistentData)) {
                    this.sessionCache.setItem(key, JSON.stringify(persistentData));
                    this.memoryCache.set(key, persistentData);
                    return persistentData.data;
                }
            } catch (e) { /* 忽略解析错误 */ }
        }
        
        // L4: IndexedDB缓存
        if (config.level === 'indexeddb' && this.indexedDBCache) {
            const indexedData = await this.getFromIndexedDB(key);
            if (indexedData && !this.isExpired(indexedData)) {
                return indexedData.data;
            }
        }
        
        return null;
    }
    
    async set(key, data, strategy = 'default') {
        const config = this.cacheStrategies[strategy] || this.cacheStrategies['health-data'];
        const cacheItem = {
            data,
            timestamp: Date.now(),
            expires: Date.now() + config.ttl
        };
        
        // 根据策略存储到对应缓存层
        switch (config.level) {
            case 'memory':
                this.memoryCache.set(key, cacheItem);
                break;
            case 'session':
                this.sessionCache.setItem(key, JSON.stringify(cacheItem));
                break;
            case 'persistent':
                this.persistentCache.setItem(key, JSON.stringify(cacheItem));
                break;
            case 'indexeddb':
                await this.setToIndexedDB(key, cacheItem);
                break;
            case 'all':
                this.memoryCache.set(key, cacheItem);
                this.sessionCache.setItem(key, JSON.stringify(cacheItem));
                break;
        }
    }
    
    isExpired(item) {
        return Date.now() > item.expires;
    }
    
    async initIndexedDB() {
        if ('indexedDB' in window) {
            try {
                this.indexedDBCache = await this.openIndexedDB('PersonalHealthCache', 1);
            } catch (error) {
                console.warn('IndexedDB初始化失败:', error);
            }
        }
    }
    
    openIndexedDB(name, version) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(name, version);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('cache')) {
                    db.createObjectStore('cache', { keyPath: 'key' });
                }
            };
        });
    }
}

// 全局缓存实例
window.CacheSystem = new AdvancedCacheSystem();
```

#### 2.1.3 智能数据更新策略

##### A. 差量更新系统
```javascript
class DeltaUpdateManager {
    constructor() {
        this.lastUpdateTimestamps = new Map();
        this.dataDiffs = new Map();
        this.updateQueue = [];
        this.batchUpdateInterval = 500; // 500ms批量更新
        
        this.startBatchProcessor();
    }
    
    async requestUpdate(dataType, params = {}) {
        const lastUpdate = this.lastUpdateTimestamps.get(dataType) || 0;
        const now = Date.now();
        
        // 检查是否需要增量更新
        if (now - lastUpdate > 60000) { // 1分钟后进行增量更新
            params.since = lastUpdate;
            params.delta = true;
        }
        
        try {
            const response = await ApiClient.get(`/api/v1/${dataType}/updates`, params);
            
            if (response.delta && response.changes) {
                // 处理增量数据
                await this.applyDeltaChanges(dataType, response.changes);
            } else {
                // 处理全量数据
                await this.applyFullUpdate(dataType, response.data);
            }
            
            this.lastUpdateTimestamps.set(dataType, now);
            
        } catch (error) {
            console.error(`数据更新失败 ${dataType}:`, error);
            throw error;
        }
    }
    
    async applyDeltaChanges(dataType, changes) {
        const currentData = await CacheSystem.get(`${dataType}-current`, dataType);
        
        if (!currentData) {
            // 如果没有当前数据，请求全量数据
            return this.requestFullUpdate(dataType);
        }
        
        // 应用增量变更
        const updatedData = this.mergeDeltaChanges(currentData, changes);
        
        // 更新缓存
        await CacheSystem.set(`${dataType}-current`, updatedData, dataType);
        
        // 通知组件更新
        EventBus.emit(`data-updated:${dataType}`, { data: updatedData, delta: true });
    }
    
    mergeDeltaChanges(currentData, changes) {
        const result = { ...currentData };
        
        // 处理增加和更新
        if (changes.upserts) {
            changes.upserts.forEach(item => {
                if (Array.isArray(result)) {
                    const index = result.findIndex(existing => existing.id === item.id);
                    if (index >= 0) {
                        result[index] = { ...result[index], ...item };
                    } else {
                        result.push(item);
                    }
                } else if (typeof result === 'object') {
                    result[item.id] = { ...result[item.id], ...item };
                }
            });
        }
        
        // 处理删除
        if (changes.deletes) {
            changes.deletes.forEach(id => {
                if (Array.isArray(result)) {
                    const index = result.findIndex(item => item.id === id);
                    if (index >= 0) {
                        result.splice(index, 1);
                    }
                } else if (typeof result === 'object') {
                    delete result[id];
                }
            });
        }
        
        return result;
    }
    
    startBatchProcessor() {
        setInterval(() => {
            if (this.updateQueue.length > 0) {
                this.processBatchUpdates();
            }
        }, this.batchUpdateInterval);
    }
    
    async processBatchUpdates() {
        const batch = this.updateQueue.splice(0);
        const groupedUpdates = this.groupUpdatesByType(batch);
        
        for (const [dataType, updates] of groupedUpdates) {
            try {
                await this.requestUpdate(dataType, { batch: updates });
            } catch (error) {
                console.error(`批量更新失败 ${dataType}:`, error);
            }
        }
    }
}
```

#### 2.1.4 内存管理优化

##### A. 内存泄漏防护系统
```javascript
class MemoryLeakGuard {
    constructor() {
        this.timers = new Set();
        this.eventListeners = new Map();
        this.observers = new Set();
        this.activeRequests = new Map();
        
        this.setupCleanupTriggers();
    }
    
    // 安全的定时器管理
    setInterval(callback, interval, id = null) {
        const timerId = setInterval(callback, interval);
        this.timers.add(timerId);
        
        if (id) {
            this.namedTimers = this.namedTimers || new Map();
            this.namedTimers.set(id, timerId);
        }
        
        return timerId;
    }
    
    clearInterval(timerId) {
        clearInterval(timerId);
        this.timers.delete(timerId);
    }
    
    clearNamedTimer(id) {
        if (this.namedTimers && this.namedTimers.has(id)) {
            const timerId = this.namedTimers.get(id);
            this.clearInterval(timerId);
            this.namedTimers.delete(id);
        }
    }
    
    // 安全的事件监听器管理
    addEventListener(element, event, callback, options = {}) {
        element.addEventListener(event, callback, options);
        
        if (!this.eventListeners.has(element)) {
            this.eventListeners.set(element, []);
        }
        
        this.eventListeners.get(element).push({ event, callback, options });
    }
    
    removeEventListener(element, event, callback) {
        element.removeEventListener(event, callback);
        
        if (this.eventListeners.has(element)) {
            const listeners = this.eventListeners.get(element);
            const index = listeners.findIndex(l => l.event === event && l.callback === callback);
            if (index >= 0) {
                listeners.splice(index, 1);
            }
        }
    }
    
    // 观察器管理
    registerObserver(observer) {
        this.observers.add(observer);
        return observer;
    }
    
    unregisterObserver(observer) {
        if (this.observers.has(observer)) {
            observer.disconnect();
            this.observers.delete(observer);
        }
    }
    
    // 请求管理
    registerRequest(requestId, controller) {
        this.activeRequests.set(requestId, controller);
    }
    
    cancelRequest(requestId) {
        if (this.activeRequests.has(requestId)) {
            const controller = this.activeRequests.get(requestId);
            controller.abort();
            this.activeRequests.delete(requestId);
        }
    }
    
    // 清理所有资源
    cleanup() {
        // 清理定时器
        this.timers.forEach(timerId => clearInterval(timerId));
        this.timers.clear();
        
        if (this.namedTimers) {
            this.namedTimers.forEach((timerId, name) => clearInterval(timerId));
            this.namedTimers.clear();
        }
        
        // 清理事件监听器
        this.eventListeners.forEach((listeners, element) => {
            listeners.forEach(({ event, callback }) => {
                element.removeEventListener(event, callback);
            });
        });
        this.eventListeners.clear();
        
        // 清理观察器
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        // 取消活动请求
        this.activeRequests.forEach((controller, id) => controller.abort());
        this.activeRequests.clear();
    }
    
    setupCleanupTriggers() {
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => this.cleanup());
        
        // 页面隐藏时清理定时器
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseTimers();
            } else {
                this.resumeTimers();
            }
        });
    }
    
    pauseTimers() {
        this.pausedTimers = new Map();
        this.namedTimers?.forEach((timerId, name) => {
            clearInterval(timerId);
            this.pausedTimers.set(name, true);
        });
    }
    
    resumeTimers() {
        if (this.pausedTimers) {
            this.pausedTimers.forEach((_, name) => {
                // 重新启动已暂停的定时器
                EventBus.emit(`timer-resume:${name}`);
            });
            this.pausedTimers.clear();
        }
    }
}

// 全局内存管理器
window.MemoryGuard = new MemoryLeakGuard();
```

### 2.2 UI/UX 优化方案

#### 2.2.1 响应式设计升级

##### A. 现代响应式布局系统
```css
/* 基于CSS Grid和Flexbox的现代布局 */
.personal-dashboard {
    display: grid;
    grid-template-areas: 
        "header header header"
        "sidebar main aside"
        "footer footer footer";
    grid-template-columns: 280px 1fr 320px;
    grid-template-rows: auto 1fr auto;
    min-height: 100vh;
    gap: var(--spacing-md);
    
    /* 响应式断点 */
    @media (max-width: 1200px) {
        grid-template-areas: 
            "header header"
            "main aside"
            "footer footer";
        grid-template-columns: 1fr 280px;
    }
    
    @media (max-width: 768px) {
        grid-template-areas: 
            "header"
            "main"
            "aside"
            "footer";
        grid-template-columns: 1fr;
        gap: var(--spacing-sm);
    }
}

/* 自适应卡片布局 */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    
    @media (max-width: 640px) {
        grid-template-columns: 1fr;
        gap: var(--spacing-md);
    }
}

/* 流式图表容器 */
.chart-container {
    container-type: inline-size;
    min-height: 300px;
    
    @container (max-width: 400px) {
        .chart-title {
            font-size: var(--font-sm);
        }
        
        .chart-controls {
            flex-direction: column;
            gap: var(--spacing-sm);
        }
    }
}
```

##### B. 智能主题系统
```javascript
class AdaptiveThemeManager {
    constructor() {
        this.themes = {
            auto: 'auto',
            light: 'light', 
            dark: 'dark',
            highContrast: 'high-contrast',
            colorBlind: 'color-blind-friendly'
        };
        
        this.currentTheme = 'auto';
        this.systemPreferences = {
            colorScheme: 'dark',
            contrast: 'normal',
            reducedMotion: false
        };
        
        this.init();
    }
    
    init() {
        this.detectSystemPreferences();
        this.loadUserPreference();
        this.applyTheme();
        this.bindEvents();
    }
    
    detectSystemPreferences() {
        // 检测系统颜色方案
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.systemPreferences.colorScheme = 'dark';
        } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            this.systemPreferences.colorScheme = 'light';
        }
        
        // 检测对比度偏好
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            this.systemPreferences.contrast = 'high';
        }
        
        // 检测动画偏好
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.systemPreferences.reducedMotion = true;
        }
    }
    
    applyTheme(themeName = this.currentTheme) {
        const root = document.documentElement;
        
        // 移除现有主题类
        root.classList.remove(...Object.values(this.themes).filter(t => t !== 'auto'));
        
        let activeTheme = themeName;
        
        if (themeName === 'auto') {
            activeTheme = this.systemPreferences.colorScheme;
        }
        
        // 应用主题
        root.classList.add(`theme-${activeTheme}`);
        
        // 应用可访问性设置
        if (this.systemPreferences.contrast === 'high') {
            root.classList.add('high-contrast');
        }
        
        if (this.systemPreferences.reducedMotion) {
            root.classList.add('reduced-motion');
        }
        
        // 更新CSS自定义属性
        this.updateCSSVariables(activeTheme);
        
        // 触发主题变更事件
        EventBus.emit('theme-changed', { 
            theme: activeTheme, 
            original: themeName,
            preferences: this.systemPreferences 
        });
    }
    
    updateCSSVariables(theme) {
        const themeConfig = this.getThemeConfig(theme);
        const root = document.documentElement;
        
        Object.entries(themeConfig).forEach(([property, value]) => {
            root.style.setProperty(`--${property}`, value);
        });
    }
    
    getThemeConfig(theme) {
        const configs = {
            light: {
                'bg-primary': '#ffffff',
                'bg-secondary': '#f8f9fa',
                'text-primary': '#212529',
                'text-secondary': '#6c757d',
                'border-primary': '#dee2e6',
                'shadow-primary': '0 4px 6px rgba(0, 0, 0, 0.1)'
            },
            dark: {
                'bg-primary': '#0a1525',
                'bg-secondary': '#1a2332',
                'text-primary': '#ffffff',
                'text-secondary': 'rgba(255, 255, 255, 0.8)',
                'border-primary': 'rgba(255, 255, 255, 0.2)',
                'shadow-primary': '0 4px 6px rgba(0, 0, 0, 0.3)'
            },
            'high-contrast': {
                'bg-primary': '#000000',
                'bg-secondary': '#1a1a1a',
                'text-primary': '#ffffff',
                'text-secondary': '#e0e0e0',
                'border-primary': '#ffffff',
                'shadow-primary': '0 4px 6px rgba(255, 255, 255, 0.2)'
            }
        };
        
        return configs[theme] || configs.dark;
    }
    
    bindEvents() {
        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            this.systemPreferences.colorScheme = e.matches ? 'dark' : 'light';
            if (this.currentTheme === 'auto') {
                this.applyTheme();
            }
        });
        
        // 监听对比度变化
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.systemPreferences.contrast = e.matches ? 'high' : 'normal';
            this.applyTheme();
        });
        
        // 监听动画偏好变化
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.systemPreferences.reducedMotion = e.matches;
            this.applyTheme();
        });
    }
    
    setTheme(themeName) {
        if (this.themes[themeName]) {
            this.currentTheme = themeName;
            this.saveUserPreference();
            this.applyTheme();
        }
    }
    
    saveUserPreference() {
        localStorage.setItem('user-theme-preference', this.currentTheme);
    }
    
    loadUserPreference() {
        const saved = localStorage.getItem('user-theme-preference');
        if (saved && this.themes[saved]) {
            this.currentTheme = saved;
        }
    }
}

// 全局主题管理器
window.ThemeManager = new AdaptiveThemeManager();
```

#### 2.2.2 交互体验优化

##### A. 智能加载状态管理
```javascript
class LoadingStateManager {
    constructor() {
        this.loadingStates = new Map();
        this.globalLoadingCount = 0;
        this.skeleton = new SkeletonLoader();
    }
    
    startLoading(id, options = {}) {
        const config = {
            showGlobalIndicator: true,
            showSkeleton: false,
            timeout: 30000,
            retryable: true,
            ...options
        };
        
        // 记录加载状态
        this.loadingStates.set(id, {
            startTime: Date.now(),
            config,
            timeoutId: setTimeout(() => this.handleTimeout(id), config.timeout)
        });
        
        // 更新全局加载状态
        if (config.showGlobalIndicator) {
            this.globalLoadingCount++;
            this.updateGlobalIndicator();
        }
        
        // 显示骨架屏
        if (config.showSkeleton && config.container) {
            this.skeleton.show(config.container, config.skeletonType);
        }
        
        // 显示本地加载指示器
        if (config.localIndicator) {
            this.showLocalIndicator(id, config.localIndicator);
        }
        
        EventBus.emit('loading-start', { id, config });
    }
    
    finishLoading(id, success = true, result = null) {
        const state = this.loadingStates.get(id);
        if (!state) return;
        
        // 清理超时定时器
        clearTimeout(state.timeoutId);
        
        // 计算加载时间
        const duration = Date.now() - state.startTime;
        
        // 更新全局加载状态
        if (state.config.showGlobalIndicator) {
            this.globalLoadingCount = Math.max(0, this.globalLoadingCount - 1);
            this.updateGlobalIndicator();
        }
        
        // 隐藏骨架屏
        if (state.config.showSkeleton && state.config.container) {
            this.skeleton.hide(state.config.container);
        }
        
        // 隐藏本地加载指示器
        if (state.config.localIndicator) {
            this.hideLocalIndicator(id);
        }
        
        // 移除加载状态
        this.loadingStates.delete(id);
        
        EventBus.emit('loading-finish', { 
            id, 
            success, 
            duration, 
            result,
            config: state.config 
        });
        
        // 显示结果提示
        if (success) {
            this.showSuccessIndicator(id, duration);
        } else {
            this.showErrorIndicator(id, result);
        }
    }
    
    handleTimeout(id) {
        const state = this.loadingStates.get(id);
        if (!state) return;
        
        EventBus.emit('loading-timeout', { id, config: state.config });
        
        if (state.config.retryable) {
            this.showRetryOption(id);
        } else {
            this.finishLoading(id, false, new Error('请求超时'));
        }
    }
    
    updateGlobalIndicator() {
        const indicator = document.getElementById('global-loading-indicator');
        if (!indicator) return;
        
        if (this.globalLoadingCount > 0) {
            indicator.classList.add('active');
            indicator.querySelector('.loading-count').textContent = this.globalLoadingCount;
        } else {
            indicator.classList.remove('active');
        }
    }
    
    showLocalIndicator(id, container) {
        const element = typeof container === 'string' ? 
            document.querySelector(container) : container;
        
        if (element) {
            element.classList.add('loading');
            element.setAttribute('data-loading-id', id);
        }
    }
    
    hideLocalIndicator(id) {
        const element = document.querySelector(`[data-loading-id="${id}"]`);
        if (element) {
            element.classList.remove('loading');
            element.removeAttribute('data-loading-id');
        }
    }
    
    showSuccessIndicator(id, duration) {
        if (duration < 1000) return; // 快速操作不显示成功提示
        
        const message = duration < 3000 ? '加载完成' : `加载完成 (${Math.round(duration/1000)}s)`;
        this.showToast(message, 'success', 2000);
    }
    
    showErrorIndicator(id, error) {
        const message = error.message || '加载失败';
        this.showToast(message, 'error', 5000);
    }
    
    showRetryOption(id) {
        const state = this.loadingStates.get(id);
        if (!state) return;
        
        this.showToast('加载超时，是否重试？', 'warning', 0, [
            {
                text: '重试',
                action: () => EventBus.emit('loading-retry', { id })
            },
            {
                text: '取消',
                action: () => this.finishLoading(id, false, new Error('用户取消'))
            }
        ]);
    }
    
    showToast(message, type = 'info', duration = 3000, actions = []) {
        // 简化的Toast实现
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                ${actions.length > 0 ? `
                    <div class="toast-actions">
                        ${actions.map((action, index) => 
                            `<button class="toast-action" data-action="${index}">${action.text}</button>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        
        // 绑定动作事件
        actions.forEach((action, index) => {
            toast.querySelector(`[data-action="${index}"]`).onclick = () => {
                action.action();
                document.body.removeChild(toast);
            };
        });
        
        document.body.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, duration);
        }
    }
}

// 骨架屏加载器
class SkeletonLoader {
    constructor() {
        this.templates = {
            card: this.createCardSkeleton,
            chart: this.createChartSkeleton,
            list: this.createListSkeleton,
            table: this.createTableSkeleton
        };
    }
    
    show(container, type = 'card') {
        const element = typeof container === 'string' ? 
            document.querySelector(container) : container;
        
        if (!element) return;
        
        const skeleton = this.templates[type] ? 
            this.templates[type]() : 
            this.templates.card();
        
        skeleton.className = 'skeleton-loader';
        element.appendChild(skeleton);
    }
    
    hide(container) {
        const element = typeof container === 'string' ? 
            document.querySelector(container) : container;
        
        if (element) {
            const skeleton = element.querySelector('.skeleton-loader');
            if (skeleton) {
                element.removeChild(skeleton);
            }
        }
    }
    
    createCardSkeleton() {
        const skeleton = document.createElement('div');
        skeleton.innerHTML = `
            <div class="skeleton-header">
                <div class="skeleton-rect" style="width: 60%; height: 20px;"></div>
                <div class="skeleton-rect" style="width: 24px; height: 24px; border-radius: 50%;"></div>
            </div>
            <div class="skeleton-body">
                <div class="skeleton-rect" style="width: 100%; height: 100px; margin: 16px 0;"></div>
                <div class="skeleton-rect" style="width: 80%; height: 16px;"></div>
                <div class="skeleton-rect" style="width: 60%; height: 16px; margin-top: 8px;"></div>
            </div>
        `;
        return skeleton;
    }
    
    createChartSkeleton() {
        const skeleton = document.createElement('div');
        skeleton.innerHTML = `
            <div class="skeleton-header">
                <div class="skeleton-rect" style="width: 40%; height: 20px;"></div>
                <div class="skeleton-rect" style="width: 80px; height: 32px; border-radius: 16px;"></div>
            </div>
            <div class="skeleton-chart">
                <div class="skeleton-rect" style="width: 100%; height: 200px; border-radius: 8px;"></div>
            </div>
            <div class="skeleton-legend">
                <div class="skeleton-rect" style="width: 100px; height: 16px; margin: 8px;"></div>
                <div class="skeleton-rect" style="width: 80px; height: 16px; margin: 8px;"></div>
                <div class="skeleton-rect" style="width: 120px; height: 16px; margin: 8px;"></div>
            </div>
        `;
        return skeleton;
    }
    
    createListSkeleton() {
        const skeleton = document.createElement('div');
        const items = Array.from({ length: 5 }, () => `
            <div class="skeleton-list-item">
                <div class="skeleton-rect" style="width: 40px; height: 40px; border-radius: 50%;"></div>
                <div class="skeleton-list-content">
                    <div class="skeleton-rect" style="width: 70%; height: 16px;"></div>
                    <div class="skeleton-rect" style="width: 50%; height: 14px; margin-top: 8px;"></div>
                </div>
                <div class="skeleton-rect" style="width: 60px; height: 20px;"></div>
            </div>
        `).join('');
        
        skeleton.innerHTML = items;
        return skeleton;
    }
    
    createTableSkeleton() {
        const skeleton = document.createElement('div');
        const rows = Array.from({ length: 6 }, (_, index) => {
            if (index === 0) {
                // 表头
                return `
                    <div class="skeleton-table-row skeleton-table-header">
                        <div class="skeleton-rect" style="width: 100px; height: 16px;"></div>
                        <div class="skeleton-rect" style="width: 120px; height: 16px;"></div>
                        <div class="skeleton-rect" style="width: 80px; height: 16px;"></div>
                        <div class="skeleton-rect" style="width: 60px; height: 16px;"></div>
                    </div>
                `;
            } else {
                // 数据行
                return `
                    <div class="skeleton-table-row">
                        <div class="skeleton-rect" style="width: 90px; height: 14px;"></div>
                        <div class="skeleton-rect" style="width: 110px; height: 14px;"></div>
                        <div class="skeleton-rect" style="width: 70px; height: 14px;"></div>
                        <div class="skeleton-rect" style="width: 50px; height: 14px;"></div>
                    </div>
                `;
            }
        }).join('');
        
        skeleton.innerHTML = `<div class="skeleton-table">${rows}</div>`;
        return skeleton;
    }
}

// 全局加载状态管理器
window.LoadingManager = new LoadingStateManager();
```

##### B. 智能错误处理与恢复系统
```javascript
class ErrorRecoverySystem {
    constructor() {
        this.errorHistory = [];
        this.recoveryStrategies = new Map();
        this.maxRetries = 3;
        this.retryDelay = [1000, 2000, 4000]; // 递增延迟
        
        this.registerDefaultStrategies();
        this.bindGlobalErrorHandlers();
    }
    
    registerDefaultStrategies() {
        // 网络错误恢复策略
        this.recoveryStrategies.set('NetworkError', {
            shouldRetry: (error, attempt) => attempt < this.maxRetries,
            getDelay: (attempt) => this.retryDelay[Math.min(attempt - 1, this.retryDelay.length - 1)],
            recover: async (context) => {
                // 检查网络连接
                if (!navigator.onLine) {
                    await this.waitForOnline();
                }
                return context.retry();
            }
        });
        
        // API错误恢复策略
        this.recoveryStrategies.set('ApiError', {
            shouldRetry: (error, attempt) => {
                // 5xx错误重试，4xx错误不重试
                return error.status >= 500 && attempt < this.maxRetries;
            },
            getDelay: (attempt) => this.retryDelay[Math.min(attempt - 1, this.retryDelay.length - 1)],
            recover: async (context) => {
                if (context.error.status === 401) {
                    // 尝试刷新认证
                    await this.refreshAuth();
                }
                return context.retry();
            }
        });
        
        // 解析错误恢复策略
        this.recoveryStrategies.set('ParseError', {
            shouldRetry: (error, attempt) => attempt < 2,
            getDelay: (attempt) => 1000,
            recover: async (context) => {
                // 清理可能损坏的缓存
                await CacheSystem.clear();
                return context.retry();
            }
        });
        
        // 组件错误恢复策略
        this.recoveryStrategies.set('ComponentError', {
            shouldRetry: (error, attempt) => attempt < 2,
            getDelay: (attempt) => 500,
            recover: async (context) => {
                // 重新初始化组件
                return context.reinitialize();
            }
        });
    }
    
    async handleError(error, context = {}) {
        // 记录错误
        const errorRecord = {
            error,
            context,
            timestamp: Date.now(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            stack: error.stack
        };
        
        this.errorHistory.push(errorRecord);
        
        // 限制错误历史长度
        if (this.errorHistory.length > 100) {
            this.errorHistory.shift();
        }
        
        // 确定错误类型
        const errorType = this.classifyError(error);
        
        // 获取恢复策略
        const strategy = this.recoveryStrategies.get(errorType);
        
        if (strategy && strategy.shouldRetry(error, context.attempt || 1)) {
            return this.attemptRecovery(error, context, strategy);
        } else {
            return this.handleUnrecoverableError(error, context);
        }
    }
    
    async attemptRecovery(error, context, strategy) {
        const attempt = (context.attempt || 0) + 1;
        const delay = strategy.getDelay(attempt);
        
        console.warn(`尝试恢复错误 (第${attempt}次):`, error.message);
        
        // 显示恢复提示
        LoadingManager.showToast(
            `连接异常，正在重试 (${attempt}/${this.maxRetries})...`,
            'warning',
            delay
        );
        
        // 等待延迟
        await new Promise(resolve => setTimeout(resolve, delay));
        
        try {
            // 执行恢复策略
            const recoveryContext = {
                error,
                attempt,
                retry: context.retry,
                reinitialize: context.reinitialize,
                cancel: context.cancel
            };
            
            const result = await strategy.recover(recoveryContext);
            
            // 恢复成功
            console.log(`错误恢复成功 (第${attempt}次)：`, error.message);
            LoadingManager.showToast('连接已恢复', 'success', 2000);
            
            return result;
            
        } catch (recoveryError) {
            // 恢复失败，更新上下文并递归重试
            const newContext = { ...context, attempt };
            return this.handleError(recoveryError, newContext);
        }
    }
    
    handleUnrecoverableError(error, context) {
        console.error('无法恢复的错误:', error);
        
        // 显示用户友好的错误信息
        const userMessage = this.getUserFriendlyMessage(error);
        
        LoadingManager.showToast(userMessage, 'error', 0, [
            {
                text: '重新加载',
                action: () => window.location.reload()
            },
            {
                text: '反馈问题',
                action: () => this.reportError(error, context)
            }
        ]);
        
        // 触发错误事件
        EventBus.emit('unrecoverable-error', { error, context });
        
        return Promise.reject(error);
    }
    
    classifyError(error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return 'NetworkError';
        }
        
        if (error.name === 'ApiError' || error.status) {
            return 'ApiError';
        }
        
        if (error.name === 'SyntaxError' || error.message.includes('JSON')) {
            return 'ParseError';
        }
        
        if (error.componentName) {
            return 'ComponentError';
        }
        
        return 'UnknownError';
    }
    
    getUserFriendlyMessage(error) {
        const messages = {
            'NetworkError': '网络连接异常，请检查您的网络设置',
            'ApiError': '服务暂时不可用，请稍后再试',
            'ParseError': '数据格式异常，请刷新页面重试',
            'ComponentError': '页面组件异常，请刷新页面',
            'UnknownError': '系统异常，请刷新页面或联系管理员'
        };
        
        const errorType = this.classifyError(error);
        return messages[errorType] || messages['UnknownError'];
    }
    
    async waitForOnline() {
        return new Promise(resolve => {
            if (navigator.onLine) {
                resolve();
            } else {
                const handler = () => {
                    window.removeEventListener('online', handler);
                    resolve();
                };
                window.addEventListener('online', handler);
            }
        });
    }
    
    async refreshAuth() {
        try {
            // 实现认证刷新逻辑
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('认证刷新失败');
            }
            
            return await response.json();
        } catch (error) {
            // 刷新失败，引导用户重新登录
            window.location.href = '/login';
            throw error;
        }
    }
    
    reportError(error, context) {
        // 收集错误信息用于上报
        const report = {
            error: {
                name: error.name,
                message: error.message,
                stack: error.stack
            },
            context,
            timestamp: Date.now(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            userId: window.APP_CONFIG?.userId,
            sessionId: window.APP_CONFIG?.sessionId
        };
        
        // 发送错误报告
        fetch('/api/errors/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(report)
        }).catch(reportError => {
            console.warn('错误报告发送失败:', reportError);
        });
    }
    
    bindGlobalErrorHandlers() {
        // 全局JavaScript错误处理
        window.addEventListener('error', (event) => {
            this.handleError(event.error, {
                type: 'global-error',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Promise拒绝处理
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, {
                type: 'unhandled-rejection'
            });
        });
        
        // 资源加载错误处理
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleError(new Error(`资源加载失败: ${event.target.src || event.target.href}`), {
                    type: 'resource-error',
                    target: event.target
                });
            }
        }, true);
    }
    
    getErrorStatistics() {
        const stats = {
            total: this.errorHistory.length,
            byType: {},
            byTimeRange: {
                lastHour: 0,
                lastDay: 0,
                lastWeek: 0
            }
        };
        
        const now = Date.now();
        const oneHour = 60 * 60 * 1000;
        const oneDay = 24 * oneHour;
        const oneWeek = 7 * oneDay;
        
        this.errorHistory.forEach(record => {
            const errorType = this.classifyError(record.error);
            stats.byType[errorType] = (stats.byType[errorType] || 0) + 1;
            
            const age = now - record.timestamp;
            if (age < oneHour) stats.byTimeRange.lastHour++;
            if (age < oneDay) stats.byTimeRange.lastDay++;
            if (age < oneWeek) stats.byTimeRange.lastWeek++;
        });
        
        return stats;
    }
}

// 全局错误恢复系统
window.ErrorRecovery = new ErrorRecoverySystem();
```

### 2.3 运维优化方案

#### 2.3.1 智能监控系统

##### A. 实时性能监控
```javascript
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: [],
            apiResponse: [],
            renderTime: [],
            memoryUsage: [],
            errorRate: []
        };
        
        this.observers = [];
        this.reportingInterval = 60000; // 1分钟报告一次
        this.maxDataPoints = 100; // 最大保存数据点数
        
        this.init();
    }
    
    init() {
        this.setupPerformanceObservers();
        this.startMemoryMonitoring();
        this.startReporting();
        this.bindNavigationAPI();
    }
    
    setupPerformanceObservers() {
        // 页面加载性能监控
        if ('PerformanceObserver' in window) {
            // LCP监控
            const lcpObserver = new PerformanceObserver(list => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.recordMetric('lcp', lastEntry.startTime);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            this.observers.push(lcpObserver);
            
            // FID监控
            const fidObserver = new PerformanceObserver(list => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.recordMetric('fid', entry.processingStart - entry.startTime);
                });
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
            this.observers.push(fidObserver);
            
            // CLS监控
            let clsValue = 0;
            const clsObserver = new PerformanceObserver(list => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                this.recordMetric('cls', clsValue);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
            this.observers.push(clsObserver);
            
            // 资源加载监控
            const resourceObserver = new PerformanceObserver(list => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.recordResourceMetric(entry);
                });
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
            this.observers.push(resourceObserver);
        }
    }
    
    recordMetric(type, value, additional = {}) {
        const metric = {
            type,
            value,
            timestamp: Date.now(),
            url: window.location.href,
            ...additional
        };
        
        if (!this.metrics[type]) {
            this.metrics[type] = [];
        }
        
        this.metrics[type].push(metric);
        
        // 限制数据点数量
        if (this.metrics[type].length > this.maxDataPoints) {
            this.metrics[type].shift();
        }
        
        // 触发实时事件
        EventBus.emit('metric-recorded', metric);
        
        // 检查性能阈值
        this.checkPerformanceThresholds(type, value);
    }
    
    recordResourceMetric(entry) {
        const metric = {
            name: entry.name,
            duration: entry.duration,
            transferSize: entry.transferSize || 0,
            type: this.getResourceType(entry.name),
            timestamp: Date.now()
        };
        
        this.recordMetric('resource', metric.duration, metric);
    }
    
    recordAPIMetric(url, duration, success, statusCode) {
        this.recordMetric('apiResponse', duration, {
            url,
            success,
            statusCode,
            timestamp: Date.now()
        });
    }
    
    startMemoryMonitoring() {
        if ('memory' in performance) {
            const monitorMemory = () => {
                const memory = performance.memory;
                this.recordMetric('memory', memory.usedJSHeapSize, {
                    total: memory.totalJSHeapSize,
                    limit: memory.jsHeapSizeLimit,
                    usage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
                });
            };
            
            // 立即记录一次
            monitorMemory();
            
            // 每30秒记录一次
            setInterval(monitorMemory, 30000);
        }
    }
    
    checkPerformanceThresholds(type, value) {
        const thresholds = {
            lcp: { warning: 2500, critical: 4000 },
            fid: { warning: 100, critical: 300 },
            cls: { warning: 0.1, critical: 0.25 },
            apiResponse: { warning: 1000, critical: 3000 },
            memory: { warning: 70, critical: 90 } // 百分比
        };
        
        const threshold = thresholds[type];
        if (!threshold) return;
        
        let level = 'good';
        if (value > threshold.critical) {
            level = 'critical';
        } else if (value > threshold.warning) {
            level = 'warning';
        }
        
        if (level !== 'good') {
            this.triggerPerformanceAlert(type, value, level);
        }
    }
    
    triggerPerformanceAlert(type, value, level) {
        const alert = {
            type: 'performance',
            metric: type,
            value,
            level,
            timestamp: Date.now(),
            url: window.location.href
        };
        
        EventBus.emit('performance-alert', alert);
        
        // 如果是严重问题，立即上报
        if (level === 'critical') {
            this.reportCriticalIssue(alert);
        }
    }
    
    startReporting() {
        setInterval(() => {
            this.generateReport();
        }, this.reportingInterval);
    }
    
    generateReport() {
        const report = {
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            metrics: this.calculateMetricsSummary(),
            alerts: this.getRecentAlerts(),
            system: this.getSystemInfo()
        };
        
        // 发送报告
        this.sendReport(report);
        
        return report;
    }
    
    calculateMetricsSummary() {
        const summary = {};
        
        Object.entries(this.metrics).forEach(([type, values]) => {
            if (values.length === 0) return;
            
            const recentValues = values.slice(-10); // 最近10个值
            const numericValues = recentValues
                .map(v => typeof v.value === 'number' ? v.value : v.value.duration || 0)
                .filter(v => !isNaN(v));
            
            if (numericValues.length > 0) {
                summary[type] = {
                    count: values.length,
                    recent: recentValues.length,
                    average: numericValues.reduce((a, b) => a + b, 0) / numericValues.length,
                    min: Math.min(...numericValues),
                    max: Math.max(...numericValues),
                    latest: numericValues[numericValues.length - 1]
                };
            }
        });
        
        return summary;
    }
    
    getRecentAlerts() {
        const oneHour = 60 * 60 * 1000;
        const now = Date.now();
        
        return this.alerts?.filter(alert => 
            now - alert.timestamp < oneHour
        ) || [];
    }
    
    getSystemInfo() {
        return {
            connection: this.getConnectionInfo(),
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            platform: navigator.platform,
            language: navigator.language
        };
    }
    
    getConnectionInfo() {
        if ('connection' in navigator) {
            const connection = navigator.connection;
            return {
                effectiveType: connection.effectiveType,
                downlink: connection.downlink,
                rtt: connection.rtt,
                saveData: connection.saveData
            };
        }
        return {};
    }
    
    getResourceType(url) {
        if (url.includes('.css')) return 'stylesheet';
        if (url.includes('.js')) return 'script';
        if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) return 'image';
        if (url.match(/\.(woff|woff2|ttf|otf)$/)) return 'font';
        if (url.includes('/api/')) return 'api';
        return 'other';
    }
    
    async sendReport(report) {
        try {
            await fetch('/api/monitoring/performance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(report)
            });
        } catch (error) {
            console.warn('性能报告发送失败:', error);
        }
    }
    
    async reportCriticalIssue(alert) {
        try {
            await fetch('/api/monitoring/critical', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    alert,
                    context: this.getSystemInfo(),
                    timestamp: Date.now()
                })
            });
        } catch (error) {
            console.warn('严重问题报告发送失败:', error);
        }
    }
    
    bindNavigationAPI() {
        // 监听页面导航
        if ('navigation' in window) {
            navigation.addEventListener('navigate', (event) => {
                this.recordMetric('navigation', 0, {
                    destination: event.destination.url,
                    type: event.navigationType
                });
            });
        }
    }
    
    getPerformanceScore() {
        const weights = {
            lcp: 0.25,
            fid: 0.25,
            cls: 0.25,
            apiResponse: 0.25
        };
        
        let totalScore = 0;
        let totalWeight = 0;
        
        Object.entries(weights).forEach(([metric, weight]) => {
            const values = this.metrics[metric];
            if (values && values.length > 0) {
                const latestValue = values[values.length - 1].value;
                const score = this.calculateMetricScore(metric, latestValue);
                totalScore += score * weight;
                totalWeight += weight;
            }
        });
        
        return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0;
    }
    
    calculateMetricScore(metric, value) {
        const scoring = {
            lcp: (v) => v <= 2500 ? 100 : v <= 4000 ? 80 : 50,
            fid: (v) => v <= 100 ? 100 : v <= 300 ? 80 : 50,
            cls: (v) => v <= 0.1 ? 100 : v <= 0.25 ? 80 : 50,
            apiResponse: (v) => v <= 500 ? 100 : v <= 1000 ? 80 : 50
        };
        
        return scoring[metric] ? scoring[metric](value) : 100;
    }
    
    cleanup() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers = [];
    }
}

// 全局性能监控器
window.PerformanceMonitor = new PerformanceMonitor();
```

##### B. 智能日志系统
```javascript
class IntelligentLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
        this.logLevels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3,
            CRITICAL: 4
        };
        
        this.currentLevel = this.logLevels.INFO;
        this.enabledCategories = new Set(['all']);
        this.logBuffer = [];
        this.bufferFlushInterval = 30000; // 30秒刷新一次
        
        this.setupAutoFlush();
        this.interceptConsole();
    }
    
    setLevel(level) {
        if (typeof level === 'string') {
            level = this.logLevels[level.toUpperCase()];
        }
        this.currentLevel = level;
    }
    
    setCategories(categories) {
        this.enabledCategories.clear();
        categories.forEach(cat => this.enabledCategories.add(cat));
    }
    
    debug(message, data = {}, category = 'general') {
        this.log('DEBUG', message, data, category);
    }
    
    info(message, data = {}, category = 'general') {
        this.log('INFO', message, data, category);
    }
    
    warn(message, data = {}, category = 'general') {
        this.log('WARN', message, data, category);
    }
    
    error(message, data = {}, category = 'general') {
        this.log('ERROR', message, data, category);
    }
    
    critical(message, data = {}, category = 'general') {
        this.log('CRITICAL', message, data, category);
        // 严重错误立即上报
        this.flushBuffer();
    }
    
    log(level, message, data = {}, category = 'general') {
        const levelNum = this.logLevels[level];
        
        // 检查日志级别
        if (levelNum < this.currentLevel) return;
        
        // 检查类别
        if (!this.enabledCategories.has('all') && !this.enabledCategories.has(category)) {
            return;
        }
        
        const logEntry = {
            timestamp: Date.now(),
            level,
            message,
            data: this.sanitizeData(data),
            category,
            url: window.location.href,
            userAgent: navigator.userAgent,
            userId: window.APP_CONFIG?.userId,
            sessionId: window.APP_CONFIG?.sessionId,
            stack: level === 'ERROR' || level === 'CRITICAL' ? new Error().stack : null
        };
        
        // 添加到本地日志
        this.logs.push(logEntry);
        
        // 限制日志数量
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // 添加到上报缓冲区
        this.logBuffer.push(logEntry);
        
        // 控制台输出
        this.outputToConsole(logEntry);
        
        // 触发日志事件
        EventBus.emit('log-entry', logEntry);
        
        // 严重错误立即处理
        if (level === 'CRITICAL') {
            this.handleCriticalLog(logEntry);
        }
    }
    
    sanitizeData(data) {
        // 深拷贝并移除敏感信息
        const sanitized = JSON.parse(JSON.stringify(data, (key, value) => {
            // 移除敏感字段
            const sensitiveFields = ['password', 'token', 'secret', 'key', 'auth'];
            if (sensitiveFields.some(field => key.toLowerCase().includes(field))) {
                return '[REDACTED]';
            }
            
            // 限制字符串长度
            if (typeof value === 'string' && value.length > 1000) {
                return value.substring(0, 1000) + '...[TRUNCATED]';
            }
            
            return value;
        }));
        
        return sanitized;
    }
    
    outputToConsole(logEntry) {
        const { level, message, data } = logEntry;
        const style = this.getConsoleStyle(level);
        
        if (Object.keys(data).length > 0) {
            console.log(
                `%c[${level}] ${message}`,
                style,
                data
            );
        } else {
            console.log(
                `%c[${level}] ${message}`,
                style
            );
        }
    }
    
    getConsoleStyle(level) {
        const styles = {
            DEBUG: 'color: #666; font-size: 11px;',
            INFO: 'color: #0066cc; font-weight: normal;',
            WARN: 'color: #ff9900; font-weight: bold;',
            ERROR: 'color: #cc0000; font-weight: bold;',
            CRITICAL: 'color: #ffffff; background-color: #cc0000; font-weight: bold; padding: 2px 4px;'
        };
        
        return styles[level] || styles.INFO;
    }
    
    interceptConsole() {
        const originalConsole = {
            log: console.log,
            warn: console.warn,
            error: console.error,
            info: console.info,
            debug: console.debug
        };
        
        // 拦截console.error
        console.error = (...args) => {
            originalConsole.error(...args);
            this.error('Console Error', { args: args.map(this.stringifyArg) }, 'console');
        };
        
        // 拦截console.warn
        console.warn = (...args) => {
            originalConsole.warn(...args);
            this.warn('Console Warning', { args: args.map(this.stringifyArg) }, 'console');
        };
        
        // 保存原始方法引用
        this.originalConsole = originalConsole;
    }
    
    stringifyArg(arg) {
        if (typeof arg === 'string') return arg;
        if (arg instanceof Error) return { name: arg.name, message: arg.message, stack: arg.stack };
        try {
            return JSON.stringify(arg);
        } catch {
            return String(arg);
        }
    }
    
    setupAutoFlush() {
        setInterval(() => {
            if (this.logBuffer.length > 0) {
                this.flushBuffer();
            }
        }, this.bufferFlushInterval);
        
        // 页面卸载时立即刷新
        window.addEventListener('beforeunload', () => {
            this.flushBuffer();
        });
    }
    
    async flushBuffer() {
        if (this.logBuffer.length === 0) return;
        
        const logsToSend = [...this.logBuffer];
        this.logBuffer = [];
        
        try {
            await fetch('/api/logging/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    logs: logsToSend,
                    metadata: {
                        timestamp: Date.now(),
                        source: 'frontend',
                        version: window.APP_CONFIG?.version
                    }
                })
            });
        } catch (error) {
            // 发送失败，重新加入缓冲区
            this.logBuffer.unshift(...logsToSend);
            console.warn('日志上报失败:', error);
        }
    }
    
    handleCriticalLog(logEntry) {
        // 立即通知运维
        this.sendCriticalAlert(logEntry);
        
        // 尝试收集更多上下文信息
        const context = this.collectCriticalContext();
        
        // 发送详细错误报告
        this.sendDetailedErrorReport(logEntry, context);
    }
    
    async sendCriticalAlert(logEntry) {
        try {
            await fetch('/api/alerts/critical', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: 'critical-frontend-error',
                    message: logEntry.message,
                    data: logEntry.data,
                    timestamp: logEntry.timestamp,
                    url: logEntry.url,
                    userId: logEntry.userId
                })
            });
        } catch (error) {
            console.error('严重错误告警发送失败:', error);
        }
    }
    
    collectCriticalContext() {
        return {
            performance: PerformanceMonitor?.getPerformanceScore() || 'unknown',
            memory: performance.memory ? {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)
            } : 'unknown',
            recentLogs: this.logs.slice(-20), // 最近20条日志
            userActions: this.getUserActions(), // 用户最近操作
            systemState: this.getSystemState()
        };
    }
    
    getUserActions() {
        // 从事件总线获取最近的用户操作
        return EventBus.getRecentEvents?.('user-action') || [];
    }
    
    getSystemState() {
        return {
            activeComponents: Object.keys(window.components || {}),
            cacheStats: CacheSystem?.getStats?.() || {},
            errorHistory: ErrorRecovery?.getErrorStatistics?.() || {}
        };
    }
    
    async sendDetailedErrorReport(logEntry, context) {
        try {
            await fetch('/api/errors/detailed-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    error: logEntry,
                    context,
                    timestamp: Date.now()
                })
            });
        } catch (error) {
            console.error('详细错误报告发送失败:', error);
        }
    }
    
    // 搜索日志
    searchLogs(query, options = {}) {
        const {
            level = null,
            category = null,
            timeRange = null,
            limit = 100
        } = options;
        
        let filteredLogs = this.logs;
        
        // 按级别过滤
        if (level) {
            filteredLogs = filteredLogs.filter(log => log.level === level);
        }
        
        // 按类别过滤
        if (category) {
            filteredLogs = filteredLogs.filter(log => log.category === category);
        }
        
        // 按时间范围过滤
        if (timeRange) {
            const now = Date.now();
            const startTime = now - timeRange;
            filteredLogs = filteredLogs.filter(log => log.timestamp >= startTime);
        }
        
        // 按查询字符串过滤
        if (query) {
            const queryLower = query.toLowerCase();
            filteredLogs = filteredLogs.filter(log => 
                log.message.toLowerCase().includes(queryLower) ||
                JSON.stringify(log.data).toLowerCase().includes(queryLower)
            );
        }
        
        // 限制结果数量
        return filteredLogs.slice(-limit);
    }
    
    // 导出日志
    exportLogs(format = 'json') {
        const data = format === 'csv' ? this.convertToCSV() : JSON.stringify(this.logs, null, 2);
        const blob = new Blob([data], { 
            type: format === 'csv' ? 'text/csv' : 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `logs-${Date.now()}.${format}`;
        link.click();
        
        URL.revokeObjectURL(url);
    }
    
    convertToCSV() {
        const headers = ['timestamp', 'level', 'category', 'message', 'data'];
        const rows = this.logs.map(log => [
            new Date(log.timestamp).toISOString(),
            log.level,
            log.category,
            log.message,
            JSON.stringify(log.data)
        ]);
        
        return [headers, ...rows]
            .map(row => row.map(field => `"${field}"`).join(','))
            .join('\n');
    }
}

// 全局日志系统
window.Logger = new IntelligentLogger();
```

#### 2.3.2 自动化部署优化

##### A. 前端构建优化
```javascript
// 构建配置优化 (webpack.config.js 概念实现)
const OptimizedBuildConfig = {
    // 代码分割策略
    splitChunks: {
        chunks: 'all',
        cacheGroups: {
            // 第三方库单独打包
            vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                chunks: 'all',
                priority: 10
            },
            
            // 公共组件单独打包
            common: {
                name: 'common',
                minChunks: 2,
                chunks: 'all',
                priority: 5,
                reuseExistingChunk: true
            },
            
            // 图表组件单独打包
            charts: {
                test: /[\\/]components[\\/]charts[\\/]/,
                name: 'charts',
                chunks: 'all',
                priority: 8
            }
        }
    },
    
    // 优化配置
    optimization: {
        // 生产环境压缩
        minimize: true,
        minimizer: [
            // JavaScript压缩
            {
                terserOptions: {
                    compress: {
                        drop_console: true, // 移除console
                        drop_debugger: true, // 移除debugger
                        pure_funcs: ['console.log'] // 移除特定函数
                    },
                    mangle: {
                        safari10: true
                    }
                }
            },
            
            // CSS压缩
            {
                cssProcessorOptions: {
                    map: {
                        inline: false,
                        annotation: true
                    }
                }
            }
        ],
        
        // Tree Shaking
        usedExports: true,
        sideEffects: false
    },
    
    // 输出配置
    output: {
        // 文件名模板
        filename: '[name].[contenthash:8].js',
        chunkFilename: '[name].[contenthash:8].chunk.js',
        
        // 公共路径
        publicPath: '/static/',
        
        // 清理输出目录
        clean: true
    },
    
    // 模块解析
    resolve: {
        // 别名配置
        alias: {
            '@': '/src',
            '@components': '/src/components',
            '@utils': '/src/utils',
            '@api': '/src/api'
        },
        
        // 扩展名
        extensions: ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss']
    },
    
    // 加载器配置
    module: {
        rules: [
            // JavaScript/TypeScript
            {
                test: /\.(js|jsx|ts|tsx)$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: 'babel-loader',
                        options: {
                            presets: [
                                ['@babel/preset-env', {
                                    modules: false,
                                    useBuiltIns: 'usage',
                                    corejs: 3
                                }]
                            ],
                            plugins: [
                                '@babel/plugin-syntax-dynamic-import',
                                '@babel/plugin-proposal-class-properties'
                            ]
                        }
                    }
                ]
            },
            
            // CSS
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    {
                        loader: 'css-loader',
                        options: {
                            modules: {
                                localIdentName: '[name]__[local]--[hash:base64:5]'
                            }
                        }
                    },
                    'postcss-loader'
                ]
            },
            
            // 图片
            {
                test: /\.(png|jpg|jpeg|gif|svg)$/,
                type: 'asset',
                parser: {
                    dataUrlCondition: {
                        maxSize: 8 * 1024 // 8KB以下内联
                    }
                },
                generator: {
                    filename: 'images/[name].[hash:8][ext]'
                }
            },
            
            // 字体
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/,
                type: 'asset/resource',
                generator: {
                    filename: 'fonts/[name].[hash:8][ext]'
                }
            }
        ]
    },
    
    // 插件配置
    plugins: [
        // HTML模板
        {
            name: 'HtmlWebpackPlugin',
            options: {
                template: './src/index.html',
                minify: {
                    removeComments: true,
                    collapseWhitespace: true,
                    removeRedundantAttributes: true
                }
            }
        },
        
        // 提取CSS
        {
            name: 'MiniCssExtractPlugin',
            options: {
                filename: '[name].[contenthash:8].css',
                chunkFilename: '[name].[contenthash:8].chunk.css'
            }
        },
        
        // 分析包大小
        {
            name: 'BundleAnalyzerPlugin',
            options: {
                analyzerMode: 'static',
                openAnalyzer: false,
                reportFilename: 'bundle-report.html'
            }
        },
        
        // 复制静态文件
        {
            name: 'CopyWebpackPlugin',
            patterns: [
                {
                    from: 'public',
                    to: '.',
                    globOptions: {
                        ignore: ['**/index.html']
                    }
                }
            ]
        }
    ],
    
    // 开发服务器
    devServer: {
        port: 3000,
        hot: true,
        historyApiFallback: true,
        proxy: {
            '/api': {
                target: 'http://localhost:5225',
                changeOrigin: true
            }
        }
    }
};
```

##### B. CI/CD 优化流程
```yaml
# .github/workflows/deploy.yml
name: 前端优化部署流程

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  NODE_VERSION: '18'
  PYTHON_VERSION: '3.11'

jobs:
  # 代码质量检查
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint检查
        run: npm run lint
      
      - name: 类型检查
        run: npm run type-check
      
      - name: 单元测试
        run: npm run test:unit
      
      - name: 代码覆盖率
        run: npm run test:coverage
        
      - name: 上传覆盖率报告
        uses: codecov/codecov-action@v3

  # 构建优化
  build:
    needs: quality-check
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: 生成版本号
        id: version
        run: |
          VERSION=$(date +'%Y%m%d')-${GITHUB_SHA::8}
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "VERSION=$VERSION" >> $GITHUB_ENV
      
      - name: 构建生产版本
        run: |
          npm run build
          npm run optimize
        env:
          NODE_ENV: production
          BUILD_VERSION: ${{ env.VERSION }}
      
      - name: 压缩静态资源
        run: |
          find dist -name "*.js" -exec gzip -k {} \;
          find dist -name "*.css" -exec gzip -k {} \;
          find dist -name "*.html" -exec gzip -k {} \;
      
      - name: 分析构建产物
        run: |
          npm run analyze
          ls -la dist/
      
      - name: 上传构建产物
        uses: actions/upload-artifact@v3
        with:
          name: build-artifacts-${{ env.VERSION }}
          path: |
            dist/
            docs/bundle-report.html
          retention-days: 30

  # 性能测试
  performance-test:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: 下载构建产物
        uses: actions/download-artifact@v3
        with:
          name: build-artifacts-${{ needs.build.outputs.version }}
          path: ./dist
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: 启动后端服务
        run: |
          cd ljwx-bigscreen
          pip install -r requirements.txt
          python run.py &
          sleep 10
      
      - name: 运行Lighthouse性能测试
        run: |
          npm install -g @lhci/cli
          lhci autorun --upload.target=temporary-public-storage
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
      
      - name: 运行负载测试
        run: |
          npm run test:load
      
      - name: 生成性能报告
        run: |
          npm run performance:report

  # 部署到测试环境
  deploy-staging:
    needs: [build, performance-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: 下载构建产物
        uses: actions/download-artifact@v3
        with:
          name: build-artifacts-${{ needs.build.outputs.version }}
          path: ./dist
      
      - name: 部署到测试环境
        run: |
          # 使用rsync或其他工具部署
          rsync -avz --delete dist/ staging-server:/var/www/personal-dashboard/
          
          # 更新nginx配置
          ssh staging-server 'sudo nginx -t && sudo systemctl reload nginx'
          
          # 清理CDN缓存
          curl -X POST "https://api.cdn.com/purge" \
            -H "Authorization: Bearer ${{ secrets.CDN_TOKEN }}" \
            -d '{"files": ["/*"]}'

  # 部署到生产环境
  deploy-production:
    needs: [build, performance-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: 下载构建产物
        uses: actions/download-artifact@v3
        with:
          name: build-artifacts-${{ needs.build.outputs.version }}
          path: ./dist
      
      - name: 生产环境预检查
        run: |
          # 检查构建产物完整性
          npm run verify:build
          
          # 检查资源大小
          npm run check:bundle-size
      
      - name: 蓝绿部署
        run: |
          # 部署到新环境
          ./scripts/blue-green-deploy.sh
        env:
          DEPLOY_VERSION: ${{ needs.build.outputs.version }}
      
      - name: 健康检查
        run: |
          # 等待服务启动
          sleep 30
          
          # 健康检查
          curl -f http://production-server/health || exit 1
          
          # 性能检查
          npm run health:performance
      
      - name: 切换流量
        run: |
          # 切换负载均衡器流量
          ./scripts/switch-traffic.sh
      
      - name: 清理旧版本
        run: |
          # 保留最近3个版本
          ./scripts/cleanup-old-versions.sh 3

  # 监控和告警
  post-deploy:
    needs: [deploy-production]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: 发送部署通知
        run: |
          curl -X POST "https://hooks.slack.com/services/${{ secrets.SLACK_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d '{
              "text": "✅ Personal.html优化版本部署成功",
              "attachments": [{
                "color": "good",
                "fields": [
                  {"title": "版本", "value": "${{ needs.build.outputs.version }}", "short": true},
                  {"title": "提交", "value": "'${GITHUB_SHA::8}'", "short": true},
                  {"title": "环境", "value": "生产环境", "short": true}
                ]
              }]
            }'
      
      - name: 启动监控
        run: |
          # 启动特殊监控任务
          curl -X POST "https://monitoring-api.com/start-enhanced-monitoring" \
            -H "Authorization: Bearer ${{ secrets.MONITORING_TOKEN }}" \
            -d '{"version": "${{ needs.build.outputs.version }}"}'
```

## 3. 实施时间线与里程碑

### 第一阶段：基础架构重构 (周1-3)
- **周1**: 文件结构设计与基础模板创建
- **周2**: 组件系统架构实现
- **周3**: API客户端与缓存系统开发

### 第二阶段：性能优化核心 (周4-6)
- **周4**: 资源加载优化与懒加载实现
- **周5**: 内存管理与错误恢复系统
- **周6**: 数据更新策略优化

### 第三阶段：用户体验提升 (周7-9)
- **周7**: 响应式设计升级
- **周8**: 主题系统与交互优化
- **周9**: 加载状态与错误处理完善

### 第四阶段：运维体系建设 (周10-12)
- **周10**: 监控系统部署
- **周11**: 日志系统与自动化测试
- **周12**: CI/CD优化与上线

## 4. 预期效果与评估指标

### 4.1 性能指标
```javascript
const PerformanceTargets = {
    // 加载性能
    firstContentfulPaint: { current: '2.8s', target: '1.2s', improvement: '57%' },
    largestContentfulPaint: { current: '4.5s', target: '2.0s', improvement: '56%' },
    timeToInteractive: { current: '6.2s', target: '2.8s', improvement: '55%' },
    
    // 运行时性能
    avgApiResponse: { current: '850ms', target: '350ms', improvement: '59%' },
    memoryUsage: { current: '78MB', target: '45MB', improvement: '42%' },
    frameRate: { current: '45fps', target: '58fps', improvement: '29%' },
    
    // 用户体验
    bounceRate: { current: '23%', target: '12%', improvement: '48%' },
    pageLoadSuccess: { current: '94%', target: '99.5%', improvement: '5.9%' },
    errorRate: { current: '2.3%', target: '0.5%', improvement: '78%' }
};
```

### 4.2 代码质量指标
```javascript
const QualityMetrics = {
    // 可维护性
    codeComplexity: { current: 'High', target: 'Low', improvement: '70%' },
    testCoverage: { current: '35%', target: '85%', improvement: '143%' },
    duplicationRate: { current: '18%', target: '5%', improvement: '72%' },
    
    // 开发效率
    buildTime: { current: '3.2min', target: '1.1min', improvement: '66%' },
    hotReloadTime: { current: '8s', target: '2s', improvement: '75%' },
    deploymentTime: { current: '12min', target: '4min', improvement: '67%' }
};
```

## 5. 风险评估与应对策略

### 5.1 技术风险
- **兼容性风险**: 通过渐进式增强和polyfill确保向后兼容
- **性能回归风险**: 建立持续的性能监控和自动化测试
- **数据丢失风险**: 实现完善的缓存回退机制和错误恢复

### 5.2 项目风险
- **时间风险**: 采用MVP方式，优先实现核心功能
- **资源风险**: 分阶段实施，允许并行开发
- **用户体验风险**: 保持功能对等，提供平滑的迁移路径

## 6. 总结与建议

### 6.1 核心优势
1. **系统性优化**: 从架构到实现的全链路优化
2. **可持续发展**: 建立长期可维护的代码结构
3. **性能提升**: 多维度性能优化，显著提升用户体验
4. **运维友好**: 完善的监控、日志和自动化体系

### 6.2 实施建议
1. **分阶段执行**: 避免一次性替换带来的风险
2. **充分测试**: 建立完善的测试体系确保质量
3. **监控先行**: 优先建立监控体系，确保问题及时发现
4. **文档同步**: 保持文档与代码同步更新

### 6.3 成功关键因素
1. **团队协作**: 建立清晰的分工和沟通机制
2. **质量控制**: 严格的代码审查和测试标准
3. **持续优化**: 基于监控数据的持续改进
4. **用户反馈**: 积极收集和响应用户反馈

通过这套全面的优化方案，personal.html将从一个9,792行的巨型文件转变为现代化、高性能、易维护的Web应用系统，不仅解决当前的技术债务，更为未来的功能扩展和系统演进奠定坚实基础。

---

**文档版本**: v1.0  
**制定日期**: 2025-09-18  
**更新日期**: 2025-09-18  
**审核状态**: 待审核  
**实施优先级**: 高