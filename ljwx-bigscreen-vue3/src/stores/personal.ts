import { defineStore } from 'pinia'
import type { 
  HealthProfile, 
  HealthGoal, 
  HealthRecommendation,
  VitalSignReading,
  DeviceInfo
} from '@/types/health'

interface PersonalHealthSummary {
  overallScore: number
  riskLevel: 'low' | 'medium' | 'high'
  lastAssessment: Date
  keyMetrics: {
    heartRate: { avg: number, status: string }
    bloodPressure: { systolic: number, diastolic: number, status: string }
    bmi: { value: number, category: string }
    sleepQuality: { score: number, status: string }
  }
}

interface DailyActivity {
  steps: number
  distance: number
  calories: number
  activeMinutes: number
  exerciseMinutes: number
  goals: {
    steps: number
    distance: number
    calories: number
    activeMinutes: number
  }
}

interface PersonalState {
  // 用户资料
  userProfile: HealthProfile | null
  healthSummary: PersonalHealthSummary | null
  lastHealthUpdate: Date | null
  
  // 今日数据
  todayVitalSigns: Record<string, VitalSignReading>
  todayActivity: DailyActivity | null
  dailyGoalProgress: Record<string, number>
  
  // 个人目标
  personalGoals: HealthGoal[]
  recentAchievements: string[]
  
  // 生命体征历史数据
  vitalSignsHistory: Record<string, any[]>
  
  // 运动与睡眠
  dailyActivityStats: any
  weeklyActivitySummary: any
  exerciseGoals: any
  sleepAnalysisData: any
  sleepTrends: any[]
  sleepRecommendations: string[]
  
  // 心理健康
  stressLevelData: any
  moodTrendData: any
  mindfulnessStats: any
  
  // 个性化建议
  healthRecommendations: HealthRecommendation[]
  priorityActions: string[]
  
  // 设备管理
  connectedDevices: DeviceInfo[]
  deviceSyncHistory: any[]
  
  // 数据统计
  dataCompleteness: Record<string, number>
  dataCollectionStats: any
  privacySettings: any
  notificationSettings: any
  
  // 状态管理
  isLoading: boolean
  selectedTimeRange: string
  layoutMode: {
    mobile: boolean
    tablet: boolean
    desktop: boolean
  }
}

export const usePersonalStore = defineStore('personal', {
  state: (): PersonalState => ({
    userProfile: {
      userId: 'user_123',
      basicInfo: {
        age: 28,
        gender: 'male',
        height: 175,
        weight: 70,
        bloodType: 'A+'
      },
      medicalHistory: {
        conditions: ['轻微高血压'],
        medications: ['降压药'],
        allergies: ['青霉素'],
        surgeries: []
      },
      lifestyle: {
        smokingStatus: 'never',
        drinkingFrequency: 'occasional',
        exerciseFrequency: 'moderate',
        dietType: 'regular'
      },
      preferences: {
        units: 'metric',
        language: 'zh-CN',
        notifications: {
          email: true,
          push: true,
          sms: false
        }
      }
    },
    
    healthSummary: {
      overallScore: 85,
      riskLevel: 'low',
      lastAssessment: new Date(),
      keyMetrics: {
        heartRate: { avg: 72, status: 'normal' },
        bloodPressure: { systolic: 120, diastolic: 80, status: 'normal' },
        bmi: { value: 22.9, category: 'normal' },
        sleepQuality: { score: 82, status: 'good' }
      }
    },
    
    lastHealthUpdate: new Date(),
    
    todayVitalSigns: {
      heartRate: {
        current: 72,
        trend: 'stable',
        range: { min: 60, max: 100 },
        timestamp: new Date(),
        quality: 'excellent'
      },
      bloodOxygen: {
        current: 98,
        trend: 'stable',
        range: { min: 95, max: 100 },
        timestamp: new Date(),
        quality: 'excellent'
      },
      temperature: {
        current: 36.5,
        trend: 'stable',
        range: { min: 36.0, max: 37.5 },
        timestamp: new Date(),
        quality: 'good'
      }
    },
    
    todayActivity: {
      steps: 8500,
      distance: 6.2,
      calories: 2100,
      activeMinutes: 180,
      exerciseMinutes: 45,
      goals: {
        steps: 10000,
        distance: 8,
        calories: 2500,
        activeMinutes: 240
      }
    },
    
    dailyGoalProgress: {
      steps: 85,
      distance: 77.5,
      calories: 84,
      activeMinutes: 75,
      water: 80,
      sleep: 90
    },
    
    personalGoals: [
      {
        id: 'goal_1',
        userId: 'user_123',
        type: 'fitness',
        title: '每日步数目标',
        description: '每天完成10000步',
        targetValue: 10000,
        currentValue: 8500,
        unit: '步',
        deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        progress: 85,
        status: 'active',
        milestones: []
      },
      {
        id: 'goal_2',
        userId: 'user_123',
        type: 'weight_loss',
        title: '体重管理',
        description: '减重到68公斤',
        targetValue: 68,
        currentValue: 70,
        unit: '公斤',
        deadline: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
        progress: 67,
        status: 'active',
        milestones: []
      }
    ],
    
    recentAchievements: [
      '连续7天达成步数目标',
      '本周睡眠质量提升15%',
      '血压保持稳定状态'
    ],
    
    vitalSignsHistory: {},
    
    dailyActivityStats: {
      today: { steps: 8500, calories: 2100, distance: 6.2 },
      yesterday: { steps: 9200, calories: 2250, distance: 6.8 },
      weekAvg: { steps: 8800, calories: 2180, distance: 6.5 },
      trend: 'stable'
    },
    
    weeklyActivitySummary: {
      totalSteps: 61600,
      totalDistance: 45.4,
      totalCalories: 15260,
      avgDailySteps: 8800,
      goalAchievementRate: 78
    },
    
    exerciseGoals: {
      weeklyExercise: { target: 150, current: 120, unit: '分钟' },
      weeklyDistance: { target: 50, current: 45.4, unit: '公里' },
      weeklyCalories: { target: 17500, current: 15260, unit: '卡路里' }
    },
    
    sleepAnalysisData: {
      lastNightScore: 82,
      averageDuration: 7.5,
      sleepEfficiency: 88,
      deepSleepPercentage: 22,
      remSleepPercentage: 20,
      lightSleepPercentage: 58,
      weeklyAverage: 81
    },
    
    sleepTrends: [
      { date: '2025-01-10', score: 85, duration: 7.8 },
      { date: '2025-01-11', score: 78, duration: 7.2 },
      { date: '2025-01-12', score: 82, duration: 7.5 },
      { date: '2025-01-13', score: 79, duration: 7.1 },
      { date: '2025-01-14', score: 84, duration: 7.6 }
    ],
    
    sleepRecommendations: [
      '建议10点前准备睡觉',
      '睡前避免使用电子设备',
      '保持卧室温度在18-22度'
    ],
    
    stressLevelData: {
      current: 35,
      average: 40,
      trend: 'down',
      weeklyData: [42, 38, 35, 40, 32, 35, 35]
    },
    
    moodTrendData: {
      happiness: 75,
      anxiety: 25,
      energy: 80,
      focus: 70,
      weeklyTrends: {
        happiness: [70, 72, 75, 78, 75, 73, 75],
        anxiety: [30, 28, 25, 22, 25, 27, 25],
        energy: [75, 78, 80, 82, 80, 78, 80],
        focus: [65, 68, 70, 72, 70, 68, 70]
      }
    },
    
    mindfulnessStats: {
      weeklyMinutes: 105,
      sessions: 7,
      averageSession: 15,
      streak: 12
    },
    
    healthRecommendations: [
      {
        id: 'rec_1',
        userId: 'user_123',
        type: 'exercise',
        priority: 'high',
        title: '增加有氧运动',
        description: '建议每周增加30分钟有氧运动以提高心肺功能',
        actions: ['每天快走20分钟', '游泳2次/周', '爬楼梯代替电梯'],
        estimatedImpact: 'high',
        difficulty: 'moderate',
        timeframe: '2-4周',
        isImplemented: false
      },
      {
        id: 'rec_2',
        userId: 'user_123',
        type: 'sleep',
        priority: 'medium',
        title: '优化睡眠环境',
        description: '改善睡眠环境可以提高睡眠质量15-20%',
        actions: ['调整室温到20度', '使用遮光窗帘', '减少睡前屏幕时间'],
        estimatedImpact: 'medium',
        difficulty: 'easy',
        timeframe: '1周',
        isImplemented: false
      }
    ],
    
    priorityActions: [
      '今日目标：完成剩余1500步',
      '建议：下午进行15分钟伸展运动',
      '提醒：晚上10点开始准备睡觉'
    ],
    
    connectedDevices: [
      {
        deviceId: 'device_smartwatch_01',
        deviceType: 'wearable',
        brand: 'Apple',
        model: 'Watch Series 8',
        batteryLevel: 85,
        connectionStatus: 'connected',
        lastSyncTime: new Date(Date.now() - 300000)
      },
      {
        deviceId: 'device_scale_01',
        deviceType: 'sensor',
        brand: 'Xiaomi',
        model: 'Mi Smart Scale 2',
        batteryLevel: 92,
        connectionStatus: 'connected',
        lastSyncTime: new Date(Date.now() - 3600000)
      }
    ],
    
    deviceSyncHistory: [
      { deviceId: 'device_smartwatch_01', timestamp: new Date(Date.now() - 300000), status: 'success', dataCount: 147 },
      { deviceId: 'device_scale_01', timestamp: new Date(Date.now() - 3600000), status: 'success', dataCount: 1 }
    ],
    
    dataCompleteness: {
      heartRate: 95,
      bloodOxygen: 88,
      steps: 100,
      sleep: 92,
      weight: 85,
      bloodPressure: 60
    },
    
    dataCollectionStats: {
      totalDataPoints: 15842,
      dailyAverage: 245,
      qualityScore: 88,
      lastWeekIncrease: 12
    },
    
    privacySettings: {
      shareWithDoctors: true,
      shareWithFamily: false,
      shareWithResearchers: false,
      dataRetentionPeriod: '2years',
      anonymizeData: true
    },
    
    notificationSettings: {
      healthAlerts: true,
      goalReminders: true,
      medicationReminders: true,
      weeklyReports: true,
      socialSharing: false
    },
    
    isLoading: false,
    selectedTimeRange: '7d',
    layoutMode: {
      mobile: false,
      tablet: false,
      desktop: true
    }
  }),

  getters: {
    // 获取指定类型和时间范围的生命体征数据
    getVitalSignData: (state) => (type: string, timeRange: string) => {
      // 模拟历史数据
      const now = new Date()
      const days = timeRange === '1d' ? 1 : timeRange === '3d' ? 3 : timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90
      
      return Array.from({ length: days * 24 }, (_, i) => {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000)
        let value: number
        
        switch (type) {
          case 'heartRate':
            value = 70 + Math.sin(i * 0.1) * 5 + Math.random() * 10
            break
          case 'bloodOxygen':
            value = 97 + Math.random() * 3
            break
          case 'bloodPressure':
            return {
              timestamp,
              systolic: 115 + Math.random() * 10,
              diastolic: 75 + Math.random() * 10
            }
          default:
            value = Math.random() * 100
        }
        
        return { timestamp, value }
      }).reverse()
    },
    
    // 健康风险评估
    healthRiskAssessment: (state) => {
      if (!state.healthSummary) return null
      
      const risks = []
      const metrics = state.healthSummary.keyMetrics
      
      if (metrics.bloodPressure.systolic > 140 || metrics.bloodPressure.diastolic > 90) {
        risks.push({ type: 'hypertension', level: 'high', message: '血压偏高，建议就医' })
      }
      
      if (metrics.bmi.value > 25) {
        risks.push({ type: 'overweight', level: 'medium', message: '体重超标，建议控制饮食' })
      }
      
      if (metrics.sleepQuality.score < 60) {
        risks.push({ type: 'sleep', level: 'medium', message: '睡眠质量差，需要改善' })
      }
      
      return {
        overall: state.healthSummary.riskLevel,
        risks,
        riskCount: risks.length
      }
    },
    
    // 目标完成情况统计
    goalCompletionStats: (state) => {
      const activeGoals = state.personalGoals.filter(goal => goal.status === 'active')
      const completedGoals = state.personalGoals.filter(goal => goal.status === 'completed')
      
      const avgProgress = activeGoals.length > 0 
        ? activeGoals.reduce((sum, goal) => sum + goal.progress, 0) / activeGoals.length 
        : 0
      
      return {
        total: state.personalGoals.length,
        active: activeGoals.length,
        completed: completedGoals.length,
        averageProgress: avgProgress,
        onTrack: activeGoals.filter(goal => goal.progress >= 75).length
      }
    },
    
    // 可导出的数据类型
    availableExportData: (state) => ([
      { type: 'vitalSigns', name: '生命体征', available: true },
      { type: 'activity', name: '运动数据', available: true },
      { type: 'sleep', name: '睡眠数据', available: true },
      { type: 'goals', name: '健康目标', available: true },
      { type: 'recommendations', name: '健康建议', available: true },
      { type: 'complete', name: '完整报告', available: true }
    ])
  },

  actions: {
    // 初始化个人仪表板
    async initializePersonalDashboard() {
      this.isLoading = true
      try {
        await Promise.all([
          this.fetchUserProfile(),
          this.fetchTodayData(),
          this.fetchPersonalGoals(),
          this.fetchHealthRecommendations(),
          this.fetchConnectedDevices()
        ])
      } catch (error) {
        console.error('Failed to initialize personal dashboard:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取用户资料
    async fetchUserProfile() {
      try {
        const response = await fetch('/api/personal/profile')
        const data = await response.json()
        this.userProfile = data.profile
        this.healthSummary = data.healthSummary
        this.lastHealthUpdate = new Date(data.lastUpdate)
      } catch (error) {
        console.error('Failed to fetch user profile:', error)
        throw error
      }
    },
    
    // 获取今日数据
    async fetchTodayData() {
      try {
        const response = await fetch('/api/personal/today')
        const data = await response.json()
        
        this.todayVitalSigns = data.vitalSigns
        this.todayActivity = data.activity
        this.dailyGoalProgress = data.goalProgress
      } catch (error) {
        console.error('Failed to fetch today data:', error)
        throw error
      }
    },
    
    // 获取个人目标
    async fetchPersonalGoals() {
      try {
        const response = await fetch('/api/personal/goals')
        const data = await response.json()
        
        this.personalGoals = data.goals
        this.recentAchievements = data.achievements
      } catch (error) {
        console.error('Failed to fetch personal goals:', error)
        throw error
      }
    },
    
    // 获取健康建议
    async fetchHealthRecommendations() {
      try {
        const response = await fetch('/api/personal/recommendations')
        const data = await response.json()
        
        this.healthRecommendations = data.recommendations
        this.priorityActions = data.priorityActions
      } catch (error) {
        console.error('Failed to fetch health recommendations:', error)
        throw error
      }
    },
    
    // 获取连接的设备
    async fetchConnectedDevices() {
      try {
        const response = await fetch('/api/personal/devices')
        const data = await response.json()
        
        this.connectedDevices = data.devices
        this.deviceSyncHistory = data.syncHistory
      } catch (error) {
        console.error('Failed to fetch connected devices:', error)
        throw error
      }
    },
    
    // 更新个人目标
    async updatePersonalGoal(goalId: string, update: any) {
      try {
        const response = await fetch(`/api/personal/goals/${goalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(update)
        })
        
        if (response.ok) {
          const goalIndex = this.personalGoals.findIndex(g => g.id === goalId)
          if (goalIndex !== -1) {
            this.personalGoals[goalIndex] = { ...this.personalGoals[goalIndex], ...update }
          }
        }
      } catch (error) {
        console.error('Failed to update personal goal:', error)
        throw error
      }
    },
    
    // 处理建议操作
    async handleRecommendationAction(recommendationId: string, action: string) {
      try {
        const response = await fetch(`/api/personal/recommendations/${recommendationId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        })
        
        if (response.ok) {
          const rec = this.healthRecommendations.find(r => r.id === recommendationId)
          if (rec && action === 'implement') {
            rec.isImplemented = true
          }
        }
      } catch (error) {
        console.error('Failed to handle recommendation action:', error)
        throw error
      }
    },
    
    // 处理设备操作
    async handleDeviceAction(deviceId: string, action: string) {
      try {
        const response = await fetch(`/api/personal/devices/${deviceId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        })
        
        if (response.ok) {
          const device = this.connectedDevices.find(d => d.deviceId === deviceId)
          if (device) {
            switch (action) {
              case 'sync':
                device.lastSyncTime = new Date()
                break
              case 'disconnect':
                device.connectionStatus = 'disconnected'
                break
              case 'connect':
                device.connectionStatus = 'connected'
                break
            }
          }
        }
      } catch (error) {
        console.error('Failed to handle device action:', error)
        throw error
      }
    },
    
    // 触发紧急联系
    async triggerEmergencyContact() {
      try {
        const response = await fetch('/api/personal/emergency', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            userId: this.userProfile?.userId,
            timestamp: new Date(),
            location: 'current'
          })
        })
        
        return response.ok
      } catch (error) {
        console.error('Failed to trigger emergency contact:', error)
        throw error
      }
    },
    
    // 更新时间范围
    updateTimeRange(range: string) {
      this.selectedTimeRange = range
    },
    
    // 更新布局模式
    updateLayoutMode(mode: { mobile: boolean; tablet: boolean; desktop: boolean }) {
      this.layoutMode = mode
    },
    
    // 刷新所有数据
    async refreshAllData() {
      await this.initializePersonalDashboard()
    },
    
    // 导出个人健康数据
    async exportPersonalData(options: any) {
      try {
        const response = await fetch('/api/personal/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(options)
        })
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `personal-health-data-${new Date().toISOString().split('T')[0]}.${options.format}`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Failed to export personal data:', error)
        throw error
      }
    },
    
    // 重置状态
    resetState() {
      this.$reset()
    }
  }
})