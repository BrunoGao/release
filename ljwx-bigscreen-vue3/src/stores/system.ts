import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Theme, LoadingState, PerformanceMetrics } from '@/types/system'

export const useSystemStore = defineStore('system', () => {
  // ========== 状态定义 ==========
  
  // 主题设置
  const theme = ref<Theme>('dark')
  const customTheme = ref<Record<string, any>>({})
  
  // 加载状态
  const loading = ref(false)
  const loadingText = ref('加载中...')
  const loadingStates = ref<Map<string, LoadingState>>(new Map())
  
  // 系统状态
  const isOnline = ref(true)
  const pageVisible = ref(true)
  const currentRoute = ref('')
  const screenMode = ref<'dashboard' | 'fullscreen'>('dashboard')
  
  // 性能指标
  const performanceMetrics = ref<PerformanceMetrics>({
    pageLoadTime: 0,
    apiResponseTimes: {},
    memoryUsage: 0,
    renderTime: 0,
    errorCount: 0
  })
  
  // 用户设置
  const userPreferences = ref({
    autoRefresh: true,
    refreshInterval: 5000,
    showAnimations: true,
    enableSounds: false,
    language: 'zh-CN'
  })
  
  // 实时数据状态
  const realtimeStatus = ref({
    wsConnected: false,
    lastUpdate: null as Date | null,
    updateCount: 0
  })
  
  // ========== 计算属性 ==========
  
  const isLoading = computed(() => loading.value || loadingStates.value.size > 0)
  
  const currentThemeColors = computed(() => {
    const baseColors = {
      primary: '#00ff9d',
      secondary: '#00e4ff', 
      success: '#67c23a',
      warning: '#ffa726',
      error: '#ff6b6b',
      info: '#409eff'
    }
    
    return { ...baseColors, ...customTheme.value }
  })
  
  const systemHealth = computed(() => {
    const score = (
      (isOnline.value ? 25 : 0) +
      (realtimeStatus.value.wsConnected ? 25 : 0) +
      (performanceMetrics.value.errorCount < 5 ? 25 : 0) +
      (performanceMetrics.value.pageLoadTime < 3000 ? 25 : 0)
    )
    
    return {
      score,
      status: score >= 75 ? 'excellent' : score >= 50 ? 'good' : score >= 25 ? 'warning' : 'error'
    }
  })
  
  // ========== 动作方法 ==========
  
  // 主题管理
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('ljwx-theme', newTheme)
  }
  
  const setCustomTheme = (colors: Record<string, any>) => {
    customTheme.value = colors
    localStorage.setItem('ljwx-custom-theme', JSON.stringify(colors))
  }
  
  // 加载状态管理
  const setLoading = (state: boolean, text = '加载中...') => {
    loading.value = state
    loadingText.value = text
  }
  
  const addLoadingState = (id: string, state: LoadingState) => {
    loadingStates.value.set(id, state)
  }
  
  const removeLoadingState = (id: string) => {
    loadingStates.value.delete(id)
  }
  
  const clearAllLoadingStates = () => {
    loadingStates.value.clear()
  }
  
  // 系统状态
  const setNetworkStatus = (online: boolean) => {
    isOnline.value = online
  }
  
  const setPageVisibility = (visible: boolean) => {
    pageVisible.value = visible
  }
  
  const setCurrentRoute = (route: string) => {
    currentRoute.value = route
  }
  
  const setScreenMode = (mode: 'dashboard' | 'fullscreen') => {
    screenMode.value = mode
  }
  
  // 性能指标
  const setPerformanceMetric = (key: keyof PerformanceMetrics, value: any) => {
    (performanceMetrics.value as any)[key] = value
  }
  
  const addApiResponseTime = (endpoint: string, time: number) => {
    performanceMetrics.value.apiResponseTimes[endpoint] = time
  }
  
  const incrementErrorCount = () => {
    performanceMetrics.value.errorCount++
  }
  
  // 用户设置
  const updateUserPreference = (key: keyof typeof userPreferences.value, value: any) => {
    (userPreferences.value as any)[key] = value
    localStorage.setItem('ljwx-user-preferences', JSON.stringify(userPreferences.value))
  }
  
  // 实时数据状态
  const setRealtimeStatus = (status: Partial<typeof realtimeStatus.value>) => {
    Object.assign(realtimeStatus.value, status)
  }
  
  const updateLastUpdateTime = () => {
    realtimeStatus.value.lastUpdate = new Date()
    realtimeStatus.value.updateCount++
  }
  
  // 初始化
  const initializeStore = () => {
    // 从 localStorage 恢复设置
    const savedTheme = localStorage.getItem('ljwx-theme') as Theme
    if (savedTheme) {
      theme.value = savedTheme
    }
    
    const savedCustomTheme = localStorage.getItem('ljwx-custom-theme')
    if (savedCustomTheme) {
      try {
        customTheme.value = JSON.parse(savedCustomTheme)
      } catch (e) {
        console.warn('Failed to parse custom theme:', e)
      }
    }
    
    const savedPreferences = localStorage.getItem('ljwx-user-preferences')
    if (savedPreferences) {
      try {
        userPreferences.value = { ...userPreferences.value, ...JSON.parse(savedPreferences) }
      } catch (e) {
        console.warn('Failed to parse user preferences:', e)
      }
    }
    
    // 检测系统主题
    if (theme.value === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
  }
  
  // 重置状态
  const resetStore = () => {
    theme.value = 'dark'
    customTheme.value = {}
    loading.value = false
    loadingStates.value.clear()
    performanceMetrics.value = {
      pageLoadTime: 0,
      apiResponseTimes: {},
      memoryUsage: 0,
      renderTime: 0,
      errorCount: 0
    }
    
    // 清除 localStorage
    localStorage.removeItem('ljwx-theme')
    localStorage.removeItem('ljwx-custom-theme')
    localStorage.removeItem('ljwx-user-preferences')
  }
  
  // 导出性能报告
  const exportPerformanceReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      theme: theme.value,
      userPreferences: userPreferences.value,
      performanceMetrics: performanceMetrics.value,
      systemHealth: systemHealth.value,
      realtimeStatus: realtimeStatus.value
    }
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ljwx-performance-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  return {
    // 状态
    theme,
    customTheme,
    loading,
    loadingText,
    loadingStates,
    isOnline,
    pageVisible,
    currentRoute,
    screenMode,
    performanceMetrics,
    userPreferences,
    realtimeStatus,
    
    // 计算属性
    isLoading,
    currentThemeColors,
    systemHealth,
    
    // 方法
    setTheme,
    setCustomTheme,
    setLoading,
    addLoadingState,
    removeLoadingState,
    clearAllLoadingStates,
    setNetworkStatus,
    setPageVisibility,
    setCurrentRoute,
    setScreenMode,
    setPerformanceMetric,
    addApiResponseTime,
    incrementErrorCount,
    updateUserPreference,
    setRealtimeStatus,
    updateLastUpdateTime,
    initializeStore,
    resetStore,
    exportPerformanceReport
  }
})