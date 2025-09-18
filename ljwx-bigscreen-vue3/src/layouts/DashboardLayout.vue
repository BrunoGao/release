<template>
  <div class="dashboard-layout">
    <!-- 顶部导航栏 -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="logo">
          <div class="logo-icon">🏥</div>
          <span class="logo-text">健康大屏</span>
        </div>
        
        <nav class="nav-tabs">
          <RouterLink
            v-for="tab in mainTabs"
            :key="tab.name"
            :to="{ name: tab.name }"
            class="nav-tab"
            :class="{ active: currentRoute === tab.name }"
          >
            <component :is="tab.icon" class="tab-icon" />
            <span class="tab-text">{{ tab.title }}</span>
            <div class="tab-indicator" />
          </RouterLink>
        </nav>
      </div>
      
      <div class="header-center">
        <div class="system-time">
          <div class="time-display">{{ currentTime }}</div>
          <div class="date-display">{{ currentDate }}</div>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 系统状态指示器 -->
        <div class="status-indicators">
          <div 
            class="status-item"
            :class="{ 'status-online': systemStore.isOnline, 'status-offline': !systemStore.isOnline }"
            title="网络状态"
          >
            <Wifi class="status-icon" />
          </div>
          
          <div 
            class="status-item"
            :class="{
              'status-excellent': systemHealth.status === 'excellent',
              'status-good': systemHealth.status === 'good',
              'status-warning': systemHealth.status === 'warning',
              'status-error': systemHealth.status === 'error'
            }"
            :title="`系统健康度: ${systemHealth.score}%`"
          >
            <MonitorIcon class="status-icon" />
            <span class="status-text">{{ systemHealth.score }}%</span>
          </div>
          
          <div 
            class="status-item"
            :class="{ 'status-connected': realtimeStatus.wsConnected }"
            title="实时连接状态"
          >
            <Connection class="status-icon" />
            <div class="connection-pulse" />
          </div>
        </div>
        
        <!-- 控制按钮 -->
        <div class="control-buttons">
          <button 
            class="control-btn"
            @click="toggleFullscreen"
            title="全屏切换"
          >
            <FullScreen />
          </button>
          
          <button 
            class="control-btn"
            @click="toggleTheme"
            title="主题切换"
          >
            <Sunny v-if="systemStore.theme === 'dark'" />
            <Moon v-else />
          </button>
          
          <button 
            class="control-btn"
            @click="refreshData"
            title="刷新数据"
            :class="{ 'refreshing': refreshing }"
          >
            <Refresh />
          </button>
        </div>
      </div>
    </header>
    
    <!-- 主内容区域 -->
    <main class="dashboard-main">
      <RouterView v-slot="{ Component, route }">
        <KeepAlive :include="keepAliveRoutes">
          <Transition
            :name="route.meta.transition || 'fade'"
            mode="out-in"
            appear
          >
            <component :is="Component" :key="route.path" />
          </Transition>
        </KeepAlive>
      </RouterView>
    </main>
    
    <!-- 底部状态栏 -->
    <footer class="dashboard-footer">
      <div class="footer-left">
        <div class="performance-info">
          <span class="perf-item">
            <Timer class="perf-icon" />
            响应: {{ avgResponseTime }}ms
          </span>
          <span class="perf-item">
            <Cpu class="perf-icon" />
            内存: {{ memoryUsage }}MB
          </span>
          <span class="perf-item">
            <TrendCharts class="perf-icon" />
            FPS: {{ currentFPS }}
          </span>
        </div>
      </div>
      
      <div class="footer-center">
        <div class="quick-actions">
          <button 
            v-for="action in quickActions"
            :key="action.name"
            class="quick-action"
            @click="handleQuickAction(action)"
            :title="action.title"
          >
            <component :is="action.icon" class="action-icon" />
          </button>
        </div>
      </div>
      
      <div class="footer-right">
        <div class="system-info">
          <span class="info-item">Version {{ version }}</span>
          <span class="info-item">© 2025 LJWX</span>
        </div>
      </div>
    </footer>
    
    <!-- 快捷键帮助 -->
    <div v-if="showHelpModal" class="help-modal" @click="showHelpModal = false">
      <div class="help-content" @click.stop>
        <h3>快捷键帮助</h3>
        <div class="shortcut-list">
          <div v-for="shortcut in shortcuts" :key="shortcut.key" class="shortcut-item">
            <kbd class="shortcut-key">{{ shortcut.key }}</kbd>
            <span class="shortcut-desc">{{ shortcut.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Monitor, 
  User, 
  Wifi, 
  Connection,
  FullScreen,
  Sunny,
  Moon,
  Refresh,
  Timer,
  Cpu,
  TrendCharts,
  QuestionFilled,
  Setting,
  Download
} from '@element-plus/icons-vue'
import { useSystemStore } from '@/stores/system'
import { useRouter, useRoute } from 'vue-router'

// 系统状态
const systemStore = useSystemStore()
const router = useRouter()
const route = useRoute()

// 当前路由
const currentRoute = computed(() => route.name as string)

// 主导航标签
const mainTabs = [
  {
    name: 'MainDashboard',
    title: '主大屏',
    icon: Monitor,
    path: '/dashboard/main'
  },
  {
    name: 'PersonalDashboard',
    title: '个人健康',
    icon: User,
    path: '/dashboard/personal'
  }
]

// 保持活跃的路由
const keepAliveRoutes = ['MainDashboard', 'PersonalDashboard']

// 时间显示
const currentTime = ref('')
const currentDate = ref('')

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short'
  })
}

// 系统健康状态
const systemHealth = computed(() => systemStore.systemHealth)
const realtimeStatus = computed(() => systemStore.realtimeStatus)

// 性能指标
const avgResponseTime = computed(() => {
  const times = Object.values(systemStore.performanceMetrics.apiResponseTimes)
  if (times.length === 0) return 0
  return Math.round(times.reduce((a, b) => a + b, 0) / times.length)
})

const memoryUsage = computed(() => {
  return Math.round(systemStore.performanceMetrics.memoryUsage / 1024 / 1024)
})

const currentFPS = ref(60)

// 刷新状态
const refreshing = ref(false)

// 快捷操作
const quickActions = [
  {
    name: 'help',
    title: '帮助',
    icon: QuestionFilled
  },
  {
    name: 'settings',
    title: '设置',
    icon: Setting
  },
  {
    name: 'export',
    title: '导出',
    icon: Download
  }
]

// 版本信息
const version = '1.0.0'

// 帮助模态框
const showHelpModal = ref(false)

// 快捷键配置
const shortcuts = [
  { key: 'F11', description: '全屏切换' },
  { key: 'Ctrl + R', description: '刷新数据' },
  { key: 'Ctrl + T', description: '主题切换' },
  { key: 'Ctrl + H', description: '显示帮助' },
  { key: 'Ctrl + 1', description: '主大屏' },
  { key: 'Ctrl + 2', description: '个人大屏' },
  { key: 'Esc', description: '返回上级' }
]

// 方法
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    systemStore.setScreenMode('fullscreen')
  } else {
    document.exitFullscreen()
    systemStore.setScreenMode('dashboard')
  }
}

const toggleTheme = () => {
  const newTheme = systemStore.theme === 'dark' ? 'light' : 'dark'
  systemStore.setTheme(newTheme)
}

const refreshData = async () => {
  if (refreshing.value) return
  
  refreshing.value = true
  
  try {
    // 触发当前页面数据刷新
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 这里可以添加实际的数据刷新逻辑
    systemStore.updateLastUpdateTime()
    
  } finally {
    refreshing.value = false
  }
}

const handleQuickAction = (action: any) => {
  switch (action.name) {
    case 'help':
      showHelpModal.value = true
      break
    case 'settings':
      // 打开设置面板
      break
    case 'export':
      // 导出数据
      systemStore.exportPerformanceReport()
      break
  }
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  // 全屏切换
  if (e.key === 'F11') {
    e.preventDefault()
    toggleFullscreen()
  }
  
  // Ctrl 组合键
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 'r':
        e.preventDefault()
        refreshData()
        break
      case 't':
        e.preventDefault()
        toggleTheme()
        break
      case 'h':
        e.preventDefault()
        showHelpModal.value = true
        break
      case '1':
        e.preventDefault()
        router.push({ name: 'MainDashboard' })
        break
      case '2':
        e.preventDefault()
        router.push({ name: 'PersonalDashboard' })
        break
    }
  }
  
  // ESC 键
  if (e.key === 'Escape') {
    if (showHelpModal.value) {
      showHelpModal.value = false
    } else if (document.fullscreenElement) {
      document.exitFullscreen()
      systemStore.setScreenMode('dashboard')
    }
  }
}

// FPS 监控
const monitorFPS = () => {
  let frames = 0
  let lastTime = performance.now()
  
  const tick = () => {
    frames++
    const now = performance.now()
    
    if (now >= lastTime + 1000) {
      currentFPS.value = Math.round((frames * 1000) / (now - lastTime))
      frames = 0
      lastTime = now
    }
    
    requestAnimationFrame(tick)
  }
  
  requestAnimationFrame(tick)
}

// 生命周期
onMounted(() => {
  // 初始化系统状态
  systemStore.initializeStore()
  
  // 更新时间
  updateTime()
  const timeInterval = setInterval(updateTime, 1000)
  
  // 绑定键盘事件
  document.addEventListener('keydown', handleKeydown)
  
  // 启动FPS监控
  monitorFPS()
  
  onUnmounted(() => {
    clearInterval(timeInterval)
    document.removeEventListener('keydown', handleKeydown)
  })
})
</script>

<style lang="scss" scoped>
.dashboard-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

// ========== 顶部导航栏 ==========
.dashboard-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
  z-index: var(--z-sticky);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  
  .logo-icon {
    width: 32px;
    height: 32px;
    font-size: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .logo-text {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--primary-500);
    text-shadow: var(--shadow-glow);
  }
}

.nav-tabs {
  display: flex;
  gap: var(--spacing-md);
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--text-secondary);
  position: relative;
  transition: all var(--duration-normal);
  
  .tab-icon {
    width: 20px;
    height: 20px;
  }
  
  .tab-text {
    font-size: var(--font-md);
    font-weight: 500;
  }
  
  .tab-indicator {
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 3px;
    background: var(--primary-500);
    border-radius: var(--radius-full);
    transition: width var(--duration-normal);
  }
  
  &:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.05);
  }
  
  &.active {
    color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
    
    .tab-indicator {
      width: 80%;
    }
  }
}

.header-center {
  .system-time {
    text-align: center;
    
    .time-display {
      font-size: var(--font-2xl);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
      text-shadow: var(--shadow-glow);
    }
    
    .date-display {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      margin-top: var(--spacing-xs);
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

// 状态指示器
.status-indicators {
  display: flex;
  gap: var(--spacing-md);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  transition: all var(--duration-normal);
  position: relative;
  
  .status-icon {
    width: 16px;
    height: 16px;
  }
  
  .status-text {
    font-size: var(--font-xs);
    font-weight: 600;
  }
  
  &.status-online,
  &.status-connected {
    color: var(--success);
    background: rgba(103, 194, 58, 0.1);
  }
  
  &.status-offline {
    color: var(--error);
    background: rgba(255, 107, 107, 0.1);
  }
  
  &.status-excellent {
    color: var(--success);
    background: rgba(103, 194, 58, 0.1);
  }
  
  &.status-good {
    color: var(--info);
    background: rgba(64, 158, 255, 0.1);
  }
  
  &.status-warning {
    color: var(--warning);
    background: rgba(255, 167, 38, 0.1);
  }
  
  &.status-error {
    color: var(--error);
    background: rgba(255, 107, 107, 0.1);
  }
}

.connection-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  animation: pulse 2s ease-in-out infinite;
}

// 控制按钮
.control-buttons {
  display: flex;
  gap: var(--spacing-sm);
}

.control-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-normal);
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
  
  &.refreshing {
    animation: spin 1s linear infinite;
  }
}

// ========== 主内容区域 ==========
.dashboard-main {
  flex: 1;
  padding: var(--spacing-lg);
  overflow: hidden;
}

// ========== 底部状态栏 ==========
.dashboard-footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  background: var(--bg-card);
  border-top: 1px solid var(--border-tertiary);
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.performance-info {
  display: flex;
  gap: var(--spacing-md);
}

.perf-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  
  .perf-icon {
    width: 12px;
    height: 12px;
  }
}

.quick-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.quick-action {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast);
  
  .action-icon {
    width: 14px;
    height: 14px;
  }
  
  &:hover {
    color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

.system-info {
  display: flex;
  gap: var(--spacing-md);
}

// ========== 帮助模态框 ==========
.help-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.help-content {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  max-width: 400px;
  
  h3 {
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
    text-align: center;
  }
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.shortcut-key {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-secondary);
  border: 1px solid var(--border-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  font-family: var(--font-tech);
  color: var(--primary-500);
}

.shortcut-desc {
  flex: 1;
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

// ========== 动画 ==========
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .dashboard-header {
    padding: 0 var(--spacing-md);
  }
  
  .header-center {
    display: none;
  }
  
  .status-indicators {
    gap: var(--spacing-sm);
  }
  
  .performance-info {
    gap: var(--spacing-sm);
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    height: 60px;
  }
  
  .nav-tabs {
    gap: var(--spacing-sm);
  }
  
  .nav-tab {
    padding: var(--spacing-xs) var(--spacing-sm);
    
    .tab-text {
      display: none;
    }
  }
  
  .control-buttons {
    gap: var(--spacing-xs);
  }
  
  .control-btn {
    width: 32px;
    height: 32px;
  }
}
</style>