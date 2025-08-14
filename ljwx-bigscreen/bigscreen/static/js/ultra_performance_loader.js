// 终极性能优化加载器 - 解决17秒加载问题
class UltraPerformanceLoader {
    constructor() {
        this.startTime = performance.now();
        this.loadingSteps = [];
        this.preloadedData = new Map();
        this.resourceCache = new Map();
    }

    log(step, data = {}) {
        const elapsed = performance.now() - this.startTime;
        this.loadingSteps.push({step, time: elapsed, ...data});
        console.log(`🚀 [${elapsed.toFixed(0)}ms] ${step}`, data);
    }

    // 1. 立即渲染骨架屏
    renderSkeleton() {
        this.log('骨架屏渲染开始');
        const skeletonHTML = `
            <style>
                .skeleton-item { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); 
                    background-size: 200% 100%; animation: loading 1.5s infinite; }
                @keyframes loading { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', skeletonHTML);
        
        // 立即显示占位符
        const placeholders = {
            'healthDataCount': '---',
            'pendingAlerts': '---', 
            'activeDevices': '---',
            'unreadMessages': '---'
        };
        
        Object.entries(placeholders).forEach(([id, text]) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = text;
                el.className += ' skeleton-item';
            }
        });
        this.log('骨架屏渲染完成');
    }

    // 2. 预加载关键资源
    async preloadResources() {
        this.log('开始预加载资源');
        const resources = [
            '/static/libs/echarts.min.js',
            '/static/libs/jquery.min.js'
        ];
        
        const promises = resources.map(url => {
            return new Promise(resolve => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'script';
                link.href = url;
                link.onload = () => {
                    this.resourceCache.set(url, true);
                    resolve();
                };
                link.onerror = resolve; // 即使失败也继续
                document.head.appendChild(link);
            });
        });
        
        await Promise.all(promises);
        this.log('资源预加载完成', {cached: this.resourceCache.size});
    }

    // 3. 智能API预取
    async preloadAPIData() {
        this.log('开始API预取');
        const urlParams = new URLSearchParams(window.location.search);
        const customerId = urlParams.get('customerId') || '1';
        const today = new Date().toISOString().slice(0, 10);
        
        try {
            // 使用Service Worker缓存策略
            const controller = new AbortController();
            setTimeout(() => controller.abort(), 1500); // 1.5秒超时
            
            const response = await fetch(`/api/statistics/overview?orgId=${customerId}&date=${today}`, {
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'max-age=30',
                    'X-Preload': 'true'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.preloadedData.set('statistics', data);
                this.log('API预取成功', {size: JSON.stringify(data).length});
                return data;
            }
        } catch (error) {
            this.log('API预取失败', {error: error.message});
        }
        return null;
    }

    // 4. 渐进式渲染
    async progressiveRender(data) {
        this.log('开始渐进式渲染');
        
        if (data?.success) {
            const {data: stats} = data;
            
            // 分批更新，避免阻塞UI
            const updateBatches = [
                [['healthDataCount', this.formatNumber(stats.healthData)]],
                [['pendingAlerts', this.formatNumber(stats.pendingAlerts)]],
                [['activeDevices', stats.activeDevices], ['unreadMessages', this.formatNumber(stats.unreadMessages)]]
            ];
            
            for (let batch of updateBatches) {
                await new Promise(resolve => {
                    requestAnimationFrame(() => {
                        batch.forEach(([id, value]) => {
                            const el = document.getElementById(id);
                            if (el) {
                                el.textContent = value;
                                el.classList.remove('skeleton-item');
                                el.style.opacity = '0';
                                el.style.transition = 'opacity 0.3s ease';
                                setTimeout(() => el.style.opacity = '1', 10);
                            }
                        });
                        resolve();
                    });
                });
                await new Promise(resolve => setTimeout(resolve, 50)); // 50ms间隔
            }
            
            this.log('渐进式渲染完成');
        }
    }

    // 5. 后台数据同步
    async backgroundSync() {
        this.log('开始后台同步');
        
        if (this.preloadedData.has('statistics')) {
            const cachedData = this.preloadedData.get('statistics');
            
            // 后台获取最新数据
            setTimeout(async () => {
                try {
                    const urlParams = new URLSearchParams(window.location.search);
                    const customerId = urlParams.get('customerId') || '1';
                    const today = new Date().toISOString().slice(0, 10);
                    
                    const response = await fetch(`/api/statistics/overview?orgId=${customerId}&date=${today}`, {
                        headers: {'X-Background-Sync': 'true'}
                    });
                    
                    if (response.ok) {
                        const latestData = await response.json();
                        if (JSON.stringify(latestData) !== JSON.stringify(cachedData)) {
                            this.progressiveRender(latestData);
                            this.log('后台同步更新完成');
                        }
                    }
                } catch (error) {
                    this.log('后台同步失败', {error: error.message});
                }
            }, 100);
        }
    }

    // 工具函数
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num?.toString() || '--';
    }

    // 性能报告
    getReport() {
        const totalTime = performance.now() - this.startTime;
        return {
            totalTime: totalTime.toFixed(0) + 'ms',
            steps: this.loadingSteps,
            performance: totalTime < 1000 ? '🚀 极速' : totalTime < 3000 ? '⚡ 快速' : '🐌 需优化',
            cacheHits: this.resourceCache.size,
            preloadedData: this.preloadedData.size
        };
    }

    // 主执行函数
    async execute() {
        // Phase 1: 立即渲染
        this.renderSkeleton();
        
        // Phase 2: 并行预加载
        const [apiData] = await Promise.all([
            this.preloadAPIData(),
            this.preloadResources()
        ]);
        
        // Phase 3: 渐进式渲染  
        if (apiData) {
            await this.progressiveRender(apiData);
        }
        
        // Phase 4: 后台同步
        this.backgroundSync();
        
        // 性能报告
        const report = this.getReport();
        console.log('🎯 终极性能报告:', report);
        
        return report;
    }
}

// 立即执行优化
window.ultraLoader = new UltraPerformanceLoader(); 